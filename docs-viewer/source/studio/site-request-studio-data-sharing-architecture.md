---
doc_id: site-request-studio-data-sharing-architecture
title: Studio Data Sharing Architecture Request
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: proposed
parent_id: change-requests
sort_order: 10025
viewable: true
---
# Studio Data Sharing Architecture Request

Status:

- proposed
- split out from [Studio Docs Viewer Dependencies](/docs/?scope=studio&doc=studio-doc-viewer-dependencies)

## Summary

Clarify and revise the Studio Data Sharing service boundary so Studio owns the Data Sharing workflow without depending on the Docs Viewer HTTP service for its own routes.

The target direction is:

- Studio Data Sharing owns workflow routes, UI, adapter registry, export configs, package preparation, returned-package review, apply orchestration, and local HTTP endpoints.
- Domain adapters live with Studio Data Sharing, even when they target documents, tags, catalogue records, or other domain schemas.
- Domain read/write engines remain domain-aware and reusable. The documents adapter should call docs-domain helpers for generated reads, simplified HTML/package creation, returned JSON review, source Markdown/front matter updates, backups, and rebuild follow-through.
- Docs Viewer owns Docs Viewer UI, public docs routes, Docs Import, and docs management routes. It should not be the runtime service boundary for Studio Data Sharing.

The desired document workflow is:

```text
docs-domain read/export helpers -> Studio Data Sharing -> external LLM
external LLM -> Studio Data Sharing -> docs-domain review/apply helpers
```

This keeps document writes in docs-aware code while avoiding this shape:

```text
Studio Data Sharing -> Docs Viewer HTTP service -> docs source writes
```

## Current Problem

The current implementation has a strong Docs Viewer service dependency because the documents adapter and document source writes are exposed through Docs Viewer HTTP endpoints.

Studio Data Sharing pages currently call configured Docs Viewer endpoints for:

- service health
- generated docs index reads
- package preparation
- returned-package listing
- returned-package review
- confirmed apply

This made sense while the document workflow lived closest to Docs Viewer. It now creates a confusing ownership boundary: Studio owns the Data Sharing UI and shared adapter registry, but the runtime service endpoint for document workflows is the Docs Viewer service.

That dependency should not be resolved in the narrower Studio/Docs Viewer link cleanup. It needs a separate architecture slice because it affects service ownership, adapter placement, document write safety, tests, and docs.

## Proposed Boundary

Studio Data Sharing owns:

- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`
- local Studio Data Sharing API endpoints
- adapter registry loading and validation
- export/sharing profile config
- operation dispatch for `prepare`, `list_returned`, `review`, and `apply`
- returned-package staging roots, review roots, and package lifecycle policy
- external LLM package shape and returned JSON handling
- shared UI states, confirmation flows, and activity append timing

Data Sharing adapters live under a Studio-owned Data Sharing package.
Adapters may be domain-specific, but their service boundary is Studio Data Sharing rather than a peer local app.

Domains own reusable data engines:

- documents: generated/published docs reads, simplified HTML export, source Markdown/front matter parsing and update helpers, docs backups, docs/search rebuild follow-through
- tags: tag registry, aliases, assignments, validation, and write helpers
- catalogue: work, series, detail, or moment schemas and write helpers when those domains become Data Sharing targets

Docs Viewer owns:

- docs browsing and management UI
- docs public-scope routes
- Docs Import UI and import endpoints
- Docs Viewer service health for Docs Viewer itself
- route links opened from Studio nav and page implementation links

## Open Design Questions

- Where should the reusable docs-domain helpers live so they are clearly not Docs Viewer UI code but can still be used by Docs Viewer and Studio Data Sharing?
- Should existing `docs-viewer/services/docs_export.py` and `docs-viewer/services/docs_import.py` be split into reusable domain helpers plus service/UI wrappers, or only wrapped by the Studio documents adapter at first?
- Which current Data Sharing routes should become same-origin Studio endpoints, and which response contracts can remain unchanged for the browser modules?
- Should the documents adapter keep the current `documents` adapter id and `library` data domain during the move?
- How should rebuild follow-through be triggered after source writes without coupling Studio Data Sharing to a running Docs Viewer service?

## Non-Goals

- Do not move Docs Viewer UI, Docs Import UI, or docs management routes into Studio.
- Do not make generic Studio code write document source files without docs-domain validation.
- Do not remove Data Sharing's document workflow.
- Do not solve portable Docs Viewer packaging in this request.
- Do not change the external LLM provider contract unless required by the service-boundary move.

## Implementation Tasks

1. Document the target boundary in `studio-data-sharing.md`, `studio-data-sharing-technical-spec.md`, and `config-data-sharing-adapters.md`.
2. Inventory the current document Data Sharing call graph: browser modules, Studio dispatch modules, Docs Viewer service wrappers, docs export/import helpers, backup/rebuild hooks, and tests.
3. Define same-origin Studio Data Sharing API endpoints for health, generated docs index reads as needed, prepare, returned-package listing, review, and apply.
4. Move or wrap the documents adapter so Studio Data Sharing can call it directly without `DOCS_VIEWER_BASE_URL`.
5. Extract or clearly name reusable docs-domain helpers for simplified HTML/package preparation, returned JSON review, summary apply, hierarchy apply, source writes, backups, and rebuild follow-through.
6. Keep existing browser response contracts where practical so UI changes are limited to endpoint configuration and service availability behavior.
7. Update `studio-transport.js` so Data Sharing endpoints are Studio-owned same-origin endpoints rather than configured Docs Viewer service endpoints.
8. Remove document Data Sharing endpoints from `app.runtime.services.docs` after the Studio endpoints are live.
9. Update tests for the new service boundary, including unavailable-service states, document prepare/review/apply flows, and tags prepare/review/apply flows.
10. Update docs and add a structured docs-log entry when the architecture change lands.

## Acceptance Criteria

- Studio Data Sharing works without a running Docs Viewer service for its own prepare/review/apply routes.
- Studio still opens Docs Viewer from top navigation and page/document implementation links.
- Document source writes remain docs-aware, validated, backed up, and followed by the required rebuild behavior.
- `DOCS_VIEWER_BASE_URL` is not used by Studio Data Sharing browser modules or Studio Data Sharing service dispatch.
- Documents and tags adapters are both resolved through the Studio Data Sharing adapter registry.
- The stable Data Sharing docs describe adapters as Studio Data Sharing-owned, with domain-specific helper dependencies where needed.

## Verification Matrix

| Slice | Codex-run checks | Manual checks |
|---|---|---|
| API boundary | focused Python tests for Studio Data Sharing endpoints and adapter resolution | Confirm prepare/review pages load with Docs Viewer stopped |
| Documents adapter | document prepare/review/apply tests with fixture source docs and returned packages | Prepare a Library package, stage a returned JSON file, review it, and apply selected rows |
| Tags adapter | existing tags adapter pytest and smoke checks | Prepare/review/apply a tags returned package |
| Runtime config | runtime config test asserts no Data Sharing endpoints under `app.runtime.services.docs` | Inspect `/studio/runtime-config.json` |
| Link boundary | runtime config test asserts Docs nav and `doc_href` links still point to configured Docs Viewer URLs | Open Studio nav Docs link and a page `i` link |

## Related Docs

- [Studio Docs Viewer Dependencies](/docs/?scope=studio&doc=studio-doc-viewer-dependencies)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec)
- [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
