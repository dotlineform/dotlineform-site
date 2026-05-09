---
doc_id: site-request-scripts-directory-organization
title: Scripts Directory Organization Request
added_date: 2026-05-09
last_updated: "2026-05-09 22:35"
ui_status: done
parent_id: change-requests
sort_order: 212
viewable: true
---
# Scripts Directory Organization Request

Status: implemented.

## Purpose

Review and rationalize the `scripts/` directory layout so script location communicates ownership.
The immediate trigger is that `scripts/studio/catalogue_write_server.py` is catalogue-domain code, but most other catalogue modules live directly under `scripts/`.
That split makes the folder structure look accidental: some files are grouped by Studio runtime, some by data domain, and some are top-level because they predate the newer package-style boundaries.

The goal is to choose the right long-term structure rather than the lowest-churn structure.
After this request is implemented, the user should be able to look at `scripts/` and understand which code belongs to Catalogue, Analytics, Docs, Search, Studio runtime, local checks, media tooling, and shared script infrastructure.

## Current Problem

The current layout has useful subfolders, but their rule is inconsistent:

- `scripts/docs/` is a coherent Docs domain package containing the docs builder implementation, docs-management server, docs source-model helpers, import/export helpers, generated-read helpers, rebuild helpers, and docs route constants.
- `scripts/search/` contains search configuration and the search builder implementation, while `scripts/build_search.rb` remains the stable top-level command wrapper.
- `scripts/studio/` contains local Studio services such as `catalogue_write_server.py`, `tag_write_server.py`, and `audit_service.py`, but catalogue and Analytics tag domain helpers mostly do not live there.
- Catalogue has many top-level modules: `catalogue_source.py`, `catalogue_json_build.py`, `catalogue_lookup.py`, `catalogue_transactions.py`, `catalogue_routes.py`, `catalogue_publication.py`, and related helpers.
- Shared helpers such as `script_logging.py`, `studio_activity.py`, `pipeline_config.py`, and `display_paths.py` also live at top level, which is reasonable only if top level is explicitly treated as shared infrastructure plus stable entrypoints.

The result is not technically broken, but it creates avoidable navigation friction and makes future structural reviews harder.

## Desired Rule

Organize script files by ownership first, not by the UI page or local process that happens to call them.

UI/domain routing is the stronger architectural signal.
Script folders should follow the product/domain model rather than force it.
If a script's folder is hard to choose, treat that as useful evidence: either the domain model is still blurry, or the script mixes responsibilities that need to be separated before moving files.
For example, if Studio routes and docs say tags belong to Analytics but the local service still lives under `scripts/studio/`, that can be acceptable as historical placement, but it should not be mistaken for the target architecture.

Target rule:

- Domain packages own domain behavior.
- Runtime/server entrypoints live with the domain they mutate or serve, unless they are truly cross-domain Studio infrastructure.
- Top-level `scripts/` is reserved for stable cross-domain entrypoints and shared script infrastructure.
- Subfolders should be few, meaningful, and documented.
- Imports should point at the owning module path directly; do not keep broad compatibility re-exports after a move.

This implies that `catalogue_write_server.py` belongs with Catalogue code, not in a generic Studio folder.
It also implies that `tag_write_server.py` belongs with Analytics code, not in a generic Studio folder, because tags are the first implemented Analytics metadata layer over catalogue works and series.

## Target Structure Spec

Proposed target folders:

- `scripts/catalogue/`
  - Catalogue source model, lookup, field registry, save/build planning, publication/delete planning, prose import, workbook import, catalogue write server, catalogue route constants, catalogue transactions, and catalogue-specific validation/export helpers.
  - Candidate moves include current `catalogue_*` modules, `generate_work_pages.py` if it remains the internal catalogue JSON engine, `validate_catalogue_source.py`, `verify_catalogue_field_registry.py`, `export_catalogue_lookup.py`, and `migrate_catalogue_media_sections.py`.
- `scripts/docs/`
  - Keep as the Docs domain package.
  - Docs builder implementation lives here; the top-level `scripts/build_docs.rb` wrapper remains the stable operational command.
- `scripts/search/`
  - Search build configuration and search builder ownership.
  - Search builder implementation lives here; the top-level `scripts/build_search.rb` wrapper remains the stable operational command.
- `scripts/analytics/`
  - Analytics metadata and analysis services over catalogue works and series.
  - Candidate moves include `tag_write_server.py` and future tag helper modules extracted by the structural review.
  - Tags should be treated as the first implemented Analytics metadata layer, not as the whole Analytics model.
  - If broader Analytics registries and scoring workflows share the same local service, consider renaming `tag_write_server.py` to `analytics_server.py` instead of creating separate one-off servers.
- `scripts/studio/`
  - Studio runtime services that are not domain-specific, such as the audit service if it remains a Studio-resource service rather than a general checks command.
  - General-purpose admin and shared Studio functionality only; avoid placing domain-owned Catalogue or Analytics services here.
  - Do not use this folder as a catch-all for any localhost service.
- top-level `scripts/`
  - Cross-domain entrypoints such as `run_checks.py`.
  - Shared infrastructure modules such as script logging, shared Studio activity helpers, pipeline config loading, path display helpers, and other intentionally common utilities.
  - Small shell wrappers only when they are the stable public command surface and the implementation clearly lives under a domain package.

## Non-Goals

- Do not change runtime behavior, endpoint URLs, ports, request payloads, response payloads, backup behavior, generated output semantics, or dry-run behavior.
- Do not combine this with another large extraction of script internals.
- Do not move files only to reduce top-level file count.
- Do not leave permanent compatibility modules that make ownership ambiguous.
- Do not reorganize docs source folders, Studio route folders, generated data folders, or tests unless a script move requires test path updates.

## Implementation Plan

### Slice 1: inventory and move map

Produce a table of every current file under `scripts/`, excluding ignored generated caches, with:

- current path
- runnable entrypoint versus imported helper
- domain owner
- proposed target path
- public command examples that will need doc updates
- tests and docs that reference the path
- risk rating for import churn

Acceptance checks:

- the move map is reviewed before moving files
- every proposed top-level survivor has a reason
- every proposed subfolder has a short ownership rule

#### Slice 1 inventory result

Inventory date: 2026-05-09.

This slice does not move files. It records the proposed ownership map so the later implementation slices can update imports, command paths, docs, tests, and `bin/dev-studio` deliberately instead of treating path churn as incidental cleanup.

Reference coverage is intentionally compact:

- `Public refs` names runnable commands and `bin/dev-studio` startup usage that would need command-path updates or wrapper decisions.
- `Tests/docs refs` lists concrete test files when present and gives primary docs plus a `+N` count when historical request/change-log docs also mention the path.
- Before moving any row, rerun `rg` for the exact path and module stem because many Python tests import modules by name rather than by path.

Proposed folder ownership rules:

- `scripts/catalogue/` owns catalogue source models, lookup/build planning, generation, publication/delete/prose workflows, catalogue validation, catalogue route constants, catalogue write service, and source-adjacent project-state utilities.
- `scripts/analytics/` owns Analytics metadata over catalogue works and series. Current `tag_*` modules and the tag write service move here as the first Analytics implementation layer.
- `scripts/docs/` owns the Docs domain package and the docs builder implementation.
- `scripts/search/` owns search build configuration and search builder implementation.
- `scripts/studio/` owns non-domain-specific Studio runtime services and admin maintenance only.
- `scripts/media/` should own media derivation and remote media publishing tooling.
- `scripts/checks/` should own standalone audit/verification commands, while `scripts/run_checks.py` remains the stable top-level aggregator command.
- Top-level `scripts/` survivors must be either stable public entrypoints, shell wrappers over a moved implementation, or shared infrastructure modules with cross-domain callers.

| Current path | Role | Owner | Proposed target | Public refs | Tests/docs refs | Risk |
|---|---|---|---|---|---|---|
| `scripts/audit_site_consistency.py` | entrypoint | Checks | `scripts/checks/audit_site_consistency.py` | `./scripts/audit_site_consistency.py` | docs: `_docs/site-change-log-2026-05.md`, `_docs/site-change-log-2026-03-and-earlier.md` +11 | high |
| `scripts/audit_studio_ready_state.py` | entrypoint | Checks | `scripts/checks/audit_studio_ready_state.py` | `./scripts/audit_studio_ready_state.py` | docs: `_docs/site-change-log-2026-05.md`, `_docs/studio-audits.md` +6 | high |
| `scripts/build_docs.rb` | wrapper | Docs | stable wrapper for `scripts/docs/build_docs.rb` | `bin/dev-studio`, `./scripts/build_docs.rb` | tests: `tests/python/test_docs_write_rebuild.py`; docs: `_docs/site-request-docs-build-incremental.md`, `_docs/site-request-catalogue-delete-cleanup.md` +23 | high |
| `scripts/build_palette_data.py` | entrypoint | Media | `scripts/media/build_palette_data.py` | `./scripts/build_palette_data.py` | - | medium |
| `scripts/build_search.rb` | wrapper | Search | stable wrapper for `scripts/search/build_search.rb` | `bin/dev-studio`, `./scripts/build_search.rb` | tests: `tests/python/test_catalogue_build_commands.py`, `tests/python/test_docs_write_rebuild.py`; docs: `_docs/site-request-docs-build-incremental.md`, `_docs/site-request-catalogue-delete-cleanup.md` +23 | high |
| `scripts/catalogue_activity.py` | helper | Catalogue | `scripts/catalogue/catalogue_activity.py` | - | tests: `tests/python/test_catalogue_routes.py`, `tests/python/test_studio_activity_context.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_build_commands.py` | helper | Catalogue | `scripts/catalogue/catalogue_build_commands.py` | - | tests: `tests/python/test_catalogue_build_commands.py`; docs: `_docs/site-request-script-structural-review-catalogue-json-build.md`, `_docs/scripts-build-catalogue-json.md` +1 | medium |
| `scripts/catalogue_build_field_plan.py` | helper | Catalogue | `scripts/catalogue/catalogue_build_field_plan.py` | - | tests: `tests/python/test_catalogue_build_field_plan.py`; docs: `_docs/site-request-script-structural-review-catalogue-json-build.md`, `_docs/scripts-build-catalogue-json.md` +1 | medium |
| `scripts/catalogue_build_media.py` | helper | Catalogue | `scripts/catalogue/catalogue_build_media.py` | - | tests: `tests/python/test_catalogue_build_media.py`, `tests/python/test_catalogue_media_cleanup.py`; docs: `_docs/site-request-script-structural-review-catalogue-json-build.md`, `_docs/scripts-build-catalogue-json.md` +1 | medium |
| `scripts/catalogue_build_scopes.py` | helper | Catalogue | `scripts/catalogue/catalogue_build_scopes.py` | - | tests: `tests/python/test_catalogue_build_scopes.py`; docs: `_docs/site-request-script-structural-review-catalogue-json-build.md`, `_docs/scripts-build-catalogue-json.md` +1 | medium |
| `scripts/catalogue_cleanup.py` | helper | Catalogue | `scripts/catalogue/catalogue_cleanup.py` | - | tests: `tests/python/test_catalogue_cleanup.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-request-script-structural-review-catalogue-json-build.md` +2 | medium |
| `scripts/catalogue_delete_plans.py` | helper | Catalogue | `scripts/catalogue/catalogue_delete_plans.py` | - | tests: `tests/python/test_catalogue_delete_plans.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_field_registry.py` | helper | Catalogue | `scripts/catalogue/catalogue_field_registry.py` | - | docs: `_docs/site-change-log-2026-05.md`, `_docs/scripts-verify-catalogue-field-registry.md` | medium |
| `scripts/catalogue_generation_common.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_common.py` | - | docs: `_docs/site-change-log.md`, `_docs/site-request-script-structural-review-generate-work-pages.md` | medium |
| `scripts/catalogue_generation_indexes.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_indexes.py` | - | tests: `tests/python/test_catalogue_generation_indexes.py`; docs: `_docs/scripts-generate-work-pages.md`, `_docs/site-request-script-structural-review-generate-work-pages.md` +1 | medium |
| `scripts/catalogue_generation_moments.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_moments.py` | - | tests: `tests/python/test_catalogue_generation_moments.py`; docs: `_docs/scripts-generate-work-pages.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_generation_recent.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_recent.py` | - | tests: `tests/python/test_catalogue_generation_recent.py`; docs: `_docs/scripts-generate-work-pages.md`, `_docs/site-request-script-structural-review-generate-work-pages.md` +1 | medium |
| `scripts/catalogue_generation_records.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_records.py` | - | tests: `tests/python/test_catalogue_generation_records.py`; docs: `_docs/scripts-generate-work-pages.md`, `_docs/site-request-script-structural-review-generate-work-pages.md` | medium |
| `scripts/catalogue_generation_source_updates.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_source_updates.py` | - | tests: `tests/python/test_catalogue_generation_source_updates.py`; docs: `_docs/scripts-generate-work-pages.md`, `_docs/site-request-script-structural-review-generate-work-pages.md` +1 | medium |
| `scripts/catalogue_generation_writes.py` | helper | Catalogue | `scripts/catalogue/catalogue_generation_writes.py` | - | tests: `tests/python/test_catalogue_generation_writes.py`; docs: `_docs/site-request-script-structural-review-generate-work-pages.md` | medium |
| `scripts/catalogue_invalidation.py` | helper | Catalogue | `scripts/catalogue/catalogue_invalidation.py` | - | tests: `tests/python/test_catalogue_invalidation.py`, `tests/python/test_catalogue_lookup_refresh.py` +1; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_json_build.py` | entrypoint | Catalogue | `scripts/catalogue/catalogue_json_build.py` | `./scripts/catalogue_json_build.py` | docs: `_docs/scripts-main-pipeline.md`, `_docs/site-change-log-2026-05.md` +26 | high |
| `scripts/catalogue_lookup.py` | helper | Catalogue | `scripts/catalogue/catalogue_lookup.py` | - | tests: `tests/python/test_catalogue_lookup_refresh.py`; docs: `_docs/site-change-log-2026-05.md`, `_docs/scripts-catalogue-write-server.md` +5 | medium |
| `scripts/catalogue_lookup_refresh.py` | helper | Catalogue | `scripts/catalogue/catalogue_lookup_refresh.py` | - | tests: `tests/python/test_catalogue_lookup_refresh.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_prose_import.py` | helper | Catalogue | `scripts/catalogue/catalogue_prose_import.py` | - | tests: `tests/python/test_catalogue_prose_import.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-request-script-structural-review-catalogue-json-build.md` +2 | medium |
| `scripts/catalogue_publication.py` | helper | Catalogue | `scripts/catalogue/catalogue_publication.py` | - | tests: `tests/python/test_catalogue_publication.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-request-script-structural-review-catalogue-json-build.md` +2 | medium |
| `scripts/catalogue_routes.py` | helper | Catalogue | `scripts/catalogue/catalogue_routes.py` | - | tests: `tests/python/test_catalogue_routes.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_save_build.py` | helper | Catalogue | `scripts/catalogue/catalogue_save_build.py` | - | tests: `tests/python/test_catalogue_save_build.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_source.py` | helper | Catalogue | `scripts/catalogue/catalogue_source.py` | - | tests: `tests/python/test_catalogue_build_field_plan.py`, `tests/python/test_catalogue_build_media.py` +8; docs: `_docs/site-change-log-2026-05.md`, `_docs/scripts-catalogue-write-server.md` +15 | medium |
| `scripts/catalogue_source_mutation.py` | helper | Catalogue | `scripts/catalogue/catalogue_source_mutation.py` | - | tests: `tests/python/test_catalogue_source_mutation.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_transactions.py` | helper | Catalogue | `scripts/catalogue/catalogue_transactions.py` | - | tests: `tests/python/test_catalogue_transactions.py`; docs: `_docs/scripts-catalogue-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/catalogue_workbook_import.py` | helper | Catalogue | `scripts/catalogue/catalogue_workbook_import.py` | - | docs: `_docs/site-change-log-2026-05.md`, `_docs/site-request-catalogue-compatibility-cleanup.md` +4 | medium |
| `scripts/css_token_audit.py` | entrypoint | Checks | `scripts/checks/css_token_audit.py` | `./scripts/css_token_audit.py` | docs: `_docs/local-setup.md`, `_docs/scripts-css-token-audit.md` +2 | medium |
| `scripts/display_paths.py` | helper | Shared infrastructure | `scripts/display_paths.py` | - | docs: `_docs/site-change-log-2026-04.md` | low |
| `scripts/docs/docs_activity.py` | helper | Docs | `scripts/docs/docs_activity.py` | - | tests: `tests/python/test_docs_activity.py`; docs: `_docs/site-request-script-structural-review-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_broken_links.py` | entrypoint | Docs | `scripts/docs/docs_broken_links.py` | `./scripts/docs/docs_broken_links.py` | tests: `tests/python/test_docs_broken_links.py`; docs: `_docs/site-change-log-2026-04.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_export.py` | entrypoint | Docs | `scripts/docs/docs_export.py` | `./scripts/docs/docs_export.py` | tests: `tests/python/test_docs_export.py`; docs: `_docs/site-change-log-2026-05.md`, `_docs/site-request-script-structural-review.md` +9 | high |
| `scripts/docs/docs_generated_reads.py` | helper | Docs | `scripts/docs/docs_generated_reads.py` | - | tests: `tests/python/test_docs_generated_reads.py`; docs: `_docs/site-request-script-structural-review-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_html_import.py` | entrypoint | Docs | `scripts/docs/docs_html_import.py` | `./scripts/docs/docs_html_import.py` | docs: `_docs/site-change-log-2026-05.md`, `_docs/site-request-docs-html-inline-raster-media.md` +7 | high |
| `scripts/docs/docs_import.py` | entrypoint | Docs | `scripts/docs/docs_import.py` | `./scripts/docs/docs_import.py` | tests: `tests/python/test_docs_import.py`; docs: `_docs/library-import.md`, `_docs/site-change-log-2026-05.md` +10 | high |
| `scripts/docs/docs_import_source_service.py` | helper | Docs | `scripts/docs/docs_import_source_service.py` | - | tests: `tests/python/test_docs_import_service.py`; docs: `_docs/site-request-script-structural-review-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_live_rebuild_watcher.py` | entrypoint | Docs | `scripts/docs/docs_live_rebuild_watcher.py` | `bin/dev-studio`, `./scripts/docs/docs_live_rebuild_watcher.py` | tests: `tests/python/test_docs_live_rebuild_watcher.py`; docs: `_docs/site-change-log-2026-04.md`, `_docs/search-change-log.md` +5 | medium |
| `scripts/docs/docs_management_mutations.py` | helper | Docs | `scripts/docs/docs_management_mutations.py` | - | tests: `tests/python/test_docs_management_mutations.py`, `tests/python/test_docs_management_server.py`; docs: `_docs/scripts-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_management_routes.py` | helper | Docs | `scripts/docs/docs_management_routes.py` | - | tests: `tests/python/test_docs_activity.py`, `tests/python/test_docs_management_routes.py`; docs: `_docs/scripts-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_management_server.py` | entrypoint | Docs | `scripts/docs/docs_management_server.py` | `bin/dev-studio`, `./scripts/docs/docs_management_server.py` | tests: `tests/python/test_docs_import_service.py`, `tests/python/test_docs_management_routes.py` +1; docs: `_docs/library-import.md`, `_docs/site-change-log-2026-05.md` +20 | high |
| `scripts/docs/docs_scope_config.py` | helper | Docs | `scripts/docs/docs_scope_config.py` | - | docs: `_docs/site-change-log.md` | low |
| `scripts/docs/docs_scopes.json` | config | Docs | `scripts/docs/docs_scopes.json` | config read | docs: `_docs/site-change-log.md`, `_docs/scripts-docs-live-rebuild-watcher.md` +1 | medium |
| `scripts/docs/docs_source_model.py` | helper | Docs | `scripts/docs/docs_source_model.py` | - | tests: `tests/python/test_docs_import_service.py`, `tests/python/test_docs_live_rebuild_watcher.py` +3; docs: `_docs/scripts-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/docs_watch_suppression.py` | helper | Docs | `scripts/docs/docs_watch_suppression.py` | - | docs: `_docs/site-change-log-2026-04.md` | low |
| `scripts/docs/docs_write_rebuild.py` | helper | Docs | `scripts/docs/docs_write_rebuild.py` | - | tests: `tests/python/test_docs_write_rebuild.py`; docs: `_docs/site-request-script-structural-review-docs-management-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/docs/export_import_adapters.py` | helper | Docs | `scripts/docs/export_import_adapters.py` | - | tests: `tests/python/test_docs_import_service.py`, `tests/python/test_docs_management_server.py` +1; docs: `_docs/config-export-import-adapters.md`, `_docs/site-request-export-import-adapters.md` +2 | medium |
| `scripts/export_catalogue_lookup.py` | entrypoint | Catalogue | `scripts/catalogue/export_catalogue_lookup.py` | `bin/dev-studio`, `./scripts/export_catalogue_lookup.py` | docs: `_docs/scripts-catalogue-lookup.md`, `_docs/studio-runtime.md` +3 | high |
| `scripts/fix_missing_title_sort.py` | entrypoint | Catalogue | `scripts/catalogue/fix_missing_title_sort.py` | `./scripts/fix_missing_title_sort.py` | docs: `_docs/scripts-fix-missing-title-sort.md` | medium |
| `scripts/generate_work_pages.py` | entrypoint | Catalogue | `scripts/catalogue/generate_work_pages.py` | `./scripts/generate_work_pages.py` | tests: `tests/python/test_catalogue_build_commands.py`; docs: `_docs/site-change-log-2026-05.md`, `_docs/scripts-generate-work-pages.md` +29 | high |
| `scripts/jekyll_markdown_renderer.rb` | entrypoint | Shared infrastructure | `scripts/jekyll_markdown_renderer.rb` | `./scripts/jekyll_markdown_renderer.rb` | docs: `_docs/site-change-log-2026-04.md` | low |
| `scripts/jekyll_webrick_client_reset_filter.rb` | entrypoint | Shared infrastructure | `scripts/jekyll_webrick_client_reset_filter.rb` | `bin/dev-studio`, `./scripts/jekyll_webrick_client_reset_filter.rb` | docs: `_docs/site-change-log-2026-04.md`, `_docs/scripts-dev-studio.md` | low |
| `scripts/local_env.py` | helper | Shared infrastructure | `scripts/local_env.py` | - | tests: `tests/python/test_local_env.py`; docs: `_docs/site-change-log.md` | medium |
| `scripts/make_srcset_images.py` | entrypoint | Media | `scripts/media/make_srcset_images.py` | `./scripts/make_srcset_images.py` | tests: `tests/python/test_catalogue_build_media.py`, `tests/python/test_catalogue_cleanup.py` +1; docs: `_docs/site-change-log-2026-04.md`, `_docs/pipeline-config-refactor-plan.md` +2 | medium |
| `scripts/make_srcset_images.sh` | entrypoint | Media | Keep top-level shell wrapper; implementation to `scripts/media/make_srcset_images.py` | `./scripts/make_srcset_images.sh` | tests: `tests/python/test_catalogue_build_media.py`, `tests/python/test_catalogue_cleanup.py` +1; docs: `_docs/pipeline-config-refactor-plan.md`, `_docs/scripts.md` +1 | medium |
| `scripts/migrate_catalogue_media_sections.py` | entrypoint | Catalogue | `scripts/catalogue/migrate_catalogue_media_sections.py` | `./scripts/migrate_catalogue_media_sections.py` | tests: `tests/python/test_catalogue_media_section_migration.py`; docs: `_docs/site-request-catalogue-media-section-schema.md`, `_docs/scripts-catalogue-source.md` +1 | medium |
| `scripts/moment_sources.py` | helper | Catalogue | `scripts/catalogue/moment_sources.py` | - | tests: `tests/python/test_catalogue_build_scopes.py`, `tests/python/test_catalogue_delete_plans.py` +2; docs: `_docs/site-change-log-2026-05.md`, `_docs/site-request-catalogue-source-registry-drift-verification.md` +7 | medium |
| `scripts/pipeline_config.py` | helper | Shared infrastructure | `scripts/pipeline_config.py` | - | tests: `tests/python/test_catalogue_build_media.py`; docs: `_docs/pipeline-config-refactor-plan.md`, `_docs/moments-json-migration-plan.md` +2 | medium |
| `scripts/project_state_report.py` | entrypoint | Catalogue | `scripts/catalogue/project_state_report.py` | `./scripts/project_state_report.py` | docs: `_docs/scripts-project-state-report.md`, `_docs/scripts-catalogue-write-server.md` +4 | medium |
| `scripts/publish_media_to_r2.py` | entrypoint | Media | `scripts/media/publish_media_to_r2.py` | `./scripts/publish_media_to_r2.py` | tests: `tests/python/test_publish_media_to_r2.py`; docs: `_docs/scripts-publish-media-to-r2.md`, `_docs/local-setup.md` +2 | medium |
| `scripts/render_markdown_with_jekyll.rb` | entrypoint | Shared infrastructure | `scripts/render_markdown_with_jekyll.rb` | `./scripts/render_markdown_with_jekyll.rb` | docs: `_docs/moments-json-migration-plan.md` | low |
| `scripts/run_checks.py` | entrypoint | Shared entrypoint | `scripts/run_checks.py` | `./scripts/run_checks.py` | tests: `tests/README.md`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/library-import.md` +22 | high |
| `scripts/script_logging.py` | helper | Shared infrastructure | `scripts/script_logging.py` | - | - | low |
| `scripts/search/build_config.json` | config | Search | `scripts/search/build_config.json` | config read | docs: `_docs/search-validation-checklist.md`, `_docs/search-overview.md` +7 | medium |
| `scripts/series_ids.py` | helper | Catalogue | `scripts/catalogue/series_ids.py` | - | tests: `tests/python/test_catalogue_build_commands.py`, `tests/python/test_catalogue_build_field_plan.py` +11; docs: `_docs/site-change-log-2026-04.md` | medium |
| `scripts/studio/audit_service.py` | entrypoint | Studio runtime | `scripts/studio/audit_service.py` | `bin/dev-studio`, `./scripts/studio/audit_service.py` | docs: `_docs/site-change-log-2026-05.md`, `_docs/studio-runtime.md` +8 | high |
| `scripts/studio/catalogue_write_server.py` | entrypoint | Catalogue | `scripts/catalogue/catalogue_write_server.py` | `bin/dev-studio`, `./scripts/studio/catalogue_write_server.py` | tests: `tests/python/test_catalogue_routes.py`, `tests/python/test_studio_activity_feed.py`; docs: `_docs/site-change-log-2026-05.md`, `_docs/site-request-catalogue-delete-cleanup.md` +24 | high |
| `scripts/studio/tag_write_server.py` | entrypoint | Analytics | `scripts/analytics/tag_write_server.py` | `bin/dev-studio`, `./scripts/studio/tag_write_server.py` | tests: `tests/python/test_tag_activity.py`, `tests/python/test_tag_routes.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/offline-tag-assignments-implementation-breakdown.md` +12 | high |
| `scripts/studio_activity.py` | helper | Shared infrastructure | `scripts/studio_activity.py` | - | tests: `tests/python/test_docs_activity.py`, `tests/python/test_studio_activity_feed.py`; docs: `_docs/scripts-tag-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/studio_backup_retention.py` | entrypoint | Studio runtime | `scripts/studio/studio_backup_retention.py` | `bin/dev-studio`, `./scripts/studio_backup_retention.py` | tests: `tests/python/test_studio_backup_retention.py`; docs: `_docs/scripts-studio-backup-retention.md`, `_docs/site-change-log.md` +1 | high |
| `scripts/tag_activity.py` | helper | Analytics | `scripts/analytics/tag_activity.py` | - | tests: `tests/python/test_tag_activity.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/scripts-tag-write-server.md` | medium |
| `scripts/tag_alias_mutations.py` | helper | Analytics | `scripts/analytics/tag_alias_mutations.py` | - | tests: `tests/python/test_tag_alias_mutations.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/scripts-tag-write-server.md` +1 | medium |
| `scripts/tag_assignment_service.py` | helper | Analytics | `scripts/analytics/tag_assignment_service.py` | - | tests: `tests/python/test_tag_assignment_service.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/tag_promotion_mutations.py` | helper | Analytics | `scripts/analytics/tag_promotion_mutations.py` | - | tests: `tests/python/test_tag_promotion_mutations.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/scripts-tag-write-server.md` +1 | medium |
| `scripts/tag_registry_mutations.py` | helper | Analytics | `scripts/analytics/tag_registry_mutations.py` | - | tests: `tests/python/test_tag_registry_mutations.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/tag_routes.py` | helper | Analytics | `scripts/analytics/tag_routes.py` | - | tests: `tests/python/test_tag_activity.py`, `tests/python/test_tag_routes.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/tag_source_model.py` | helper | Analytics | `scripts/analytics/tag_source_model.py` | - | tests: `tests/python/test_tag_source_model.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/site-change-log.md` +1 | medium |
| `scripts/tag_write_transactions.py` | helper | Analytics | `scripts/analytics/tag_write_transactions.py` | - | tests: `tests/python/test_tag_write_transactions.py`; docs: `_docs/site-request-script-structural-review-tag-write-server.md`, `_docs/scripts-tag-write-server.md` +1 | medium |
| `scripts/validate_catalogue_source.py` | entrypoint | Catalogue | `scripts/catalogue/validate_catalogue_source.py` | `./scripts/validate_catalogue_source.py` | docs: `_docs/local-setup.md`, `_docs/site-request-catalogue-media-section-schema.md` +4 | medium |
| `scripts/verify_activity_contract.py` | entrypoint | Checks | `scripts/checks/verify_activity_contract.py` | `./scripts/verify_activity_contract.py` | tests: `tests/python/test_activity_contract.py`; docs: `_docs/site-request-studio-unified-activity-log-inventory.md` | medium |
| `scripts/verify_catalogue_field_registry.py` | entrypoint | Catalogue | `scripts/catalogue/verify_catalogue_field_registry.py` | `./scripts/verify_catalogue_field_registry.py` | tests: `tests/python/test_catalogue_field_registry.py`; docs: `_docs/site-change-log-2026-05.md`, `_docs/site-request-catalogue-source-registry-drift-verification.md` +8 | high |

### Slice 2: catalogue package move

Move Catalogue-owned modules into `scripts/catalogue/`.
This is the highest-value slice because it resolves the observed inconsistency around `catalogue_write_server.py`.

Expected work:

- move catalogue source/model/build/helper modules into `scripts/catalogue/`
- move `scripts/studio/catalogue_write_server.py` into `scripts/catalogue/`
- update imports, `bin/dev-studio`, tests, script docs, request docs, and command examples
- choose one import style and apply it consistently
- keep endpoint contracts and local service behavior unchanged

Acceptance checks:

- catalogue check profile passes
- `catalogue_write_server.py` still starts from its new path
- `bin/dev-studio` starts the catalogue service through the new path
- no duplicate catalogue route constants or broad compatibility re-export modules remain
- docs examples use the new command path

#### Slice 2 implementation result

Implemented 2026-05-09.

Catalogue-owned Python modules now live under `scripts/catalogue/` as a package.
The moved package includes source/model helpers, lookup/build helpers, generated-artifact helpers, validation/export utilities, `generate_work_pages.py`, `catalogue_json_build.py`, and the catalogue write server.
Imports now use explicit package paths such as `from catalogue.catalogue_source import ...` or `from catalogue import catalogue_routes`, rather than old top-level module imports.

Runtime and command-path updates:

- `bin/dev-studio` now starts the catalogue write service from `scripts/catalogue/catalogue_write_server.py`.
- `bin/dev-studio` now refreshes lookup data through `scripts/catalogue/export_catalogue_lookup.py`.
- `scripts/run_checks.py` now compiles and invokes the moved catalogue paths.
- `scripts/catalogue/catalogue_build_commands.py` now invokes the internal generator at `scripts/catalogue/generate_work_pages.py`.
- Active script docs now use `./scripts/catalogue/...` command examples.

Validation:

- Python syntax check for moved catalogue modules, updated catalogue tests, `scripts/run_checks.py`, and `scripts/audit_site_consistency.py`.
- Focused catalogue test sweep for `tests/python/test_catalogue_*.py`, `test_studio_activity_context.py`, and `test_studio_activity_feed.py`.
- `./scripts/run_checks.py --profile catalogue`.
- `./scripts/catalogue/catalogue_json_build.py --work-id 00001`.
- `./scripts/catalogue/export_catalogue_lookup.py`.
- `./scripts/catalogue/validate_catalogue_source.py`.
- dry-run catalogue write server start plus `GET /health` on port `8798`.

No compatibility modules were left at the old top-level paths.
Historical change-log and already-closed request docs may still mention the old paths as historical records; active script and runtime docs should use the new paths.

### Slice 3: Analytics tags and Studio runtime boundary

Run this slice after [Analytics Tag Route Cleanup Request](/docs/?scope=studio&doc=site-request-analytics-tag-route-cleanup) and the tag write-server structural review are complete.
At that point the Analytics tag service boundary, extracted helper modules, and server name should be stable enough to move without mixing package churn into behavior extraction.
Review `scripts/studio/tag_write_server.py`, any extracted top-level `scripts/tag_*.py` modules, and `scripts/studio/audit_service.py`.

Expected decision:

- move Analytics tag behavior to `scripts/analytics/`, because tags are conceptually Analytics metadata applied to catalogue works and series
- decide whether the service path becomes `scripts/analytics/tag_write_server.py` or `scripts/analytics/analytics_server.py`
- keep audit service under `scripts/studio/` only if it is genuinely Studio-runtime infrastructure
- document why any service remains under `scripts/studio/`

Acceptance checks:

- tag-service command paths and `bin/dev-studio` wiring are updated if moved
- route migration into `/studio/analytics/...` is already implemented, so script folder ownership can follow the settled Analytics UI domain
- focused tag tests still pass
- Studio audit docs still point at the correct path

#### Slice 3 implementation result

Slice 3 moved Analytics tag code into a concrete `analytics` Python package:

- `scripts/analytics/tag_write_server.py`
- `scripts/analytics/tag_routes.py`
- `scripts/analytics/tag_activity.py`
- `scripts/analytics/tag_source_model.py`
- `scripts/analytics/tag_assignment_service.py`
- `scripts/analytics/tag_registry_mutations.py`
- `scripts/analytics/tag_alias_mutations.py`
- `scripts/analytics/tag_promotion_mutations.py`
- `scripts/analytics/tag_write_transactions.py`

The service name remains `tag_write_server.py` because the write surface is still tag-specific.
The broader `analytics_server.py` name remains deferred until non-tag Analytics metadata or scoring writes share the same loopback-service contract.

`bin/dev-studio` now starts the tag write service from `scripts/analytics/tag_write_server.py`.
The moved modules import each other through the `analytics.*` package boundary, and tag tests import package modules rather than loose top-level `tag_*` modules.

`scripts/studio/audit_service.py` remains under `scripts/studio/` because it is Studio runtime infrastructure: it exposes allowlisted local audit checks for Studio tooling rather than owning Catalogue, Analytics, Docs, or Search data-domain behavior.

### Slice 4: docs and search entrypoint consistency

Review top-level `build_docs.rb` and `build_search.rb`.

Decision options:

- move the implementation commands under `scripts/docs/` and `scripts/search/`, updating docs and callers
- keep top-level commands as stable cross-domain entrypoints, but document that they are top-level because they are common operational commands

Acceptance checks:

- docs/search build commands in repo docs match the chosen target
- docs and search check profiles still pass
- no stale command paths remain in `_docs/`, tests, or `bin/`

#### Slice 4 implementation result

Slice 4 split implementation ownership from the stable command surface:

- `./scripts/build_docs.rb` remains the supported operational command and now wraps `scripts/docs/build_docs.rb`
- `./scripts/build_search.rb` remains the supported operational command and now wraps `scripts/search/build_search.rb`

This keeps existing docs, services, and runbook commands stable while making the implementation location match the Docs and Search domains.
The wrappers are intentionally not compatibility clutter; they are the public command API for common build operations.

### Slice 5: shared infrastructure and final closeout

Review top-level shared modules and entrypoints after domain moves are complete.

Expected work:

- confirm which helpers should remain top-level shared infrastructure
- decide whether any shared package name is clearer than top-level helper modules
- update [Scripts](/docs/?scope=studio&doc=scripts) with the final folder rules
- update relevant script reference docs
- run targeted checks plus `./scripts/run_checks.py` profiles proportional to moved domains
- rebuild Studio docs/search payloads

Acceptance checks:

- `scripts/` root is small enough to scan and every remaining file has a documented reason
- domain packages have coherent ownership
- command examples use project-local paths
- no moved behavior is still tested through old path compatibility wrappers
- no stale path references remain in docs, tests, `bin/`, or CI-like check scripts

#### Slice 5 implementation result

Implemented 2026-05-09.

Final owner folders are now concrete:

- `scripts/checks/` owns standalone audits and verification commands:
  - `audit_site_consistency.py`
  - `audit_studio_ready_state.py`
  - `css_token_audit.py`
  - `verify_activity_contract.py`
- `scripts/media/` owns media tooling:
  - `build_palette_data.py`
  - `make_srcset_images.py`
  - `publish_media_to_r2.py`
- `scripts/studio/` owns non-domain-specific Studio runtime services:
  - `audit_service.py`
  - `studio_backup_retention.py`

Top-level `scripts/` is now reserved for:

- stable command wrappers:
  - `build_docs.rb`
  - `build_search.rb`
  - `make_srcset_images.sh`
- the shared check-profile entrypoint:
  - `run_checks.py`
- shared infrastructure modules:
  - `display_paths.py`
  - `local_env.py`
  - `pipeline_config.py`
  - `script_logging.py`
  - `studio_activity.py`
- shared Ruby/Jekyll helpers:
  - `jekyll_markdown_renderer.rb`
  - `jekyll_webrick_client_reset_filter.rb`
  - `render_markdown_with_jekyll.rb`

Callers and checks now use owner paths directly:

- `bin/dev-studio` runs backup retention through `scripts/studio/studio_backup_retention.py`
- the Studio audit service runs the ready-state audit through `scripts/checks/audit_studio_ready_state.py`
- `scripts/run_checks.py` compiles and invokes the moved paths
- focused tests load moved implementations from their owner folders
- active script docs and examples use project-local owner paths

No broad compatibility Python modules were left at the old root paths.
Historical change-log/archive entries can still mention old paths as historical records.

Final validation:

- Python syntax check for moved Checks, Media, Studio runtime, shared runner, and focused test files.
- Focused tests for activity contract, R2 publishing, and Studio backup retention.
- Ready-state audit through the new Checks path.
- `./scripts/run_checks.py --profile quick`.
- `./scripts/build_docs.rb --scope studio --write`.
- `./scripts/build_search.rb --scope studio --write`.

## Benefits

- makes script ownership visible from the filesystem
- removes the current Catalogue/Studio placement ambiguity
- gives future structural reviews a cleaner package boundary
- reduces the chance that new Catalogue helpers are added at top level by inertia
- clarifies whether top-level scripts are public entrypoints or shared infrastructure

## Risks

- moving many files can create import churn without behavior changes
- path updates can miss docs, tests, local service startup commands, or smoke helpers
- package-style imports may behave differently when scripts are run directly unless entrypoint patterns are chosen carefully
- command path changes can break local notes outside the repo
- broad compatibility wrappers would reduce short-term pain but undermine the ownership goal if left in place

## Resolved Decisions

- `build_docs.rb` and `build_search.rb` stay as stable top-level wrappers over domain-owned implementations.
- the Analytics local service remains `tag_write_server.py` until non-tag Analytics writes share the same loopback-service contract.
- Studio tag UI route migration was handled separately before the Analytics script move.
- shared helpers remain top-level infrastructure modules because the root is now small and the helpers have cross-domain callers.
- no old root Python compatibility wrappers were kept; active repo docs and checks use owner paths directly.

