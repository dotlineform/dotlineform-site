---
doc_id: scripts-catalogue-write-server
title: Catalogue Services
added_date: 2026-04-22
last_updated: 2026-07-15
parent_id: studio
---
# Catalogue Services

## What They Own

Catalogue services are the mutation, validation, and focused-read boundary behind Local Studio's catalogue routes.

They own:

- allowlisted canonical and generated reads;
- Work and Series create/save transactions;
- Work bulk saves and workbook import;
- detail-section aggregate changes;
- delete and publication preview/apply workflows;
- scoped public builds and R2 media publication;
- project-media discovery and the Project State report.

The active browser API is `/studio/api/catalogue/...`; there is no standalone catalogue server or offline write path. [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) is the focused current route inventory.

## Execution Boundary

```text
browser command
  -> studio_app_server.py
  -> studio_catalogue_api.py
  -> catalogue_write_service.py or adapter-owned operation
  -> focused catalogue service
  -> source validation and transaction
  -> optional lookup/build/media/activity follow-through
```

`studio_catalogue_api.py` owns HTTP adaptation plus operations that need Local Studio context: reads, workbook import, project-media discovery, report generation, and opening the local report.

`catalogue_write_service.py` owns the registered mutation dispatcher. It delegates to focused Work, Series, detail-section, bulk, delete, publication, build, and media-publish services. The dispatcher should stay a route map rather than accumulating workflow logic.

## Source And Transaction Rules

- Canonical catalogue source is below `studio/data/canonical/catalogue/`.
- `catalogue_source.py` owns normalization, loading, serialization shape, and whole-source validation.
- `catalogue_source_mutation.py` plans pure source changes without writing.
- `catalogue_transactions.py` owns atomic single- and multi-file replacement plus in-process restoration when a later transaction step fails.
- A proposed mutation is validated against the combined catalogue state, not just the submitted record.
- Derived lookups, public artifacts, media, and activity logs are outcomes of a canonical operation; they are not alternate source authorities.

Source success and downstream failure are intentionally distinguishable. For example, a canonical publication change can succeed while a public build or remote cleanup reports incomplete follow-through. The response must preserve that state instead of pretending the whole action rolled back when it did not.

## Safety Boundary

Local Studio binds to loopback. Catalogue reads and writes are allowlisted; request values cannot select arbitrary repository paths.

Project-media and report operations confine resolved paths below configured roots and return relative catalogue values rather than absolute filesystem paths. Remote media credentials and object details stay server-side.

Operational logs under `var/studio/catalogue/logs/` record compact IDs, fields, states, and errors rather than full submitted records. Supported workflows may also append normalized rows to the Studio Activity feed.

## How To Extend It

1. Decide which focused service owns the new operation and its transaction.
2. Add a service path only when a browser command is actually required.
3. Register the path in `catalogue_write_service.SERVICE_POST_PATHS` or keep it adapter-owned when it depends on Local Studio capabilities.
4. Add the browser constant in `studio-transport.js` and the exact API inventory in [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis).
5. Define lookup, public-build, media, cleanup, and activity effects explicitly.
6. Cover preview/apply agreement, path confinement, validation, and partial follow-through in tests.

## Known Weak Spots

- `studio_catalogue_api.py` is a broad adapter because it combines reads and several local-machine capabilities.
- Many mutations cross canonical source, generated lookups, public output, and remote media; response shapes must keep those boundaries legible.
- Full lookup refresh remains a safe fallback for changes whose dependency scope is not proven.
- Lower-level catalogue helpers retain capabilities that have no active Studio UI. Service or generator presence alone is not proof of a user-facing feature.

Use [Catalogue Build And Lookup Refresh](/docs/?scope=studio&doc=scripts-catalogue-write-server-build-lookup) for the two derived-output planners. Code and request-contract tests are the authority for exact payload fields.
