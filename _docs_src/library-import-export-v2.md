---
doc_id: library-import-export-v2
title: Library Export/Import v2
added_date: 2026-05-04
last_updated: "2026-05-04"
ui_status: proposed
parent_id: library
sort_order: 50
---

# Library Export/Import v2

Status:

- proposed

## Purpose

This request adds UI and workflow refinements to the export and import workflows. The primary focus is import because export has already had refinements made to its UI.

Current behaviour is described in places for clarification/context.

## Export

page:`/studio/library-export/`

- No need to preview or manually edit files, export straight to staging as v1 does.

### list filter options

create new pills that act as list filters:

- show all
- no content
- not viewable

### export options

add new checkboxes:

- **JSON** - JSON is an option for all config patterns
- **JSONL** - JSONL is default for when document content field is included in the export config pattern

### Staging

folder:`var/docs/exports/library`

- export creates a JSON/L which includes the metadata defined by the config for the selected documents.

## Import

page:`/studio/library-import/`

### workflow

1. **staging**: a JSON file is manually copied into the staging folder.
2. **preview**: the staged file has been split into separate documents and formatted to plain text with front matter 

### staging

folder:`var/docs/import-staging/library`

workflow:

1. JSON files are manually copied into staging.

### preview

folder:`var/docs/import-preview/library`

workflow:

1. user selects a staged file in the dropdown on the import page
2. Preview button creates files in the preview folder

for all config patterns:

- the staged file is split into separate documents (as current)
- an additional tree hierarchy file is created if there is parent-child data available in the staged JSON
- the tree file displays the parent-child metadata from the staged JSON as a hierarchical tree in the {content}.
- each document is formatted as plain text with front-matter and saved as .txt
- front-matter is split into two sections:
    - first section contains any fields that match the fields from the export config
    - second section contains any new fields in the staged JSON that do not appear in the config.
- no validation or further processing is applied to the preview files.

example preview file:
```
---
doc_id: “my-test”
title: “my title”
summary: “my summary paragraph”
etc...
---
tags: “tag1,tag2”
etc...
---

{content}
```

### file naming for preview files

```[doc_id]-[timestamp].json | jsonl```

where:

- timestamp is the timestamp suffix of the staged file as displayed in the file name
- if staged file is missing a timestamp suffix, use the current local time.

### UI

- the page mirrors the design of the export page
- Preview files created are displayed in a list
- the list mirrors the design of the list on the export page, with checkboxes and document titles
- the list shows the parent-child relationships by indenting the displayed titles

list selection buttons: add two new buttons (as on the export page):

- select all
- clear

## Import Actions

The following actions are available on the library-import page:

1. Update summary
2. Apply hierarchy

### Update summary

- sets the source `_docs_library_src/*.md` summary metadata field with the summary text in the staged JSON for the documents selected in the list
- a confirmation modal is displayed which shows the count of documents that will be updated
- the modal has OK and Cancel buttons

### Apply hierarchy

- sets the parent_id field for each document in the staged JSON
- the staged JSON will contain a list of parent_id for each doc:

example:
```
"documents":[
    {
        doc_id: “....”,
        parent_id: “....”
    }
]
```

- a confirmation modal is displayed which shows the count of documents that will be updated
- the modal has OK and Cancel buttons

## Review Notes

- The v2 work should start with the Import UI because the existing v1 import route, parser, preview renderer, and local service already provide enough data to reshape the page without changing source-write behavior.
- The first import milestone should remain preview-only. Summary and hierarchy apply actions write canonical Library source and need a narrower confirmation, backup, and validation contract before they are enabled.
- The source-write target for Library documents should be `_docs_library_src/*.md`, not `_docs_src/*.md`.
- The preview file extension requirement needs one explicit decision. This request says preview files are plain text saved as `.txt`, while v1 currently writes Markdown preview files under `var/docs/import-preview/library/`.
- Export changes are lower risk if treated as small additions to the existing Library export page: list-filter pills first, then output-format options after the export config/runtime format contract is checked.

## Open Questions

- Should v2 preview files use `.txt` exactly, or should they continue using Markdown-style preview files because they contain front matter and readable content sections?

continue using markdown. I only chose txt to differentiate the preview files from the source files which we often refer to as 'the markdown files' but it is just a question of being clear about what we are referring to.

- Should preview files include two YAML front-matter blocks as shown, or should the matched-config fields and unknown fields be represented inside one valid front-matter block with separate keys or sections?

it doesn't need to be valid YAML front matter, because we are not 'reading' the files as source documents. they only need to be human readable. data will be read from the staged JSON.

- When a staged file has parent-child data, should the hierarchy tree file be generated in addition to per-document previews for every import type, or only for relationship-shaped exports?

yes for all import types where possible. I am thinking that it might be best if relationship data is included in all config patterns. but that is a config choice, the import should cleanly handle files without the necessary partent-child data.

- Should the Import UI list represent preview files that were just generated in the current run only, or should it also show older preview files already present in `var/docs/import-preview/library/`?

only show preview files generated from the selected staged file.

- Should selected import actions operate from the staged JSON records, the generated preview files, or the in-memory preview report returned by the local service?

it depends on whether the in-memory contains the data needed. if not then operate from the JSON, not the preview files.

- What validation is required before enabling `Update summary`? For example: existing `doc_id`, changed summary only, non-empty summary, and source file found.

only validation needed is that doc_id exists as a target.

- What validation is required before enabling `Apply hierarchy`? For example: existing `doc_id`, existing parent id, no cycles, no self-parenting, and no orphaned parent references.

only validation needed is that doc_id exists as a target. if parent_id doesn't exist, the viewer should handle that by acting like parent_id = "".

- Should `Apply hierarchy` preserve current `sort_order` values exactly, or should parent changes trigger any sibling ordering review?

for now, preserve current values. it may be possible to infer the correct sort order from the order in which the tree is created, or the external service defining the relationships might also be able to specify sort order for each document.

- Should source-write actions create timestamped backups under `var/backups/` before editing `_docs_library_src/*.md`?

yes, as long as they are targetted by the recently introduced retention script

- Should output format checkboxes allow both JSON and JSONL for all configs, or should unsupported combinations be disabled by config with explanatory UI text?

yes allow both with unsupported combinations disabled

- Should the export filter pill `no content` mean missing source text in generated payloads, no body content after plain-text extraction, or missing summary/content fields in the selected export config?

no body content after plain-text extraction

- Should `not viewable` include unpublished docs, generated non-viewable docs, or only published docs that are present in generated data but hidden from the public docs viewer?

only published docs that are present in generated data but hidden from the public docs viewer

## Draft Implementation Tasks

### Task 1. Align The Import UI With The Export Page

Reshape `/studio/library-import/` to mirror the Library export page's layout, status handling, selection controls, and result presentation.

Expected outputs:

- staged-file selector remains the first control
- preview action remains disabled when the docs-management service is unavailable
- generated preview results render in the main document list area
- selection controls include `select all` and `clear`
- import-action buttons are present but disabled until their service contracts exist
- UI copy is stored in `studio_config.json` where the page needs labels or messages

### Task 2. Render Preview Results As A Selectable Hierarchy

Use the preview-generation report to populate a selectable list of previewed documents.
Indent rows by parent-child relationship when staged relationship data is available.

Expected outputs:

- checkbox rows for previewed documents
- document titles shown before file paths
- parent-child indentation derived from staged metadata
- clear handling for missing titles, missing ids, duplicate ids, and records that cannot map to current Library docs
- a visible hierarchy/tree preview file row when the import engine generated one

### Task 3. Decide And Normalize Preview File Output

Confirm the v2 preview file extension and front-matter structure, then update the import renderer and docs to match.

Expected outputs:

- deterministic preview filenames based on `doc_id` plus the staged-file timestamp, with a current-local-time fallback
- one chosen preview extension and content format
- matched export-config fields separated from staged-only fields in a way that remains parseable or intentionally plain text
- tree hierarchy preview output when parent-child metadata is available
- tests updated for the chosen filename and preview content contract

### Task 4. Add Export Page Filter Pills

Add the requested Library export list filters without changing the export write path.

Expected outputs:

- `show all` filter
- `no content` filter
- `not viewable` filter
- filter counts if they can be derived cheaply from the existing index/config data
- focused UI smoke coverage for filter state and selection behavior

### Task 5. Add Export Format Options

Expose JSON and JSONL format options in the Library export UI after confirming the config/runtime format contract.

Expected outputs:

- JSON available where the selected config supports JSON output
- JSONL defaulted for document-content exports if the config supports it
- unsupported format/config combinations disabled or blocked before service submission
- export request payload and result modal show the selected format
- CLI/service tests cover both JSON and JSONL where supported

### Task 6. Define Summary Apply Contract

Specify and implement the narrow source-write path for applying imported summaries.

Expected outputs:

- selected preview records map back to staged JSON records and current Library source files
- preflight report with update count, skipped rows, warnings, and blocking errors
- confirmation modal with OK and Cancel
- timestamped backup before writing source files
- write service endpoint constrained to `_docs_library_src/`
- tests for unchanged summaries, missing docs, missing source files, malformed staged rows, backup creation, and write output

### Task 7. Define Hierarchy Apply Contract

Specify and implement parent_id writes separately from summary updates.

Expected outputs:

- parent-id preflight checks for existing docs, existing parents, no cycles, no self-parenting, and no missing source files
- confirmation modal with OK and Cancel
- timestamped backup before writing source files
- source writes limited to selected documents
- report includes changed, unchanged, skipped, warning, and error counts
- tests cover valid hierarchy changes, invalid parents, cycles, duplicate ids, partial selections, and cancellation/no-write paths

### Task 8. Update Documentation And Verification

Keep the v2 request, stable Library import/export docs, script docs, and generated docs-viewer payloads aligned as tasks move from proposed to implemented.

Expected outputs:

- update `_docs_src/library-import.md` when preview or apply behavior changes
- update `_docs_src/library-export.md` when filter or format behavior changes
- update script docs if CLI or service contracts change
- run `./scripts/build_docs.rb --scope studio --write` after docs-source changes
- run focused parser/service/UI checks for any runtime changes

## Benefits And Risks

Benefits:

- makes the import workflow match the export workflow visually and operationally
- keeps risky source writes behind explicit preview, selection, preflight, confirmation, and backup steps
- makes staged hierarchy data easier to inspect before applying `parent_id` changes
- gives JSON/JSONL export behavior a clearer UI contract

Risks:

- two-block front matter may be useful for human review but invalid for normal front-matter parsers
- import preview lists can become confusing if old preview files and current-run preview files are mixed without clear provenance
- applying hierarchy changes can create broad docs-navigation side effects from a small selected set
- broad JSON/JSONL format options can produce misleading exports unless each config declares supported formats precisely
