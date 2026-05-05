---
doc_id: ui-primitive-panel
title: "Panel Primitive"
added_date: 2026-05-05
last_updated: "2026-05-05"
parent_id: ui-catalogue
sort_order: 40
---
# Panel Primitive

This doc is the durable implementation contract for shared panel surfaces.

Live reference:

- [Panel primitive page](/studio/ui-catalogue/panel/)

## Scope

The panel primitive covers deliberate contained surfaces such as:

- simple content panels
- compact supporting panels
- editor panels
- panel links
- image panel links
- nested panels when there is a real containment relationship

Do not use panels as generic wrappers just to add a border around unrelated controls.

## Contract

The panel primitive should:

- create a clear contained surface
- keep nested panels visually subordinate
- use fixed design-time height for whole-panel navigation targets
- keep panel-link copy edited to fit the panel rather than stretching the panel to fit copy
- keep image panel text contrast explicit rather than accidental

## Implementation Notes

Current implementation lives in:

- `assets/studio/css/studio.css`

Primary classes:

- `tagStudio__panel`
- `tagStudio__panel--compact`
- `tagStudio__panel--editor`
- `tagStudio__panelLink`
- `tagStudio__panelLink--image`
- `tagStudio__panelLink--imageContrast`

Jekyll-rendered image panel links should keep design-time asset selections in shared page data where possible.
Asset width should be treated as an explicit page design variable.

## Lifecycle Notes

Panel usage should be evaluated as page composition:

- use a panel when the content is a coherent surface
- use a panel link when the whole surface is the navigation target
- keep command feedback adjacent to the relevant controls rather than adding a separate generic panel
- promote repeated panel compositions into documented patterns before copying page-local classes

Stable panel rules from [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) should move here as that log is retired.
