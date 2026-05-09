---
doc_id: site-docs
title: "Site Docs"
added_date: 2026-04-19
last_updated: 2026-04-19
parent_id: ""
sort_order: 10
---
# Site Docs

This is the top-level map for the current site documentation.

Use it as the default entry point for `/docs/`.

## Main Sections

- **[Studio](/docs/?scope=studio&doc=studio)**
  Studio routes, page wiring, and Studio-specific behavior.
- **[Design](/docs/?scope=studio&doc=design)**
  site-wide UI rules, docs-viewer/search UI standards, Studio UI patterns, and CSS guidance.
- **[Change Requests](/docs/?scope=studio&doc=change-requests)**
  proposed and in-progress request docs, including UI request specs and task breakdowns.
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
- **[Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)**
  checked-in dependency sources, critical versus workflow-specific packages, and local/cloud dependency expectations.
- **[UI Audits](/docs/?scope=studio&doc=ui-audits)**
  saved page-level UI conformance reviews and follow-up audit records.
- **[Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)**
  rules for maintaining the site change log.

## Practical Reading Order

- start here when you need the right section quickly
- use `Data Models` for schema and payload-contract questions
- use `Config` for checked-in config ownership
- use `Scripts` for build/write mechanics
- use section docs such as `Studio`, `Search`, or `Docs Viewer` for runtime behavior
