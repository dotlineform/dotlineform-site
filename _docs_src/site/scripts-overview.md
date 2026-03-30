---
doc_id: scripts-overview
title: Scripts Overview
last_updated: 2026-03-30
parent_id: site
sort_order: 20
---

# Scripts Overview

Use this command prefix for all script commands:

```bash
./
```

All commands below assume you are in `dotlineform-site/`.

For local environment/bootstrap steps, see [Local Setup](/docs/?scope=studio&doc=local-setup).

## Purpose

This page is now the high-level entry point for repo scripts.
Command-level usage, flags, output paths, and operational notes now live in the child docs below.

## Common Runtime Assumptions

- run project commands from `dotlineform-site/`
- use project-local script paths such as `./scripts/...`
- docs-data rebuild command:

```bash
./scripts/build_docs_data.rb --write
```

- if `jekyll serve` or `bin/dev-studio` is already running, verify one-off builds to `/tmp/dlf-jekyll-build` rather than `_site/`
- media and generation scripts expect:
  - `DOTLINEFORM_PROJECTS_BASE_DIR`
  - `DOTLINEFORM_MEDIA_BASE_DIR`
- shared pipeline defaults live in `_data/pipeline.json`

## Script References

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  Build scope-owned docs JSON for Studio and Library docs.
- [Main Draft Pipeline](/docs/?scope=studio&doc=scripts-main-pipeline)
  Run the copy -> srcset -> generation pipeline from one entrypoint.
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
  Stage source media for works, work details, and moments from workbook-driven IDs.
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
  Build srcset derivatives through the stable shell entrypoint and shared Python implementation.
- [Build Search Data](/docs/?scope=studio&doc=scripts-build-search-data)
  Build search-owned artifacts for non-catalogue scopes; current implemented scope is `studio`.
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
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest)
