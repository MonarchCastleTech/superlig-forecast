"""Parser for current-season Transfermarkt league squad values."""

from dataclasses import dataclass
import html as html_module
import re

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class CurrentSquadValue:
    club_id: int
    club_name: str
    squad_size: int
    squad_value_eur: int


@dataclass(frozen=True)
class CurrentPlayerValue:
    player_id: int
    player_name: str
    club_id: int
    club_name: str
    position: str
    age: int | None
    nationalities: tuple[str, ...]
    contract: str
    market_value_eur: int | None


def _text(value: str) -> str:
    return " ".join(html_module.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def _money_to_eur(value: str) -> int:
    normalized = value.lower().replace(",", ".")
    number_match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    if number_match is None:
        raise ValueError(f"missing market value in {value!r}")
    number = float(number_match.group(1))
    multiplier = 1.0
    if "milyar" in normalized:
        multiplier = 1_000_000_000.0
    elif "mil." in normalized:
        multiplier = 1_000_000.0
    elif "bin" in normalized:
        multiplier = 1_000.0
    return round(number * multiplier)


def parse_current_squad_values(page_html: str) -> list[CurrentSquadValue]:
    """Parse the 2026-27 league overview's deterministic value table."""

    tables = re.findall(
        r"<table[^>]*class=[\"'][^\"']*\bitems\b[^\"']*[\"'][^>]*>(.*?)</table>",
        page_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    target = next(
        (table for table in tables if "marktwert_gesamt_anzeige" in table),
        None,
    )
    if target is None:
        raise ValueError("current squad-value table was not found")
    body_match = re.search(r"<tbody[^>]*>(.*?)</tbody>", target, re.I | re.S)
    if body_match is None:
        raise ValueError("current squad-value table has no body")
    values: list[CurrentSquadValue] = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", body_match.group(1), re.I | re.S):
        club_id_match = re.search(r"/verein/(\d+)/", row, re.I)
        name_match = re.search(
            r"<td[^>]*class=[\"'][^\"']*\bhauptlink\b[^\"']*[\"'][^>]*>"
            r".*?<a[^>]*title=[\"']([^\"']+)[\"'][^>]*>",
            row,
            re.I | re.S,
        )
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.I | re.S)
        if club_id_match is None or name_match is None or len(cells) < 7:
            continue
        squad_match = re.search(r"\d+", _text(cells[2]))
        if squad_match is None:
            raise ValueError(f"missing squad size for {name_match.group(1)}")
        values.append(
            CurrentSquadValue(
                club_id=int(club_id_match.group(1)),
                club_name=html_module.unescape(name_match.group(1)).strip(),
                squad_size=int(squad_match.group()),
                squad_value_eur=_money_to_eur(_text(cells[-1])),
            )
        )
    if not values:
        raise ValueError("current squad-value table contained no clubs")
    return values


def parse_current_squad_links(page_html: str, *, season: int) -> dict[int, str]:
    """Return stable current-season squad URLs keyed by Transfermarkt club ID."""

    links: dict[int, str] = {}
    pattern = rf'href=["\'](/[^"\']+/kader/verein/(\d+)/saison_id/{season})["\']'
    for path, club_id in re.findall(pattern, page_html, flags=re.IGNORECASE):
        links[int(club_id)] = f"https://www.transfermarkt.com.tr{path}"
    if not links:
        raise ValueError("current league page contained no squad links")
    return links


def parse_current_players(
    page_html: str, *, club_id: int, club_name: str
) -> list[CurrentPlayerValue]:
    """Parse every player and current value from one nested squad table."""

    soup = BeautifulSoup(page_html, "html.parser")
    table = soup.find("table", class_="items")
    if table is None:
        raise ValueError(f"squad table was not found for {club_name}")
    body = table.find("tbody", recursive=False)
    if body is None:
        raise ValueError(f"squad table has no body for {club_name}")
    players: list[CurrentPlayerValue] = []
    for row in body.find_all("tr", recursive=False):
        link = row.select_one('td.hauptlink a[href*="/profil/spieler/"]')
        if link is None:
            continue
        player_id_match = re.search(r"/spieler/(\d+)", str(link.get("href", "")))
        if player_id_match is None:
            continue
        cells = row.find_all("td", recursive=False)
        if len(cells) < 6:
            continue
        position_row = link.find_parent("tr")
        position_sibling = (
            position_row.find_next_sibling("tr") if position_row is not None else None
        )
        age_match = re.search(r"\d+", cells[2].get_text(" ", strip=True))
        nationalities = tuple(
            title
            for image in cells[3].find_all("img")
            if (title := str(image.get("title") or "").strip())
        )
        market_text = cells[-1].get_text(" ", strip=True)
        try:
            market_value = _money_to_eur(market_text)
        except ValueError:
            market_value = None
        players.append(
            CurrentPlayerValue(
                player_id=int(player_id_match.group(1)),
                player_name=link.get_text(" ", strip=True),
                club_id=club_id,
                club_name=club_name,
                position=(
                    position_sibling.get_text(" ", strip=True)
                    if position_sibling is not None
                    else str(cells[0].get("title") or "")
                ),
                age=int(age_match.group()) if age_match else None,
                nationalities=nationalities,
                contract=cells[4].get_text(" ", strip=True),
                market_value_eur=market_value,
            )
        )
    if not players:
        raise ValueError(f"squad table contained no players for {club_name}")
    return players
