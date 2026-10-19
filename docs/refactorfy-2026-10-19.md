# Refactorfy report — flarchitect, 2026-10-19

## Summary
Mapped the public package exports and dependencies between routing, authentication, schemas, database operations and documentation. Selected one bounded responsibility move: PATCH request-schema preparation belongs in the schema package, rather than documentation utilities. No new confirmed bug was found in the selected scope; known correctness fixes from the preceding robustify pass remain separate in the primary checkout.

### Dependency map
- Public entry point `flarchitect.Architect` is re-exported from `core.architect`; core consumes route factories, authentication and schema utilities.
- `schemas.utils` delegates model factories to `schemas.bases` and handles request deserialization.
- Before this change, PATCH deserialization imports `_prepare_patch_schema` from `specs.utils`, which also implements documentation examples, endpoint descriptions and metadata generation.
- `schemas.bases` separately imports endpoint/metadata helpers from `specs.utils`; that broader dependency remains unchanged.
- After the move, PATCH deserialization imports a schema-only module depending on stdlib `deepcopy` and Marshmallow. `specs.utils` keeps an explicit alias for the previous import path; no public export is removed.

## Baseline
- Starting primary branch: `master`, commit `749789cc056f58022eb1a5300351863826715c2c` (published 1.5.8 performance release).
- Primary checkout has uncommitted robustify changes to database constants/operations, configuration/response helpers, response tests and new report/tests. They are outside this refactor's files and were neither transferred nor modified.
- Dedicated worktree: `/mnt/storage_drive/Projects/flarchitect-refactor-2026-10-19`; branch `refactor/2026-10-19-structure`. Worktree initially clean. All subsequent repository operations run here.
- Fresh complete pytest baseline started before edits. Lint (`ruff check --no-fix --no-cache .`) and wheel/sdist build passed using `/tmp/flarchitect-fastify/venv/bin/python` (Python 3.14).
- Behavior snapshot covers None, schema class and instance inputs, generated class name/module, field flags, metadata, valid/invalid loads, nested inputs and unchanged original fields. SHA256: `1afbe53f56d00c751f4f8b32efba1e33a258ef0b72b22afe82d945c0d34f87cc`.
- Preparation timing: median of seven 1,000-call batches, 67.271 microseconds/call. Measurement artifacts are local under `/tmp/flarchitect-refactor/`, not committed logs.
- Version source is `pyproject.toml` (1.5.8); release policy publishes version changes on master. This internal refactor gets no version bump and no publication.

## Findings

### R-01 — Move PATCH schema preparation into the schema package (minor, moderate)
- **File:** flarchitect/specs/utils.py:637-678; flarchitect/schemas/utils.py:85-88; new flarchitect/schemas/patch.py
- **Category:** structure
- **Problem:** Runtime `deserialise_data` imports `_prepare_patch_schema` from documentation utilities, despite the helper containing only schema-copying and field-optionalization logic.
- **Why it matters:** Request validation is owned by the documentation implementation, obscuring where PATCH behavior should be maintained and coupling runtime changes to a 1,400-line documentation utility module.
- **Fix direction:** Move the helper body unchanged to `schemas/patch.py` with its `deepcopy` and `Schema` imports. Replace the old definition in `specs.utils` with an explicit module-level import alias retaining `_prepare_patch_schema`; remove only the now-unused direct `deepcopy` import there (keep `import copy`, still used). Change the function-local import in `schemas.utils` to the new module, retaining lazy timing. Do not change class naming, Meta handling, field copying, return annotations, or error behavior, even where surprising. No compatibility wrapper call is added.
- **Preservation check:** Assert both import paths resolve to the same function; compare old/new function AST; validate class/instance input behavior, required/nullable flags, independent deep copies, original-field immutability, metadata and nested validation. Exercise PATCH deserialization. Compare saved complete behavior snapshot and timings. Run full tests, lint, build and wheel content check.

## Execution order
1. Capture released-commit baseline and snapshots in the dedicated worktree.
2. One fixer moves the helper, compatibility alias and sole runtime import together, then adds focused regression coverage.
3. Primary agent reviews the complete move against the original AST, reruns snapshots/timing/checks, completes this report and commits only the task files.

## Not touching
- Known robustify changes in primary checkout are not part of this branch; merge/cherry-pick this refactor later alongside them if desired.
- JWT signing/verifying helpers duplicate selection policy but retaining wrappers would add an extra call on a hot path for limited gain; defer.
- Role normalizers have explicitly tested differences in coercion, empty lists and default matching; do not merge them.
- API-key matching paths have differing exception/callable semantics; no speculative deduplication.
- Small pre-process hooks have different public keyword names; compatibility wrappers add indirection for little benefit.
- Schema factory wrappers deliberately synchronize monkeypatchable cache references.
- Broader documentation-module extraction risks public imports, monkeypatch targets and cycles; not justified by this bounded task.
- The generated schema's class-input naming and Meta behavior are preserved, not silently corrected.

## Results
- R-01 implemented by the schema fixer, then reviewed by the primary agent. The old and new helper definitions have identical ASTs, including annotations, docstring and full body. The old import is an alias to the same function, not a wrapper.
- Seven new preservation cases added; focused schema tests passed nine cases including existing coverage.
- Complete behavior snapshots are equal, with the same SHA256 recorded above. Class/instance naming, generated module, Meta handling, validation errors and original-field state are unchanged.
- Initial separate timing runs: 67.271 -> 67.939 microseconds/call (about 1% variation). Follow-up interleaved comparison, 20 alternating 1,000-call batches per implementation: original median 64.959 microseconds (range 63.816–68.107), moved median 65.057 (range 63.883–69.285). The 0.15% median difference is within overlapping run variation; no measurable regression or added runtime wrapper/allocation was found. No performance improvement is claimed.
- Import-reference sweep shows one implementation, the legacy compatibility alias and the runtime schema import. No orphaned runtime call site remains.
- Baseline full suite: **651 passed, 112 warnings** in 211.37 seconds. Updated full suite: **658 passed, 112 warnings** in 213.02 seconds. All seven new cases passed; no failures or additional warnings. Full-suite duration is not used as a performance measure. Lint and wheel/sdist build pass; wheel content includes `flarchitect/schemas/patch.py`.
- Python 3.14 was tested; the full CI version matrix was not run here. No browser check is needed for this internal Python-only move.
- No bugs were silently fixed, and no version bump is appropriate. Raw measurements and test logs remain under `/tmp/flarchitect-refactor/`; task commits contain no generated logs.
- Commit scope: helper move, two import changes, preservation tests and this report. No push, merge or release; primary checkout remains untouched.
