---
doc_id: scripts-docs-management-endpoints-source-mutations
title: Source Mutation Endpoints
added_date: 2026-06-07
last_updated: 2026-07-13
parent_id: scripts-docs-management-endpoints
---
# Docs Viewer Source Mutation Endpoints

Source mutation endpoints rewrite source Markdown front matter or delete source Markdown files. They do not move files on disk except when deleting a confirmed source doc.

Returned source paths are repo-relative for repo-backed scopes and relative to the fixed external Docs Viewer root for external-local scopes. User-specific absolute workspace roots are not exposed.

## `POST /docs/update-metadata`

Expected data:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer",
  "title": "Docs Viewer",
  "summary": "Runtime and management docs.",
  "ui_status": "done",
  "viewable": true,
  "parent_id": "docs-viewer-overview"
}
```

Actions:

- updates supported front matter fields only
- preserves body content, filename, `doc_id`, and `added_date`
- refreshes `last_updated` when a real change is written
- removes blank `summary` and `ui_status` fields
- validates non-blank `parent_id` in the same scope
- rejects parent cycles and descendant-parent moves
- rebuilds targeted docs payloads for affected docs
- runs targeted docs-search updates when search-affecting fields change

Returned data includes change flags, source path, rebuild diagnostics, summary text, and `dry_run`.

## `POST /docs/update-viewability`

Expected data:

```json
{
  "scope": "library",
  "doc_id": "example-doc",
  "viewable": true
}
```

Actions:

- updates only one doc's `viewable` and `last_updated` front matter
- preserves title, parent, body, `doc_id`, and `added_date`
- skips writes and rebuilds for no-op requests
- rebuilds targeted docs payloads and docs search when changed

Returned data includes changed state, affected doc ids, rebuild diagnostics when changed, and `dry_run`.

## `POST /docs/update-viewability-bulk`

Expected data:

```json
{
  "scope": "library",
  "doc_ids": ["example-doc", "example-parent"],
  "viewable": true,
  "include_descendants": false
}
```

Actions:

- expands requested ids to descendants when `include_descendants: true`
- writes only docs whose `viewable` value changes
- runs one targeted docs payload rebuild and one targeted docs-search update for changed ids
- skips writes and rebuilds when every selected doc is already in the requested state

Returned data includes requested ids, changed ids, skipped/no-op state, rebuild diagnostics, summary text, and `dry_run`.

## `POST /docs/move`

Expected data:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer",
  "parent_id": "scripts"
}
```

Actions:

- writes only the moved doc's `parent_id` and `last_updated`
- preserves source filename, body, title, `doc_id`, and `added_date`
- accepts blank `parent_id` for root-level placement
- validates non-blank parent ids inside the same scope
- rejects moving a doc under itself or a descendant
- skips writes and rebuilds for no-op moves
- rebuilds the moved doc payload and updates search for the moved doc plus descendants

Returned data includes previous and next parent ids, affected search ids, rebuild diagnostics, summary text, and `dry_run`.

## `POST /docs/delete-preview`

Expected data:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer"
}
```

Actions:

- validates the selected doc
- reports child-doc blockers
- reports inbound Markdown references as warnings
- returns the source file path that would be removed
- does not delete files

Returned data includes `allowed`, `blockers`, `warnings`, target doc metadata, source path, and `dry_run: true`.

## `POST /docs/delete-apply`

Expected data:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer",
  "confirm": true
}
```

Actions:

- requires `confirm: true`
- re-runs delete preview validation
- deletes the Markdown source file only when no blockers remain
- clears `default_doc_id` when the deleted doc was the optional configured default
- opens the first remaining loadable root in the browser without making it the new default
- rebuilds targeted generated docs payloads and docs search after deletion
- writes watcher-suppression markers for the deleted source path

Returned data includes deletion metadata, source path, rebuild diagnostics, summary text, and `dry_run`.
