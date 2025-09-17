import json
from types import SimpleNamespace

from flarchitect.utils.release import bump_version_if_needed


def test_bump_version_if_needed_noop(monkeypatch):
    # Simulate bumpwright decide returning no level
    def fake_run(args, capture_output, text, check):
        if args[:2] == ["bumpwright", "decide"]:
            return SimpleNamespace(stdout=json.dumps({"level": None}))
        raise AssertionError("bump should not be called")

    monkeypatch.setattr("subprocess.run", fake_run)
    assert bump_version_if_needed() is None


def test_bump_version_if_needed_performs_bump(monkeypatch):
    calls = []

    def fake_run(args, capture_output, text, check):
        calls.append(args)
        if args[:2] == ["bumpwright", "decide"]:
            return SimpleNamespace(stdout=json.dumps({"level": "patch"}))
        if args[:2] == ["bumpwright", "bump"]:
            return SimpleNamespace(stdout=json.dumps({"new_version": "1.2.3"}))
        raise AssertionError("unexpected command")

    monkeypatch.setattr("subprocess.run", fake_run)
    assert bump_version_if_needed(base="v1.2.0", head="HEAD", dry_run=True) == "1.2.3"
    # ensure both commands were invoked
    assert any(cmd[:2] == ["bumpwright", "decide"] for cmd in calls)
    assert any(cmd[:2] == ["bumpwright", "bump"] for cmd in calls)
