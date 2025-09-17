from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, List

import pytest

from flarchitect.utils.release import bump_version_if_needed


class _RunRecorder:
    """Helper to emulate subprocess.run with programmable results."""

    def __init__(self, responses: List[str]):
        self.calls: list[list[str]] = []
        self._responses = responses

    def __call__(self, cmd: list[str], capture_output: bool, text: bool, check: bool):  # noqa: D401 - mimic subprocess.run signature
        self.calls.append(cmd)
        # Pop next prepared response
        stdout = self._responses.pop(0)
        # Minimal object with stdout attribute
        return SimpleNamespace(stdout=stdout)


def test_bumpwright_no_release(monkeypatch: pytest.MonkeyPatch) -> None:
    """When decide returns no level, do not bump and return None."""

    recorder = _RunRecorder([json.dumps({"level": None})])
    monkeypatch.setattr("subprocess.run", recorder)

    new_ver = bump_version_if_needed()

    assert new_ver is None
    # Only the decide command runs; includes --head by default
    assert recorder.calls[0][:3] == ["bumpwright", "decide", "--format"]
    assert "--head" in recorder.calls[0]
    # Only one invocation (no bump command executed)
    assert len(recorder.calls) == 1


def test_bumpwright_applies_bump_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """When a level is suggested, run bump with base/head and dry-run flags."""

    decide = json.dumps({"level": "patch"})
    bumped = json.dumps({"new_version": "1.2.3"})
    recorder = _RunRecorder([decide, bumped])
    monkeypatch.setattr("subprocess.run", recorder)

    new_ver = bump_version_if_needed(base="v1.0.0", head="", dry_run=True)

    assert new_ver == "1.2.3"
    # First call: decide without --head (empty head suppressed), but with base
    decide_cmd = recorder.calls[0]
    assert decide_cmd[:3] == ["bumpwright", "decide", "--format"]
    assert "--base" in decide_cmd and "v1.0.0" in decide_cmd
    assert "--head" not in decide_cmd

    # Second call: bump includes level, base and dry-run
    bump_cmd = recorder.calls[1]
    assert bump_cmd[:3] == ["bumpwright", "bump", "--level"]
    assert "patch" in bump_cmd
    assert "--base" in bump_cmd and "v1.0.0" in bump_cmd
    assert "--dry-run" in bump_cmd
