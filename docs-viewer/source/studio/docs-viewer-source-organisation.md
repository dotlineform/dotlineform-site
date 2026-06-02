---
doc_id: docs-viewer-source-organisation
title: Source Organisation
added_date: 2026-04-23
last_updated: "2026-05-13 20:20"
parent_id: docs-viewer
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

The shared Docs Viewer currently serves three separate source trees.

Studio docs source root:

- `docs-viewer/source/studio/`

Analysis docs source root:

- `docs-viewer/source/analysis/`

Library docs source root:

- `docs-viewer/source/library/`

Each scope owns its own source-doc tree and generated output tree.
The shared viewer does not merge those scopes into one combined docs corpus.

Studio and Library source roots are flat:

- Studio docs: `docs-viewer/source/studio/*.md`
- Library docs: `docs-viewer/source/library/*.md`

Analysis allows nested source folders:

- Analysis docs: `docs-viewer/source/analysis/**/*.md`

Analysis folder names are source-organisation affordances for future helpers such as series/work analysis lookup. Viewer navigation still comes from `doc_id` and `parent_id`.

## Current Tree Model

Each source doc declares a `doc_id` and can optionally declare a `parent_id`.

Current tree rules:

- a blank `parent_id` makes a top-level document within that scope
- a populated `parent_id` places the document under that parent
- root siblings and each parent’s children are sorted case-insensitively by `title`
- `doc_id` is the stable tie-breaker when titles match

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

Working docs and historical notes that should stay out of public/default discovery use `viewable: false`.

Examples:

- `backlog.md`
- `ideas.md`
- `design-backlog.md`
- `search-config-architecture.md`

## Guidance Split

The current docs set now distinguishes between two different documentation jobs:

- technical reference docs for contracts, implementation details, and generated-output behavior
- practical user guidance for concrete editing tasks and copy-paste usage examples
- technical subsystem docs should link to that guidance rather than burying task-level instructions inside implementation detail

Example:

- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images) explains where docs images should be saved and exactly what syntax to type
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder) remains the technical reference for token resolution and build behavior

## Current Management-Relevant Constraint

The flat Studio source layout is now part of the live Docs Viewer contract.

Current effect:

- Studio file storage no longer carries section meaning
- tree structure comes only from `doc_id` and `parent_id`; sibling order comes from generated title ordering

Important builder consequence:

- the docs builder still resolves relative markdown links from each file's `source_path`
- any future source-layout change must review or rewrite source-relative `.md` links if nested paths are reintroduced

## Current Generated Output Boundary

The docs builder writes scope-owned viewer data under:

- `docs-viewer/generated/docs/studio/`
- `assets/data/docs/scopes/analysis/`
- `assets/data/docs/scopes/library/`

At a high level, each scope currently has:

- one generated docs index for the tree
- one generated per-doc payload for each included source doc

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
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)