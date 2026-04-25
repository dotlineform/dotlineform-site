---
doc_id: scripts-docs-management-server
title: "Docs Management Server"
added_date: 2026-04-24
last_updated: 2026-04-25
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
- `GET /docs/import-html-files`
- `POST /docs/import-html`
- `POST /docs/broken-links`
- `POST /docs/rebuild`
- `POST /docs/open-source`
- `POST /docs/update-metadata`
- `POST /docs/update-viewability`
- `POST /docs/create`
- `POST /docs/move`
- `POST /docs/restore-move`
- `POST /docs/archive`
- `POST /docs/delete-preview`
- `POST /docs/delete-apply`

Current behavior:

- local-only write service for the shared Docs Viewer
- used by `/docs/?mode=manage` and `/library/?mode=manage`
- also used by `/studio/docs-broken-links/` for a read-only docs link audit
- also used by `/studio/library-import/` for staged-file listing and docs HTML import writes
- creates, archives, and deletes flat source docs under the current scope root
- creates Studio docs as `published: true`, `viewable: true`
- creates Library docs as `published: true`, `viewable: false`
- rebuilds scope-owned docs payloads after successful writes
- runs targeted docs-search updates after successful writes when affected doc ids are explicit
- coordinates successful source writes with the docs live watcher so `bin/dev-studio` does not immediately run a redundant second same-scope rebuild for the same changed source file

Search update behavior:

- create/import targets the new doc id
- import overwrite and metadata title edits target the changed doc id plus direct children because child search entries include `parent_title`
- metadata parent/order edits, move, archive, and delete target the changed doc id
- bulk viewability targets changed doc ids only
- internal targeted calls pass `--remove-missing` so missing, non-viewable, and `_archive` ids can be reconciled safely
- `POST /docs/rebuild` remains a full same-scope docs-search rebuild

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
- new docs write `added_date` and `last_updated` to the current date
- new Studio docs write `published: true`, `viewable: true`
- new Library docs write `published: true`, `viewable: false`
- `doc_id` and filename stem are generated from the title and made unique with `-2`, `-3`, and so on
- `after_doc_id`, when present, inserts the new doc after the referenced doc and reuses that doc's `parent_id`
- `parent_id`, when present without `after_doc_id`, must resolve inside the same scope
- `sort_order` appends as the last sibling when both `after_doc_id` and explicit `sort_order` are omitted

`GET /docs/import-html-files` returns:

- the current staged `.html` files under `var/docs/import-staging/`
- filename, repo-relative path, size, and modified time for each staged file
- a read-only listing intended for the Studio import page

`POST /docs/import-html` expects:

```json
{
  "scope": "studio",
  "staged_filename": "example 1.html",
  "include_prompt_meta": false,
  "overwrite_doc_id": "",
  "confirm_overwrite": false,
  "preview_only": false
}
```

Import behavior:

- `scope` must be `studio` or `library`
- `staged_filename` must resolve inside `var/docs/import-staging/`
- parses the full staged HTML file through the shared importer
- escapes literal pipe characters from source text so mathematical notation such as `I(X;Y|Z)` does not become an accidental Markdown table
- converts plain-text `http://` and `https://` URLs in prose into Markdown autolinks while leaving existing anchors and code/preformatted text alone
- validates the generated Markdown through the repo's Jekyll renderer helper before returning success
- supports the prompt/meta include toggle already defined by the import spec
- creates a new Markdown source doc immediately when the generated import target does not collide
- new imported docs write `added_date` and `last_updated` to the current date
- new Studio imports write `published: true`, `viewable: true`
- new Library imports write `published: true`, `viewable: false`
- preserves blank `parent_id` and appends the new imported doc at the end of the root-level `sort_order`
- reports collision details when the generated import target already matches an existing `doc_id`
- requires both `overwrite_doc_id` and `confirm_overwrite: true` before overwriting an existing doc
- preserves the overwritten doc's `doc_id`, filename, `added_date`, `parent_id`, `sort_order`, and existing `published`/`viewable` state
- creates an import-specific backup before overwrite using a light-touch same-day replacement rule
- `preview_only: true` forces a non-writing preview response even when the server is not running with `--dry-run`
- successful create/overwrite writes rebuild the same-scope docs payloads and run targeted docs-search updates for affected ids

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
- `added_date` is preserved; `last_updated` is refreshed after a successful metadata write
- `parent_id` may be blank for root, but must otherwise resolve inside the same scope
- `parent_id` cannot point at the current doc or any of its descendants
- `sort_order` accepts a non-negative integer, blank, or `append`
- `append` stores the next available sparse `sort_order` under the requested `parent_id`
- always rebuilds docs payloads for the scope
- runs a targeted same-scope docs-search update for affected ids after a successful write

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

- updates only the source doc's `viewable` front matter
- preserves `doc_id`, title, parent, sort order, body content, `added_date`, and `last_updated`
- writes `published: true` alongside `viewable` so the doc stays in generated docs payloads
- the single-doc endpoint is preserved for callers that already use `doc_id`
- the bulk endpoint accepts explicit `doc_ids`; `include_descendants: true` expands each requested doc to include its descendants from canonical docs source data
- no-op requests write no files, create no backup, and do not rebuild docs/search
- changed bulk requests copy only changed source files into the backup bundle, then run one docs rebuild and one targeted docs-search update for the scope
- the Docs Viewer manage-mode `Make viewable` action now uses the bulk endpoint so it can include required ancestors and optional descendants in one write/rebuild

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
- moves update the dragged doc's `parent_id` and normalize the destination sibling set to sparse unique `sort_order` values
- moves preserve `added_date`
- moves may rewrite multiple sibling docs when normalization changes their order values
- successful move responses include `undo_records` for every doc whose placement changed
- successful moves rebuild the current scope docs payloads and run a targeted docs-search update for the moved doc

`POST /docs/restore-move` expects:

```json
{
  "scope": "studio",
  "focus_doc_id": "docs-viewer-management",
  "records": [
    {
      "doc_id": "docs-viewer-management",
      "parent_id": "ui-requests",
      "sort_order": 21
    }
  ]
}
```

Restore-move behavior:

- restores one client-side move history step by rewriting all supplied placement records
- validates each restored `parent_id` against the current scope and rejects self-parent or descendant-parent cycles
- accepts integer or blank `sort_order`
- writes only records whose current placement differs from the supplied restore record
- rebuilds the current scope docs payloads and runs targeted docs-search updates for changed doc ids

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
- preserves `added_date` and refreshes `last_updated`
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
- rebuilds the current scope docs payloads and runs a targeted docs-search removal/update after delete

## Security Constraints

- binds to loopback only
- CORS allows loopback origins only
- write targets are allowlisted to:
  - `_docs_src/*.md`
  - `_docs_library_src/*.md`
  - `var/docs/backups/`
  - `var/docs/logs/`
  - `var/docs/watch-suppressions/`
- timestamped backup bundles are created under `var/docs/backups/` before each non-dry-run write batch
- backups are operation-scoped rather than full-scope:
  - `create` writes a manifest-only backup bundle
  - `archive` backs up only the touched doc before rewrite
  - `delete` backs up only the deleted doc before removal

## Operational Notes

- `bin/dev-studio` starts this service on `http://127.0.0.1:8789`
- the shared Docs Viewer probes `GET /capabilities` only when `?mode=manage` is present
- if the local service is unavailable, the viewer stays read-only and shows a manage-mode unavailable message
- successful source writes now leave short-lived suppression markers under `var/docs/watch-suppressions/` so the docs live watcher can skip duplicate same-scope rebuilds for the exact files already rebuilt by the server
- `var/` is excluded from Jekyll because docs-management backups, logs, staged imports, and watcher-suppression markers are local operational files rather than publishable site input

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
