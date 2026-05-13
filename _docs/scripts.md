---
doc_id: scripts
title: Scripts
added_date: 2026-04-23
last_updated: "2026-05-13 18:15"
parent_id: site-docs
sort_order: 80
---
# Scripts

- This page is the high-level entry point for active repo scripts.
- Command-level usage, flags, output paths, and operational notes live in the child docs below.
- Local server architecture and future consolidation strategy live in **[Servers](/docs/?scope=studio&doc=servers)**.

The current script surface is organized by owner:

- catalogue-domain source, build, and write-service behavior
- analytics-domain tag metadata behavior
- docs-domain builders for scope-owned docs artifacts
- search builders for scope-owned search artifacts
- Studio runtime services that are not domain-owned
- checks and media tooling
- shared infrastructure plus stable top-level command wrappers

## Common Runtime Assumptions

- All commands assume you are in `dotlineform-site/`.
- For local environment/bootstrap steps, see [Local Setup](/docs/?scope=studio&doc=local-setup).
- use project-local script paths
- if `jekyll serve` or `bin/dev-studio` is already running, verify one-off builds to `/tmp/dlf-jekyll-build` rather than `_site/`
- media and generation scripts read `DOTLINEFORM_PROJECTS_BASE_DIR` from `var/local/site.env` for local runs
- R2 media publishing reads R2 credentials from `var/local/site.env` for local runs
- in cloud/Codespaces runs, those same keys should be provided through platform environment variables or secrets
- shared pipeline defaults live in `_data/pipeline.json`

## Folder Rules

- `scripts/catalogue/` owns catalogue source models, lookup/build planning, generation, publication/delete/prose workflows, validation/export utilities, and the catalogue write service.
- `scripts/analytics/` owns tag metadata services and helpers as the first Analytics metadata layer over catalogue works and series.
- `scripts/docs/` owns Docs Viewer build, Docs Import, documents Data Sharing adapter behavior, live rebuild, generated-read, and docs-management behavior.
- `scripts/search/` owns search build configuration and the search builder implementation.
- `scripts/studio/` owns non-domain-specific Studio runtime services such as audit, backup-retention, and Data Sharing dispatch services.
- `scripts/checks/` owns standalone audits and verification commands.
- `scripts/media/` owns media derivation and remote media publishing commands.
- top-level `scripts/` is reserved for stable wrappers and shared infrastructure modules.

Top-level survivors are intentional:

- `build_docs.rb` and `build_search.rb` are stable operational wrappers over domain-owned implementations.
- `run_checks.py` is the shared check-profile entrypoint.
- `make_srcset_images.sh` is the stable shell wrapper for the media implementation.
- `display_paths.py`, `local_env.py`, `pipeline_config.py`, `script_logging.py`, and `studio_activity.py` are shared infrastructure modules with cross-domain callers.
- `jekyll_markdown_renderer.rb`, `render_markdown_with_jekyll.rb`, and `jekyll_webrick_client_reset_filter.rb` are shared Ruby/Jekyll helpers.

## Current Build Boundaries

Docs-domain builds:

- `./scripts/build_docs.rb`
  - stable top-level wrapper for `scripts/docs/build_docs.rb`
  - source docs:
    - `_docs/`
    - `_docs_analysis/`
    - `_docs_library/`
  - outputs:
    - `assets/data/docs/scopes/studio/`
    - `assets/data/docs/scopes/analysis/`
    - `assets/data/docs/scopes/library/`

Search builds:

- `./scripts/build_search.rb`
  - stable top-level wrapper for `scripts/search/build_search.rb`
  - source indexes:
    - `assets/data/series_index.json`
    - `assets/data/works_index.json`
    - `assets/data/moments_index.json`
    - `assets/studio/data/tag_assignments.json`
    - `assets/studio/data/tag_registry.json`
    - `assets/data/docs/scopes/studio/index.json`
    - `assets/data/docs/scopes/analysis/index.json`
    - `assets/data/docs/scopes/library/index.json`
  - outputs:
    - `assets/data/search/catalogue/index.json`
    - `assets/data/search/studio/index.json`
    - `assets/data/search/analysis/index.json`
    - `assets/data/search/library/index.json`

Catalogue/runtime maintenance:

- `./scripts/run_checks.py`
  - runs optional repo check profiles and writes local logs under `var/test-runs/`
- `./scripts/checks/audit_studio_ready_state.py`
  - audits Studio route-ready template contracts and flags static routes that need a route-specific ready/busy implementation
- `./scripts/catalogue/catalogue_json_build.py`
  - previews or runs a scoped JSON-source rebuild for one work or one series scope, including aggregate indexes and catalogue search
- `./scripts/catalogue/verify_catalogue_field_registry.py`
  - verifies representative field-aware catalogue build plans without writing files
- `./scripts/docs/docs_export.py`
  - prepares generated Docs Viewer data through source-controlled sharing profiles into `var/studio/data-sharing/<scope>/exports/`; also powers the Studio Library Data Sharing prepare service path
- `./scripts/docs/docs_import.py`
  - parses staged Library returned-package JSON/JSONL files under `var/studio/data-sharing/library/import-staging/` and returns a structured review report
- `./scripts/catalogue/validate_catalogue_source.py`
  - validates canonical catalogue source JSON under `assets/studio/data/catalogue/`; `--target-media-section-schema` verifies migrated detail section fields
- `./scripts/catalogue/migrate_catalogue_media_sections.py`
  - previews or applies the work-detail source migration from legacy `project_subfolder` to separated `details_subfolder`, `section_id`, and `section_title`
- `./scripts/catalogue/export_catalogue_lookup.py`
  - exports derived Studio lookup JSON from canonical source into `assets/studio/data/catalogue_lookup/`
- `bash scripts/make_srcset_images.sh`
  - builds derivative image outputs when media work is needed outside the Studio metadata flow

## Script References

- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
  Run optional check profiles and capture local run logs for larger-risk changes.
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
  Audit Studio route-ready template contracts and static-route drift.
- [Studio Audit Service](/docs/?scope=studio&doc=scripts-studio-audit-service)
  Run the localhost allowlisted audit service used by `/studio/audits/`.
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
  Run the integrated local Studio development stack, including Jekyll, localhost write services, optional startup docs refreshes, and live docs watching.
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
  Watch docs source roots and rebuild same-scope docs payloads plus docs search during local development.
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
  Audit Studio or Library docs links for missing targets.
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
  Run the local Docs Viewer create/archive/delete service with explicit write allowlists.
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
  Export generated Docs Viewer data through configured export patterns.
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
  Parse staged Library import data without writing source or preview files.
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
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
  Run the local Studio tag-save/import service with explicit write allowlists.
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
  Run the local Studio catalogue source save service with explicit write allowlists.
- [Studio Backup Retention](/docs/?scope=studio&doc=scripts-studio-backup-retention)
  Prune local Studio backup files by newest-N-per-target retention.
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit)
  Audit typography and color literals across CSS files.
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
  Run read-only structural and contract checks across generated pages, JSON, and media.
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
  Define a shared local/cloud runtime contract for Codex Cloud, Codespaces, and R2-backed media workflows.
- [Legacy Title Sort Fix](/docs/?scope=studio&doc=scripts-fix-missing-title-sort)
  Backfill legacy `_works` front matter that still depends on numeric `title_sort`.

## Related References

- [Servers](/docs/?scope=studio&doc=servers)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec (v1)](/docs/?scope=studio&doc=css-audit-spec)
- CSS Audit Latest
