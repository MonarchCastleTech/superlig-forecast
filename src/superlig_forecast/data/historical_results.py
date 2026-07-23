"""Acquisition helpers for the historical Football-Data archive."""

from pathlib import Path
import shutil
from zipfile import ZipFile

HISTORICAL_RESULTS_MEMBER = "all_euro_data.csv"


def extract_historical_results_archive(archive_path: Path, output_dir: Path) -> Path:
    """Extract the single expected CSV without trusting archive paths."""

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / HISTORICAL_RESULTS_MEMBER
    temporary = target.with_suffix(".csv.part")
    with ZipFile(archive_path) as archive:
        if HISTORICAL_RESULTS_MEMBER not in archive.namelist():
            raise ValueError(f"historical archive is missing {HISTORICAL_RESULTS_MEMBER}")
        with (
            archive.open(HISTORICAL_RESULTS_MEMBER) as source,
            temporary.open("wb") as destination,
        ):
            shutil.copyfileobj(source, destination, length=1024 * 1024)
    temporary.replace(target)
    return target
