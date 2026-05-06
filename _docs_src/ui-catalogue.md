---
doc_id: ui-catalogue
title: UI Catalogue
added_date: 2026-04-21
last_updated: "2026-05-06 20:11"
parent_id: ""
sort_order: 70
---
# UI Catalogue

This section is the top-level index for shared UI primitives, composition patterns, and their live reference pages.

Use it to keep recurring elements visible as named, documented primitives and patterns rather than redesigning them inside page work.

## Route Ready State

The UI catalogue pages expose static/reference route-ready state:

- `/studio/ui-catalogue/` uses `#studioUiCatalogueRoot`
- `/studio/ui-catalogue/button/` uses `#studioUiCatalogueButtonRoot`
- `/studio/ui-catalogue/input/` uses `#studioUiCatalogueInputRoot`
- `/studio/ui-catalogue/list/` uses `#studioUiCatalogueListRoot`
- `/studio/ui-catalogue/panel/` uses `#studioUiCataloguePanelRoot`
- `/studio/ui-catalogue/reopenable-command-result/` uses `#studioUiCatalogueReopenableCommandResultRoot`
- `/studio/ui-catalogue/column-links/` uses `#studioUiCatalogueColumnLinksRoot`

These roots use `data-studio-mode="reference"` and mark ready after DOM load. The purpose is to give future primitive pages an obvious route-state contract to extend if a reference page later adds async demos or route-level controls.

The docs-viewer role of this page is to explain the catalogue method and link to child docs.
Each primitive or composition pattern should have a matching docs-viewer page for implementation, lifecycle, and ownership notes.
Published Studio catalogue pages remain the live visual references for primitives.

## Purpose

The catalogue exists to separate:

- primitive design
- page composition
- interactive behavior

When a page uses a shared element such as a `panel` or `toolbar`, the expectation should come from this catalogue first.

## Primitive Docs And Pages

Current primitives have both a docs-viewer contract and a live reference page:

- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button) / [live page](/studio/ui-catalogue/button/)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input) / [live page](/studio/ui-catalogue/input/)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list) / [live page](/studio/ui-catalogue/list/)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel) / [live page](/studio/ui-catalogue/panel/)

Add new links here when a primitive gets either a matching implementation doc or a live reference page.

## Composition Pattern Docs

Composition patterns cover UI behavior that depends on route state, server payloads, or several primitives working together.

Current pattern docs:

- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result) / [live page](/studio/ui-catalogue/reopenable-command-result/)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links) / [live page](/studio/ui-catalogue/column-links/)

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
- [UI](/docs/?scope=studio&doc=ui)
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Change Requests](/docs/?scope=studio&doc=change-requests) for UI request specs and task docs

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

## Primitive Doc And Page Structure

Each primitive should have:

- a docs-viewer child doc for purpose, contract, implementation notes, lifecycle notes, and migration ownership
- a published live page for visual references, canonical markup, variants, states, and inspectable examples

The default child-doc structure is:

- purpose
- contract
- implementation notes
- lifecycle notes
- migration notes when stable content still lives in older docs

The default live-page structure is:

- anatomy
- variants and states
- canonical markup
- visual references
- short editable notes that complement the child doc

When a primitive can compose with itself, for example nested panels or stacked list shells, include that use case explicitly rather than treating it as an out-of-scope environment issue.

Include design guidance when the success of a primitive depends not just on CSS behavior but also on how it should be composed, sized, or edited on a page.

Include common design-led overrides in the sample markup when those overrides are part of normal reuse rather than an edge case.

## List Primitive Direction

Detailed list rules now live in [List Primitive](/docs/?scope=studio&doc=ui-primitive-list).

If a primitive grows more complex, expand its matching primitive doc and keep the published page focused on live visual references and canonical examples.

## Broader Design Direction

- use this docs-viewer catalogue as the parent index
- use matching primitive and pattern docs for implementation contracts, lifecycle notes, and ownership rules
- use published primitive pages for live visual references, canonical markup, and inspectable examples
- prefer one implementation source of truth for each primitive or pattern, with live pages linking back to the matching doc

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

When a new shared element appears repeatedly, add a matching primitive doc under this page and link any published live reference page here.

That keeps the viewer tree visible and scalable as the UI system grows.
