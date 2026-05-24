---
doc_id: studio-ui-start
title: UI Start
added_date: 2026-04-21
last_updated: 2026-05-15
parent_id: archive
sort_order: 86000
---

This doc is deprecated. Please refer to [UI](/docs/?scope=studio&doc=ui) and [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue).

---

# UI Start

Use this as the first doc for UI work.

## Direction

UI guidance should be organized around the design problem and affected surfaces, not around an artificial split between Studio and the public site Use one framework vocabulary for:

- public pages
- docs viewer pages
- Library pages
- Studio pages
- local-service-backed command pages

Some primitives and patterns will only appear on Studio routes today.
That does not make them Studio-only design rules.
It means the current affected surface is Studio.

## Design Steps

For any UI task:

1. Identify the UI type before editing.
2. Check whether the page should use an existing shared primitive or composition.
3. Check whether visible runtime copy should come from `studio_config.json`.
4. Check whether the issue is local or systemic.
5. Only then move into the detailed framework or page docs.

## Identify The UI Type

Decide which contract the change belongs to:

- command button
- link or route-entry action
- pill or chip
- panel or panel-link
- input or search field
- local command feedback/status
- list shell or capped list
- modal shell or modal action row
- page-specific composition

If the answer is unclear, stop and classify it first. Several recent inconsistencies came from mixing buttons, links, and route-local compositions.

## Shared Primitive Check

Before adding or changing UI:

- check the isolated demo pages under `/studio/ui-catalogue/demos/`
- map the demo structure into the shared `tagStudio*` layer or an owning route namespace before inventing unrelated markup or CSS
- if the live page fails after mapping a catalogue pattern, use UI Audit to decide whether the issue is in the live route, the shared production primitive, or the demo pattern
- if a pattern is repeated but not yet formalized, decide whether it is:
  - a shared primitive
  - a shared composition
  - or a truly route-specific layout

Relevant references:

- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [UI Audits](/docs/?scope=studio&doc=ui-audits)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)

## UI Copy Check

For Studio pages, visible runtime copy should normally come from `assets/studio/data/studio_config.json`.

Check these points:

- if the runtime calls `getStudioText(config, "<scope>.<key>")`, the matching `ui_text.<scope>` block must exist
- do not let JS fallback strings become the real source of truth
- route paths belong in config routes
- visible button labels, headings, placeholders, status text, and other runtime copy belong in `ui_text`
- build-time-only design selections for static pages belong in Jekyll data, not Studio runtime config

Relevant references:

- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio Config And Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)

## Fast Rules

Use these default checks on every Studio UI task:

- buttons are commands, not navigation
- route-entry actions should usually be links, not buttons
- shared command buttons should use the shared size/width contract unless reviewed otherwise
- command feedback should stay adjacent to the related control area
- capped-list search should appear only when the list is actually truncated
- if a row already has a clear link to the target record, do not duplicate that same navigation as a button
- do not use a panel as a generic wrapper just to get a border around unrelated controls
- if a static Studio route gains async data, service checks, or route commands, replace the static ready initializer with a route-specific ready/busy contract before treating it as smoke-test ready

## Local Or Systemic

Ask this before fixing:

- is the issue only in one route
- or does it expose a shared primitive, shared token, shared config pattern, or repeated interaction problem

If it is systemic:

- fix the shared source where possible
- update the shared framework doc if the contract changed
- create a structured docs-log entry when the change is meaningful enough to preserve as implementation history

Relevant references:

- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)

## Close-Out Checklist

Before finishing Studio UI work:

- update `studio_config.json` if visible runtime copy changed
- update shared docs if the contract changed
- update [Site Change Log](/docs/?scope=studio&doc=site-change-log) for meaningful Studio/site changes
- create a structured docs-log entry for meaningful systemic UI decisions or implementations
- save any formal page-level conformance review in [UI Audits](/docs/?scope=studio&doc=ui-audits)
- verify desktop and mobile behavior
- run `$HOME/miniconda3/bin/python3 studio/checks/audit_studio_ready_state.py --strict` after changing Studio route shells or route-ready scripts
- run the sanitization scan on changed files
