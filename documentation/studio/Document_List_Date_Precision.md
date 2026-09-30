---
draft: false
doc_id: d-20260930-133318-bcc07d
title: Document List Date Precision
added_date: "2026-09-30 13:33:18"
last_updated: "2026-09-30 13:33:18"
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Document List Date Precision

## Requirements

Use calendar dates for document browsing metadata because site updates do not need time-of-day ordering. Preserve complete source and by-ID timestamps. Remove creation-date fields from list inventories and retire added-based Recents. The owner approved this scope on 2026-09-30; test changes are outside it.

## Deliverables And Process

Collection reader/management manifests, the ordinary builder's in-memory flat rows, Search, Recents and Selected Documents project `YYYY-MM-DD` update dates. The ordinary flat index remains retired. Source/output consistency still compares source and by-ID update values at their original precision, with manifest date comparison at the projected boundary. Existing date-only sources remain valid; undated documents remain undated and are excluded from Recents. Recents becomes `docs_recent_v2` without a basis field or route setting. The two existing Selected Documents cache rows migrate without changing membership. [Generated Data Contracts](Generated_Data_Contracts.md#list-date-projections) owns maintained behavior.

Existing complete collection builds reconcile saved manifests before the ordinary Working build generates Recents and the explicit Search build refreshes its index. Builds skip registered media and Links work. Public runtime code follows the tracked site projection. Publish, commit and push remain separate actions.

## Delivery Steps

- [x] DP.0 — Readiness: inspect date consumers and receive owner approval.
- [x] DP.1 — Implement shared date projection, update consumers and remove added-based Recents.
- [x] DP.2 — Regenerate Working metadata and project changed public runtime code.
- [x] DP.3 — Review final code, generated deltas and focused evidence.
- [x] DP.4 — Record completion and remaining publication boundary.

Verification uses explicit Python/JavaScript lint, existing builder diagnostics, scoped generated inspection, site projection checks, static-site validation and whitespace checks. No tests, fixtures, browser automation or benchmarks are added or changed. Existing source/by-ID timestamps remain the authority for exact document evidence.

## Completion Evidence

Completed on 2026-09-30. Full collection dry runs addressed the risk of changing document bodies during a metadata migration. Works (244 documents), Concepts (246) and Moments (57) write builds changed their reader and management manifests only, with zero by-ID, semantic-token or Links changes and no warnings. Catalogue's 4,616 rows already had the current shape; its dry run reported no changes. A targeted Works dry run read one selected source, retained all 244 manifest rows and reported no output changes.

The ordinary Working dry run and write build read 41 sources, changed only Recents and retained all by-ID payloads, navigation, semantic tokens, backlinks and Links. Recents and the explicitly rebuilt Search index each contain 16 eligible documents. Both existing Selected Documents rows retain their membership and now cache calendar dates. Direct JSON inspection found no `added_date` in any collection manifest, only ten-character populated update dates and 17 intentionally undated Moments rows. A selected Works by-ID payload retained its complete creation and update timestamps.

Python lint passed for the ten changed Python files; JavaScript lint passed for the eight changed canonical modules. `bin/site-code-update` projected seven public modules; the local Works module stays excluded by the maintained inventory. The public route registry and site validator both retire `recent_basis`. `bin/site-code-update --check`, `bin/site-validate` and `git diff --check` passed. Static-site validation checks files, routes and code projection; it does not verify generated date formats or browser behavior.

The final code review checked the shared projection and original-precision source/by-ID comparison, date-only report sorting, removal of added-based Recents, targeted manifest requirements and the exact public code/config delta. No implementation findings remain. The full collection and ordinary write diagnostics establish that document payloads did not change; no extra body scan or test run was needed.

Preview and public document data still contain the previously published format. Run the normal Publish operation before committing or deploying the new public readers, so manifests, Recents and Selected Documents match them. Publish, browser review, commit, push and public deployment were not run as part of this implementation.
