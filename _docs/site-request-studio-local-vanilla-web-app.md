---
doc_id: site-request-studio-local-vanilla-web-app
title: Studio Local Vanilla Web App Request
added_date: 2026-05-22
last_updated: 2026-05-22
ui_status: in-progress
parent_id: change-requests
sort_order: 10000
viewable: true
---
# Studio Local Vanilla Web App Request

Status:

- proposed
- target direction agreed
- implementation not started

Related migration documentation under: [Local Studio App](/docs/?scope=studio&mode=manage&doc=local-studio-app)

## Summary

Studio should become a local vanilla web app, not a Jekyll section and not a frontend-framework rewrite.

The current Studio implementation is already a local service-backed application in practice.
It is hosted by Jekyll route pages, Liquid config injection, and public/dev config overlays, but its functional workflows depend on `bin/dev-studio` and localhost services.
That hosting model creates more problems than it solves for Studio: route regeneration, `_site` state, static-page URL constraints, Jekyll/Liquid coupling, and public shells that are not useful on dotlineform.com.

The strategic move is to keep the existing vanilla browser modules, CSS conventions, local services, and workflow behavior, while replacing Jekyll as the Studio application host.
Jekyll can remain the public site publisher.

## Core Decision

Use a local vanilla web app for Studio.

Do not use this migration to rewrite Studio in React, Vue, Svelte, Swift, or another native/frontend framework.
Those options might have had tradeoffs earlier, but they now carry too much migration and revalidation cost for the current developer constraints.
The current maintenance problem is Jekyll coupling, not the absence of a UI framework.

## Product Boundary

Public site:

- owns dotlineform.com publishing
- includes intentionally public catalogue pages, works, series, moments, public assets, public search, `/library/`, and `/analysis/`
- keeps `/library/` and `/analysis/` as public read-only Docs Viewer installs
- should not publish Studio routes, Studio app assets, local write surfaces, or local operational docs at `/docs/`

Studio:

- is a local application and workflow shell
- owns canonical authoring/source data, local editors, local services, audits, imports, exports, build orchestration, and unpublished operational docs
- generates public projections for the public site
- can remain in this repo until the boundaries settle

Docs Viewer:

- remains a reusable viewer/manager module
- supports public read-only installs such as `/library/` and `/analysis/`
- supports local management mode for Studio docs and other configured docs scopes
- should not require Studio pages to be Jekyll-managed

## Public Does Not Mean Private

This request uses `public` to mean publicly served on dotlineform.com, not hidden in a private repository.

The repositories can remain public.
Canonical data can include fields that are not published, as long as generated public projections exclude them.
For catalogue data, [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source) already states the rule:

- source-only fields such as `notes` and `provenance` stay out of public projections unless an explicit runtime contract includes them

The important boundary is:

```text
canonical source data
  -> Studio builders and validators
  -> public projections
  -> Jekyll public site
```

## Navigation Principle

Preserve user workflow navigation, not current URL mechanics.

For Studio users, navigation means:

- clicking a button opens the expected page, panel, modal, or workflow
- record context is preserved where needed
- return state works for lists, editors, and previews
- save, build, import, delete, and audit workflows keep their current behavior

The current URL/query model is an implementation detail of the Jekyll route host.
A local app may use internal app state, browser history, hash state, session storage, or a small router abstraction.
Stable `/studio/...` URLs are useful for debugging and migration, but they are not the product contract.

## Reuse Strategy

Reuse existing Studio JavaScript and CSS wherever practical.

Current route controllers are browser ES modules that generally bind to stable DOM ids, classes, and `data-role` contracts.
The migration should preserve those contracts first and replace only the Jekyll/Liquid route shell around them.

Reusable as-is or with small adapters:

- shared Studio data loaders and shapers
- service transport helpers
- route-ready and busy-state helpers
- field/render modules that receive DOM roots or explicit config
- CSS primitives and route-local styles
- focused workflow modules created by recent JavaScript refactoring

Needs adaptation:

- route files currently written as Jekyll Markdown/Liquid
- `relative_url` and `site.*` config injection
- `data-*` attributes generated from `_config.yml` and `_data`
- query-string based initial state
- `window.location` navigation between Studio pages
- tests that assume Jekyll-served `/studio/...` routes

Avoid:

- rewriting working route controllers only to match a new app architecture
- replacing established CSS/component conventions without a concrete maintenance reason
- converting every page into a single-page workflow in the first slice
- preserving URL query state where a local app state model is simpler

## Existing Site Work Before Migration

Before moving Studio off Jekyll, clean up what the public site intentionally publishes.
This reduces migration noise and creates a target contract for the eventual Studio/public split.

Recommended prework:

1. Define a public published-surface manifest.
2. Keep `/library/` and `/analysis/` public read-only.
3. Exclude `/studio/` routes from public builds.
4. Exclude `assets/studio/` app assets and Studio-only generated data from public builds.
5. Exclude `/docs/` from public builds unless a curated public read-only docs install is explicitly required.
6. Exclude Studio docs generated payloads and Studio docs search from public builds.
7. Add a lightweight build/audit check that public output does not contain Studio routes or Studio-only assets.
8. Keep local dev config able to serve current Studio while the local app migration proceeds.

This prework should be behavior-preserving for public users.
It should not move canonical data yet.

## CSS Boundary Benefit

Moving Studio out of the public Jekyll section should also simplify CSS ownership.

Today, public `assets/css/main.css` and related site styles have to coexist with Studio-admin surfaces because Studio is rendered as part of the same Jekyll site.
After the public/local boundary is cleaned up, CSS can be organized by runtime responsibility:

- public site CSS for public catalogue pages, work/series/moment pages, public navigation, and public read-only routes
- Docs Viewer CSS for the portable viewer shell, read-only document UI, and local management UI where management mode is enabled
- Studio CSS for the local app shell, editors, modals, dense admin lists, status panels, import/export flows, and audit tooling

This should make later CSS refactoring safer.
Rules can be judged by which runtime owns them rather than by whether they happen to be loaded through the current Jekyll layout.
It also reduces the long-term responsibility of public `main.css`, because Studio-only primitives do not need to remain available to dotlineform.com.

## Refactoring Pause Decision

Broad script and JavaScript risk-reduction work can pause.

The high-value script structural review tracks have already reduced the largest local-service risks.
Recent JavaScript work has created clearer route/module boundaries and reusable owners.
Continuing broad refactoring before the host-runtime decision is implemented risks optimizing for the current Jekyll shape rather than the next Studio shape.

Pause by default:

- inventory-driven JavaScript extractions that are not needed for a migration slice
- broad Python/Ruby service reshuffles without a concrete migration blocker
- route cleanup whose only purpose is to improve Jekyll-hosted page organization
- package or repo split work before the local app boundary is proven

Continue only when needed:

- a migration slice touches a high-risk controller and needs a focused owner
- a service endpoint must be stabilized or adapted for the local app server
- tests need a small extraction to verify behavior outside Jekyll
- public projection safety requires a specific source/projection fix
- a known bug blocks current Studio usage

The migration should use the existing JavaScript maintenance gate when it changes high-risk files, but it should not keep reducing scores as a standalone goal.

## Implementation Phases

### Phase 0: Published Surface Cleanup

Goal:

- make the current public build reflect what dotlineform.com should actually expose
- keep `/library/` and `/analysis/` public read-only

Tasks:

- document the public published-surface manifest
- remove or exclude public `/studio/` output
- remove or exclude public `/docs/` output unless a curated read-only docs install is intentionally defined
- exclude Studio-only assets and generated Studio docs/search payloads from public output
- add or update checks so accidental public Studio output is visible
- decide if `bin/dev-studio` remains unchanged or if a small config split is needed

Acceptance:

- public users can still access intended public catalogue pages, `/library/`, and `/analysis/`
- public builds no longer produce non-functional Studio shells
- public builds no longer expose local-management docs route output
- local dev Studio still runs through the current path until replacement slices land

### Phase 1: Local App Shell Spike

Goal:

- prove a non-Jekyll Studio host can serve one existing Studio view without changing its workflow

Tasks:

- add a small local Studio app server or extend an existing local server in a scoped way
- serve a single app shell at a local Studio URL
- serve existing Studio CSS and JS assets directly
- provide a browser-safe runtime config JSON that replaces the Liquid values needed by the chosen route
- mount one simple route/view, preferably a low-write review surface such as Studio Works, Activity, or a dashboard
- preserve current ids, classes, and `data-role` hooks for that view

Acceptance:

- the chosen view loads without Jekyll
- existing browser module behavior is reused rather than rewritten
- route-ready state still becomes inspectable for smoke tests
- the spike identifies which Jekyll assumptions must become app-server config or navigation adapters

### Phase 2: Config And Navigation Adapter

Goal:

- replace Jekyll route/query assumptions with explicit Studio app services

Tasks:

- define a Studio runtime config shape for media bases, thumb bases, pipeline variants, UI text paths, docs links, and service endpoints
- add a navigation adapter with methods such as `navigateTo(view, params)`, `openModal(name, params)`, and return-context helpers
- add an initial-state adapter that can read URL state during transition but does not require it as the long-term owner
- centralize app-shell nav labels and view ids outside Jekyll front matter
- keep compatibility with existing route controllers until each route is migrated

Acceptance:

- migrated views do not need Liquid to receive runtime config
- migrated views can navigate by app state rather than hardcoded `window.location` URLs
- current URL query behavior can remain as a transitional input, not the product contract

### Phase 3: Representative Route Migration

Goal:

- prove both simple and complex Studio workflows can run in the local app shell

Tasks:

- migrate one simple/review route
- migrate one complex editor route, likely Catalogue Work Editor or Catalogue Series Editor
- preserve current user-facing workflow behavior
- keep existing write endpoints stable or proxy them without changing response contracts
- update focused smoke tests to run against the local app host
- record any controllers that need small ownership extractions before further migration

Acceptance:

- one complex editor can create/open/save through the local app shell
- route-local behavior is preserved without Jekyll page generation
- test coverage proves the migrated view can boot, load data, and reach route-ready state
- no frontend-framework rewrite has been introduced

### Phase 4: Local Service Integration

Goal:

- make Studio startup and service access coherent without tying app serving to Jekyll

Tasks:

- decide whether the local app server proxies existing write services or starts them as sibling processes
- keep loopback binding, CORS limits, write allowlists, and compact logs
- preserve existing service endpoint contracts during the first migration
- split `bin/dev-studio` into separate responsibilities if needed:
  - start Studio local app
  - start local write/read services
  - optionally preview/build the public Jekyll site
- keep public-site preview explicit rather than required for using Studio

Acceptance:

- Studio can run locally without Jekyll serve
- Jekyll public preview/build remains available as a separate action
- local write services retain existing safety constraints

### Phase 5: Route Family Migration

Goal:

- move remaining Studio surfaces from Jekyll route pages into the local app shell

Tasks:

- migrate catalogue editors and dashboards
- migrate analytics/tag routes
- migrate data-sharing routes
- migrate audit and project-state routes
- migrate Docs management entry points while keeping Docs Viewer portable
- remove or retire Jekyll Studio route files after their local app replacements are verified
- keep old route redirects only if useful for local transitional ergonomics

Acceptance:

- all active Studio workflows run through the local app shell
- Jekyll no longer owns Studio page rendering
- existing workflows, labels, service effects, and generated outputs remain stable unless explicitly changed

### Phase 6: Projection And Build Contract

Goal:

- make the canonical-source to public-projection boundary explicit enough for a future repo split

Tasks:

- document canonical source families and their public projections
- distinguish public projections, Studio projections, and Docs Viewer payloads
- add checks for source-only fields leaking into public projections
- ensure Jekyll consumes public projections rather than Studio-only data
- keep generated output paths boring and explicit

Acceptance:

- public Jekyll builds depend only on intended public source/projection files
- source-only fields are allowed in canonical data but excluded from public runtime artifacts unless a runtime contract includes them
- the future site/studio repo boundary is visible even while both remain in one repo

### Phase 7: Optional Repo Split Decision

Goal:

- decide whether a separate Studio repo is worth the operational cost after the local app boundary is stable

Tasks:

- review what files now belong to public site, Studio app, canonical data, Docs Viewer, and generated outputs
- decide whether to keep one repo, split into public-site and Studio repos, or extract Docs Viewer first
- avoid splitting only for tidiness
- require a concrete benefit such as simpler deployment, clearer publish artifacts, or easier local app maintenance

Acceptance:

- repo split is a separate decision, not a prerequisite for local app migration
- if split, the publish/export contract is already proven

## Non-Goals

- do not rewrite Studio in a frontend framework
- do not build a native app shell in this request
- do not move canonical data out of the repo before the projection boundary is clear
- do not redesign all local write service contracts during the first app-shell migration
- do not make stable Studio URLs a primary user-facing requirement
- do not continue broad refactoring just because inventory scores can still improve

## Verification Strategy

For planning/docs-only slices:

- source review is enough unless generated docs payloads are intentionally rebuilt

For public build cleanup:

- run a Jekyll build to a separate destination
- inspect output for absence of `/studio/`, `assets/studio/`, public `/docs/`, and Studio docs/search payloads
- smoke intended public routes including `/library/` and `/analysis/`

For local app slices:

- run syntax/import checks for touched JavaScript modules
- run focused Playwright smoke tests against the local app host
- verify route-ready state for migrated views
- verify affected save/build/read workflows against existing local service contracts
- keep public Jekyll build checks separate from Studio app checks

For projection-contract slices:

- add focused leak checks for source-only fields
- verify generated public JSON/search payloads
- verify representative public pages consume public projections only

## Open Questions

- Should the local app server be Python, Ruby, or Node?
- Should existing write services stay as sibling processes or be proxied through one app server?
- Should the local app use hash/history state for debug restore, or keep state mostly in memory/session storage?
- Which route should be the first complex editor migration?
- Should `/docs/` management remain a Docs Viewer route hosted by the local app, or continue as a separate local viewer shell during transition?

## Related Docs

- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)
- [Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)
- [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Management Current State](/docs/?scope=studio&doc=docs-viewer-management-current)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
