---
doc_id: scripts
title: Scripts
last_updated: 2026-03-31
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

The current script surface falls into three groups:

- docs-domain builders for scope-owned docs and docs-search artifacts
- catalogue/media generators for public site content
- local tooling for audits, CSS analysis, and Studio write flows

## Common Runtime Assumptions

- run project commands from `dotlineform-site/`
- use project-local script paths
  - the two Ruby docs builders are executable directly:
    - `./scripts/build_docs_data.rb`
    - `./scripts/build_search_data.rb`
  - most Python entrypoints are currently invoked through `python3 ./scripts/...`
- docs-data rebuild command:

```bash
./scripts/build_docs_data.rb --write
```

- if `jekyll serve` or `bin/dev-studio` is already running, verify one-off builds to `/tmp/dlf-jekyll-build` rather than `_site/`
- media and generation scripts expect:
  - `DOTLINEFORM_PROJECTS_BASE_DIR`
  - `DOTLINEFORM_MEDIA_BASE_DIR`
- shared pipeline defaults live in `_data/pipeline.json`

## Current Build Boundaries

Docs-domain builds:

- `./scripts/build_docs_data.rb`
  - source docs:
    - `_docs_src/`
    - `_docs_library_src/`
  - outputs:
    - `assets/data/docs/scopes/studio/`
    - `assets/data/docs/scopes/library/`
- `./scripts/build_search_data.rb`
  - source docs indexes:
    - `assets/data/docs/scopes/studio/index.json`
    - `assets/data/docs/scopes/library/index.json`
  - outputs:
    - `assets/data/search/studio/index.json`
    - `assets/data/search/library/index.json`

Catalogue/media builds:

- `./scripts/run_draft_pipeline.py`
  - orchestrates copy -> srcset -> generation for works, work details, and moments
- `./scripts/generate_work_pages.py`
  - builds catalogue pages plus runtime JSON, including:
    - `assets/data/series_index.json`
    - `assets/data/works_index.json`
    - `assets/data/moments_index.json`
    - `assets/data/search/catalogue/index.json`
- `./scripts/copy_draft_media_files.py`
  - stages source media into the srcset input folders
- `bash scripts/make_srcset_images.sh`
  - builds derivative image outputs from staged source media

## Script References

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Main Draft Pipeline](/docs/?scope=studio&doc=scripts-main-pipeline)
  Run the copy -> srcset -> generation pipeline from one entrypoint.
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
  Stage source media for works, work details, and moments from workbook-driven IDs.
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
  Build srcset derivatives through the stable shell entrypoint and shared Python implementation.
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
  Generate collection stubs, per-record JSON, aggregate indexes, and the catalogue search artifact.
- [Delete Work](/docs/?scope=studio&doc=scripts-delete-work)
  Remove one work from generated artifacts when workbook status is `delete`.
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
  Run the local Studio tag-save/import service with explicit write allowlists.
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit)
  Audit typography and color literals across CSS files.
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
  Run read-only structural and contract checks across generated pages, JSON, and media.
- [Legacy Title Sort Fix](/docs/?scope=studio&doc=scripts-fix-missing-title-sort)
  Backfill legacy `_works` front matter that still depends on numeric `title_sort`.

## Related References

- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest)
