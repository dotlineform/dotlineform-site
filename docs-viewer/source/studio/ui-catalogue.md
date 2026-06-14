---
doc_id: ui-catalogue
title: UI Catalogue
added_date: 2026-04-21
last_updated: 2026-06-14
parent_id: ui
viewable: true
---
# UI Catalogue

This section is the top-level index for shared UI primitives, composition patterns, and isolated demo pages.

The UI Catalogue is now a demo system, not a live-system CSS check. It exists to make patterns readable, inspectable, and reusable while keeping demo code separate from production Studio and Docs Viewer implementation code.
The demo pages are now served by the local Admin app.
They do not mutate catalogue data and should not be wired through Local Studio routes.
The durable Admin route and static-serving boundary is documented in [Local Admin App](/docs/?scope=studio&doc=local-admin-app).

Use the catalogue to understand the shape and behavior of a primitive or pattern. Do not treat catalogue CSS classes as production names.

## Demo Route Structure

Published demo pages live under:

- `/admin/ui-catalogue/demos/`
- `/admin/ui-catalogue/demos/primitives/<primitive>/`
- `/admin/ui-catalogue/demos/patterns/<pattern>/`

Reference pages live under:

- `/admin/ui-catalogue/palette/`

Current demo pages:

- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/button/)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/input/)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/list/)
- [Modal Shell Primitive](/docs/?scope=studio&doc=ui-primitive-modal-shell) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/modal-shell/)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/panel/)
- [Action Menu Pattern](/docs/?scope=studio&doc=ui-pattern-action-menu) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/patterns/action-menu/)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/patterns/reopenable-command-result/)
- [Select Menu Pattern](/docs/?scope=studio&doc=ui-pattern-select-menu) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/patterns/select-menu/)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links) / [demo page](http://127.0.0.1:8768/admin/ui-catalogue/demos/patterns/column-links/)

Current shared production controls and patterns:

- [Search List Pattern](/docs/?scope=studio&doc=ui-pattern-search-list)
- [File Picker Pattern](/docs/?scope=studio&doc=ui-pattern-file-picker)
- [Record Action List Working Spec](/docs/?scope=studio&doc=ui-pattern-record-action-list)

The demo links target the default Admin app port.
If `ADMIN_APP_PORT` is changed from `8768`, adjust the port in the browser URL.

Retired Studio routes such as `/studio/ui-catalogue/demos/`, `/studio/ui-catalogue/button/`, and `/studio/ui-catalogue/panel/` should not be recreated. New catalogue pages should use the Admin-hosted demo route hierarchy.
The palette page currently reads checked-in YAML at `admin-app/ui-catalogue/source/palette/palette.yml`; future refresh work should convert that data to a UI Catalogue-owned JSON/JavaScript refresh path.

## Demo Namespace

Demo implementation lives outside the production Studio namespace:

- demo CSS: `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- demo JS: `admin-app/ui-catalogue/assets/js/ui-catalogue-demo.js`
- demo classes: `uiCatalogueDemo*`
- palette data: `admin-app/ui-catalogue/source/palette/palette.yml`

Do not import `studio/app/assets/css/studio.css` into demo pages to prove a primitive. Do not use `tagStudio*`, `docsViewer*`, or route-local production classes inside rendered demo markup unless the page is explicitly documenting a migration comparison.
Do not put demo-only fragments in `_includes/`. Demo pages should own their rendered example markup directly.

Markup examples on demo pages should also use the demo namespace. That keeps the examples clear: designers and developers are reading a pattern that must be mapped from demo classes into the live implementation namespace when building real pages.

`tagStudio*` is a legacy Studio implementation namespace, not a catalogue namespace. Do not add it to new demos and do not introduce new production usage just because an older primitive doc still names it as a current live example.

## Demo Ready State

The demo pages expose a demo-local ready contract:

- `data-ui-catalogue-demo-route`
- `data-ui-catalogue-demo-ready`
- `data-ui-catalogue-demo-busy`

Current roots:

- `/admin/ui-catalogue/demos/` uses `#uiCatalogueDemoIndexRoot`
- `/admin/ui-catalogue/demos/primitives/button/` uses `#uiCatalogueDemoButtonRoot`
- `/admin/ui-catalogue/demos/primitives/input/` uses `#uiCatalogueDemoInputRoot`
- `/admin/ui-catalogue/demos/primitives/list/` uses `#uiCatalogueDemoListRoot`
- `/admin/ui-catalogue/demos/primitives/modal-shell/` uses `#uiCatalogueDemoModalShellRoot`
- `/admin/ui-catalogue/demos/primitives/panel/` uses `#uiCatalogueDemoPanelRoot`
- `/admin/ui-catalogue/demos/patterns/action-menu/` uses `#uiCatalogueDemoActionMenuRoot`
- `/admin/ui-catalogue/demos/patterns/reopenable-command-result/` uses `#uiCatalogueDemoReopenableCommandResultRoot`
- `/admin/ui-catalogue/demos/patterns/select-menu/` uses `#uiCatalogueDemoSelectMenuRoot`
- `/admin/ui-catalogue/demos/patterns/column-links/` uses `#uiCatalogueDemoColumnLinksRoot`

This contract is intentionally separate from the production `data-studio-ready` route contract.

## Purpose

The catalogue separates:

- primitive design
- page composition
- interactive demo behavior
- UI reference data such as the public CSS palette
- live implementation auditing

Use the catalogue when defining or discussing a shared element before or during implementation. Use UI Audit when checking whether live production pages actually conform to the intended pattern.

If a requested UI element has no matching primitive or pattern, record that as a coverage gap. Do not stretch an unrelated primitive to cover it only to avoid naming the gap.

## Demo To Live Mapping

Catalogue demos are not dual-purpose production checks.

When creating a live page from a demo:

- start from the demo structure and behavior
- map `uiCatalogueDemo*` classes into the owning live namespace
- use production UI text sources where the live page is config-backed
- wire production state, validation, service calls, and route readiness in the live route
- verify the live result through UI Audit, not by making the demo import live CSS

This keeps demo examples stable even when live implementation details evolve.

Live namespace examples:

- Docs Viewer maps shared ideas into `docsViewer*`.
- Admin app routes should use Admin or route-owned classes.
- Analytics routes should use Analytics or route-owned classes.
- older Studio routes may still use legacy `tagStudio*`, but new work should avoid expanding that namespace.

## Primitive Scope

The current primitive set includes:

- panel
- button
- input
- list
- toolbar
- modal shell

Toolbar still needs a complete demo page. Modal shell now has a primitive demo page. Richer modal behavior should stay in `admin-app/ui-catalogue/assets/js/ui-catalogue-demo.js` or a scoped demo module under `admin-app/ui-catalogue/assets/js/`.

## Composition Patterns

Composition patterns cover behavior that depends on route state, stored results, modal lifecycle, server payloads, or several primitives working together.

Pattern demos should follow:

- route: `/admin/ui-catalogue/demos/patterns/<pattern>/`
- CSS/JS namespace: `uiCatalogueDemo*`

## Folder Structure

Use this structure for new catalogue work:

- `admin-app/ui-catalogue/source/demos/primitives/<primitive>/index.md`
- `admin-app/ui-catalogue/source/demos/patterns/<pattern>/index.md`
- `admin-app/ui-catalogue/source/palette/palette.yml`
- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/assets/js/ui-catalogue-demo.js`
- `admin-app/ui-catalogue/assets/docs/<primitive-or-pattern>/` for reference images

Prefer one shared demo stylesheet until a pattern proves it needs its own scoped file.
Keep route-local demo markup inside the route page.

## Visual Reference Assets

UI screenshots and reference images for this catalogue should live in the repo under:

- `admin-app/ui-catalogue/assets/docs/panel/`
- `admin-app/ui-catalogue/assets/docs/button/`
- `admin-app/ui-catalogue/assets/docs/input/`
- `admin-app/ui-catalogue/assets/docs/list/`
- `admin-app/ui-catalogue/assets/docs/toolbar/`
- `admin-app/ui-catalogue/assets/docs/modal-shell/`
- `admin-app/ui-catalogue/assets/docs/action-menu/`
- `admin-app/ui-catalogue/assets/docs/select-menu/`
- `admin-app/ui-catalogue/assets/docs/column-links/`
- `admin-app/ui-catalogue/assets/docs/reopenable-command-result/`

Use these folders for optimized documentation-facing assets only. Live route screenshots collected during UI Audit should be stored or referenced by the owning audit doc.

## Expansion Rule

When a new shared element appears repeatedly, add a matching primitive or pattern doc under this page and publish an isolated demo route under the demo hierarchy.

Do not add a new UI Catalogue page that imports production CSS as its primary implementation. If live CSS needs checking, create or update a UI Audit.

If a live route relies on a pattern that is missing from the catalogue, the correct short-term result is a documented coverage gap plus a focused standardisation follow-up.
