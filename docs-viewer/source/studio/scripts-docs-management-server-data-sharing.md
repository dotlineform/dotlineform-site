---
doc_id: scripts-docs-management-server-data-sharing
title: Docs Management Service Data Sharing
added_date: 2026-05-19
last_updated: 2026-05-26
parent_id: scripts-docs-management-server
sort_order: 15300
---
# Docs Management Service Data Sharing

`POST <DOCS_VIEWER_BASE_URL>/data-sharing/prepare` expects:

```json
{
  "data_domain": "library",
  "config_id": "library-document-summaries",
  "target_format": "jsonl",
  "doc_ids": ["library"],
  "select_all": false,
  "missing_summary_only": true
}
```

Prepare behavior:

- `data_domain` must resolve the `prepare` operation through `data-sharing/config/adapters.json`; the first implemented domain is `library`
- stub adapters and planned capabilities fail closed before the endpoint runs document-specific package preparation behavior
- `config_id` must resolve in the adapter-declared sharing profile config file
- `target_format` may be `json`, `jsonl`, or omitted; omitted uses the config's default `target.format`
- `doc_ids` is an explicit list used by configs that support explicit selection
- `select_all: true` asks the export engine to select every doc matching the config filters
- `missing_summary_only` may be `true`, `false`, or `null`; unsupported configs ignore `true`
- unsupported config/format combinations return the export engine's structured validation report without writing
- the endpoint dispatches through the Data Sharing documents adapter at `data-sharing/data_sharing/adapters/documents/adapter.py`, which calls Docs Viewer docs-domain helpers in-process
- output paths are validated by the package-preparation engine and must stay under the adapter-declared outbound package root
- normal server mode writes the package file and returns `output_written: true`
- server `--dry-run` mode validates and reports the target path without writing
- failed validation returns the same report shape with `ok: false`, `errors`, `warnings`, `issue_counts`, and `output_written: false`
- logs include data domain, adapter id, scope, config id, counts, target format, dry-run state, issue counts, and whether output was written; logs do not include document body content or package payloads

Runtime role:

- Studio uses this endpoint as the only browser-to-filesystem boundary for Library package preparation
- the endpoint does not accept arbitrary output paths from the browser
- config-defined paths are resolved and allowlisted by the shared export engine
- generated package files are local working artifacts for Studio reporting or manual external use

`GET <DOCS_VIEWER_BASE_URL>/data-sharing/returned-packages` accepts:

```text
?data_domain=library
```

Import file listing behavior:

- `data_domain` must resolve exactly one adapter with `list_returned` capability through `data-sharing/config/adapters.json`
- the first implementation maps `data_domain=library` to the `documents` adapter
- stub adapters and planned capabilities fail closed before the endpoint runs document-specific import behavior
- lists staged `.json` and `.jsonl` files under the adapter-declared staging root
- returns filename, repo-relative path, format, size, and modified time
- does not parse or log file content

`POST <DOCS_VIEWER_BASE_URL>/data-sharing/review` expects:

```json
{
  "data_domain": "library",
  "staged_filename": "library-document-summaries.jsonl"
}
```

Import preview behavior:

- `data_domain` must resolve exactly one adapter with `review` capability
- stub adapters and planned capabilities fail closed before the endpoint runs document-specific preview behavior
- `staged_filename` must resolve inside the adapter-declared staging root
- dispatches through the Data Sharing documents adapter at `data-sharing/data_sharing/adapters/documents/adapter.py`, which parses the staged data file through Docs Viewer docs-domain helpers
- loads current generated docs index and payload state through the shared import engine for the adapter-declared docs scope
- writes Markdown previews under the adapter-declared preview root in normal server mode
- reports planned preview paths without writing when the server runs with `--dry-run`
- returns the same structured report shape as the import CLI, including `counts`, `issues`, `records`, `current_library`, `preview_files`, and `preview_written`
- logs include scope, staged filename, dry-run state, import type, counts, issue counts, and preview paths; logs do not include document body content or staged payload content

Runtime role:

- this endpoint is the browser-to-filesystem boundary for import preview files
- it does not mutate `docs-viewer/source/library/*.md`
- it does not apply summaries, relationship recommendations, or full-content changes to canonical source
- generated preview files are local working artifacts for Studio review
- unconfigured data domains fail closed instead of falling back to document parsing

`POST <DOCS_VIEWER_BASE_URL>/data-sharing/apply` expects for summary updates:

```json
{
  "data_domain": "library",
  "operation": "apply",
  "apply_action": "summary_apply",
  "staged_filename": "library-document-summaries.jsonl",
  "record_indices": [0, 3, 4],
  "confirm": false
}
```

Library import summary-apply behavior:

- `data_domain` and `operation: "apply"` must resolve the `documents` adapter
- `apply_action: "summary_apply"` selects the document summary apply planner
- `staged_filename` must resolve inside the adapter-declared staging root
- `record_indices` must be a non-empty list of selected staged record indexes
- `confirm: false` runs a non-writing preflight and reports selected rows, updates, skipped rows, warnings, errors, and counts
- `confirm: true` applies the selected summary updates when the preflight has no blocking errors
- selected rows map back to parsed staged records by `record_index`, then to current source docs loaded from `docs-viewer/source/library/`
- only selected missing target source docs are blocking errors
- selected rows with missing staged records, missing `doc_id`, duplicate `doc_id`, missing summary text, or unchanged summary text are skipped
- source writes update only `summary`, preserve or initialize `added_date`, and refresh `last_updated`
- successful writes create a timestamped `documents-summary-apply` backup bundle under `var/docs/backups/` before writing source files
- successful writes rebuild targeted Library docs payloads and run targeted docs-search updates for changed ids
- server `--dry-run` mode validates and reports without writing even when `confirm: true`

Runtime role:

- this endpoint is the browser-to-filesystem boundary for summary-only Library import writes
- it does not accept browser-supplied source paths and does not write outside the Library source-doc scope
- it does not apply full content, `parent_id`, `sort_order`, or other relationship changes
- backups use the existing docs-management backup root so Studio backup retention can manage them with the other docs source-write backups

`POST <DOCS_VIEWER_BASE_URL>/data-sharing/apply` expects for hierarchy updates:

```json
{
  "data_domain": "library",
  "operation": "apply",
  "apply_action": "hierarchy_apply",
  "staged_filename": "library-parent-child-relationships.json",
  "record_indices": [0, 3, 4],
  "confirm": false
}
```

Library import hierarchy-apply behavior:

- `data_domain` and `operation: "apply"` must resolve the `documents` adapter
- `apply_action: "hierarchy_apply"` selects the document hierarchy apply planner
- `staged_filename` must resolve inside the adapter-declared staging root
- `record_indices` must be a non-empty list of selected staged record indexes
- `confirm: false` runs a non-writing preflight and reports selected rows, changed rows, unchanged rows, skipped rows, warnings, errors, and counts
- `confirm: true` applies the selected `parent_id` updates when the preflight has no blocking errors
- selected rows map back to parsed staged records by `record_index`, then to current source docs loaded from `docs-viewer/source/library/`
- only selected missing target source docs are blocking errors
- selected rows with missing staged records, missing `doc_id`, duplicate `doc_id`, or self-parent ids are skipped
- unknown non-empty staged `parent_id` values are warnings and are allowed
- source writes update only `parent_id`, preserve current `sort_order`, preserve or initialize `added_date`, and refresh `last_updated`
- successful writes create a timestamped `documents-hierarchy-apply` backup bundle under `var/docs/backups/` before writing source files
- successful writes rebuild targeted Library docs payloads and run targeted docs-search updates for changed ids
- server `--dry-run` mode validates and reports without writing even when `confirm: true`

Runtime role:

- this endpoint is the browser-to-filesystem boundary for parent-id-only Library import writes
- it does not accept browser-supplied source paths and does not write outside the Library source-doc scope
- it does not apply summaries, full content, `sort_order`, or other future relationship fields
- unresolved parent ids are preserved in source but normalized to root-level relationships in generated Library docs data
- backups use the existing docs-management backup root so Studio backup retention can manage them with the other docs source-write backups
