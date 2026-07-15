---
doc_id: analytics-shareable-content-blocks-concept
title: Shareable Content Blocks Concept
added_date: 2026-06-23
last_updated: 2026-07-15
ui_status: draft
parent_id: analytics-shareable-content-blocks
viewable: true
---
# Shareable Content Blocks Concept

Status: proposed

## Summary

Define a managed workflow for extracting bounded source content, sharing it with an external or cross-app process, reviewing returned text, and writing approved changes back to canonical local source.

This is adjacent to semantic tokens but should not be implemented as a semantic token feature.
Semantic tokens render deterministic build-time content.
Shareable content blocks are source-editing and data-exchange workflows.

## Ownership

Primary ownership should sit with Data Sharing and Analytics:

- `data-sharing/` owns package contracts, adapter routing, external exchange records, returned-package staging, review artifacts, provenance, and import/writeback rules.
- `analytics-app/` owns analytics/tag-domain meaning, canonical analytics data, prompt/context construction, and any tag/work relationship semantics.
- Docs Viewer supports the workflow when the block lives in a Docs Viewer Markdown document, but it does not own the meaning of the data or the transformation.

Docs Viewer support should be limited to:

- identifying safe source block boundaries in Markdown source
- exposing the selected block text and source document identity to a management workflow
- hosting a review/writeback UI when the source document is already being edited in Docs Viewer
- rebuilding the document after a confirmed local source write

Docs Viewer should not:

- call external services during a docs build
- decide what analytics/tag data means
- own data-sharing package formats
- silently rewrite source from returned content
- treat returned external text as builder output

## Block Shape

The source format should be explicit, easy to scan, and safe to parse without Markdown rendering.

Possible shape:

```md
<!-- shareable:block start id=tag-summary source=tag:slow-looking workflow=analysis-summary-v1 -->
Current authored or generated text.
<!-- shareable:block end -->
```

The block body is ordinary source text.
The markers define an addressable managed region.

Open syntax decisions:

- whether marker names should be `shareable:block`, `managed:block`, or another term
- required attributes
- whether nested blocks are prohibited
- whether block ids are unique per document, per scope, or globally
- whether attributes should include source ids directly or reference a separate workflow config record

## Workflow Model

The expected workflow is:

1. Author marks a source region as a shareable content block.
2. A management action extracts the block body plus block metadata.
3. The workflow owner builds a package using local canonical data and workflow config.
4. The package may be sent to an external service or another local process.
5. Returned text is staged as a review artifact.
6. The author reviews a diff between current block content and returned content.
7. Approved returned text replaces only the block body.
8. The source document is rebuilt through the normal Docs Viewer rebuild path.

External calls and returned text handling should be explicit management actions, not automatic builder behavior.

## Data Sources

Likely first-class source data:

- `analytics-app/data/canonical/tag-registry.json`
- `analytics-app/data/canonical/tag-assignments.json`
- `analytics-app/data/canonical/tag-aliases.json`
- `analytics-app/data/canonical/tag-groups.json`
- Docs Viewer source Markdown containing the block
- generated reference artifacts or search indexes only when a workflow explicitly declares them as read-only context

The block itself should not encode every data dependency.
It should provide a stable source anchor; the workflow config should decide which canonical data is packaged.

## Relationship To Semantic Tokens

Semantic tokens and shareable blocks can coexist, but they need different guarantees.

Semantic tokens:

- are deterministic render directives
- resolve during the Docs Viewer build
- read known local data
- produce predictable HTML and reference artifacts
- do not rewrite source Markdown

Shareable content blocks:

- are bounded source regions
- may be exported to external services or local processors
- may return replacement text
- require review, provenance, and writeback controls
- update canonical source only after explicit approval

The two systems may share some registry concepts, such as declared kinds or data-source ids, but they should not share the same parser or builder execution path unless a future design proves that boundary is safe.

## Implementation Questions

- Where should workflow config live: `data-sharing/config/`, `analytics-app/`, or a shared registry?
- Does Data Sharing need a new `content-blocks` adapter, or should this be an extension of the existing documents/tags adapters?
- Should returned content be reviewed in Analytics, Docs Viewer, or a Data Sharing review route?
- What provenance record is required before writeback?
- How should stale returned packages be detected when the source block changed after export?
- Should block extraction work on saved source only, or the current unsaved editor buffer?
- Should block writeback require the document to be open in Docs Viewer source mode?
- How should conflicts be reported when block markers are missing, duplicated, or changed?

## V1 Candidate

A narrow first slice could support:

- one block syntax
- one Analytics-owned workflow for tag summary text
- extraction from saved Docs Viewer Markdown source
- package creation through Data Sharing
- returned text staged under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`
- diff review before writeback
- writeback limited to replacing the body between unchanged start/end markers
- rebuild through the existing Docs Viewer management rebuild path

Out of scope for v1:

- automatic external calls during docs build
- generated source edits without review
- nested blocks
- multi-block batch writeback
- public-site runtime behavior
- interpreting arbitrary source Markdown outside declared block boundaries

## Risks To Watch

- ownership drift could make Docs Viewer responsible for analytics meaning or external-service policy
- returned text could overwrite local source without enough provenance or conflict checking
- block syntax could become a hidden programming language inside Markdown comments
- unsaved editor-buffer extraction could conflict with source-on-disk review and writeback
- external-service workflows could make local builds non-deterministic if they leak into builder behavior
