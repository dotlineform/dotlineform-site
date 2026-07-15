---
doc_id: ui
title: Shared UI
added_date: 2026-05-05
last_updated: 2026-07-15
parent_id: ""
---
# Shared UI

Use this section only for browser components shared across routes or apps. The code is the exact component contract; these pages explain which primitive to start with and where its ownership ends.

## Choose The Smallest Primitive

- [Record List And Actions](/docs/?scope=studio&doc=ui-pattern-record-action-list): fixed columns, optional single-row selection, and a separate action toolbar.
- [Selectable List](/docs/?scope=studio&doc=ui-selectable-list-component): single or multiple checkbox selection, including optional parent/child tree behaviour.
- [Search List](/docs/?scope=studio&doc=ui-search-list-component): autocomplete/listbox behaviour around a caller-owned text input and option loader.
- [File Picker](/docs/?scope=studio&doc=ui-pattern-file-picker): load a folder, an optional subfolder, and one or more files through caller-provided loaders.

The components share styling and interaction behaviour, not domain workflows. Routes still own loading, normalization, mutations, persistence, and workflow state.

## Maintenance Rule

For route-specific UI, inspect the live app and make the new behaviour match its established forms, modals, controls, and feedback. Do not document each route composition. If consistency cannot be achieved from current code, record the missing shared primitive or cross-app gap instead.

Shared UI code lives under:

- `shared/frontend/js/`
- `shared/frontend/css/`

An app adapter translates its records into component input, receives events, updates canonical route state, and renders again. A shared component should not know about catalogue records, Data Sharing adapters, Docs Viewer scopes, or server endpoints.

If a proposed option only makes sense for one route, keep it in the adapter. Extend the shared component only when the behaviour is reusable and can be described without naming the first consumer.

## Weak Spots

- The primitives are independent rather than a single UI framework, so similar needs can still be implemented twice.
- Shared options are ordinary JavaScript objects; code and focused tests are the only exact schema.
- Older app surfaces do not consistently follow the current namespace and ownership rules. Do not introduce new `tagStudio*` classes.

Treat those as reasons to inspect the live consumer, not as reasons to add a complete consumer inventory here.
