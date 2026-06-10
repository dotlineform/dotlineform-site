---
doc_id: ui-primitive-button
title: Button Primitive
added_date: 2026-05-05
last_updated: 2026-06-10
parent_id: ui-catalogue
---
# Button Primitive

This doc is the durable implementation contract for shared command buttons.

Demo reference:

- [Button primitive demo](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/button/)

## Scope

Buttons are command controls.
They perform an action in the current context.

Use the button primitive for commands such as:

- save
- import
- create
- generate
- close
- confirm
- cancel

Do not use the button primitive for ordinary navigation.
Navigation should use links or a documented link-style composition.

## Namespace Rule

This primitive defines behavior and visual expectations, not a universal CSS class name.

Map the primitive into the owning app namespace:

- Docs Viewer uses `docsViewer*`.
- Admin app routes use Admin or route-owned classes.
- Analytics routes use Analytics or route-owned classes.
- older Studio routes may still use legacy `tagStudio*`.

Do not introduce new `tagStudio*` button classes. Existing `tagStudio*` names below are legacy Studio implementation examples.

## Contract

The shared command-button contract currently includes:

- stable box sizing and height
- one compact shared command height
- optional default-width behavior
- disabled state for temporarily unavailable commands
- modal action-row compatibility
- adjacent feedback when the command produces local status text

## Implementation Notes

Current legacy Studio implementation lives in:

- `assets/studio/css/studio.css`

Current demo implementation lives in:

- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/source/demos/primitives/button/index.md`

Legacy Studio classes:

- `tagStudio__button`
- `tagStudio__button--defaultWidth`
- `tagStudio__button--defaultAction`

In older Studio routes, `tagStudio__button` uses the same compact height for page commands and modal actions.
Use the same default-width behavior in new app namespaces when commands in a row should share the standard minimum width, including modal action rows.

Button-related visible copy belongs in the relevant route or feature `ui_text` config when the page is config-backed.

The UI Catalogue demo uses `uiCatalogueDemo*` classes. Treat the demo markup as a pattern reference that must be mapped into the live production namespace during implementation.

## Lifecycle Notes

Button state should follow the command lifecycle:

- enabled only when the command can run
- disabled while a conflicting async operation is active
- status or validation feedback remains adjacent to the command area
- destructive or write actions use confirmation only when the workflow requires explicit review

Historical button notes from the retired Studio UI rules log are no longer a live source; stable guidance belongs in this primitive doc.
Stable button guidance should move here as that log is retired.
