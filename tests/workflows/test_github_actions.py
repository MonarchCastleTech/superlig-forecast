from pathlib import Path


def test_update_workflow_has_strict_quality_gates() -> None:
    text = Path(".github/workflows/update-forecast.yml").read_text()
    assert 'cron: "17 */6 * * *"' in text
    assert "workflow_dispatch:" in text
    assert "contents: write" in text
    assert "issues: write" in text
    assert "fetch-data" in text
    assert "--source tff-season" in text
    assert "--tff-base-url https://www.tff.org" in text
    assert "--value-coefficient 0" in text
    assert "--squad-page" not in text
    assert "forecast-season" in text
    assert "--model-artifact automation/seeds/model-2026-27.json" in text
    assert "export-dashboard-data" in text
    assert "superlig refresh-dashboard" in text
    assert '--candidate "$RUNNER_TEMP/dashboard-candidate.json"' in text
    assert '[[ -e "$path" ]] && existing+=("$path")' in text
    assert 'git add -- "${existing[@]}"' in text
    assert "git restore -- dashboard/public/data/dashboard.json" not in text
    assert "Alert on autonomous refresh failure" in text
    assert "[forecast-deadman] Autonomous refresh failed" in text
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
    assert 'workflows: ["Update forecast data"]' in text
    assert "github.event.workflow_run.conclusion == 'success'" in text
    assert text.count("continue-on-error: true") == 1
    assert "if: steps.deployment.outcome == 'failure'" in text
    assert "id: deployment_retry" in text
