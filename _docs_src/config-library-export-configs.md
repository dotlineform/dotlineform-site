---
doc_id: config-library-export-configs
title: "Library Export Configs"
added_date: "2026-05-03 14:15"
last_updated: "2026-05-03 14:15"
parent_id: config
sort_order: 70
---

# Library Export Configs

Config file:

- `assets/studio/data/library_export_configs.json`

Schema file:

- `assets/studio/data/library_export_configs.schema.json`

## Scope

`library_export_configs.json` will define saved export patterns for the Library export workflow.

The first implementation scope is Library, but the schema keeps the scope field as an array so the same export engine can later support other Docs Viewer scopes.

The config is source-controlled project configuration.
The Studio UI should list and run existing configs, but it should not create or edit config definitions in v1.

## Top-Level Shape

The config root contains `schema_version: "library_export_configs_v1"` plus a `configs` array.
`configs` is an array of export pattern objects and must contain at least one enabled or disabled export pattern once the config file is added.
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

`target.record_shape` supports:

- `envelope`
  one JSON object containing run metadata plus a document array
- `document_rows`
  one complete document record per JSONL row

When `target.record_shape` is `envelope`, `document_array_path` identifies where document records are written, normally `documents`.

## Output

`output.path_pattern` must stay under:

```text
var/docs/exports/{scope}/{timestamp}/{export_id}.json
var/docs/exports/{scope}/{timestamp}/{export_id}.jsonl
```

The placeholders are resolved by the export engine.
The path is intentionally constrained to keep generated export files out of source docs and public assets.

`timestamp_format` defaults to `%Y%m%d-%H%M%S`.

## Selection

`selection.mode` supports:

- `explicit_doc_ids`
  the Studio UI supplies selected document ids
- `all_matching`
  the exporter includes every document matching the config filters

Selection also defines whether the run includes descendants, non-viewable docs, archived docs, and unpublished docs.

V1 Library exports should normally use:

- `include_non_viewable: true`
- `exclude_archived: true`
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

Supported transforms are:

- `identity`
- `plain_text_from_rendered_html`
- `headings_from_rendered_html`
- `normalize_whitespace`
- `omit_code_blocks`
- `truncate_chars`

The default v1 content export should use rendered Docs Viewer HTML as the source for plain text extraction, not raw Markdown.

## Validation Boundary

The schema validates config shape and allowed keys.
Runtime validation still needs to check source-dependent concerns such as unknown `doc_id` values, archived descendants, missing required fields, output path resolution, and whether a selected config is enabled for the requested scope.

Benefits:

- config files can be reviewed independently before exporter code exists
- Studio UI code can rely on one stable config shape
- future Docs Viewer scopes are not blocked by Library-first defaults

Risks:

- the first schema is intentionally narrow and may need extension once real exports expose missing field or batching needs
- JSON Schema validates the static shape, not the full runtime behavior of an export run
