---
doc_id: scripts-docs-export
title: "Docs Export"
added_date: "2026-05-03 15:05"
last_updated: "2026-05-03 15:05"
parent_id: scripts
sort_order: 25
---

# Docs Export

Script:

```bash
./scripts/docs/docs_export.py
```

## Scope

`docs_export.py` is the read-only export engine for Docs Viewer export configs.

It reads generated Docs Viewer artifacts and source-controlled export configs, then writes an ephemeral export file under `var/docs/exports/`.
It does not mutate source Markdown, generated docs payloads, or config files.

Current input paths:

- `assets/studio/data/library_export_configs.json`
- `assets/data/docs/scopes/<scope>/index.json`
- `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`

Current output pattern:

- `var/docs/exports/<scope>/<timestamp>/<export_id>.json`
- `var/docs/exports/<scope>/<timestamp>/<export_id>.jsonl`

## Current Capability

Implemented now:

- loads a selected export config by `id`
- validates that the config is enabled for the requested scope
- loads generated Docs Viewer index data for the requested scope
- resolves selected `doc_id` values
- supports all-matching configs
- expands selected descendants when the config requests it
- excludes archived docs when the config requests it
- excludes unpublished docs when the config requests it
- includes generated but non-viewable docs when the config requests it
- supports missing-summary filtering for configs that allow it
- maps supported document fields into configured output paths
- computes parent, ancestor, and child relationship fields from the generated index
- extracts heading lists from rendered per-doc payload HTML
- writes JSON envelope exports
- writes JSONL document-row exports
- returns a structured JSON report

Not implemented yet:

- plain-text `source_text` extraction from rendered document content
- code-block omission and character truncation transforms
- batching or chunking
- Studio UI/service invocation

Configs that require `source_text` currently return a report error until the source-text extraction task is implemented.

## Commands

Dry-run the parent-child relationships export:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-parent-child-relationships
```

Write the parent-child relationships export:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-parent-child-relationships --write
```

Export explicit documents for configs that require selected ids:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-document-summaries --doc-id library
```

Use all matching docs for an explicit-selection config:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-document-summaries --all
```

Disable a summary config's default missing-summary-only filter:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-document-summaries --all --include-summary-complete
```

## Report Shape

The script prints a JSON report with:

- `ok`
- `dry_run`
- `config_id`
- `scope`
- `target_format`
- `output_file`
- `counts`
- `selected_doc_ids`
- `exported_doc_ids`
- `skipped`
- `warnings`
- `errors`
- `output_written`

The command exits with:

- `0` when the export is valid
- `1` for command/runtime failures
- `2` when the export config and selection load but validation errors prevent output

## Validation Boundary

The engine validates runtime concerns that the static config schema cannot know:

- selected config id exists
- config is enabled for the requested scope
- selected docs exist
- archive and publication filters are applied
- required mapped fields are present
- output paths stay under `var/docs/exports/`
- unsupported transforms are reported before writing

The static config schema remains documented in [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs).
