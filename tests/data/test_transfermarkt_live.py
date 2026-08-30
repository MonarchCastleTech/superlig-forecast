from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from superlig_forecast.data.transfermarkt_live import (
    ConditionalPage,
    fetch_current_squad_pages,
    parse_current_players,
    parse_current_squad_links,
    parse_current_squad_values,
)


def test_parse_current_squad_values_from_league_table() -> None:
    html = """
    <table class="items">
      <thead><tr><th>marktwert_gesamt_anzeige</th></tr></thead>
      <tbody>
        <tr class="odd">
          <td><a href="/club/startseite/verein/36/saison_id/2026">crest</a></td>
          <td class="hauptlink"><a title="Fenerbahçe SK">Fenerbahçe SK</a></td>
          <td class="zentriert">43</td><td>27.2</td><td>24</td>
          <td class="rechts">7.75 mil. €</td>
          <td class="rechts"><a href="/fenerbahce-sk/kader/verein/36/saison_id/2026">333.15 mil. €</a></td>
        </tr>
        <tr class="even">
          <td><a href="/club/startseite/verein/12382/saison_id/2026">crest</a></td>
          <td class="hauptlink"><a title="Amed SK">Amed SK</a></td>
          <td class="zentriert">30</td><td>25.0</td><td>5</td>
          <td class="rechts">400 bin €</td>
          <td class="rechts"><a href="/amed-sk/kader/verein/12382/saison_id/2026">12.00 mil. €</a></td>
        </tr>
      </tbody>
    </table>
    """

    values = parse_current_squad_values(html)

    assert [(item.club_id, item.club_name, item.squad_value_eur) for item in values] == [
        (36, "Fenerbahçe SK", 333_150_000),
        (12382, "Amed SK", 12_000_000),
    ]
    assert parse_current_squad_links(html, season=2026) == {
        36: "https://www.transfermarkt.com/fenerbahce-sk/kader/verein/36/saison_id/2026",
        12382: "https://www.transfermarkt.com/amed-sk/kader/verein/12382/saison_id/2026",
    }


def test_parse_current_squad_links_keeps_allowed_public_origin() -> None:
    html = """
      <meta property="og:url" content="https://www.transfermarkt.co.uk/super-lig/startseite/wettbewerb/TR1/" />
      <a href="/fenerbahce/kader/verein/36/saison_id/2026">Fenerbahce</a>
    """
    assert parse_current_squad_links(html, season=2026) == {
        36: "https://www.transfermarkt.co.uk/fenerbahce/kader/verein/36/saison_id/2026"
    }


def test_parse_current_squad_values_supports_english_money_suffixes() -> None:
    html = """
    <table class="items">
      <thead><tr><th>marktwert_gesamt_anzeige</th></tr></thead>
      <tbody><tr>
        <td><a href="/club/startseite/verein/36/saison_id/2026">crest</a></td>
        <td class="hauptlink"><a title="Fenerbahce">Fenerbahce</a></td>
        <td>30</td><td>25.1</td><td>20</td><td>€800k</td>
        <td><a href="/fenerbahce/kader/verein/36/saison_id/2026">€333.15m</a></td>
      </tr></tbody>
    </table>
    """

    assert parse_current_squad_values(html)[0].squad_value_eur == 333_150_000


def test_parse_current_player_values_from_nested_squad_table() -> None:
    html = """
    <table class="items"><tbody>
      <tr class="odd theme6">
        <td class="zentriert rueckennummer bg_Torwart" title="Kaleci">1</td>
        <td class="posrela">
          <table class="inline-table">
            <tr><td class="hauptlink">
              <a href="/alban-lafont/profil/spieler/357117">Alban Lafont</a>
            </td></tr>
            <tr><td>Kaleci</td></tr>
          </table>
        </td>
        <td class="zentriert">27</td>
        <td class="zentriert"><img title="Fransa"></td>
        <td class="zentriert">2028</td>
        <td class="rechts hauptlink">4.00 mil. €</td>
      </tr>
    </tbody></table>
    """

    players = parse_current_players(html, club_id=12382, club_name="Amed SK")

    assert len(players) == 1
    assert players[0].player_id == 357117
    assert players[0].player_name == "Alban Lafont"
    assert players[0].position == "Kaleci"
    assert players[0].market_value_eur == 4_000_000


def test_fetch_current_squads_uses_conditional_cache(tmp_path: Path) -> None:
    requests: list[dict[str, str]] = []

    def first_fetch(
        url: str,
        headers: Mapping[str, str],
    ) -> ConditionalPage:
        del url
        requests.append(dict(headers))
        return ConditionalPage(200, b"<html>squad</html>", etag='"v1"')

    first = fetch_current_squad_pages(
        {36: "https://example.test/36"},
        tmp_path,
        fetch_page=first_fetch,
        now=lambda: datetime(2026, 7, 25, tzinfo=UTC),
    )
    assert first.fetched == ("36",)
    assert first.complete is True

    def second_fetch(
        url: str,
        headers: Mapping[str, str],
    ) -> ConditionalPage:
        del url
        requests.append(dict(headers))
        return ConditionalPage(304, b"")

    second = fetch_current_squad_pages(
        {36: "https://example.test/36"},
        tmp_path,
        fetch_page=second_fetch,
        now=lambda: datetime(2026, 7, 26, tzinfo=UTC),
    )
    assert second.unchanged == ("36",)
    assert requests[-1]["If-None-Match"] == '"v1"'

    def alternate_origin_fetch(
        url: str,
        headers: Mapping[str, str],
    ) -> ConditionalPage:
        del url
        requests.append(dict(headers))
        return ConditionalPage(200, b"<html>same squad</html>", etag='"v2"')

    fetch_current_squad_pages(
        {36: "https://example.co.uk/36"},
        tmp_path,
        fetch_page=alternate_origin_fetch,
        now=lambda: datetime(2026, 7, 27, tzinfo=UTC),
    )
    assert requests[-1] == {}
