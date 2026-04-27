---
doc_id: site-request-work-series-prose-source-model
title: "Work And Series Prose Source Model Request"
added_date: 2026-04-26
last_updated: 2026-04-27
parent_id: site-docs
sort_order: 140
---
# Work And Series Prose Source Model Request

Status:

- proposed

## Summary

This change request tracks a narrower migration for work and series prose.

The goal is to make work and series prose more document-like as source material without changing how that prose is published on public work and series pages.

The important split is:

- source handling should become closer to the docs import model
- public catalogue pages should keep reading prose through the existing generated catalogue payloads

This request does not move catalogue prose into Library, Studio docs, or a future public analysis viewer.

## Goal

Move work and series prose away from externally resolved project-folder Markdown files and into permanent repo-managed Markdown source.

The desired end state is:

- work and series prose imports start from a repo-local staging folder
- imported Markdown is retained as the permanent source of the published prose
- source prose is tracked in the repository rather than resolved from `DOTLINEFORM_PROJECTS_BASE_DIR`
- the current public publishing model remains stable
- work pages still receive rendered prose through `assets/works/index/<work_id>.json`
- series pages still receive rendered prose through `assets/series/index/<series_id>.json`

## Current Workflow

Current work prose flow:

- the source prose filename is recorded on `/studio/catalogue-new-work/` or the work editor
- the generator resolves it through `DOTLINEFORM_PROJECTS_BASE_DIR`
- the resolved path is shaped as `projects/<project_folder>/<prose_subdir>/<work_prose_file>`
- the default prose subdirectory is currently `site text`
- `Import prose + rebuild` renders the Markdown into HTML
- rendered HTML is saved into `assets/works/index/<work_id>.json` as `content_html`
- `/works/<work_id>/` reads the work payload and displays that rendered HTML

Current series prose flow is similar, but the source project folder is resolved through the series `primary_work_id`.

## Proposed Direction

Work and series prose should use a repo-local source model.

Staging root:

- `var/docs/catalogue/import-staging/`

Permanent source roots:

- `_docs_src_catalogue/works/`
- `_docs_src_catalogue/series/`

The source root is repo-local and clearly separate from:

- `_docs_src/`
- `_docs_library_src/`
- any future `_docs_analysis_src/`

Source filenames are ID-derived:

- work prose source is keyed by `work_id`
- series prose source is keyed by `series_id`
- legacy prose filenames are not retained as permanent source names

Examples:

- `_docs_src_catalogue/works/00008.md`
- `_docs_src_catalogue/series/067.md`

Prose source files are Markdown body files only. They do not need front matter for the first implementation because the catalogue record ID is derived from the filename stem and catalogue metadata remains canonical in the catalogue JSON source records.

The `work_prose_file` and `series_prose_file` source fields should be replaced by ID-derived source lookup. If a staged Markdown file exists at the expected work or series ID filename, the Studio import flow should confirm that it has been picked up and import it into the permanent source root.

The first import flow is Markdown-only. It does not reuse the docs HTML-to-Markdown conversion path.

Missing prose is represented as blank optional prose in the editor and generator. Public work and series pages should cleanly accept no prose.

The generated public payloads should stay as they are today:

- `assets/works/index/<work_id>.json`
- `assets/series/index/<series_id>.json`

Those payloads can continue to embed rendered prose as `content_html`.

Generated public payloads should not store source provenance for the repo-local prose file.

## Why Works And Series Belong Together

Works and series are conceptually linked in the current catalogue model.

Reasons:

- series pages derive membership and primary-work context from works
- series prose resolution currently depends on `Series.primary_work_id`
- work and series publication often changes together
- public work and series pages already share related navigation and catalogue-generation paths

That makes work and series prose a shared source-model problem.

Moments are different enough to handle later:

- moments have their own route family
- moment source files currently combine metadata and prose
- moments do not have the same membership relationship with works or series
- moment migration can be planned as a separate, self-contained change

## Review Suggestions

### Keep This Separate From Public Analysis Docs

Work and series prose source should not become the first implementation of the public analysis viewer.

Reason:

- work and series prose is public catalogue page content
- analysis documents are a separate publishing surface for interpretation, tags, catalogue data review, and LLM analysis
- mixing the two would make ownership less clear

The work/series prose change should improve source handling while leaving page ownership with the catalogue pipeline.

### Preserve Existing Public Page Behavior

The first implementation should not require public work or series layouts to fetch a new docs-style payload.

Instead, the generator should read the new repo-local Markdown source and continue writing `content_html` into the existing per-record catalogue JSON.

That keeps the migration focused on source ownership and import workflow.

### Treat Media And Prose Differently

Media images still need to be connected to external project/media folders.

Work and series prose does not have the same constraint. It is authored text, and the published source should be durable and reviewable in the repository.

This justifies moving prose into a repo-managed source tree without changing media lookup rules.

### Avoid Duplicating Catalogue Metadata In Prose Front Matter

The prose source file should not become a second owner for catalogue facts.

Catalogue metadata should remain canonical for:

- `work_id`
- `series_id`
- title
- status
- publication date
- membership
- routes
- media relationships

Prose source should own the authored Markdown body only. Front matter is intentionally omitted for the first implementation.

## Benefits

Expected benefits:

- work and series prose becomes repo-visible and reviewable
- imported prose has a permanent Markdown source, not only rendered `content_html`
- source handling aligns with the safer docs import model
- public work and series pages stay stable
- future LLM review/export helpers can operate on durable Markdown source
- external project folders remain focused on media and project assets rather than published prose

## Risks And Tradeoffs

Main risks:

- the current `work_prose_file` and `series_prose_file` fields need to be removed or deprecated in favor of ID-derived lookup
- existing generator code resolves prose through project folders and will need a new source lookup
- source files keyed by ID are simpler, but existing legacy prose filenames need a small rename/copy migration
- keeping `content_html` embedded in catalogue JSON preserves stability but leaves some duplication between rendered docs and page payloads

The main tradeoff is migration clarity versus runtime normalization.

For this phase, preserving existing runtime payloads is the better tradeoff because it isolates the change to source handling and generation.

## Source Contract

Resolved decisions:

1. Permanent source roots are `_docs_src_catalogue/works/` and `_docs_src_catalogue/series/`.
2. Permanent source filenames are always ID-based: `<work_id>.md` and `<series_id>.md`.
3. Work and series prose source files have no front matter in the first implementation.
4. Catalogue metadata stays in catalogue JSON source records, not prose Markdown.
5. `work_prose_file` and `series_prose_file` should be replaced by ID-derived source lookup.
6. The import flow supports Markdown only at first.
7. Import overwrite does not create a backup for this flow.
8. Missing prose is blank and optional.
9. Generated public payloads do not store repo-local prose source provenance.
10. Prose import remains available from both work and series editors.

## Proposed Implementation Steps

### Task 1. Define The Source Contract

Status:

- complete

Defined:

- staging root
- permanent source roots
- source filename rules
- front matter policy
- source ownership boundary
- missing-prose behavior
- relationship to existing `work_prose_file` and `series_prose_file` fields

### Task 2. Add Work And Series Prose Import

Status:

- complete

Add or adapt a Studio import flow that:

- reads staged files from `var/docs/catalogue/import-staging/`
- targets one work or series record
- previews the staged source
- validates the staged Markdown
- avoids silent overwrite
- overwrites without creating backups for this prose flow
- writes the permanent repo-local prose source file

Implemented behavior:

- work import reads `var/docs/catalogue/import-staging/works/<work_id>.md`
- series import reads `var/docs/catalogue/import-staging/series/<series_id>.md`
- permanent source files are written to `_docs_src_catalogue/works/<work_id>.md` or `_docs_src_catalogue/series/<series_id>.md`
- preview validates UTF-8 Markdown, rejects front matter, and reports overwrite requirements
- apply requires overwrite confirmation when replacing different permanent prose content
- runtime generator lookup for the permanent source roots is implemented in Task 3

### Task 3. Update Generator Prose Lookup

Status:

- complete

Update the catalogue generator so work and series prose are read from the new repo-local source roots using ID-derived lookup.

The generator should continue to write:

- `assets/works/index/<work_id>.json`
- `assets/series/index/<series_id>.json`

The public payload shape should continue to include `content_html` where prose exists.

Implemented behavior:

- work prose is read from `_docs_src_catalogue/works/<work_id>.md`
- series prose is read from `_docs_src_catalogue/series/<series_id>.md`
- missing work or series prose remains optional and publishes as blank `content_html`
- `work_prose_file` and `series_prose_file` no longer control public prose rendering
- planner prose fingerprinting watches the same repo-local source files

### Task 4. Migrate Existing Work And Series Prose

Status:

- complete

Create a migration plan for current referenced prose files.

The migration should:

- identify all referenced work prose files
- identify all referenced series prose files
- copy or import them into the new repo-local source roots with ID-based filenames
- report missing or ambiguous external sources
- avoid deleting external source files
- keep generated public pages stable

Implemented behavior:

- existing work prose for `00008` was imported through the staged Markdown flow
- permanent source now lives at `_docs_src_catalogue/works/00008.md`
- no series prose sources were identified for migration in the current inventory
- external source files were not deleted
- public work payload generation was verified after import

### Task 5. Update Studio Readiness And Import UI

Status:

- complete

Update the work and series editors so prose readiness points at the repo-local source model.

The UI should no longer imply that work and series prose must be resolved from external project folders.

Implemented behavior:

- new work and work editor forms no longer show or submit `work_prose_file`
- new series and series editor forms no longer show or submit `series_prose_file`
- work and series prose import remains available through the staged Markdown readiness/action flow
- existing catalogue source records are preserved; the legacy fields are no longer publication controls

### Task 6. Update Docs And Verification

Status:

- complete

Update the relevant docs after implementation.

Likely docs:

- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

Implemented behavior:

- prose source model docs were updated through the implementation tasks
- catalogue work/series editor usage docs were moved under [User Guide](/docs/?scope=studio&doc=user-guide)
- technical generator, data-model, script, and change-log docs remain under their existing Studio technical sections
- Studio docs/search payloads were rebuilt after the documentation updates

### Task 7. Reduce Forced Scoped Build Noise

Status:

- complete

Implemented behavior:

- the internal generator now has `--refresh-published` for scoped runtime recomputation of selected published records
- `catalogue_json_build.py` uses that narrow refresh mode for normal work, series, and moment scopes
- normal scoped builds no longer pass broad `--force` into generator/search just to process already-published records
- unchanged aggregate JSON and catalogue search payloads continue to skip by content version instead of rewriting only for `generated_at_utc`
- already-published records no longer receive a fresh `published_date` unless they transition from `draft` to `published`
- explicit `--force` remains available for intentional full rewrites
- the scoped CLI now supports `--series-id` for direct series preview/write runs

## Validation Plan

Codex-run checks should include:

- syntax checks for changed Python scripts
- generator dry run for one work with prose
- generator dry run for one series with prose
- write run for a narrow test work or series only when explicitly requested
- docs rebuild for updated Studio docs
- search rebuild if docs/search output changed
- sanitization scan for changed source/docs/scripts

Manual checks should include:

- import one work prose document from staging
- import one series prose document from staging
- verify staged ID-based filenames are detected
- verify overwrite behavior does not create backups
- verify `/works/<work_id>/` still displays prose
- verify `/series/<series_id>/` still displays prose
- verify missing prose guidance in the editor is understandable

## Out Of Scope

- changing public work or series page layouts
- moving work or series prose into Library
- publishing work or series prose through the future public analysis viewer
- migrating moments
- changing media lookup rules
- deleting external prose files

## Related References

- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
