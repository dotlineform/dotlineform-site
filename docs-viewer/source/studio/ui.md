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

## Purpose

UI conformance means a live route follows the applicable shared design contract for its controls, layout, interaction lifecycle, copy ownership, accessibility behavior, and responsive behavior.

The goal is not to force every app into one CSS namespace or one component system. The goal is to make repeated UI decisions consistent across:

- Docs Viewer and Docs Viewer management
- Local Studio routes
- Admin app routes, including UI Catalogue
- catalogue, analytics, docs, and other JavaScript app surfaces
- public Jekyll pages when they use shared site patterns

When a pattern is covered, use it. When a pattern is not covered, call out the gap instead of inventing a local convention silently.

## Required Workflow

For every UI change:

1. Classify the UI surface: command, navigation link, field, list, panel, modal, menu, result message, route shell, or page-specific composition.
2. Check [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) for a primitive or pattern demo that describes the structure.
3. Map the primitive or pattern into the live app namespace. Do not copy demo classes into production markup.
4. Use stable JS hooks such as `id`, `data-role`, or feature-scoped `data-*` for behavior. Do not bind JS to presentation classes.
5. Put visible runtime copy in the owning app's normal UI text source when the app is config-backed.
6. Verify the live route, not only the demo.
7. If the route cannot be judged because the primitive or pattern is missing or incomplete, record a UI coverage gap.

## Namespace Rules

Use app-owned namespaces for production UI:

- `docsViewer*` for Docs Viewer runtime and management surfaces
- Admin app route-owned namespaces for Admin tools and UI Catalogue demo pages
- route-owned or app-owned namespaces for new Studio and analytics surfaces
- public-site namespaces for public Jekyll page patterns

Do not introduce new `tagStudio*` classes. That namespace is historical and confusing because tags now belong to Analytics. Existing `tagStudio*` classes may still appear in older Studio CSS and docs as current legacy implementation details, but new work should either use the owning app or route namespace, or first define a shared replacement namespace as part of a focused UI cleanup.

Do not use `uiCatalogueDemo*` outside UI Catalogue demo pages.

## Coverage Gaps

Many live pages predate the current primitive and pattern model. Treat gaps explicitly:

- If a repeated pattern has no primitive or pattern doc, say it is uncovered.
- If a primitive doc names a concept but does not define enough behavior to audit, say it is partial.
- If a page uses old route-local CSS to mimic a shared primitive, record whether it should be migrated now or left as a follow-up.
- If a legacy namespace such as `tagStudio*` is the only current implementation, do not expand it without a named migration decision.

Coverage gaps are valid findings. They should lead to focused UI standardisation work rather than ad hoc page fixes.

## Authoritative Docs

- [UI Framework](/docs/?scope=studio&doc=ui-framework): app-wide implementation model and workflow.
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue): Admin-hosted primitive and pattern demos.
- [UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance): how to audit a live route against current coverage.
- [UI Audits](/docs/?scope=studio&doc=ui-audits): where page-level audit findings and remediation notes live.
