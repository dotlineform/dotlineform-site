---
doc_id: ui-catalogue
title: "UI Catalogue"
last_updated: 2026-04-20
parent_id: design
sort_order: 25
---
# UI Catalogue

This section is the working catalogue of shared UI elements.

Use it to keep recurring elements visible as named, documented primitives rather than redesigning them inside page work.

## Purpose

The catalogue exists to separate:

- primitive design
- page composition
- interactive behavior

When a page uses a shared element such as a `panel` or `toolbar`, the expectation should come from this catalogue first.

## First-Pass Primitive Set

The initial catalogue covers:

- [UI Primitive: Panel](/docs/?scope=studio&doc=ui-primitive-panel)
- [UI Primitive: Button](/docs/?scope=studio&doc=ui-primitive-button)
- [UI Primitive: Input](/docs/?scope=studio&doc=ui-primitive-input)
- [UI Primitive: List Shell](/docs/?scope=studio&doc=ui-primitive-list-shell)
- [UI Primitive: Toolbar](/docs/?scope=studio&doc=ui-primitive-toolbar)
- [UI Primitive: Modal Shell](/docs/?scope=studio&doc=ui-primitive-modal-shell)

These are the first primitives that should become predictable enough to reuse without re-designing them in each task.

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

## Primitive Doc Structure

Each primitive doc should stay simple but complete enough to guide implementation.

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

If a primitive grows more complex, add detail inside its own doc rather than expanding this index into a large framework document.

## Visual Reference Assets

UI screenshots and reference images for this catalogue should live in the repo under:

- `assets/docs/ui-catalogue/panel/`
- `assets/docs/ui-catalogue/button/`
- `assets/docs/ui-catalogue/input/`
- `assets/docs/ui-catalogue/list-shell/`
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

When a new shared element appears repeatedly, add a dedicated child doc here rather than folding it into a general CSS or framework note.

That keeps the viewer tree visible and scalable as the UI system grows.
