# Deployify report — flarchitect, 2026-10-19

## Summary
Prepared 1.5.9 with XML status, request configuration isolation and soft-delete collection fixes, plus the behavior-preserving PATCH schema refactor. All 691 tests pass. Published successfully through Trusted Publishing. Fresh installation and API smoke checks passed; seven redundant historical branches were pruned with recovery refs retained.

## Deployed
Published revision: `73a8d448607a4d70e7d4f2677f0777348888fe09`, pushed to `origin/master`. Release workflow run `39318359967` succeeded (20:19–20:20 UTC). Integration branch: `deploy/2026-10-19-consolidated`; the initial report accompanied the release-facing commit and was updated after publication. Refactor commit `2e8ecc308fddf66815b43503ce85fdb9a1e02669` was merged normally in `90a90b9`. Starting master is `749789cc056f58022eb1a5300351863826715c2c`, protected by `backup/master-before-merge-20261019`.

The repository deployment seam is `.github/workflows/release.yml`: a version change pushed to master builds and publishes wheel and source distributions to PyPI. This is a library release; it has no production host, services, migrations or scheduled workers to restart. PyPI 1.5.9 was absent at preflight and is now published.

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
| New release CI | GitHub run 39318359887 | Still running at report time; local complete suite passed | Pending |
| PyPI artifacts | Compare published SHA-256 against workflow artifacts | Both match; neither yanked | Passed |
| Fresh installation | pip install from PyPI in isolated environment | 1.5.9 installed; imports, compatibility alias, XML 404, request isolation and soft-delete endpoints passed | Passed |
| master on origin | Revision comparison | Published revision 73a8d44 | Passed |

## Issues found and fixes applied
### D-01 — Redundant historical branches
User authorized pruning after inspection. Seven branches had all unique commits patch-equivalent to commits in master (git cherry reports only minus entries). Deleted their remote branch names with expected-tip guards; kept local `backup/pruned-20261019/` recovery refs. Deleted redundant local `admin-dash` too. The remaining 24 historical remote branches have no exact-patch equivalence proof and were retained, excluded from this release. No old implementation was merged merely to tidy history.

Pruned remote branches:
- `409htq-arched/add-roles_accepted-decorator-with-tests`
- `admin-dash`
- `arched/add-default-fallbacks-for-openapi-metadata-gm01mi`
- `arched/add-tests-for-demo-applications-y0c8in`
- `arched/enable-cors-support-in-architect.py`
- `arched/update-test_authentication.py-for-test-client-requests`
- `codex/extend-paginate_query-to-skip-count-ao0aw0`

Also removed the clean, fully merged refactor worktree and branch after proving ancestry and origin/master parity. Original robustness input is preserved in a named git stash; evidence logs remain in the primary checkout. Backup refs remain local.

### D-02 — Fresh-install index propagation
The first pip request did not yet list 1.5.9, although PyPI version metadata already listed both artifacts. Retrying without cache against the public PyPI index succeeded. No package re-upload was needed.

Artifact hashes:
- Wheel: `0b08d3fec1474003f544ceb4cf3aca7c944d23c46550677a397d4b65d7c5ef81`
- Source archive: `a77f932f360b3343b8e9609e54d3647cedebf3ea509d12d7244224ba20db36c3`

## Needs you
No release action required. Retained historical branches can be reviewed separately if their work is wanted.

## Final status
Healthy-with-notes: PyPI 1.5.9 verified by hashes and fresh API smoke tests; full remote test matrix still running at report time.
