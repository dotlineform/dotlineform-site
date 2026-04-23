---
doc_id: scripts-docs-management-server
title: "Docs Management Server"
last_updated: 2026-04-23
parent_id: scripts
sort_order: 10
---
# Docs Management Server

Script:

```bash
./scripts/docs/docs_management_server.py
```

## Optional Flags

- `--port 8789`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--dry-run`: validate and return responses without writing source docs

## Endpoints And Behavior

Exposed endpoints:

- `GET /health`
- `GET /capabilities`
- `POST /docs/broken-links`
- `POST /docs/rebuild`
- `POST /docs/open-source`
- `POST /docs/update-metadata`
- `POST /docs/create`
- `POST /docs/move`
- `POST /docs/archive`
- `POST /docs/delete-preview`
- `POST /docs/delete-apply`

Current behavior:

- local-only write service for the shared Docs Viewer
- used by `/docs/?mode=manage` and `/library/?mode=manage`
- also used by `/studio/docs-broken-links/` for a read-only docs link audit
- creates, archives, and deletes flat source docs under the current scope root
- rebuilds scope-owned docs payloads and scope-owned docs search after successful writes

`GET /capabilities` reports:

- whether docs management is available
- which scopes are writable
- whether the current scope has `_archive`

`POST /docs/create` expects:

```json
{
  "scope": "studio",
  "title": "New Doc",
  "after_doc_id": "docs-viewer-management"
}
```

Request behavior:

- `scope` must be `studio` or `library`
- `title` defaults to `New Doc` when omitted or blank
- `doc_id` and filename stem are generated from the title and made unique with `-2`, `-3`, and so on
- `after_doc_id`, when present, inserts the new doc after the referenced doc and reuses that doc's `parent_id`
- `parent_id`, when present without `after_doc_id`, must resolve inside the same scope
- `sort_order` appends as the last sibling when both `after_doc_id` and explicit `sort_order` are omitted

`POST /docs/rebuild` expects:

```json
{
  "scope": "studio"
}
```

Rebuild behavior:

- `scope` must be `studio` or `library`
- rebuilds generated docs payloads for the requested scope
- rebuilds the docs-search artifact for the requested scope
- is intended for local manage mode rather than the public hosted site

`POST /docs/broken-links` expects:

```json
{
  "scope": "studio"
}
```

Broken-links behavior:

- `scope` must be `studio` or `library`
- runs the shared docs broken-links audit for that scope
- reports `not found` and strict `wrong title` issues
- does not write source docs or generated outputs
- is intended for the Studio audit page and terminal-backed local maintenance

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
- the server first checks `DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP`
- if that env var is unset, it currently prefers `MarkEdit`, then `Typora`, then `Marked 2`, then `Marked` when installed
- if none of those apps are present, it falls back to plain `open`, which follows macOS Launch Services defaults
- `editor: "vscode"` opens the file in Visual Studio Code
- intended for use from the manage-mode right-click menu on doc rows

`POST /docs/update-metadata` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "title": "Docs Viewer Management",
  "parent_id": "ui-requests",
  "sort_order": 21
}
```

Metadata-update behavior:

- updates only front matter; body content and filename remain unchanged
- currently supports `title`, `parent_id`, and `sort_order`
- title changes do not mutate `doc_id` or filename
- `parent_id` may be blank for root, but must otherwise resolve inside the same scope
- `parent_id` cannot point at the current doc or any of its descendants
- `sort_order` accepts a non-negative integer or blank
- always rebuilds docs payloads for the scope
- always rebuilds the same-scope docs-search artifact after a successful write

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
- moves update only the dragged doc's `sort_order` and `parent_id`
- sibling `sort_order` values are left unchanged to keep write noise low
- successful moves rebuild the current scope docs payloads and docs-search artifact

`POST /docs/archive` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Request behavior:

- moves the doc into the Archive section by setting `parent_id = _archive`
- appends the archived doc as the last sibling under `_archive`
- does not move the file on disk
- fails when `_archive` is not defined for the scope

`POST /docs/delete-preview` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Preview behavior:

- reports blockers such as reserved docs or child docs
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
- rebuilds the current scope docs payloads and docs-search artifact after delete

## Security Constraints

- binds to loopback only
- CORS allows loopback origins only
- write targets are allowlisted to:
  - `_docs_src/*.md`
  - `_docs_library_src/*.md`
  - `var/docs/backups/`
  - `var/docs/logs/`
- timestamped backup bundles are created under `var/docs/backups/` before each non-dry-run write batch
- backups are operation-scoped rather than full-scope:
  - `create` writes a manifest-only backup bundle
  - `archive` backs up only the touched doc before rewrite
  - `delete` backs up only the deleted doc before removal

## Operational Notes

- `bin/dev-studio` starts this service on `http://127.0.0.1:8789`
- the shared Docs Viewer probes `GET /capabilities` only when `?mode=manage` is present
- if the local service is unavailable, the viewer stays read-only and shows a manage-mode unavailable message

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
