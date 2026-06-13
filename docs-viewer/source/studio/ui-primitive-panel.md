---
doc_id: ui-primitive-panel
title: Panel Primitive
added_date: 2026-05-05
last_updated: 2026-06-10
parent_id: ui-catalogue
---
# Panel Primitive

This doc is the durable implementation contract for shared panel surfaces.

Demo reference:

- [Panel primitive demo](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/panel/)

## Scope

The panel primitive covers deliberate contained surfaces such as:

- simple content panels
- compact supporting panels
- editor panels
- panel links
- image panel links
- nested panels when there is a real containment relationship

Do not use panels as generic wrappers just to add a border around unrelated controls.

## Namespace Rule

This primitive defines panel purpose, containment, and link behavior, not one production class prefix.

Map the panel into the owning app namespace. Do not introduce new `tagStudio*` panel classes. Existing `tagStudio*` names below describe older Studio implementation details only.

## Contract

The panel primitive should:

- create a clear contained surface
- keep nested panels visually subordinate
- keep surface, border, body text, and muted text tokens on the same theme layer
- use fixed design-time height for whole-panel navigation targets
- keep panel-link copy edited to fit the panel rather than stretching the panel to fit copy
- keep image panel text contrast explicit rather than accidental
- keep the base image-panel text treatment stable across light and dark themes unless an explicit contrast modifier is used

## Implementation Notes

Current legacy Studio implementation lives in:

- `site/assets/studio/css/studio.css`

Current demo implementation lives in:

- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/source/demos/primitives/panel/index.md`

Dark-mode panel surfaces must override the Studio surface token set together.
Do not combine a light `--studio-surface` with global dark-mode text tokens such as `--muted`; that makes labels and disabled text low contrast on white panels.

Image panel links are the exception to normal theme inheritance.
The legacy Studio image-panel variant keeps a dark text treatment over a light image overlay in both light and dark mode.
Choose images and overlays that support that treatment, or use an explicit high-contrast image-panel variant for white text.

Legacy Studio classes:

- `tagStudio__panel`
- `tagStudio__panel--compact`
- `tagStudio__panel--editor`
- `tagStudio__panelLink`
- `tagStudio__panelLink--image`
- `tagStudio__panelLink--imageContrast`

The UI Catalogue demo uses `uiCatalogueDemo*` classes. Treat those as demo-only pattern names, then map the structure into the owning production namespace during page work.

Asset width should be treated as an explicit page design variable.

## Lifecycle Notes

Panel usage should be evaluated as page composition:

- use a panel when the content is a coherent surface
- use a panel link when the whole surface is the navigation target
- keep command feedback adjacent to the relevant controls rather than adding a separate generic panel
- promote repeated panel compositions into documented patterns before copying page-local classes

Stable panel rules belong here when they need to become permanent reference guidance.
