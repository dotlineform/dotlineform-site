---
doc_id: scripts-docs-export
title: Documents Package Preparation Script
added_date: "2026-05-03 15:05"
last_updated: "2026-05-19"
parent_id: docs-viewer
sort_order: 2000
---
# Documents Package Preparation Script

Script:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py
```

## Scope

`docs_export.py` is the read-only package-preparation engine used by the documents Data Sharing adapter.

It reads generated Docs Viewer artifacts and source-controlled Library sharing profiles, then writes an ephemeral share package under `var/studio/data-sharing/<scope>/exports/`.
It does not mutate source Markdown, generated docs payloads, or config files.

Current input paths:

- `assets/studio/data/library_export_configs.json`
- `assets/data/docs/scopes/<scope>/index.json`
- `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`

Current output pattern:

- `var/studio/data-sharing/<scope>/exports/<export_id>-<timestamp>.json`
- `var/studio/data-sharing/<scope>/exports/<export_id>-<timestamp>.jsonl`

The filename timestamp is formatted in the local runtime timezone.
Package metadata `generated_at` remains UTC (`YYYY-MM-DDTHH:MM:SSZ`) for stable provenance.

## Runtime Contract

The script is the documents-adapter package engine for both CLI runs and the Studio Data Sharing `prepare` endpoint.
It is intentionally source-read-only: the only write it performs is the generated package artifact when `--write` is passed or when the local service calls it in write mode.

Inputs:

- a sharing profile id from `assets/studio/data/library_export_configs.json`
- a Docs Viewer scope, currently Library in v1
- explicit document ids or `--all`
- an optional `--format json|jsonl` override when the selected profile declares that format in `target.supported_formats`
- an optional missing-summary override for profiles that support it

Outputs:

- a structured JSON report on stdout
- no file in dry-run mode
- one JSON or JSONL share package in write mode

Export preparation is read-only with respect to docs source and generated docs/search payloads.
It does not run `build_docs.rb`, does not run `build_search.rb`, and does not include rebuild diagnostics in its report.

Share packages are local working files.
They are ignored by git, may be deleted, and should be reproduced from generated Docs Viewer data plus the selected profile and document selection.

## Current Capability

Implemented now:

- loads a selected sharing profile by `id`
- validates that the profile is enabled for the requested scope
- loads generated Docs Viewer index data for the requested scope
- resolves selected `doc_id` values
- supports all-matching profiles
- expands selected descendants when the profile requests it
- excludes archived docs when the profile requests it
- excludes unpublished docs when the profile requests it
- includes generated but non-viewable docs when the profile requests it
- supports missing-summary filtering for profiles that allow it
- maps supported document fields into configured output paths
- computes parent, ancestor, and child relationship fields from the generated index
- extracts heading lists from rendered per-doc payload HTML
- extracts deterministic plain-text `source_text` from rendered per-doc payload HTML when a content package profile requests it
- preserves paragraphs, headings, list items, and quoted text in `source_text`
- omits code blocks when the selected field mapping includes `omit_code_blocks`
- truncates `source_text` when the selected field mapping includes `truncate_chars`
- handles image/SVG text according to field-level extraction options
- writes JSON envelope exports
- writes JSONL document-row exports
- writes JSON arrays for document-row configs when `json` is selected
- returns a structured JSON report

The `library-full-document-content` sharing profile explicitly includes `parent_id`, `parent_title`, `ancestor_ids`, `ancestor_titles`, `child_ids`, and `child_titles` alongside `source_text`.
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
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-parent-child-relationships --doc-id library
```

Write the parent-child relationships export:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-parent-child-relationships --doc-id library --write
```

Use all matching docs for whole-corpus relationship review:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-parent-child-relationships --all
```

Prepare explicit documents for profiles that require selected ids:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-document-summaries --doc-id library
```

Use all matching docs for an explicit-selection config:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-document-summaries --all
```

Disable a summary config's default missing-summary-only filter:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-document-summaries --all --include-summary-complete
```

Write a document-row export as JSON instead of its JSONL default when the config supports both:

```bash
$HOME/miniconda3/bin/python3 studio/docs-viewer/services/docs_export.py --scope library --config-id library-document-summaries --all --format json --write
```

## Verification

Focused package-preparation checks live in:

```bash
studio/tests/python/test_docs_export.py
```

They cover config loading, semantic config validation, selected-document descendant resolution, deterministic JSONL output for a fixed run time, JSON format overrides for document-row packages, unsupported format overrides, and representative dry-runs for the three v1 Library sharing profiles.
The same check runs in the `docs` profile:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs
```

## Report Shape

The script prints a JSON report with:

- `ok`
- `dry_run`
- `config_id`
- `scope`
- `target_format`
- `supported_target_formats`
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

- `0` when the package is valid
- `1` for command/runtime failures
- `2` when the sharing profile and selection load but validation errors prevent output

## Validation Boundary

The engine validates runtime concerns that the static config schema cannot know:

- selected config id exists
- sharing profile is enabled for the requested scope
- selected docs exist
- archive and publication filters are applied
- required mapped fields are present
- source-text mappings use plain-text conversion rather than raw rendered HTML
- truncating mappings have configured integer limits
- output paths stay under `var/studio/data-sharing/` by default
- unsupported sources, transforms, target formats, and record shapes are reported before writing

Warnings report non-blocking context:

- expected skipped-doc filters
- ignored `doc_ids` when `select_all` is true
- ignored `missing_summary_only` on unsupported profiles
- truncation
- deferred `max_total_chars` enforcement

The static sharing profile schema remains documented in [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs).

The Studio page runs the same documents package engine through the configured Docs Viewer service endpoint `POST <DOCS_VIEWER_BASE_URL>/data-sharing/prepare`.
The local service first resolves `data_domain` and `operation` through `assets/studio/data/data_sharing_adapters.json`, then dispatches to the documents adapter, writes under the adapter-declared export root, and returns the same report shape used by the CLI.
The response is annotated with `data_domain`, `adapter_id`, and service summary text, but it does not include `rebuild` or `rebuild.diagnostics` because package preparation does not mutate source docs or generated docs/search payloads.
