---
doc_id: scripts
title: "Scripts"
added_date: 2026-04-23
last_updated: "2026-05-06 12:05"
parent_id: ""
sort_order: 130
---
# Scripts

This section describes the active repo scripts used to maintain site data.

# Introduction

All commands below assume you are in `dotlineform-site/`.

For local environment/bootstrap steps, see [Local Setup](/docs/?scope=studio&doc=local-setup).

## Purpose

This page is the high-level entry point for active repo scripts.
Command-level usage, flags, output paths, and operational notes live in the child docs below.
Local server architecture and future consolidation strategy live in **[Servers](/docs/?scope=studio&doc=servers)**.

The current script surface falls into four groups:

- docs-domain builders for scope-owned docs artifacts
- search builders for scope-owned search artifacts
- JSON-led catalogue maintenance and scoped rebuild helpers
- local tooling for audits, CSS analysis, and Studio write flows
- optional check profiles for larger-risk changes

## Common Runtime Assumptions

- run project commands from `dotlineform-site/`
- use project-local script paths
  - the two Ruby docs builders are executable directly:
    - `./scripts/build_docs.rb`
    - `./scripts/build_search.rb`
  - most Python entrypoints are currently invoked through `python3 ./scripts/...`
- docs-data rebuild command:

```bash
./scripts/build_docs.rb --write
```

- if `jekyll serve` or `bin/dev-studio` is already running, verify one-off builds to `/tmp/dlf-jekyll-build` rather than `_site/`
- media and generation scripts expect:
  - `DOTLINEFORM_PROJECTS_BASE_DIR`
  - `DOTLINEFORM_MEDIA_BASE_DIR`
- shared pipeline defaults live in `_data/pipeline.json`

## Current Build Boundaries

Docs-domain builds:

- `./scripts/build_docs.rb`
  - source docs:
    - `_docs_src/`
    - `_docs_library_src/`
  - outputs:
    - `assets/data/docs/scopes/studio/`
    - `assets/data/docs/scopes/library/`

Search builds:

- `./scripts/build_search.rb`
  - source indexes:
    - `assets/data/series_index.json`
    - `assets/data/works_index.json`
    - `assets/data/moments_index.json`
    - `assets/studio/data/tag_assignments.json`
    - `assets/studio/data/tag_registry.json`
    - `assets/data/docs/scopes/studio/index.json`
    - `assets/data/docs/scopes/library/index.json`
  - outputs:
    - `assets/data/search/catalogue/index.json`
    - `assets/data/search/studio/index.json`
    - `assets/data/search/library/index.json`

Catalogue/runtime maintenance:

- `./scripts/run_checks.py`
  - runs optional repo check profiles and writes local logs under `var/test-runs/`
- `./scripts/audit_studio_ready_state.py`
  - audits Studio route-ready template contracts and flags static routes that need a route-specific ready/busy implementation
- `./scripts/catalogue_json_build.py`
  - previews or runs a scoped JSON-source rebuild for one work or one series scope, including aggregate indexes and catalogue search
- `./scripts/verify_catalogue_field_registry.py`
  - verifies representative field-aware catalogue build plans without writing files
- `./scripts/docs/docs_export.py`
  - exports generated Docs Viewer data through source-controlled export configs into `var/studio/export-import/<scope>/exports/`; also powers the Studio Library export service path
- `./scripts/docs/docs_import.py`
  - parses staged Library import JSON/JSONL files under `var/studio/export-import/library/import-staging/` and returns a read-only structured report
- `./scripts/validate_catalogue_source.py`
  - validates canonical catalogue source JSON under `assets/studio/data/catalogue/`; `--target-media-section-schema` verifies migrated detail section fields
- `./scripts/migrate_catalogue_media_sections.py`
  - previews or applies the work-detail source migration from legacy `project_subfolder` to separated `details_subfolder`, `section_id`, and `section_title`
- `python3 ./scripts/export_catalogue_lookup.py`
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
  Audit Studio or Library docs links for missing targets and strict title mismatches.
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
  Run the local Docs Viewer create/archive/delete service with explicit write allowlists.
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
  Export generated Docs Viewer data through configured export patterns.
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
  Parse staged Library import data without writing source or preview files.
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
  Build srcset derivatives through the stable shell entrypoint and shared Python implementation.
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
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest)
