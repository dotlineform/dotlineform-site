---
doc_id: site-request-public-route-simplification-tasks
title: Public Route Simplification Tasks
added_date: 2026-06-01
last_updated: 2026-06-01
ui_status: draft
parent_id: site-request-public-route-simplification
viewable: true
---
# Public Route Simplification Tasks

This is the implementation tracker for [Public Route Simplification Request](/docs/?scope=studio&doc=site-request-public-route-simplification).

## Next Session Steer

Start from the current changed working tree; do not restart the route-helper slice.
The first slice already added the canonical browser route helper, `/series/` query-state modes, `/works/?work=...`, `/work-details/?detail=...`, `/moments/` recovery, `404.html`, and first-party route retargeting for recent/search/legacy layout links, Studio public-link helpers, catalogue search generation, and Docs Viewer semantic references.

Next session should focus on the remaining task rows:

- finish task 8 by scanning and cleaning plain public Library/Analysis links that still point to retired catalogue paths, without adding compatibility redirects
- finish task 9 by reviewing generated public payload contracts for derivable URL fields, especially moment `public_url`, and either remove/replace consumers or document any non-derivable exception
- advance task 10 by auditing remaining first-party dependence on `_works/`, `_series/`, and `_work_details/` collection outputs; keep collection generation only where Jekyll build constraints still require it, and record the removal condition
- advance task 12 by turning the ad hoc public route smoke into focused checked-in smoke coverage for the recommended route set
- update owning docs in task 13 after the remaining contract decisions are made; do not manually rebuild Docs Viewer payloads

Useful verification already run for the first slice:

- `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/build/build_docs.py studio/services/catalogue/search/build_search.py`
- `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_build_docs_python.py studio/tests/python/test_catalogue_search_builder_python.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- local Playwright smoke against an isolated static server for `/series/`, `/series/?mode=moments`, `/series/?series=009`, `/works/?work=00001`, `/works/?work=00001&series=009`, `/work-details/?detail=00001-001&from_work=00001`, `/moments/`, `/404.html`, and `/catalogue/search/?q=00001`

## Implementation Steer

Implement the simplified public route model while Jekyll remains the public preview/build layer.
This request should settle route behavior before [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) starts replacing Jekyll.

The agreed route shape is:

```text
/series/                         catalogue/series index shell
/series/?series=009              selected/filtered series state in the catalogue index shell
/series/?mode=moments            moments browse state in the catalogue index shell

/works/                          works list shell
/works/?work=00001               selected work view
/works/?work=00001&series=009    selected work with series navigation context

/work-details/?detail=00001-001  selected work detail view
/moments/                        explicit recovery route to /series/?mode=moments
/moments/a-doll-story/           individual moment page
```

Route implementation rules:

- old inbound URL compatibility is not required
- do not add broad redirect tables for old per-record paths
- keep `/series/` as the single public catalogue entry point for works, series, and moments
- keep individual moment pages for selected moments
- make `/moments/` recover to `/series/?mode=moments` with a visible fallback link
- use `/work-details/` rather than the legacy `/work_details/`
- derive public URLs dynamically in runtime helpers from record id plus route state
- remove persistent generated public URL fields if they exist, unless a documented non-derivable exception is required
- centralize route building and route parsing before the static-builder migration
- treat browser history as best-effort; explicit in-page back links carry important return context
- preserve first-party navigation from public indexes, grids, search, and public Docs Viewer semantic references

`assets/js/public-catalogue-runtime.js` is the likely first owner for the browser-side route helper contract unless implementation review shows that a smaller dedicated route module is cleaner.
Route strings should not be assembled independently across page scripts after this migration.

## Implementation Tasks

Work through the table by ID order.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory public route construction and route parsing. Cover `assets/js/public-catalogue-runtime.js`, `series/index.md`, `works/index.md`, `recent/index.md`, `_layouts/work.html`, `_layouts/series.html`, `_layouts/work_details.html`, `_layouts/moment.html`, catalogue search runtime modules, Docs Viewer semantic reference URL output, Studio public-link helpers, and generated public payload fields. Deliverable: short note in this tracker or implementation closeout naming the first-party route string assembly that must move to the canonical helper. |
| 2 | done | Define and implement the canonical public route helper contract. Add or reshape helpers for catalogue index state, selected series, selected work, selected work with series context, selected work detail, individual moment pages, `/moments/` recovery, and `404.html` recovery. Keep route building and route parsing together. |
| 3 | done | Update `/series/` as the catalogue index state shell. Preserve works mode, add or confirm URL-restorable moments mode at `/series/?mode=moments`, and support selected/filtered series state at `/series/?series=<series_id>` without relying on `/series/<series_id>/` for first-party navigation. |
| 4 | done | Update `/works/` to support selected work state. `/works/?work=<work_id>` should render the selected work view with title, media, metadata, prose/details entry points, and explicit back links. `/works/?work=<work_id>&series=<series_id>` should preserve visible series navigation context. Reuse or extract current work-page runtime/rendering behavior where practical rather than duplicating it. |
| 5 | done | Add the `/work-details/` selected-detail shell. `/work-details/?detail=<detail_uid>` should render the selected detail view with media, title, explicit back link to parent work context, and detail prev/next behavior. Retire first-party links to legacy `/work_details/<detail_uid>/`. |
| 6 | done | Keep individual moment pages and clean the moments index behavior. Individual moment links from the catalogue moments grid/list may continue to open paths such as `/moments/a-doll-story/`. Add an explicit `/moments/` recovery route that sends or links users to `/series/?mode=moments`, preventing local directory listings and accidental public 404 behavior. |
| 7 | done | Update catalogue search and first-party public navigation to use the canonical route helper. Search result links, recent links, series/grid links, works-list links, detail links, prev/next links, and back links should stop assembling old path-style routes locally. |
| 8 | in progress | Update Docs Viewer semantic references and plain public docs links. Semantic references that publish as public catalogue links must emit the new canonical routes. Any existing plain links in Library or Analysis can be cleaned directly and should not create compatibility requirements. |
| 9 | in progress | Update Studio public-link helpers and generated public payload contracts. Studio preview/public links should resolve through the new route contract. If generated public payloads contain derivable URL fields, remove them or replace consumers with runtime-derived routes unless a documented exception is required. |
| 10 | planned | Stop relying on per-record Jekyll collection outputs for first-party navigation. After the fixed shells and route helpers are verified, remove or disable first-party dependence on `/works/<work_id>/`, `/series/<series_id>/`, and `/work_details/<detail_uid>/`. Keep any remaining collection output only if a current build or cleanup constraint requires it, and document the removal condition. |
| 11 | done | Add or update `404.html`. Unknown retired routes should show simple "page unavailable" copy with a link back to `/series/`. Do not create broad compatibility redirects for old paths. |
| 12 | in progress | Add or update focused public route smoke coverage. Cover the recommended smoke set below using a Jekyll build served from an isolated temporary destination. |
| 13 | planned | Update owning docs after implementation. Update this tracker, the parent route simplification request if the route contract changes during implementation, public route/source ownership docs if route ownership changes materially, and the static-site build request only if its preconditions change. Do not rebuild Docs Viewer payloads manually. |
| 14 | planned | Close out the route simplification request. Confirm no unresolved route-compatibility layers remain, record any still-generated per-record outputs with owner/removal condition, and create a structured docs-log entry if the implementation is meaningful enough to record in change history. |

## Recommended Verification

Use this smoke set for implementation verification:

- build the current Jekyll public site to an isolated temporary destination
- serve the built output through a local static server
- load `/series/` and verify works mode renders
- switch to moments mode and verify `/series/?mode=moments` restores moments browse state
- open a selected series state through `/series/?series=<series_id>` and verify the filtered/selected view renders
- open a selected work through `/works/?work=<work_id>` and verify title, media, metadata, and explicit back link render
- open a selected work with series context through `/works/?work=<work_id>&series=<series_id>` and verify prev/next series navigation
- open a work detail through `/work-details/?detail=<detail_uid>` and verify media, title, explicit back link, and detail prev/next behavior
- open a moment from the catalogue moments grid/list and verify the individual moment page renders
- open `/moments/` and verify it recovers to `/series/?mode=moments` with a visible fallback link
- open catalogue search, choose a work/series/moment result, and verify the result uses the canonical route helper
- load a public Library or Analysis semantic reference link and verify it resolves to the canonical catalogue route
- load an unknown retired route and verify `404.html` shows "page unavailable" with a `/series/` recovery link
- run a focused source scan to catch stale first-party route string assembly outside the canonical route helper

## Implementation Notes

2026-06-01 route-helper and public-shell slice:

- First-party route construction moved into `assets/js/public-catalogue-runtime.js` for `/series/`, `/works/`, `/work-details/`, individual moment pages, `/moments/` recovery, and 404 recovery.
- `series/index.md` now restores `/series/?mode=moments` and renders selected-series works at `/series/?series=<series_id>`.
- `works/index.md` now supports selected work rendering at `/works/?work=<work_id>` and preserves `series` query context for visible series navigation/back links.
- `work-details/index.md` was added for `/work-details/?detail=<detail_uid>` and derives the parent work payload from the detail UID.
- First-party public links in `recent/index.md`, legacy work/series/detail layouts, catalogue search rendering, catalogue search generation, Studio public-link helpers, and Docs Viewer semantic reference generation now use canonical query-state routes for works and series.
- `/moments/` now recovers to `/series/?mode=moments`, and `404.html` provides simple "page unavailable" recovery without a compatibility redirect table.

Inventory note for task 1:

- Route string assembly found and moved or retargeted in this slice: `assets/js/public-catalogue-runtime.js`, `series/index.md`, `works/index.md`, `recent/index.md`, `_layouts/work.html`, `_layouts/series.html`, `_layouts/work_details.html`, `assets/js/search/catalogue-search-runtime.js`, `studio/services/catalogue/search/build_search.py`, `studio/app/frontend/js/catalogue-public-links.js`, and `docs-viewer/build/build_docs.py`.
- Remaining planned cleanup: plain public docs links in Library/Analysis, generated payload contract review for derivable URL fields such as moment `public_url`, permanent public route smoke coverage, and removal or disablement of first-party dependence on per-record Jekyll collection outputs.

## Closeout Requirements

Closeout should confirm:

- the parent route request still reflects the implemented route contract
- old inbound URL compatibility remains intentionally unsupported
- first-party public navigation uses the canonical route helper contract
- generated public payloads do not carry derivable URL fields, or any exception is documented
- `/moments/` no longer exposes local directory listings and recovers to `/series/?mode=moments`
- unknown retired routes show the agreed `404.html`
- the later public static-site builder can consume the simplified route contract without knowing the old route model
