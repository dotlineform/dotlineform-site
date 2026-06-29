---
doc_id: scripts-docs-export
title: Documents Package Preparation Script
added_date: "2026-05-03 15:05"
last_updated: 2026-06-29
parent_id: docs-viewer
---
# Documents Package Preparation Script

Script:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_export.py
```

## Scope

`docs_export.py` is the read-only package-preparation engine used by the documents Data Sharing adapter.

It reads Docs Viewer source context and source-controlled document sharing profiles, then writes an ephemeral share package under `var/analytics/data-sharing/exports/`.
It does not mutate source Markdown, generated docs payloads, or config files.

Current input paths:

- `data-sharing/adapters/documents/config/prepare-profiles.json`
- `docs-viewer/config/scopes/docs_scopes.json`
- `docs-viewer/source/<scope>/*.md` or the configured source root for that scope

Current output pattern:

- `var/analytics/data-sharing/exports/<data_domain>-<profile_id>-<timestamp>.json`
- `var/analytics/data-sharing/exports/<data_domain>-<profile_id>-<timestamp>.jsonl`
- `var/analytics/data-sharing/exports/<data_domain>-<profile_id>-<timestamp>.context.json` for external task and schema context
- `var/analytics/data-sharing/meta/<export_id>.meta.json` for internal export provenance and review routing

The filename timestamp is formatted in the local runtime timezone.
Package metadata `generated_at` remains UTC (`YYYY-MM-DDTHH:MM:SSZ`) for stable provenance.
The `export_id` is derived from that UTC timestamp as `ds_YYYYMMDDTHHMMSSZ`.
The internal `.meta.json` file stores source scope, profile, domain, and adapter routing data; external package payloads carry `export_id`, but external filenames use profile id and timestamp.
The metadata and `export_id` contract is documented in [Data Sharing Export Metadata](/docs/?scope=studio&doc=data-sharing-export-metadata).

## Runtime Contract

The script is the documents-adapter package engine for both CLI runs and the Analytics Data Sharing `prepare` endpoint.
It is intentionally source-read-only: the only writes it performs are generated package artifacts when `--write` is passed or when the local service calls it in write mode.

Inputs:

- a sharing profile id from `data-sharing/adapters/documents/config/prepare-profiles.json`
- a Docs Viewer scope, currently Library in v1
- explicit document ids or `--all`
- an optional `--format json|jsonl` override when the selected profile declares that format in `target.supported_formats`
- an optional `--content-format markdown|plain_text` override when the selected profile declares those values in `content_format.supported_formats`

Outputs:

- a structured JSON report on stdout
- no file in dry-run mode
- one JSON or JSONL external share package in write mode
- one internal `.meta.json` metadata file under `var/analytics/data-sharing/meta/`
- one sibling `.context.json` external task/schema sidecar

Export preparation is read-only with respect to docs source and generated docs/search payloads.
It does not run `build_docs.py`, does not run `build_search.py`, and does not include rebuild diagnostics in its report.

Share packages are local working files.
They are ignored by git, may be deleted, and should be reproduced from Docs Viewer source context plus the selected profile and document selection.

## Current Capability

Implemented now:

- loads a selected sharing profile by `id`
- validates that the profile is enabled for the requested scope
- loads Docs Viewer source context for the requested scope
- resolves selected `doc_id` values
- supports all-matching profiles
- exports the exact selected document ids supplied by the caller
- includes source docs marked non-viewable when the profile requests it
- maps supported document fields into configured output paths
- computes parent, ancestor, and child relationship fields from source records
- extracts heading lists from source-rendered HTML
- extracts deterministic plain-text `content` from source-rendered HTML when a content package profile requests it
- preserves paragraphs, headings, list items, and quoted text in `content`
- omits code blocks when the selected field mapping includes `omit_code_blocks`
- truncates `content` when the selected field mapping includes `truncate_chars`
- handles image/SVG text according to field-level extraction options
- writes JSONL document-row exports with a first-line `data_sharing_header` record containing `export_id`
- writes JSON document-row overrides as objects containing top-level `schema_version`, `export_id`, and `records`
- writes internal `.meta.json` files under `var/analytics/data-sharing/meta/` and external `.context.json` sidecars
- derives external task wording and field descriptions from profile `external_context`
- keeps source timestamp provenance in internal `.meta.json` rather than in external records
- returns a structured JSON report

The `document-content` sharing profile explicitly includes `parent_id`, `parent_title`, `ancestors`, and `children` alongside `current_summary`, `summary`, and `content`.
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

Prepare explicit documents for profiles that require selected ids:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_export.py --scope library --config-id document-content --doc-id library
```

Use all matching docs for an explicit-selection config:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_export.py --scope library --config-id document-content --all
```

Write a document-row export as JSON instead of its JSONL default when the config supports both:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_export.py --scope library --config-id document-content --all --format json --write
```

Write `document-content` with plain-text body content instead of the profile's Markdown default:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_export.py --scope library --config-id document-content --all --content-format plain_text --write
```

## Verification

Focused package-preparation checks live in:

```bash
docs-viewer/tests/python/test_docs_export.py
```

They cover config loading, semantic config validation, exact selected-document resolution, deterministic JSONL output, metadata/context sidecars, JSON format overrides for document-row packages, unsupported format overrides, and representative dry-runs for the v1 document sharing profiles.
The same check runs in the `docs` profile:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs
```

## Report Shape

The script prints a JSON report with:

- `ok`
- `dry_run`
- `export_id`
- `config_id`
- `scope`
- `target_format`
- `supported_target_formats`
- `output_file`
- `metadata_file`
- `context_file`
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
- viewability filters are applied
- required mapped fields are present
- source-text mappings use plain-text conversion rather than raw rendered HTML
- truncating mappings have configured integer limits
- output paths stay under `var/analytics/data-sharing/` by default
- unsupported sources, transforms, target formats, and record shapes are reported before writing

Warnings report non-blocking context:

- expected skipped-doc filters
- ignored `doc_ids` when `select_all` is true
- ignored `missing_summary_only` on unsupported profiles
- truncation
- deferred `max_total_chars` enforcement

The documents prepare profile contract remains documented in [Documents Prepare Profiles](/docs/?scope=studio&doc=data-sharing-documents-prepare-profiles).

The Analytics Data Sharing page runs the same documents package engine through the Analytics-owned same-origin endpoint `POST /analytics/api/data-sharing/prepare`.
The local service first resolves `data_domain` and `operation` through `data-sharing/config/adapters.json`, then dispatches to the documents adapter, writes under the adapter-declared export root, and returns the same report shape used by the CLI.
The response is annotated with `data_domain`, `adapter_id`, and service summary text, but it does not include `rebuild` or `rebuild.diagnostics` because package preparation does not mutate source docs or generated docs/search payloads.

## Source Context Boundary

Document export uses Docs Viewer-owned Data Sharing source helpers:

- `docs-viewer/services/docs_data_sharing/source_context.py` loads scope config, source Markdown, source records, parent-child indexes, and render cache.
- `docs-viewer/services/docs_data_sharing/source_records.py` owns the stable document record projection exposed to Data Sharing package preparation.
- `docs-viewer/services/docs_data_sharing/rendered_content.py` owns source-rendered HTML, headings, and plain-text extraction.

Generated Docs Viewer publication artifacts are not metadata inputs for this script.
Do not replace source context reads with public flat docs indexes, public tree/search/recently-added payloads, generated by-id payloads, manage/local generated indexes, or generated metadata JSON.
