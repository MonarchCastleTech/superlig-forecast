"""Safe extraction of the pinned Transfermarkt CSV archive."""

from pathlib import Path
import shutil
from zipfile import ZipFile

TRANSFERMARKT_CSV_TABLES = {
    "competitions": "competitions.csv",
    "clubs": "clubs.csv",
    "matches": "games.csv",
    "players": "players.csv",
    "valuations": "player_valuations.csv",
    "appearances": "appearances.csv",
    "lineups": "game_lineups.csv",
    "transfers": "transfers.csv",
}


def extract_transfermarkt_archive(archive_path: Path, output_dir: Path) -> dict[str, Path]:
    """Extract only the explicitly allowed analytical tables."""

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Path] = {}
    with ZipFile(archive_path) as archive:
        available = set(archive.namelist())
        missing = set(TRANSFERMARKT_CSV_TABLES.values()) - available
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"Transfermarkt archive is missing required files: {names}")
        for table, member in TRANSFERMARKT_CSV_TABLES.items():
            target = output_dir / member
            temporary = target.with_suffix(f"{target.suffix}.part")
            with archive.open(member) as source, temporary.open("wb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
            temporary.replace(target)
            extracted[table] = target
    return extracted
