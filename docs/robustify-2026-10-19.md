# Robustify report — flarchitect, 2026-10-19

## Summary
Reviewed response construction, request configuration caching, database filtering/pagination, and authentication/core paths. Confirmed XML status errors, configuration-cache collisions and lifetime leakage, and soft-delete collection inconsistencies. These are correctness fixes, unlike the preceding behavior-preserving performance passes. The separately authorized 1.5.8 release contains the completed performance work; these subsequent fixes are not part of that artifact.

## Baseline
Previous complete suite: 650 passed, one skipped, 111 warnings. Fresh baseline started before edits; lint and wheel/sdist build passed. Isolated Python 3.14 environment: `/tmp/flarchitect-fastify/venv`. Reproductions: XML requested status 404 returns HTTP 200; distinct same-name metadata sources return first/first instead of first/second; sequential requests within one app context retain the first configuration value; deleting the sole soft-deleted Widget leaves list `value=[]` but `total_count=1`; collection `include_deleted=1` is rejected as an invalid field under default filtering.

## Findings

### R-01 — XML responses discard the requested HTTP status
- **File:** flarchitect/utils/response_helpers.py:145-152
- **Severity:** major
- **Complexity:** trivial
- **Problem:** `response.status_code = status` is inside the JSON-only branch.
- **Why it matters:** XML errors appear as successful HTTP 200 responses; XML creation responses lose 201.
- **Fix direction:** Assign requested status after both serialization branches. Test JSON, application/xml and text/xml for success, creation, client/server errors. Update prior fastify tests that deliberately preserved this known behavior; explicitly record the intended behavior change.

### R-02 — Configuration cache conflates sources and can outlive a request
- **File:** flarchitect/utils/config_helpers.py:59-71,111-119
- **Severity:** major
- **Complexity:** moderate
- **Problem:** Cache keys use model/type names; distinct sources with identical names or different instance Meta share entries. Cache resides only on Flask g, whose app context may span several requests.
- **Why it matters:** Wrong model/schema settings or stale settings can be applied to a later request.
- **Fix direction:** Use source identity while retaining strong references, without relying on source hashability or equality (a small private identity-key wrapper is acceptable). Store the actual cache on the request object; retain g._flarch_cfg_cache only as an alias for existing introspection compatibility, refreshing alias on access. Preserve method, join, source reporting and positive-only caching. Test distinct same-name models/schema classes, instance Meta, unhashable/equality-custom sources, sequential requests within one app context and nested requests restoring outer cached results. Confirm existing cache-hit optimization still works.

### R-03 — Pagination counts hidden soft-deleted records
- **File:** flarchitect/database/operations.py:706-722
- **Severity:** major
- **Complexity:** trivial
- **Problem:** `count = query.count()` executes before `apply_soft_delete_filter`.
- **Why it matters:** Totals and navigation describe records that cannot appear in the response.
- **Fix direction:** Count the soft-delete-filtered query before pagination. Preserve ordering and other filtering. Test all-deleted, mixed visible/deleted, filters and multiple pages, plus include-deleted behavior.

### R-04 — Collection soft-delete filtering ignores model metadata
- **File:** flarchitect/database/operations.py:591-615
- **Severity:** major
- **Complexity:** moderate
- **Problem:** Collection lookups omit model= while single-row and delete operations honor per-model metadata.
- **Why it matters:** A model configured only through Meta can return deleted rows from its collection despite hiding them individually.
- **Fix direction:** Resolve soft-delete enabled/attribute/values against each represented model when applying its predicate, retaining global configuration as fallback. Preserve show-deleted opt-out, existing truthiness rules and behavior for models without the configured attribute. Test Meta-only configuration, global fallback, explicit model disable overriding global enable, and correct filtered totals. Do not redesign joins or access policy behavior.

### R-05 — include_deleted is parsed as a database field
- **File:** flarchitect/database/constants.py:OTHER_FUNCTIONS and database/utils.py filter argument handling
- **Severity:** minor
- **Complexity:** trivial
- **Problem:** `include_deleted` is not reserved when general filters are enabled.
- **Why it matters:** Documented opt-in collection requests return 400 instead of deleted records.
- **Fix direction:** Exclude include_deleted from ordinary field filtering through the existing reserved-argument mechanism; retain existing truthy-value semantics. Test normal collection include-deleted with filters enabled and alongside a real field filter.

## Deferred
- Zero-valued lookup identifiers are a candidate, not yet runtime-confirmed; investigate separately rather than expand this bounded set blindly.
- Callback payload extraction for non-snake styles and XML needs a separate contract decision for arbitrary custom responses.
- No unrelated schema construction, authentication, or query-loader redesign.

## Results
- R-01 implemented by the primary agent. Nine new XML assertions failed before the fix; the response-focused suite now passes 43 cases. Updated two earlier fastify test expectations from the deliberately preserved bug to the corrected XML transport status.
- R-02 implemented by the configuration sub-agent. Eight regression cases failed before the fix; nine new cases now pass, including retained-source lifetime. Combined focused configuration tests: 16 passed. Flask context lifetime was checked against its official documentation via Context7; request storage now controls ownership, with g only an introspection alias.
- R-03/R-04/R-05 implemented by the database sub-agent. All eight new endpoint cases failed before the fix; focused soft-delete/join/aggregation tests now pass 17 cases. Existing include_deleted truthiness is intentionally preserved, including non-empty "0".
- Primary agent reviewed each diff. Available inherited models were used because named Haiku/Sonnet models are unavailable.
- Full baseline: **650 passed, 1 skipped, 111 warnings** in 292.21 seconds. Full after-suite: **684 passed, 111 warnings**, no skips or failures, in 211.61 seconds. This comprises the original 650 passing tests, 33 new regression cases and the previously skipped RS256 test: installing Twine for the authorized release also installed cryptography, enabling that optional test. No regression is hidden by the changed skip count. Lint, package build and diff whitespace checks passed.
- Before-fix regression failures and baseline logs are retained locally in the original checkout under `docs/robustify-2026-10-19-evidence/`; runtime logs are not included in the release commit.
- Verification is local Python 3.14, not the full supported CI matrix. No browser check is required for these Python API fixes.

### Separate release status
The previously authorized performance release was committed as `749789cc056f58022eb1a5300351863826715c2c` and pushed to master. GitHub publication failed twice before upload because Sigstore's Rekor returned HTTP 502. The original release workflow artifacts were then uploaded directly with Twine. PyPI lists both 1.5.8 wheel and sdist with hashes matching those artifacts, and a clean install passed import/cache/response smoke checks. These robustness changes are subsequent local work, not in the published 1.5.8 files, and remain uncommitted. No new version has been published for them.

### Release consolidation
The fixes are now included in the prepared 1.5.9 release candidate on `deploy/2026-10-19-consolidated`, together with the PATCH schema refactor. The combined suite passes 691 tests (111 warnings). Published as 1.5.9 from commit `73a8d44`; see the deployify report for publication and installed-package verification. The prior paragraph records the state before consolidation.
