---
doc_id: scripts-docs-import
title: Documents Returned Package Script
added_date: "2026-05-03 20:25"
last_updated: "2026-05-19 14:30"
parent_id: docs-viewer
sort_order: 10000
---
# Documents Returned Package Script

Script:

```bash
./scripts/docs/docs_import.py
```

## Scope

`docs_import.py` is the staged returned-package parser and Markdown review renderer used by the documents Data Sharing adapter.

It reads local JSON or JSONL files manually copied under the Library returned-package staging root and returns a structured JSON report.
It does not mutate source Markdown, generated docs payloads, share packages, or config files.
When `--write-previews` is passed, it writes Markdown review artifacts under the Library review output root.
The same engine is used by the documents adapter when `/studio/data-sharing/review/` calls `POST /data-sharing/review`.

Current input path:

- `var/studio/data-sharing/library/import-staging/<filename>.json`
- `var/studio/data-sharing/library/import-staging/<filename>.jsonl`

Current lookup paths:

- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Current outputs:

- a structured JSON report on stdout
- optional Markdown review artifacts under `var/studio/data-sharing/library/import-preview/`

## Current Capability

Implemented now:

- enforces that parsed files stay under `var/studio/data-sharing/library/import-staging/`
- reads `.json` and `.jsonl`
- parses JSON package envelopes with a `documents` array
- parses JSON arrays of document-like records
- parses JSONL document-row packages
- detects the three v1 Library package families when package metadata is present
- falls back to structural detection for relationship, summary, full-content, and minimal document records
- normalizes `doc_id`, title, parent id, headings, relationship lists, and known metadata into a stable record shape
- preserves unknown file-level metadata and unknown record-level metadata in the report
- loads the current generated Library docs index and generated payload filenames
- annotates each normalized record with current Library existence, publication, viewability, payload, and parent state
- renders one Markdown-style review artifact per parsed document
- renders one additional whole-tree Markdown review artifact whenever staged relationship metadata is available
- writes review artifacts only under `var/studio/data-sharing/library/import-preview/`
- supports timestamped document review filenames based on `doc_id`, duplicate record index fallback, and missing-id fallback
- uses the staged-file timestamp suffix for review filenames when present, otherwise the current review-generation time
- supports deterministic relationship-tree review filenames based on the staged filename plus timestamp suffix
- writes front-matter-like matched-config, staged-only, and preview-metadata sections for human review rather than source parsing
- is callable through the documents Data Sharing adapter for returned-package listing and review generation
- is exposed through the `/studio/data-sharing/review/` page for local returned-package review
- reports missing `doc_id`, missing title, duplicate `doc_id`, non-object records, invalid JSON/JSONL, unsupported extensions, unsupported shapes, and unsafe staged paths
- reports unknown current `doc_id`, unpublished current records, missing current payloads, missing parents, unpublished parents, and parent records with missing payloads

## Commands

Parse a staged Library summary package:

```bash
./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl
```

Write Markdown review artifacts for a staged Library summary package:

```bash
./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl --write-previews
```

Parse a staged Library relationships package and omit normalized records from the printed report:

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

The Data Sharing review endpoint returns this same report shape from `POST /data-sharing/review` after documents-adapter dispatch.

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

- the source service creates the configured backup before writing changed source docs
- the write/rebuild helper rebuilds targeted same-scope Docs Viewer payloads after the source write succeeds
- docs search is updated for the affected ids when the adapter can provide a targeted set
- the apply response includes `rebuild.steps`, `rebuild.docs`, `rebuild.search`, and `rebuild.diagnostics`
- `rebuild.docs` reports whether docs payloads used targeted mode or a full fallback
- `rebuild.diagnostics.docs` comes from the docs builder diagnostics line
- `rebuild.diagnostics.search` describes the full or targeted search update
- activity rows are attached by the docs-management server after successful apply handling

The parser CLI remains read-only unless `--write-previews` is passed, and preview writes do not trigger generated docs or docs-search rebuilds.

## Validation Boundary

This parser is intentionally not an apply validator.

It blocks only concerns that prevent useful parsing:

- unsupported file extension
- unreadable or missing staged file
- invalid JSON or JSONL
- staged path outside `var/studio/data-sharing/library/import-staging/`

Record-level problems are warnings when the file can still be inspected.
Current-Library lookup warnings do not block parsing.
Review writes are limited to `var/studio/data-sharing/library/import-preview/`.
Apply-time freshness checks belong to the documents adapter apply actions.

## Verification

Focused parser checks live in:

```bash
tests/python/test_docs_import.py
```

They cover JSONL rows, JSON envelopes, full-content structural detection, minimal hand-authored rows, unknown metadata preservation, malformed records, current-Library lookup warnings, summary review output, full-content review output, relationship whole-tree review output for relationship and non-relationship packages, staged-timestamp review filenames, dry-run review reporting, invalid JSONL blocking, and staging/review path allowlisting.
Service handler checks live in:

```bash
tests/python/test_docs_import_service.py
```

They cover documents adapter returned-package listing, review writing, dry-run review reporting, non-Library domain rejection, the summary-apply contract for missing target docs, backup creation, skipped rows, source write output, and rebuild diagnostics shape, and the hierarchy-apply contract for missing target docs, backup creation, unknown parent warnings, partial selections, no-write dry runs, preserved `sort_order`, and rebuild diagnostics shape.
The parser and service checks run in the `docs` profile:

```bash
./scripts/run_checks.py --profile docs
```

The Studio page shell, unavailable-service route behavior, mocked preview flow, mocked summary-apply confirmation flow, and mocked hierarchy-apply confirmation flow are covered by `tests/smoke/data_sharing_review.py`.
That smoke check runs in the `studio-smoke` profile after a temporary Jekyll build:

```bash
./scripts/run_checks.py --profile studio-smoke
```
