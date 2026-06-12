---
doc_id: public-static-site-build-batch-03-route-parity
title: Public Static Site Build Batch 3 Public Route Rendering Parity
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: done
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

## Verification set

- Static build success.
- Route file presence checks in the generated artifact.
- Liquid-token checks for generated HTML.
- Browser smoke checks for representative catalogue routes and public Docs Viewer mounts against the static preview after Batch 4 copies required assets and payloads.
- Baseline-vs-static browser checks for the same route list after Batch 4 copies required assets and payloads.
- Jekyll/static parity comparison for routes touched by this batch while Jekyll still exists, after Batch 4 makes the static artifact executable.

## Tasks

### Batch 3: Public Route Rendering Parity

| ID | status | action |
| --- | --- | --- |
| 3.1 | done | Use the completed Batch 3a script-tag contract, then implement the Batch 1 route/helper inventory without adding broad Liquid semantics. |
| 3.2 | done | Implement shared render helpers and static page renderers. |
| 3.3 | done | Implement fixed catalogue, work, work-detail, moment, and search route shells. |
| 3.4 | done | Implement public Docs Viewer route shells for `/library/` and `/analysis/` using `docs-viewer-public-routes.json`. |
| 3.5 | deferred | Add representative browser smoke checks for the static preview after Batch 4 copies CSS, JS, data payloads, thumbnails, and Docs Viewer runtime files. |
| 3.6 | deferred | Add local preview parity checks that compare the Jekyll baseline and static output on the same route list after Batch 4 makes `_public_site/` executable. |

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile public-site/build/build_site.py public-site/build/public_site_builder/audit.py public-site/build/public_site_builder/builder.py public-site/build/public_site_builder/config.py public-site/build/public_site_builder/render.py public-site/build/public_site_builder/routes.py`
- `$HOME/miniconda3/bin/python3 -m json.tool public-site/config/public-site.json`
- `$HOME/miniconda3/bin/python3 -m pytest public-site/tests/test_build_site.py`
- `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit`
- `rg -n '\{\{|\{%' _public_site --glob '*.html'` returned no matches.
- Route script-reference spot check confirmed generated HTML references the expected public runtime files and Batch 3a route scripts.

## follow-on tasks

- Batch 4 must copy the public CSS/JS/data/thumb/Docs Viewer assets referenced by the generated route shells before browser parity can be completed.
- Batch 4 must add the browser smoke and local dual-running parity checks deferred from this batch.

## batch close

- Handoff note added to [Batch 4](/docs/?scope=studio&doc=public-static-site-build-batch-04-assets-docs-viewer).
- Batch route-shell rendering is complete. Static browser parity remains owned by Batch 4 because route assets are not copied in Batch 3.
