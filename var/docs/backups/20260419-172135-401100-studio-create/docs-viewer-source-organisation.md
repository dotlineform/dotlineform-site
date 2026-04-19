---
doc_id: docs-viewer-source-organisation
title: Source Organisation
last_updated: 2026-04-19
parent_id: docs-viewer
sort_order: 20
---

# Docs Viewer Source Organisation

## Purpose

This document records how source docs are currently organised for the shared Docs Viewer.

It covers:

- the current source roots
- how docs are grouped into trees
- how that organisation maps onto scope-owned generated outputs

It does not define the detailed schema of the generated JSON payloads.

## Current Source Roots

The shared Docs Viewer currently serves two separate source trees.

Studio docs source root:

- `_docs_src/`

Library docs source root:

- `_docs_library_src/`

Each scope owns its own source-doc tree and generated output tree.
The shared viewer does not merge those scopes into one combined docs corpus.

Both source roots are now flat:

- Studio docs: `_docs_src/*.md`
- Library docs: `_docs_library_src/*.md`

## Current Tree Model

Each source doc declares a `doc_id` and can optionally declare a `parent_id`.

Current tree rules:

- a blank `parent_id` makes a top-level document within that scope
- a populated `parent_id` places the document under that parent
- `sort_order` controls sibling ordering
- if `sort_order` is equal or absent, the viewer falls back to title and `doc_id`

This gives each scope its own hierarchical navigation tree without requiring separate viewer code.

## Current Section Organisation

Within the Studio source root, top-level parent docs group documentation by implementation area, including:

- `architecture`
- `config`
- `data-models`
- `design`
- `scripts`
- `docs-viewer`
- `search`
- `studio`

Unpublished working docs and historical notes also live in the same flat root and stay out of the published viewer through `published: false`.

Examples:

- `backlog.md`
- `ideas.md`
- `design-backlog.md`
- `search-config-architecture.md`

Archive remains a normal viewer-tree concept through the reserved `_archive` doc, not through a special storage folder.

## Current Management-Relevant Constraint

The flat Studio source layout is now part of the live Docs Viewer contract.

Current effect:

- Studio file storage no longer carries section meaning
- tree structure comes only from `doc_id`, `parent_id`, and `sort_order`
- `_archive` remains meaningful as a reserved system doc in the viewer tree

Important builder consequence:

- the docs builder still resolves relative markdown links from each file's `source_path`
- any future source-layout change must review or rewrite source-relative `.md` links if nested paths are reintroduced

## Current Generated Output Boundary

The docs builder writes scope-owned viewer data under:

- `assets/data/docs/scopes/studio/`
- `assets/data/docs/scopes/library/`

At a high level, each scope currently has:

- one generated docs index for the tree
- one generated per-doc payload for each published source doc

This is why the shared runtime can stay generic: it consumes the same kind of scope-owned output for each docs scope.

Detailed payload shape and rationale are intentionally left out of this section.

## Practical Documentation Rule

When updating Docs Viewer docs:

- document shared viewer behavior here if it applies to both Studio and Library
- document route-shell or scope differences here if they affect how the common module is wired
- document builder implementation in [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- leave payload-schema detail for [Shared Patterns](/docs/?scope=studio&doc=data-models-shared), [Studio Scope](/docs/?scope=studio&doc=data-models-studio), and [Library Scope](/docs/?scope=studio&doc=data-models-library)

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Data Models](/docs/?scope=studio&doc=data-models)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
