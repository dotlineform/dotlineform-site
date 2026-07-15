---
doc_id: analytics-tag-services
title: Tag Services
added_date: 2026-06-02
last_updated: 2026-07-15
parent_id: analytics
---
# Tag Services

## Stable Structure

```text
Analytics route controller
  -> analytics_api.py dispatch by allowlisted path
  -> tag_write_api/ translates HTTP body/result
  -> tag_services/ validates and plans domain change
  -> tag_write_transactions.py atomic replace
  -> canonical tag JSON + optional activity row
```

Reads and writes are served by the standalone Local Analytics server under `/analytics/api`. Endpoint constants in `tag_services/tag_routes.py` and dispatch maps in `analytics_api.py` are the exact route inventory.

## Ownership

- `tag_source_paths.py` — canonical path contract.
- `tag_source_model.py` — IDs, limits, normalization, schema validation, comparison helpers.
- `tag_assignment_service.py` — series/work save plus offline import preview/apply.
- focused registry/alias/promotion mutation modules — cross-file plans and impact summaries.
- `tag_write_api/` — request parsing, activity context, and service response shaping.
- `tag_write_transactions.py` — atomic single/multi-file replacement and rollback on partial failure.
- `analytics_api.py` — GET/POST allowlists only.

## Mutation Families

- save or import assignments;
- import/create/edit/delete registry tags;
- import/create/edit/delete aliases;
- promote an alias into a canonical tag;
- demote a canonical tag into an alias;
- preview destructive/cross-file effects before apply.

Exact request fields belong to the handlers/tests. The important common contract is: validate IDs and current source, plan effects without writing, then apply through the fixed transaction boundary.

## Safety And Failure

- writes are confined to Registry, Aliases, and Assignments source paths;
- subprocesses and arbitrary browser paths are not part of this service;
- multi-file replacements retain original bytes for in-process rollback;
- successful local mutations can append one normalized Admin activity row;
- dry-run paths return planned effects without canonical writes;
- browser patch/offline fallbacks do not share the server transaction guarantee until reconciled.

## Extension Method

Add the narrowest domain function first, then an API wrapper and one allowlisted route. Cover validation, dry-run/no-write, cross-file effects, rollback, activity, and HTTP dispatch at the smallest useful level.

Do not add a generic mutation endpoint or browser-selected source path. If a new workflow changes several canonical files, its service should own one explicit plan and one atomic apply boundary.
