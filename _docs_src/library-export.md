---
doc_id: library-export
title: Library Export
added_date: 2026-05-03
last_updated: 2026-05-03
ui_status: in-progress
parent_id: library
sort_order: 25
---
# Library Export

Status:

- proposed

## Summary

This change request specifies a Studio Library export workflow for creating files derived from canonical Docs Viewer source data.

An export is not a canonical source record and is not a direct language-model integration.
It is a generated document produced from selected Docs Viewer source documents, shaped for a configured consumer, and written as a file that can be used by internal Studio reporting or manually copied for external consumption.

The first use case is Library semantic enrichment, especially document summaries and structure review.
The export framework should still be extensible across all Docs Viewer scopes.
Library is the primary scope and should drive the first implementation.

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

Config should define at least:

- export id and label
- allowed scope or scopes
- target format
- output path pattern
- selected fields
- field aliases or nested output paths
- body extraction mode, when content is included
- optional limits such as maximum characters per document
- default inclusion filters such as published-only or missing-summary-only

The config file should be edited as source-controlled project configuration.
The Studio UI can present and run existing configs, but creating or changing config definitions is not part of the first UI requirement.

### Selection UI

The Studio Library export page should support selecting many documents from the Library hierarchy.
The Library hierarchy may be deeper and more book-like than Studio docs, so branch selection matters.

Recommended UI shape:

- hierarchical checklist of Library docs
- indentation to show depth
- expand and collapse controls for branches
- checkbox per doc
- selecting a parent selects all descendants
- deselecting a child puts ancestors into an indeterminate state
- select all and clear controls
- option to limit the view or export to docs missing summaries when the selected config supports it
- optional include or exclude archived docs control

The UI should show operational counts before export:

- selected docs
- selected docs missing summaries when summary fields are relevant
- estimated exported characters or file size
- number of batches or files when batching is configured

The exporter should write explicit selected `doc_id` values into the export metadata.
The exported file should not depend on parent-selection state after it is created.

### Target Formats

The primary target format is JSON.
JSON exports should be structured and populated for LLM upload workflows, but the shape should not be locked to LLM usage only.
Other consumers may need the same source data later.

The export structure should therefore be template or config driven rather than hardcoded around one prompt.

Markdown export may be added later for cases where a human-readable document is the better target.
Markdown is out of scope for the first implementation except for reserving the config boundary so it can be added cleanly.

### Source Text Extraction

When an export includes document content, the default `source_text` should be plain UTF-8 text derived from rendered document content, not raw Markdown or raw HTML.

Rules:

- omit YAML front matter
- omit HTML tags
- omit the document title when it is already present in the structured title field
- preserve paragraph breaks with blank lines
- preserve list items as separate lines
- preserve headings as text while also exposing headings as structured data
- preserve blockquotes as separate lines, optionally prefixed with `> `
- omit code blocks or replace them with a short marker unless the export config explicitly includes code
- normalize whitespace enough for model input without destroying paragraph structure

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

This export should normally include the full published Library corpus because relationship review depends on corpus-wide context.
It should not require full document body text once summaries exist.

#### 2. Document Summaries

Purpose:

- support summary generation, missing-summary review, and summary audit workflows

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
      "current_summary": "",
      "source_text": "Plain text derived from the rendered document."
    }
  ]
}
```

Useful config defaults:

- published docs only
- option for missing summaries only
- configurable maximum characters per document
- optional batching when file size or character count crosses a configured threshold

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

### Output Files

Export files are ephemeral working artifacts, not canonical source.
They should be safe to delete and reproducible from canonical Docs Viewer source plus the selected export config.

Expected first output pattern:

```text
var/docs/exports/<scope>/<timestamp>/<export_id>.json
```

Each export file should include metadata:

- export id
- scope
- generated timestamp
- source docs index version or checksum when available
- selected `doc_id` values
- config id or config checksum
- counts for included, skipped, and truncated documents

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

## Open Questions

- Where should export configs live: `assets/studio/data/studio_config.json`, a dedicated `assets/studio/data/library_export_configs.json`, or another config file?
- Should exports write one JSON file by default, or should large exports automatically create batches plus a manifest?
- Should all export files use array-based JSON, or should some configs support JSONL for easier streaming and recombination?
- Which checksum or generated-docs metadata is stable enough to record as the source version?
- Should archived or unpublished docs ever be exportable through the Studio UI?
- Should source Markdown be allowed as a first implementation option, or only after plain-text extraction is stable?
- What validation should block an export config from running?
- Should export runs be added to a Studio activity feed?

## Implementation Tasks

### Task 1. Define Export Config Schema

Create the config schema for export patterns, including scope support, output format, field mapping, transform rules, limits, and output path pattern.

### Task 2. Add Initial Export Configs

Add configs for:

- parent-child relationships data
- document summaries
- full document content with multiple documents in one file

### Task 3. Build Read-Only Export Engine

Implement a read-only exporter that loads the selected Docs Viewer scope, applies the selected config, resolves selected `doc_id` values, writes the export file, and returns a structured report.

### Task 4. Add Source Text Extraction

Add plain-text extraction from rendered Docs Viewer content for configs that include body text.
Keep extraction deterministic and avoid including raw HTML in default exports.

### Task 5. Add Studio Library Export Page

Create a Library-scope Studio page that lists export configs, supports hierarchical document selection, runs the export, and displays the resulting report.

### Task 6. Add Local Service Endpoint

Expose the export engine through a loopback-only Studio service endpoint with an allowlisted output directory and minimal logs.

### Task 7. Add Validation And Reporting

Validate export config shape, selected documents, output paths, and required fields.
Return counts and warnings to the Studio UI.

### Task 8. Document Runtime And Config Usage

Update Library, Studio, config, scripts, and data-model docs as needed once implementation begins.

### Task 9. Verify Export Workflows

Add targeted checks for config loading, deterministic output, selected-doc resolution, and representative Library exports.
Add a light Studio smoke test once the UI exists.
