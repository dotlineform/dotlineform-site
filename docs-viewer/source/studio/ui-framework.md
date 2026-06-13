---
doc_id: ui-framework
title: UI Framework
added_date: 2026-04-24
last_updated: 2026-06-10
parent_id: ui
---
# UI Framework

This document defines the current app-wide UI implementation model.

It applies to visible UI work across Local Studio, Docs Viewer, Admin app routes, Analytics-owned tools, and public-site surfaces when they use shared UI patterns.

References:

- [UI](/docs/?scope=studio&doc=ui)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [UI Audits](/docs/?scope=studio&doc=ui-audits)

## Framework Goal

The UI framework is a consistency contract, not a component framework.

It should help developers:

- identify whether a UI element is already covered by a primitive or pattern
- map shared designs into the owning app namespace
- avoid mixing command, navigation, field, and panel semantics
- keep JavaScript behavior separate from presentation classes
- surface uncovered or partial patterns as real gaps
- verify live routes against the applicable contract

## UI Surface Types

Classify the surface before editing.

Common types:

- command button
- navigation link or route-entry action
- select menu or value picker
- input field or field shell
- list, table-like list, or result list
- panel, panel link, or contained editor surface
- modal shell, confirmation, notice, input, or choice dialog
- local command status or reopenable result
- app shell, route shell, or page-specific composition

If a UI element combines several types, split the responsibilities. For example, a link should navigate; a button should run a command; a modal shell should own dialog mechanics but not the write operation.

## Primitive And Pattern Workflow

Before adding new markup or CSS:

1. Check [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) for the nearest primitive or pattern.
2. Read the primitive or pattern doc for anatomy, lifecycle, accessibility, and ownership.
3. Treat the Admin catalogue demo as a design reference, not production CSS.
4. Map the pattern into the live app's namespace and state model.
5. If no usable primitive exists, call that out as a UI coverage gap.
6. If the pattern is repeated enough to standardise, add or request a primitive or pattern doc and demo.

The UI Catalogue proves the isolated pattern. It does not prove the live route. Live routes still need route-level verification or UI Audit.

## JavaScript App Model

Most local tools are JavaScript app surfaces. Treat them as apps when they have route state, async reads, service calls, generated data, management capability checks, or write workflows.

JavaScript app surfaces should follow these rules:

- templates own stable shell regions and major layout containers
- JavaScript owns dynamic fragments, state projection, command dispatch, and async lifecycle
- route controllers receive explicit refs, services, config, and callbacks
- shared helpers should receive normalized records or options rather than reading broad global state
- route-owned state decides which commands are hidden, disabled, busy, or selected
- service writes and rebuilds stay behind named backend endpoints with server-side validation
- visible status should be adjacent to the command or region it describes

Do not add a global framework or implicit plugin system to solve a page-local UI problem. Add narrow shared helpers only when several routes need the same lifecycle or interaction contract.

## CSS And Hook Boundary

Keep these responsibilities separate:

- `class=""`: presentation and layout
- stable `id=""`: single known element lookup or test hook
- `data-role=""`: reusable semantic JS hook inside a feature
- feature-scoped `data-*`: route or app state hooks
- `data-state=""` and `aria-*`: runtime state and accessibility

Rules:

- JS behavior should not query presentational classes when a stable hook can be exposed.
- JS should not toggle route-local presentation classes as its primary state model.
- State should project through `disabled`, `hidden`, `aria-*`, `data-state`, or explicit render output.
- Page templates should expose stable shells; generated markup should remain small and inspectable.

## Namespace Ownership

Production markup must use an owning namespace:

- Docs Viewer uses `docsViewer*`.
- UI Catalogue demos use `uiCatalogueDemo*` and only inside Admin-hosted demo pages.
- Admin app routes should use Admin or route-owned namespaces.
- Analytics-owned routes should use Analytics or route-owned namespaces.
- Public-site page patterns should use public-site namespaces.
- Legacy Studio routes may still contain `tagStudio*`, but new work should not expand that namespace.

`tagStudio*` is historical. It is doubly confusing now that tags belong to Analytics. When docs mention `tagStudio*`, read it as a legacy Studio production mapping, not a universal primitive namespace.

If a shared production namespace is needed to replace `tagStudio*`, define that as a focused migration request. Do not create compatibility aliases casually.

## Copy Ownership

Visible runtime copy should come from the owning app's normal UI text source when that app is config-backed.

Examples:

- Docs Viewer management copy belongs in Docs Viewer UI text config.
- Studio app copy belongs in Studio route UI text config.
- Admin app copy belongs in Admin app route data or code-owned copy according to that route's contract.

JS fallback strings are acceptable defensive defaults, but they should not become the real source of product copy for config-backed apps.

## Ready, Busy, And Capability State

Every app route with async behavior should expose a route-appropriate readiness contract.

Rules:

- ready means the shell has loaded enough for the route to be usable or for an error state to be visible
- busy should be scoped to the operation or route region that is busy
- command buttons disable while conflicting operations run
- capability checks should hide unavailable features only when the feature truly cannot be used
- unsupported write services should report a clear management or service-unavailable state

Do not copy `data-studio-ready` into non-Studio apps. Use the route's own ready contract unless a shared contract has been explicitly defined.

## Fast Rules

Use these checks on every UI task:

- buttons are commands, not ordinary navigation
- links navigate, even when styled as pills or cards
- disabled means temporarily unavailable, not readonly display
- route-entry actions should usually be links
- command feedback stays near the command area
- search controls appear only when useful for the list size or workflow
- modal helpers own shell mechanics, not writes or route reloads
- list row actions should not duplicate an obvious row title link unless the duplicate action has a distinct purpose
- panels should contain coherent content, not arbitrary controls needing a border
- demo classes never ship in production routes
- gaps are findings, not excuses to invent silent local conventions

## Verification

For UI implementation work, choose verification proportional to the change.

Common checks:

- inspect the live route in a browser at desktop size
- inspect mobile behavior for public pages and responsive app surfaces
- verify keyboard behavior for menus, modals, and custom controls
- run focused Playwright smoke tests when a route has one
- run `node --check` for changed JavaScript modules
- run relevant Python smoke or audit commands for route-owned UI checks
- run UI Audit when a task is explicitly conformance work or when a shared pattern migration is risky

When a live route cannot be fully checked because the primitive or pattern is not defined, record a coverage gap and the minimum follow-up needed.

## App-Specific Notes

### Docs Viewer

Docs Viewer is a shared JavaScript app for `/docs/`, `/library/`, and `/analysis/`.

It uses `docsViewer*` classes and portable runtime modules. Do not map Docs Viewer UI into `tagStudio*`.

Current standards:

- keep the document-reader layout quiet and scannable
- keep the docs tree as the stable navigation surface
- keep search and recently-added results inline in the main pane
- keep management controls explicit and hidden from public read-only routes
- use generated index options for scope-level tree visibility rather than hard-coded route checks
- in manage mode, non-viewable docs are visible through manage controls and should have a clear non-viewable treatment

### Admin App And UI Catalogue

The Admin app hosts operational checks and UI Catalogue demo pages.

UI Catalogue demos use `uiCatalogueDemo*` classes to document primitives and patterns in isolation. Production routes should map those structures into their owning namespace.

### Local Studio And Legacy CSS

Older Studio routes still use shared CSS in `assets/studio/css/studio.css` and legacy `tagStudio*` classes.

Those classes are current implementation details, not the target naming model. New work should avoid expanding `tagStudio*` unless the task is explicitly maintaining an existing legacy route and no scoped migration is in scope.
