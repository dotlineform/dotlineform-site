---
doc_id: scripts-docs-export
title: "Docs Export"
added_date: "2026-05-03 15:05"
last_updated: "2026-05-04"
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

- `var/docs/exports/<scope>/<export_id>-<timestamp>.json`
- `var/docs/exports/<scope>/<export_id>-<timestamp>.jsonl`

The filename timestamp is formatted in the local runtime timezone.
Export metadata `generated_at` remains UTC (`YYYY-MM-DDTHH:MM:SSZ`) for stable provenance.

## Runtime Contract

The script is the shared export engine for both CLI runs and the Studio docs-management endpoint.
It is intentionally source-read-only: the only write it performs is the generated export artifact when `--write` is passed or when the local service calls it in write mode.

Inputs:

- a config id from `assets/studio/data/library_export_configs.json`
- a Docs Viewer scope, currently Library in v1
- explicit document ids or `--all`
- an optional missing-summary override for configs that support it

Outputs:

- a structured JSON report on stdout
- no file in dry-run mode
- one JSON or JSONL export file in write mode

Export artifacts are local working files.
They are ignored by git, may be deleted, and should be reproduced from generated Docs Viewer data plus the selected config and document selection.

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
- extracts deterministic plain-text `source_text` from rendered per-doc payload HTML when a content export config requests it
- preserves paragraphs, headings, list items, and quoted text in `source_text`
- omits code blocks when the selected field mapping includes `omit_code_blocks`
- truncates `source_text` when the selected field mapping includes `truncate_chars`
- handles image/SVG text according to field-level extraction options
- writes JSON envelope exports
- writes JSONL document-row exports
- returns a structured JSON report

The `library-full-document-content` config explicitly includes `parent_id`, `parent_title`, `ancestor_ids`, `ancestor_titles`, `child_ids`, and `child_titles` alongside `source_text`.
Relationship data is therefore controlled by config, not by a separate CLI or Studio UI option.

Not implemented yet:

- batching or chunking

Image handling:

- `image_text_mode: "omit"` omits image markers
- `image_text_mode: "marker"` emits `[image]`
- `image_text_mode: "extract_text"` emits `[image: ...]` when text is available
- image text comes from `img alt`, SVG `title`, SVG `desc`, and SVG `text`
- `empty_image_mode: "marker"` emits `[image]` when no useful text is available
- `empty_image_mode: "omit"` omits empty images

## Commands

Dry-run the parent-child relationships export:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-parent-child-relationships --doc-id library
```

Write the parent-child relationships export:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-parent-child-relationships --doc-id library --write
```

Use all matching docs for whole-corpus relationship review:

```bash
./scripts/docs/docs_export.py --scope library --config-id library-parent-child-relationships --all
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

## Verification

Focused export checks live in:

```bash
tests/python/test_docs_export.py
```

They cover config loading, semantic config validation, selected-document descendant resolution, deterministic JSONL output for a fixed run time, and representative dry-runs for the three v1 Library export configs.
The same check runs in the `docs` profile:

```bash
./scripts/run_checks.py --profile docs
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
- `skipped_summary`
- `warnings`
- `errors`
- `issue_counts`
- `output_written`

`counts` includes:

- `selected`
- `exported`
- `skipped`
- `failed`
- `truncated`

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
- source-text mappings use plain-text conversion rather than raw rendered HTML
- truncating mappings have configured integer limits
- output paths stay under `var/docs/exports/`
- unsupported sources, transforms, target formats, and record shapes are reported before writing

Warnings report non-blocking context:

- expected skipped-doc filters
- ignored `doc_ids` when `select_all` is true
- ignored `missing_summary_only` on unsupported configs
- truncation
- deferred `max_total_chars` enforcement

The static config schema remains documented in [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs).

The Studio page runs the same export engine through the docs-management local endpoint `POST /docs/export`.
That endpoint writes with the same `var/docs/exports/` allowlist and returns the same report shape used by the CLI.
