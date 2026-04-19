---
doc_id: site-docs
title: Site Docs
last_updated: 2026-04-19
parent_id: ""
sort_order: 0
---

# Site Docs

This is the top-level map for the current site documentation.

Use it as the default entry point for `/docs/`.

## Main Sections

- **[Studio](/docs/?scope=studio&doc=studio)**
  Studio routes, page wiring, and Studio-specific behavior.
- **[Design](/docs/?scope=studio&doc=design)**
  site-wide UI rules, docs-viewer/search UI standards, Studio UI patterns, and CSS guidance.
- **[UI Requests](/docs/?scope=studio&doc=ui-requests)**
  working specs and task docs for UI-driven feature requests.
- **[Architecture](/docs/?scope=studio&doc=architecture)**
  route/runtime building blocks, shared shell behavior, and generated-artifact flow into the live site.
- **[Config](/docs/?scope=studio&doc=config)**
  checked-in config files and loader modules, what reads them, and when.
- **[Data Models](/docs/?scope=studio&doc=data-models)**
  the main reference for generated/runtime data contracts and source-data records.
- **[Scripts](/docs/?scope=studio&doc=scripts)**
  repo scripts, their flags, outputs, and operational responsibilities.
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)**
  the shared docs module used by `/docs/` and `/library/`.
- **[Search](/docs/?scope=studio&doc=search)**
  dedicated catalogue search plus inline docs-domain search.

## Supporting Docs

- **[Site Change Log](/docs/?scope=studio&doc=site-change-log)**
  meaningful non-search site and Studio history.
- **[Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)**
  rules for maintaining the site change log.

## Practical Reading Order

- start here when you need the right section quickly
- use `Data Models` for schema and payload-contract questions
- use `Config` for checked-in config ownership
- use `Scripts` for build/write mechanics
- use section docs such as `Studio`, `Search`, or `Docs Viewer` for runtime behavior
