---
doc_id: public-static-site-build-batch-03-route-parity
title: Public Static Site Build Batch 3 Public Route Rendering Parity
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 3 Public Route Rendering Parity

This is the delivery specification for Batch 3 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: render production-equivalent public route shells without Jekyll or Liquid.

## Steer for these tasks

- Batch 3 is paused until [Public Route JavaScript Extraction](/docs/?scope=studio&doc=public-static-site-build-batch-03a-js-extraction) is complete.
- Batch 1 is closed; route parity comes from [Public Route Model](/docs/?scope=studio&doc=public-route-model) and the Batch 1 route inventory.
- Do not redesign public routes, visual design, or route behavior. Batch 1 must record a required migration exception before this batch changes them.
- Use local dual-running preview for route parity: serve the Jekyll baseline and `_public_site/` static comparison target on separate ports and smoke the same route list against both.
- Render `/library/` and `/analysis/` with `docs-viewer-public-routes.json`; do not use the private/manage Docs Viewer route registry.
- Do not embed the large route runtime scripts in Python renderers. Emit script tags for the JS modules created in Batch 3a.

## Batch 1 handoff

Render these route owners:

- `routes.render_home_redirect()` for `/`.
- `routes.render_about()` for `/about/`.
- `routes.render_recent()` for `/recent/`.
- `routes.render_series()` for `/series/` and query states.
- `routes.render_works()` for `/works/` and query states.
- `routes.render_work_details()` for `/work-details/` and query states.
- `routes.render_moments()` for `/moments/` and query states.
- `routes.render_catalogue_search()` for `/catalogue/search/`.
- `routes.render_docs_viewer_route("library")` for `/library/`.
- `routes.render_docs_viewer_route("analysis")` for `/analysis/`.
- `routes.render_404()` for `/404.html`.

Render helper owners:

- `render.render_page()` for the full document shell.
- `render.render_head()` for title, description, favicon/site manifest links, CSS, and deterministic asset versioning.
- `render.render_nav()` and `render.render_nav_item()` for public navigation.
- `render.render_footer()` for footer and global script includes.
- `render.render_docs_viewer_shell()` for the public Docs Viewer mount.

Do not implement compatibility redirects for retired path-style routes.

## Batch 2 handoff

Batch 2 created the static builder boundary:

- Entry point: `public-site/build/build_site.py`.
- Config owner: `public-site/config/public-site.json`.
- Builder modules: `public_site_builder.config`, `public_site_builder.builder`, `public_site_builder.render`, and `public_site_builder.audit`.
- Build wrapper: `bin/public-site-build`.
- Static preview wrapper: `bin/public-site-preview-static`.
- Default artifact output: `_public_site/`, guarded by `.public-site-artifact`.

Batch 3 route work must extend these files rather than adding a second builder path. The initial `render_initial_page()` helper currently renders only `404.html`; replace or broaden it into shared layout helpers for all public route shells.

## Batch 3a handoff

Batch 3a extracted large route runtime scripts into public JS files. Python route renderers must emit these script tags:

- `/series/`: `assets/js/public-catalogue-runtime.js`, then `assets/js/series-index.js`.
- `/recent/`: `assets/js/public-catalogue-runtime.js`, then `assets/js/recent-index.js`.
- `/works/`: `assets/js/public-catalogue-runtime.js`, `assets/js/work-page.js`, `assets/js/work.js`, then `assets/js/works-index.js`.
- `/work-details/`: `assets/js/swipe-nav.js`, `assets/js/public-catalogue-runtime.js`, `assets/js/work-detail-page.js`, then `assets/js/work.js`.
- `/moments/`: existing `assets/js/public-catalogue-runtime.js`, then `assets/js/moment.js`.
- `/catalogue/search/`: existing module script `assets/js/catalogue-search.js`.

Do not re-embed the extracted script bodies in Python strings.

## Deliverables

- Static-builder render helpers for shared layout, head metadata, navigation, footer, asset includes, catalogue shells, search shell, and Docs Viewer shell mounts.
- Generated HTML for the public root, static pages, catalogue shells, query-state shells, catalogue search, `/library/`, `/analysis/`, and `404.html`.
- Route parity checks against the active Jekyll output while Jekyll remains available.
- Python renderers that emit route shell contracts and script tags, not large inline runtime scripts.

## Implementation and policy guidance

- Page renderers pass structured data into focused helpers and return complete HTML files.
- Keep escaping and URL generation explicit.
- Avoid recreating broad Liquid semantics.

## Proposed verification set

- Static build success.
- Route file presence checks in the generated artifact.
- Browser smoke checks for representative catalogue routes and public Docs Viewer mounts against the static preview.
- Baseline-vs-static browser checks for the same route list when route shells or runtime boot behavior changes.
- Jekyll/static parity comparison for routes touched by this batch while Jekyll still exists.

## Tasks

### Batch 3: Public Route Rendering Parity

| ID | status | action |
| --- | --- | --- |
| 3.1 | planned | Use the completed Batch 3a script-tag contract, then implement the Batch 1 route/helper inventory without adding broad Liquid semantics. |
| 3.2 | planned | Implement shared render helpers and static page renderers. |
| 3.3 | planned | Implement fixed catalogue, work, work-detail, moment, and search route shells. |
| 3.4 | planned | Implement public Docs Viewer route shells for `/library/` and `/analysis/` using `docs-viewer-public-routes.json`. |
| 3.5 | planned | Add route presence and representative browser smoke checks for the static preview. |
| 3.6 | planned | Add local preview parity checks that compare the Jekyll baseline and static output on the same route list. |

## completed verification

- Not started.

## follow-on tasks

- Update Batch 4 with any route-specific asset or payload copy needs discovered during rendering, especially Docs Viewer runtime dependencies and catalogue JSON paths referenced by route data attributes.

## batch close

- Add a handoff note to [Batch 4](/docs/?scope=studio&doc=public-static-site-build-batch-04-assets-docs-viewer).
- Set this batch status and front matter `ui_status` to `done` after route parity is verified.
