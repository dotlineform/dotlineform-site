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
- each document is formatted as readable Markdown-style preview text with front-matter-like metadata sections and saved as `.md`
- the front-matter-like metadata area is split into two sections:
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

`[doc_id]-[timestamp].md`

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
- Preview files should continue to use Markdown-style preview files under `var/docs/import-preview/library/`; they are review artifacts, not source Markdown documents.
- Export changes are lower risk if treated as small additions to the existing Library export page: list-filter pills first, then output-format options after the export config/runtime format contract is checked.

## Resolved Decisions

- Preview files should continue using Markdown-style files so they can use readable front-matter-like sections and body content without being confused with canonical Library source docs.
- Preview file front matter does not need to be valid YAML. Preview files are human-readable review artifacts; apply actions read from the staged JSON or the service report, not from preview files.
- When staged parent-child data is available, import preview should generate a hierarchy tree file in addition to per-document previews for all import types. Files without parent-child data should still preview cleanly.
- The Import UI should show only preview files generated from the selected staged file, not all older files already present in `var/docs/import-preview/library/`.
- Import actions should use the in-memory service report when it contains the needed data; otherwise they should read from the staged JSON. They should not read from generated preview files.
- `Update summary` validation should only require that each selected `doc_id` exists as a target Library source document.
- `Apply hierarchy` validation should only require that each selected `doc_id` exists as a target Library source document. Missing or unknown `parent_id` values are allowed, and the viewer should behave as if `parent_id` were blank.
- `Apply hierarchy` should preserve current `sort_order` values for now.
- Source-write actions should create timestamped backups before editing `_docs_library_src/*.md`, and those backups should be covered by a retention policy before write actions are enabled.
- Export format options should expose both JSON and JSONL, with unsupported config/format combinations disabled.
- The `no content` export filter means no body content after plain-text extraction.
- The `not viewable` export filter means published docs that are present in generated data but hidden from the public docs viewer.
- Relationship data should be explicit in export config rather than exposed as a UI option.
- Relationship data should be added to the current `full document content` export config pattern.
- The backup root for Library import source-write actions should use the easiest implementation path that keeps backups retention-managed.
- External hierarchy imports should be expected to include `sort_order` in a future version. Export configs and import apply behavior should be extended for `sort_order` when that field is introduced.

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
The list should represent the selected staged file's latest preview output only.

Expected outputs:

- checkbox rows for previewed documents
- document titles shown before file paths
- parent-child indentation derived from staged metadata
- clear handling for missing titles, missing ids, duplicate ids, and records that cannot map to current Library docs
- a visible hierarchy/tree preview file row when parent-child metadata is available
- no mixed display of unrelated older preview files already present in the preview folder

### Task 3. Normalize Preview File Output

Update preview rendering so generated files are clearly review-only Markdown-style artifacts.
They do not need valid YAML front matter because source writes read from staged JSON or the service report.

Expected outputs:

- deterministic preview filenames based on `doc_id` plus the staged-file timestamp, with a current-local-time fallback
- Markdown-style preview files, not `.txt` files
- matched export-config fields separated from staged-only fields in a human-readable format
- tree hierarchy preview output when parent-child metadata is available
- importer remains tolerant of missing relationship metadata
- tests updated for the chosen filename and preview content contract

### Task 4. Add Relationship Data To Full Document Content Export

Update the existing full-document-content Library export config so relationship metadata is explicitly present in that config pattern.
This is a config/runtime contract, not a UI toggle.

Expected outputs:

- current `parent_id` relationship data included in full-document-content exports
- relationship data remains config-declared rather than controlled by a separate UI checkbox
- import preview can generate the hierarchy tree from full-document-content staged files when relationship data is present
- tests cover full-document-content export relationship fields
- note future `sort_order` support as a later config extension

### Task 5. Add Export Page Filter Pills

Add the requested Library export list filters without changing the export write path.

Expected outputs:

- `show all` filter
- `no content` filter for docs with no body content after plain-text extraction
- `not viewable` filter for published generated docs hidden from the public Docs Viewer
- filter counts if they can be derived cheaply from the existing index/config data
- focused UI smoke coverage for filter state and selection behavior

### Task 6. Add Export Format Options

Expose JSON and JSONL format options in the Library export UI after confirming the config/runtime format contract.

Expected outputs:

- JSON available where the selected config supports JSON output
- JSONL defaulted for document-content exports if the config supports it
- unsupported format/config combinations disabled before service submission
- export request payload and result modal show the selected format
- CLI/service tests cover both JSON and JSONL where supported

### Task 7. Define Summary Apply Contract

Specify and implement the narrow source-write path for applying imported summaries.

Expected outputs:

- selected preview records map back to staged JSON records and current Library source files
- preflight report with update count and skipped rows
- validation limited to selected `doc_id` values that do not exist as target Library source documents
- confirmation modal with OK and Cancel
- timestamped backup before writing source files, using the easiest compatible retention-managed backup root
- write service endpoint constrained to `_docs_library_src/`
- tests for missing target docs, backup creation, and write output

### Task 8. Define Hierarchy Apply Contract

Specify and implement parent_id writes separately from summary updates.

Expected outputs:

- preflight checks limited to selected `doc_id` values that do not exist as target Library source documents
- unknown or missing parent ids are allowed and treated by the viewer as root-level relationships
- confirmation modal with OK and Cancel
- timestamped backup before writing source files, using the easiest compatible retention-managed backup root
- source writes limited to selected documents
- current `sort_order` values are preserved
- report includes changed, unchanged, skipped, warning, and error counts
- tests cover valid hierarchy changes, missing target docs, unknown parent ids, partial selections, and cancellation/no-write paths
- future `sort_order` import remains out of scope until staged import files include that field

### Task 9. Update Documentation And Verification

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

- front-matter-like preview sections may look parseable even though they are intentionally review-only text
- import preview folders can still accumulate older files even if the UI only shows the selected staged file's current previews
- applying hierarchy changes can create broad docs-navigation side effects from a small selected set, especially because unknown parent ids are allowed
- broad JSON/JSONL format options can produce misleading exports unless each config declares supported formats precisely
