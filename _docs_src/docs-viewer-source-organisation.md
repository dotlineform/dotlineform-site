---
doc_id: docs-viewer-source-organisation
title: "Source Organisation"
last_updated: 2026-04-23
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
- `user-guide`

Unpublished working docs and historical notes also live in the same flat root and stay out of the published viewer through `published: false`.

Examples:

- `backlog.md`
- `ideas.md`
- `design-backlog.md`
- `search-config-architecture.md`

Archive remains a normal viewer-tree concept through the reserved `_archive` doc, not through a special storage folder.

## Guidance Split

The current docs set now distinguishes between two different documentation jobs:

- technical reference docs for contracts, implementation details, and generated-output behavior
- practical user guidance for concrete editing tasks and copy-paste usage examples

Current rule:

- practical how-to guidance should live under [User Guide](/docs/?scope=studio&doc=user-guide)
- technical subsystem docs should link to that guidance rather than burying task-level instructions inside implementation detail

Example:

- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images) explains where docs images should be saved and exactly what syntax to type
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder) remains the technical reference for token resolution and build behavior

## Current Management-Relevant Constraint

The flat Studio source layout is now part of the live Docs Viewer contract.

Current effect:

- Studio file storage no longer carries section meaning
- tree structure comes only from `doc_id`, `parent_id`, and `sort_order`
- `_archive` remains meaningful as a reserved system doc in the viewer tree
- `_archive` is structural in the viewer runtime and redirects to its first child doc instead of loading its own payload
- if `_archive` has no children, viewer links and direct routes fall back to the scope's normal default doc

Important builder consequence:

- the docs builder still resolves relative markdown links from each file's `source_path`
- any future source-layout change must review or rewrite source-relative `.md` links if nested paths are reintroduced

Current runtime reason:

- the generated per-doc payload path for `_archive` would be `_archive.json`
- Jekyll does not publish that leading-underscore asset path reliably under `_site`
- the viewer therefore treats `_archive` as a non-loadable section node rather than changing the reserved `doc_id` contract

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
- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Data Models](/docs/?scope=studio&doc=data-models)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
