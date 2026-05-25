---
doc_id: scripts
title: Scripts
added_date: 2026-04-23
last_updated: 2026-05-25
parent_id: dev-home
sort_order: 7000
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
- if `jekyll serve` is already running, verify one-off builds to `/tmp/dlf-jekyll-build` rather than `_site/`
- media and generation scripts read `DOTLINEFORM_PROJECTS_BASE_DIR` from `var/local/site.env` for local runs
- R2 media publishing reads R2 credentials from `var/local/site.env` for local runs
- in cloud/Codespaces runs, those same keys should be provided through platform environment variables or secrets
- shared pipeline defaults live in `_data/pipeline.json`

## Folder Rules

- `studio/services/catalogue/` owns catalogue source models, lookup/build planning, generation, publication/delete/prose workflows, validation/export utilities, and the catalogue write service.
- `studio/services/analytics/` owns tag metadata services and helpers as the first Analytics metadata layer over catalogue works and series.
- `docs-viewer/` owns Docs Viewer config, source docs, browser runtime, local service, Docs Import, documents Data Sharing adapter behavior, live rebuild, generated-read, and docs-management behavior.
- `studio/services/catalogue/search/` owns Catalogue search build configuration and implementation.
- `docs-viewer/build/` owns Docs Viewer docs and search build implementations.
- `studio/app/server/studio/` owns non-domain-specific Studio runtime services such as audit, backup-retention, and Data Sharing dispatch services.
- `studio/checks/` owns standalone audits and verification commands.
- `studio/services/media/` owns media derivation and remote media publishing commands.
- top-level `scripts/` is reserved for stable wrappers that delegate into Studio/Docs Viewer owners.

Top-level survivors are intentional:

- `build_docs.rb` and `build_search.rb` are stable operational wrappers over domain-owned implementations.
- `make_srcset_images.sh`, when present, is the stable shell wrapper for the media implementation.
- shared infrastructure modules now live under `studio/shared/`.
- shared Ruby/Jekyll helpers now live under `studio/shared/ruby/` or the owning Docs Viewer build path.

## Current Build Boundaries

Docs-domain builds:

- `./scripts/build_docs.rb`
  - stable top-level wrapper for `docs-viewer/build/build_docs.rb`
  - source docs:
    - `docs-viewer/source/studio/`
    - `docs-viewer/source/analysis/`
    - `docs-viewer/source/library/`
  - outputs:
    - `assets/data/docs/scopes/studio/`
    - `assets/data/docs/scopes/analysis/`
    - `assets/data/docs/scopes/library/`

Search builds:

- `./scripts/build_search.rb`
  - stable top-level wrapper that dispatches through `studio/commands/search-adapters.json`
  - source indexes:
    - `assets/data/series_index.json`
    - `assets/data/works_index.json`
    - `assets/data/moments_index.json`
    - `studio/data/canonical/analytics/tag-assignments.json`
    - `studio/data/canonical/analytics/tag-registry.json`
    - `assets/data/docs/scopes/studio/index.json`
    - `assets/data/docs/scopes/analysis/index.json`
    - `assets/data/docs/scopes/library/index.json`
  - outputs:
    - `assets/data/search/catalogue/index.json`
    - `assets/data/search/studio/index.json`
    - `assets/data/search/analysis/index.json`
    - `assets/data/search/library/index.json`

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
  - prepares generated Docs Viewer data through source-controlled sharing profiles into `var/studio/data-sharing/<scope>/exports/`; also powers the Studio Library Data Sharing prepare service path
- `$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py`
  - parses staged Library returned-package JSON/JSONL files under `var/studio/data-sharing/library/import-staging/` and returns a structured review report
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py`
  - validates canonical catalogue source JSON under `studio/data/canonical/catalogue/`; `--target-media-section-schema` verifies migrated detail section fields
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/migrate_catalogue_media_sections.py`
  - previews or applies the work-detail source migration from legacy `project_subfolder` to separated `details_subfolder`, `section_id`, and `section_title`
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
  Run the integrated local Studio development stack, including Jekyll, localhost write services, optional startup docs refreshes, and live docs watching.
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
  Watch docs source roots and rebuild same-scope docs payloads plus docs search during local development.
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
  Audit Studio or Library docs links for missing targets.
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
  Maintain the standalone Docs Viewer service and shared management API dispatcher.
- [Documents Package Preparation Script](/docs/?scope=studio&doc=scripts-docs-export)
  Prepare generated Docs Viewer data through configured documents Data Sharing profiles.
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
- [Retired Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
  Records the retired standalone tag write service and the active local Studio analytics API replacement.
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

- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Servers](/docs/?scope=studio&doc=servers)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec (v1)](/docs/?scope=studio&doc=css-audit-spec)
- CSS Audit Latest
