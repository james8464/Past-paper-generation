"""CI signs locally without using a developer account or provisioning profile."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("target", ["test", "preflight-app-store"])
def test_ci_uses_explicit_ad_hoc_manual_signing_despite_personal_project_team(target):
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    commands = [
        shlex.split(line.split("run:", 1)[1])
        for line in workflow.splitlines()
        if line.strip().startswith("run:")
    ]
    (command,) = [
        parts for parts in commands if parts[:4] == ["make", "-C", "macOS", target]
    ]
    settings = dict(part.split("=", 1) for part in command[4:] if "=" in part)
    assert settings.get("SIGNING_IDENTITY") == "-"
    assert settings.get("SIGNING_STYLE") == "Manual"
    assert not any("allowProvisioning" in part for part in command)
