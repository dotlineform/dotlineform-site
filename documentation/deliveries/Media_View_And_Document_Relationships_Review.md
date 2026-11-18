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

- **Document Related Links and pinning.** Related Links replaced the separate per-document Links view. The 1 October targeted build of `10,000` verified the ordering fix that made `compressed` appear in the generated section during the same build as its graph update. Reader pinning was accepted separately on 1 October. A later targeted build verified the Gallery `084` row in `kylie`, including preservation of its authored Catalogue search query. [Related Links delivery](../_working/Related_Links_Delivery.md) · [Pinning acceptance](Info_Panel_Links_And_Pinning_Delivery.md)
- **Media View Context links.** Gallery Context rows landed in `33c8925d6c`. Work Context rows landed in `6d1664a4c0` alongside scoped search. The current view uses the referring Context manifest and an exact Work or Gallery match. The full Related Links section is on the Work's Catalogue document. [Current behaviour and diagnosis](../reference/Catalogue_Media_View.md#what-links-appear) · [Scoped Search delivery](Public_Index_Search_Scopes.md#3-verify-the-cutover-locally)
- **Catalogue picker lookup retirement.** The old private generated lookup, standalone builder and browser loader were removed. The bounded test retirement removed the three tests of that generator in `test_semantic_target_lookup.py` and lookup-specific CLI and fixture setup. That work used lint, syntax, registry and diff review. It did not run or certify the retained scope-era tests. The active chooser response still uses `docs_semantic_token_target_lookup_v2`. [Catalogue authoring delivery](Catalogue_Authoring_In_Docs_Viewer.md) · [Current chooser](../reference/Document_And_Catalogue_References.md#registry-and-lookups)

## What remains open

The proposal for media entries and Media View → Links return was stopped before implementation when the direction changed to document relationships and pinning. It concerned the former Links view. The reviewed records contain no scheduled follow-on to put the full document relationship list on Work Media View. [Stopped proposal](Links_View_Semantic_Tokens_Delivery.md#superseded) · [Design decisions](../design/Media_View_And_Document_Relationships.md)

The original directive and Related Galleries records still call for local manual review. Code naming, registry ownership and out-of-date tests are tracked as separate follow-ups. [Related Links acceptance](../_working/Related_Links_Delivery.md) · [Related Galleries acceptance](../_working/Related_Galleries.md) · [Code and file follow-ups](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)
