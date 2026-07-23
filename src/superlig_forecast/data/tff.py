"""Parser for official Turkish Football Federation competition pages."""

import html as html_module
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

from superlig_forecast.domain import MatchRecord

ISTANBUL = ZoneInfo("Europe/Istanbul")

TFF_PAGES = {
    "TR1": {"tier": 1, "page_id": 198, "archive_page_id": 545},
    "TR2": {"tier": 2, "page_id": 142, "archive_page_id": 563},
    "TR3": {"tier": 3, "page_id": 976, "archive_page_id": 371},
    "TR4": {"tier": 4, "page_id": 971, "archive_page_id": 376},
    "TRC": {"tier": 0, "page_id": 288, "archive_page_id": 288},
}


class TffCompetition(BaseModel):
    """One official TFF competition page."""

    model_config = ConfigDict(frozen=True)

    competition_id: str
    tier: int
    page_id: int
    archive_page_id: int


def decode_tff(payload: bytes, declared_charset: str | None = None) -> str:
    """Decode official pages with the legacy Turkish fallback."""

    for encoding in (declared_charset, "windows-1254", "utf-8"):
        if encoding:
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
    raise ValueError("TFF payload is not valid in declared, windows-1254, or UTF-8 encoding")


class TffAdapter:
    """Converts official fixture HTML into typed match records."""

    def parse_competitions(self, page_html: str) -> list[TffCompetition]:
        """Return required competitions whose configured pages are present."""

        found_page_ids = {
            int(value) for value in re.findall(r"pageID=(\d+)", page_html, flags=re.IGNORECASE)
        }
        return [
            TffCompetition(
                competition_id=competition_id,
                tier=config["tier"],
                page_id=config["page_id"],
                archive_page_id=config["archive_page_id"],
            )
            for competition_id, config in TFF_PAGES.items()
            if config["page_id"] in found_page_ids
        ]

    def parse_matches(
        self,
        page_html: str,
        *,
        observed_at: datetime,
        competition_id: str,
        season: str,
    ) -> list[MatchRecord]:
        """Parse all fixture rows from one TFF page."""

        rows = re.findall(
            r'<tr[^>]*class=["\']haftaninMaclariTr["\'][^>]*>(.*?)</tr>',
            page_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        matches: dict[str, MatchRecord] = {}
        for row in rows:
            match_id_match = re.search(r"[?&]macId=(\d+)", row, flags=re.IGNORECASE)
            if match_id_match is None:
                continue
            match_id = f"tff:{match_id_match.group(1)}"
            date_text = self._cell_text(row, "haftaninMaclariTarih")
            date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*(\d{2}:\d{2})", date_text)
            if date_match is None:
                raise ValueError(f"missing kickoff for {match_id}")
            kickoff = datetime.strptime(
                f"{date_match.group(1)} {date_match.group(2)}", "%d.%m.%Y %H:%M"
            ).replace(tzinfo=ISTANBUL)
            home_cell = self._cell(row, "haftaninMaclariEv")
            away_cell = self._cell(row, "haftaninMaclariDeplasman")
            score_text = self._cell_text(row, "haftaninMaclariSkor")
            score_match = re.search(r"(\d+)\s*-\s*(\d+)", score_text)
            record = MatchRecord(
                match_id=match_id,
                competition_id=competition_id,
                season=season,
                kickoff=kickoff,
                home_club_id=f"tff-club:{self._club_id(home_cell)}",
                away_club_id=f"tff-club:{self._club_id(away_cell)}",
                home_club_name=self._display_name(self._strip_tags(home_cell)),
                away_club_name=self._display_name(self._strip_tags(away_cell)),
                home_goals=int(score_match.group(1)) if score_match else None,
                away_goals=int(score_match.group(2)) if score_match else None,
                observed_at=observed_at,
            )
            previous = matches.get(match_id)
            if previous is not None and previous != record:
                raise ValueError(f"conflicting duplicate TFF match {match_id}")
            matches[match_id] = record
        return list(matches.values())

    @staticmethod
    def _cell(row: str, class_name: str) -> str:
        match = re.search(
            rf'<td[^>]*class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'][^>]*>'
            r"(.*?)</td>",
            row,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match is None:
            raise ValueError(f"missing TFF cell {class_name}")
        return match.group(1)

    def _cell_text(self, row: str, class_name: str) -> str:
        return self._strip_tags(self._cell(row, class_name))

    @staticmethod
    def _club_id(cell: str) -> str:
        match = re.search(r"[?&]kulupID=(\d+)", cell, flags=re.IGNORECASE)
        if match is None:
            raise ValueError("missing TFF club ID")
        return match.group(1)

    @staticmethod
    def _strip_tags(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value)
        return " ".join(html_module.unescape(text).split())

    @staticmethod
    def _display_name(value: str) -> str:
        return re.sub(r"\b(Fk|Sk)\b", lambda match: match.group(1).upper(), value.title())
