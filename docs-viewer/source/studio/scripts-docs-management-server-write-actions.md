---
doc_id: scripts-docs-management-server-write-actions
title: Docs Management Service Write Actions
added_date: 2026-05-19
last_updated: 2026-05-22
parent_id: scripts-docs-management-server
sort_order: 15400
---
# Docs Management Service Write Actions

`POST /docs/open-source` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "editor": "default"
}
```

Open-source behavior:

- resolves the source Markdown path for the current doc within the current scope
- `editor: "default"` opens the file in the preferred Markdown app for the local machine
- the server first checks `DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP` from `var/local/site.env` for local runs
- if that key is unset, it currently prefers `MarkEdit`, then `Typora`, then `Marked 2`, then `Marked` when installed
- if none of those apps are present, it falls back to plain `open`, which follows macOS Launch Services defaults
- `editor: "vscode"` opens the file in Visual Studio Code
- intended for use from the manage-mode right-click menu on doc rows

`POST /docs/update-metadata` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "title": "Docs Viewer Management",
  "summary": "Manage-mode source editing contract.",
  "ui_status": "done",
  "viewable": true,
  "parent_id": "ui-requests",
  "sort_order": 21
}
```

Metadata-update behavior:

- updates only front matter; body content and filename remain unchanged
- currently supports `title`, `summary`, `ui_status`, `viewable`, `parent_id`, and `sort_order`
- title changes do not mutate `doc_id` or filename
- `added_date` is preserved; `last_updated` is refreshed to the current minute after a successful metadata write
- blank `summary` removes the front matter field
- blank `ui_status` removes the front matter field
- non-blank `ui_status` is stored as the raw status key supplied by the client; the write server does not validate it against Docs Viewer config
- `viewable` is stored as a boolean when supplied; the Docs Viewer Edit modal uses this to map `status = draft` to `viewable: false` and any non-draft status to `viewable: true`
- responses include `changes.status_changed` and `changes.viewable_changed` alongside the other metadata change flags
- `parent_id` may be blank for root, but must otherwise resolve inside the same scope
- `parent_id` cannot point at the current doc or any of its descendants
- `sort_order` accepts a non-negative integer, blank, or `append`
- `append` stores the next available sparse `sort_order` under the requested `parent_id`
- sparse order spacing uses `1000` between normalized siblings
- always rebuilds docs payloads for the scope, using targeted docs payload ids for changed source docs
- runs a targeted same-scope docs-search update for affected ids after a successful write
- skips docs-search updates when `ui_status` is the only changed field, because status emoji are viewer-only metadata
- keeps docs-search updates enabled for `viewable` changes so non-viewable docs are removed from search and newly viewable docs are added back
- successful write responses include the same `rebuild.diagnostics` shape used by `POST /docs/rebuild`

`POST /docs/update-viewability` expects:

```json
{
  "scope": "library",
  "doc_id": "example-doc",
  "viewable": true
}
```

`POST /docs/update-viewability-bulk` expects:

```json
{
  "scope": "library",
  "doc_ids": ["example-doc", "example-parent"],
  "viewable": true,
  "include_descendants": false
}
```

Viewability-update behavior:

- updates only the source doc's `viewable`, `published`, and `last_updated` front matter
- preserves `doc_id`, title, parent, sort order, body content, and `added_date`
- writes `published: true` alongside `viewable` so the doc stays in generated docs payloads
- the single-doc endpoint is preserved for callers that already use `doc_id`
- the bulk endpoint accepts explicit `doc_ids`; `include_descendants: true` expands each requested doc to include its descendants from canonical docs source data
- no-op requests write no files, create no backup, and do not rebuild docs/search
- changed bulk requests copy only changed source files into the backup bundle, then run one targeted docs payload rebuild and one targeted docs-search update for the scope
- the Docs Viewer manage-mode `Make viewable` action now uses the bulk endpoint so it can include required ancestors and optional descendants in one write/rebuild
- successful write responses include the same `rebuild.diagnostics` shape used by `POST /docs/rebuild`

`POST /docs/move` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "target_doc_id": "scripts-docs-management-server",
  "position": "after"
}
```

Move behavior:

- `position: "after"` places the dragged doc immediately after the target doc and adopts the target doc's `parent_id`
- `position: "inside"` places the dragged doc as the last child of the target doc
- only leaf docs can move; docs with child docs are rejected
- moves rewrite front matter only and never move files on disk
- moves update the dragged doc's `parent_id` and assign a sparse `sort_order` to the moved doc when there is room between neighboring siblings
- moves normalize the destination sibling set to sparse unique `sort_order` values only when the numeric gap is exhausted or the target order is ambiguous
- moves preserve `added_date`
- moves refresh `last_updated` on each source doc whose placement front matter is rewritten
- moves usually rewrite only the moved doc; they may rewrite multiple sibling docs when fallback normalization changes order values
- same-parent reorder rebuilds targeted current-scope docs payloads without a docs-search update
- reparenting rebuilds targeted current-scope docs payloads and runs a targeted docs-search update for the moved doc
- successful write responses include the same `rebuild.diagnostics` shape used by `POST /docs/rebuild`

`POST /docs/normalize-order` expects either a single sibling group:

```json
{
  "scope": "studio",
  "parent_id": "docs-viewer"
}
```

or a whole-scope repair:

```json
{
  "scope": "studio",
  "whole_scope": true
}
```

Normalize-order behavior:

- rewrites sibling `sort_order` values to `1000`, `2000`, `3000`, and so on
- defaults to the root sibling group when `parent_id` is omitted or blank
- validates non-root `parent_id` values against current scope source data
- `whole_scope: true` normalizes every sibling group in the scope
- the Docs Viewer `Actions` menu opens a modal for current sibling group, selected-doc children, root sibling group, or whole-scope repair
- writes only docs whose `sort_order` changes
- creates no backup bundle
- rebuilds targeted current-scope docs payloads without a docs-search update

`POST /docs/archive` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Request behavior:

- moves the doc into the Archive section by setting `parent_id = archive`
- appends the archived doc as the last sibling under `archive`
- does not move the file on disk
- preserves `added_date` and refreshes `last_updated` to the current minute
- fails when `archive` is not defined for the scope

`POST /docs/delete-preview` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Preview behavior:

- reports blockers such as child docs that still depend on the target
- reports inbound markdown references as warnings
- returns the file path that would be removed

`POST /docs/delete-apply` accepts the same shape plus:

```json
{
  "confirm": true
}
```

Apply behavior:

- requires explicit confirmation
- re-runs preview validation before delete
- deletes the Markdown source file when no blockers remain
- rebuilds targeted current-scope docs payloads and runs a targeted docs-search removal/update after delete
- successful write responses include the same `rebuild.diagnostics` shape used by `POST /docs/rebuild`

Scope lifecycle preview endpoints:

- `POST /docs/scopes/create-preview`
- `POST /docs/scopes/delete-preview`
- `POST /docs/scopes/create-apply`
- `POST /docs/scopes/delete-apply`

Scope lifecycle preview behavior:

- reads scope ownership from `docs-viewer/config/scopes/docs_scope_manifest.json`
- backfills existing scopes as system-owned when the manifest is missing
- validates new scope ids, source roots, default doc ids, publishing mode, and public route paths before reporting a write set
- reports planned created files, changed files, build commands, management URL, and public URL without writing files
- blocks delete preview for system-owned scopes and scopes not created by the lifecycle tool
- create apply requires `confirm: true`, re-runs create-preview validation, writes the allowlisted source root, default welcome doc, config entry, optional route page, and manifest record, then runs the requested docs/search rebuilds
- delete apply requires `confirm: true`, re-runs delete-preview validation, deletes manifest-owned scope files, removes the scope config entry and manifest record, then refreshes docs output for remaining scopes
