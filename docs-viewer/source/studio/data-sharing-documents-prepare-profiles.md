---
doc_id: data-sharing-documents-prepare-profiles
title: Documents Prepare Profiles
added_date: "2026-05-03 14:15"
last_updated: 2026-06-25
parent_id: data-sharing
viewable: true
---
# Documents Prepare Profiles

Config file:

- `data-sharing/adapters/documents/config/prepare-profiles.json`

There is no separate JSON Schema file for this config.
The documents package engine validates the profile payload and selected profile semantically at runtime.

## Scope

`prepare-profiles.json` defines package-preparation profiles for the documents Data Sharing adapter.
The file is adapter-local because it describes document package shapes, document field mappings, target formats, selection defaults, and output behavior interpreted by `data-sharing/adapters/documents/`.

Docs Viewer scope is not encoded in the filename.
The running prepare request supplies scope through `selection.docs_scope`.
Current profiles are used for the Library scope, but the same profile file can support other Docs Viewer-backed scopes when their document package shape is compatible.

The Analytics Data Sharing UI reads a browser-safe projection of these profiles from `/analytics/api/data-sharing/config`.
Browser routes must not fetch this config file directly.

## Usage Model

To add or change a document package pattern, edit `data-sharing/adapters/documents/config/prepare-profiles.json`.
Profile changes should be checked with the documents package/export tests because there is no standalone schema file.
The Analytics prepare page can edit the selected profile's `external_context` fields through its Edit context modal; structural profile changes such as field mappings, target shape, and output paths remain source-file edits.

Each profile controls:

- whether the UI presents it
- whether the user selects explicit documents or the exporter uses all matching documents
- whether selected parent documents include descendants
- whether source docs marked non-viewable are included
- whether summary profiles default to missing-summary-only filtering
- which source-derived document fields are written to each output record
- whether body content is converted to plain text and how images/SVGs are represented
- which JSON or JSONL file pattern the run writes

The config is the contract between the Analytics prepare UI, the Analytics Data Sharing API, the documents adapter, and the documents package engine.
Any new field source, transform, output format, or record shape needs export-engine validation before use.

## Current Profiles

The current file defines three enabled document package profiles:

- `library-parent-child-relationships`
  envelope JSON for selected-branch or explicitly selected whole-corpus hierarchy and relationship review
- `library-document-summaries`
  JSONL document rows for summary coverage and summary audit, defaulting to missing-summary filtering and excluding full document body text
- `library-full-document-content`
  JSONL document rows for exporting multiple selected document bodies in one file, including explicitly declared parent, ancestor, and child relationship metadata

The profile ids are still Library-named because those were the first document package patterns.
Do not infer a separate config file per Docs Viewer scope from those ids.
Add a new profile only when another scope needs a materially different package shape, field set, limits, or selection behavior.

## Top-Level Shape

The config root contains `schema_version: "documents_prepare_profiles_v1"` plus a `configs` array.
`configs` is an array of profile objects and must contain at least one enabled or disabled profile.
Each profile must be independently runnable and must define its data-domain support, target format, output path, selection rules, limits, export metadata, and document field mappings.

## Profile Fields

Each profile requires:

- `id`: stable profile id, using lowercase kebab-case
- `label`: UI label for the prepare-profile selector
- `description`: short UI-facing description
- `enabled`: whether the Analytics UI should present the profile
- `data_domains`: allowed Data Sharing data domains, currently `documents`
- `target`: output format and record shape
- `output`: output path pattern and optional timestamp format
- `selection`: default document selection and filtering behavior
- `limits`: document and character limits
- `metadata`: export-run metadata fields to include
- `external_context`: external task wording, response guidance, and field descriptions
- `document_fields`: mappings from Docs Viewer source metadata into the output record

## Target

`target.format` supports:

- `json`
- `jsonl`

`target.format` is the default format for the profile.
`target.supported_formats` optionally declares every format the runtime and Analytics UI may choose for that profile.
When omitted, the default `target.format` is the only supported format.

`target.record_shape` supports:

- `envelope`: one JSON object containing a document array
- `document_rows`: one complete document record per JSONL row, or one JSON array when `json` is selected

When `target.record_shape` is `envelope`, `document_array_path` identifies where document records are written, normally `documents`.
Envelope profiles support JSON only.
Document-row profiles may support JSONL and JSON when both are declared in `target.supported_formats`.
Export-run metadata is written once to a sibling `.meta.json` sidecar instead of being included in the external JSON or JSONL payload.
A sibling `.context.json` sidecar describes the external task, record container, record schema, and response guidance without internal provenance.
External payload records should not include internal run details, row counts, checksums, or source timestamps; source-date provenance belongs in `.meta.json`.

## External Context

`external_context` owns the operator-facing wording sent beside an external package.
It is intentionally config-driven so task labels, response guidance, and field descriptions can iterate without changing exporter code.

Each profile must define:

- `task`: short machine-readable task label for the external service
- `response_guidance`: concise instruction text for the expected response shape
- `field_descriptions`: one description for every `document_fields[].output_path`

The exporter derives `.context.json` from `external_context`, `target`, and `document_fields`.
It infers simple field types from the field mapping/defaults and preserves the configured descriptions verbatim.
Validation fails when a document output field has no description or when `field_descriptions` contains a stale field that no longer exists in `document_fields`.

The prepare UI exposes only `external_context.task`, `external_context.response_guidance`, and `external_context.field_descriptions`.
Saving from the modal rewrites the profile config after validating the full prepare-profile payload.

## Output

`output.path_pattern` must stay under the shared Data Sharing export root:

```text
var/analytics/data-sharing/exports/{export_id}-{timestamp}.json
var/analytics/data-sharing/exports/{export_id}-{timestamp}.jsonl
var/analytics/data-sharing/exports/{export_id}-{timestamp}.meta.json
var/analytics/data-sharing/exports/{export_id}-{timestamp}.context.json
```

The placeholders are resolved by the export engine.
Current profiles use `{export_id}` and `{timestamp}`.
Other placeholders, including `{data_domain}`, are only valid when supported by the export engine and still resolve under the shared export root.
When an operator chooses a non-default supported format, the export engine keeps the configured directory, export id, and timestamp, then switches the output file extension to the selected format.
The `.meta.json` and `.context.json` patterns are derived from the output filename; they are not configured as separate profile paths.

`timestamp_format` defaults to `%Y%m%d-%H%M%S`.
It formats the filename timestamp in the local runtime timezone.
Export metadata `generated_at` remains UTC.

The package engine is documented in [Documents Package Preparation Script](/docs/?scope=studio&doc=scripts-docs-export).

## Selection

`selection.mode` supports:

- `explicit_doc_ids`: the Analytics UI supplies selected document ids through `selection.doc_ids`
- `all_matching`: the exporter includes every document matching the profile filters

Selection also defines whether the run includes descendants and non-viewable docs.
Current profiles use explicit document selection; Select all in Analytics or `--all` in the CLI remains available when a whole-corpus export is intentional.

`supports_missing_summary_only` and `default_missing_summary_only` are profile-level flags for summary-focused exports.

## Document Fields

`document_fields` maps source fields to output paths.
Fields are read from Docs Viewer source metadata and source-rendered content.
Generated docs indexes, generated by-id payloads, public tree/search/recently-added payloads, and generated metadata JSON are not valid field sources for document Data Sharing exports.

Supported source fields include:

- `doc_id`
- `title`
- `parent_id`
- `parent_title`
- `ancestor_ids`
- `ancestor_titles`
- `child_ids`
- `child_titles`
- `summary`
- `current_summary`
- `headings`
- `source_text`
- `last_updated`
- `viewable`

Each field mapping requires `source` and `output_path`.
Optional controls include `required`, `include_if_empty`, `default`, `transforms`, `limit_key`, and `options`.

Supported transforms include:

- `identity`
- `plain_text_from_rendered_html`
- `headings_from_rendered_html`
- `normalize_whitespace`
- `omit_code_blocks`
- `truncate_chars`

The default content export should use rendered Docs Viewer HTML as the source for plain text extraction, not raw Markdown.

## Validation Boundary

Validation is implemented by the documents package engine, not by a separate schema file.
Runtime validation checks source-dependent concerns such as unknown `doc_id` values, missing required fields, output path resolution, target format support, profile enablement, and whether a selected profile supports the requested data domain.

Blocking profile errors include duplicate profile ids, unsupported target formats, unsupported record shapes, unsupported field sources or transforms, duplicate or conflicting output paths, unsafe output paths, `source_text` mappings that would emit raw rendered HTML, and truncating mappings without configured integer limits.

Warnings are reserved for non-blocking runtime context such as expected skipped filters, ignored `doc_ids` when `select_all` is true, ignored `missing_summary_only` on unsupported profiles, truncation, and deferred `max_total_chars` enforcement.

## Verification

Run focused checks after changing document prepare profiles:

```bash
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_export.py -q
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_analytics_data_sharing_api.py analytics-app/tests/python/test_data_sharing_adapters.py -q
```
