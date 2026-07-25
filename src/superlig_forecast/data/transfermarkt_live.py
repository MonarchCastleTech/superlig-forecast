"""Parser and cached fetcher for current-season Transfermarkt squad values."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import html as html_module
import json
from pathlib import Path
import re
import time

from bs4 import BeautifulSoup
import httpx

from superlig_forecast.data.fetch import FetchResult, system_ssl_context
from superlig_forecast.data.snapshots import SnapshotStore


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


@dataclass(frozen=True, slots=True)
class ConditionalPage:
    status_code: int
    content: bytes
    etag: str | None = None
    last_modified: str | None = None
    content_type: str = "text/html"


@dataclass(frozen=True, slots=True)
class SquadFetchManifest:
    fetched: tuple[str, ...]
    unchanged: tuple[str, ...]
    failed: dict[str, str]
    snapshot_timestamp: str
    source_urls: dict[str, str]
    complete: bool


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
        links[int(club_id)] = f"https://www.transfermarkt.com{path}"
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


def _fetch_conditional(
    url: str,
    headers: Mapping[str, str],
) -> ConditionalPage:
    timeout = httpx.Timeout(connect=15.0, read=60.0, write=60.0, pool=15.0)
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": "superlig-forecast-transfermarkt/1.0",
        },
        verify=system_ssl_context(),
    ) as client:
        for attempt in range(4):
            response = client.get(url, headers=headers)
            if response.status_code == 304:
                return ConditionalPage(status_code=304, content=b"")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 3:
                    response.raise_for_status()
                time.sleep(0.25 * (2**attempt))
                continue
            response.raise_for_status()
            return ConditionalPage(
                status_code=response.status_code,
                content=response.content,
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
                content_type=response.headers.get("content-type", "text/html"),
            )
    raise RuntimeError("Transfermarkt request exhausted retries")


def _cache_path(root: Path, club_id: str) -> Path:
    return root / "_http_cache" / f"transfermarkt-squad-{club_id}.json"


def _read_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if item is not None}


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def fetch_current_squad_pages(
    links: Mapping[int, str],
    output: Path,
    *,
    fetch_page: Callable[[str, Mapping[str, str]], ConditionalPage] | None = None,
    now: Callable[[], datetime] | None = None,
) -> SquadFetchManifest:
    """Fetch all squads with retries, validators, and immutable raw snapshots."""

    request = fetch_page or _fetch_conditional
    timestamp = (now or (lambda: datetime.now(UTC)))()
    store = SnapshotStore(output)
    fetched: list[str] = []
    unchanged: list[str] = []
    failed: dict[str, str] = {}
    source_urls = {str(club_id): url for club_id, url in sorted(links.items())}

    for club_id, url in sorted(links.items()):
        key = str(club_id)
        source = f"transfermarkt-squad-{club_id}"
        cache_path = _cache_path(output, key)
        cache = _read_cache(cache_path)
        headers: dict[str, str] = {}
        if cache.get("etag"):
            headers["If-None-Match"] = cache["etag"]
        if cache.get("last_modified"):
            headers["If-Modified-Since"] = cache["last_modified"]
        try:
            page = request(url, headers)
            if page.status_code == 304:
                unchanged.append(key)
                continue
            if page.status_code != 200:
                raise RuntimeError(f"unexpected HTTP status {page.status_code}")
            digest = hashlib.sha256(page.content).hexdigest()
            latest = store.latest(source)
            if latest is not None and latest.sha256 == digest:
                unchanged.append(key)
            else:
                store.put(
                    FetchResult(
                        source=source,
                        url=url,
                        fetched_at=timestamp,
                        status_code=page.status_code,
                        content_type=page.content_type,
                        content=page.content,
                        extension=".html",
                    )
                )
                fetched.append(key)
            _write_json_atomic(
                cache_path,
                {
                    "etag": page.etag,
                    "last_modified": page.last_modified,
                    "sha256": digest,
                    "url": url,
                },
            )
        except Exception as error:  # noqa: BLE001 - manifest must retain every club failure
            failed[key] = f"{type(error).__name__}: {error}"
            store.record_failure(
                source=source,
                url=url,
                reason=str(error),
                failed_at=timestamp,
            )

    manifest = SquadFetchManifest(
        fetched=tuple(fetched),
        unchanged=tuple(unchanged),
        failed=failed,
        snapshot_timestamp=timestamp.isoformat(),
        source_urls=source_urls,
        complete=not failed,
    )
    if manifest.complete:
        _write_json_atomic(
            output / "_manifests" / "current-squads-complete.json",
            {
                "fetched": manifest.fetched,
                "unchanged": manifest.unchanged,
                "failed": manifest.failed,
                "snapshot_timestamp": manifest.snapshot_timestamp,
                "source_urls": manifest.source_urls,
                "complete": manifest.complete,
            },
        )
    return manifest
