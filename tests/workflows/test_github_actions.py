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


def test_pages_workflow_is_least_privilege_and_static() -> None:
    text = Path(".github/workflows/deploy-pages.yml").read_text()
    assert "pages: write" in text
    assert "id-token: write" in text
    assert "contents: read" in text
    assert "actions/upload-pages-artifact" in text
    assert "actions/deploy-pages" in text
    assert "npm run build:pages" in text
    assert "continue-on-error" not in text
