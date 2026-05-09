---
doc_id: site-change-log
title: Site Change Log
added_date: 2026-04-24
last_updated: "2026-05-09 17:51"
parent_id: ""
sort_order: 270
---
# Site Change Log

This page keeps the current site and non-search Studio change history compact enough to edit and review directly.
Older entries are kept in dated archive child docs so existing links to this document remain stable.

Archives:

- [Site Change Log Archive: May 2026](/docs/?scope=studio&doc=site-change-log-2026-05)
- [Site Change Log Archive: April 2026](/docs/?scope=studio&doc=site-change-log-2026-04)
- [Site Change Log Archive: March 2026 And Earlier](/docs/?scope=studio&doc=site-change-log-2026-03-and-earlier)

## [2026-05-09] Completed tag write-server structural review

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented Slice 8 closeout for the tag write-server structural review.
`scripts/tag_registry_mutations.py` now owns canonical tag assignment rewrites for rename and delete flows, and `scripts/studio/tag_write_server.py` calls extracted owners through explicit module namespaces while remaining the localhost HTTP orchestration layer.
The service name remains `tag_write_server.py`; a future `analytics_server.py` rename is deferred until broader Analytics metadata or scoring writes exist.

**Files changed/docs:**

- `scripts/tag_registry_mutations.py`
- `scripts/studio/tag_write_server.py`
- `tests/python/test_tag_registry_mutations.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, request payloads, response payload keys, dry-run behavior, backup behavior, and write allowlists are unchanged.
The next structural-review work starts with Priority 4 rather than adding more cleanup to the tag server.

## [2026-05-09] Advanced tag write-server transaction ownership

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented Slice 7 of the tag write-server structural review.
`scripts/tag_write_transactions.py` now owns timestamped backup names, single-file JSON writes with backup, multi-file JSON writes with shared-stamp backups, temporary-file cleanup, and rollback for replaced or newly created files after failed multi-file writes.
`scripts/studio/tag_write_server.py` still owns HTTP request parsing, source artifact loading, request value sanitization, preview/apply response mapping, dry-run write suppression, write allowlist checks, local logging, and Studio Activity append timing.
The focused tag write-transaction test is included in the `quick` run-checks profile.

**Files changed/docs:**

- `scripts/tag_write_transactions.py`
- `scripts/studio/tag_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_tag_write_transactions.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, request payloads, response payload keys, dry-run behavior, backup naming behavior, and write allowlists are unchanged.
The remaining Slice 8 work can focus on handler cleanup and final boundary decisions rather than low-level file transaction mechanics.

## [2026-05-09] Advanced tag write-server promotion and demotion ownership

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented Slice 6 of the tag write-server structural review.
`scripts/tag_promotion_mutations.py` now owns alias promotion planning, canonical-tag creation-versus-existing decisions, promoted alias removal, tag demotion target validation, demoted canonical removal, demotion assignment rewrites, alias-reference rewrites through the alias mutation owner, and promotion/demotion summary text.
`scripts/studio/tag_write_server.py` still owns HTTP request parsing, source artifact loading, request value sanitization, preview/apply response mapping, dry-run write suppression, write allowlist checks, writes/backups, local logging, and Studio Activity append timing.
The focused promotion-mutation test is included in the `quick` run-checks profile.

**Files changed/docs:**

- `scripts/tag_promotion_mutations.py`
- `scripts/studio/tag_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_tag_promotion_mutations.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, request payloads, response payload keys, dry-run behavior, backup/write behavior, and write allowlists are unchanged.
Promotion and demotion edge cases now have direct-module coverage before backup/write helpers are moved.

## [2026-05-09] Advanced tag write-server registry and alias ownership

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented Slice 5 of the tag write-server structural review.
`scripts/tag_registry_mutations.py` now owns registry import add/merge/replace behavior, duplicate import compaction, canonical tag edit/delete planning, canonical rename guards, and registry import/mutation summary text.
`scripts/tag_alias_mutations.py` now owns alias import add/merge/replace behavior, duplicate alias compaction, alias edit/delete planning, registry-target validation for aliases, alias target constraints, alias target rewrite helpers, redundant alias cleanup, and alias mutation summary text.
`scripts/studio/tag_write_server.py` still owns HTTP request parsing, source artifact loading, cross-artifact endpoint orchestration, dry-run write suppression, write allowlist checks, writes/backups, local logging, and Studio Activity append timing.
The focused registry and alias mutation tests are included in the `quick` run-checks profile.

**Files changed/docs:**

- `scripts/tag_registry_mutations.py`
- `scripts/tag_alias_mutations.py`
- `scripts/studio/tag_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_tag_registry_mutations.py`
- `tests/python/test_tag_alias_mutations.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, request payloads, response payload keys, dry-run behavior, backup/write behavior, and write allowlists are unchanged.
Registry and alias edge cases now have direct-module coverage before promotion and demotion planners are moved.

## [2026-05-09] Advanced tag write-server assignment-service ownership

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented Slice 4 of the tag write-server structural review.
`scripts/tag_assignment_service.py` now owns tag assignment save planning, work override planning, assignment import preview/apply decisions, and assignment import response summary text.
`scripts/studio/tag_write_server.py` still owns HTTP request parsing, source artifact loading, dry-run write suppression, write allowlist checks, assignment writes/backups, local logging, and Studio Activity append timing.
The focused assignment-service test is included in the `quick` run-checks profile.

**Files changed/docs:**

- `scripts/tag_assignment_service.py`
- `scripts/studio/tag_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_tag_assignment_service.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, request payloads, response payload keys, dry-run behavior, backup/write behavior, and write allowlists are unchanged.
Series and work assignment behavior now has direct-module coverage before registry, alias, promotion, and demotion planners are moved.

## [2026-05-09] Advanced tag write-server source-model ownership

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented Slice 3 of the tag write-server structural review.
`scripts/tag_source_model.py` now owns tag source artifact path constants, JSON loading defaults, tag id/slug/group/alias/manual-weight validation, assignment tag normalization, import filename sanitization, import registry/alias validation, import assignment row validation, normalized assignment comparison helpers, and series-index membership extraction.
`scripts/studio/tag_write_server.py` still owns HTTP orchestration, endpoint artifact selection, write allowlist checks, backups/writes, local logs, and response status mapping.
The focused source-model test is included in the `quick` run-checks profile.

**Files changed/docs:**

- `scripts/tag_source_model.py`
- `scripts/studio/tag_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_tag_source_model.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, payloads, dry-run behavior, backup/write behavior, and write allowlists are unchanged.
Later assignment, registry, alias, promotion, and demotion planner slices can now call one source-model owner instead of sharing validation and loading logic through the HTTP server.

## [2026-05-09] Started tag write-server structural review slices

**Status:** implemented

**Area:** Studio / Analytics / scripts / maintainability

**Summary:**
Implemented the first tag write-server structural review slice.
`scripts/tag_routes.py` now owns tag local-service endpoint constants, POST route inventory, and OPTIONS coverage, while `scripts/studio/tag_write_server.py` keeps HTTP orchestration and dispatches through `Handler.POST_HANDLERS`.
The focused route test is included in the `quick` run-checks profile.

**Files changed/docs:**

- `scripts/tag_routes.py`
- `scripts/studio/tag_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_tag_routes.py`
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Endpoint URLs, payloads, write behavior, dry-run behavior, backups, and allowlists are unchanged.
Future tag endpoint additions now have one route inventory plus a dispatch coverage test instead of duplicated literals in preflight and POST handling.

## [2026-05-09] Moved tag Studio routes under Analytics

**Status:** implemented

**Area:** Studio / Analytics / routing

**Summary:**
Moved the tag registry, tag aliases, tag groups, series tags, and series tag editor pages from top-level Studio routes into the Analytics namespace.
The old routes were removed without compatibility redirects or aliases, and route config, activity metadata, dashboard links, docs, and smoke-test route references now use `/studio/analytics/...`.

**Files changed/docs:**

- `studio/analytics/tag-registry/index.md`
- `studio/analytics/tag-aliases/index.md`
- `studio/analytics/tag-groups/index.md`
- `studio/analytics/series-tags/index.md`
- `studio/analytics/series-tag-editor/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/data/activity_contract.json`
- [Analytics Tag Route Cleanup Request](/docs/?scope=studio&doc=site-request-analytics-tag-route-cleanup)
- [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server)

**Impact:**
Analytics route ownership is now explicit before the tag write-server structural review continues.
Local bookmarks and any missed hardcoded links to the old `/studio/tag-*`, `/studio/series-tags/`, or `/studio/series-tag-editor/` routes now fail instead of being masked by aliases.

## [2026-05-09] Advanced docs-management server structural review slices

**Status:** implemented

**Area:** Studio / Docs Viewer / scripts / maintainability

**Summary:**
Advanced the priority-2 docs-management server sequence in the script structural review through Slice 8 closeout.
The extracted owners now cover endpoint route inventory, docs source-model helpers, generated Docs Viewer read helpers, docs-specific Studio Activity row construction, write/rebuild follow-through, management mutation planning, and staged source-import orchestration.
The closeout removed temporary HTML-import wrapper aliases, made server call sites use explicit extracted-module namespaces, and recorded the final boundary between the docs-management server and the separate import/export adapter review.

**Files changed/docs:**

- `scripts/docs/docs_management_server.py`
- `scripts/docs/docs_management_routes.py`
- `scripts/docs/docs_source_model.py`
- `scripts/docs/docs_generated_reads.py`
- `scripts/docs/docs_activity.py`
- `scripts/docs/docs_write_rebuild.py`
- `scripts/docs/docs_management_mutations.py`
- `scripts/docs/docs_import_source_service.py`
- `tests/python/test_docs_management_routes.py`
- `tests/python/test_docs_source_model.py`
- `tests/python/test_docs_generated_reads.py`
- `tests/python/test_docs_activity.py`
- `tests/python/test_docs_write_rebuild.py`
- `tests/python/test_docs_management_mutations.py`
- `tests/python/test_docs_import_service.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Docs Management Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-docs-management-server)

**Impact:**
Endpoint URLs and payload behavior are unchanged, but route, source-model, generated-read, activity-row, write/rebuild, mutation-planning, and source-import orchestration responsibilities now have focused module owners and direct tests.

## [2026-05-09] Renamed docs source roots

**Status:** implemented

**Area:** Docs Viewer / scripts / source layout

**Summary:**
Renamed the docs source directories to remove the `_src` suffix and moved docs scope configuration into a shared script-owned JSON file so the builder, docs-management server, HTML importer, and live watcher use the same scope roots.

**Files changed/docs:**

- `_docs/`
- `_docs_library/`
- `_docs_analysis/`
- `_docs_catalogue/`
- `scripts/docs/docs_scopes.json`
- `scripts/docs/docs_scope_config.py`
- `scripts/build_docs.rb`
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Documentation and script references now use `_docs`, `_docs_library`, `_docs_analysis`, and `_docs_catalogue`.
The main residual risk is external local commands or notes outside the repo that still refer to the old directory names.

## [2026-05-09] Closed catalogue write-server structural review slices

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the fourteenth and final catalogue write-server slice of the script structural review.
The closeout removed stale local server surface, kept endpoint paths owned by `scripts/catalogue_routes.py`, and refreshed the module ownership docs after the delete/publication transaction extractions.

**Files changed/docs:**

- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
The write server remains the local HTTP orchestration layer, while source mutation, lookup refresh, cleanup, delete/publication planning, transactions, activity, routes, prose import, and save-build follow-through now have explicit module owners and focused test coverage.

## [2026-05-09] Extracted catalogue delete and publication apply orchestration

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the thirteenth implementation slice of the script structural review by moving delete apply planning, publication source/build orchestration, and cleanup transaction execution out of `scripts/studio/catalogue_write_server.py`.
The write server still owns endpoint request parsing, final response assembly, and Studio Activity append timing.

**Files changed/docs:**

- `scripts/catalogue_delete_plans.py`
- `scripts/catalogue_publication.py`
- `scripts/catalogue_transactions.py`
- `scripts/studio/catalogue_write_server.py`
- `tests/python/test_catalogue_delete_plans.py`
- `tests/python/test_catalogue_publication.py`
- `tests/python/test_catalogue_transactions.py`
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
Delete and publication apply paths now have direct-module coverage for payload planning, cleanup transaction backups, rollback behavior, search rebuild hooks, and moment-specific response keys.
Destructive endpoint response contracts and activity logging remain visible in the local write server.

## [2026-05-09] Extracted catalogue delete and publication preview planners

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the twelfth implementation slice of the script structural review by moving delete preview planning into `scripts/catalogue_delete_plans.py` and publication preview planning into `scripts/catalogue_publication.py`.
The write server still owns HTTP request handling, apply transaction execution, endpoint-specific allowlist checks, response assembly, and Studio Activity timing.

**Files changed/docs:**

- `scripts/catalogue_delete_plans.py`
- `scripts/catalogue_publication.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_delete_plans.py`
- `tests/python/test_catalogue_publication.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
Delete and publication preflight behavior now has direct-module coverage before the later apply-transaction extraction.
Destructive apply ordering and write allowlists remain in the local write server.

## [2026-05-09] Extracted catalogue source write executor

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the eleventh implementation slice of the script structural review by adding a shared source JSON write executor to `scripts/catalogue_transactions.py`.
Save, create, bulk-save, and workbook-import apply handlers still perform endpoint-specific allowlist checks in `scripts/studio/catalogue_write_server.py`, then delegate payload-map validation, dry-run write suppression, atomic JSON writes, rollback behavior, and backup response-path formatting to the transaction module.

**Files changed/docs:**

- `scripts/catalogue_transactions.py`
- `scripts/studio/catalogue_write_server.py`
- `tests/python/test_catalogue_transactions.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
Source-write mechanics for save/create-style flows now have direct executor coverage while endpoint response assembly, lookup/build/activity timing, and write allowlist visibility remain in the write server.

## [2026-05-08] Extracted catalogue source mutation planners

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the tenth implementation slice of the script structural review by moving pure save/create source mutation planning into `scripts/catalogue_source_mutation.py`.
The write server still owns file reads, allowlist checks, transaction writes/backups, lookup/build/activity orchestration, and response assembly, while the new module owns source record normalization, changed-field calculation, validation against loaded source records, generated detail section-id planning, series member-work update planning, and source JSON payload construction.

**Files changed/docs:**

- `scripts/catalogue_source_mutation.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_source_mutation.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
Work, work-detail, series, and moment save/create source-shape behavior now has direct-module coverage without running the local HTTP service.
Endpoint write timing and response contracts remain unchanged.

## [2026-05-08] Extracted catalogue save-build follow-through helper

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the ninth implementation slice of the script structural review by moving common save-time public-build follow-through logic for work, work-detail, series, and moment saves into `scripts/catalogue_save_build.py`.
The write server still chooses endpoint-specific build targets and appends Studio Activity rows, while the helper owns `build_requested`, `build_skipped`, no-public-artifact skips, and the common build runner call.

**Files changed/docs:**

- `scripts/catalogue_save_build.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_save_build.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
Save-time build response decisions now have direct-module coverage for published saves, draft skips, no-public-artifact skips, moment message-key payloads, and build-failure payload preservation.
Endpoint response contracts remain unchanged.

## [2026-05-08] Extracted catalogue lookup refresh helpers

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the eighth implementation slice of the script structural review by moving Studio catalogue lookup refresh execution into `scripts/catalogue_lookup_refresh.py`.
The write server keeps refresh timing, response insertion, local service logging, and Studio Activity append timing, while the extracted module owns full and focused refresh writes plus the `lookup_refresh` result payload shape.
The series-save member-work fallback now correctly forces a full lookup refresh when the save changes work membership.

**Files changed/docs:**

- `scripts/catalogue_lookup_refresh.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_lookup_refresh.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)

**Impact:**
Lookup refresh execution now has direct-module coverage for full, work, detail, and series refresh result payloads, and the write server is left with endpoint orchestration rather than payload-writing loops.

## [2026-05-08] Split catalogue write-server slice plan

**Status:** documented

**Area:** Studio / scripts / maintainability

**Summary:**
Moved the detailed `scripts/studio/catalogue_write_server.py` restructuring notes out of the high-level script structural review request into a dedicated child doc.
The new slice doc records implemented Slices 1-7 and adds the foreseeable Slice 8-14 path for lookup refresh execution, save/build follow-through, source mutation planners, save/create transaction execution, delete/publication planners, delete/publication apply orchestration, and final handler cleanup.

**Files changed/docs:**

- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Catalogue Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-catalogue-write-server)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The parent request stays readable as a broad structural-review brief, while the catalogue write-server work now has an explicit completion plan and risk sequence.

## [2026-05-08] Cleaned catalogue write-server route dispatch

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the seventh implementation slice of the script structural review by moving catalogue write-service POST and OPTIONS route inventory into `scripts/catalogue_routes.py` and replacing the write server's long POST route cascade with a single handler dispatch table.
Endpoint URLs, request parsing, handler bodies, and response payload contracts remain unchanged.

**Files changed/docs:**

- `scripts/catalogue_routes.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_routes.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

**Impact:**
The route inventory is now direct-testable, activity profile endpoints are checked against known POST routes, and the write server keeps only the method-name dispatch table that points to its local handler methods.

## [2026-05-08] Extracted catalogue prose import helpers

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the sixth implementation slice of the script structural review by moving staged prose import and draft moment source import helpers out of the catalogue write server.
`scripts/catalogue_prose_import.py` now owns prose import target normalization, staged Markdown validation, preview payloads, no-backup prose writes, and draft moment import metadata/prose application.
The write server keeps endpoint conflict handling, allowlist set ownership, local logging, moment-import Studio Activity append timing, and response assembly.

**Files changed/docs:**

- `scripts/catalogue_prose_import.py`
- `scripts/catalogue_transactions.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_prose_import.py`
- `tests/python/test_catalogue_transactions.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

**Impact:**
Staged prose preview/apply behavior and draft moment import application now have focused direct-module coverage.
The endpoint payloads remain server-assembled, and no-backup prose writes now use the same transaction helper module that owns other catalogue write mechanics.

## [2026-05-08] Consolidated moment cleanup transaction path

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the fifth implementation slice of the script structural review by consolidating the duplicated moment delete/unpublish cleanup transaction path in the catalogue write server.
Moment index cleanup payload mutation now lives in `scripts/catalogue_cleanup.py`, while the write server keeps endpoint-specific source and generated write allowlist checks visible before any writes occur.

**Files changed/docs:**

- `scripts/catalogue_cleanup.py`
- `scripts/studio/catalogue_write_server.py`
- `tests/python/test_catalogue_cleanup.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

**Impact:**
Moment delete and moment unpublish now share one server-side transaction helper for metadata writes, generated moment cleanup, moments-index updates, file deletion, search rebuild, backup, and restore behavior.
The cleanup module owns the moment index payload mutation directly, and targeted cleanup tests pin that behavior.

## [2026-05-08] Extracted catalogue cleanup helpers

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the third implementation slice of the script structural review by moving generated public-artifact cleanup discovery, allowlist checks, generated JSON cleanup payload mutation, and cleanup file deletion helpers out of the catalogue write server.
The write server now calls those helpers through the explicit `catalogue_cleanup.*` namespace while keeping HTTP handlers, source writes, transaction backup timing, and response assembly in place.
Shared catalogue id-list and detail-uid normalization now lives in `scripts/catalogue_source.py` so the extraction does not duplicate request/source identity helpers.

**Files changed/docs:**

- `scripts/catalogue_cleanup.py`
- `scripts/catalogue_source.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_cleanup.py`
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

**Impact:**
Generated cleanup behavior now has a direct module owner and focused coverage for preview counts, allowlist rejection, and generated payload mutation.
Delete and unpublish endpoint contracts remain unchanged; transaction-helper extraction remains a later slice.

## [2026-05-08] Extracted catalogue activity helpers

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the second implementation slice of the script structural review by moving catalogue-specific Studio Activity profiles, context normalization, and row builders out of the catalogue write server.
Added a small shared route-constant module so activity profiles and route dispatch no longer duplicate endpoint strings.
Switched the write server to namespaced `activity.*`, `invalidation.*`, and `routes.*` references so extracted helpers are not re-presented as server-owned names.
Updated the structural-review request to make that the required slice discipline: conservative slices should still close with clean ownership, not deferred cleanup.

**Files changed/docs:**

- `scripts/catalogue_activity.py`
- `scripts/catalogue_routes.py`
- `scripts/studio/catalogue_write_server.py`
- `tests/python/test_studio_activity_context.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

**Impact:**
`scripts/catalogue_activity.py` now owns the catalogue activity contract helpers while the write server keeps endpoint orchestration and append timing.
`scripts/catalogue_routes.py` is the single endpoint path source, and the write server now uses explicit module-qualified references instead of re-exporting moved helper names.
The focused activity test now exercises the extracted activity and invalidation modules directly.

## [2026-05-08] Extracted catalogue invalidation rules

**Status:** implemented

**Area:** Studio / scripts / maintainability

**Summary:**
Completed the first implementation slice of the script structural review by moving catalogue lookup and moment-build invalidation rules out of the catalogue write server.

**Files changed/docs:**

- `scripts/catalogue_invalidation.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/run_checks.py`
- `tests/python/test_catalogue_invalidation.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

**Impact:**
`scripts/catalogue_invalidation.py` now owns the field-to-derived-artifact registries and pure invalidation helpers.
The write server now calls those helpers through the `invalidation.*` namespace, so endpoint behavior and response payloads remain stable while the module boundary becomes clearer.

## [2026-05-08] Added script structural review request

**Status:** proposed

**Area:** Studio / scripts / maintainability

**Summary:**
Added a change request for reviewing structurally confusing large scripts, led by `scripts/studio/catalogue_write_server.py`.

**Files changed/docs:**

- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
The new request frames modularisation as a responsibility-boundary problem rather than a file-size target.
It identifies other review candidates, including the docs and tag write servers, `generate_work_pages.py`, and `catalogue_json_build.py`, while keeping behavior-preserving extraction and targeted tests as the default path.

## [2026-05-08] Moved Studio Activity link to Studio resources

**Status:** implemented

**Area:** Studio / navigation

**Summary:**
Moved the Activity link from the Catalogue dashboard admin block into the Studio home Resources section.

**Files changed:**

- `studio/index.md`
- `studio/catalogue/index.md`

**Impact:**
The Studio Activity report now sits with other cross-Studio resources on `/studio/`, and `/studio/catalogue/` no longer shows a separate Admin heading.

## [2026-05-08] Cleaned up moment lookup-refresh naming

**Status:** implemented

**Area:** Studio / catalogue write server / activity reporting

**Summary:**
Completed the Studio Activity Follow-Ups `lookup_refresh` naming cleanup for moment writes.

**Files changed/docs:**

- `scripts/studio/catalogue_write_server.py`
- `assets/studio/data/activity_contract.json`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups)

**Impact:**
Moment save responses now expose `moment_build_invalidation` instead of a misleading `lookup_refresh` object, and moment publication no longer runs the shared Studio lookup refresh path.
Work, work-detail, and series responses still use `lookup_refresh` for actual Studio lookup payload writes.

## [2026-05-08] Closed Studio unified activity request

**Status:** implemented

**Area:** Studio / activity reporting / docs

**Summary:**
Closed the unified Studio activity log request and inventory after Batch D cleanup, and moved remaining optional expansion work into a separate follow-up request.

**Files changed/docs:**

- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups)

**Impact:**
The original request now reads as a completed implementation record.
Bulk-save activity, readiness prose/media rows, background watcher attribution, terminal-script context, future writable review surfaces, R2 Studio-triggered media activity, and the `lookup_refresh` naming cleanup are tracked outside the closed request.

## [2026-05-08] Retired split Studio activity reports

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Completed Batch D of the unified Studio activity log by removing the old split activity report pages and feeds.

**Files changed:**

- retired split activity route files
- retired split activity page controllers
- retired split activity feed writer modules
- `scripts/studio/catalogue_write_server.py`
- `scripts/catalogue_json_build.py`
- retired split activity feed artifacts
- `tests/python/test_studio_activity_context.py`
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio Data Models](/docs/?scope=studio&doc=data-models-studio)

**Impact:**
`/studio/activity/` is now the only active Studio activity report.
The retired routes, dashboard links, config keys, read keys, feed readers, feed writer modules, and old feed artifacts were removed rather than redirected.

## [2026-05-08] Completed Batch C Studio activity logging

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Completed the remaining Batch C unified activity coverage for docs import/export/import apply, docs broken-links audits, Studio audits, and tag write actions.

**Files changed:**

- `assets/studio/data/activity_contract.json`
- `scripts/studio_activity.py`
- `scripts/docs/docs_management_server.py`
- `scripts/studio/audit_service.py`
- `scripts/studio/tag_write_server.py`
- `assets/studio/js/activity-log.js`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/studio-audits.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-studio-save.js`
- `assets/studio/js/tag-registry-service.js`
- `assets/studio/js/tag-aliases-service.js`
- `tests/python/test_studio_activity_feed.py`
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Audit Service](/docs/?scope=studio&doc=scripts-studio-audit-service)
- [Studio Data Export](/docs/?scope=studio&doc=studio-data-export)
- [Studio Data Import](/docs/?scope=studio&doc=studio-data-import)
- [Series Tags](/docs/?scope=studio&doc=series-tags)
- [Tag Editor](/docs/?scope=studio&doc=tag-editor)
- [Tag Registry](/docs/?scope=studio&doc=tag-registry)
- [Tag Aliases](/docs/?scope=studio&doc=tag-aliases)

**Impact:**
The unified activity log now records covered Batch C utility writes and report runs with contract-backed page/action context.
Preview-only and cancelled confirmation flows stay excluded, while confirmed writes and output-generating actions emit concise modal details and affected record groups.

## [2026-05-08] Started Batch C Studio activity logging for catalogue-service actions

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Started Batch C by wiring workbook import apply, moment import apply, and project-state report generation into the unified Studio activity contract and feed.

**Files changed:**

- `assets/studio/data/activity_contract.json`
- `scripts/studio/catalogue_write_server.py`
- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/project-state.js`
- `tests/python/test_studio_activity_context.py`
- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The first Batch C slice now reports durable import/report actions while keeping preview-only commands excluded.
Workbook import adds import and lookup-refresh rows, moment import adds a source-import row, and project-state generation adds a report row with summary counts.
Docs import/export, audits, and tag writes remain in the rest of Batch C.

## [2026-05-08] Extended Studio activity logging to catalogue create, delete, and publication actions

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Completed Batch B for unified Studio activity logging by wiring catalogue work/detail/series create actions, work/detail/series/moment delete actions, and work/detail/series/moment publish/unpublish actions into the structured activity contract and feed.

**Files changed:**

- `assets/studio/data/activity_contract.json`
- `scripts/studio/catalogue_write_server.py`
- `assets/studio/js/studio-activity-context.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `tests/python/test_studio_activity_context.py`
- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Create, delete, publish, and unpublish flows now preserve the original Studio route/control context through confirmation flows and emit unified activity rows for source writes, lookup refreshes where applicable, public builds, cleanup, and search updates.
Moment creation remains with import/apply coverage because the current workflow is staged import rather than normal create mode.

## [2026-05-08] Added Studio activity action profiles

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Added a thin server-side action-profile layer for catalogue-side Studio Activity logging before expanding into create, delete, and publication actions.

**Files changed:**

- `scripts/studio/catalogue_write_server.py`
- `tests/python/test_studio_activity_context.py`
- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The Batch A save paths now share profile-driven context normalization and build-row mapping while keeping source writes, lookup refreshes, builds, and future cleanup decisions in the owning handlers.
Tests compare the runtime profiles with the visible activity contract registry so later batches are less likely to drift.

## [2026-05-08] Extended Studio activity logging to catalogue editor saves

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Completed Batch A for unified Studio activity logging by wiring single-record save actions on the work, work detail, series, and moment catalogue editors into the structured activity contract and feed.

**Files changed:**

- `assets/studio/data/activity_contract.json`
- `scripts/studio/catalogue_write_server.py`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Single metadata saves now produce correlated activity rows for canonical source writes, lookup refreshes where they actually occur, published-data rebuilds when attempted, and catalogue search rebuilds when attempted.
Batch findings are recorded in the request so later create/delete/publication coverage can reuse the same approach without over-expanding this slice.

## [2026-05-08] Implemented v1 Studio activity report route

**Status:** implemented

**Area:** Studio / activity reporting

**Summary:**
Added `/studio/activity/`, backed by the unified activity feed, with columns for date-time, status, page, user action, and script purpose.
Status markers open a detail modal with the row's persisted activity descriptions.

**Files changed:**

- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)
- [Studio](/docs/?scope=studio&doc=studio)

**Impact:**
The v1 correlated activity feed now has a user-facing Studio route alongside the then-existing split activity reports during validation.

## [2026-05-08] Added unified Studio activity log request

**Status:** proposed

**Area:** Studio / activity reporting

**Summary:**
Added a change request for replacing split activity reports with a single Studio activity log that groups script-level rows by the initiating Studio page action.

**Files changed:**

- [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request defines the desired row columns, status modal behavior, user-action correlation model, source-log coverage, and acceptance checks for a future implementation.

## [2026-05-08] Implemented R2 media upload automation

**Status:** implemented

**Area:** Catalogue / media publishing

**Summary:**
Added `./scripts/publish_media_to_r2.py`, a dry-run-first Cloudflare R2 publisher for catalogue primary-image derivatives.

**Files changed:**

- `scripts/publish_media_to_r2.py`
- `tests/python/test_publish_media_to_r2.py`
- `.gitignore`
- [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [R2 Media Upload Automation Request](/docs/?scope=studio&doc=site-request-r2-media-upload-automation)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
Catalogue work, work-detail, and moment primary variants can now be previewed or uploaded to R2 from the CLI.
The publisher loads credentials from environment variables or gitignored local env files, skips unchanged objects, blocks changed remote objects unless `--force` is explicit, supports exact-id remote primary deletion with `--delete --write`, and keeps docs media publishing out of scope for this milestone.

## [2026-05-07] Clarified Docs Viewer draft visibility

**Status:** implemented

**Area:** Docs Viewer / Management

**Summary:**
Changed manage-mode draft visibility from a hidden `drafts` toggle and bold index styling to always-visible non-viewable docs with a `✏️` prefix, plus a checked-by-default `show viewable` toggle.

**Impact:**
The Edit modal status dropdown now includes `draft` across all scopes. Saving `draft` writes `viewable: false`; saving any non-draft status writes `viewable: true`.

## [2026-05-07] Fixed Studio mobile nav overflow

**Status:** implemented

**Area:** Studio / Navigation

**Summary:**
Moved secondary Studio header links behind the existing shared mobile `nav-more` menu and removed source-format suffixes from the Docs Import staged-file dropdown.

**Impact:**
Studio pages no longer force horizontal page overflow on mobile due to the full inline nav, while desktop keeps the full header link row.

## [2026-05-07] Refined Docs Import result panel layout

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Stacked Docs Import result fields vertically and reduced result message text to the small text token.

**Impact:**
Long staged media paths, R2 keys, and media tokens now use the full result-panel width and wrap more predictably on desktop and mobile.

## [2026-05-07] Refined Docs Import filename conflict UI

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Changed Docs Import collision recovery from an inline title prompt to a shared Studio modal for editing the replacement `doc_id`.

**Reason:**
The conflict is caused by an existing Markdown filename/doc_id, not by the imported document title. The UI should ask for the exact filename stem that will change.

**Files changed:**

- `scripts/docs/docs_management_server.py`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
When a staged source would write a filename that already exists, `/studio/docs-import/` now opens a `File already exists` modal seeded with the colliding `doc_id`.
OK resubmits with `replacement_doc_id`, Replace explicitly overwrites the existing source file, Cancel leaves the import unwritten, and the imported document title is preserved.
The staged-file control is also constrained to half the content width on desktop so `publish into` sits beside it.

## [2026-05-07] Implemented Docs Import inline raster extraction

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Implemented extraction of inline raster data URLs from Docs Import sources into generated staged media files.

**Reason:**
Imported docs can contain very long `data:image/...;base64,...` Markdown image targets. Those should become normal docs media tokens with explicit staged files and manual R2 copy instructions.

**Files changed:**

- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Docs HTML Inline Raster Media Request](/docs/?scope=studio&doc=site-request-docs-html-inline-raster-media)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
HTML and Markdown imports now rewrite Markdown-image-form inline PNG, JPEG, WebP, and GIF data URLs to <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code> tokens during preview.
On create or overwrite, the docs service decodes the planned images into `var/docs/import-staging/` with incrementing filenames such as `example-doc-image-01.png`, returns `inline_media_written`, and the Studio result panel lists staged paths, R2 keys, and media tokens for copying to R2.

## [2026-05-07] Implemented Docs Import source registry and media support

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Implemented the Docs Import source registry and expanded staged imports beyond HTML and Markdown.

**Reason:**
Docs Import needed a structured importer boundary before adding text, standalone SVG, R2-backed image wrappers, and downloadable file wrappers.

**Files changed:**

- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The route now lists HTML, Markdown, text, SVG, raster image, and file-media staged files.
Text imports autolink plain URLs, HTML and standalone SVG share SVG safety behavior, image and file imports generate <code>&#91;&#91;media:docs/&lt;scope&gt;/...&#93;&#93;</code> wrappers with manual R2 copy warnings, and source-stem collisions prompt for a replacement title instead of silently suffixing.

## [2026-05-07] Added duplicate stem handling to Docs Import media request

**Status:** proposed

**Area:** Studio / Docs Import

**Summary:**
Updated the Docs Import media request so proposed `doc_id` collisions prompt for a replacement title instead of auto-appending a suffix.

**Reason:**
When a staged file stem already matches an existing Markdown source file, the user should control the new title and resulting `doc_id` while still getting the current name as an easy starting point.

**Files changed:**

- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request now requires collision detection during preview, a replacement-title prompt seeded with the current name, server-side `doc_id` regeneration, and a second collision check before apply.

## [2026-05-07] Refined Docs Import media request around shared SVG and R2 links

**Status:** proposed

**Area:** Studio / Docs Import

**Summary:**
Updated the Docs Import media request so raw SVG files and SVG embedded in HTML share one sanitizer policy, plain text URLs become autolinks, and imported media wrappers point at expected R2 docs media keys.

**Reason:**
The import model should keep SVG behavior consistent across source formats and should match the current manual R2 media workflow instead of introducing a separate repo-local image copy path.

**Files changed:**

- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request now treats images and downloadable files as separate docs media classes, with image links under `docs/<scope>/img/` and file links under `docs/<scope>/files/`.
The generated Markdown points at <code>&#91;&#91;media:...&#93;&#93;</code> tokens while the actual R2 copy remains manual.

## [2026-05-07] Added R2 media upload automation request

**Status:** proposed

**Area:** Catalogue / media publishing

**Summary:**
Added a change request for replacing manual R2 media uploads with a script-managed publishing workflow.

**Reason:**
Catalogue primary derivatives are generated locally but still require a manual R2 handoff.
That is easy to miss today and would become harder to manage once docs imports can create media assets too.

**Files changed:**

- [R2 Media Upload Automation Request](/docs/?scope=studio&doc=site-request-r2-media-upload-automation)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request proposes a dry-run-first R2 publisher, secure credential loading through local environment variables or gitignored secret files, catalogue primary-image support first, and a registry-style adapter path for future docs media.

## [2026-05-07] Added Docs Import registry and media support request

**Status:** proposed

**Area:** Studio / Docs Import

**Summary:**
Added a change request for making Docs Import format-extensible and supporting standalone text, SVG, and raster image files.

**Reason:**
The current source import flow now handles HTML and body-only Markdown, but future standalone media imports need a clearer registry boundary, asset-copy plan, and SVG safety policy before implementation.

**Files changed:**

- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request proposes a source importer registry, `.txt` import, standalone SVG wrapper-doc import, and raster image import that copies assets under `assets/docs/imports/<scope>/<doc_id>/` before generating wrapper Markdown.

## [2026-05-07] Enabled Markdown files in Docs Import

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Extended `/studio/docs-import/` so staged body-only Markdown files can be imported alongside staged HTML files.

**Reason:**
Some source material is already authored as Markdown and should not be forced through the HTML conversion path.

**Files changed:**

- `studio/docs-import/index.md`
- `studio/library/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The import page now lists `.html`, `.htm`, `.md`, and `.markdown` files from `var/docs/import-staging/`.
Markdown imports are treated as body-only source, derive `doc_id` from the staged filename, derive title from the first `# H1` when present, and get normal Docs Viewer front matter during create or overwrite.

## [2026-05-07] Added a dense Studio list primitive variant

**Status:** implemented

**Area:** Studio UI / List Primitive

**Summary:**
Added `tagStudioList--dense` as a shared list primitive variant based on the `/studio/studio-works/` scan-table design.

**Reason:**
The works list density is useful beyond the works route, but copying `worksList__*` classes would mix page-specific semantics into unrelated Studio pages.

**Files changed:**

- `assets/studio/css/studio.css`
- `studio/ui-catalogue/list/index.md`
- `_includes/studio_ui_catalogue_list_demo.html`
- `_includes/ui_catalogue_notes/list.md`
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Studio pages can now opt into a dense sortable list with `--text-xs` type, no row dividers, and a bold title column while keeping their own column templates and row semantics.

## [2026-05-07] Aligned Studio Works with the dense list primitive

**Status:** implemented

**Area:** Studio UI / Catalogue Works

**Summary:**
Moved `/studio/studio-works/` onto `tagStudioList--dense` for its header, sortable buttons, rows, sort indicator, cell links, metadata cells, and bold title cell.

**Reason:**
Once the dense list became a shared primitive, the Studio works page no longer needed to own the same presentation through route-local `worksList__*` styling.

**Files changed:**

- `studio/studio-works/index.md`
- `assets/studio/js/studio-works.js`
- `assets/css/main.css`
- `assets/studio/css/studio.css`
- [Catalogue Works](/docs/?scope=studio&doc=studio-works)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The route keeps works-specific data loading, return links, and column templates while sharing the dense list type scale, row rhythm, sortable-header styling, indicator styling, and title emphasis.

## [2026-05-07] Added the Library Documents Studio page

**Status:** implemented

**Area:** Studio / Library

**Summary:**
Added `/studio/library-documents/` as a read-only dense-list review page for generated Library Docs Viewer records.

**Reason:**
Library document review needs a compact scan table with viewable and parent state without entering the export selection workflow.

**Files changed:**

- `studio/library-documents/index.md`
- `assets/studio/js/library-documents.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `studio/library/index.md`
- [Library Documents](/docs/?scope=studio&doc=library-documents)
- [Library](/docs/?scope=studio&doc=library)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The Library dashboard now links to a document index under the HTML Import entry.
The page sorts by `doc_id`, `added_date`, and `title`, opens document links in Library manage mode, places parent and viewable status before the title, shows the export-style green viewable dot, marks parent docs with a tick, and filters independently by `viewable` and `parent`.

## [2026-05-06] Respected root sort order in Docs Viewer metadata edits

**Status:** implemented

**Area:** Docs Viewer / Management

**Summary:**
Changing a doc's parent to root in the metadata modal now preserves the visible `sort_order` value instead of converting the save request to append.

**Reason:**
The modal's append shortcut was intended for moving a doc into another parent while leaving the existing sort field untouched.
For root moves, that made the shown `sort_order` look ignored and placed the doc at the bottom of the root index.

**Files changed:**

- `assets/js/docs-viewer.js`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Root reparenting now respects the sort field the user can see and edit.
Moving into a non-root parent still appends by default when the sort field is left unchanged.

## [2026-05-06] Quieted available Docs Viewer manage mode

**Status:** implemented

**Area:** Docs Viewer / UI

**Summary:**
The Docs Viewer no longer shows the "Manage mode is local-only" note after the local docs-management server is confirmed available.

**Reason:**
The visible note was only useful while manage mode was unavailable or still checking.
Once the local server is running and the management toolbar is enabled, it became persistent chrome rather than actionable status.

**Files changed:**

- `assets/js/docs-viewer.js`
- `assets/studio/data/studio_config.json`
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Manage mode still shows checking, server-unavailable, archive-unavailable, search-blocked, and operation-result notes.
The normal available state is quieter and leaves the management controls to carry the mode context.

## [2026-05-06] Preserved cross-scope Docs Viewer links

**Status:** implemented

**Area:** Docs / Builder

**Summary:**
The docs builder now keeps cross-scope viewer links on their original viewer route instead of resolving matching `doc` query values against the current build scope.

**Reason:**
The Studio `library` doc intentionally links to the public Library viewer at `/library/?doc=library`.
Because the Studio docs scope also has a `library` doc id, the previous link rewrite treated that public Library route as a same-scope Studio docs link and generated `/docs/?scope=studio&doc=library`.

**Files changed:**

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Library](/docs/?scope=studio&doc=library)
- `scripts/build_docs.rb`

**Impact:**
Same-scope viewer links and relative `.md` links still normalize onto the current scope's viewer route.
Cross-scope links such as `/library/?doc=library` now keep their intended public destination.

## [2026-05-06] Ignored code-block links in Docs Broken Links

**Status:** implemented

**Area:** Docs / Validation

**Summary:**
The Docs Broken Links audit now skips links rendered inside code blocks.

**Reason:**
Code examples may intentionally contain illustrative docs URLs that are not live navigation and should not be reported as broken links.

**Files changed:**

- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- `scripts/docs/docs_broken_links.py`
- `scripts/run_checks.py`
- `tests/python/test_docs_broken_links.py`

**Impact:**
The audit remains focused on navigable prose links while code samples can show obsolete, example, or placeholder docs URLs without creating maintenance findings.

## [2026-05-06] Removed title mismatches from Docs Broken Links

**Status:** implemented

**Area:** Docs / Validation

**Summary:**
The Docs Broken Links audit now reports only missing docs targets. The Studio route no longer renders title-mismatch filters or counts, and the CLI summary no longer includes `wrong title`.

**Reason:**
Visible link labels are not hard failures. They may intentionally shorten a title, preserve historical wording, or correct an outdated target title in context.

**Files changed:**

- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_broken_links.py`
- `scripts/docs/docs_management_server.py`

**Impact:**
The audit is focused on links that fail to resolve. Stale or intentionally different link text is left to editorial review rather than treated as a broken-link issue.

## [2026-05-06] Relaxed archived changelog title-link audits

**Status:** implemented

**Area:** Docs / Validation

**Summary:**
The Docs Broken Links audit now skips strict wrong-title checks for historical site-change-log archive docs while still reporting missing targets from those archives.

**Reason:**
Archived changelog entries preserve historical wording, so their link labels often intentionally differ from current document titles.
Missing targets are still useful maintenance findings, but exact title warnings from old entries were creating noise.

**Files changed:**

- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)
- `scripts/docs/docs_broken_links.py`

**Impact:**
This was superseded later on 2026-05-06 when title mismatches were removed from the broken-links audit altogether.
The archived-doc exception is no longer needed, but this entry remains as historical context for the intermediate behavior.

## [2026-05-06] Split the site change log into dated archive docs

**Status:** implemented

**Area:** Docs / Architecture

**Summary:**
Kept the stable Site Change Log doc as the current entry point and moved older entries into dated archive child docs.
The main log now carries the newest entries plus links to the May 2026, April 2026, and March 2026-and-earlier archives.

**Reason:**
The single source file had grown past 7,300 lines, making routine close-out edits, review, and docs payload inspection harder than necessary.
Keeping a compact current page preserves the existing docs-viewer link while moving historical reading into focused archive docs.

**Files changed:**

- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Site Change Log Archive: May 2026](/docs/?scope=studio&doc=site-change-log-2026-05)
- [Site Change Log Archive: April 2026](/docs/?scope=studio&doc=site-change-log-2026-04)
- [Site Change Log Archive: March 2026 And Earlier](/docs/?scope=studio&doc=site-change-log-2026-03-and-earlier)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)

**Impact:**
New change-log entries still go into the stable `site-change-log` doc first.
Older history remains published and searchable through archive child docs under the same docs-viewer section.

## [2026-05-06] Stabilized shared data export/import routes

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Moved the active Studio export/import shells to `/studio/export/` and `/studio/import/`.
The browser modules, route-ready names, DOM ids, CSS classes, Studio config route keys, and UI text namespaces now use shared `data_export` and `data_import` naming.
The Library-specific export config file remains Library-named because it is the current documents-adapter config contract.

**Reason:**
The shared route shell should be the stable target before Catalogue and Analytics workflow requirements grow.
Keeping active routes neutral avoids preserving the old Library route names as compatibility aliases while still leaving Library domain docs and adapter configs explicit.

**Files changed:**

- [Studio Data Export](/docs/?scope=studio&doc=studio-data-export)
- [Studio Data Import](/docs/?scope=studio&doc=studio-data-import)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)
- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- `studio/export/index.md`
- `studio/import/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `tests/smoke/data_export.py`
- `tests/smoke/data_import.py`

**Impact:**
Library dashboard links and future Catalogue/Analytics dashboard links all target the same shared shell with `scope=...`.
The old `/studio/library-export/` and `/studio/library-import/` pages are removed rather than retained as aliases.

## [2026-05-06] Closed export/import adapter boundary request

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Completed the export/import adapter boundary documentation and verification pass.
The request now records the implemented Library documents adapter, normalized workflow folders, future Catalogue and Analytics stubs, and verification coverage.

**Reason:**
The adapter boundary should be visible in stable Library, script, config, and change-request docs before future data-domain work starts.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Standard checks now include adapter dispatch verification and a Studio smoke case for disabled future adapters.
The change request is marked implemented while Catalogue and Analytics behavior remains explicitly deferred.

## [2026-05-06] Added future export/import adapter stubs

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Added explicit `catalogue` and `analytics` adapter stubs to the export/import adapter registry.
The stubs declare planned capabilities and placeholder workflow roots without implementing domain behavior.

**Reason:**
Future Catalogue and Analytics requirements need named extension points, but they should not be folded into the Library documents adapter or inferred by route code.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- `assets/studio/data/export_import_adapters.json`
- `scripts/docs/export_import_adapters.py`

**Impact:**
The current export/import pages read domain availability from the adapter registry and can show planned future domains as unavailable.
The docs-management service still dispatches only active capabilities, so stub adapters fail closed before document-specific code runs.

## [2026-05-06] Normalized export/import workflow folders

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Moved Library export/import working artifacts to a data-domain-first layout under `var/studio/export-import/library/`.
The `documents` adapter now declares the Library export, staging, and preview roots used by the docs-management service.

**Reason:**
The shared export/import shell should not encode Docs Viewer folder names as the universal workflow layout.
Keeping folders under the adapter registry makes the path contract explicit and keeps future domains from inheriting document-specific paths.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)

**Impact:**
Exports now write under `var/studio/export-import/library/exports/`.
Staged import files are read from `var/studio/export-import/library/import-staging/`, and generated previews write under `var/studio/export-import/library/import-preview/`.
Old local files under the previous test folders are not migrated.

## [2026-05-06] Moved document import/export dispatch behind adapter config

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Added the explicit export/import adapter registry and routed the Library document export/import behavior through the configured `documents` adapter.
The active import service endpoints are now neutral dispatch endpoints instead of Library-named service routes.

**Reason:**
The first implementation should target the shell-adapter architecture directly so old route names and migration artifacts do not become long-lived compatibility layers.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
`data_domain` and `operation` now resolve exactly one configured adapter before the docs-management service runs document-specific import/export logic.
Unconfigured domains fail closed, and the removed Library-named import endpoints are not retained as aliases.

## [2026-05-05] Added export/import adapter boundary request

**Status:** proposed

**Area:** Studio / Data workflows

**Summary:**
Added a change request to adopt an adapter-based export/import architecture before more Library, Analytics, or Catalogue requirements are added to the shared workflow shell.
The current Library document workflow is identified as the first adapter implementation target.

**Reason:**
Library import/export is document-specific, while future Analytics and Catalogue workflows need domain-specific validation and apply behavior against structured site data.
The adapter boundary keeps shared lifecycle behavior reusable without making document preview semantics universal.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
Future export/import requirements now have a stable planning target that separates shared shell responsibilities from scope-specific adapter behavior.
Follow-up review resolved the initial direction: adapters map to data domains rather than route scopes, Library should use a general documents adapter with Library config, neutral export/import routes are preferred, and user-facing workflow folders should be data-domain-first.

## [2026-05-05] Added Docs Toolkit extraction request

**Status:** proposed

**Area:** Docs / Tooling

**Summary:**
Added a change request to explore whether the Docs Viewer, generated docs/search pipeline, local docs-management server, and scope-aware export/import workflow should become a reusable docs toolkit that other repositories can track from a master version.

**Reason:**
The combined docs viewer and export/import workflow is becoming a useful local tool beyond this site, but reuse needs a managed upstream model instead of copied files.

**Files changed:**

- [Docs Toolkit Extraction Request](/docs/?scope=studio&doc=site-request-docs-toolkit-extraction)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
The extraction idea now has a stable planning target with goals, non-goals, install-shape options, open questions, and acceptance criteria.

## [2026-05-05] Stabilized image-panel text across themes

**Status:** implemented

**Area:** Studio / UI

**Summary:**
Base Studio image panel links now keep their dark text treatment in both light and dark mode.
The existing `tagStudio__panelLink--imageContrast` modifier remains the explicit white-text variant for darker or busier images.

**Reason:**
Image panels are design-time compositions.
Keeping one text treatment avoids per-theme image swaps and makes image/overlay choice the design responsibility.

**Files changed:**

- `assets/studio/css/studio.css`
- `_includes/ui_catalogue_notes/panel.md`
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
`/studio/` image panels and the Panel primitive image examples stay legible in dark mode without changing source images.

## [2026-05-05] Fixed dark-mode Studio panel contrast

**Status:** implemented

**Area:** Studio / UI

**Summary:**
Studio panels now switch their surface, border, muted text, default-value, and control tokens together in dark mode.
This prevents light panels from combining with dark-mode muted text on routes such as `/studio/import/`.

**Reason:**
The previous token mix left field labels and disabled controls nearly invisible in dark mode because the panel stayed white while muted text became pale grey.

**Files changed:**

- `assets/studio/css/studio.css`
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Shared Studio panels and controls have coherent dark-mode contrast instead of relying on route-local overrides.

## [2026-05-05] Added aggregate public search

**Status:** implemented

**Area:** Search

**Summary:**
Direct `/search/` now works as an aggregate search across enabled dedicated-route scopes instead of showing the missing-scope message.
Explicit scoped search URLs remain supported for Catalogue, Library, Studio, and Analysis.

**Reason:**
The public search route should be useful when opened directly now that multiple generated search indexes exist.

**Files changed:**

- `assets/js/search/search-page.js`
- `assets/js/search/search-policy.js`
- `assets/data/search/policy.json`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Search](/docs/?scope=studio&doc=search)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
- [Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Users can open `/search/` directly and search across Catalogue, Library, Studio docs, and Analysis results in one list.
The aggregate route does not show a visible `all` heading and does not fail the whole page when one enabled scope index is unavailable.
During `bin/dev-studio`, docs-domain search reads use the docs-management generated-search endpoint rather than Jekyll's dev-overlay output.

## [2026-05-05] Refined Search dashboard to column links

**Status:** implemented

**Area:** Studio / Search

**Summary:**
`/studio/search/` now matches the compact dashboard structure used by the other Studio domain dashboards.
The page keeps its metrics, removes intro and panel-card descriptive copy, and groups routes into `interface` and `documents` columns using the shared Column Links pattern.
The documents column links to the Search plan and Search change log.

**Reason:**
Search is a Studio domain entry page.
The shared column-link pattern is a better fit for routine navigation than bespoke descriptive panels.

**Files changed:**

- `studio/search/index.md`
- [Search Plan](/docs/?scope=studio&doc=new-pipeline-refine-search)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Catalogue, Library, Analytics, and Search dashboards now share the same compact route-entry language.

## [2026-05-05] Added scoped data links to domain dashboards

**Status:** implemented

**Area:** Studio / Dashboards

**Summary:**
`/studio/catalogue/` now includes a `Data` column with export and import pills linked to the shared workflow routes with `?scope=catalogue`.
`/studio/library/` now makes its existing export and import pills explicit with `?scope=library`.
The Column Links pattern supports a three-column modifier for Catalogue while keeping two-column dashboards unchanged.

**Reason:**
After import/export became scope-aware, domain dashboards should route users directly to the relevant scoped data workflow instead of relying on defaults or leaving Catalogue without data entry points.

**Files changed:**

- `studio/catalogue/index.md`
- `studio/library/index.md`
- `assets/css/main.css`
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Catalogue, Library, and Analytics now all expose scoped data workflow links from their dashboards.

## [2026-05-05] Refined Analytics dashboard to column links

**Status:** implemented

**Area:** Studio / Analytics

**Summary:**
`/studio/analytics/` now matches the compact dashboard structure used by Catalogue and Library.
The page keeps its metrics, removes intro and panel-card descriptive copy, and groups routes into `Data` and `Tags` columns using the shared Column Links pattern.
Analytics import/export links point at the shared scope-aware data workflow shell.

**Reason:**
Analytics is a Studio domain entry page like Catalogue and Library.
The shared column-link pattern is a better fit for routine navigation than bespoke descriptive panels.

**Files changed:**

- `studio/analytics/index.md`
- [Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The three main Studio domain dashboards now share the same compact route-entry language while preserving their domain-specific links.

## [2026-05-05] Made Library import/export routes scope-aware

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
`/studio/export/` and `/studio/import/` now expose a scope selector for `library`, `catalogue`, and `analytics`.
Library remains the default scope.
Export config filtering now uses the selected scope and handles future scopes with no enabled configs without failing the page.
Import staged-file listing and preview generation now use `var/docs/import-staging/<scope>/` and `var/docs/import-preview/<scope>/` for the supported workflow scopes.
Source-write apply actions remain enabled only for Library.

**Reason:**
Catalogue and Analytics need the same export/stage/preview workflow shape for future LLM review work, but their record shapes, config details, and write actions are not defined yet.
The shared page and service infrastructure can support those scopes before the scope-specific contracts are designed.

**Files changed:**

- `studio/export/index.md`
- `studio/import/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/docs/docs_import.py`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The workflow shell is ready for Catalogue and Analytics configs.
Until those configs and source-write contracts exist, non-Library export scopes show no enabled configs and non-Library import scopes support staged preview only.

## [2026-05-05] Added UI Catalogue composition pattern pages

**Status:** implemented

**Area:** Studio / UI Catalogue

**Summary:**
The UI Catalogue index now uses the shared two-column route-link pattern already used by the Catalogue and Library dashboards.
It groups links into `Primitives` and `Composition Patterns`.
Added live UI Catalogue pages for the reopenable command result pattern and the column links pattern, plus a matching docs-viewer contract for Column Links.

**Reason:**
The catalogue index is a route-entry page, not a descriptive card surface.
Reusing the dashboard column-link composition keeps the UI system catalogue aligned with the pattern it is documenting.

**Files changed:**

- `studio/ui-catalogue/index.md`
- `studio/ui-catalogue/reopenable-command-result/index.md`
- `studio/ui-catalogue/column-links/index.md`
- `assets/studio/css/studio.css`
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Repeated Studio route-entry link groups now have a named composition pattern and a live reference page.

## [2026-05-05] Added UI framework and catalogue target docs

**Status:** implemented

**Area:** Docs / Design

**Summary:**
Added `UI` as the unified site-wide UI framework target under Design.
Added matching UI Catalogue child docs for button, input, list, and panel primitives, plus a composition-pattern doc for reopenable command results.
Updated the catalogue model so live primitive pages are visual references while matching docs hold implementation and lifecycle contracts.

**Reason:**
The old split between `UI Framework`, `Studio UI Framework`, `UI Catalogue`, and `Studio UI Rules` mixed framework guidance, primitive contracts, implementation notes, and historical decisions in one layer.
The new targets give stable destinations for moving durable content out of the rules log and retiring the artificial site-vs-Studio split.

**Files changed:**

- [Design](/docs/?scope=studio&doc=design)
- [UI](/docs/?scope=studio&doc=ui)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Future UI work can file durable rules into framework, primitive, or composition-pattern docs instead of burying them in the Studio UI decision log.

## [2026-05-05] Refined Library import review UI

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
The Library import route now keeps staged-file selection and preview/apply commands in one compact row.
It removes staged-file path/format/size/modified metadata from the page, removes generated preview-file paths from document row metadata, and shows preview/apply completion details in a shared modal with a single `Close` button.
The modal presents counts as a compact vertical label/value stack with right-aligned values and issues below the counts.
Preview completion messages now use context-aware singular/plural wording for generated preview files.
A small `results` button appears beside the preview success message while that message remains current, allowing the last preview result modal to be reopened.

**Reason:**
The route is now a repeated review/apply workflow.
Persistent file and result details made the page harder to scan after the document list became the main working surface.

**Files changed:**

- `studio/import/index.md`
- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-modal.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/smoke/data_import.py`
- [Library Import UI Refinements](/docs/?scope=studio&doc=library-import-ui)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Library import is more compact and consistent with the Library export result-modal pattern.
The result modal no longer exposes source export id, generated timestamp, or preview-file paths in the main UI; those remain available through staged/generated files and service payloads when needed.

## [2026-05-04] Closed Library import/export v2 task list

**Status:** implemented

**Area:** Studio / Library import-export

**Summary:**
Marked the Library import/export v2 request as implemented and closed its documentation and verification task.
The request now points at the separate generated-parent-nodes follow-up for future hierarchy imports that need to create new Library grouping docs.

**Reason:**
The v2 task list now has implemented export filters, export formats, import previews, summary apply, hierarchy apply, docs updates, generated docs payloads, and verification coverage.
New parent-node creation is a distinct future source-creation contract rather than a loose extension of unknown `parent_id` handling.

**Files changed:**

- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Library Import Generated Parent Nodes Request](/docs/?scope=studio&doc=site-request-library-import-generated-parent-nodes)

**Impact:**
The current v2 implementation can be treated as closed.
Future generated parent-node work has its own request and should not be folded into the existing hierarchy apply contract without a new task pass.

## [2026-05-04] Added hierarchy apply for Library imports

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
The Library import page can now apply selected staged `parent_id` values to canonical Library source documents.
`Apply hierarchy` enables only for selected document preview rows, runs a preflight against staged record indexes and current `_docs_library/` files, shows a shared OK/Cancel confirmation modal, then writes only selected parent-id changes.
The docs-management endpoint creates a timestamped `data-import-hierarchy-apply` backup under the existing `var/docs/backups/` root before writing and runs targeted Library docs-search updates for changed ids.
Generated Library docs data now treats unresolved imported source parents as root-level relationships so unknown external parents do not break `/library/`.

**Reason:**
Task 8 needed hierarchy writes separate from summary writes.
Keeping this parent-id-only preserves current `sort_order` and leaves future sort-order imports for the later file format that actually includes that field.

**Files changed:**

- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_management_server.py`
- `scripts/build_docs.rb`
- `tests/python/test_docs_import_service.py`
- `tests/smoke/data_import.py`
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Selected staged hierarchy rows can update Library source safely with preflight reporting, backups, and skipped/warning rows.
Full-content applies and imported `sort_order` writes remain separate future contracts.

## [2026-05-04] Added summary apply for Library imports

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
The Library import page can now apply selected staged summaries to canonical Library source documents.
`Update summary` enables only for selected document preview rows, runs a preflight against the staged record indexes and current `_docs_library/` files, shows a shared OK/Cancel confirmation modal, then writes only the selected summary changes.
The docs-management endpoint creates a timestamped `data-import-summary-apply` backup under the existing `var/docs/backups/` root before writing and runs targeted Library docs-search updates for changed ids.

**Reason:**
Task 7 needed the first narrow source-write path before hierarchy writes.
Keeping the apply action summary-only makes the import flow useful for missing-summary cleanup without mixing it with full-content or relationship changes.

**Files changed:**

- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- `tests/smoke/data_import.py`
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Selected staged summary rows can update Library source safely with preflight reporting and backups.
Hierarchy, `sort_order`, and full-content applies remain separate future contracts.

## [2026-05-04] Added selectable Library export formats

**Status:** implemented

**Area:** Studio / Library export

**Summary:**
Library export configs now declare selectable output formats with `target.supported_formats`, while `target.format` remains the default.
The Studio Library export page shows JSON and JSONL options, disables unsupported combinations, sends `target_format` to `POST /docs/export`, and shows the selected format in the result modal.
Document-row exports can now write JSON arrays as well as JSONL rows when the config supports both.

**Reason:**
Task 6 needed user-visible format choice without making broad format assumptions across every export pattern.
Keeping supported formats config-declared lets the CLI, service endpoint, and Studio UI share the same validation boundary.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/library_export_configs.schema.json`
- `scripts/docs/docs_export.py`
- `scripts/docs/docs_management_server.py`
- `studio/export/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/css/studio.css`
- `tests/python/test_docs_export.py`
- `tests/python/test_docs_management_server.py`
- `tests/smoke/data_export.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Summary and full-content exports default to JSONL but can be written as JSON arrays.
Parent-child relationship exports remain JSON-only.

## [2026-05-04] Added Library export list filters

**Status:** implemented

**Area:** Studio / Library export

**Summary:**
The Library export page now has `show all`, `no content`, and `not viewable` filter pills with counts.
The generated docs index now includes `content_text_length`, derived from rendered document HTML after plain-text extraction and title stripping, so the page can identify no-content docs without fetching every per-doc payload.
Select all now targets the currently visible filtered list; the export request still sends explicit selected doc ids and the export write path is unchanged.

**Reason:**
Library export review needs quick slices for empty generated docs and generated-but-hidden docs before output-format work starts.

**Files changed:**

- `scripts/build_docs.rb`
- `studio/export/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/smoke/data_export.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Docs Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
The UI can narrow selection without changing config definitions or service payload shape.
Generated docs index rows have one additional numeric metadata field.

## [2026-05-04] Added relationship metadata to full Library content exports

**Status:** implemented

**Area:** Studio / Library export

**Summary:**
The `library-full-document-content` export config now declares parent, ancestor, and child relationship fields alongside `source_text`.
Full-content JSONL rows include `parent_id`, `parent_title`, `ancestor_ids`, `ancestor_titles`, `child_ids`, and `child_titles` without adding a separate UI option.
`sort_order` remains deferred until external hierarchy files and import apply behavior support it.

**Reason:**
Library import previews can now build a staged hierarchy tree from full-content export files when relationship metadata is present.
Keeping the fields in the export config preserves the config/runtime contract and avoids adding another export-page control.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `tests/python/test_docs_export.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)

**Impact:**
Full-content exports are more useful as import-preview staging files and external review bundles.
Consumers should expect relationship fields in the full-content rows, but not `sort_order` yet.

## [2026-05-04] Aligned Library import with the export page shell

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
Updated `/studio/import/` so its first v2 milestone uses the same compact command/list shell as `/studio/export/`.
The page now places Preview beside the staged-file selector, shows Select all and Clear pills, renders generated previews in the main selectable list area, and keeps future `Update summary` and `Apply hierarchy` actions visible but disabled.
Preview rows are ordered and indented from staged `parent_id` metadata when relationship data is available, and generated relationship-tree preview files appear as their own visible list row.
Preview files now use staged-file timestamp suffixes when present, include front-matter-like matched-config and staged-only sections, and generate a whole-tree preview whenever staged relationship metadata is available.

**Reason:**
Library import v2 should begin with review-oriented UI changes before source-write wiring.
Sharing the export page structure keeps the Library data workflows predictable while the apply contracts remain intentionally unavailable.

**Files changed:**

- `studio/import/index.md`
- `assets/studio/js/data-import.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/smoke/data_import.py`
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The import route now has the hierarchy-aware preview list needed before preview-file normalization and source-write contract work.
The main risk is that preview-row selection is currently review-only because source-write endpoints do not exist yet; the disabled action buttons make that boundary explicit.

## [2026-05-04] Added Studio backup retention on dev startup

**Status:** implemented

**Area:** Studio / local operations

**Summary:**
Added `scripts/studio_backup_retention.py` and wired it into `bin/dev-studio` startup.
The script prunes local Studio backup files by keeping the newest backups per target file: `20` for `var/studio/backups/` and `30` for `var/studio/catalogue/backups/`.

**Reason:**
This repo has no separate admin role, so local operational backups need a default retention policy that runs through the normal development entry point rather than relying on manual cleanup habits.

**Changes:**
`bin/dev-studio` now runs backup retention once at startup before long-running services start.
The cleanup skips unparseable backups, keeps whole catalogue transaction bundles when any contained target is still retained, and continues startup with a warning if cleanup fails.
Startup cleanup can be disabled with `DOTLINEFORM_BACKUP_RETENTION=off` or `DOTLINEFORM_BACKUP_RETENTION=0`.

**Files changed:**

- `bin/dev-studio`
- `scripts/studio_backup_retention.py`
- `tests/python/test_studio_backup_retention.py`
- `scripts/run_checks.py`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Studio Backup Retention](/docs/?scope=studio&doc=scripts-studio-backup-retention)
- [Studio Config And Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)

**Impact:**
Local backup folders should stop growing indefinitely during normal Studio use.
The main risk is accidental pruning of a backup that would have been useful for unusually old local recovery; the newest-N-per-target policy and skipped unparseable files keep that risk narrow.

## [2026-05-04] Cleaned staged catalogue thumbnails after asset copy

**Status:** implemented

**Area:** Catalogue / local media generation

**Summary:**
Scoped catalogue media builds now treat staged thumbnail derivatives as temporary files.
After a generated thumbnail is copied into `assets/works/img/`, `assets/work_details/img/`, or `assets/moments/img/`, the matching file under `var/catalogue/media/<kind>/srcset_images/thumb/` is removed.

**Reason:**
Primary derivatives under `var/catalogue/media/` remain the manual handoff point for remote media publishing until R2 upload is automated.
Staged thumbnails do not have the same handoff responsibility once the public asset-folder copy succeeds, so retaining them only grows local cache size.

**Changes:**
The local media planner no longer treats staged thumbnail paths as persistent currentness outputs.
It generates staged thumbnails only when public asset thumbnails need refresh, copies them to the asset folders, and then deletes the staged thumbnail intermediates.
The media build response records cleaned staged thumbnail paths for diagnostics.

**Files changed:**

- `scripts/catalogue_json_build.py`
- `tests/python/test_catalogue_media_cleanup.py`
- `scripts/run_checks.py`
- [Build Catalogue JSON](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

**Impact:**
Future media refreshes keep staged source images and staged primary derivatives, but no longer retain thumbnail intermediates after successful asset copy.
Existing staged thumbnail files can be removed manually or by a later retention cleanup.

## [2026-05-04] Routed local Docs Viewer data reads through the docs server

**Status:** implemented

**Area:** Docs Viewer / local Studio runtime

**Summary:**
The docs-management server now serves allowlisted generated docs index, payload, and docs-search JSON for Studio, Library, and Analysis scopes. The shared Docs Viewer prefers those server reads when the localhost capability is available, while public/static routes continue to use generated JSON assets directly.

**Reason:**
Generated docs/search rewrites are local runtime data changes, not Jekyll source changes. Moving local reads through the server lets `bin/dev-studio` stop making Jekyll watch those generated JSON trees.

**Changes:**
Added `GET /docs/generated/index`, `GET /docs/generated/payload`, and `GET /docs/generated/search` with raw JSON responses, strict scope/doc validation, and `Cache-Control: no-store`.
The Docs Viewer now probes generated-read capability and uses server reads for index, payload, and search data when available.
`bin/dev-studio` now starts Jekyll with `_config.yml,_config.dev-studio.yml`; the overlay excludes generated docs/search JSON and keeps public builds unchanged.

**Files changed:**

- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `bin/dev-studio`
- `_config.dev-studio.yml`
- [Local Docs Data Server Reads Request](/docs/?scope=studio&doc=site-request-local-docs-data-server-reads)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)

**Impact:**
Local docs source edits can still rebuild generated docs/search data immediately, but Jekyll no longer needs to regenerate because those generated files changed during `bin/dev-studio`.

## [2026-05-04] Fixed Studio static docs/search reads under the dev overlay

**Status:** implemented

**Area:** Studio / local data reads

**Summary:**
`/studio/export/` now reads the generated Library docs index through the docs-management server when that service is available. The Studio dashboard also uses docs-management generated-data reads for Library docs count and docs-search metrics when running locally.

**Reason:**
The dev-only Jekyll overlay removes generated docs/search JSON from Jekyll output, so Studio pages must not fetch those static paths while `bin/dev-studio` is running.

**Files changed:**

- `assets/studio/js/data-export.js`
- `assets/studio/js/studio-dashboard.js`
- `assets/studio/js/studio-transport.js`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

## [2026-05-04] Treated Archive as a normal Docs Viewer folder

**Status:** implemented

**Area:** Docs Viewer / docs search

**Summary:**
Renamed the Archive docs parent from `_archive` to `archive` and removed structural Archive behavior from the docs viewer, docs builder, docs search builder, Library export list, and docs-management server.

**Reason:**
The `viewable` flag now provides the visibility contract directly. Keeping `_archive` preserved a hidden-file naming problem and made Archive behave differently from other folders.

**Changes:**
Studio and Library Archive docs now use `doc_id: archive` and set `viewable: false`.
Generated viewer options no longer mark `archive` as non-loadable or manage-only.
Docs search excludes non-viewable docs rather than excluding `archive` by id.
The docs-management server lets `archive` be edited, moved, deleted when it has no children, and made viewable; the Archive command uses `archive` as its conventional destination parent and no-ops if invoked on `archive` itself.
Library export now includes generated Archive docs according to the same selection rules as other docs.

**Files changed:**

- `_docs/archive.md`
- `_docs_library/archive.md`
- `scripts/build_docs.rb`
- `scripts/build_search.rb`
- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `assets/studio/js/data-export.js`
- `assets/studio/data/library_export_configs.json`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Archive behavior is simpler and more consistent with the rest of the docs tree.
The main risk is accidental public exposure if `archive` or archived child docs are manually changed to `viewable: true`; that is now an explicit metadata decision rather than hidden structural behavior.

## [2026-05-04] Refined the Library export Studio UI

**Status:** implemented

**Area:** Library / Studio data export

**Summary:**
Applied the Library export UI refinements from [Library Export - UI refinements](/docs/?scope=studio&doc=library-export-ui).

**Reason:**
The export page needed less passive helper text, tighter command placement, and a dismissible result surface that focuses on counts and created files.

**Changes:**
The route now places `Run export` beside the export-pattern dropdown, keeps the missing-summaries checkbox under that dropdown, and shows Select all / Clear as checklist pills.
The selected-doc summary no longer reports missing-summary counts.
Completed export reports now open in a shared Studio modal with vertical counts, a filename-only read-only text box, optional warnings/issues, and one Close button.
The docs-management export summary now uses `document` or `documents` according to the exported count.

**Files changed:**

- `studio/export/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- [Library Export - UI refinements](/docs/?scope=studio&doc=library-export-ui)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The page is denser and more command-oriented, with export completion details no longer occupying permanent page space.
The modal adds a small interaction step after successful exports, but keeps the main checklist workflow cleaner.

## [2026-05-04] Library relationship exports now respect checklist selection

**Status:** implemented

**Area:** Library / Studio data export

**Summary:**
Changed the Parent-child relationships export pattern from implicit all-matching selection to explicit selected-document selection.

**Reason:**
The `/studio/export/` page displayed the same hierarchical checklist for this pattern as for the other export patterns, but the config asked the export engine to include all matching docs.
That made selected branches irrelevant and produced whole-corpus exports.

**Changes:**
`library-parent-child-relationships` now uses `explicit_doc_ids`, while keeping descendant expansion so selecting a parent still exports its branch.
Whole-corpus relationship review remains available by selecting all in Studio or passing `--all` to the CLI.
Focused export coverage now asserts that the parent-child pattern respects a single selected doc.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `tests/python/test_docs_export.py`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Branch-level relationship exports now match the operator's checklist selection.
Large whole-corpus exports require an explicit Select all or `--all` action.
