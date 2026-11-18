---
draft: false
doc_id: d-20261118-235300-3e840d
title: Reader And Authoring Refinements
added_date: "2026-11-18 23:50:00"
last_updated: "2026-11-18"
summary: Preserved November reader and image-authoring implementation evidence from the retired planning register.
parent_id: d-20260419-000000-d2e47b
---
# Reader And Authoring Refinements

These 12 November 2026 entries were preserved from Planned Features when its method moved to Development and its register retired. They record bounded implementation/static evidence and explicit manual limits, not new acceptance.

## Catalogue Image Sizes

Left-aligned Catalogue image sizing was implemented and reviewed. Build derives thumbnail identity from Work ID and the loaded rendition policy. Review traced the 50% candidate set, 33% single primary, thumbnail native width and selected Publish/Export assets. A read-only Work `00638` diagnostic confirmed three prepared selections and packaged assets, including Export's larger link target. Lint, compilation, whitespace, public projection and site validation passed. Dialog/layout/live actions remained manual after service restart and hard reload. [Current forms](../reference/Document_And_Catalogue_References.md#catalogue-image)

## Numeric Title Search

Working generation and retained title updates shared title-only numeric matching. Review kept other fields and technical-compound components outside it. A Working Search build queued its output and added 232 bytes of numeric postings across 156 documents. Generated-index inspection found `10,000` and `10000` returned **10,000**, while `10` did not match by prefix. Lint, compilation, whitespace, projection and site validation passed. This record claims no subsequent Publish or deployment. [Current query semantics](../reference/Docs_Search_Tokenizer.md#query-semantics)

## Index Follows Reading

The sidebar adopted displayed-record/configuration ownership in place of route-supplied selection and separate state. Static review covered fresh/retained navigation, loading/errors and Search/Recent-to-tree transitions. Hidden tracking deferred ancestor expansion/scroll until the tree became visible. JavaScript lint, whitespace, projection and site validation passed; actual navigation/tree reveal remained manual after reload. [Current retained views](../reference/Reader_Discovery_And_Return.md#retained-index-views)

## Image Text Wrapping

Ordinary and Catalogue image modals shared placement controls and serialized both wrapping choices in the existing field; the ordinary modal used the wider standard card. Review followed both rendering paths and Image Detail, with reading-column-dependent floats and clearing headings. Existing authoring/media owners served both forms. JavaScript/Python lint, compilation, whitespace, projection and site validation passed. Browser layout and live Source Save remained manual after restart/reload. [Current wrapping](../reference/Document_And_Catalogue_References.md#wrap-body-text)
