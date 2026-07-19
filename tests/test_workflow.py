from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "update-readme-assets.yml"


def test_workflow_exists():
    assert WORKFLOW_PATH.exists()


def test_workflow_triggers_schedule_and_manual_dispatch():
    content = WORKFLOW_PATH.read_text()
    assert "schedule:" in content
    assert 'cron: "17 6 * * *"' in content
    assert "workflow_dispatch:" in content


def test_workflow_uses_generator_seam_and_no_op_guard():
    content = WORKFLOW_PATH.read_text()
    assert "GITHUB_CONTRIBUTION_USERNAME: ${{ github.repository_owner }}" in content
    assert "python -m generator" in content
    assert "git diff --quiet --exit-code -- assets/contribution-life-light.gif assets/contribution-life-dark.gif" in content
    assert "No asset changes detected; skipping commit." in content