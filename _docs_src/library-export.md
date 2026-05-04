---
doc_id: library-export
title: Library Export v1
added_date: 2026-05-03
last_updated: "2026-05-04"
ui_status: done
parent_id: library
sort_order: 25
---
# Library Export v1

Status:

- completed

## Summary

This change request specifies a Studio Library export workflow for creating files derived from canonical Docs Viewer source data.

An export is not a canonical source record and is not a direct language-model integration.
It is a generated document produced from selected Docs Viewer source documents, shaped for a configured consumer, and written as a file that can be used by internal Studio reporting or manually copied for external consumption.

The first use case is Library semantic enrichment, especially document summaries and structure review.
The export framework should still be extensible across all Docs Viewer scopes.
Library is the primary scope and should drive the first implementation.

The implementation should ship a narrow v1 and then iterate from real export runs.
The first version should prioritize predictable files, explicit selection, and simple config-driven shapes over automatic batching, direct LLM calls, or broad reporting infrastructure.

## Spec

### Product Boundary

Exports are run from a new Studio page under the Library scope.
The page presents available export configurations, lets the user choose which documents to include, runs the export, and reports the generated file location and counts.

The export path should:

- read from canonical Docs Viewer source for the selected scope
- resolve user selection to explicit `doc_id` values before writing
- write a generated export file rather than mutating source documents
- keep direct API calls to LLMs out of scope
- allow export files to support internal Studio reporting as well as manual external use

The implementation should treat Library as the first-class scope while avoiding assumptions that make Studio, Catalogue, or future Docs Viewer scopes impossible later.

### Configuration Model

Export patterns should be config driven.
A saved export pattern defines the fields, transforms, structure, target format, and defaults used for one export.

The Studio UI should not hardcode field sets.
It should read the available export configs, present them to the user, and then combine the selected config with an explicit document selection.

V1 export configs should live in a dedicated Library export config file, not in the general Studio config.
The expected first path is:

```text
assets/studio/data/library_export_configs.json
```

Config should define at least:

- export id and label
- allowed scope or scopes
- target format
- output path pattern
- selected fields
- field aliases or nested output paths
- body extraction mode, when content is included
- optional limits such as maximum characters per document
- default inclusion filters such as viewable state and missing-summary-only

The config file should be edited as source-controlled project configuration.
The Studio UI can present and run existing configs, but creating or changing config definitions is not part of the first UI requirement.

### Selection UI

The Studio Library export page should support selecting many documents from the Library hierarchy.
The Library hierarchy may be deeper and more book-like than Studio docs, so branch selection matters.

V1 UI shape:

- hierarchical checklist of Library docs
- indentation to show depth
- checkbox per doc
- list order matching the Docs Viewer index panel
- small read-only green dot when `viewable: true`
- selecting a parent selects all descendants
- deselecting a child puts ancestors into an indeterminate state
- select all and clear controls
- option to limit the view or export to docs missing summaries when the selected config supports it
- no other row metadata in the document list

V1 should exclude `published: false` docs because they are outside generated Docs Viewer data.
It should also exclude `_archive` and its descendants from the Studio export UI.
Generated but non-viewable docs, where `published: true` and `viewable: false`, are in scope and should be selectable because they are likely to need analysis before they become ready for public/default viewing.

The UI may show operational counts outside the document list before export:

- selected docs
- selected docs missing summaries when summary fields are relevant
- estimated exported characters or file size
- number of batches or files when batching is configured

The exporter should write explicit selected `doc_id` values into the export metadata.
The exported file should not depend on parent-selection state after it is created.

### V1 Target Formats

The primary target family is structured JSON data.
V1 should support config-selected `json` and `jsonl` output.

Array-based JSON is useful when the export needs one metadata object with a `documents` array.
JSONL is useful when multiple complete documents are included in one file, because each row can represent one complete document record and common LLM upload workflows handle that shape well.

JSON exports should be structured and populated for LLM upload workflows, but the shape should not be locked to LLM usage only.
Other consumers may need the same source data later.

The export structure should therefore be template or config driven rather than hardcoded around one prompt.

Automatic batching and chunking should wait until a later enhancement.
The first implementation should write one file per run unless a selected config explicitly defines a simple fixed split.
Criteria such as batch size, model input budget, and long-document chunking need real export evidence before they become product rules.

Markdown export may be added later for cases where a human-readable document is the better target.
Markdown is out of scope for the first implementation except for reserving the config boundary so it can be added cleanly.
Raw source Markdown should also wait for later configs rather than being a first implementation option.
Some future export configs may allow Markdown or raw source fields while others forbid them.

### Source Text Extraction

When an export includes document content, the default `source_text` should be plain UTF-8 text derived from rendered document content, not raw Markdown or raw HTML.

Rules:

- omit YAML front matter
- omit HTML tags
- omit the document title when it is already present in the structured title field
- preserve paragraph breaks with blank lines
- put headings on their own lines while also exposing headings as structured data
- preserve bullet items as separate lines starting with `- `
- preserve numbered list items as separate lines starting with `1.`, `2.`, `3.`, and so on
- preserve quoted material only when it is an actual quotation, using either `> ` or `quote: ` consistently
- omit code blocks or replace them with a short marker unless the export config explicitly includes code
- normalize whitespace enough for model input without destroying paragraph structure
- represent embedded images and SVGs according to the selected `source_text` field options
- when image text extraction is enabled, prefer `img alt`, SVG `title`, SVG `desc`, and SVG `text`
- when no image text is available, either emit `[image]` or omit the image based on config

Optional future or debug configs may include raw source Markdown.
`content_html` should not be part of the default LLM-oriented exports.

### Initial Export Configs

#### 1. Parent-Child Relationships Data

Purpose:

- support structure review and hierarchy analysis
- give an LLM or reporting workflow enough context to reason about current placement

Initial JSON shape should include:

```json
{
  "export_id": "library-parent-child-relationships",
  "scope": "library",
  "documents": [
    {
      "doc_id": "example-doc",
      "title": "Example Doc",
      "parent_id": "example-parent",
      "parent_title": "Example Parent",
      "ancestor_ids": ["root-doc"],
      "ancestor_titles": ["Root Doc"],
      "child_ids": ["example-child"],
      "child_titles": ["Example Child"],
      "summary": "Existing summary when available.",
      "headings": ["Purpose", "Details"]
    }
  ]
}
```

This export respects the Studio document checklist.
Select a parent to include that branch, or use Select all when relationship review needs the full generated, non-archived Library corpus.
It should not require full document body text once summaries exist.
Non-viewable docs should be included and marked so readiness review can focus on them.

#### 2. Document Summaries

Purpose:

- support missing-summary review and summary audit workflows
- export summary metadata only, without full document body text

Initial JSON shape should include:

```json
{
  "export_id": "library-document-summaries",
  "scope": "library",
  "documents": [
    {
      "doc_id": "example-doc",
      "title": "Example Doc",
      "parent_id": "example-parent",
      "headings": ["Purpose", "Details"],
      "current_summary": ""
    }
  ]
}
```

Useful config defaults:

- generated, non-archived docs only
- option for missing summaries only
- JSONL output when each row should be one complete document input

This export should not include `source_text` or full document body content.
When source text is needed for generation or external analysis, use the full document content export instead.

#### 3. Full Document Content

Purpose:

- create one file containing multiple full document bodies for external review, bulk LLM upload, or internal Studio reporting

Initial JSON shape should include:

```json
{
  "export_id": "library-full-document-content",
  "scope": "library",
  "documents": [
    {
      "doc_id": "example-doc",
      "title": "Example Doc",
      "parent_id": "example-parent",
      "summary": "Existing summary when available.",
      "headings": ["Purpose", "Details"],
      "source_text": "Full plain text body for this document."
    },
    {
      "doc_id": "second-doc",
      "title": "Second Doc",
      "parent_id": "example-parent",
      "summary": "Existing summary when available.",
      "headings": ["Purpose", "Details"],
      "source_text": "Full plain text body for another document."
    }
  ]
}
```

This export must support multiple documents in the same export file.
Character limits should be configurable, but the core purpose is to preserve enough content for meaningful external analysis.
JSONL should be the preferred v1 shape for this export when each line can carry one complete document.

### Output Files

Export files are ephemeral working artifacts, not canonical source.
They should be safe to delete and reproducible from canonical Docs Viewer source plus the selected export config.

Expected first output pattern:

```text
var/docs/exports/<scope>/<export_id>-<timestamp>.json
```

JSONL configs use the same flat scope directory and filename timestamp pattern:

```text
var/docs/exports/<scope>/<export_id>-<timestamp>.jsonl
```

Filename timestamps use the local runtime timezone so Studio output paths match the operator's clock.
Export metadata should keep `generated_at` in UTC for stable provenance.

Each export file should include metadata:

- export id
- scope
- generated timestamp
- source document `last_updated` values
- selected `doc_id` values
- config id or config checksum
- counts for included, skipped, and truncated documents

V1 should use source document `last_updated` as the source version marker.
Existing date-only docs remain valid, and new Docs Viewer management writes use minute-precision `last_updated` values.

### Reporting

The exporter should report:

- docs selected
- docs exported
- docs skipped and reasons
- docs truncated by configured limits
- output file path
- target format
- warnings about missing fields required by the selected config

The Studio page should show this report after export and make the file path visible for the next manual step.

### Local Service Endpoint

Studio runs exports through the docs-management local service:

```text
POST /docs/export
```

Request shape:

```json
{
  "scope": "library",
  "config_id": "library-document-summaries",
  "doc_ids": ["library"],
  "select_all": false,
  "missing_summary_only": true
}
```

The endpoint calls the shared read-only export engine and writes only under `var/docs/exports/`.
It logs ids, counts, format, and write state, but not document body content or full export payloads.
When the docs-management server runs with `--dry-run`, the endpoint validates and reports the target file path without writing the export file.

## Open Questions

- What real thresholds should later trigger batching or long-document chunking?

## Current Decisions

- V1 should be small and iterative rather than attempting a complete export platform.
- Library is the first implementation scope, but configs should not prevent future Docs Viewer scopes.
- Export configs should live in a dedicated Library export config file.
- V1 should support config-selected `json` and `jsonl`.
- JSONL is preferred when multiple complete document records are exported in one file for LLM upload.
- Automatic batching and chunking are future enhancements.
- V1 should use source document `last_updated` values as the source version marker.
- Existing date-only `last_updated` values remain valid; newly managed docs use `YYYY-MM-DD HH:MM`.
- `published: false` docs and `_archive` descendants should not be exportable through the v1 Studio UI.
- Non-viewable generated docs should be exportable and visibly marked.
- Raw source Markdown and Markdown target documents are later config extensions, not v1 defaults.
- Export runs should not be added to a Studio activity feed in v1.

## Validation And Reporting

V1 validation should prefer blocking failures when an export would be ambiguous, unsafe, structurally invalid, or likely to mislead a consumer.
It should prefer warnings when the export can still produce a coherent file and the issue is useful context for the user.

Blocking validation errors:

- config file shape is invalid, including wrong `schema_version`, duplicate config ids, unsupported target format, unsupported record shape, unsupported field source, unsupported transform, duplicate or conflicting output paths, or mismatched output extension
- selected config is disabled or does not support the requested scope
- output path is missing, unsafe, or outside `var/docs/exports/`
- explicit selected `doc_id` values are unknown
- selection resolves to zero exportable documents after filters
- required mapped fields are missing or empty
- a required generated payload cannot be loaded for mapped fields such as headings or source text
- `source_text` mappings would write raw rendered HTML instead of using `plain_text_from_rendered_html`
- truncating field mappings are configured without a supported integer limit

Warnings:

- selected docs are skipped by expected filters such as archive exclusion, publication exclusion, missing-summary filtering, non-viewable filtering, or `max_documents`
- `select_all` causes explicit `doc_ids` to be ignored
- `missing_summary_only` is requested for a config that does not support it
- selected docs are truncated by configured limits
- `max_total_chars` is declared, because total-length enforcement and batching are deferred beyond v1

Export reports should include:

- selected, exported, skipped, failed, and truncated counts
- explicit exported `doc_id` values
- structured skipped rows with reason codes
- skipped reason totals
- warning and error lists
- issue counts for warnings and errors

## V1 Runtime Usage

The Library export v1 runtime has three entry points around one shared export engine:

- Studio page: `/studio/library-export/`
- local service endpoint: `POST /docs/export` on `./scripts/docs/docs_management_server.py`
- CLI: `./scripts/docs/docs_export.py`

The Studio page is the normal interactive path.
It loads enabled Library export configs, loads the generated Library docs index, applies the config's selection behavior, and posts the selected config plus explicit document ids to the docs-management service.
The browser does not write files directly.

The local service endpoint is the Studio write boundary.
It validates request shape, calls the same export engine used by the CLI, writes only under `var/docs/exports/`, logs only ids/counts/status, and returns the structured report used by the Studio result panel.

The CLI is the operational and testable path.
It can dry-run by default, write with `--write`, run the same config validation, and report the same selected/exported/skipped/failed/truncated counts.

V1 export files are working artifacts.
They are not canonical source, are ignored by git, and should be reproducible from:

- generated Docs Viewer scope data
- the selected source-controlled export config
- the selected document ids and run options

The first supported output layouts are:

```text
var/docs/exports/library/library-parent-child-relationships-<timestamp>.json
var/docs/exports/library/library-document-summaries-<timestamp>.jsonl
var/docs/exports/library/library-full-document-content-<timestamp>.jsonl
```

Manual external use is expected in v1.
Direct LLM API calls, automatic batching, markdown target files, raw Markdown exports, and Studio activity-feed entries are deferred.

## Implementation Tasks

### Task 1. Define Export Config Schema

Create the config schema for export patterns, including scope support, output format, field mapping, transform rules, limits, and output path pattern.

Status: implemented as `assets/studio/data/library_export_configs.schema.json`; see [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs).

### Task 2. Add Initial Export Configs

Add configs for:

- parent-child relationships data
- document summaries
- full document content with multiple documents in one file

Status: implemented in `assets/studio/data/library_export_configs.json`.

### Task 3. Build Read-Only Export Engine

Implement a read-only exporter that loads the selected Docs Viewer scope, applies the selected config, resolves selected `doc_id` values, writes the export file, and returns a structured report.

Status: implemented by `./scripts/docs/docs_export.py`; see [Docs Export](/docs/?scope=studio&doc=scripts-docs-export).

### Task 4. Add Source Text Extraction

Add plain-text extraction from rendered Docs Viewer content for configs that include body text.
Keep extraction deterministic and avoid including raw HTML in default exports.

Status: implemented in `./scripts/docs/docs_export.py`, including config-driven image/SVG text handling.

### Task 5. Add Studio Library Export Page

Create a Library-scope Studio page that lists export configs, supports hierarchical document selection, and prepares the selected config/doc ids for the export service.

Status: implemented at `/studio/library-export/`. The page loads enabled Library export configs, renders a hierarchical checkbox list in Docs Viewer order, excludes `_archive` descendants, marks viewable docs with a green dot, runs exports through the local service endpoint, and displays counts, output path, warnings, and errors.

### Task 6. Add Local Service Endpoint

Expose the export engine through a loopback-only Studio service endpoint with an allowlisted output directory and minimal logs.

Status: implemented as `POST /docs/export` on `./scripts/docs/docs_management_server.py`; the Studio Library export page now runs exports through that endpoint and displays the output file, format, counts, and warnings.

### Task 7. Add Validation And Reporting

Validate export config shape, selected documents, output paths, and required fields.
Return counts and warnings to the Studio UI.

Status: implemented in `./scripts/docs/docs_export.py`, `POST /docs/export`, and the Studio Library export result UI.

### Task 8. Document Runtime And Config Usage

Update Library, Studio, config, scripts, and data-model docs as needed once implementation begins.

Status: implemented across this doc, [Docs Export](/docs/?scope=studio&doc=scripts-docs-export), [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server), [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs), [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json), [Library Scope](/docs/?scope=studio&doc=data-models-library), [Studio](/docs/?scope=studio&doc=studio), and [Scripts](/docs/?scope=studio&doc=scripts).

### Task 9. Verify Export Workflows

Add targeted checks for config loading, deterministic output, selected-doc resolution, and representative Library exports.
Add a light Studio smoke test once the UI exists.

Status: implemented in `tests/python/test_docs_export.py`, `tests/smoke/library_export.py`, and the `docs` profile in `./scripts/run_checks.py`.
