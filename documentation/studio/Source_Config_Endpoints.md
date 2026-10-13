---
draft: false
doc_id: d-20260607-222033-d9b8b1
title: Source Config Endpoints
added_date: 2026-06-07 22:20:33
last_updated: "2026-10-13 20:05:39"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Source Config Endpoints

`GET /docs/source-config` remains retired. The Settings endpoints below edit the single configured Working workspace; scope/stage selectors are retired without aliases.

## `GET /docs/source-config-settings`

No query selector is required. `docs_source_config_settings_v2` returns `source_config_path`, `editable_fields`, `blocked_fields`, `deferred_global_fields` and `workspace.fields`. Each editable field declares its type, current value, source/generated paths and description. The sole editable field is `default_doc_id`; roots, output locations, collections and other install-time configuration remain blocked.

The source path is `docs-viewer/config/workspace/docs-workspace.json stages.working.default_doc_id`; its local browser projection is `docs-viewer/config/defaults/docs-viewer-config.json workspace.default_doc_id`. Blank means the first ordinary Index root. No `requires_rebuild` flag is projected.

## `POST /docs/source-config-settings`

Expected request:

```json
{
  "changes": {
    "default_doc_id": "d-20260101-120000-a1b2c3"
  }
}
```

Optional `dry_run: true` validates the request without either write. The browser owns nonblank membership validation against its loaded ordinary Index. The server owns the editable allowlist, string type and immutable-ID syntax, preserving exact configured ownership without scanning document sources.

A real Save persists changed Working configuration, carries the resolved workspace directly into local browser-configuration projection and reports completion after that projection. Explicit unchanged Save still projects browser configuration for recovery without rewriting the source configuration. No document, Search or media build runs. A committed changed setting logs one `docs_source_config_settings` event.

Responses retain validation details, proposed/current values, warnings and `changed`, adding `committed`, `projection_complete`, `phase` and `dry_run`. Success returns HTTP 200. Write/projection failure returns HTTP 500 with `ok: false`, error/summary and completed effects: `committed: true` distinguishes saved configuration from later projection failure. No rebuild diagnostics are returned.

The browser applies the supplied default once committed, including on a later projection failure. It makes no configuration, Index or displayed-document GETs and preserves the current target/position. Correct a failing projection and explicitly Save again; there is no automatic retry or recovery build.

Empty changes, unsupported/blocked/deferred fields, wrong value types and malformed immutable IDs are rejected. Source-model/readiness/Title/report checks and corpus membership audits are outside this operation. [Management Operations](Management_Operations.md#settings) and [User Facing Rules](data/User_Facing_Rules.md) M.05 own completion behavior and pending manual acceptance.
