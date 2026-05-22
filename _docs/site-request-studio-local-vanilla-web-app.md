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

- in progress
- target direction agreed
- Phase 0, Phase 1, and Phase 1A implemented
- Phase 2 implemented
- Phase 3 implemented for Docs Viewer manage mode
- Phase 4 in progress with Docs management, analytics tag reads, tag assignment writes, tag alias writes, and tag registry writes routed through the local app server

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

## Local App Server Decision

Use Python for the local Studio app server.

The decision drivers are operational:

- existing Studio write/read services and many generators are already Python
- the first app server mostly needs to serve HTML, JavaScript, CSS, static assets, and runtime config JSON
- Python can proxy or coordinate existing loopback services without introducing a new frontend toolchain
- using Ruby risks preserving the wrong coupling because the goal is to remove Jekyll as the Studio host
- using Node is not justified while the frontend remains vanilla browser modules without bundling or a framework

Ruby should remain available for the public Jekyll build, current docs rendering, and existing Ruby-owned builders until those are intentionally replaced or wrapped.
Node can be reconsidered later only if there is a concrete need for bundling, TypeScript, hot reload, module graph tooling, or desktop-shell packaging.

The Python app server should stay deliberately small:

- serve the local Studio app shell
- serve existing Studio static assets
- expose browser-safe runtime config JSON
- proxy or coordinate existing local services where needed
- avoid becoming a new application framework

## Local Service Architecture Decision

Use one Python Studio app server as the preferred end state.

The app server should own the local Studio HTTP surface:

- serve the Studio app shell
- serve Studio static assets
- expose runtime config JSON
- expose local API routes
- call existing domain modules directly where practical
- start or delegate long-running/background tasks only where needed

Do not make proxying to old sibling HTTP services the default architecture.
A permanent proxy layer would keep two routing models alive and preserve avoidable compatibility work.
During migration, temporary sibling services may remain for routes that have not moved yet, but each migrated workflow should retire the corresponding proxy/sibling dependency where practical.

Preferred migration rule:

- do not proxy by default
- move endpoint ownership into the Python Studio app server as each workflow migrates
- reuse extracted Python domain modules from the current catalogue, docs, analytics, audit, and Studio services
- preserve response contracts where existing frontend code depends on them
- keep temporary proxying narrow, explicit, and retired slice by slice

This is one reason the recent script structural work is useful to pause rather than continue broadly.
The extracted helpers can become app-server modules directly instead of remaining hidden behind old per-service HTTP wrappers.

## Docs Viewer Server Boundary Decision

Keep Docs Viewer as a distinct module and package boundary, but host local Docs Viewer management through the one Python Studio app server by default.

Do not introduce a separate always-running Docs Viewer server for normal Studio use.
That would reintroduce several problems this migration is meant to reduce:

- another local port
- another health and capability surface
- another CORS and loopback policy
- another startup and shutdown path
- another proxy or compatibility layer
- more process decisions in `bin/dev-studio`

The target shape is one local app server with Docs-owned route modules:

```text
Python Studio app server
  /studio/...       Studio shell and views
  /docs/...         Docs Viewer management shell
  /api/docs/...     Docs management APIs
  /api/catalogue/... etc.
```

Docs Viewer should still own its domain boundary:

- browser JavaScript, CSS, and UI text
- source/docs scope config
- generated docs payload contract
- management route module
- write policies and allowlists
- import, rebuild, and search behavior
- public read-only install behavior

For portability, a standalone Docs Viewer server launcher can be considered later for non-Studio installs.
That should be an alternate entrypoint over the same Docs Viewer modules, not the default architecture inside this repo.
The normal Studio path should feel like one local app.

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

## State And Restore Decision

Keep Studio state primarily in app and session state.

Do not make hash/history debug restore a first-order migration requirement.
Current Studio uses URL query state heavily because Jekyll routes made the browser URL the easiest route-state carrier, not because every workflow needs a shareable or restorable URL.

Preferred state model:

- use in-memory app state for active view, modal, selected record, filters, and return context
- use `sessionStorage` only where restoring the last local workspace after refresh is useful
- use explicit navigation APIs such as `navigateTo(view, params)` and `openModal(name, params)`
- treat URL, hash, and history state as optional diagnostic or restore metadata
- add URL/hash restore only for specific high-value cases after the local app shell is proven

The migration should preserve workflow continuity, not every current query parameter.

## First Complex Migration Decision

Use Docs Viewer `/docs/` manage mode as the first complex workflow migration after a small local app shell spike.

The app shell spike should still come first, using a simple read/review surface to prove static asset serving, runtime config JSON, route-ready smoke testing, and basic view mounting outside Jekyll.
After that, `/docs/` manage mode is the right first serious workflow because it is frequently used, fundamental to site maintenance, and directly exercises the architecture this request is trying to prove.

Reasons:

- it targets a current source of Jekyll-regeneration friction
- it exercises local management UI, runtime config, source writes, generated docs payload rebuilds, docs search rebuilds, and service/API ownership
- it clarifies that public `/library/` and `/analysis/` remain read-only Docs Viewer installs
- it moves local Docs management into the Python Studio app server while preserving Docs Viewer portability
- it avoids starting with a catalogue editor whose migration would also carry public catalogue projection risk

Target direction:

- local `/docs/` management is hosted by the Python Studio app server
- public `/library/` and `/analysis/` continue to use read-only Docs Viewer installs
- Docs Viewer remains portable, with management enabled only in local app/server contexts
- Jekyll should not be required to serve the local Docs management shell once this migration lands
- the separate Docs management HTTP server is no longer part of normal `bin/dev-studio` startup, but remains available as an explicit fallback/debug entrypoint

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

## Migration Workflow Guardrails

Treat this request as a major behavior-changing migration even when individual slices try to preserve features.

Use [Development Workflow](/docs/?scope=studio&doc=development-workflow) as the lifecycle guide for every non-trivial slice.
In particular:

- classify each slice before editing: local runtime, Docs Viewer, Studio route behavior, public build surface, generated data, UI/CSS, or workflow documentation
- read the owning docs before changing that surface
- keep implementation scoped to the owning runtime, script, route module, data contract, or UI primitive
- run the smallest verification that proves the changed behavior
- update owning docs and generated artifacts when their source contracts changed
- close each slice with changed files, checks run, generated payload status, risks, and next task

Carry forward the recent JavaScript risk-review rules:

- do not add new responsibilities to large Studio or Docs Viewer route controllers by default
- use the JavaScript maintenance gate before touching files with maintenance score 2, total risk score 6 or higher, or recent churn
- prefer focused owners for rendering, modal lifecycle, service orchestration, validation, result shaping, import/export flow, route-state projection, and domain logic
- run focused browser-module or route smoke checks when behavior moved out of a controller
- update the relevant JavaScript inventory docs only when scores, owners, or follow-up tasks materially changed

Carry forward the recent Python service-refactoring rules:

- keep `studio_app_server.py` as request dispatch and process startup, not a domain module
- add route-family API modules before adding broad behavior to the server entrypoint
- reuse extracted domain modules from catalogue, docs, analytics, audit, and Studio services rather than adding proxy compatibility layers by default
- preserve loopback binding, CORS limits, write allowlists, backups, preview/apply boundaries, and compact activity/log records
- keep focused tests against the owning domain module where practical, with server tests covering HTTP routing and status mapping

Docs and generated-payload follow-through remains explicit:

- source docs under `_docs/` are not the runtime payload
- Studio docs payloads under `assets/data/docs/scopes/studio/...` must be updated before docs output is treated as final
- do not manually rebuild docs payloads when `bin/dev-studio` or the docs watcher is expected to do it
- if generated docs/search payloads are not rebuilt in a slice, state that in close-out

Security and publication checks remain part of the migration:

- do not widen local write paths, CORS origins, or localhost service scope implicitly
- do not add local services that bind beyond loopback
- do not publish Studio routes, Studio app assets, local write surfaces, source-only fields, or local operational docs to dotlineform.com
- use sanitization scans when a slice touches credential handling, logging, local-service writes, generated docs payloads, or docs/examples with system paths

## Commit Points And Change History

Use explicit commit points for this migration.
A commit point is appropriate when a slice has a coherent behavior boundary, targeted verification has passed, docs are updated, and the next slice can start without needing uncommitted context from the previous one.

Good commit points include:

- public published-surface cleanup
- first local app server shell
- first migrated Studio view
- navigation/runtime-config adapter completion
- Docs Viewer management shell or API milestone
- each migrated Docs management workflow
- each route-family migration
- each local-service consolidation milestone
- projection/build contract changes

At every phase end or meaningful commit point:

- update this change request and the implementation plan status
- add a structured `_docs_logs/entries/*.json` entry using `_docs_logs/README.md` and include `change_request_doc_id: site-request-studio-local-vanilla-web-app`
- include related docs and related files that help future Codex sessions trace the decision
- record behavior changes even when features were intended to remain equivalent
- record verification commands or smoke-test results
- state whether generated docs/search payloads were rebuilt or intentionally left to the watcher/manual workflow

Do not combine unrelated route-family migrations into one commit just because they share the same local app server.
Prefer small green commits that leave a clear next slice.

## Implementation Plan

The phased task plan lives in [Local Studio App Implementation Plan](/docs/?scope=studio&doc=local-studio-app-implementation-plan).
Keep this request focused on direction, boundaries, and design decisions.

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

## Related Docs

- [Development Workflow](/docs/?scope=studio&doc=development-workflow)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)
- [Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)
- `_docs_logs/README.md`
- [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Management Current State](/docs/?scope=studio&doc=docs-viewer-management-current)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)

## Change Log Entries

- `change-2026-05-22-added-local-docs-management-ui-smoke`
- `change-2026-05-22-added-public-docs-readonly-smoke`
- `change-2026-05-22-added-local-docs-management-workflow-smoke`
- `change-2026-05-22-completed-local-studio-config-navigation-adapter`
- `change-2026-05-22-migrated-docs-management-api-to-local-studio-app`
- `change-2026-05-22-added-local-studio-app-to-dev-runner`
- `change-2026-05-22-started-local-studio-app-migration`
