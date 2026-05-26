---
doc_id: site-request-studio-data-sharing-architecture
title: Studio Data Sharing Architecture Request
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: done
parent_id: change-requests
sort_order: 12000
viewable: true
---
# Studio Data Sharing Architecture Request

Status:

- done
- implementation and final verification are recorded in [Studio Data Sharing Architecture Tasks](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture-tasks)

## Summary

Clarify and revise the Studio Data Sharing boundary so Studio owns the UI/API host, while shared Data Sharing code, configs, schemas, adapters, and flow artifacts have a clear top-level subsystem rather than being mixed into Studio or Docs Viewer service code.

The target direction is:

- `studio/` remains the permanent home for UI pages, browser modules, route state, and local HTTP endpoints.
- `docs-viewer/` remains the permanent home for Docs Viewer UI, docs management/import behavior, and docs-domain helpers needed in this repo.
- a top-level, headless `data-sharing/` subsystem owns workflow code, adapter code, schemas, registry/config files, and package contract code.
- `data-sharing/` does not host servers, UI routes, browser modules, or Studio shell behavior.
- Domain adapters live under `data-sharing/`, even when they target documents, tags, catalogue records, or other domain schemas.
- Domain read/write engines remain domain-aware and reusable. The documents adapter calls explicit docs-domain helper modules for generated reads, selectable-record discovery, simplified HTML/package creation, returned JSON review, source Markdown/front matter updates, backups, and rebuild follow-through.
- Runtime package/staging/review artifacts move directly to `var/studio/data-sharing/<domain>/...`. Existing disposable packages under `var/studio/export-import/...` do not need compatibility reads or migration support.

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

This made sense while the document workflow lived closest to Docs Viewer. It created a confusing ownership boundary: Studio owned the Data Sharing UI and shared adapter registry, but the runtime service endpoint for document workflows was the Docs Viewer service.

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
- adapter-owned selectable-record contracts for prepare workflows
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
The shared Studio shell asks the active adapter for selectable records instead of assuming the current Library generated-index shape is the durable prepare-page contract.
Future document adapters can therefore provide different selection inputs, filters, payload fields, and eligibility rules without creating a generic Studio docs-read endpoint.

Domains own reusable data engines:

- documents: generated/published docs reads, selectable-record discovery, simplified HTML export, source Markdown/front matter parsing and update helpers, docs backups, docs/search rebuild follow-through
- tags: tag registry, aliases, assignments, validation, and write helpers
- catalogue: work, series, detail, or moment schemas and write helpers when those domains become Data Sharing targets

Reusable docs-domain helper code stays under `docs-viewer/services/` unless the implementation plan deliberately creates a new package boundary.
The target state is explicit domain-oriented modules for document package, review, apply, backup, and rebuild helpers, callable by both Docs Viewer and Studio Data Sharing without going through Docs Viewer HTTP or UI/service wrapper modules.

Docs Viewer owns:

- docs browsing and management UI
- docs public-scope routes
- Docs Import UI and import endpoints
- Docs Viewer service health for Docs Viewer itself
- route links opened from Studio nav and page implementation links

Runtime artifacts remain outside tracked subsystem code.
The first migration should standardize active package, staging, and review outputs under:

```text
var/studio/data-sharing/<domain>/
```

Existing disposable packages under `var/studio/export-import/...` do not block the move and should not receive compatibility reads.

## Non-Goals

- Do not move Docs Viewer UI, Docs Import UI, or docs management routes into Studio.
- Do not make generic Studio code write document source files without docs-domain validation.
- Do not remove Data Sharing's document workflow.
- Do not solve portable Docs Viewer packaging in this request.
- Do not change the external LLM provider contract unless required by the service-boundary move.
- Do not preserve old `var/studio/export-import/...` package roots through compatibility reads or migration code.

## Implementation Tasks

The implementation tracker is [Studio Data Sharing Architecture Tasks](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture-tasks).
Work through that table in order and keep this request document focused on the target architecture.

## Acceptance Criteria

- Studio Data Sharing works without a running Docs Viewer service for its own prepare/review/apply routes.
- Studio still opens Docs Viewer from top navigation and page/document implementation links.
- `data-sharing/` exists as a tracked, headless subsystem with no server or UI route ownership.
- Studio remains the only owner of Data Sharing UI pages and local HTTP endpoints.
- Document source writes remain docs-aware, validated, backed up, and followed by the required rebuild behavior.
- `DOCS_VIEWER_BASE_URL` is not used by Studio Data Sharing browser modules or Studio Data Sharing service dispatch.
- Documents and tags adapters are both resolved through the Data Sharing adapter registry.
- Runtime package, staging, and review artifacts are written under `var/studio/data-sharing/<domain>/...`; old `var/studio/export-import/...` roots are not kept through compatibility reads.
- The stable Data Sharing docs describe adapters as Data Sharing-owned, with domain-specific helper dependencies where needed.

## Closeout

SDSA-016 completed the final verification pass on 2026-05-26.
The architecture request is implemented: Studio owns the Data Sharing UI and same-origin API, `data-sharing/` owns headless dispatch/config/adapters/path contracts, and Docs Viewer remains the owner of docs-domain helpers without hosting Data Sharing HTTP endpoints.

Final Codex-run verification:

- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_data_sharing_subsystem_scaffold.py studio/tests/python/test_studio_data_sharing_api.py studio/tests/python/test_data_sharing_adapters.py studio/tests/python/test_data_sharing_service.py docs-viewer/tests/python/test_docs_import_service.py studio/tests/python/test_tags_data_sharing_adapter.py` passed: 63 tests.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_prepare_modules.py --site-root .` passed.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_review_workflow_modules.py --site-root .` passed.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_data_sharing_routes.py` passed.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_prepare.py --mock-data-sharing-api` passed after the smoke default was updated to start a temporary Local Studio app.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_prepare.py --block-data-sharing-api` passed after the smoke default was updated to start a temporary Local Studio app.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_review.py --mock-data-sharing-api` passed after the smoke default was updated to start a temporary Local Studio app.
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_review.py --block-data-sharing-api` passed after the smoke default was updated to start a temporary Local Studio app.

During final verification, the full prepare/review browser smokes timed out in static `--site-root .` mode because the now Local-Studio-owned route roots stayed hidden there.
The same mocked and blocked API checks passed in the Local Studio host, which is now the default for these smoke entrypoints.

Follow-on work:

- archive this request according to the current change-request practice when ready
- treat future catalogue or non-tag Analytics sharing as new adapter work under the same `data-sharing/` boundary
- keep portable Docs Viewer packaging decisions in a separate request

## Verification Matrix

| Slice | Codex-run checks | Manual checks |
|---|---|---|
| API boundary | focused Python tests for Studio Data Sharing endpoints and adapter resolution | Confirm prepare/review pages load with Docs Viewer stopped |
| Headless subsystem | import/syntax tests for `data-sharing/` modules and registry/config loading | Confirm no UI routes or servers are introduced under `data-sharing/` |
| Documents adapter | document prepare/review/apply tests with fixture source docs and returned packages | Prepare a Library package, stage a returned JSON file, review it, and apply selected rows |
| Tags adapter | existing tags adapter pytest and smoke checks | Prepare/review/apply a tags returned package |
| Artifact roots | path-contract tests for `var/studio/data-sharing/<domain>/...` roots | Confirm new prepare/review artifacts are written under `var/studio/data-sharing/<domain>/...` |
| Runtime config | runtime config test asserts no Data Sharing endpoints under `app.runtime.services.docs` | Inspect `/studio/runtime-config.json` |
| Link boundary | runtime config test asserts Docs nav and `doc_href` links still point to configured Docs Viewer URLs | Open Studio nav Docs link and a page `i` link |

## Related Docs

- [Studio Docs Viewer Dependencies](/docs/?scope=studio&doc=studio-doc-viewer-dependencies)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec)
- [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)

## Change Log Entries

- `change-2026-05-26-completed-studio-data-sharing-architecture-boundary`
