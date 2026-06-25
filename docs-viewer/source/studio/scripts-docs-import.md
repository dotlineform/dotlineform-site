---
doc_id: scripts-docs-import
title: Documents Returned Package Script
added_date: "2026-05-03 20:25"
last_updated: 2026-06-06
parent_id: docs-viewer
---
# Documents Returned Package Script

Script:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py
```

## Scope

`docs_import.py` is the staged returned-package parser and Markdown review renderer used by the documents Data Sharing adapter.

It reads local JSON or JSONL files manually copied under the Library returned-package staging root and returns a structured JSON report.
It does not mutate source Markdown, generated docs payloads, share packages, or config files.
When `--write-previews` is passed, it writes Markdown review artifacts under the Library review output root.
The same engine is used by the documents adapter when `/analytics/data-sharing/review/` calls `POST /analytics/api/data-sharing/review`.

Current input path:

- `var/analytics/data-sharing/import-staging/<filename>.json`
- `var/analytics/data-sharing/import-staging/<filename>.jsonl`
- optional `var/analytics/data-sharing/import-staging/<stem>.meta.json` sidecar for package metadata
- optional `var/analytics/data-sharing/import-staging/<stem>.context.json` sidecar for external task/schema context

Current lookup path:

- `docs-viewer/source/library/`, resolved through the configured Docs Viewer scope and `docs_data_sharing/source_metadata.py`

Current outputs:

- a structured JSON report on stdout
- optional Markdown review artifacts under `var/analytics/data-sharing/import-preview/`

## Current Capability

Implemented now:

- enforces that parsed files stay under `var/analytics/data-sharing/import-staging/`
- reads `.json` and `.jsonl`
- parses JSON package envelopes with a `documents` array
- parses JSON arrays of document-like records
- parses JSONL document-row packages
- reads sibling `.meta.json` sidecars for package metadata
- excludes `.meta.json` and `.context.json` sidecars from staged package listings
- detects the three v1 Library package families when package metadata is present
- falls back to structural detection for relationship, summary, full-content, and minimal document records
- normalizes `doc_id`, title, parent id, headings, relationship lists, and known metadata into a stable record shape
- preserves unknown file-level metadata and unknown record-level metadata in the report
- loads current Library source metadata through Docs Viewer source parsing/rendering helpers
- annotates each normalized record with current Library existence, viewability, source renderability, current summary, and parent source state
- renders one Markdown-style review artifact per parsed document
- renders one additional whole-tree Markdown review artifact whenever staged relationship metadata is available
- writes review artifacts only under `var/analytics/data-sharing/import-preview/`
- supports timestamped document review filenames based on `doc_id`, duplicate record index fallback, and missing-id fallback
- uses the staged-file timestamp suffix for review filenames when present, otherwise the current review-generation time
- supports deterministic relationship-tree review filenames based on the staged filename plus timestamp suffix
- writes front-matter-like matched-config, staged-only, and preview-metadata sections for human review rather than source parsing
- is callable through the documents Data Sharing adapter for returned-package listing and review generation
- is exposed through the `/analytics/data-sharing/review/` page for local returned-package review
- reports missing `doc_id`, missing title, duplicate `doc_id`, non-object records, invalid JSON/JSONL, unsupported extensions, unsupported shapes, and unsafe staged paths
- reports unknown current `doc_id`, unreadable current source metadata, unrenderable current source records, missing parents, and parent records with unrenderable source

## Commands

Parse a staged Library summary package:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py --scope library --file library-document-summaries.jsonl
```

Write Markdown review artifacts for a staged Library summary package:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py --scope library --file library-document-summaries.jsonl --write-previews
```

Parse a staged Library relationships package and omit normalized records from the printed report:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py --scope library --file library-parent-child-relationships.json --no-records
```

## Report Shape

The script prints a JSON report with:

- `ok`
- `scope`
- `input_file`
- `input_format`
- `detected_import_type`
- `source_export_id`
- `source_scope`
- `generated_at`
- `counts`
- `issues`
- `records`
- `source_metadata`
- `source_metadata_file`
- `unknown_file_metadata`
- `current_library`
- `preview_files`
- `preview_written`

The Data Sharing review endpoint returns this same report shape from `POST /analytics/api/data-sharing/review` after documents-adapter dispatch.

`current_library` reports source metadata status with `source_loaded`, `source_root`, `doc_count`, and `renderable_count`.
Per-record `current_library` values report `exists`, `viewable`, `source_exists`, `source_renderable`, `current_summary`, `parent_exists`, `parent_source_exists`, and `parent_source_renderable`.

`counts` includes:

- `records`
- `parsed_records`
- `malformed_records`
- `warnings`
- `errors`

The command exits with:

- `0` when parsing succeeds without file-level blockers
- `1` for command/runtime failures
- `2` when parsing returns a structured report with errors

## Apply Follow-Through

Returned-package apply behavior is owned by the documents Data Sharing adapter and source service rather than by `docs_import.py` itself.

When an apply action writes Library Markdown source:

- the write/rebuild helper rebuilds targeted same-scope Docs Viewer payloads after the source write succeeds
- docs search is updated for the affected ids when the adapter can provide a targeted set
- the apply response includes `rebuild.steps`, `rebuild.docs`, `rebuild.search`, and `rebuild.diagnostics`
- `rebuild.docs` reports whether docs payloads used targeted mode or a full fallback
- `rebuild.diagnostics.docs` comes from the docs builder diagnostics line
- `rebuild.diagnostics.search` describes the full or targeted search update
- activity rows are attached by the Docs Viewer service after successful apply handling

The parser CLI remains read-only unless `--write-previews` is passed, and preview writes do not trigger generated docs or docs-search rebuilds.

## Validation Boundary

This parser is intentionally not an apply validator.

It blocks only concerns that prevent useful parsing:

- unsupported file extension
- unreadable or missing staged file
- invalid JSON or JSONL
- staged path outside `var/analytics/data-sharing/import-staging/`

Record-level problems are warnings when the file can still be inspected.
Current-Library lookup warnings do not block parsing.
Review writes are limited to `var/analytics/data-sharing/import-preview/`.
Apply-time freshness checks belong to the documents adapter apply actions.

## Verification

Focused parser checks live in:

```bash
docs-viewer/tests/python/test_docs_import.py
```

They cover JSONL rows, JSON envelopes, package metadata sidecars, full-content structural detection, minimal hand-authored rows, unknown metadata preservation, malformed records, current-Library lookup warnings, summary review output, full-content review output, relationship whole-tree review output for relationship and non-relationship packages, staged-timestamp review filenames, dry-run review reporting, invalid JSONL blocking, and staging/review path allowlisting.
Service handler checks live in:

```bash
docs-viewer/tests/python/test_docs_import_service.py
```

They cover documents adapter returned-package listing, review writing, dry-run review reporting, non-Library domain rejection, the summary-apply contract for missing target docs, skipped rows, source write output, and rebuild diagnostics shape, and the hierarchy-apply contract for missing target docs, unknown parent warnings, partial selections, no-write dry runs, retired `sort_order` removal, and rebuild diagnostics shape.
The parser and service checks run in the `docs` profile:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs
```

The Analytics Data Sharing route shells are covered by `analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py`, and returned-package API behavior is covered by the focused Python service tests above.
Those checks run through the `analytics-smoke` and `docs` profiles:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile analytics-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs
```
