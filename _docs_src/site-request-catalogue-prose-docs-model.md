---
doc_id: site-request-catalogue-prose-docs-model
title: "Catalogue Prose Docs Model Request"
added_date: 2026-04-26
last_updated: 2026-04-26
parent_id: site-docs
sort_order: 140
---
# Catalogue Prose Docs Model Request

Status:

- proposed

## Summary

This change request tracks a proposed migration of catalogue prose for works, series, and moments into a docs-style source and publishing model.

The core idea is that catalogue prose should become a first-class document family, closer to the Library and Studio docs model, instead of being treated as markdown fragments resolved from external project folders during catalogue generation.

## Goal

Make work, series, and moment prose consistent with the shared docs pipeline while preserving the current public catalogue routes.

The desired end state is:

- catalogue prose source files live in a repo-managed source tree
- imported catalogue prose starts from a repo-local staging area
- generated catalogue prose payloads use the common docs metadata and rendered-content model
- work, series, and moment pages can consume catalogue prose without depending on external prose paths at page-build time
- the same document helpers used for Library, Studio docs, tags, and LLM review can eventually operate on catalogue prose

## Current Catalogue Prose Workflow

Current work prose flow:

- the source prose filename is recorded on `/studio/catalogue-new-work/` or the work editor
- the generator resolves it through `DOTLINEFORM_PROJECTS_BASE_DIR`
- the resolved path is shaped as `projects/<project_folder>/<prose_subdir>/<work_prose_file>`
- the default prose subdirectory is currently `site text`
- `Import prose + rebuild` renders the Markdown into HTML
- rendered HTML is saved into `assets/works/index/<work_id>.json` as `content_html`
- `/works/<work_id>/` reads the work payload and displays that rendered HTML

Current series prose flow is similar, but the source project folder is resolved through the series `primary_work_id`.

Current moment prose flow is related but not identical:

- canonical moment source currently lives in the external `moments/<moment_id>.md` tree
- moment metadata and prose are coupled in that source file
- generated moment content is written into `assets/moments/index/<moment_id>.json`

## Current Library Docs Workflow

Current Library document flow:

- source documents are staged under `var/docs/import-staging/`
- import converts the source document into Markdown
- the generated Markdown source lives under `_docs_library_src/`
- `./scripts/build_docs.rb --scope library --write` renders the Markdown into docs-viewer payloads
- generated content is written under `assets/data/docs/scopes/library/`
- `/library/` consumes the generated docs index and per-doc payloads

The useful property is not that Library has a different public route. The useful property is that source Markdown, metadata, generated HTML, search eligibility, and management state all pass through a shared docs contract.

## Proposed Direction

Catalogue prose should adopt the same broad source-to-rendered-doc shape.

Proposed source and staging roots:

- staging: `var/docs/catalogue/import-staging/`
- work prose source: `_docs_catalogue_src/works/`
- series prose source: `_docs_catalogue_src/series/`
- moment prose source: `_docs_catalogue_src/moments/`

Proposed generated roots:

- work prose payloads: `assets/data/docs/scopes/catalogue/works/by-id/`
- series prose payloads: `assets/data/docs/scopes/catalogue/series/by-id/`
- moment prose payloads: `assets/data/docs/scopes/catalogue/moments/by-id/`

The exact generated path shape is still open. The important requirement is that each catalogue prose record becomes addressable as a document with stable identity, metadata, rendered HTML, and source path ownership.

## Review Suggestions

### Treat This As A Document Model Migration, Not Only A Path Move

Moving files into the repo is only part of the change.

The real contract should define:

- document identity
- source file ownership
- front matter fields
- render output shape
- relationship to catalogue metadata records
- search and docs-viewer eligibility
- update and overwrite behavior

Without that contract, the migration could simply recreate the current prose-fragment model in a new folder.

### Preserve Catalogue Metadata As The Owner Of Catalogue State

Catalogue records should probably remain the owner of object-level facts such as:

- `work_id`, `series_id`, and `moment_id`
- public route
- publication status
- title used for catalogue cards and pages
- series membership
- media relationships

Catalogue prose docs should own authored prose content and document-level editorial metadata.

This avoids having the same title, status, or route facts diverge between catalogue JSON and docs front matter.

### Add A Transitional Runtime Phase

A safe first implementation can generate docs-style catalogue prose payloads while still copying rendered `content_html` into the existing public catalogue JSON payloads.

That keeps `/works/`, `/series/`, and `/moments/` stable while the source and builder model changes underneath.

A later phase can decide whether public catalogue pages should fetch prose directly from `assets/data/docs/scopes/catalogue/...` instead of reading `content_html` from `assets/works/index/`, `assets/series/index/`, and `assets/moments/index/`.

### Decide Whether Catalogue Is One Docs Scope Or Several Document Families

The current docs builder assumes one source root and one generated `by-id/` directory per docs scope.

The proposed shape introduces families under one catalogue scope:

- works
- series
- moments

That is a good conceptual model, but it may need either:

- a new family-aware docs builder mode
- separate configured scopes such as `catalogue-works`, `catalogue-series`, and `catalogue-moments`
- a flat catalogue source root with IDs such as `work-00008`, `series-067`, and `moment-keys`
- a nested-source extension to the docs builder

The choice matters because the builder currently rejects nested Markdown docs for Studio and Library so their flat source-layout contract remains explicit.

### Keep Moment Migration Separate Enough To Avoid Metadata Loss

Moment prose migration is likely broader than work and series prose migration.

Reason:

- work and series prose files are mostly external prose fragments referenced by catalogue metadata
- moment Markdown files currently carry both prose and canonical moment metadata

The moment path may need a split where moment metadata first moves fully into catalogue JSON source, then moment prose becomes a catalogue prose doc.

## Benefits

Expected benefits:

- source prose becomes repo-visible and reviewable with normal docs/source tooling
- Library, Studio docs, and catalogue prose can share import, render, metadata, search, and LLM-review helpers
- public content becomes less dependent on machine-local external prose folders
- catalogue prose gains a path toward docs-viewer review, manage mode, and export workflows
- generated prose payloads can use a consistent metadata schema instead of ad hoc `content_html` embedding only

## Risks And Tradeoffs

Main risks:

- public catalogue pages currently expect prose inside page-local catalogue JSON payloads
- changing the generated output shape too early could create unnecessary runtime churn
- nested catalogue prose folders may conflict with the current flat docs-source assumptions
- metadata ownership can become ambiguous if docs front matter duplicates catalogue source fields
- moments have coupled metadata/prose source files today, so their migration can affect more than rendering
- search scope boundaries may blur if catalogue prose becomes both catalogue content and docs-viewer content

The main tradeoff is between immediate consistency and migration safety.

A direct cutover to docs-style runtime payloads would simplify the target architecture sooner, but a transitional phase is likely easier to verify and less risky for public catalogue pages.

## Open Questions

1. Should catalogue prose be one docs scope with document families, or separate docs scopes for works, series, and moments?
2. Should public catalogue pages continue reading `content_html` from existing catalogue payloads, or should they fetch docs-style prose payloads directly?
3. What is the stable document ID format?
   - examples: `work-00008`, `series-067`, `moment-keys`
4. Should work and series prose source filenames be derived from catalogue IDs rather than preserving legacy prose filenames?
5. Which front matter fields belong in catalogue prose source files, and which must stay only in catalogue metadata JSON?
6. Should catalogue prose appear in the public docs viewer, local manage mode only, or neither at first?
7. Should catalogue prose participate in docs search, catalogue search, both, or neither during the first phase?
8. Should the import staging area accept only Markdown, or should it reuse the current HTML-to-Markdown import flow?
9. What backup and overwrite behavior should apply when importing over an existing catalogue prose doc?
10. How should missing prose be represented: no source doc, unpublished source doc, or empty generated payload?
11. What happens to existing `work_prose_file` and `series_prose_file` fields after migration?
12. What is the migration plan for external source prose files that are not currently referenced by any catalogue record?

## Proposed Implementation Steps

### Task 1. Define The Catalogue Prose Document Contract

Status:

- pending

Define:

- source roots
- generated roots
- doc ID scheme
- required front matter
- optional front matter
- ownership boundary between catalogue metadata and prose document metadata
- handling for missing, draft, unpublished, and viewable states

This task should explicitly decide whether nested source roots are allowed for catalogue prose.

### Task 2. Add Catalogue Scope Support To Docs Configuration

Status:

- pending

Extend the docs build configuration so catalogue prose can be rendered through the shared docs builder or a closely related builder path.

This task must decide whether to use:

- one family-aware `catalogue` docs scope
- separate catalogue-family scopes
- a flat source root with family-prefixed IDs
- a new builder mode for nested source folders

### Task 3. Add Catalogue Prose Import Staging

Status:

- pending

Create a repo-local import flow from:

- `var/docs/catalogue/import-staging/`

The import flow should:

- preview the staged source
- map it to a target work, series, or moment document
- validate the output Markdown
- avoid silent overwrite
- create a backup before overwrite
- write into the agreed catalogue prose source root

### Task 4. Migrate Work And Series Prose First

Status:

- pending

Move work and series prose onto the new source model before moments.

Reason:

- work and series prose are already referenced from catalogue metadata
- moment source files currently combine metadata and prose, making them a broader migration

Initial work and series migration should preserve public catalogue output behavior.

### Task 5. Add A Transitional Publication Bridge

Status:

- pending

Render catalogue prose docs and feed their `content_html` into existing catalogue payloads.

During this phase:

- `assets/works/index/<work_id>.json` can still contain `content_html`
- `assets/series/index/<series_id>.json` can still contain `content_html`
- `assets/moments/index/<moment_id>.json` can still contain `content_html`
- public pages do not need to change their prose-loading behavior
- generated docs-style payloads become available for review and future runtime use

### Task 6. Split Moment Metadata From Moment Prose

Status:

- pending

Define and implement a moment-specific migration.

The likely target is:

- canonical moment metadata lives in catalogue source JSON
- moment prose lives in `_docs_catalogue_src/moments/`
- generated moment page payloads continue to serve `/moments/<moment_id>/`

This task should be planned separately enough to avoid accidental loss of front matter fields currently stored in external moment Markdown files.

### Task 7. Decide Search And Viewer Exposure

Status:

- pending

Decide whether catalogue prose docs are:

- hidden implementation payloads only
- visible in docs-viewer manage mode
- public docs-viewer documents
- inputs to catalogue search full-text expansion
- inputs to a separate catalogue prose review/export flow

This should be decided before broad search integration so catalogue search and docs search do not duplicate or contradict each other.

### Task 8. Update Docs And Operational Guidance

Status:

- pending

Update the relevant docs after the model is chosen and implemented.

Likely docs:

- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## Validation Plan

Codex-run checks should include:

- docs builder dry run for the affected scope or scopes
- docs builder write run for the affected scope or scopes
- syntax checks for changed Python scripts, if any
- Ruby/Jekyll build after runtime or layout changes
- targeted generator dry run before any catalogue write run
- search rebuild checks if search payloads are affected
- stale-output checks for renamed or removed catalogue prose docs

Manual checks should include:

- import one work prose document from staging
- import one series prose document from staging
- preview overwrite behavior for an existing prose document
- verify `/works/<work_id>/` still displays prose
- verify `/series/<series_id>/` still displays prose
- verify a migrated moment still displays metadata, image, and prose
- verify docs-viewer manage/public exposure matches the chosen policy

## Out Of Scope For The First Change

- redesigning the public work, series, or moment page layouts
- replacing catalogue search ranking
- deleting external prose source files
- migrating all historical prose in one unreviewed batch
- changing media source or srcset behavior
- using docs-viewer public routes as canonical catalogue routes

## Related References

- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
