---
doc_id: site-request-moments-prose-source-model
title: Moments Prose Source Model Request
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: change-requests
sort_order: 50
---
# Moments Prose Source Model Request

Status:

- proposed

## Summary

This change request tracks the missing moments follow-up to the work and series prose source-model migration.

The goal is to implement a repo-managed source model for moment prose without weakening the current moment metadata, import, and public runtime contracts.

Moments need their own request because the current source file is not only prose. It also owns moment metadata in front matter, and this migration intentionally separates those concerns.

## Goal

Move moment prose source handling toward the same durable repo-local model now used for work and series prose.

The desired end state is:

- moment prose no longer depends on external `DOTLINEFORM_PROJECTS_BASE_DIR` Markdown at publication time
- imported moment source is retained in the repository as durable Markdown
- public moment pages keep reading generated runtime payloads from `assets/moments/index/<moment_id>.json`
- `/moments/` keeps reading aggregate card metadata from `assets/data/moments_index.json`
- moment source-image lookup can continue to use the configured external media/source image roots
- moment metadata is entered through `/studio/catalogue-moment-import/`, not through prose front matter
- moment prose Markdown is body-only source under `_docs_src_catalogue/moments/`

## Current Workflow

Current moment source flow:

- `/studio/catalogue-moment-import/` asks for one explicit moment Markdown filename
- the write server resolves that file under the canonical external moments source folder
- the source filename stem becomes `moment_id`
- moment metadata lives in the source file front matter
- moment prose lives in the same source file body
- `catalogue_json_build.py --moment-file <file>.md` runs a targeted import/rebuild
- `generate_work_pages.py` renders the moment body into `assets/moments/index/<moment_id>.json` as `content_html`
- `_moments/<moment_id>.md` remains a minimal routing stub
- `/moments/<moment_id>/` fetches the per-moment JSON payload at runtime

This is already file-based, but the file is still external to the repository and combines two kinds of ownership.

## Relationship To Work And Series

The work and series prose migration established these useful conventions:

- staged Markdown enters through `var/docs/catalogue/import-staging/`
- permanent source lives under `_docs_src_catalogue/`
- public pages keep using existing generated runtime JSON payloads
- prose source files are ID-derived
- missing prose is optional

Moments should reuse the stable parts of that model where they fit.

The main difference is metadata ownership. Work and series metadata already lives in catalogue JSON records, so their repo-local prose source files can be Markdown body files with no front matter. Moments currently use front matter as their canonical metadata record, but this request moves moment prose toward the same body-only source shape.

## Proposed Direction

Use a repo-local permanent moment source root:

- `_docs_src_catalogue/moments/`

Use ID-derived filenames:

- `_docs_src_catalogue/moments/<moment_id>.md`

Use a moment staging root:

- `var/docs/catalogue/import-staging/moments/`

Staged imports should read only from that staging root. They should not support direct import from the current external moments folder.

Moment prose source files should be body-only Markdown. Metadata should be entered on `/studio/catalogue-moment-import/` and owned outside the prose Markdown source.

Publish-state writes should not update moment source front matter. A publishable moment requires a source prose file.

Existing `<pre class="moment-text">...</pre>` wrappers should remain accepted during the migration so current prose can move without a formatting cleanup being bundled into the source-model change.

Media image import and srcset generation are intentionally out of scope for this pass. Moment source-image lookup should remain a metadata/runtime concern, not part of the prose-source migration.

The first implementation should preserve the public generated artifacts:

- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`

The generator should read moment prose from the repo-local source root once migration is complete.

## Resolved Source Contract

Resolved decisions:

1. Repo-local moment Markdown becomes body-only prose.
2. Moment metadata is entered on `/studio/catalogue-moment-import/`, not stored in prose front matter.
3. Permanent moment prose source root is `_docs_src_catalogue/moments/`.
4. Permanent source filenames are ID-derived: `<moment_id>.md`.
5. Staged imports read from `var/docs/catalogue/import-staging/moments/` only.
6. The import flow does not directly read from the current external moments folder.
7. Publish-state writes do not update moment prose front matter.
8. A source prose file is required for a publishable moment.
9. Existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration.
10. Source-image lookup remains separate from prose source lookup.
11. Media image import/edit/srcset work is deferred to a future shared mechanism across works and moments.

## Metadata Ownership

Moment metadata should move out of the moment prose Markdown source.

The moment import page should collect the metadata needed to create or update the moment record. The prose Markdown file owns only the authored body content.

Implemented metadata ownership:

- moment metadata is stored in `assets/studio/data/catalogue/moments.json`
- existing front matter metadata was migrated into that JSON source
- draft, published, and `published_date` behavior now uses metadata JSON rather than prose front matter

## Benefits

Expected benefits:

- moment prose becomes repo-visible and reviewable
- moment imports no longer depend on an external Markdown source tree after import
- work, series, and moments share a clearer source-staging convention
- moment prose becomes body-only like work and series prose
- metadata entry becomes explicit in the Studio moment import workflow
- public moment runtime payloads stay stable
- future review/export tools can operate on durable repo-local moment Markdown

## Risks And Tradeoffs

Main risks:

- moving moment metadata out of front matter increased implementation scope
- the import page needs enough metadata fields to create or update a publishable moment safely
- source-image lookup must not accidentally move into the prose-source tree
- existing prose wrappers are accepted for migration, so cleanup to pure Markdown remains a later step
- deferring image import/edit/srcset work keeps this pass focused, but leaves a known workflow gap for both works and moments

The main tradeoff is implementation scope versus long-term model consistency.

This request chooses the more consistent long-term model: body-only prose source, with moment metadata owned outside the prose Markdown.

The media tradeoff is deliberate: moment images should not get a one-off solution here. A later task should define one shared import/edit/srcset mechanism that works consistently for works and moments.

## Source Contract Notes

Open implementation details:

1. How wrapper-preserving prose migration is reported and later cleaned up.

## Proposed Implementation Steps

### Task 1. Define The Moment Source Contract

Status:

- complete

Defined:

- permanent source root: `_docs_src_catalogue/moments/`
- staging root: `var/docs/catalogue/import-staging/moments/`
- source filename rule: `<moment_id>.md`
- front matter policy: body-only prose, no canonical metadata front matter
- metadata entry surface: `/studio/catalogue-moment-import/`
- missing-prose behavior: source prose file is required for a publishable moment
- source-image lookup boundary
- media image import/edit/srcset work deferred to a future shared work/moment mechanism
- compatibility with existing `<pre class="moment-text">...</pre>` wrappers during migration

### Task 2. Add Moment Source Import Or Migration

Status:

- complete

Add or adapt a moment import path that:

- reads staged moment Markdown from `var/docs/catalogue/import-staging/moments/`
- validates the ID-derived filename
- rejects canonical metadata front matter in the permanent prose source
- accepts existing `<pre class="moment-text">...</pre>` wrappers during migration
- collects required moment metadata through `/studio/catalogue-moment-import/`
- rejects unsafe paths
- avoids silent overwrite
- writes the permanent repo-local source file
- keeps external source files untouched

Implemented behavior:

- staged prose is read from `var/docs/catalogue/import-staging/moments/<moment_id>.md`
- permanent prose is written to `_docs_src_catalogue/moments/<moment_id>.md`
- canonical metadata is written to `assets/studio/data/catalogue/moments.json`
- the apply endpoint validates staged body-only Markdown before writing
- local media/srcset generation is skipped for this pass

### Task 3. Update Moment Generator Source Lookup

Status:

- complete

Update the catalogue generator so moment prose is read from the repo-local source root and moment metadata is read from the new canonical metadata source.

The generator should continue to write:

- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`

Public runtime behavior should stay unchanged.

Implemented behavior:

- generator moment metadata lookup reads `assets/studio/data/catalogue/moments.json`
- generator moment prose lookup reads `_docs_src_catalogue/moments/<moment_id>.md`
- generated runtime payloads remain `_moments/<moment_id>.md`, `assets/moments/index/<moment_id>.json`, and `assets/data/moments_index.json`
- generator no longer writes moment source front matter

### Task 4. Update Studio Moment Import UI

Status:

- complete

Update `/studio/catalogue-moment-import/` so the UI reflects the new source model.

The UI should:

- collect required moment metadata
- preview the staged body-only prose source
- explain that staged prose comes from `var/docs/catalogue/import-staging/moments/`
- avoid describing external moment Markdown as the permanent canonical source after migration

Implemented behavior:

- the page now renders metadata fields for title, status, date, date display, published date, source image file, and image alt
- preview/apply requests send metadata alongside the staged filename
- UI copy now describes staged body-only prose and catalogue JSON metadata ownership

### Task 5. Migrate Existing Moment Sources

Status:

- complete

Create a migration pass for existing moment Markdown files.

The migration should:

- identify all current external moment source files
- extract existing front matter metadata into the new canonical metadata source
- stage or import prose bodies into the permanent repo-local source root with ID-derived filenames
- report invalid filenames or front matter
- preserve existing `<pre class="moment-text">...</pre>` wrappers during the first migration
- avoid deleting external source files
- keep generated public moment pages stable

Implemented behavior:

- current external moment front matter was migrated into `assets/studio/data/catalogue/moments.json`
- current external moment prose bodies were copied into `_docs_src_catalogue/moments/<moment_id>.md`
- source front matter was stripped from the repo-local prose files
- existing `<pre class="moment-text">...</pre>` wrappers were preserved
- external source files were not deleted

### Task 6. Update Docs And Verification

Status:

- complete

Update relevant docs after implementation.

Likely docs:

- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

Implemented behavior:

- moment import, generator, scoped build, catalogue data-model, write-server, and change-log docs were updated
- Studio docs and search payloads were rebuilt after source-doc updates

## Validation Plan

Codex-run checks should include:

- syntax checks for changed Python scripts
- moment import preview for one staged source file
- generator dry run for one moment with prose
- docs rebuild for updated Studio docs
- search rebuild if docs/search output changed
- sanitization scan for changed source/docs/scripts

Manual checks should include:

- import one moment source document from staging
- verify ID-based staged filenames are detected
- verify moment metadata is entered through `/studio/catalogue-moment-import/`
- verify permanent moment prose source has no canonical metadata front matter
- verify existing public `/moments/<moment_id>/` still renders title, date, image, and prose
- verify `/moments/` card metadata is unchanged except for intentional updates
- verify source image lookup still uses the expected external media/source image path
- verify the change does not add moment-specific media import/edit/srcset behavior

## Out Of Scope

- changing public moment page layout
- changing moment srcset variant policy
- adding media image import, edit, or srcset generation to the moment import flow
- moving moment prose into Library
- publishing moment prose through the public analysis viewer
- deleting external moment source files
- cleaning up existing `<pre class="moment-text">...</pre>` wrappers beyond accepting them during migration
- redesigning all catalogue metadata storage beyond the moment metadata needed for this request

## Future Follow-Up

A later request should define a consistent media import/edit/srcset mechanism across works and moments.

That future work should cover:

- how Studio work and moment flows declare image readiness
- when source images are copied or staged
- when srcset variants are generated
- how generated image metadata is reflected in runtime payloads
- how the UI reports missing, stale, or regenerated media consistently

## Related References

- [Work And Series Prose Source Model Request](/docs/?scope=studio&doc=site-request-work-series-prose-source-model)
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- `_docs_src/moments-json-migration-plan.md`
