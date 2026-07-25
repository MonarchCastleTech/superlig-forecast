from pathlib import Path


def test_update_workflow_has_strict_quality_gates() -> None:
    text = Path(".github/workflows/update-forecast.yml").read_text()
    assert "17 */6 * * *" in text
    assert "workflow_dispatch:" in text
    assert "contents: write" in text
    assert "superlig refresh-dashboard" in text
    assert "pytest" in text
    assert "mypy" in text
    assert "ruff check" in text
    assert "continue-on-error" not in text
