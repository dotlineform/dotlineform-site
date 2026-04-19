---
doc_id: ui-primitive-panel
title: "UI Primitive: Panel"
last_updated: 2026-04-19
parent_id: ui-catalogue
sort_order: 10
---
# UI Primitive: Panel

## Purpose

The panel is the default surface wrapper for grouped content, controls, and local page sections.

It should give structure and containment without feeling like a heavy card component.

## Contract

A panel is:

- a bounded surface
- visually quieter than a modal
- suitable for static content or embedded controls
- reusable across Studio and site-owned interfaces where the same shell treatment is appropriate

A panel is not:

- a full page section by default
- a popover or modal
- a stateful JS component in its own right

## Anatomy

The default panel should define:

- outer container
- surface/background
- border or equivalent edge treatment
- radius
- internal padding
- optional heading area
- optional actions area

## Variants And States

Expected variants:

- default panel
- compact panel
- editor panel
- muted or secondary panel where needed

Expected states:

- neutral
- selected or active when a context requires it
- error or warning only when the panel is explicitly acting as a message container

## Usage Rules

- use the panel when content needs visual grouping and a shared shell
- do not create page-local panel lookalikes when the shared primitive is sufficient
- do not overload the panel with feature behavior; add behavior to the content inside it
- if a panel needs a repeated internal layout, document that as a composition rather than changing the base primitive

## Current Implementation Notes

The current Studio baseline is the `tagStudio__panel` surface family in `assets/studio/css/studio.css`.

This doc defines the concept more broadly than one class name, but existing implementations should converge on one shared contract rather than page-local alternatives.

## Visual References

Asset folder:

- `assets/docs/ui-catalogue/panel/`

Add screenshots here for:

- default panel treatment
- compact/editor variants
- examples from Studio or docs surfaces when relevant
