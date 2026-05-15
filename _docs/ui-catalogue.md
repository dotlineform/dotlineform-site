---
doc_id: ui-catalogue
title: UI Catalogue
added_date: 2026-04-21
last_updated: "2026-05-15"
parent_id: ""
sort_order: 70
---
# UI Catalogue

This section is the top-level index for shared UI primitives, composition patterns, and isolated demo pages.

The UI Catalogue is now a demo system, not a live-system CSS check. It exists to make patterns readable, inspectable, and reusable while keeping demo code separate from production Studio and Docs Viewer implementation code.

## Demo Route Structure

Published demo pages live under:

- `/studio/ui-catalogue/demos/`
- `/studio/ui-catalogue/demos/primitives/<primitive>/`
- `/studio/ui-catalogue/demos/patterns/<pattern>/`

Current demo pages:

- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button) / [demo page](/studio/ui-catalogue/demos/primitives/button/)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input) / [demo page](/studio/ui-catalogue/demos/primitives/input/)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list) / [demo page](/studio/ui-catalogue/demos/primitives/list/)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel) / [demo page](/studio/ui-catalogue/demos/primitives/panel/)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result) / [demo page](/studio/ui-catalogue/demos/patterns/reopenable-command-result/)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links) / [demo page](/studio/ui-catalogue/demos/patterns/column-links/)

Removed legacy routes such as `/studio/ui-catalogue/button/` and `/studio/ui-catalogue/panel/` should not be recreated. New catalogue pages should use the demo route hierarchy.

## Demo Namespace

Demo implementation lives outside the production Studio namespace:

- demo CSS: `assets/ui-catalogue/css/ui-catalogue-demo.css`
- demo JS: `assets/ui-catalogue/js/ui-catalogue-demo.js`
- demo classes: `uiCatalogueDemo*`

Do not import `assets/studio/css/studio.css` into demo pages to prove a primitive. Do not use `tagStudio*`, `docsViewer*`, or route-local production classes inside rendered demo markup unless the page is explicitly documenting a migration comparison.
Do not put demo-only fragments in `_includes/`. Demo pages should own their rendered example markup directly.

Markup examples on demo pages should also use the demo namespace. That keeps the examples clear: designers and developers are reading a pattern that must be mapped from demo classes into the live implementation namespace when building real pages.

## Demo Ready State

The demo pages expose a demo-local ready contract:

- `data-ui-catalogue-demo-route`
- `data-ui-catalogue-demo-ready`
- `data-ui-catalogue-demo-busy`

Current roots:

- `/studio/ui-catalogue/demos/` uses `#uiCatalogueDemoIndexRoot`
- `/studio/ui-catalogue/demos/primitives/button/` uses `#uiCatalogueDemoButtonRoot`
- `/studio/ui-catalogue/demos/primitives/input/` uses `#uiCatalogueDemoInputRoot`
- `/studio/ui-catalogue/demos/primitives/list/` uses `#uiCatalogueDemoListRoot`
- `/studio/ui-catalogue/demos/primitives/panel/` uses `#uiCatalogueDemoPanelRoot`
- `/studio/ui-catalogue/demos/patterns/reopenable-command-result/` uses `#uiCatalogueDemoReopenableCommandResultRoot`
- `/studio/ui-catalogue/demos/patterns/column-links/` uses `#uiCatalogueDemoColumnLinksRoot`

This contract is intentionally separate from the production `data-studio-ready` route contract.

## Purpose

The catalogue separates:

- primitive design
- page composition
- interactive demo behavior
- live implementation auditing

Use the catalogue when defining or discussing a shared element before or during implementation. Use UI Audit when checking whether live production pages actually conform to the intended pattern.

## Demo To Live Mapping

Catalogue demos are not dual-purpose production checks.

When creating a live page from a demo:

- start from the demo structure and behavior
- map `uiCatalogueDemo*` classes into the owning live namespace
- use production UI text sources where the live page is config-backed
- wire production state, validation, service calls, and route readiness in the live route
- verify the live result through UI Audit, not by making the demo import live CSS

This keeps demo examples stable even when live implementation details evolve.

## Primitive Scope

The current primitive set includes:

- panel
- button
- input
- list
- toolbar
- modal shell

Toolbar and modal shell still need complete demo pages. The modal work should use the same `primitives` and `patterns` structure, with any richer modal behavior implemented in `assets/ui-catalogue/js/ui-catalogue-demo.js` or a scoped demo module under `assets/ui-catalogue/js/`.

## Composition Patterns

Composition patterns cover behavior that depends on route state, stored results, modal lifecycle, server payloads, or several primitives working together.

Pattern demos should follow:

- route: `/studio/ui-catalogue/demos/patterns/<pattern>/`
- CSS/JS namespace: `uiCatalogueDemo*`

## Folder Structure

Use this structure for new catalogue work:

- `studio/ui-catalogue/demos/primitives/<primitive>/index.md`
- `studio/ui-catalogue/demos/patterns/<pattern>/index.md`
- `assets/ui-catalogue/css/ui-catalogue-demo.css`
- `assets/ui-catalogue/js/ui-catalogue-demo.js`
- `assets/docs/ui-catalogue/<primitive-or-pattern>/` for reference images

Prefer one shared demo stylesheet until a pattern proves it needs its own scoped file.
Keep route-local demo markup inside the route page. `_includes/` remains reserved for production, layout, or genuinely shared Jekyll partials.

## Visual Reference Assets

UI screenshots and reference images for this catalogue should live in the repo under:

- `assets/docs/ui-catalogue/panel/`
- `assets/docs/ui-catalogue/button/`
- `assets/docs/ui-catalogue/input/`
- `assets/docs/ui-catalogue/list/`
- `assets/docs/ui-catalogue/toolbar/`
- `assets/docs/ui-catalogue/modal-shell/`
- `assets/docs/ui-catalogue/column-links/`
- `assets/docs/ui-catalogue/reopenable-command-result/`

Use these folders for optimized documentation-facing assets only. Live route screenshots collected during UI Audit should be stored or referenced by the owning audit doc.

## Expansion Rule

When a new shared element appears repeatedly, add a matching primitive or pattern doc under this page and publish an isolated demo route under the demo hierarchy.

Do not add a new UI Catalogue page that imports production CSS as its primary implementation. If live CSS needs checking, create or update a UI Audit.
