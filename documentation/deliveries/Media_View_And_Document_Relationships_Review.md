---
draft: false
doc_id: d-20261118-161600-29ce37
title: Media View And Document Relationships Review
added_date: "2026-11-18 16:16:00"
last_updated: "2026-11-18"
summary: What shipped, what was superseded and which reviews remain open for Media View and document relationships.
ui_status: done
parent_id: d-20261118-151521-a0f9c3
---
# Media View and document relationships review

## What shipped

- **Document Related Links and pinning.** Related Links replaced the separate per-document Links view. On 1 October, saving `10,000` exposed a build-order defect: Links JSON named `compressed` while the rendered section omitted it. Moving the shared refresh before rendering fixed the exact Works build, which wrote only the document payload and displayed `3 symbols` and `compressed`. An ordinary-document dry run covered 42 sources without payload or relationship changes. Focused lint, syntax, public projection and site validation passed. Reader pinning was accepted separately on 1 October. A later targeted build verified the Gallery `084` row in `kylie`, preserved its authored Catalogue search query and removed the former relationship from both endpoints. [Current Related Links](../reference/Related_Links.md) · [Pinning acceptance](Info_Panel_Links_And_Pinning_Delivery.md)
- **Media View Context links.** Gallery Context rows landed in `33c8925d6c`. Work Context rows landed in `6d1664a4c0` alongside scoped search. The current view uses the referring Context manifest and an exact Work or Gallery match. The full Related Links section is on the Work's Catalogue document. [Current behaviour and diagnosis](../reference/Catalogue_Media_View.md#what-links-appear) · [Scoped Search delivery](Public_Index_Search_Scopes.md#3-verify-the-cutover-locally)
- **Catalogue picker lookup retirement.** The old private generated lookup, standalone builder and browser loader were removed. The bounded test retirement removed the three tests of that generator in `test_semantic_target_lookup.py` and lookup-specific CLI and fixture setup. That work used lint, syntax, registry and diff review. It did not run or certify the retained scope-era tests. At delivery, the chooser response used `docs_semantic_token_target_lookup_v2`. [Catalogue authoring delivery](Catalogue_Authoring_In_Docs_Viewer.md) · [Current chooser](../reference/Document_And_Catalogue_References.md#catalogue-target-lookup)

## Related Galleries Closeout

The September implementation seeded 302 exact Series–Gallery pairs for 302 Galleries across 139 Series. Refresh produced the verified `catalogue_series_galleries_index_v1` covering all 139 valid Series, and the public inventory selected its prepared bytes. Gallery `307` had no saved pair in the recorded local read. Review confirmed separate membership/relevance ownership, pair removal with Gallery/Series deletion and selected Gallery reads on activation. Focused lint, syntax, JSON, source and whitespace checks were recorded. These are historical results, with the full implementation record in Git at `c76f6608ef:documentation/studio/Related_Galleries.md`.

On 18 November 2026 the user confirmed Related Galleries should be considered done and requested retirement. Its local acceptance and retain-or-retire gates are closed; individual visual scenarios were not separately itemised, and this retirement ran no browser review. Current behaviour remains with [Media View](../reference/Catalogue_Media_View.md#what-links-appear) and the [Series–Gallery source model](../reference/Catalogue_Source_Model.md), with [design rationale](../design/Media_View_And_Document_Relationships.md) preserved separately. References and document-ID/parent dependencies were checked before removing the Working record.

## Related Links Closeout

On 18 November 2026 the user confirmed Related Links Delivery was done and requested retirement. Its remaining directive acceptance and closeout gates are closed. Individual insertion, heading, list, navigation and freshness scenarios were not separately itemised, and this retirement ran no browser review. Useful same-build freshness evidence is preserved above; [current behaviour](../reference/Related_Links.md) and [design rationale](../design/Media_View_And_Document_Relationships.md) retain their own owners. References and document-ID/parent dependencies were checked before removing the Working record.

## What remains open

The proposal for media entries and Media View → Links return was stopped before implementation when the direction changed to document relationships and pinning. It concerned the former Links view. The reviewed records contain no scheduled follow-on to put the full document relationship list on Work Media View. [Stopped proposal](Links_View_Semantic_Tokens_Delivery.md#superseded) · [Design decisions](../design/Media_View_And_Document_Relationships.md)

Related Links and Related Galleries are complete as recorded above. The follow-up delivery records the code naming and registry ownership changes. The separate site test retirement resolved the outdated test findings. [Code and file follow-ups](Documentation_Code_Follow_Ups.md#code-and-file-follow-ups) · [Site test retirement](Review_Test_Policy_And_Checks.md)
