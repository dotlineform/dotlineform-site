---
doc_id: scripts
title: Scripts
added_date: 2026-04-23
last_updated: 2026-06-01
parent_id: dev-home
---
# Scripts

- This page is the high-level entry point for active repo scripts.
- Command-level usage, flags, output paths, and operational notes live in the child docs below.

The current script surface is organized by owner:

- catalogue-domain source, build, and write-service behavior
- analytics-domain tag metadata behavior
- Local Analytics app and Data Sharing route/API behavior
- UI Catalogue demo app behavior
- docs-domain builders for scope-owned docs artifacts
- search builders for scope-owned search artifacts
- Studio runtime services that are not domain-owned
- checks and media tooling
- shared infrastructure plus stable top-level command wrappers

## Common Runtime Assumptions

- All commands assume you are in `dotlineform-site/`.
- For local environment/bootstrap steps, see [Local Setup](/docs/?scope=studio&doc=local-setup).
- use project-local script paths
- if `jekyll serve` is already running, verify one-off builds to `/tmp/dlf-jekyll-build` rather than `_site/`
- media and generation scripts read `DOTLINEFORM_PROJECTS_BASE_DIR` from `var/local/site.env` for local runs
- R2 media publishing reads R2 credentials from `var/local/site.env` for local runs
- in cloud/Codespaces runs, those same keys should be provided through platform environment variables or secrets
- shared pipeline defaults live in `_data/pipeline.json`

## Folder Rules

- `studio/services/catalogue/` owns catalogue source models, lookup/build planning, generation, publication/delete/prose workflows, validation/export utilities, and the catalogue write service.
- `analytics-app/` owns the Local Analytics app server, Analytics route shells, Analytics runtime config, Analytics frontend modules, tag APIs, tag-domain helper services, Data Sharing route/API dispatch, and Analytics tests.
- `analytics-app/app/server/analytics_app/tag_services/` owns tag-domain source path contracts, validation, planning, dry-run/write transactions, route constants, and compact activity projection used by Analytics.
- `data-sharing/` owns headless Data Sharing config, adapter registry, package path contracts, workflow dispatch, package I/O, and documents/tags adapters. The active browser-facing Data Sharing HTTP endpoints are hosted by Local Analytics.
- `admin-app/ui-catalogue/` owns UI Catalogue demo source and static demo assets; Admin app server code owns the `/admin/ui-catalogue/...` routes and tests.
- `docs-viewer/` owns Docs Viewer config, source docs, browser runtime, local service, Docs Import, documents Data Sharing adapter behavior, live rebuild, generated-read, and docs-management behavior.
- `studio/services/catalogue/search/` owns Catalogue search build configuration and implementation.
- `docs-viewer/build/` owns Docs Viewer docs and search build implementations.
- `studio/app/server/studio/` owns non-domain-specific Studio runtime services such as audit and Studio catalogue/admin route dispatch services.
- `studio/checks/` owns standalone audits, risk checks, and verification commands.
- `studio/services/media/` owns media derivation and remote media publishing commands.
- top-level `scripts/` is reserved for stable wrappers that delegate into Studio/Docs Viewer owners when a wrapper is still intentionally supported.

Risk operations use the Local Studio app server.
Do not add a separate risk server for risk dashboards, app inventories, audit launching, unified activity review, or local risk artifacts; see [Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations).

Top-level survivors are intentional:

- Docs Viewer docs/search rebuilds use `./docs-viewer/build/build_docs.py` and `./docs-viewer/build/build_search.py` directly.
- Catalogue search uses `./studio/services/catalogue/search/build_search.py` directly.
- `make_srcset_images.sh`, when present, is the stable shell wrapper for the media implementation.
- shared infrastructure modules now live under `studio/shared/`.
- Ruby/Jekyll is public-site preview/build tooling only; active app-facing docs, search, and catalogue generation use Python builders.

## Current Build Boundaries

Docs-domain builds:

- `./docs-viewer/build/build_docs.py`
  - Docs Viewer-owned docs payload builder
  - source docs:
    - `docs-viewer/source/studio/`
    - `docs-viewer/source/analysis/`
    - `docs-viewer/source/library/`
  - outputs:
    - `docs-viewer/generated/docs/studio/`
    - `assets/data/docs/scopes/analysis/`
    - `assets/data/docs/scopes/library/`

Search builds:

- `./docs-viewer/build/build_search.py`
  - Docs Viewer-owned search builder for configured docs scopes
  - source docs:
    - `docs-viewer/source/studio/`
    - `docs-viewer/source/analysis/`
    - `docs-viewer/source/library/`
  - outputs:
    - `docs-viewer/generated/search/studio/index.json`
    - `assets/data/search/analysis/index.json`
    - `assets/data/search/library/index.json`
- `./studio/services/catalogue/search/build_search.py`
  - Catalogue-owned search builder
  - source indexes:
    - `assets/data/series_index.json`
    - `assets/data/works_index.json`
    - `assets/data/moments_index.json`
  - outputs:
    - `assets/data/search/catalogue/index.json`

Catalogue prose rendering:

- `studio/services/catalogue/generate_work_pages.py`
  - renders work, series, and moment Markdown from `studio/data/canonical/catalogue-markdown/`
  - writes rendered `content_html` into public catalogue payloads
  - uses the shared Python Markdown renderer at `studio/shared/python/markdown_renderer.py`
  - does not invoke Ruby, Bundler, or Jekyll

Catalogue/runtime maintenance:

- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py`
  - runs optional repo check profiles and writes local logs under `var/test-runs/`
- `$HOME/miniconda3/bin/python3 studio/checks/audit_projection_contract.py`
  - validates the Phase 6 projection contract manifest, checked-in public JSON leak rules, `_config.yml` exclusion policy, and optional built public output
- `$HOME/miniconda3/bin/python3 studio/checks/audit_studio_ready_state.py`
  - audits Studio route-ready template contracts and flags static routes that need a route-specific ready/busy implementation
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py`
  - previews or runs a scoped JSON-source rebuild for one work or one series scope, including aggregate indexes and catalogue search
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py`
  - verifies representative field-aware catalogue build plans without writing files
- `$HOME/miniconda3/bin/python3 docs-viewer/services/docs_export.py`
  - prepares Docs Viewer source metadata through source-controlled sharing profiles into `var/analytics/data-sharing/<scope>/exports/`; also powers the Library documents adapter used by Analytics Data Sharing
- `$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py`
  - parses staged Library returned-package JSON/JSONL files under `var/analytics/data-sharing/library/import-staging/` and returns a structured review report
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py`
  - validates canonical catalogue source JSON under `studio/data/canonical/catalogue/`; `--target-media-section-schema` verifies migrated detail section fields
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/export_catalogue_lookup.py`
  - exports derived Studio lookup JSON from canonical source into `studio/data/generated/catalogue-lookup/`
- `bash scripts/make_srcset_images.sh`
  - builds derivative image outputs when media work is needed outside the Studio metadata flow

## Script References

- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
  Run optional check profiles and capture local run logs for larger-risk changes.
- [Projection Contract Audit](/docs/?scope=studio&doc=scripts-audit-projection-contract)
  Validate the source/projection manifest and public/local build boundary.
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
  Audit Studio route-ready template contracts and static-route drift.
- [Studio Audit Runner](/docs/?scope=studio&doc=scripts-studio-audit-service)
  Maintain the allowlisted audit runner used by `/studio/audits/?mode=manage`; the active HTTP endpoints are served by the local Studio app.
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
  Run Local Studio, Local Analytics, UI Catalogue, public-site preview, and Docs Viewer either independently or through the sibling-service `bin/local-all` runner.
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
  Watch docs source roots and rebuild same-scope docs payloads plus docs search during local development.
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
  Audit Studio or Library docs links for missing targets.
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
  Maintain the standalone Docs Viewer service and shared management API dispatcher.
- [Documents Package Preparation Script](/docs/?scope=studio&doc=scripts-docs-export)
  Prepare Docs Viewer source metadata through configured documents Data Sharing profiles.
- [Documents Returned Package Script](/docs/?scope=studio&doc=scripts-docs-import)
  Parse staged Library returned packages and render Markdown review artifacts without writing source files.
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
  Build srcset derivatives through the stable shell entrypoint and shared Python implementation.
- [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2)
  Preview or upload approved catalogue primary-image derivatives to Cloudflare R2.
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
  Preview or run the Phase 5 scoped JSON-source rebuild flow for one work.
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
  Verify representative field-aware catalogue build plans and fallback behavior.
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
  Validate canonical catalogue source JSON and inspect source-adjacent project state.
- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report)
  Report source project folders and primary images that are not represented by `works.json`.
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
  Export derived Studio lookup payloads for focused editor reads.
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
  Run the local Studio catalogue source save service with explicit write allowlists.
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit)
  Audit typography and color literals across CSS files.
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
  Run read-only structural and contract checks across generated pages, JSON, and media.
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
  Define a shared local/cloud runtime contract for Codex Cloud, Codespaces, and R2-backed media workflows.

## Related References

- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec (v1)](/docs/?scope=studio&doc=css-audit-spec)
- CSS Audit Latest
