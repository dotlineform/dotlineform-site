---
doc_id: scripts-docs-import
title: "Docs Import"
added_date: "2026-05-03 20:25"
last_updated: "2026-05-06 12:05"
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

- `var/studio/export-import/library/import-staging/<filename>.json`
- `var/studio/export-import/library/import-staging/<filename>.jsonl`

Current lookup paths:

- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Current outputs:

- a structured JSON report on stdout
- optional Markdown previews under `var/studio/export-import/library/import-preview/`

## Current Capability

Implemented now:

- enforces that parsed files stay under `var/studio/export-import/library/import-staging/`
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
- renders one Markdown-style preview per parsed document
- renders one additional whole-tree Markdown preview file whenever staged relationship metadata is available
- writes previews only under `var/studio/export-import/library/import-preview/`
- supports timestamped document preview filenames based on `doc_id`, duplicate record index fallback, and missing-id fallback
- uses the staged-file timestamp suffix for preview filenames when present, otherwise the current preview-generation time
- supports deterministic relationship-tree preview filenames based on the staged filename plus timestamp suffix
- writes front-matter-like matched-config, staged-only, and preview-metadata sections for human review rather than source parsing
- is callable through docs-management endpoints for staged-file listing and preview generation
- is exposed through the `/studio/library-import/` page for local preview generation
- supports staged data workflow scopes `library`, `catalogue`, and `analytics`; Library remains the only scope with implemented source-write apply actions
- reports missing `doc_id`, missing title, duplicate `doc_id`, non-object records, invalid JSON/JSONL, unsupported extensions, unsupported shapes, and unsafe staged paths
- reports unknown current `doc_id`, unpublished current records, missing current payloads, missing parents, unpublished parents, and parent records with missing payloads

Not implemented yet:

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

Write previews for a future Catalogue staged export shape:

```bash
./scripts/docs/docs_import.py --scope catalogue --file works.jsonl --write-previews
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

The docs-management endpoint returns this same report shape from `POST /docs/import/preview` after adapter dispatch.

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
- staged path outside `var/studio/export-import/library/import-staging/`

Record-level problems are warnings when the file can still be inspected.
Current-Library lookup warnings do not block parsing.
Preview writes are limited to `var/studio/export-import/library/import-preview/`.
Apply-time freshness checks belong to later Library import tasks.

## Verification

Focused parser checks live in:

```bash
tests/python/test_docs_import.py
```

They cover JSONL rows, JSON envelopes, full-content structural detection, minimal hand-authored rows, unknown metadata preservation, malformed records, current-Library lookup warnings, summary preview output, full-content preview output, relationship whole-tree preview output for relationship and non-relationship imports, staged-timestamp preview filenames, dry-run preview reporting, invalid JSONL blocking, and staged/preview path allowlisting.
Service handler checks live in:

```bash
tests/python/test_docs_import_service.py
```

They cover staged-file listing, preview writing, dry-run preview reporting, non-Library scope rejection, the docs-management summary-apply contract for missing target docs, backup creation, skipped rows, and source write output, and the hierarchy-apply contract for missing target docs, backup creation, unknown parent warnings, partial selections, no-write dry runs, and preserved `sort_order`.
The parser and service checks run in the `docs` profile:

```bash
./scripts/run_checks.py --profile docs
```

The Studio page shell, unavailable-service route behavior, mocked preview flow, mocked summary-apply confirmation flow, and mocked hierarchy-apply confirmation flow are covered by `tests/smoke/library_import.py`.
That smoke check runs in the `studio-smoke` profile after a temporary Jekyll build:

```bash
./scripts/run_checks.py --profile studio-smoke
```
