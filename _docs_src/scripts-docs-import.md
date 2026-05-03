---
doc_id: scripts-docs-import
title: "Docs Import"
added_date: "2026-05-03 20:25"
last_updated: "2026-05-03 21:25"
parent_id: scripts
sort_order: 26
---

# Docs Import

Script:

```bash
./scripts/docs/docs_import.py
```

## Scope

`docs_import.py` is the staged data parser and Markdown preview renderer for [Library Import v1](/docs/?scope=studio&doc=library-import).

It reads local JSON or JSONL files manually copied under the Library import staging root and returns a structured JSON report.
It does not mutate source Markdown, generated docs payloads, exports, or config files.
When `--write-previews` is passed, it writes Markdown previews under the Library import preview root.
The same engine is used by the docs-management local service for Studio integration.

Current input path:

- `var/docs/import-staging/library/<filename>.json`
- `var/docs/import-staging/library/<filename>.jsonl`

Current lookup paths:

- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Current outputs:

- a structured JSON report on stdout
- optional Markdown previews under `var/docs/import-preview/library/`

## Current Capability

Implemented now:

- enforces that parsed files stay under `var/docs/import-staging/library/`
- reads `.json` and `.jsonl`
- parses JSON envelope exports with a `documents` array
- parses JSON arrays of document-like records
- parses JSONL document-row exports
- detects the three v1 Library export families when export metadata is present
- falls back to structural detection for relationship, summary, full-content, and minimal document records
- normalizes `doc_id`, title, parent id, headings, relationship lists, and known metadata into a stable record shape
- preserves unknown file-level metadata and unknown record-level metadata in the report
- loads the current generated Library docs index and generated payload filenames
- annotates each normalized record with current Library existence, publication, viewability, payload, and parent state
- renders summary and full-content imports as one Markdown preview per parsed document
- renders relationship imports as one whole-tree Markdown preview file
- writes previews only under `var/docs/import-preview/library/`
- supports deterministic preview filenames based on `doc_id`, duplicate record index fallback, or staged relationship filename
- is callable through docs-management endpoints for staged-file listing and preview generation
- reports missing `doc_id`, missing title, duplicate `doc_id`, non-object records, invalid JSON/JSONL, unsupported extensions, unsupported shapes, and unsafe staged paths
- reports unknown current `doc_id`, unpublished current records, missing current payloads, missing parents, unpublished parents, and parent records with missing payloads

Not implemented yet:

- Studio Library import page integration
- source apply workflows

## Commands

Parse a staged Library summary export:

```bash
./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl
```

Write Markdown previews for a staged Library summary export:

```bash
./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl --write-previews
```

Parse a staged Library relationships export and omit normalized records from the printed report:

```bash
./scripts/docs/docs_import.py --scope library --file library-parent-child-relationships.json --no-records
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
- `unknown_file_metadata`
- `current_library`
- `preview_files`
- `preview_written`

The docs-management endpoint returns this same report shape from `POST /docs/library-import/preview`.

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

## Validation Boundary

This parser is intentionally not an apply validator.

It blocks only concerns that prevent useful parsing:

- unsupported file extension
- unreadable or missing staged file
- invalid JSON or JSONL
- staged path outside `var/docs/import-staging/library/`

Record-level problems are warnings when the file can still be inspected.
Current-Library lookup warnings do not block parsing.
Preview writes are limited to `var/docs/import-preview/library/`.
Apply-time freshness checks belong to later Library import tasks.

## Verification

Focused parser checks live in:

```bash
tests/python/test_docs_import.py
```

They cover JSONL rows, JSON envelopes, full-content structural detection, minimal hand-authored rows, unknown metadata preservation, malformed records, current-Library lookup warnings, summary preview output, full-content preview output, relationship whole-tree preview output, dry-run preview reporting, invalid JSONL blocking, and staged/preview path allowlisting.
Service handler checks live in:

```bash
tests/python/test_docs_import_service.py
```

They cover staged-file listing, preview writing, dry-run preview reporting, and non-Library scope rejection.
The same check runs in the `docs` profile:

```bash
./scripts/run_checks.py --profile docs
```
