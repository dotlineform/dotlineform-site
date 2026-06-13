---
doc_id: ui-primitive-input
title: Input Primitive
added_date: 2026-05-05
last_updated: 2026-06-10
parent_id: ui-catalogue
---
# Input Primitive

This doc is the durable implementation contract for shared input controls and field shells.

Demo reference:

- [Input primitive demo](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/input/)

## Scope

The input primitive covers controls that assign or display a field value:

- text inputs
- native selects
- readonly display values
- stepped numeric compositions
- field label and control wrappers

## Namespace Rule

This primitive defines field anatomy and state behavior, not a universal CSS namespace.

Map the structure into the owning app namespace. Do not introduce new `tagStudio*` classes. Existing `tagStudio*` names below describe older Studio implementation details only.

## Contract

The shared input contract separates the field shell from the input surface:

- an input-surface class owns the visual control surface
- a field-shell class owns label placement, control width, and add-on composition
- a fill variant allows a field to fill its available layout area
- route-local CSS may set deliberate width constraints when the surrounding layout requires it

Disabled means temporarily unavailable because the current state is incomplete.
Display-only values should use a readonly display treatment rather than a disabled editable control.

## Implementation Notes

Current legacy Studio implementation lives in:

- `site/assets/studio/css/studio.css`

Current demo implementation lives in:

- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/source/demos/primitives/input/index.md`

Legacy Studio classes:

- `tagStudio__input`
- `tagStudio__input--defaultValue`
- `tagStudio__input--readonlyDisplay`
- `tagStudioField`
- `tagStudioField--inline`
- `tagStudioField--split`
- `tagStudioField--fill`
- `tagStudioField__label`
- `tagStudioField__control`
- `tagStudioField__stepButton`
- `tagStudioField__incrementValue`

The UI Catalogue demo uses `uiCatalogueDemo*` classes. Treat those as demo-only pattern names, then map the structure into the owning production namespace.

## Lifecycle Notes

Input state should follow the owning page state:

- values come from the route's current source record or selection
- controls disable while conflicting async commands are active
- changing an input should clear stale result actions when those results depend on the previous input
- validation feedback should stay near the field or command area that caused it

Stable input guidance belongs here when it is promoted from implementation work or review notes.
