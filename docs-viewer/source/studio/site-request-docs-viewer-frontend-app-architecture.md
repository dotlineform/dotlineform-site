---
doc_id: site-request-docs-viewer-frontend-app-architecture
title: Docs Viewer Front-End App Architecture Request
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: in-progress
parent_id: change-requests
sort_order: 14180
viewable: true
---
# Docs Viewer Front-End App Architecture Request

Status:

- planned

This request is the parent policy and benefits analysis for the next Docs Viewer frontend-app architecture work.
Implementation should happen in child task documents, following the pattern used by the closed [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The previous request moved Docs Viewer away from Liquid-owned shell markup and a monolithic entrypoint.
That work produced focused owners for boot, route config, access projection, route/document workflow, search/recent callbacks, bookmarks, document rendering, generated-data reads, document-index projection, info-panel coordination, hosted views, and lazy management loading.

The next goal is more structural: make Docs Viewer clearly recognisable as a frontend app, not a set of migrated helper modules held together by `docs-viewer-app-runtime.js`.

## Problem

The current runtime is materially better, but the architecture is still transitional.

`docs-viewer/runtime/js/docs-viewer-app-runtime.js` still bridges old and new shapes by:

- defining broad shared state defaults
- constructing all major controllers
- assembling cross-controller callbacks
- coordinating config handoff
- binding top-level events
- sequencing initial load
- returning a small legacy runtime API

More small helper splits would reduce line count but would not necessarily make the system more app-like.
The next work should create explicit frontend-app concepts: app session, state domains, service adapters, lifecycle phases, controller/view ownership, and public/manage app contexts.

## Why This Matters

The current model often works by letting a module inspect raw flags or state values and then decide what to do locally.
That is manageable while behavior is simple, but the public/manage boundary can blur quickly.

The info panel is the clearest example.
The original requirement sounded like one feature: add an info panel.
Once it exists, a natural follow-up is that the panel should show different fields in public read-only routes and local manage mode.
That single feature can become several different contracts:

- public metadata info: presentation-oriented and public-safe
- manage metadata info: operational fields and source/config clues
- local diagnostics: service status, generated-read state, rebuild context, or local-only paths
- future semantic/reference info: derived data that may be manage-only before it is public-safe

If this is handled by one view with scattered `if managementMode` or `if allowManagement` checks, it becomes hard to tell which fields are public-safe, which fields require backend capability, and which fields are only local operational details.
The same pattern can happen with reports, side panels, document actions, search result affordances, bookmarks, diagnostics, and future editor surfaces.

The architecture direction is to move from:

```text
read raw flags and broad state -> decide behavior locally
```

to:

```text
receive an explicit app context or view model -> render/act according to that contract
```

For the info panel, that might mean the same panel slot hosts separate or separately-shaped views:

- `metadata-public-info`
- `metadata-manage-info`
- `source-diagnostics`
- `semantic-references`

Those views may share render helpers, but they should not pretend to be one implementation if their safety, data, and purpose differ.
Route/app context should decide which views are available.
Each view should receive a clear data shape, such as a public-safe metadata view model or a manage-mode metadata view model, rather than reaching into broad runtime state to rediscover what mode means.

This is the policy reason for app context, state-domain facades, service adapters, and view models.
They make public vs manage behavior visible in data structures and contracts instead of hidden in scattered conditionals.

## Benefits

- public and manage behavior can diverge intentionally without becoming accidental forks
- public-safe fields and manage-only fields are easier to audit
- future views can be added to a named panel slot without expanding one overloaded implementation
- tests can assert view-model contracts instead of clicking through every local flag combination
- optional or local-only capabilities can be omitted cleanly from public installs
- implementation decisions become easier to document because the app context and view model carry the policy

## Goal

Create a Docs Viewer frontend-app architecture that is easy to explain:

- route shells provide mounts and route identity
- app boot resolves route config and creates an app session
- the app session owns current route/scope/context state through named domains
- service adapters own generated/config/backend reads and writes
- controllers and hosted views attach to explicit lifecycle inputs
- public read-only and local manage mode are two app contexts, not two separate runtimes
- `docs-viewer-app-runtime.js` becomes ordinary startup wiring or disappears into a clearer app composition module

## Non-Goals

- do not add source editor features in this request
- do not add semantic-reference editing or visualization features in this request
- do not introduce a plugin architecture, marketplace, sandbox, or package system
- do not replace the Python management backend
- do not change generated docs/search payload schemas unless a focused follow-up proves it is required
- do not rewrite all controllers in one pass
- do not move management write authority into browser code
- do not fork public and manage runtimes

## Target Shape

The target frontend app should have these recognisable parts:

```text
Docs Viewer app boot
  resolves route config
  initializes shell mounts
  creates app session
  starts app composition

App session
  route state
  scope/config state
  document-index state
  selected-document state
  search/recent state
  bookmark state
  panel/view state
  management state
  busy/status state

Service adapters
  generated-data reader
  viewer config reader
  search index reader
  report registry/loader
  bookmark storage
  management backend client

Controllers and views
  route workflow
  document controller
  index/sidebar renderer
  search/recent controller
  bookmark controller
  panel layout and hosted views
  management controller in manage context

App composition
  wires session domains, services, controllers, and lifecycle phases
```

This shape does not require a framework.
It does require explicit ownership and contracts.

## Architecture Principles

- Move complete concepts, not stray helpers.
- Prefer state-domain facades over passing the full broad `state` object to every owner.
- Keep service adapters separate from rendering and controller event logic.
- Treat backend/service contracts as first-class architecture, not as consequences of browser refactors.
- Keep route/document workflow, search/recent, bookmarks, document rendering, management workflows, and hosted-view lifecycle in their current focused owners unless a slice defines a better complete owner.
- Preserve public read-only routes as first-class app contexts.
- Preserve manage mode as a first-class local editing app context with backend-enforced write authority.
- Keep route shells thin: mounts, route id/config URL, CSS links, and entry script.
- Avoid generic architecture where a concrete Docs Viewer concept is enough.

## Backend Co-Evolution Policy

The next phase should not focus on frontend architecture while quietly building backend debt or permanent compatibility layers.
Frontend app concepts and backend/service contracts need to move together.

Each child task must explicitly answer:

- What frontend app concept is being introduced or clarified?
- What backend capability, generated-data contract, service endpoint, or local-only read/write boundary does it consume?
- Is that backend/service contract already clean enough?
- If not, will the child task clean it in the same slice or create a paired backend/service task?
- What compatibility path is temporary, how is it named, and what later slice removes it?

The desired relationship is:

```text
frontend app context, view model, and service needs
  use an explicit contract with
backend capability, generated data, local service, and write authority
```

The anti-pattern is:

```text
frontend service adapter hides unclear backend ownership indefinitely
```

Frontend service adapters are useful only when they make a contract clearer.
They should not become a polished wrapper around ambiguous backend behavior.
When a frontend slice exposes backend ambiguity, the slice should either clean the backend contract immediately or create a concrete child task for that backend work with an explicit temporary compatibility limit.

Backend authority stays firm:

- source writes, imports, deletes, archives, moves, settings saves, scope lifecycle, rebuilds, source opening, filesystem access, and local-only protected data remain backend/service responsibilities
- browser app code may request those actions only through named endpoints or generated/static read contracts
- public routes must keep working without backend services
- manage mode must keep backend capability checks and endpoint enforcement independent from client visibility

## Feature Freeze Policy

New Docs Viewer feature requests should be on hold by default while this architecture work is active.
The purpose is to avoid adding more behavior that depends on transitional runtime state, broad compatibility APIs, unclear public/manage boundaries, or backend endpoints that are about to be reshaped.

Exceptions are allowed only when the work is urgent or clearly low-risk.
An exception should state:

- why the feature cannot wait for the relevant architecture slice
- which app context, state domain, service adapter, controller, or view owns the new behavior
- which backend/generated-data/service contract it consumes
- why it does not add a new long-lived compatibility layer
- how it preserves public read-only and manage-mode boundaries
- what follow-up is required, if any, after the architecture slice lands

When practical, feature requests should instead become requirements or acceptance checks for the relevant child architecture task.
For example, a new info-panel field request should first clarify whether it belongs to a public metadata view model, a manage metadata view model, a local diagnostics view, or a separate hosted view.
This keeps new product behavior aligned with the app architecture instead of forcing the architecture to preserve another interim path.

## Structural Slices

- Work through these as child task trackers under this parent request using [Tasks Template](/docs/?scope=studio&doc=tasks-template) as the template.
- Each slice should define the app concept being introduced and the old bridge behavior it removes.
- Keep this parent request focused on policy, architecture direction, benefits, and slice framing.

### 1. App Session And State Domains

Task tracker: [Docs Viewer App Session State Domains Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-session-state-domains-tasks).

Define a focused app-session owner that creates named state domains instead of one broad runtime state bag.

Candidate owner:

- `docs-viewer/runtime/js/docs-viewer-app-session.js`

Implemented first slice 2026-05-28:

- `docs-viewer/runtime/js/docs-viewer-app-session.js` creates the app session, broad compatibility state, named state-domain facades, and the explicit temporary compatibility bridge.
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` now imports the app-session owner, passes `appSession.state` to existing controllers, updates the route-session domain when route globals change, and returns `appSession` for future slices.
- Existing controllers intentionally still receive the broad state object until a later slice narrows one complete controller family to domain inputs.

Candidate domains:

- route/session context
- scope/config context
- document index
- selected document and payload cache
- search/recent
- bookmarks
- panel/view state
- management state
- busy/status projection

Acceptance:

- controllers receive only the state domain or facade they need where practical
- state initialization moves out of `docs-viewer-app-runtime.js`
- no behavior changes in `/docs/`, `/library/`, or `/analysis/`
- focused smoke coverage pins the app-session contract

Backend/service handling:

- inventory which state domains are browser-only, generated-data-backed, local-service-backed, or backend-write-backed
- do not move backend-derived management capability state into a generic browser state domain without preserving backend authority
- if management state is reshaped, verify the existing management service capability flow is still the source of write availability truth

### 2. Service Adapter Boundary

Task tracker: [Docs Viewer Service Adapter Boundary Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-service-adapter-boundary-tasks).

Define service adapters for generated/config/backend reads so controllers do not need ad hoc `fetch`, retry, capability, or URL option bundles.

Candidate owners:

- keep and extend `docs-viewer-generated-data-runtime.js` where it is the right owner
- introduce a viewer config service only if it removes real config handoff coupling
- introduce a management service adapter only if it narrows the management context shape

Implemented second slice 2026-05-28:

- `docs-viewer/runtime/js/docs-viewer-service-context.js` defines the explicit public/manage service context. Public contexts keep static generated/config/report assets and omit management base URLs, generated-read service base URLs, backend probes, and management service adapters. Manage contexts keep local generated-read and management backend base URLs separate from backend capability truth.
- `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` now owns named read methods for docs index, document payload, generated search, cross-scope docs index, references index, and reference-target buckets. Route workflow, search, and document/report handoff code consume those methods instead of assembling generated-read fetch/reload/capability options locally.
- Config reads remain with `docs-viewer-config-controller.js`, report registry reads remain with `docs-viewer-reports.js`, and management writes remain with `docs-viewer-management-client.js` plus the management action controllers because those owners already match the source of authority.

Acceptance:

- generated docs, payload, search, report registry, config, and management backend reads have explicit adapters
- public/static reads do not require backend services
- management writes remain behind existing management/backend modules
- public routes still avoid management-only JS and management base URLs

Backend/service handling:

- review every adapter against the actual source of authority: generated static asset, local generated-read service, browser storage, or management backend endpoint
- do not introduce an adapter that normalizes over unclear backend endpoint responsibilities without documenting whether the endpoint should be changed
- if an endpoint shape is awkward only because of old compatibility needs, create or pair a backend cleanup task instead of baking that shape into the app contract

### 3. App Composition And Startup Phases

Task tracker: [Docs Viewer App Composition And Startup Phases Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-composition-startup-phases-tasks).

Replace broad inline controller construction with a composition owner that wires session domains, services, controllers, and lifecycle phases.

Candidate owner:

- `docs-viewer/runtime/js/docs-viewer-app-composition.js`

Startup phases should be readable:

- create session
- create services
- create controllers
- bind events
- load config
- initialize optional context such as bookmarks and management
- load initial index/route
- handle import-open-on-load in manage context

Acceptance:

- `startDocsViewerRuntime(...)` becomes ordinary app startup wiring or delegates almost entirely to composition
- controller construction order is explicit and testable
- initial load sequencing is covered without relying on a giant runtime integration assertion

Backend/service handling:

- separate public startup phases from manage-only backend startup phases
- keep backend reachability and capability checks out of public route boot
- make import-open-on-load and management initialization depend on explicit manage app context, not incidental URL flags alone
- if startup currently relies on backend timing or retry behavior that is not a clean contract, document and task that backend/service behavior

Implemented third slice 2026-05-28:

- `docs-viewer/runtime/js/docs-viewer-app-composition.js` now owns runtime defaults, service-context projection handoff, hosted-view registry creation, panel layout creation, app-session creation, generated-data runtime creation, document-index state creation, public/manage startup phase records, startup authority records, and initial startup sequencing.
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` remains the compatibility coordinator for focused controller construction and callback handoff because existing controllers still depend on function-scoped bridge callbacks. It now delegates foundational app composition and startup phase sequencing to the composition owner.
- Public startup records omit management initialization, management backend surfaces, local generated-read service base URLs, and import-open-on-load. Manage startup records keep management initialization and import-open-on-load gated by management route access plus the current `mode=manage` route state.

### 4. Runtime API Shrink

Task tracker: [Docs Viewer Runtime API Shrink Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-api-shrink-tasks).

Retire the legacy returned runtime API where possible.

Current returned app handle includes:

- `root`
- `routeContext()`
- `appShellRefs`
- `initialLoadPromise`

Implemented fourth slice 2026-05-28:

- The returned runtime/app handle from `startDocsViewerRuntime(...)` and `startDocsViewerApp(...)` was narrowed to `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`.
- Broad `state`, app-composition internals, app-session internals, `loadManagementController`, `applyCurrentRoute`, `loadIndex`, and `loadDoc` were removed from the returned handle.
- Management reload and selected-doc refresh behavior still receive `loadIndex` and `loadDoc` through the private lazy-management context assembled inside `docs-viewer-app-runtime.js`.
- Public `/library/` and `/analysis/` app handles do not expose management service handles, backend capability probes, management lazy loaders, or route workflow bridges.

Acceptance:

- tests and callers use focused owner contracts or a small app handle
- any remaining public app handle is intentional and documented
- no feature module reaches into broad runtime internals when a service/session/controller contract exists

Backend/service handling:

- ensure tests that move away from broad runtime internals still cover backend/service contracts through focused service or management smokes
- do not remove a runtime API by replacing it with direct endpoint calls from feature modules
- if a caller needs backend behavior, route it through the appropriate service adapter or management controller contract

### 5. Public And Manage App Contexts

Task tracker: [Docs Viewer Public And Manage App Contexts Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-app-contexts-tasks).

Make public read-only and local manage mode explicit app contexts.

This should not become a speculative permissions framework.
It should explain and enforce the current split:

- public routes read generated/static assets, show document/search/recent/bookmark/report/info behavior, and omit management assets
- manage mode reads generated data through local services when available and uses backend endpoints for writes/rebuilds/imports/settings/scope lifecycle

Acceptance:

- route config and access projection produce a clear app context object
- management-only assets remain gated by context
- backend capability checks stay in the management/service flow
- public read-only smoke stays part of every context-boundary slice

Backend/service handling:

- define which context facts are static route-config facts and which are backend capability facts
- do not let browser route config imply write authority
- keep public app context free of management base URLs, management-only assets, and backend capability probes
- if manage context needs finer capability fields, add them only with matching backend endpoint semantics and tests

### 6. Controller And View Lifecycle

Task tracker: [Docs Viewer Controller And View Lifecycle Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-controller-view-lifecycle-tasks).

Define a practical lifecycle for controllers and hosted views.

This should build on existing hosted-view lifecycle methods without turning Docs Viewer into a plugin platform.

Acceptance:

- owners have clear `initialize`, `bind`, `update`, and optional `dispose` responsibilities where needed
- hosted views receive explicit context and service inputs
- top-level event binding is not scattered across unrelated modules
- future feature views can attach without modifying route shells or broad runtime state

Backend/service handling:

- hosted views that need backend data must declare the service adapter or capability they consume
- public-safe views should be able to mount without backend services
- manage-only views must not infer write authority from being visible; backend endpoints still enforce writes
- local diagnostic or source-related views should stay local/manage-only until their data contract is safe and documented

Implemented sixth slice 2026-05-28:

- [Docs Viewer Controller And View Lifecycle Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-controller-view-lifecycle-tasks) inventoried the current controller and hosted-view lifecycle owners and found no runtime behavior change was warranted.
- The durable lifecycle contract now defines controller `create`, `initialize`, `bind`, `update`/`project`, and optional `dispose`, plus hosted-view `load`, `mount`, `update`, `unmount`, `close`, and `dispose`.
- Public-safe hosted-view limits and manage-only hosted-view limits are now documented in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) and summarized in [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview).
- Existing focused smoke coverage already pins startup order, session domains, public/manage access separation, hosted-view context shape, hosted-view registry access states, info-panel lifecycle behavior, and lazy management adapter contracts.
- No top-level binding, generated-data flow, route/config behavior, public hosted-view behavior, or management write authority changed in this slice.

### 7. Architecture Review And Cleanup

Task tracker: [Docs Viewer Architecture Review And Cleanup Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-review-cleanup-tasks).

After the structural slices land, update the durable docs so future work has one current architecture story.
This task also owns compatibility cleanup notes carried forward from the structural slices.
Compatibility paths, broad callbacks, broad state dependencies, and legacy JS/server structuring patterns should be treated as migration debt during this review.
The review should remove them where the owner contract is clear, or create named follow-up tasks immediately.
If a reviewed pattern is actually current architecture, the cleanup task should stop describing it as compatibility and document the named owner contract instead.
They should not remain as vague future-development warnings that can surprise later feature work.

Required docs:

- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Docs Viewer Portable File Manifest](/docs/?scope=studio&doc=docs-viewer-portable-files) if runtime copy sets change
- this request and any child trackers

Acceptance:

- `docs-viewer-app-runtime.js` is no longer described as compatibility coordination unless a specific cleanup task or current owner contract explains why that bridge remains
- the app/session/service/controller/view model is documented in one place
- JavaScript inventory scores and owner notes match the new boundaries
- final cleanup audits tests against the target architecture, not just historical compatibility behavior
- legacy JavaScript and server-side patterns that could encourage code to be added in the wrong module are identified and either removed, renamed as current architecture with a named owner contract, or converted into named cleanup tasks

Explicit final cleanup audit points:

- tests reaching through broad state instead of focused owners or DOM/user-visible behavior
- docs describing compatibility fields as current public API
- runtime fields kept only for tests rather than runtime callers or intentional app contracts
- feature modules using app/runtime handles instead of owner-specific callbacks or service/controller contracts
- local service endpoints, management write helpers, generated-read helpers, or broad server modules whose shape hides the intended app/service ownership

Backend/service handling:

- update backend/service docs when a frontend slice changes service contracts, capability semantics, generated-read behavior, or write-boundary assumptions
- record temporary compatibility layers and their removal task rather than leaving them implicit
- keep portable docs clear about which pieces are public static app contract and which require local management services

## Verification Expectations

Each structural slice should run only the checks warranted by touched files, but the baseline for app architecture work is:

- JavaScript syntax checks for changed runtime modules
- focused app-shell module smoke coverage for new owner contracts
- management modal/service smokes when management context, lazy loading, status pills, generated reads, import-open-on-load, or route state changes
- public read-only smoke when public route boot, generated reads, document visibility, info panel, search/recent, bookmarks, reports, or management omission changes
- docs-only source review when no runtime behavior changes

Browser/local-service smokes should use the repo's elevated localhost/browser path in Codex.

## Success Criteria

This request is complete when:

- Docs Viewer can be explained as a browser app with app session, services, controllers, views, and lifecycle
- `docs-viewer-app-runtime.js` is ordinary startup wiring or replaced by a clearer composition module
- broad shared state is replaced or hidden behind named state domains where it matters
- generated/config/backend service boundaries are explicit
- public and manage contexts are first-class and tested
- future source editor, semantic-reference, activity, visualization, and portable fixture work can attach to named app contracts without expanding a compatibility runtime
