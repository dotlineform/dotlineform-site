---
doc_id: docs-viewer-source-organisation
title: Source Organisation
added_date: 2026-04-23
last_updated: 2026-06-05
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

Document Data Sharing reads this same source boundary through Docs Viewer-owned source context helpers.
Those helpers use scope config plus source Markdown front matter and body content, then render source content through shared Docs Viewer rendering code when export or review workflows need headings or plain text.
Generated Docs Viewer payloads are publication/runtime outputs and are not the Data Sharing document source-record input.

Normal scope source roots are flat:

- Studio docs: `docs-viewer/source/studio/*.md`
- Library docs: `docs-viewer/source/library/*.md`
- Analysis docs: `docs-viewer/source/analysis/*.md`

Nested source Markdown is not supported for normal scope discovery.
Large detail-document sets should use configured Docs Viewer sub-scopes, which keep nested detail docs out of the parent index tree and global docs search.

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

- source-relative `.md` links are unsupported; docs should link to viewer URLs with `doc=<doc_id>`
- source filenames are loader inputs only and are not emitted as generated runtime metadata

## Current Generated Output Boundary

The docs builder writes scope-owned viewer data under:

- `docs-viewer/generated/docs/studio/`
- `site/assets/data/docs/scopes/analysis/`
- `site/assets/data/docs/scopes/library/`

At a high level, each scope currently has:

- one generated `index-tree.json` payload for the tree
- one generated `recently-added.json` payload for recently-added mode
- one generated per-doc payload for each included source doc

This is why the shared runtime can stay generic: it consumes the same kind of scope-owned output for each docs scope.

Validated returned-package source and generated previews are not repository source or configured scopes. They live under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/<package_id>/`, with temporary Markdown in `source/`, inventoried files in `assets/`, and review output in `generated/`. Data Sharing creates the validated handoff; Docs Review may edit and rebuild only within that package folder and cannot promote it into canonical source.

Detailed payload shape and rationale are intentionally left out of this section.

## Practical Documentation Rule

When updating Docs Viewer docs:

- document shared viewer behavior here if it applies to both Studio and Library
- document route-shell or scope differences here if they affect how the common module is wired
- document builder implementation in [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- leave payload-schema detail for [Shared Patterns](/docs/?scope=studio&doc=data-models-shared), [Studio Scope](/docs/?scope=studio&doc=data-models-studio), and [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes)
