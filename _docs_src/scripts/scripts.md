---
doc_id: scripts
title: Scripts
last_updated: 2026-04-17
parent_id: ""
sort_order: 30
---

# Scripts

This section describes the scripts used to build site data.

# Introduction

All commands below assume you are in `dotlineform-site/`.

For local environment/bootstrap steps, see [Local Setup](/docs/?scope=studio&doc=local-setup).

## Purpose

This page is now the high-level entry point for repo scripts.
Command-level usage, flags, output paths, and operational notes now live in the child docs below.
Local server architecture and future consolidation strategy live in **[Servers](/docs/?scope=studio&doc=servers)**.

The current script surface falls into four groups:

- docs-domain builders for scope-owned docs artifacts
- search builders for scope-owned search artifacts
- catalogue/media generators for public site content
- local tooling for audits, CSS analysis, and Studio write flows

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

Catalogue/media builds:

- `./scripts/build_catalogue.py`
  - plans workbook-backed work/series/detail generation plus file-backed moment generation, canonical source-media changes, and current work/series/moment prose changes from `var/build_catalogue_state.json`, runs a shared workbook/source preflight, prunes stale repo-owned generated artifacts and stale local media outputs for removed rows, then orchestrates copy -> srcset -> generation for works, work details, and moments, then rebuilds catalogue search
  - writes a local build-activity journal and a Studio-facing recent-activity feed after successful non-dry-run runs
- `./scripts/generate_work_pages.py`
  - runs the shared workbook preflight, then builds catalogue pages plus runtime JSON, including:
    - `assets/data/series_index.json`
    - `assets/data/works_index.json`
    - `assets/data/moments_index.json`
- `./scripts/export_catalogue_source.py`
  - exports Phase 0 catalogue source JSON from `data/works.xlsx` into `assets/studio/data/catalogue/`
- `./scripts/validate_catalogue_source.py`
  - validates the exported catalogue source JSON
- `./scripts/compare_catalogue_sources.py`
  - compares workbook-normalized source records with JSON-normalized source records
- `./scripts/copy_draft_media_files.py`
  - stages source media into the srcset input folders
- `bash scripts/make_srcset_images.sh`
  - builds derivative image outputs from staged source media

## Script References

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
  Run the copy -> srcset -> generation pipeline from one entrypoint.
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
  Stage source media for works, work details, and moments from workbook-driven IDs.
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
  Build srcset derivatives through the stable shell entrypoint and shared Python implementation.
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
  Generate collection stubs, per-record JSON, and aggregate catalogue indexes.
- [Catalogue Source Export](/docs/?scope=studio&doc=scripts-catalogue-source)
  Export, validate, and compare Phase 0 catalogue source JSON.
- [Delete Work](/docs/?scope=studio&doc=scripts-delete-work)
  Remove one work from generated artifacts when workbook status is `delete`.
- [Delete Moment](/docs/?scope=studio&doc=scripts-delete-moment)
  Remove one moment from generated artifacts, with optional source-file deletion.
- [Delete Moment](/docs/?scope=studio&doc=scripts-delete-moment)
  Remove one moment from canonical source files and generated artifacts.
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
  Run the local Studio tag-save/import service with explicit write allowlists.
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
  Run the local Studio catalogue source save service with explicit write allowlists.
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit)
  Audit typography and color literals across CSS files.
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
  Run read-only structural and contract checks across generated pages, JSON, and media.
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
  Define a shared local/cloud runtime contract for Codex Cloud, Codespaces, and R2-backed media workflows.
- [Legacy Title Sort Fix](/docs/?scope=studio&doc=scripts-fix-missing-title-sort)
  Backfill legacy `_works` front matter that still depends on numeric `title_sort`.

## Related References

- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Servers](/docs/?scope=studio&doc=servers)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest)
