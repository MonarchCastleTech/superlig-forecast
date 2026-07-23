"""Reproducible static research report."""

from pathlib import Path


def build_report(summary: dict[str, object], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.md"
    lines = ["# Süper Lig Forecast Report", "", "## Run summary", ""]
    lines.extend(f"- **{key}:** {value}" for key, value in sorted(summary.items()))
    lines.extend(
        [
            "",
            "Observed data, model estimates, missing coverage, and validation gates are reported separately.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
