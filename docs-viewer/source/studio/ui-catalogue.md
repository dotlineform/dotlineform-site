---
doc_id: ui-catalogue
title: UI Catalogue
added_date: 2026-04-21
last_updated: 2026-06-02
parent_id: ui
viewable: true
---
# UI Catalogue

This section is the top-level index for shared UI primitives, composition patterns, and isolated demo pages.

The UI Catalogue is now a demo system, not a live-system CSS check. It exists to make patterns readable, inspectable, and reusable while keeping demo code separate from production Studio and Docs Viewer implementation code.
The demo pages are now served by the standalone local UI Catalogue app.
They do not mutate catalogue data and should not be wired through Local Studio routes.

## Demo Route Structure

Published demo pages live under:

- `/ui-catalogue/demos/`
- `/ui-catalogue/demos/primitives/<primitive>/`
- `/ui-catalogue/demos/patterns/<pattern>/`

Reference pages live under:

- `/ui-catalogue/palette/`

Current demo pages:

- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/primitives/button/)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/primitives/input/)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/primitives/list/)
- [Modal Shell Primitive](/docs/?scope=studio&doc=ui-primitive-modal-shell) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/primitives/modal-shell/)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/primitives/panel/)
- [Action Menu Pattern](/docs/?scope=studio&doc=ui-pattern-action-menu) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/patterns/action-menu/)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/patterns/reopenable-command-result/)
- [Select Menu Pattern](/docs/?scope=studio&doc=ui-pattern-select-menu) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/patterns/select-menu/)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links) / [demo page](http://127.0.0.1:8767/ui-catalogue/demos/patterns/column-links/)

The demo links target the default UI Catalogue app port.
If `UI_CATALOGUE_APP_PORT` is changed from `8767`, adjust the port in the browser URL.

Retired Studio routes such as `/studio/ui-catalogue/demos/`, `/studio/ui-catalogue/button/`, and `/studio/ui-catalogue/panel/` should not be recreated. New catalogue pages should use the standalone demo route hierarchy.
The retired public `/palette/` route should not be recreated; palette inspection belongs under `/ui-catalogue/palette/`.
The palette page currently reads checked-in YAML at `ui-catalogue-app/source/palette/palette.yml`; future refresh work should convert that data to a UI Catalogue-owned JSON/JavaScript refresh path rather than restoring Jekyll data ownership.

## Demo Namespace

Demo implementation lives outside the production Studio namespace:

- demo CSS: `ui-catalogue-app/app/assets/css/ui-catalogue-demo.css`
- demo JS: `ui-catalogue-app/app/assets/js/ui-catalogue-demo.js`
- demo classes: `uiCatalogueDemo*`
- palette data: `ui-catalogue-app/source/palette/palette.yml`

Do not import `studio/app/assets/css/studio.css` into demo pages to prove a primitive. Do not use `tagStudio*`, `docsViewer*`, or route-local production classes inside rendered demo markup unless the page is explicitly documenting a migration comparison.
Do not put demo-only fragments in `_includes/`. Demo pages should own their rendered example markup directly.

Markup examples on demo pages should also use the demo namespace. That keeps the examples clear: designers and developers are reading a pattern that must be mapped from demo classes into the live implementation namespace when building real pages.

## Demo Ready State

The demo pages expose a demo-local ready contract:

- `data-ui-catalogue-demo-route`
- `data-ui-catalogue-demo-ready`
- `data-ui-catalogue-demo-busy`

Current roots:

- `/ui-catalogue/demos/` uses `#uiCatalogueDemoIndexRoot`
- `/ui-catalogue/demos/primitives/button/` uses `#uiCatalogueDemoButtonRoot`
- `/ui-catalogue/demos/primitives/input/` uses `#uiCatalogueDemoInputRoot`
- `/ui-catalogue/demos/primitives/list/` uses `#uiCatalogueDemoListRoot`
- `/ui-catalogue/demos/primitives/modal-shell/` uses `#uiCatalogueDemoModalShellRoot`
- `/ui-catalogue/demos/primitives/panel/` uses `#uiCatalogueDemoPanelRoot`
- `/ui-catalogue/demos/patterns/action-menu/` uses `#uiCatalogueDemoActionMenuRoot`
- `/ui-catalogue/demos/patterns/reopenable-command-result/` uses `#uiCatalogueDemoReopenableCommandResultRoot`
- `/ui-catalogue/demos/patterns/select-menu/` uses `#uiCatalogueDemoSelectMenuRoot`
- `/ui-catalogue/demos/patterns/column-links/` uses `#uiCatalogueDemoColumnLinksRoot`

This contract is intentionally separate from the production `data-studio-ready` route contract.

## Purpose

The catalogue separates:

- primitive design
- page composition
- interactive demo behavior
- UI reference data such as the public CSS palette
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

Toolbar still needs a complete demo page. Modal shell now has a primitive demo page. Richer modal behavior should stay in `ui-catalogue-app/app/assets/js/ui-catalogue-demo.js` or a scoped demo module under `ui-catalogue-app/app/assets/js/`.

## Composition Patterns

Composition patterns cover behavior that depends on route state, stored results, modal lifecycle, server payloads, or several primitives working together.

Pattern demos should follow:

- route: `/ui-catalogue/demos/patterns/<pattern>/`
- CSS/JS namespace: `uiCatalogueDemo*`

## Folder Structure

Use this structure for new catalogue work:

- `ui-catalogue-app/source/demos/primitives/<primitive>/index.md`
- `ui-catalogue-app/source/demos/patterns/<pattern>/index.md`
- `ui-catalogue-app/source/palette/palette.yml`
- `ui-catalogue-app/app/assets/css/ui-catalogue-demo.css`
- `ui-catalogue-app/app/assets/js/ui-catalogue-demo.js`
- `ui-catalogue-app/app/assets/docs/<primitive-or-pattern>/` for reference images

Prefer one shared demo stylesheet until a pattern proves it needs its own scoped file.
Keep route-local demo markup inside the route page. `_includes/` remains reserved for production, layout, or genuinely shared Jekyll partials.

## Visual Reference Assets

UI screenshots and reference images for this catalogue should live in the repo under:

- `ui-catalogue-app/app/assets/docs/panel/`
- `ui-catalogue-app/app/assets/docs/button/`
- `ui-catalogue-app/app/assets/docs/input/`
- `ui-catalogue-app/app/assets/docs/list/`
- `ui-catalogue-app/app/assets/docs/toolbar/`
- `ui-catalogue-app/app/assets/docs/modal-shell/`
- `ui-catalogue-app/app/assets/docs/action-menu/`
- `ui-catalogue-app/app/assets/docs/select-menu/`
- `ui-catalogue-app/app/assets/docs/column-links/`
- `ui-catalogue-app/app/assets/docs/reopenable-command-result/`

Use these folders for optimized documentation-facing assets only. Live route screenshots collected during UI Audit should be stored or referenced by the owning audit doc.

## Expansion Rule

When a new shared element appears repeatedly, add a matching primitive or pattern doc under this page and publish an isolated demo route under the demo hierarchy.

Do not add a new UI Catalogue page that imports production CSS as its primary implementation. If live CSS needs checking, create or update a UI Audit.
