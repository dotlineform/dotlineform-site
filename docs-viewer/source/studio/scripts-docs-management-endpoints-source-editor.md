---
doc_id: scripts-docs-management-endpoints-source-editor
title: Source Editor Endpoints
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: scripts-docs-management-endpoints
---
# Docs Viewer Source Editor Endpoints

## `GET /docs/source`

Query parameters:

```text
scope=studio
doc_id=docs-viewer
```

`doc=<doc_id>` is also accepted.

Returned data:

```json
{
  "ok": true,
  "scope": "studio",
  "doc_id": "docs-viewer",
  "source_body": "# Docs Viewer\n",
  "source_revision": "sha256:...",
  "path": "docs-viewer/source/studio/docs-viewer.md"
}
```

Used for:

- loading the manage-mode Markdown source editor
- giving the browser a stale-write revision token
- displaying the repo-relative source path for the selected doc

Validation:

- `scope` must be configured
- `doc_id` must resolve through the source model
- the source path must remain inside the configured scope root
- existing front matter must parse and contain the requested `doc_id`

This endpoint returns only the body after front matter. It does not write files.

## `POST /docs/source/rebuild`

Expected data:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer",
  "source_revision": "sha256:...",
  "source_body": "# Docs Viewer\n"
}
```

Actions:

- validates the selected source doc and front matter
- compares `source_revision` with the current source file digest
- rejects stale revisions before writing
- preserves the exact existing front matter block
- normalizes submitted body line endings to `\n`
- writes the new source body
- rebuilds generated docs payloads for the selected doc id
- runs a targeted docs-search update for the selected doc id
- creates watcher-suppression markers for the changed source path
- logs a `docs-source-editor-rebuild` event

Returned data includes `ok`, `scope`, `doc_id`, the next `source_revision`, repo-relative `path`, rebuild diagnostics, summary text, and `dry_run`.

## `POST /docs/open-source`

Expected data:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer",
  "editor": "default"
}
```

`editor` must be `default` or `vscode`.

Actions:

- resolves the selected source Markdown file inside the configured scope
- for `editor: "vscode"`, opens the file with Visual Studio Code
- for `editor: "default"`, uses `DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP` when configured, otherwise prefers `MarkEdit`, `Typora`, `Marked 2`, then `Marked`, then macOS Launch Services defaults
- logs a `docs-open-source` event when the open command succeeds

Returned data includes `ok`, `scope`, `doc_id`, `editor`, `preferred_app`, repo-relative `path`, summary text, and `dry_run`.

This endpoint opens a local application. It does not modify docs source or generated output.
