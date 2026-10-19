# Deployify report — flarchitect, 2026-10-19

## Summary
Prepared 1.5.9 with XML status, request configuration isolation and soft-delete collection fixes, plus the behavior-preserving PATCH schema refactor. All 691 tests pass. No publication was attempted: historical branch scope awaits user confirmation.

## Deployed
Not yet deployed. Candidate branch: `deploy/2026-10-19-consolidated`; this report accompanies the release-facing commit. Refactor commit `2e8ecc308fddf66815b43503ce85fdb9a1e02669` was merged normally in `90a90b9`. Starting master is `749789cc056f58022eb1a5300351863826715c2c`, protected by `backup/master-before-merge-20261019`.

The repository deployment seam is `.github/workflows/release.yml`: a version change pushed to master builds and publishes wheel and source distributions to PyPI. This is a library release; it has no production host, services, migrations or scheduled workers to restart. Existing PyPI release is 1.5.8; 1.5.9 was absent at preflight.

## Expected production inventory
| Component | Kind | Expected because | Verified by |
| --- | --- | --- | --- |
| master on origin | Source revision | Release workflow push trigger | Compare local and remote revisions after integration |
| 1.5.9 wheel | PyPI artifact | Release workflow | PyPI metadata, SHA-256 and fresh installation |
| 1.5.9 source archive | PyPI artifact | Release workflow | PyPI metadata and SHA-256 |
| Installed package | Consumer runtime | README installation instructions | Fresh install and API smoke checks |

## Health checks
| Check | How | Result | Status |
| --- | --- | --- | --- |
| Combined tests | pytest -q | 691 passed, 111 warnings in 227.01 seconds; Python 3.14 | Passed |
| Lint | ruff check --no-fix --no-cache . | All checks passed | Passed |
| Whitespace | git diff --check | No errors | Passed |
| Build | python -m build --no-isolation | Wheel and source archive built | Passed |
| Metadata | python -m twine check | Both artifacts passed | Passed |
| Archive contents | Inspect wheel and source archive | PATCH module included; changed wheel source matches checkout | Passed |
| Prior release CI | GitHub run 39312646419 | Completed successfully | Passed |
| New release CI | Not pushed | Awaiting integration | Pending |
| PyPI artifacts and installation | No upload attempted | 1.5.9 not published | Pending |

## Issues found and fixes applied
### D-01 — Historical branch scope needs confirmation
After fetching, 31 older remote branches remain outside master's ancestry. Each has one unique commit and is 8–739 commits behind master; their tips are from August–September 2025. `admin-dash` also exists locally (21 behind, one ahead). The mergify workflow requires confirmation before merging or skipping stale branches. They remain untouched. The current refactor merged without conflicts.

Original uncommitted robustness work was copied into the dedicated release worktree and preserved in the primary checkout. Local evidence logs remain there. No branch or worktree pruning is appropriate before master is successfully verified and pushed.

## Needs you
Confirm whether to publish today's robustness fixes and refactor while retaining the older branches untouched, or review those branches for inclusion first.

## Final status
Release candidate verified; publication pending branch-scope confirmation. Existing PyPI 1.5.8 unchanged.
