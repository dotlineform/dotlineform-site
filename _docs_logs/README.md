# Docs Logs

`_docs_logs/` is the structured source for project change-history entries.

It is separate from `_docs/` by design:

- `_docs/` remains the human-authored documentation source for the Docs Viewer.
- `_docs_logs/entries/*.jsonl` stores durable change-history records optimized for validation, generated indexes, search, and Codex retrieval.
- generated reports and search payloads are projections of the JSONL records, not the source of truth.

## Layout

```text
_docs_logs/
  README.md
  schema.json
  entries/
  generated/
  reports/
```

## Source Records

Canonical records live in `entries/*.jsonl`.
Use one JSON object per line and one change entry per object.

File names should use the month covered by the entries:

- `YYYY-MM.jsonl` for normal monthly files
- `YYYY-MM-and-earlier.jsonl` only for an initial legacy bucket when source history predates the monthly split

Entries are grouped by metadata, not by nested folders.

## Required Intent

Every entry should answer:

- what changed
- when it changed
- which domain or subsystem it belongs to
- why the change matters
- which docs, files, or change request can help trace the decision later

The minimum useful retrieval fields are `title`, `date`, `domains`, `subjects`, `related_docs`, `related_files`, `summary`, `effect`, and `source`.

## Generated Outputs

Files under `generated/` are rebuilt from JSONL source records.
They should update automatically when log entries change, but staging and commits remain manual.

Expected generated projections include:

- date index
- domain index
- related-doc index
- related-file index
- change-request index
- change-history search payload

## Human Views

Human-readable browsing should come from generated reports or compact index views.
Individual log entries are not normal Docs Viewer documents in v1 and should not be added to `_docs/`.

