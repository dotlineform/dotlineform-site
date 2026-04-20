---
doc_id: studio-ui-start
title: "Studio UI Start"
last_updated: 2026-04-20
parent_id: design
sort_order: 15
---

# Studio UI Start

Use this as the first doc for Studio UI work.

This is a short implementation preflight, not the full reference.

Use the longer docs only after this checklist has told you which one you actually need.

## Start Here

For any Studio UI task:

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

Before adding or changing Studio UI:

- check the live primitive pages under `/studio/ui-catalogue/`
- use the shared `tagStudio*` layer before inventing route-local markup or CSS
- if the primitive fails on the catalogue page, treat that as a shared problem rather than hiding it with page-local compensation
- if a pattern is repeated but not yet formalized, decide whether it is:
  - a shared primitive
  - a shared composition
  - or a truly route-specific layout

Relevant references:

- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
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

## Local Or Systemic

Ask this before fixing:

- is the issue only in one route
- or does it expose a shared primitive, shared token, shared config pattern, or repeated interaction problem

If it is systemic:

- fix the shared source where possible
- update the permanent decision log
- update the shared framework doc if the contract changed

Relevant references:

- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)

## Close-Out Checklist

Before finishing Studio UI work:

- update `studio_config.json` if visible runtime copy changed
- update shared docs if the contract changed
- update [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) if the issue is systemic
- update [Site Change Log](/docs/?scope=studio&doc=site-change-log) for meaningful Studio/site changes
- verify desktop and mobile behavior
- run the sanitization scan on changed files

## Then Go Deeper

Use the detailed docs only as needed:

- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework) for Studio shared contracts and primitives
- [UI Framework](/docs/?scope=studio&doc=ui-framework) for site-wide interaction defaults
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) for primitive pages and implementation notes
- [Studio](/docs/?scope=studio&doc=studio) for Studio feature/runtime docs
