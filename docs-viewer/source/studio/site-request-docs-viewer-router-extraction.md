---
doc_id: site-request-docs-viewer-router-extraction
title: Docs Viewer Router Extraction Request
added_date: 2026-05-14
last_updated: 2026-05-14
ui_status: done
parent_id: archive
sort_order: 68000
viewable: true
---
# Docs Viewer Router Extraction Request

Status:

- implementation complete
- test-first implementation started
- retained route smoke added
- route helper extraction implemented
- document-resolution extraction implemented
- payload-load handoff implemented

## Summary

Extract the Docs Viewer route/history/document-loading spine out of `docs-viewer/runtime/js/docs-viewer.js` into a dedicated router boundary.

This work should happen now, while Docs Viewer routing is the current focus, rather than waiting for the next local route requirement to force the issue.
The current entry controller is still carrying too much broad behavior, and route changes are likely to keep arriving through local Studio and management workflows even if public internet-facing routes do not expand soon.

## Problem

`docs-viewer.js` remains over the review threshold after the sidebar, search, bookmark, config, and render helper extractions.
The remaining maintenance risk is concentrated in the route/history and document-loading path:

- URL creation for current scope and cross-scope links
- canonical query and hash handling
- anchor interception
- browser history writes
- popstate handling
- requested-doc resolution and non-loadable doc redirects
- payload loading and render handoff
- search route state handoff
- management mode route state

This makes short-lived local route work expensive because each new route behavior must be understood in the same file that also coordinates sidebar, search, bookmarks, reports, and management dynamic loading.

## Goals

- Add route-focused smoke coverage before moving runtime code.
- Extract route parsing, URL creation, history writes, document resolution, and document-load orchestration behind a small Docs Viewer router module.
- Keep `docs-viewer.js` as the entry coordinator, not the owner of routing rules.
- Preserve read-only Docs Viewer behavior for direct doc loads, internal doc links, hash links, search query URLs, alternate scope routes, and browser back/forward.
- Keep management/local route behavior explicitly in scope, even when the first retained smoke coverage uses read-only routes.

## Non-Goals

- Do not create a general Studio route framework.
- Do not add new product routes as part of this extraction.
- Do not move sidebar, search rendering, bookmark storage, report internals, or management write behavior into the router.
- Do not rebuild docs payloads as part of defining this request unless a separate docs-output verification slice needs it.

## Test-First Requirement

Route behavior tests must exist and pass against the pre-extraction implementation before router code moves.

Initial retained smoke coverage should verify:

- direct `/docs/` load with an explicit `scope` and `doc`
- direct search-query route state
- internal Docs Viewer links use in-page routing rather than full browser reloads
- browser back/forward restores the previous routed doc without full reload
- hash fragments survive route navigation and target visible document anchors
- alternate configured public scope routes still load

Management-mode route smoke coverage should be added when the isolated test build can render the dev Studio Docs Viewer management shell or when the test can run against a known local `bin/local-studio` route.

## Proposed Runtime Boundary

Candidate file:

- `docs-viewer/runtime/js/docs-viewer-router.js`

The router should own or wrap:

- `viewerUrl`
- `viewerUrlForScope`
- `routeFromAnchor`
- `setHistory`
- `resolveDocId`
- `applyCurrentRoute`
- `loadDoc`
- the `popstate` route branch

The entry controller should keep:

- DOM lookup and startup sequencing
- shared state object creation
- sidebar/search/bookmark/report/management controller wiring
- payload rendering markup handoff
- dynamic imports for reports and management

## Implementation Slices

### Slice 1: Retained Route Smoke Tests

Status: implemented.

Add a focused `studio/tests/smoke/docs_viewer_routes.py` script and wire it into the `docs-viewer-smoke` check profile.
Keep the same route smoke in `studio-smoke` as an optional integration guard.

Acceptance:

- the smoke script can run against a temporary Jekyll build root
- it verifies direct load, search route, internal link interception, back/forward, hash routing, and Library scope loading
- it passes before router extraction starts

### Slice 2: Pure Route Helper Module

Status: implemented.

Move pure URL and route parsing helpers first.

Implementation result:

- `docs-viewer/runtime/js/docs-viewer-router.js` owns current-scope URL building, cross-scope URL building, anchor route parsing, and history writes.
- `docs-viewer/runtime/js/docs-viewer.js` keeps small wrapper functions for existing controller call sites while delegating the route mechanics.
- A pre-existing direct-hash route issue was fixed so canonical URL replacement preserves `#hash` fragments before payload rendering.

Acceptance:

- URL construction and anchor parsing live in `docs-viewer-router.js`
- `docs-viewer.js` delegates to the router helper
- route smoke passes

### Slice 3: Document Resolution And History Orchestration

Status: implemented.

Move requested-doc resolution, history writes, and current-route application behind the router boundary.

Implementation result:

- `docs-viewer/runtime/js/docs-viewer-router.js` now owns requested-doc resolution, canonical route correction decisions, search-route state setup, current-route application, and the popstate route branch.
- `docs-viewer/runtime/js/docs-viewer.js` delegates route application to the router while retaining DOM lookup, payload fetching/rendering, report mounting, sidebar/search/bookmark/management controller wiring, and small callback adapters for existing controller call sites.
- Search route rendering remains delegated through the search controller; the router only sets route state and calls the provided search-render callback.
- Non-loadable docs still resolve to the first loadable descendant or the configured/default loadable target before history correction and document load.

Acceptance:

- `docs-viewer.js` no longer owns route correction logic directly
- search route state still delegates to the search controller
- non-loadable doc resolution still redirects to a loadable target
- route smoke still passes

### Slice 4: Payload Load Handoff

Status: implemented.

Move document-load orchestration only if it can be done without hiding rendering and report ownership inside the router.

Implementation result:

- `docs-viewer/runtime/js/docs-viewer-router.js` now owns document-load orchestration, including non-loadable redirects, selected-doc state, load history writes, payload-cache hits, request-id stale protection, payload fetch initiation, payload-cache storage, and stale-safe error handling.
- `docs-viewer/runtime/js/docs-viewer.js` keeps the concrete generated-payload fetch dependency, loading-shell DOM updates, missing-doc/error display, final payload rendering, report mounting, and document-pane ownership.
- Management and search callers still use the same entry-controller `loadDoc(...)` wrapper, so the external controller contract stays stable.

Acceptance:

- payload fetching can be initiated through the router boundary
- final rendering remains an entry-controller or renderer handoff
- stale request protection remains intact
- route smoke still passes

## Risks

- Browser history regressions can be subtle because full page reloads may still land on the right document.
- Search route state crosses the search controller boundary, so the router must not duplicate search rendering rules.
- Management mode has a different route surface from the normal static build; local/manage coverage needs a clear test environment before it is treated as fully protected.
- Over-extracting payload rendering would move non-route ownership into the router and recreate the same mixed-controller problem under a new filename.

## Verification

Required before implementation:

- `studio/tests/smoke/docs_viewer_routes.py` against the current implementation

Required after each runtime slice:

- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`
- optionally run `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile studio-smoke` when the slice should also be checked against broader Studio route smoke coverage

## Related References

- [Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Docs Viewer Extraction Plan](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-extraction-plan)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
