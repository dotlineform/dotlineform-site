---
doc_id: config-data-sharing-adapters
title: Data Sharing Adapter Registry
added_date: "2026-05-06 11:35"
last_updated: 2026-07-15
parent_id: data-sharing
viewable: true
---
# Data Sharing Adapter Registry

## Owner

`data-sharing/config/adapters.json` is checked policy for Data Sharing dispatch and capability projection. `adapters.schema.json` validates the structural contract; `analytics-app/.../data_sharing_adapters.py` adds semantic and path validation.

The registry answers:

- which adapter handles a domain/operation;
- which canonical capabilities and apply actions are active;
- where the domain's canonical reads/writes/config live;
- which external workspace root each operation may use;
- what safe labels/options/actions the browser may be shown.

It does not implement selectors, package shapes, review parsing, validation, or writes.

## Stable Shape

```text
paths
  -> exports, import-staging, import-preview, meta

dispatch[data_domain + operation]
  -> adapter id
     -> data domain ownership/sources/write targets/config
     -> capability for prepare | list_returned | review | apply
        -> profiles, path contract, review rows, apply actions, activity
```

Exact adapters, profiles, actions, formats, and copy belong in the current JSON. Do not duplicate their inventory here.

## Dispatch Rules

- Canonical operations are only `prepare`, `list_returned`, `review`, and `apply`.
- Each `(data_domain, operation)` pair resolves to exactly one active adapter.
- Domain-specific choices such as `summary_apply` are `apply_actions`, not top-level operations.
- A profile/family/selector is the variation mechanism inside an adapter; duplicate dispatch rows are not.
- Status can describe planned/stub/disabled declarations, but active UI capability requires implemented handlers and an available workspace.

## Path And Source Rules

- Runtime roots must be distinct descendants of `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/` and are resolved through `services/paths.py`.
- `import-staging/` is the shared drop-zone for returned packages and Docs Import inputs; file schema and user action decide the consumer.
- Canonical source and write-target paths are safe repo-relative paths.
- Document domains point to Docs Viewer scope config/source helpers, never generated tree/by-id/search payloads.
- Tag sources point to Analytics canonical JSON and supporting public catalogue indexes.
- No retired `var/studio/...` or Studio route/API fallback is supported.

## Browser Projection

`/analytics/api/data-sharing/config` whitelists domain labels, capability status, selection/profile options, apply UI/confirmation/result metadata, Docs scope options, and workspace availability.

It must not expose:

- filesystem roots or path contracts;
- source/write targets;
- implementation modules;
- output filename patterns/internal metadata contracts;
- activity emission metadata;
- arbitrary profile internals.

## Change Method

1. Identify whether the change is dispatch, profile configuration, or new behaviour.
2. Change code first when a family/selector/review/apply contract is new.
3. Update registry/schema and public projection only with the minimum fields required.
4. Cover semantic validation, unsafe paths, ambiguous dispatch, handler availability, and projection redaction.
5. Update focused docs only if the ownership or extension rule changed.

The current registry is intentionally exhaustive; this page is its map and safety explanation.
