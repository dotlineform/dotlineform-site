---
doc_id: public-route-model
title: Public Route Model
added_date: 2026-06-02
last_updated: 2026-06-02
ui_status: stable
parent_id: architecture
viewable: true
---
# Public Route Model

This document is the durable route contract for the public site.

## Route Principles

- keep stable top-level public shells for `/series/`, `/works/`, `/recent/`, `/catalogue/search/`, `/library/`, and `/analysis/`
- prefer query/state-driven catalogue record views where this preserves user workflows with fewer generated HTML files
- avoid generating per-record route stubs solely to keep URLs readable
- do not add broad compatibility redirect tables for old per-record URLs
- provide a clean `404.html` with simple "page unavailable" copy and a link back to `/series/`, the current public home/root experience
- keep URL/state contracts as small as possible; use query parameters when they are the simplest way to restore the intended view
- dynamically derive public URLs in runtime helpers from record id plus route state
- avoid persistent generated URL fields unless a documented non-derivable exception is required
- centralize public URL construction and route-state parsing in `assets/js/public-catalogue-runtime.js` or a successor route-helper module
- route strings should not be assembled independently across page scripts, catalogue search rendering, generated payloads, Docs Viewer semantic references, or Studio public-link helpers
- do not make the route model depend on Jekyll collections or generated route stubs as durable contracts

## Canonical Routes

```text
/                                  public home
/about/                            about page
/recent/                           recent public catalogue updates

/series/                           catalogue/series index shell
/series/?series=009                selected/filtered series state in the catalogue index shell
/series/?mode=moments              moments browse state in the catalogue index shell

/works/                            works list shell
/works/?work=00001                 selected work view
/works/?work=00001&series=009      selected work with series navigation context

/work-details/                     work-detail shell
/work-details/?detail=00001-001    selected work detail view

/moments/                          explicit recovery route to /series/?mode=moments
/moments/a-doll-story/             individual moment page

/catalogue/search/                 public catalogue search shell
/library/                          public read-only Library Docs Viewer install
/analysis/                         public read-only Analysis Docs Viewer install
/404.html                          clean recovery page for unknown or retired routes
```

The public static-site builder should emit fixed route shells for the canonical shell routes and enumerate individual moment pages from public moment records or generated public moment data.
It should not generate one HTML page per work, series, or work detail.

## Retired Routes

Old inbound URL compatibility is intentionally unsupported.
Do not add compatibility redirects, aliases, or broad fallback tables for retired path-style routes.

Retired first-party public routes include:

- `/works/<work_id>/`
- `/series/<series_id>/`
- `/work_details/<detail_uid>/`

`/work-details/` is the canonical spelling for the work-detail shell.
`/work_details/` is legacy and should not be restored.

`/palette/` is not part of the public-site route model.
Palette inspection is owned by the Admin-hosted UI Catalogue at `/admin/ui-catalogue/palette/`.

## Route-State Semantics

Query parameters are route state, not compatibility shims for old paths.

- `series` on `/series/` selects or filters a series in the catalogue index shell.
- `mode=moments` on `/series/` restores moments browsing.
- `work` on `/works/` selects a work in the works shell.
- `series` on `/works/` preserves visible series navigation context for a selected work.
- `detail` on `/work-details/` selects a work detail in the work-detail shell.

Important return paths should be represented by explicit in-page links.
Browser history is useful but should not be the primary mechanism for required navigation context.

## Moment Pages

Individual moment pages may remain path routes because the current interaction opens selected moments from the catalogue moments grid/list.
They should be generated from public moment records or generated public moment data, not from Jekyll `_moments` stubs.

`/moments/` is a recovery route to `/series/?mode=moments`.
It should not expose a directory listing or accidental 404 behavior.

## URL Ownership

Public route construction and route-state parsing are owned by `assets/js/public-catalogue-runtime.js` unless implementation creates a smaller dedicated public route-helper module.

Consumers should derive public routes through that contract or its Studio equivalent:

- public catalogue shells
- recent links
- catalogue search rendering
- Docs Viewer semantic reference output for public links
- Studio preview/public-link helpers

Generated public catalogue payloads should not serialize derivable route URLs such as work, series, work-detail, moment, or search-result `href` fields unless a documented non-derivable exception is required.

## Static Builder Contract

The public static-site builder should consume this route model directly.
It should generate:

- fixed public route shell HTML
- individual moment page HTML
- `404.html`
- public route assets and generated public data required by those shells

It should not consume `_works/`, `_series/`, `_work_details/`, or `_moments` as route-input contracts.
Those Jekyll collection outputs are build-layer artifacts only while Jekyll remains the public build layer and should disappear when the static builder becomes production.
