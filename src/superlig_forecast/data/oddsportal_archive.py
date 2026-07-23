"""Safe extraction of the pinned OddsPortal archive."""

from pathlib import Path
import shutil
from zipfile import ZipFile

ODDSPORTAL_MEMBERS = {
    "leagues": "leagues.csv",
    "matches": "matches.csv",
}


def extract_oddsportal_archive(archive_path: Path, output_dir: Path) -> dict[str, Path]:
    """Extract only the league index and match table."""

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Path] = {}
    with ZipFile(archive_path) as archive:
        missing = set(ODDSPORTAL_MEMBERS.values()) - set(archive.namelist())
        if missing:
            raise ValueError(f"OddsPortal archive is missing: {', '.join(sorted(missing))}")
        for table, member in ODDSPORTAL_MEMBERS.items():
            target = output_dir / member
            temporary = target.with_suffix(".csv.part")
            with archive.open(member) as source, temporary.open("wb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
            temporary.replace(target)
            extracted[table] = target
    return extracted
