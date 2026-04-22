---
doc_id: scripts
title: "Scripts"
last_updated: 2026-04-18
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

- `python3 ./scripts/catalogue_json_build.py`
  - previews or runs a scoped JSON-source rebuild for one work or one series scope, including aggregate indexes and catalogue search
- `python3 ./scripts/validate_catalogue_source.py`
  - validates canonical catalogue source JSON under `assets/studio/data/catalogue/`
- `python3 ./scripts/compare_catalogue_sources.py`
  - compares workbook-normalized source records with JSON-normalized source records during transition checks
- `python3 ./scripts/export_catalogue_lookup.py`
  - exports derived Studio lookup JSON from canonical source into `assets/studio/data/catalogue_lookup/`
- `bash scripts/make_srcset_images.sh`
  - builds derivative image outputs when media work is needed outside the Studio metadata flow

## Script References

- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
  Run the integrated local Studio development stack, including Jekyll, localhost write services, and startup data refreshes.
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
  Run the local Docs Viewer create/archive/delete service with explicit write allowlists.
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
  Build srcset derivatives through the stable shell entrypoint and shared Python implementation.
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
  Preview or run the Phase 5 scoped JSON-source rebuild flow for one work.
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
  Validate and compare canonical catalogue source JSON during the transition away from workbook-led tooling.
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
  Export derived Studio lookup payloads for focused editor reads.
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

- [Servers](/docs/?scope=studio&doc=servers)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest)
