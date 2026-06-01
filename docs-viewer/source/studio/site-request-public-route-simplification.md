---
doc_id: site-request-public-route-simplification
title: Public Route Simplification Request
added_date: 2026-06-01
last_updated: 2026-06-01
ui_status: draft
parent_id: change-requests
viewable: true
---
# Public Route Simplification Request

Status:

- draft
- This request should define the cleaner public route model before the public static-site builder migration starts.
- Do not create an implementation task list until the route model and 404 behavior are agreed.

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

- define the canonical public route model for catalogue browsing before the Jekyll replacement
- decide whether works, series, moments, and work details need dedicated path routes or can use query/state-driven route shells
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

## Proposed Defaults

Use these defaults unless route review finds a better model:

- keep stable top-level public shells for `/series/`, `/works/`, `/recent/`, `/catalogue/search/`, `/library/`, and `/analysis/`
- prefer query/state-driven catalogue record views where this preserves user workflows with fewer generated HTML files
- avoid generating per-record route stubs solely to keep URLs readable
- do not add broad compatibility redirect tables for old per-record URLs
- provide a clean `404.html` with a short route back to current public navigation
- keep URL/state contracts as small as possible; use query parameters when they are the simplest way to restore the intended view, but do not replicate current URL fields or path shapes without a current user need
- prefer runtime URL builders over storing redundant generated URL fields when a URL can be derived from record id plus route state
- use Jekyll only as the existing rendering/preview mechanism during this request; do not make the route model depend on Jekyll collections as a durable contract

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
- catalogue search runtime
  currently emits path-style result URLs for works, series, moments, or work details
- generated public catalogue payloads
  may contain URL fields or route assumptions; review whether each is still needed rather than carrying fields forward by default
- Docs Viewer semantic references
  may link from public Library or Analysis docs to catalogue work, series, or moment targets
- Studio public-link helpers
  may need to resolve public preview links against the new route contract

The durable outcome should be a small public route helper contract driven by actual navigation and share-state needs.
Generated URL fields should be retained only when they remove real complexity or represent data the runtime cannot cheaply derive.

## Implementation Sequence Shape

The implementation task list should follow this order once the route model is agreed:

1. Define the canonical route helper contract for works, series, work details, moments, and index routes.
2. Add or adapt fixed Jekyll shell routes for the new canonical route model.
3. Update browser runtime helpers to build and parse the new route URLs.
4. Update public shell scripts so record identity comes from query/state parameters where needed rather than `page.slug`.
5. Update catalogue search, generated URL fields, Docs Viewer references, and Studio public-link helpers only where they have a current navigation requirement.
6. Stop relying on per-record Jekyll collection outputs for first-party navigation.
7. Add or update `404.html` for retired and unknown route recovery.
8. Run public route smoke checks while Jekyll is still the build baseline.
9. Document the resulting route contract for the later public static-site builder.

The later static-builder request should not need to know the old route model.
It should consume only the route contract produced by this request.

## Route Model Questions

Answer these before creating an implementation task list.

1. Work pages:
   Should individual works keep `/works/<work_id>/`, move to `/works/?work=<work_id>`, or use another shell/query shape?

2. Series pages:
   Should individual series keep `/series/<series_id>/`, move to `/series/?series=<series_id>`, or merge into the existing series index state model?

3. Work detail pages:
   Should work details remain independent public pages, become state within a work page, or use a single `/work_details/?detail=<detail_uid>` shell?

4. Moments:
   Should moments keep individual readable paths, move to one route shell, or be represented through the same catalogue browse/search experience as works and series?

5. Search and generated URL fields:
   Which generated payload fields currently store public URLs, and are they still needed?
   If a URL can be derived from id plus route state, prefer deriving it in the runtime helper rather than preserving a generated field.

6. Public runtime helpers:
   Which JavaScript helpers build public URLs, and should they centralize on one canonical route builder before the static-builder migration?

7. Docs Viewer semantic references:
   Do public Library or Analysis docs link to catalogue work, series, or moment URLs that must move to the new model?

8. Browser history and sharing:
   Which views actually need restorable copied URLs, and which transient navigation context can remain local UI state?

9. 404 behavior:
   What should `404.html` show, and which current navigation target should it offer as the primary recovery path?

10. Verification:
    Which public smoke tests should prove that index navigation, search-result navigation, series navigation, detail opening, browser back/forward, and unknown routes behave correctly?

## Acceptance Criteria For The Spec

- the canonical public route model is documented before Jekyll replacement begins
- old inbound URL compatibility is explicitly not required
- first-party public navigation still reaches works, series, moments, work details, catalogue search, Library, and Analysis as needed
- generated public URL fields are removed or retained based on current navigation needs, not on preserving old route shapes
- runtime URL helpers own derivable URLs and route-state parsing where practical
- unknown retired routes resolve to a clean 404 experience
- the later public static-site builder can enumerate a smaller, explicit route set
