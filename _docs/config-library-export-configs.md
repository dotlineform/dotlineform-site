---
doc_id: config-library-export-configs
title: Library Export Configs
added_date: "2026-05-03 14:15"
last_updated: "2026-05-06 21:14"
parent_id: import-export
sort_order: 50
---
# Library Export Configs

Config file:

- `assets/studio/data/library_export_configs.json`

Schema file:

- `assets/studio/data/library_export_configs.schema.json`

## Scope

`library_export_configs.json` defines saved export patterns for the Library export workflow.

The first active data domain is Library.
The schema keeps the scope field as an array so the same export engine can later support other document-backed scopes, but non-Library domains must still be enabled through `assets/studio/data/export_import_adapters.json`.

The config is source-controlled project configuration.
The Studio UI lists existing configs and uses them to drive selection behavior, but it should not create or edit config definitions in v1.
Running configs from Studio uses the local docs-management export endpoint.

## Usage Model

To add or change an export pattern, edit `assets/studio/data/library_export_configs.json` and keep it aligned with `assets/studio/data/library_export_configs.schema.json`.
The Studio UI reads enabled configs for the Library scope and presents them as runnable export patterns; it does not persist config edits.

Each config controls:

- whether Studio presents it for Library
- whether the user selects explicit docs or the exporter uses all matching docs
- whether selected parent docs include descendants
- whether generated but non-viewable docs are included
- whether unpublished docs are excluded
- whether summary configs default to missing-summary-only filtering
- which source/generated fields are written to each output record
- whether body content is converted to plain text and how images/SVGs are represented
- which JSON or JSONL file pattern the run writes

The config is the contract between Studio selection, the local service, and the CLI.
Any new field source, transform, output format, or record shape needs both config/schema documentation and export-engine validation before use.

## Initial Configs

The first config file defines three enabled Library export patterns:

- `library-parent-child-relationships`
  envelope JSON for selected-branch or explicitly selected whole-corpus hierarchy and relationship review
- `library-document-summaries`
  JSONL document rows for summary coverage and summary audit, defaulting to missing-summary filtering and excluding full document body text
- `library-full-document-content`
  JSONL document rows for exporting multiple selected document bodies in one file, including explicitly declared parent, ancestor, and child relationship metadata

These configs are Library-only for v1.
They include generated but non-viewable docs and exclude unpublished docs. `archive` is treated like any other generated Library doc.
Catalogue and Analytics do not use these configs unless a future adapter explicitly chooses a compatible document-backed export model.

## Top-Level Shape

The config root contains `schema_version: "library_export_configs_v1"` plus a `configs` array.
`configs` is an array of export pattern objects and must contain at least one enabled or disabled export pattern.
Each pattern must be independently runnable and must define its scope support, target format, output path, selection rules, limits, export metadata, and document field mappings.

## Export Config Fields

Each config requires:

- `id`
  stable export id, using lowercase kebab-case
- `label`
  UI label for the export selector
- `description`
  short UI-facing description
- `enabled`
  whether the Studio UI should present the config
- `scopes`
  allowed Docs Viewer scopes, initially expected to contain `library`
- `target`
  output format and record shape
- `output`
  output path pattern and optional timestamp format
- `selection`
  default document selection and filtering behavior
- `limits`
  document and character limits
- `metadata`
  export-run metadata fields to include
- `document_fields`
  mappings from Docs Viewer source/generated fields into the export record

## Target

`target.format` supports:

- `json`
- `jsonl`

`target.format` is the default format for the config.
`target.supported_formats` optionally declares every format the runtime and Studio UI may choose for that config.
When omitted, the default `target.format` is the only supported format.

`target.record_shape` supports:

- `envelope`
  one JSON object containing run metadata plus a document array
- `document_rows`
  one complete document record per JSONL row, or one JSON array when `json` is selected

When `target.record_shape` is `envelope`, `document_array_path` identifies where document records are written, normally `documents`.
Envelope configs support JSON only.
Document-row configs may support JSONL and JSON when both are declared in `target.supported_formats`.

## Output

`output.path_pattern` must stay under:

```text
var/studio/export-import/{scope}/exports/{export_id}-{timestamp}.json
var/studio/export-import/{scope}/exports/{export_id}-{timestamp}.jsonl
```

The placeholders are resolved by the export engine.
The path is intentionally constrained to keep generated export files out of source docs and public assets.
When an operator chooses a non-default supported format, the export engine keeps the configured directory, export id, and timestamp, then switches the output file extension to the selected format.

`timestamp_format` defaults to `%Y%m%d-%H%M%S`.
It formats the filename timestamp in the local runtime timezone.
Export metadata `generated_at` remains UTC.

The first export engine is documented in [Docs Export](/docs/?scope=studio&doc=scripts-docs-export).

## Selection

`selection.mode` supports:

- `explicit_doc_ids`
  the Studio UI supplies selected document ids
- `all_matching`
  the exporter includes every document matching the config filters

Selection also defines whether the run includes descendants, non-viewable docs, archived docs, and unpublished docs.
The initial Library export patterns use explicit document selection; Select all in Studio or `--all` in the CLI remains available when a whole-corpus export is intentional.

V1 Library exports should normally use:

- `include_non_viewable: true`
- `exclude_archived: false`
- `exclude_unpublished: true`

`supports_missing_summary_only` and `default_missing_summary_only` are config-level flags for summary-focused exports.

## Limits

Limits are optional but explicit:

- `max_documents`
- `max_chars_per_document`
- `max_total_chars`
- `truncate.enabled`
- `truncate.strategy`
- `truncate.marker`

V1 should use these as simple guardrails.
Batching and long-document chunking remain future enhancements.

## Metadata

`metadata.include` lists export-level metadata fields.

Supported values are:

- `export_id`
- `config_id`
- `config_checksum`
- `scope`
- `generated_at`
- `selected_doc_ids`
- `source_last_updated`
- `counts`

V1 exports should include enough metadata to identify the selected source docs and their `last_updated` values.

## Document Field Mappings

`document_fields` maps source fields to output paths.

Supported source fields are:

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
- `published`

Each field mapping requires:

- `source`
  source field key
- `output_path`
  dot-path inside the exported document record

Optional field mapping controls:

- `required`
  missing or empty values should be reported as validation failures
- `include_if_empty`
  whether empty values should still be written
- `default`
  value used when the source field is missing
- `transforms`
  deterministic transforms applied before writing
- `limit_key`
  named limit used by truncating transforms
- `options`
  field-specific transform options, currently used by `source_text`

Supported transforms are:

- `identity`
- `plain_text_from_rendered_html`
- `headings_from_rendered_html`
- `normalize_whitespace`
- `omit_code_blocks`
- `truncate_chars`

The default v1 content export should use rendered Docs Viewer HTML as the source for plain text extraction, not raw Markdown.

`source_text` options:

- `image_text_mode`
  one of `omit`, `marker`, or `extract_text`
- `empty_image_mode`
  one of `omit` or `marker`

The initial document summaries export does not include `source_text`; body text belongs to the full-content export.
The initial full-content export declares `parent_id`, `parent_title`, `ancestor_ids`, `ancestor_titles`, `child_ids`, and `child_titles` in the config so relationship metadata travels with source text without a separate UI option.
It uses `image_text_mode: "extract_text"` and `empty_image_mode: "marker"` so external review can see where a visual object existed even without useful text.
`sort_order` is a future field-source/config extension for external hierarchy imports and is not part of the current full-content config.

## Validation Boundary

The schema validates config shape and allowed keys.
Runtime validation still needs to check source-dependent concerns such as unknown `doc_id` values, archived descendants, missing required fields, output path resolution, and whether a selected config is enabled for the requested scope.

The export engine also applies v1 semantic validation before writing.
Blocking config errors include duplicate config ids, unsupported target formats, unsupported record shapes, unsupported field sources or transforms, duplicate or conflicting output paths, unsafe output paths, `source_text` mappings that would emit raw rendered HTML, and truncating mappings without configured integer limits.

Warnings are reserved for non-blocking runtime context such as expected skipped filters, ignored `doc_ids` when `select_all` is true, ignored `missing_summary_only` on unsupported configs, truncation, and deferred `max_total_chars` enforcement.

Benefits:

- config files can be reviewed independently before exporter code exists
- Studio UI code can rely on one stable config shape
- future Docs Viewer scopes are not blocked by Library-first defaults

Risks:

- the first schema is intentionally narrow and may need extension once real exports expose missing field or batching needs
- JSON Schema validates the static shape, not the full runtime behavior of an export run
