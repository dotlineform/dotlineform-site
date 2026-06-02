---
doc_id: site-request-public-route-simplification
title: Public Route Simplification Request
added_date: 2026-06-01
last_updated: 2026-06-01
ui_status: done
parent_id: change-requests
viewable: true
---
# Public Route Simplification Request

Status:

- done
- The cleaner public route model has been implemented while Jekyll remains the public preview/build layer.
- The child task document records implementation notes, verification, and remaining Jekyll collection-output removal conditions.

## Task Tracker

Use [Public Route Simplification Tasks](/docs/?scope=studio&doc=site-request-public-route-simplification-tasks) for the implementation sequence, task status, and verification checklist.

## Summary

Review and simplify the public catalogue route model before replacing Jekyll.

The current public site has thousands of per-record route stubs for works, series, moments, and work details.
Those routes were a practical fit for Jekyll collections, but they may not match the current user need.
The public runtime already uses generated JSON payloads and query/state parameters for much of its behavior, so the next route model can be smaller and more app-like.

The goal is to reduce public route surface and future builder complexity while keeping the user experience clear.
Old inbound URL compatibility is not required.
The site is public but not widely advertised, so broken historical links are acceptable if the site has clean 404 behavior and the current navigation paths work.

This request should be completed while Jekyll is still the public preview/build layer.
Jekyll can render a smaller set of fixed shell routes, so the route model can be simplified against the known current build before the public static-site builder is introduced.
That keeps route behavior changes separate from the later build-system replacement.

## Context

[Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) should start from a cleaner public route model rather than treating the current Jekyll collection structure as permanent.

Current public route families include:

- index and shell routes such as `/`, `/about/`, `/series/`, `/works/`, `/recent/`, `/catalogue/search/`, `/library/`, and `/analysis/`
- per-work routes under `/works/<work_id>/`
- per-series routes under `/series/<series_id>/`
- per-moment routes under `/moments/<moment_id>/`
- per-work-detail routes under `/work_details/<detail_uid>/`

The per-record routes currently exist mainly because Jekyll collections make them easy to generate.
They also create a large build surface and make the future static builder look more complex than the public experience may require.

In the current implementation, the route dependency is spread across browser runtime helpers, Liquid route shells, generated payload URL fields, and search result rendering.
The route simplification work should concentrate those responsibilities before any Jekyll replacement work begins.

## Goals

- implement the canonical public route model for catalogue browsing before the Jekyll replacement
- move works, series state, and work details to query/state-driven route shells where that reduces route count without harming current navigation
- reduce route count and build complexity when there is no clear user-facing reason to keep per-record pages
- preserve current first-party navigation flows from public indexes, grids, search, and Docs Viewer references
- define a clean public `404.html` behavior for retired or unknown routes
- update route-generation, search-result, catalogue-runtime, and public-link helper expectations only where the chosen model needs them
- give the later static-site builder a smaller and explicit route contract
- keep Jekyll as the preview/build layer while this route behavior is changed, so the later build migration starts from a stable route contract

## Non-Goals

- preserving all old inbound public URLs
- adding compatibility redirects for every current per-record route
- changing the public visual design except where route simplification requires small navigation or empty-state adjustments
- replacing Jekyll in this request; that belongs to [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build)
- designing around the later static builder's internals; this request should define route behavior independently of how the future builder renders files
- changing generated catalogue data schemas unless the chosen navigation model genuinely needs a narrow URL or state-field update
- changing Library or Analysis Docs Viewer route ownership unless a public-link dependency needs adjustment

## Design Decisions

Use these decisions for the implementation task list:

- keep stable top-level public shells for `/series/`, `/works/`, `/recent/`, `/catalogue/search/`, `/library/`, and `/analysis/`
- prefer query/state-driven catalogue record views where this preserves user workflows with fewer generated HTML files
- avoid generating per-record route stubs solely to keep URLs readable
- do not add broad compatibility redirect tables for old per-record URLs
- provide a clean `404.html` with simple "page unavailable" copy and a link back to `/series/`, the current public home/root experience
- keep URL/state contracts as small as possible; use query parameters when they are the simplest way to restore the intended view, but do not replicate current URL fields or path shapes without a current user need
- dynamically derive public URLs in runtime helpers from record id plus route state; if persistent generated URL fields exist, remove them unless a documented non-derivable exception is found
- centralize public URL construction and route-state parsing before the static-builder migration; route strings should not be assembled independently across page scripts
- use Jekyll only as the existing rendering/preview mechanism during this request; do not make the route model depend on Jekyll collections as a durable contract

## Route Design

Preferred canonical shape:

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

Design rationale:

- use one fixed shell per public record family instead of one generated HTML page per record
- keep copied URLs restorable through explicit query parameters
- treat query parameters as route state, not as compatibility shims for old paths
- treat selected series as state in the existing `/series/` catalogue index shell rather than as a separate series page family
- keep the historically named `/series/` route as the single public catalogue entry point for works, series, and moments unless route naming becomes a real blocker
- keep moments discoverable through the `/series/` catalogue index mode rather than adding moments back to the top navigation
- make `/moments/` an explicit recovery route to `/series/?mode=moments`, with a visible fallback link, rather than allowing local directory listings or accidental 404 behavior
- individual moment pages can remain path routes for now because the current interaction opens a selected moment from the catalogue index grid/list
- keep work details as selected state in the `/work-details/` shell for this route simplification, with explicit links back to parent work context
- keep first-party navigation context, such as selected series, in query parameters only when it changes visible behavior
- keep important return paths in explicit in-page back links rather than depending on browser history
- prefer `/work-details/` over the legacy `/work_details/` spelling because old inbound compatibility is not required
- avoid preserving path-style routes solely because they are more readable
- centralize URL construction and parsing in public runtime helpers so templates, search, generated payloads, and Studio previews do not each invent route shapes
- use `assets/js/public-catalogue-runtime.js` as the first likely owner for the browser-side route helper contract unless implementation review shows a smaller dedicated route module is cleaner
- treat browser history as best-effort; predictable back/forward behavior is useful, but explicit page back links carry the navigation context that matters

## Current Surfaces To Review

The simplified route model must account for these current route assumptions:

- `assets/js/public-catalogue-runtime.js`
  owns shared public helpers such as `workUrl(...)`, `workDetailUrl(...)`, series back links, and series prev/next links
- `series/index.md`
  renders the public catalogue index shell and currently links into per-work and per-series routes
- `works/index.md`
  renders the works list shell and currently links into per-work and per-series routes
- `recent/index.md`
  links recent works and series into per-record routes
- `_layouts/work.html`
  currently gets `work_id` from the Jekyll page slug and builds detail links under `/work_details/<detail_uid>/`
- `_layouts/series.html`
  currently gets `series_id` from the Jekyll page slug and builds work links under `/works/<work_id>/`
- `_layouts/work_details.html`
  currently gets `detail_uid` from the Jekyll page slug and builds back/prev/next links around `/works/<work_id>/` and `/work_details/<detail_uid>/`
- `_layouts/moment.html`
  currently gets moment identity from the Jekyll page slug
- `/moments/`
  currently has inconsistent behavior: local preview may expose a directory listing while the public site returns 404; target behavior is a small redirect/recovery page to `/series/?mode=moments`
- catalogue search runtime
  currently emits path-style result URLs for works, series, moments, or work details
- generated public catalogue payloads
  should not store derivable public URLs; if URL fields or route assumptions are found, remove or replace them with runtime-derived helpers unless a documented exception is required
- Docs Viewer semantic references
  publish as normal public links in Library or Analysis docs, so they must move to the new catalogue route model without exposing special-link behavior to the user
- Studio public-link helpers
  may need to resolve public preview links against the new route contract

The durable outcome should be a small public route helper contract driven by actual navigation and share-state needs.
Generated public payloads should avoid persistent URL fields because URLs are route projections, not record data.
Browser-side route building and route parsing should live together, so selected work, selected series, selected detail, selected moment, and navigation context are handled consistently.

The later static-builder request should not need to know the old route model.
It should consume only the route contract produced by this request.

## Acceptance Criteria For The Spec

- the canonical public route model is documented before Jekyll replacement begins
- old inbound URL compatibility is explicitly not required
- first-party public navigation still reaches works, series, moments, work details, catalogue search, Library, and Analysis as needed
- moments remain part of the single catalogue entry point, not a top-nav route family
- `/moments/` no longer exposes a local directory listing and recovers to `/series/?mode=moments`
- generated public URL fields are removed if they exist, unless a documented non-derivable exception is required
- runtime URL helpers own derivable URLs and route-state parsing where practical
- important return navigation is available through explicit in-page links, with browser history treated as useful but not primary
- unknown retired routes resolve to a clean `404.html` with a `/series/` recovery link
- the later public static-site builder can enumerate a smaller, explicit route set
