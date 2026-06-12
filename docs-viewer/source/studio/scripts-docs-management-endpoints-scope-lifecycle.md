---
doc_id: scripts-docs-management-endpoints-scope-lifecycle
title: Scope Lifecycle Endpoints
added_date: 2026-06-07
last_updated: 2026-06-12
parent_id: scripts-docs-management-endpoints
---
# Docs Viewer Scope Lifecycle Endpoints

Scope lifecycle endpoints create and delete user-created Docs Viewer scopes. Ownership is recorded in `docs-viewer/config/scopes/docs_scope_manifest.json`; system-owned scopes and public scopes are blocked from lifecycle deletion.

Current create support is limited to local scope modes:

- `local_uncommitted`
- `local_committed`

`public_readonly` creation is rejected until public Docs Viewer routes are data-driven.
Public scope deletion is also rejected.

## `POST /docs/scopes/create-preview`

Expected data:

```json
{
  "scope_id": "notes",
  "title": "Notes",
  "source_root": "docs-viewer/source/notes",
  "default_doc_id": "notes",
  "publishing_mode": "local_uncommitted",
  "build_inline_search": true,
  "write_generated_outputs": true
}
```

Actions:

- validates the new scope id, title, default doc id, publishing mode, source root, and generated output paths
- checks for collisions with existing scopes and files
- reports planned created files, changed files, build commands, and management URL
- does not write files

Returned data includes `schema_version`, `allowed`, `blockers`, planned scope config, planned manifest record, planned file changes, rebuild commands, URLs, and `dry_run: true`.

## `POST /docs/scopes/create-apply`

Expected data:

```json
{
  "scope_id": "notes",
  "title": "Notes",
  "source_root": "docs-viewer/source/notes",
  "default_doc_id": "notes",
  "publishing_mode": "local_uncommitted",
  "build_inline_search": true,
  "write_generated_outputs": true,
  "confirm": true
}
```

Actions:

- requires `confirm: true`
- re-runs create-preview validation
- creates the allowlisted source root
- writes the default welcome source doc
- updates `docs-viewer/config/scopes/docs_scopes.json`
- writes or updates `docs-viewer/config/scopes/docs_scope_manifest.json`
- rebuilds generated docs/search output for the new scope
- logs a `docs_scope_create_apply` event

Returned data includes created files, changed files, scope config, manifest record, rebuild output, URLs, summary text, and `dry_run`.

## `POST /docs/scopes/delete-preview`

Expected data:

```json
{
  "scope_id": "notes"
}
```

`scope` is also accepted by apply internals, but callers should use `scope_id`.

Actions:

- loads the scope manifest, backfilling existing scopes as system-owned when the manifest is missing
- verifies the scope is manifest-recorded, user-created, and tool-created
- reports planned deleted files and config changes
- blocks system-owned scopes
- blocks public scopes
- does not delete files

Returned data includes `allowed`, `blockers`, manifest ownership metadata, planned deleted files, planned changed files, and `dry_run: true`.

## `POST /docs/scopes/delete-apply`

Expected data:

```json
{
  "scope_id": "notes",
  "confirm": true
}
```

Actions:

- requires `confirm: true`
- re-runs delete-preview validation
- deletes only files owned by the manifest record
- removes the scope config entry
- removes the manifest record
- refreshes docs output for remaining scopes
- logs a `docs_scope_delete_apply` event

Returned data includes deleted files, missing files, changed files, rebuild output, summary text, and `dry_run`.
