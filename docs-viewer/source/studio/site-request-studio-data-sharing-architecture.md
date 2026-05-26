---
doc_id: site-request-studio-data-sharing-architecture
title: Studio Data Sharing Architecture Request
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: in-progress
parent_id: change-requests
sort_order: 10025
viewable: true
---
# Studio Data Sharing Architecture Request

Status:

- in progress

## Summary

Clarify and revise the Studio Data Sharing boundary so Studio owns the UI/API host, while shared Data Sharing code, configs, schemas, adapters, and flow artifacts have a clear top-level subsystem rather than being mixed into Studio or Docs Viewer service code.

The target direction is:

- `studio/` remains the permanent home for UI pages, browser modules, route state, and local HTTP endpoints.
- `docs-viewer/` remains the permanent home for Docs Viewer UI, docs management/import behavior, and docs-domain helpers needed in this repo.
- a top-level, headless `data-sharing/` subsystem owns workflow code, adapter code, schemas, registry/config files, and package contract code.
- `data-sharing/` does not host servers, UI routes, browser modules, or Studio shell behavior.
- Domain adapters live under `data-sharing/`, even when they target documents, tags, catalogue records, or other domain schemas.
- Domain read/write engines remain domain-aware and reusable. The documents adapter should call docs-domain helpers for generated reads, simplified HTML/package creation, returned JSON review, source Markdown/front matter updates, backups, and rebuild follow-through.
- Runtime package/staging/review artifacts stay under the existing configured `var/` roots during the first migration. Existing `var/studio/export-import/library/...` or `var/studio/data-sharing/...` roots should not be renamed as part of the boundary cleanup unless a later path migration is explicitly scoped.

The desired document workflow is:

```text
docs-domain read/export helpers -> data-sharing workflow
-> Studio API -> external LLM
-> external LLM -> Studio API
-> data-sharing workflow -> docs-domain review/apply helpers
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

Studio owns:

- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`
- local Studio Data Sharing API endpoints
- browser modules, route-ready state, UI copy loading, and user-facing page behavior
- service availability presentation and route-level lifecycle states
- activity append timing when the local Studio API has completed a successful operation

The top-level `data-sharing/` subsystem owns:

- adapter registry loading and validation
- export/sharing profile config
- operation dispatch for `prepare`, `list_returned`, `review`, and `apply`
- returned-package staging roots, review roots, and package lifecycle policy
- external LLM package shape and returned JSON handling
- shared prepare/review/apply orchestration code
- adapter implementations grouped by domain
- schemas, package contracts, and path-contract helpers

`data-sharing/` is deliberately headless.
It should not contain servers, UI routes, browser modules, or Studio page shell code.
Studio calls into this subsystem from its local API endpoints.

Candidate tracked layout:

```text
data-sharing/
  README.md
  config/
    adapters.json
    adapters.schema.json
    library-export-configs.json
  adapters/
    documents/
    tags/
    catalogue/
  services/
    registry.py
    dispatch.py
    paths.py
    package_io.py
  workflows/
    prepare.py
    list_returned.py
    review.py
    apply.py
```

Adapters may be domain-specific, but their service boundary is Studio's Data Sharing API rather than a peer local app.

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

Runtime artifacts remain outside tracked subsystem code.
The first migration should preserve existing configured roots such as:

```text
var/studio/export-import/library/
var/studio/data-sharing/<domain>/
```

Path cleanup can be a later task.
It should not block the architecture cleanup or force migration of already staged packages.

## Open Design Questions

- Which docs-domain helper functions should be renamed or extracted during the Studio API move, and which should remain wrapped until a later cleanup slice?
  - Recommendation: define and implement the target docs-domain helper boundary in this slice. Reusable document package, review, apply, backup, and rebuild helpers should have explicit domain-oriented module names and should be callable by both Docs Viewer and Studio Data Sharing without going through Docs Viewer HTTP or UI/service wrapper modules. Keep the code under `docs-viewer/services/` unless the implementation plan deliberately creates a new package boundary, but do not leave wrapper-only or "extract later" cleanup as the intended end state.
- Should Studio Data Sharing expose a same-origin generated-docs-index endpoint, or should prepare-page document selection be served through the documents adapter response?
  - Recommendation: serve prepare-page document selection through the documents adapter rather than adding a generic same-origin generated-docs-index endpoint. Future document adapters are likely to need different selection inputs, filters, payload fields, and eligibility rules, so the shared Studio shell should ask the active adapter for its selectable records instead of assuming the current Library generated-index shape is the durable contract.
- Should runtime package, staging, and review artifacts move directly to `var/studio/data-sharing/<domain>/...`?
  - Recommendation: yes. Treat `var/studio/data-sharing/<domain>/...` as the immediate target convention for this slice. Existing disposable packages under `var/studio/export-import/...` do not need compatibility reads or migration support.

## Non-Goals

- Do not move Docs Viewer UI, Docs Import UI, or docs management routes into Studio.
- Do not make generic Studio code write document source files without docs-domain validation.
- Do not remove Data Sharing's document workflow.
- Do not solve portable Docs Viewer packaging in this request.
- Do not change the external LLM provider contract unless required by the service-boundary move.
- Do not rename or migrate existing `var/` artifact roots in the first architecture slice unless required to keep existing workflows working.

## Implementation Tasks

1. Document the target boundary in `studio-data-sharing.md`, `studio-data-sharing-technical-spec.md`, and `config-data-sharing-adapters.md`.
2. Inventory the current document Data Sharing call graph: browser modules, Studio dispatch modules, Docs Viewer service wrappers, docs export/import helpers, backup/rebuild hooks, and tests.
3. Create the top-level headless `data-sharing/` subsystem for tracked workflow code, adapter code, schemas, registry/config files, and package contract helpers.
4. Move Data Sharing adapter registry/config files out of `studio/data/config/data-sharing/` only if the migration can preserve browser/API loading behavior cleanly; otherwise create compatibility reads first and move configs in a later slice.
5. Define same-origin Studio Data Sharing API endpoints for health, generated docs index reads as needed, prepare, returned-package listing, review, and apply.
6. Move or wrap the documents adapter so Studio's Data Sharing API can call `data-sharing/` code directly without `DOCS_VIEWER_BASE_URL`.
7. Extract or clearly name reusable docs-domain helpers for simplified HTML/package preparation, returned JSON review, summary apply, hierarchy apply, source writes, backups, and rebuild follow-through.
8. Preserve existing configured artifact roots, including any current `var/studio/export-import/library/...` or `var/studio/data-sharing/<domain>/...` roots, unless a separate path migration is explicitly scoped.
9. Keep existing browser response contracts where practical so UI changes are limited to endpoint configuration and service availability behavior.
10. Update `studio-transport.js` so Data Sharing endpoints are Studio-owned same-origin endpoints rather than configured Docs Viewer service endpoints.
11. Remove document Data Sharing endpoints from `app.runtime.services.docs` after the Studio endpoints are live.
12. Update tests for the new service boundary, including unavailable-service states, document prepare/review/apply flows, and tags prepare/review/apply flows.
13. Update docs and add a structured docs-log entry when the architecture change lands.

## Acceptance Criteria

- Studio Data Sharing works without a running Docs Viewer service for its own prepare/review/apply routes.
- Studio still opens Docs Viewer from top navigation and page/document implementation links.
- `data-sharing/` exists as a tracked, headless subsystem with no server or UI route ownership.
- Studio remains the only owner of Data Sharing UI pages and local HTTP endpoints.
- Document source writes remain docs-aware, validated, backed up, and followed by the required rebuild behavior.
- `DOCS_VIEWER_BASE_URL` is not used by Studio Data Sharing browser modules or Studio Data Sharing service dispatch.
- Documents and tags adapters are both resolved through the Data Sharing adapter registry.
- Existing runtime artifact roots continue to work; no staged packages are invalidated by the boundary cleanup.
- The stable Data Sharing docs describe adapters as Data Sharing-owned, with domain-specific helper dependencies where needed.

## Verification Matrix

| Slice | Codex-run checks | Manual checks |
|---|---|---|
| API boundary | focused Python tests for Studio Data Sharing endpoints and adapter resolution | Confirm prepare/review pages load with Docs Viewer stopped |
| Headless subsystem | import/syntax tests for `data-sharing/` modules and registry/config loading | Confirm no UI routes or servers are introduced under `data-sharing/` |
| Documents adapter | document prepare/review/apply tests with fixture source docs and returned packages | Prepare a Library package, stage a returned JSON file, review it, and apply selected rows |
| Tags adapter | existing tags adapter pytest and smoke checks | Prepare/review/apply a tags returned package |
| Artifact roots | path-contract tests for existing configured roots | Confirm existing staged/exported packages remain discoverable |
| Runtime config | runtime config test asserts no Data Sharing endpoints under `app.runtime.services.docs` | Inspect `/studio/runtime-config.json` |
| Link boundary | runtime config test asserts Docs nav and `doc_href` links still point to configured Docs Viewer URLs | Open Studio nav Docs link and a page `i` link |

## Related Docs

- [Studio Docs Viewer Dependencies](/docs/?scope=studio&doc=studio-doc-viewer-dependencies)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec)
- [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
