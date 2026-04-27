---
doc_id: site-request-work-owned-files-links
title: "Work-Owned Files And Links Request"
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: site-docs
sort_order: 152
---
# Work-Owned Files And Links Request

Status:

- proposed

## Summary

This change request tracks the planned simplification of catalogue files and links.

The current source model treats files and links as first-class child records:

- `assets/studio/data/catalogue/work_files.json`
- `assets/studio/data/catalogue/work_links.json`

That shape is heavier than the current product need. Files and links no longer need independent workflows, independent publication state, or separate editor routes. They are metadata owned by a work and should be edited as part of the work record.

The desired end state is:

- work source records own `downloads` and `links` arrays directly
- generated public output remains equivalent
- Studio edits files and links from the work editor, likely through add/edit modals
- the separate file/link source files, lifecycle fields, lookup records, and editor routes are retired

## Current Behavior

Current source data:

- work records live in `assets/studio/data/catalogue/works.json`
- file records live in `assets/studio/data/catalogue/work_files.json`
- link records live in `assets/studio/data/catalogue/work_links.json`

Current public output:

- work files become `downloads` entries on generated work metadata
- work links become `links` entries on generated work metadata
- file/link `status` and `published_date` do not appear in the public `downloads` or `links` arrays

Current Studio behavior:

- the work editor lists files and links as summary/navigation rows
- separate routes create and edit file records
- separate routes create and edit link records
- separate local write-server endpoints save/delete those records

## Problem

The current model implies that files and links have first-class catalogue importance.

That implication is no longer accurate:

- files and links do not need their own draft/published workflow
- files and links do not need their own published dates
- files and links do not need stable cross-record references
- files and links do not need independent pages or search records
- files and links are understood by the user as metadata attached to a work

The result is unnecessary complexity in:

- source schema
- validation
- derived lookup payloads
- write-server endpoints
- delete cascades
- Studio navigation
- add/edit workflows
- documentation

## Goals

- make files and links work-owned metadata
- simplify adding and editing files and links from the work editor
- remove misleading file/link lifecycle fields
- preserve the existing public catalogue output shape
- reduce source-file count and pipeline branching
- keep the migration deterministic and reversible through normal backups/git history

## Non-Goals

- do not add file upload or remote media publishing
- do not delete existing referenced PDF/source files
- do not redesign the whole work editor in the schema migration stage
- do not change the public `downloads` or `links` runtime contract unless a later request explicitly does so
- do not add per-file or per-link audit workflows
- do not introduce a database-style generic child-record layer

## Target Source Model

Work records should own optional arrays:

```json
{
  "work_id": "00008",
  "downloads": [
    {
      "filename": "nerve.pdf",
      "label": "nerve.pdf"
    }
  ],
  "links": [
    {
      "url": "https://example.com",
      "label": "example"
    }
  ]
}
```

Download fields:

- `filename`
- `label`

Link fields:

- `url`
- `label`

Fields to retire from file/link metadata:

- `file_uid`
- `link_uid`
- `work_id`
- `status`
- `published_date`

The parent `work_id` is already implied by the owning work record.

## Delivery Strategy

Do this in two stages.

### Stage 1. Schema And Pipeline

Move the canonical source model and pipeline first.

Stage 1 should be intentionally mechanical:

- migrate existing file/link source rows into `works.json`
- preserve generated public output
- remove file/link lifecycle semantics from the source model
- update pipeline and write-server internals to use embedded arrays
- keep UI changes minimal

This stage should avoid modal work unless a small compatibility edit is required to keep the work editor usable.

### Stage 2. Studio UI Simplification

After the source model is simple, replace the separate file/link pages with work-editor interactions.

The likely UI direction is:

- work editor shows files and links as editable lists
- `Add file`, `Edit file`, `Delete file` use a modal
- `Add link`, `Edit link`, `Delete link` use a modal
- file/link edits become part of the parent work draft and save flow
- obsolete file/link routes redirect to the parent work editor or show a retirement notice

## Stage 1 Task List

### Task 1. Confirm Source Contract

Status:

- pending

Lock the embedded array schema for:

- `Works.downloads`
- `Works.links`

Confirm validation rules:

- filenames are required for downloads
- labels are required for downloads
- URLs are required for links
- labels are required for links
- empty arrays may be omitted or normalized to empty arrays, but output should be deterministic

### Task 2. Migrate Source Data

Status:

- pending

Write a deterministic migration from:

- `work_files.json` into `works.json[].downloads`
- `work_links.json` into `works.json[].links`

Migration behavior:

- preserve existing sort order deterministically
- drop file/link lifecycle fields
- keep only public metadata fields
- create backups before write
- leave retired source files untouched until removal is explicitly included in the same reviewed change

### Task 3. Update Source Readers And Validators

Status:

- pending

Update catalogue source helpers so canonical records are read from `works.json`.

Affected areas are expected to include:

- `scripts/catalogue_source.py`
- source validation
- workbook compatibility helpers if still needed
- source record serialization
- migration/import helpers

Validation should no longer require separate file/link maps.

### Task 4. Update Public Generation

Status:

- pending

Update generation so public work metadata reads `downloads` and `links` directly from work source records.

The generated public output should remain equivalent for existing records.

Affected areas are expected to include:

- `scripts/generate_work_pages.py`
- `scripts/catalogue_json_build.py`
- any helper that materializes temporary workbook rows for the generator

### Task 5. Update Studio Lookup Payloads

Status:

- pending

Update lookup generation so work lookup payloads include embedded file/link summaries from the work record.

Retire focused lookup payloads for:

- `catalogue_lookup/work_files/<file_uid>.json`
- `catalogue_lookup/work_links/<link_uid>.json`

Keep work-editor summary data available from the focused work lookup payload.

### Task 6. Update Write Server Source Boundary

Status:

- pending

Update the catalogue write server so file/link changes are work-record changes.

Expected changes:

- remove or deprecate `work-file` and `work-link` create/save/delete endpoints
- update work save validation to accept `downloads` and `links`
- update record hashing expectations for work-owned metadata
- update lookup invalidation so file/link edits refresh the parent work surfaces
- update delete preview/apply so work delete no longer cascades to separate file/link source maps

### Task 7. Update Activity And Build Reporting

Status:

- pending

Update activity summaries so file/link changes are reported as work source changes, not independent child-record operations.

Build impact should remain work-scoped.

### Task 8. Update Documentation

Status:

- pending

Update docs that currently describe file/link records as separate source families.

Expected docs include:

- `Data Models`
- `Catalogue Work Editor`
- `Catalogue Work File Editor`
- `Catalogue Work Link Editor`
- `Catalogue Write Server`
- relevant script docs
- `Site Change Log`

Docs should clearly state that files and links are work-owned metadata.

### Task 9. Verify Stage 1

Status:

- pending

Codex-run checks:

- syntax-check changed Python scripts with the configured interpreter
- run source migration in dry-run mode first if implemented as a script
- run the targeted catalogue dry-run build for a work with files and links
- run the targeted catalogue write/build preview path for an affected work
- compare generated public work metadata before/after for representative records
- rebuild Studio docs after docs changes

Manual checks:

- open a work with downloads and links in Studio
- confirm its file/link summaries still display
- confirm generated public work page still exposes the same downloads and links
- confirm no obsolete file/link status or published-date meaning remains visible in normal editing

## Stage 2 Task List

### Task 1. Define Work Editor Interaction Contract

Status:

- pending

Specify how files and links behave inside the work editor:

- add
- edit
- delete
- reorder, if needed
- dirty-state handling
- validation messages
- save and save-and-update behavior

File/link edits should participate in the parent work draft state.

### Task 2. Build File Modal

Status:

- pending

Add a work-editor modal for download metadata:

- filename
- label
- save/apply to draft
- cancel without changing draft
- delete existing draft item

The modal should not imply upload or file copy behavior.

### Task 3. Build Link Modal

Status:

- pending

Add a work-editor modal for link metadata:

- URL
- label
- save/apply to draft
- cancel without changing draft
- delete existing draft item

### Task 4. Replace File/Link Navigation Rows

Status:

- pending

Replace current navigation rows with editable rows on the work editor.

Rows should support:

- opening the edit modal
- adding a new item
- deleting an item through confirmation
- clear empty states

### Task 5. Retire Separate Routes

Status:

- pending

Retire or redirect:

- `/studio/catalogue-work-file/`
- `/studio/catalogue-new-work-file/`
- `/studio/catalogue-work-link/`
- `/studio/catalogue-new-work-link/`

Route behavior should be explicit:

- redirect to the parent work editor when a parent work can be resolved
- otherwise show a short retirement message with a work search/link

### Task 6. Update Studio Config Copy

Status:

- pending

Move any new UI copy into `assets/studio/data/studio_config.json`.

Remove obsolete file/link route labels once the routes are retired.

### Task 7. Update Studio UI Rules

Status:

- pending

Record the UI outcome in `studio-ui-rules.md` because this changes a repeated catalogue editor pattern:

- files and links are metadata sections on the owning editor
- child metadata should not get separate editor routes unless it has an independent workflow

### Task 8. Verify Stage 2

Status:

- pending

Codex-run checks:

- run JavaScript syntax/module checks used by the repo, if available
- run a Jekyll build to catch route/template errors
- smoke-test the work editor on desktop and mobile

Manual checks:

- add, edit, delete, and save a file entry from a work
- add, edit, delete, and save a link entry from a work
- cancel each modal and confirm the parent draft does not change
- confirm dirty-state warnings include file/link edits
- confirm save plus `Update site now` publishes the expected generated output

## Benefits

- simpler source model
- fewer Studio routes and write endpoints
- files and links match the user's mental model as work metadata
- removes misleading file/link `status` and `published_date` fields
- reduces lookup invalidation complexity
- makes add/edit workflows faster and less fragmented
- keeps public output stable while changing the source/editor boundary

## Risks

- source migration touches canonical catalogue data
- parent work hashes will change when file/link metadata changes
- retiring separate lookup payloads can break routes or docs that still reference them
- UI modal work can expand into a broader work-editor redesign if not scoped tightly
- embedded arrays make future independent file/link workflows less natural

## Open Questions

- Should embedded arrays preserve the source order from existing file/link maps, or should Studio expose explicit reordering?
- Should empty `downloads` and `links` arrays be omitted from source records or stored as empty arrays?
- Should retired file/link source files be deleted in Stage 1, or kept for one release as migration evidence?
- Should old file/link URLs redirect to the work editor indefinitely or only during the migration window?

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work File Editor](/docs/?scope=studio&doc=catalogue-work-file-editor)
- [Catalogue Work Link Editor](/docs/?scope=studio&doc=catalogue-work-link-editor)
- [Data Models](/docs/?scope=studio&doc=data-models)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
