"""Release helpers for BumpWright integration.

This module wraps the ``bumpwright`` command-line tool to avoid accidental
version bumps. The helper verifies whether a bump is required before applying
it, returning ``None`` when no release is needed.
"""

from __future__ import annotations

import json
import subprocess


def bump_version_if_needed(base: str | None = None, head: str = "HEAD", dry_run: bool = False) -> str | None:
    """Bump project version only when BumpWright recommends a release.

    The function first runs ``bumpwright decide``. If no bump level is
    suggested, ``None`` is returned and no version files are touched. When a
    level is suggested, ``bumpwright bump`` is executed with that level and the
    new version is returned.

    Args:
        base: Base git reference for comparison. When ``None``, BumpWright
            selects the last release commit automatically.
        head: Head git reference for comparison. Defaults to ``HEAD``.
        dry_run: When ``True``, perform a dry run without modifying any files.

    Returns:
        The new version string if a bump is applied; otherwise ``None``.

    Raises:
        subprocess.CalledProcessError: If either BumpWright command fails.
    """

    decide_cmd = ["bumpwright", "decide", "--format", "json"]
    if base:
        decide_cmd.extend(["--base", base])
    if head:
        decide_cmd.extend(["--head", head])
    result = subprocess.run(decide_cmd, capture_output=True, text=True, check=True)
    level = json.loads(result.stdout).get("level")
    if level in (None, "None"):
        return None

    bump_cmd = ["bumpwright", "bump", "--level", str(level), "--format", "json"]
    if base:
        bump_cmd.extend(["--base", base])
    if head:
        bump_cmd.extend(["--head", head])
    if dry_run:
        bump_cmd.append("--dry-run")
    bump_res = subprocess.run(bump_cmd, capture_output=True, text=True, check=True)
    data = json.loads(bump_res.stdout)
    return data.get("new_version")
