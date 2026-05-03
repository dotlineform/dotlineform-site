---
doc_id: scripts-docs-import
title: "Docs Import"
added_date: "2026-05-03 20:25"
last_updated: "2026-05-03 20:33"
parent_id: scripts
sort_order: 26
---

# Docs Import

Script:

```bash
./scripts/docs/docs_import.py
```

## Scope

`docs_import.py` is the read-only staged data parser for [Library Import v1](/docs/?scope=studio&doc=library-import).

It reads local JSON or JSONL files manually copied under the Library import staging root and returns a structured JSON report.
It does not mutate source Markdown, generated docs payloads, preview files, exports, or config files.

Current input path:

- `var/docs/import-staging/library/<filename>.json`
- `var/docs/import-staging/library/<filename>.jsonl`

Current lookup paths:

- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Current outputs:

- a structured JSON report on stdout
- no files

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
- reports missing `doc_id`, missing title, duplicate `doc_id`, non-object records, invalid JSON/JSONL, unsupported extensions, unsupported shapes, and unsafe staged paths
- reports unknown current `doc_id`, unpublished current records, missing current payloads, missing parents, unpublished parents, and parent records with missing payloads

Not implemented yet:

- Markdown preview rendering
- Studio service endpoints
- Studio Library import page integration
- source apply workflows

## Commands

Parse a staged Library summary export:

```bash
./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl
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
Preview path checks, Markdown rendering behavior, and apply-time freshness checks belong to later Library import tasks.

## Verification

Focused parser checks live in:

```bash
tests/python/test_docs_import.py
```

They cover JSONL rows, JSON envelopes, full-content structural detection, minimal hand-authored rows, unknown metadata preservation, malformed records, current-Library lookup warnings, invalid JSONL blocking, and staged path allowlisting.
The same check runs in the `docs` profile:

```bash
./scripts/run_checks.py --profile docs
```
