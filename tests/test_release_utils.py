from __future__ import annotations

import subprocess
from unittest.mock import call, patch

from flarchitect.utils.release import bump_version_if_needed


def test_bump_version_if_needed_no_change() -> None:
    """It should return ``None`` and avoid calling bump when no release is needed."""
    decide_cp = subprocess.CompletedProcess([], 0, stdout='{"level": null}')
    with patch(
        "flarchitect.utils.release.subprocess.run", return_value=decide_cp
    ) as run:
        assert bump_version_if_needed() is None
        run.assert_called_once_with(
            ["bumpwright", "decide", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )


def test_bump_version_if_needed_with_change() -> None:
    """It should apply a bump when a level is suggested."""
    decide_cp = subprocess.CompletedProcess([], 0, stdout='{"level": "patch"}')
    bump_cp = subprocess.CompletedProcess(
        [],
        0,
        stdout='{"old_version": "0.1.0", "new_version": "0.1.1", "level": "patch"}',
    )

    def side_effect(cmd, capture_output, text, check):  # type: ignore[override]
        if cmd[1] == "decide":
            return decide_cp
        if cmd[1] == "bump":
            return bump_cp
        raise AssertionError("Unexpected command")

    with patch(
        "flarchitect.utils.release.subprocess.run", side_effect=side_effect
    ) as run:
        assert bump_version_if_needed() == "0.1.1"
        assert run.mock_calls == [
            call(
                ["bumpwright", "decide", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            ),
            call(
                [
                    "bumpwright",
                    "bump",
                    "--level",
                    "patch",
                    "--format",
                    "json",
                    "--tag",
                ],
                capture_output=True,
                text=True,
                check=True,
            ),
        ]


def test_bump_version_if_needed_dry_run() -> None:
    """It should omit tagging when performing a dry run."""
    decide_cp = subprocess.CompletedProcess([], 0, stdout='{"level": "minor"}')
    bump_cp = subprocess.CompletedProcess(
        [],
        0,
        stdout='{"old_version": "0.1.0", "new_version": "0.2.0", "level": "minor"}',
    )

    def side_effect(cmd, capture_output, text, check):  # type: ignore[override]
        if cmd[1] == "decide":
            return decide_cp
        if cmd[1] == "bump":
            return bump_cp
        raise AssertionError("Unexpected command")

    with patch(
        "flarchitect.utils.release.subprocess.run", side_effect=side_effect
    ) as run:
        assert bump_version_if_needed(dry_run=True) == "0.2.0"
        assert run.mock_calls == [
            call(
                ["bumpwright", "decide", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            ),
            call(
                [
                    "bumpwright",
                    "bump",
                    "--level",
                    "minor",
                    "--format",
                    "json",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=True,
            ),
        ]
