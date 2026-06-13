---
doc_id: site-request-canonical-static-site-root-tasks
title: Canonical Static Site Root Migration Tasks
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-canonical-static-site-root
---
# Canonical Static Site Root Migration Tasks

This is the delivery specification for Batch 1 in [Canonical Static Site Root Request](/docs/?scope=studio&doc=site-request-canonical-static-site-root).

Purpose: migrate the public site to tracked `site/` source and move public-site tooling to validation-only `site-tools/`.

## Steer For These Tasks

- Keep the migration direct: no aliases, compatibility layers, redirects, or old command shims.
- Treat `site/` as the static document root. Filesystem path `site/assets/...` serves public URL `/assets/...`.
- Prefer config retargeting over call-site edits when apps already resolve public paths through config.
- Keep `bin/site-validate` limited to deploy-artifact readiness. Do not mix site content audits into deploy validation.
- Keep site audit checks available as separate design-time or general audit responsibilities.
- Keep `site-tools/` simpler than the current public-site build package, while still modularizing Python validation code by responsibility when needed.
- Do not introduce a new generated-payload review or gating copy outside `site/`.

## Deliverables

- Tracked canonical static site root at `site/`.
- Validation-only tooling under `site-tools/`.
- `bin/site-validate` command.
- Direct static preview that serves `site/`.
- Studio, Docs Viewer, Analytics, Data Sharing, Admin audit, and workflow paths retargeted away from root-level `assets/` and `_public_site/`.
- GitHub Actions workflow that validates and uploads `site/`.
- Stable documentation updated for the new public-site root and validation workflow.

## Implementation And Policy Guidance

- The parent request owns the design decisions and should not duplicate implementation task state.
- Public route HTML is canonical source under `site/`; do not add build-time shell generation in this migration.
- Public URLs remain unchanged unless a separate request approves route changes.
- Keep canonical source data outside `site/`; only deployable public files belong there.
- If a hardcoded root-level `assets/` filesystem path is found, either move it into owning config, remove it, or document the reason it remains.
- If an existing test or fixture depends on retired paths, retarget the test rather than adding compatibility.

## Proposed Verification Set

- Focused tests for `bin/site-validate` against `site/`.
- Focused tests for Studio catalogue output path configuration.
- Focused tests for Docs Viewer public publish paths and route config paths.
- Focused tests for Analytics and Data Sharing reads of public catalogue indexes.
- Admin projection-contract or public-surface audit updated for `site/`.
- GitHub Actions workflow syntax or dry-run validation where practical.
- Representative public route smoke checks only when touched implementation warrants browser verification.

## Tasks

### Batch 1: Canonical Static Site Root Migration

| ID | status | action |
| --- | --- | --- |
| 1.1 | done | Audit root-level `assets/` path ownership: identify config-driven reads/writes, hardcoded defaults, and path configs that must retarget public outputs to `site/assets/...`. |
| 1.1a | done | Create a Studio catalogue public-output path contract and retarget catalogue generated JSON, catalogue search, thumbnail outputs, cleanup, and preview code to it. |
| 1.1b | done | Retarget Docs Viewer public publish paths, public output-root validation, and interactive asset filesystem paths to `site/assets/...` while preserving public `/assets/...` URLs. |
| 1.1c | done | Retarget Analytics and Data Sharing public catalogue input paths to explicit configured `site/assets/data/...` sources, removing defensive defaults and old compatibility fallbacks. |
| 1.1d | done | Retarget local same-origin static serving so Studio and Docs Viewer serve `/assets/...` from `site/assets/...` during local app workflows. |
| 1.1e | done | Retarget Admin check, projection-contract, and site-audit path contracts from root `assets/...` to `site/assets/...` where they refer to filesystem paths. |
| 1.2 | done | Move `_public_site/` to `site/` as tracked canonical source and delete `_public_site/.public-site-artifact` rather than replacing it. |
| 1.3 | done | Move public-site tooling from `public-site/` to `site-tools/`, simplifying it to validation/audit responsibilities only. |
| 1.4 | done | Replace `bin/public-site-build` with `bin/site-validate`, with no command alias or compatibility shim. |
| 1.5 | done | Update preview tooling so it serves `site/` directly and does not rebuild or copy the public tree. |
| 1.6 | done | Remove or rename root-level `assets/` once no active consumer remains. |
| 1.7 | done | Update GitHub Actions to validate and upload `site/`, with no retired build/copy command. |
| 1.8 | done | Update stable docs that still describe `_public_site/`, `public-site/build/`, or root `assets/` as the public deploy surface. |

## Completed Verification

- Task 1.1 audit completed by source/config search and targeted file reads. No tests were run because no runtime code was changed.
- Tasks 1.1a-1.1e implementation completed with syntax checks, JSON parsing checks, and focused path-contract tests. Docs Viewer payloads were not rebuilt.
- Task 1.2 completed by moving `_public_site/` to `site/`, removing the generated-artifact marker, and removing the ignore rule that kept the public tree untracked.
- Tasks 1.3-1.5 and 1.7 completed by replacing the public-site builder with `site-tools/` validation, replacing command wrappers with `bin/site-validate` and `bin/site-preview`, serving `site/` directly for preview, and updating GitHub Actions to validate and upload `site/`.
- Site validation verification: `bin/site-validate`
- Tooling syntax and config verification: `bash -n bin/site-validate bin/site-preview bin/local-all`; `$HOME/miniconda3/bin/python3 -m py_compile site-tools/site_validate.py site-tools/site_tools/config.py site-tools/site_tools/validation.py docs-viewer/build/build_docs.py docs-viewer/services/docs_scope_config.py studio/services/media/publish_media_to_r2.py admin-app/commands/run_checks.py studio/shared/python/studio_python_paths.py studio/shared/python/local_env.py studio/shared/python/pipeline_config.py studio/shared/python/script_logging.py`; JSON parse checks for `site-tools/config/site-tools.json`, `admin-app/checks/config/admin-checks.json`, and `admin-app/checks/projection_contract.json`; `git diff --check`.
- Focused migration tests: `$HOME/miniconda3/bin/python3 -m pytest -q site-tools/tests/test_site_validate.py docs-viewer/tests/python/test_build_docs_python.py studio/tests/python/test_publish_media_to_r2.py studio/tests/python/test_studio_app_server.py`; `$HOME/miniconda3/bin/python3 -m pytest -q analytics-app/tests/python/test_tags_data_sharing_adapter.py docs-viewer/tests/python/test_docs_import_service.py::test_html_import_copies_role_marked_interactive_assets docs-viewer/tests/python/test_docs_management_service.py::test_docs_scope_config_requires_public_readonly_publish_outputs docs-viewer/tests/python/test_docs_viewer_service.py`
- Expanded root-marker and public-output fixture verification: `$HOME/miniconda3/bin/python3 -m pytest -q studio/tests/python/test_local_env.py analytics-app/tests/python/test_analytics_data_sharing_api.py docs-viewer/tests/python/test_docs_import.py docs-viewer/tests/python/test_docs_export.py docs-viewer/tests/python/test_docs_broken_links.py`
- Task 1.6 completed by retargeting remaining active root `assets/` filesystem consumers to `site/assets/...` or current owner paths, then deleting the tracked root `assets/` tree.
- Task 1.8 completed by updating stable operational docs for `site/`, `site-tools/`, `bin/site-validate`, `bin/site-preview`, `SITE_*` preview env vars, and `site/assets/...` filesystem paths. Docs Viewer generated payloads were not rebuilt.
- Task 1.6/1.8 verification: root `assets/` absent and `site/assets/` present; active stale-reference scan for retired root `assets/`, `_public_site`, `public-site/build`, `public-site/config`, old public-site commands, and old `PUBLIC_SITE_*` env names; `bash -n bin/site-validate bin/site-preview bin/local-all`; py-compile for added/modified Python files; `$HOME/miniconda3/bin/python3 -m pytest -q studio/tests/python/test_studio_app_server.py analytics-app/tests/python/test_analytics_app_server.py site-tools/tests/test_site_validate.py docs-viewer/tests/python/test_docs_data_sharing_source_metadata.py docs-viewer/tests/python/test_docs_write_rebuild.py`; `bin/site-validate`; `git diff --check`.
- Studio/Analytics verification: `$HOME/miniconda3/bin/python3 -m pytest -q studio/tests/python/test_catalogue_build_commands.py studio/tests/python/test_catalogue_build_media.py studio/tests/python/test_catalogue_cleanup.py studio/tests/python/test_catalogue_transactions.py studio/tests/python/test_catalogue_search_builder_python.py analytics-app/tests/python/test_tags_data_sharing_adapter.py analytics-app/tests/python/test_analytics_app_server.py`
- Docs Viewer verification: `$HOME/miniconda3/bin/python3 -m pytest -q docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_docs_import_service.py::test_html_import_copies_role_marked_interactive_assets docs-viewer/tests/python/test_docs_import_service.py::test_html_import_reports_role_marked_interactive_assets_in_preview_only docs-viewer/tests/python/test_docs_import_service.py::test_html_import_confirms_existing_role_marked_interactive_asset_target docs-viewer/tests/python/test_docs_management_service.py::test_docs_scope_config_requires_public_readonly_publish_outputs docs-viewer/tests/python/test_docs_management_service.py::test_docs_scope_config_rejects_manage_mode_assets_outputs docs-viewer/tests/python/test_docs_management_service.py::test_scope_create_preview_blocks_committed_manage_mode_assets_regression docs-viewer/tests/python/test_docs_management_service.py::test_scope_create_apply_blocks_committed_manage_mode_assets_regression docs-viewer/tests/python/test_docs_generated_reads.py docs-viewer/tests/python/test_docs_publish_gate.py`

## Task 1.1 Findings

Summary: the migration is only partly a config retarget.
Docs Viewer public publish paths are mostly config-owned, but Studio catalogue public outputs and local public-asset serving still have several hardcoded root `assets/` filesystem defaults.

### Config-Owned Or Mostly Config-Owned Paths

| Area | current owner | finding |
| --- | --- | --- |
| Public-site assembly | `public-site/config/public-site.json` | This is build/copy configuration, not a durable path owner for the new model. It should be retired or reduced into `site-tools/` validation config. |
| Docs Viewer public scopes | `docs-viewer/config/scopes/docs_scopes.json` | `publish_output`, `publish_search_output`, and `repo_assets_path_prefix` are explicit config fields. These are good candidates for direct retargeting to `site/assets/...`. |
| Docs Viewer public route URLs | `docs-viewer/config/routes/*.json`, generated defaults | Browser URLs such as `/assets/data/docs/scopes/...` should remain `/assets/...` because `site/` is the document root. These are URL config values, not filesystem paths. |
| Analytics browser reads | `analytics-app/app/frontend/config/analytics-config.json` | Browser read URLs are config-owned and can remain `/assets/...`; local server/static mapping must serve them from `site/assets/...`. |
| Data Sharing tag source reads | `data-sharing/config/adapters.json` | `sources.series` and `sources.works` are config-owned and should retarget to `site/assets/data/...`. |
| Search runtime policy URL | `assets/data/search/policy.json` and `assets/js/search/search-policy.js` fallback | The browser URL can remain `/assets/data/search/catalogue/index.json`. The filesystem location should move with the public site file to `site/assets/data/search/policy.json`. |

### Hardcoded Filesystem Defaults To Retarget Or Move Into Config

| Area | active files | finding |
| --- | --- | --- |
| Catalogue generated JSON | `studio/services/catalogue/generate_work_pages.py`, `studio/services/catalogue/catalogue_build_commands.py` | The generator exposes output path flags, but the scoped build command does not pass them and the CLI defaults point at root `assets/...`. Add a small catalogue public-output path contract or config, then have the command builder pass those paths. |
| Catalogue search build | `studio/services/catalogue/search/build_search.py` | `CATALOGUE_DEFAULTS` and `works_json_dir` are hardcoded to root `assets/...`. `build_config.json` owns field/source policy, not paths. Move path ownership into a small config or shared catalogue public-output path contract. |
| Catalogue local thumbnail outputs | `studio/services/catalogue/catalogue_build_media.py` | Thumbnail output dirs are direct `repo_root / "assets" / ...` joins. They need to resolve through the same public-output path contract. |
| Catalogue cleanup and preview | `studio/services/catalogue/catalogue_cleanup.py`, `studio/services/catalogue/catalogue_build_scopes.py` | Cleanup/update previews and existence checks hardcode root `assets/...`. These should read from the shared output path contract rather than duplicating strings. |
| Docs Viewer public output roots | `docs-viewer/services/docs_scope_config.py`, `docs-viewer/services/docs_scope_manifest.py` | Scope config owns concrete paths, but validation/planning constants still hardcode root `assets/data/...`. Retarget constants to the configured site filesystem root or teach them the public output root. |
| Docs Viewer interactive assets | `docs-viewer/build/build_docs.py`, `docs-viewer/services/docs_import_source_service.py` | Interactive docs asset paths hardcode `assets/docs/interactive/...`. Retarget through Docs Viewer scope/import media config or a dedicated Docs Viewer public asset root constant. |
| Data Sharing fallback paths | `data-sharing/data_sharing/adapters/tags/adapter.py`, `analytics-app/app/server/analytics_app/tag_services/tag_source_paths.py` | Adapter config owns these paths. Remove the defensive defaults for missing adapter `sources.*` values and remove the explicit compatibility branch from old `studio/data/canonical/catalogue/series.json` to `assets/data/series_index.json`; require explicit configured sources instead. |
| Local Studio static serving | `studio/app/server/studio/studio_app_server.py` | `/assets/...` static prefixes currently resolve from repo root. After the move, local Studio should serve same-origin `/assets/...` reads from `site/assets/...`. The public-site preview base remains for opening or inspecting public pages, not for Studio runtime data fetches. |
| Docs Viewer local static serving | `docs-viewer/services/docs_viewer_service.py` | Public-safe `/assets/data/` and `/assets/docs/` local reads assume root `assets/...`. They need retargeting to `site/assets/...` for local service/static reads. |
| Admin checks and audits | `admin-app/checks/*.py`, `admin-app/checks/*.json`, `admin-app/commands/run_checks.py` | These are audit/test/report path contracts. They should be updated as design-time checks for `site/`, but they are not deploy-validation inputs. |

### URL Paths That Should Not Change

- Public browser URLs under `/assets/...` remain correct when `site/` is the document root.
- Public JS fallback URLs such as `/assets/data/search/catalogue/index.json` remain URL contracts, not filesystem root `assets/` dependencies.
- Studio and Analytics browser configs that expose `/assets/...` URLs do not need public URL changes; their local servers or preview targets need to serve those URLs from `site/assets/...`.

### Recommended Implementation Shape

Do not retarget these paths with scattered string replacements.
Create or identify small owner-level path contracts:

- Studio catalogue public output paths for indexes, per-record JSON, search index, and thumbnails.
- Docs Viewer public output root paths for docs/search and public interactive assets.
- Analytics/Data Sharing public catalogue index input paths.
- Site-tools validation paths for deploy-root-only files such as `CNAME`, `.nojekyll`, icons, and required route HTML.

Then update call sites to use those contracts and retarget the contracts to `site/assets/...`.

## Follow-On Tasks

- None yet.

## Batch Close

- When complete, update this task tracker with verification results, remaining risks, and any follow-on tasks discovered during implementation.
- Mark `ui_status` and task statuses only after the corresponding implementation and verification are complete.
