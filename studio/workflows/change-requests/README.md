# Docs Logs

`studio/workflows/change-requests/` is the structured source for project change-history entries.

It is separate from Docs Viewer source Markdown by design:

- `studio/docs-viewer/source/studio/` remains the Studio documentation source for the Docs Viewer.
- `studio/workflows/change-requests/logs/entries/*.json` stores durable per-entry change-history records optimized for validation, generated indexes, search, and Codex retrieval.
- generated reports and search payloads are projections of the JSON records, not the source of truth.

## Layout

```text
studio/workflows/change-requests/
  README.md
  schema.json
  logs/
    entries/
  generated/
  reports/
```

## Source Records

Canonical records live in `entries/*.json`.
Use one JSON object per file and one change entry per object.

File names must match the stable entry id:

- `change-YYYY-MM-DD-entry-slug.json`

Entries are grouped by metadata, not by nested folders.
The retired monthly `*.jsonl` files were only an intermediate migration format.

## Required Intent

Every entry should answer:

- what changed
- when it changed
- which domain or subsystem it belongs to
- why the change matters
- which docs, files, or change request can help trace the decision later

The minimum useful retrieval fields are `title`, `date`, `domains`, `subjects`, `related_docs`, `related_files`, `summary`, `effect`, and `source`.

## Authoring Workflow

Structured log entries are the durable implementation history.
They do not replace change requests, implementation docs, or generated activity logs.

Create log entries for meaningful completed work, especially when the change affects:

- user workflow
- Studio or public UI behavior
- build flow, validation, or generated data
- search behavior, schema, ranking, or index shape
- local services, scripts, or write paths
- data models, config contracts, or source ownership
- development workflow or repo conventions

Small typo fixes, narrow copy edits, and purely mechanical cleanup usually do not need log entries unless they explain an important decision.

### Completed Change Request Path

When work was driven by a change request:

1. Complete the implementation and targeted verification.
2. Update the change request task/status sections.
3. Create one or more JSON log records for the completed implementation work.
4. Set `change_request_doc_id` to the request doc id on each related log record.
5. Include related docs and files that would help Codex trace the decision later.
6. Add references from the completed request back to the created log entry ids when the request has a closure/cleanup task for that.
7. Move or mark the request according to the current request archive practice.
8. Rebuild generated log indexes/search payloads after the entries are written.

One change request may produce more than one log entry when the implementation landed as distinct meaningful changes.
Do not force every task-list item into its own entry.

### Direct Change Path

When meaningful work was not backed by a change request:

1. Use the current implementation context to identify the change date, title, domains, subjects, related docs, and related files.
2. Create a JSON log record without `change_request_doc_id`.
3. Keep `summary` factual and short.
4. Use `effect` to explain why the change matters.
5. Set `source.file` to the best available trace source, such as the current implementation summary, old changelog source, or follow-up workflow artifact.
6. Rebuild generated log indexes/search payloads after the entry is written.

Direct entries should still be structured enough for search and Codex retrieval.
They do not need to read like standalone release notes.

### Record Style

Keep records compact:

- use lower-case hyphenated domain ids such as `docs-viewer`, `search`, `catalogue`, `library`, `studio-ui`, `build`, `scripts`, `data-models`, or `workflow`
- use `subjects` for more specific concepts, not folder structure
- keep `summary` to one short paragraph
- keep `effect` focused on behavior, maintenance impact, or decision context
- prefer repo-relative paths in `related_files`
- prefer Docs Viewer doc ids in `related_docs`
- preserve old changelog prose in `body` only when it cannot be cleanly split into structured fields

### Current Implementation State

The source model, schema, authoring workflow, entry helper, legacy migration, generated indexes, and migration review report exist.
The report UI and compact human-facing archive replacement are still part of the change-log entry model implementation.

## Helper Script

Use `studio/workflows/change-requests/services/docs_logs/log_entry.py` to preview or write one log entry.
The script previews by default; it writes only with `--write`.

Preview a direct entry:

```bash
$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/log_entry.py \
  --title "Added Example Workflow" \
  --summary "Added a short example workflow for structured log entries." \
  --domain workflow \
  --subject docs-logs \
  --related-doc development-workflow \
  --related-file studio/docs-viewer/source/studio/development-workflow.md \
  --source-file studio/docs-viewer/source/studio/development-workflow.md
```

Seed from a change request:

```bash
$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/log_entry.py \
  --from-change-request site-request-change-log-entry-model \
  --title "Added Docs Log Entry Helper" \
  --summary "Added a helper for previewing and writing structured docs-log entries." \
  --domain workflow \
  --domain docs-viewer \
  --related-file studio/workflows/change-requests/services/docs_logs/log_entry.py
```

Create the entry file after reviewing the preview:

```bash
$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/log_entry.py ... --write
```

Add `--update-change-request` with `--write` when the completed request has a closure task that should reference the created log entry id.

The helper validates required fields and common id/list formats with standard-library checks.
After writes, the helper runs `studio/workflows/change-requests/services/docs_logs/build_indexes.py --write` unless `--no-rebuild-generated` is passed.

## Migration Script

Use `studio/workflows/change-requests/services/docs_logs/migrate_legacy_logs.py` to parse legacy Markdown change logs into per-entry JSON records.
The script previews by default and writes only with `--write`.

Preview the migration:

```bash
$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/migrate_legacy_logs.py
```

Write migration records and the review report:

```bash
$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/migrate_legacy_logs.py --write
```

The v1 migration created per-entry records from the site and Search change logs.
Review diagnostics live in `studio/workflows/change-requests/reports/migration-review.json`.

## Generated Indexes

Use `studio/workflows/change-requests/services/docs_logs/build_indexes.py` to rebuild generated projections from JSON source records.
The script previews by default and writes only with `--write`.

```bash
$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/build_indexes.py --write
```

## Generated Outputs

Files under `generated/` are rebuilt from JSON source records.
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
Individual log entries are not normal Docs Viewer documents in v1 and should not be added to `studio/docs-viewer/source/studio/`.
