from superlig_forecast.data.transfermarkt_live import (
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
        36: "https://www.transfermarkt.com.tr/fenerbahce-sk/kader/verein/36/saison_id/2026",
        12382: "https://www.transfermarkt.com.tr/amed-sk/kader/verein/12382/saison_id/2026",
    }


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
