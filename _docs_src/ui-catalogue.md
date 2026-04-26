---
doc_id: ui-catalogue
title: "UI Catalogue"
added_date: 2026-04-21
last_updated: 2026-04-26
parent_id: design
sort_order: 25
---
# UI Catalogue

This section is the working catalogue of shared UI elements.

Use it to keep recurring elements visible as named, documented primitives rather than redesigning them inside page work.

The docs-viewer role of this page is to explain the catalogue method and link out to the published primitive pages. Implementation details, code samples, and variant-specific notes should live on those published primitive pages rather than being duplicated here.

## Purpose

The catalogue exists to separate:

- primitive design
- page composition
- interactive behavior

When a page uses a shared element such as a `panel` or `toolbar`, the expectation should come from this catalogue first.

## Published Primitive Pages

Current published primitive pages:

- [Button primitive page](/studio/ui-catalogue/button/)
- [Input primitive page](/studio/ui-catalogue/input/)
- [List primitive page](/studio/ui-catalogue/list/)
- [Panel primitive page](/studio/ui-catalogue/panel/)

Add new links here when a primitive gets its own published reference page.

## Primitive Scope

The current first-pass primitive set still includes:

- panel
- button
- input
- list
- toolbar
- modal shell

These remain the first primitives that should become predictable enough to reuse without re-designing them in each task, even if not all of them have published primitive pages yet.

## How To Use This Section

Use the catalogue when:

- defining a shared element for the first time
- checking whether a page should reuse an existing primitive
- recording the canonical structure, rules, and visual reference for a primitive
- adding screenshots or examples that make the intended result unambiguous

Do not use the catalogue for:

- page-specific layout notes
- one-off UI requests
- detailed runtime behavior for a feature-specific widget

Those still belong in:

- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [UI Requests](/docs/?scope=studio&doc=ui-requests)

## Working Method

Use the catalogue as a primitive pressure test, not as a protective demo shell.

- render primitives with the minimum harness needed to inspect them clearly
- if a primitive fails here, prefer assuming the shared primitive or composition contract is incomplete
- inspect live pages for one-off compensation before deciding the failure is page-specific
- fix the shared primitive or shared composition pattern when possible, even if that exposes legacy page drift

Reason:

- a primitive that only works because live pages compensate for it is not reliable enough to reuse
- surfacing those hidden fixes here is the point of the catalogue
- for this project, future design clarity and shared-system reliability matter more than preserving accidental legacy behavior

## Primitive Page Structure

Each published primitive page should stay simple but complete enough to guide implementation.

The default structure is:

- purpose
- contract
- anatomy
- variants and states
- usage rules
- implementation notes
- design guidance
- visual references

When a primitive can compose with itself, for example nested panels or stacked list shells, include that use case explicitly rather than treating it as an out-of-scope environment issue.

Include design guidance when the success of a primitive depends not just on CSS behavior but also on how it should be composed, sized, or edited on a page.

Include common design-led overrides in the sample markup when those overrides are part of normal reuse rather than an edge case.

## List Primitive Direction

The list primitive currently defines three baseline versions:

- simple list: minimal row treatment, no column headers, suitable for short lists where the surrounding page already explains the row context
- sortable list: column headers become clickable buttons on sortable columns and show the active sort direction beside the label
- thumbnail list: the first column is a fixed media thumbnail; sorting may still exist, but it can be controlled by buttons or other controls outside the list

The shared `tagStudioList` / `tagStudioList__*` layer should own the optional width wrapper, row rhythm, header treatment, row-alignment modifiers, common cell text, cell links, sort indicator, and thumbnail frame. Page-specific classes should still own column templates, row actions, chips, and responsive data labels.

By default, a list fills the available width. Constrain it by setting `--studio-list-width` on the `tagStudioList` wrapper. Column widths belong to page/demo-specific paired header and row classes so the list can display its actual content sensibly.

Rows with one-line cells should center-align their contents. Rows that may contain multiline cells should top-align so secondary lines sit consistently beneath the first line.

Studio UI primitives use the small type scale by default. Normal page prose outside primitives should remain at the body type scale.

Current list-like Studio pages should be mapped to these versions before broad refactors. Existing pages may keep page-local row classes where the behavior is data-specific.

If a primitive grows more complex, expand its published primitive page rather than rebuilding a second parallel doc in the docs viewer.

## Broader Design Direction

- use the docs viewer catalogue to explain the method, scope, and design direction of the primitive system
- use the published primitive pages to hold implementation notes, canonical markup, common overrides, and code-facing warnings
- prefer one implementation source of truth even when the docs viewer carries a higher-level summary

## Visual Reference Assets

UI screenshots and reference images for this catalogue should live in the repo under:

- `assets/docs/ui-catalogue/panel/`
- `assets/docs/ui-catalogue/button/`
- `assets/docs/ui-catalogue/input/`
- `assets/docs/ui-catalogue/list/`
- `assets/docs/ui-catalogue/toolbar/`
- `assets/docs/ui-catalogue/modal-shell/`

Use these folders for:

- cropped screenshots of current approved implementations
- comparison images for acceptable variants
- simple annotated reference images when a text-only description is too vague

Recommended file naming:

- `default.png`
- `compact.png`
- `state-disabled.png`
- `example-docs-viewer.png`
- `example-studio.png`

If larger source captures need to exist separately, keep only optimized documentation-facing assets in these folders.

## Expansion Rule

When a new shared element appears repeatedly, add a published primitive page for it and link that page here rather than creating another parallel docs-viewer child doc.

That keeps the viewer tree visible and scalable as the UI system grows.
