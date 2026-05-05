---
doc_id: ui-primitive-input
title: "Input Primitive"
added_date: 2026-05-05
last_updated: "2026-05-05"
parent_id: ui-catalogue
sort_order: 20
---
# Input Primitive

This doc is the durable implementation contract for shared input controls and field shells.

Live reference:

- [Input primitive page](/studio/ui-catalogue/input/)

## Scope

The input primitive covers controls that assign or display a field value:

- text inputs
- native selects
- readonly display values
- stepped numeric compositions
- field label and control wrappers

## Contract

The shared input contract separates the field shell from the input surface:

- `tagStudio__input` owns the visual control surface
- `tagStudioField` owns label placement, control width, and add-on composition
- `tagStudioField--fill` allows a field to fill its available layout area
- route-local CSS may set deliberate width constraints when the surrounding layout requires it

Disabled means temporarily unavailable because the current state is incomplete.
Display-only values should use a readonly display treatment rather than a disabled editable control.

## Implementation Notes

Current implementation lives in:

- `assets/studio/css/studio.css`

Primary classes:

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

## Lifecycle Notes

Input state should follow the owning page state:

- values come from the route's current source record or selection
- controls disable while conflicting async commands are active
- changing an input should clear stale result actions when those results depend on the previous input
- validation feedback should stay near the field or command area that caused it

Historical input guidance currently buried in [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) should move here as stable rules are promoted.
