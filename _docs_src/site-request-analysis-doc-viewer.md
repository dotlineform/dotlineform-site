---
doc_id: site-request-analysis-doc-viewer
title: "Analysis Docs Viewer Request"
added_date: 2026-04-26
last_updated: 2026-04-26
parent_id: change-requests
sort_order: 150
---
# Analysis Docs Viewer Request

Status:

- implemented

## Summary

This change request tracks a future public-facing Analysis docs viewer.

The Analysis viewer is a separate publication surface for documents about catalogue data, tags, LLM analysis, series analysis, and related interpretive material.

It should not be merged into Library or Studio docs.

## Goal

Create a public Analysis docs scope at:

- `/analysis/`

The desired end state is:

- Analysis has its own public viewer route
- Analysis has its own source document tree
- Analysis has its own generated docs payloads
- Analysis can publish documents about catalogue data, tags, dimensions, LLM analysis, and series analysis
- Library remains a separate public reading/research scope
- Studio docs remain an internal implementation and workflow reference scope
- internal Studio Analytics routes can keep their current naming and URLs

## Terminology

Official public docs scope name:

- `analysis`

Public route:

- `/analysis/`

Internal Studio domain:

- `analytics`
- `/studio/analytics/`

The internal Analytics route and docs can remain as they are for now. That avoids unnecessary route churn and keeps this request focused on the future public Analysis viewer.

## Scope Boundary

Analysis is for interpretive and analytical documents related to the portfolio data model.

Likely content:

- catalogue-data interpretation
- tag and dimension documentation
- LLM-assisted analysis outputs
- series-level analysis
- comparative portfolio analysis
- notes derived from structured catalogue or tag data

Not Analysis:

- Library essays and independent reading documents
- Studio implementation docs
- Studio operator workflow docs
- canonical catalogue page prose for works and series

## Relationship To Work And Series Prose

Work and series prose source migration is a separate request.

Work and series prose should continue to publish through public catalogue pages:

- `/works/<work_id>/`
- `/series/<series_id>/`

Analysis may later contain separate interpretive documents about works or series, but those should not replace canonical catalogue prose.

Example distinction:

- work prose source: published on `/works/00008/`
- analysis document: published on `/analysis/`, possibly with `doc_id: series-001`

## Possible Source And Output Model

The exact model is open.

Source root:

- `_docs_src_analysis/`

Generated output:

- `assets/data/docs/scopes/analysis/index.json`
- `assets/data/docs/scopes/analysis/by-id/<doc_id>.json`

The first implementation follows the existing Studio and Library docs model, with one source-layout exception: Analysis allows nested Markdown files under `_docs_src_analysis/`.

## Future Family Model

The viewer may eventually need the idea of document families.

Expected families could include:

- `series`
- `works`
- `tags`
- `dimensions`
- `llm`

The clearest early family expectation is series analysis.

Example:

- family: `series`
- source folder: `series/`
- doc ID: `series-001`

The source folders now exist as a future affordance, but viewer organisation remains controlled by front matter.

## Benefits

Expected benefits:

- public analysis content gets a clear home
- Library stays focused on its own reading/research corpus
- Studio docs stay focused on implementation and operations
- analysis documents can use shared docs rendering and search infrastructure
- future LLM review/export workflows can target a dedicated scope
- internal Studio Analytics routes do not need to be renamed to create the public Analysis route

## Risks And Tradeoffs

Main risks:

- the name difference between internal `analytics` and public `analysis` needs clear documentation
- adding families too early could overcomplicate the first viewer implementation
- not adding family support early may require a later source-layout migration
- analysis content may overlap with catalogue prose unless ownership rules are explicit
- search behavior needs a clear boundary from Library and catalogue search

The main tradeoff is between building a simple scope first and designing the family model upfront.

The implemented first step is a simple Analysis docs scope with nested source folders allowed for future series/work helpers.

## Open Questions

1. Should series analysis docs be generated from data, authored manually, or both?
2. Should Analysis docs link back to catalogue routes using structured metadata?
3. What source fields distinguish an analysis doc from canonical catalogue prose?
4. Should internal Studio Analytics link to public Analysis later?
5. When real content exists, should Analysis need family-aware navigation beyond metadata-driven folders?

## Proposed Implementation Steps

### Task 1. Define The Analysis Scope Contract

Status:

- implemented

Define:

- source root
- generated output root
- public route
- viewer default doc
- search behavior
- public/manage visibility rules
- relationship to internal Studio Analytics

### Task 2. Add The Public Analysis Route

Status:

- implemented

Add a public route at:

- `/analysis/`

The route should use the shared docs viewer runtime where practical.

### Task 3. Add Analysis Docs Build Support

Status:

- implemented

Configure the docs builder to support an `analysis` scope.

The first implementation should prefer the simplest model compatible with Studio and Library unless family support is clearly required immediately.

### Task 4. Add Initial Analysis Content

Status:

- implemented

Add a small seed set of Analysis docs so the route has real content to validate against.

Good first candidates:

- Analysis scope overview
- tag/dimension overview
- one series analysis draft

### Task 5. Decide Family Support From Real Content

Status:

- pending

After initial content exists, decide whether Analysis needs:

- flat source docs with family-prefixed IDs
- family folders under one source root
- separate sub-indexes by family
- family-aware viewer navigation

### Task 6. Update Docs And Search Guidance

Status:

- implemented

Update relevant docs after implementation.

Likely docs:

- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## Validation Plan

Codex-run checks should include:

- docs builder dry run for `analysis`
- docs builder write run for `analysis`
- search builder dry/write checks if Analysis search is added
- Jekyll build after adding the route
- browser smoke check for `/analysis/` on desktop and mobile
- sanitization scan for changed source/docs/scripts

Manual checks should include:

- open `/analysis/`
- verify default document routing
- verify links between Analysis docs and catalogue routes
- verify Analysis does not appear inside Library
- verify internal `/studio/analytics/` still works

## Out Of Scope

- renaming internal `/studio/analytics/`
- moving Library documents into Analysis
- moving Studio implementation docs into Analysis
- replacing public catalogue prose
- solving family-aware navigation before real Analysis content exists

## Related References

- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)
