---
doc_id: ui
title: UI
added_date: 2026-05-05
last_updated: 2026-06-10
parent_id: ""
---
# UI

This section is the entry point for UI design and implementation rules across the local tools and site apps.

Use this page in change requests when the work includes visible UI, interaction behavior, app shell layout, form controls, modals, command feedback, or route navigation. A request can say "follow UI guidance" and this is the contract to start from.

For every UI change:

1. Classify the UI surface: command, navigation link, field, list, panel, modal, menu, result message, route shell, or page-specific composition.
2. Check the current shared component, primitive, or pattern guidance for the nearest live-system structure.
3. Map the structure into the live app namespace.
4. Use stable JS hooks such as `id`, `data-role`, or feature-scoped `data-*` for behavior. Do not bind JS to presentation classes.
5. Put visible runtime copy in the owning app's normal UI text source when the app is config-backed.
6. Verify the live route, not only the demo.
7. If the route cannot be judged because the primitive or pattern is missing or incomplete, record a UI coverage gap.

## Namespace Rules

Use app-owned namespaces for production UI:

- `docsViewer*` for Docs Viewer runtime and management surfaces
- Admin app route-owned namespaces for Admin tools
- route-owned or app-owned namespaces
- public-site namespaces for public page patterns

Do not introduce new `tagStudio*` classes. Existing `tagStudio*` classes may still appear in older Studio CSS and docs as current legacy implementation details, but new work should either use the owning app or route namespace, or first define a shared replacement namespace as part of a focused UI cleanup.
