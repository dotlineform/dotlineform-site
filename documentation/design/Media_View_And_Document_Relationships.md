---
draft: false
doc_id: d-20261118-161600-68ddab
title: Media View And Document Relationships
added_date: "2026-11-18 16:16:00"
last_updated: "2026-11-18"
summary: Decisions about media navigation, document relationships and reusable authored reference identities.
parent_id: d-20261118-151521-a0f9c3
---
# Media View and document relationships

## Media navigation and document reading

The Gallery study established that the invoking gallery supplies the browsing sequence. Previous and Next can then use the already loaded membership, read the exact Work on selection and return the reader to the page they were exploring. A Work can belong to several Galleries and can have a Series-relevant Gallery without being a member. The separate authored Series–Gallery pair makes that distinction explicit, including for curated Galleries that span several Series. [Gallery study](../deliveries/Gallery_Design.md) · [Catalogue source model](../reference/Catalogue_Source_Model.md) · [Current presentation](../reference/Catalogue_Media_View.md)

The document model makes the Work's Catalogue page the exact document endpoint. Work media references can therefore contribute document edges even when there is no Context document for the Work. A Gallery has a media identity and no corresponding Gallery document. Its authored association can produce a Gallery opener and Context matches without manufacturing a document edge. Projects can reuse the same typed identities while deriving its own Series and folder associations. [Work relationship delivery](../deliveries/Catalogue_Token_Links_Delivery.md) · [Subject retirement](../deliveries/Subject_Retirement.md#existing-reference-inputs-for-projects) · [Related Links](../reference/Related_Links.md)

Work Media View's caption is oriented around the selected image, its browsing sequence and Context that mentions the exact Work. The `cat.` link leads to the document and its broader relationship section. This describes the shipped division. The records reviewed contain no product decision permanently ruling out the full relationship list in Media View. [Current link sources](../reference/Catalogue_Media_View.md#what-links-appear) · [Delivery evidence](../deliveries/Media_View_And_Document_Relationships_Review.md)

## A generated list and a pinned copy

The former Links-view proposal would have mixed document and media destinations and added a Media View return path through that view. The September change chose a compact list of document relationships with a pinned reading companion. The later Related Links delivery embedded the list at an author-chosen position and retired the separate view. Rendering from persisted relationship records reuses maintenance already done by Build and lets readers open the list and pin from the document they have loaded. Generated rows stay outside authored-link collection so displaying an incoming edge cannot manufacture a reciprocal edge. [Stopped Links-view proposal](../deliveries/Links_View_Semantic_Tokens_Delivery.md#superseded) · [Accepted Info panel delivery](../deliveries/Info_Panel_Links_And_Pinning_Delivery.md) · [Related Links acceptance](../_working/Related_Links_Delivery.md)

## Occurrence identity and presentation

Store the exact target and presentation choices in each source occurrence. A Work image, a labeled Media View opener and an ordinary link serve different reading purposes and can refer to the same Work. Editable occurrences keep authored text and layout while allowing generated Work facts to change on rebuild. The chooser already has the exact IDs and titles it needs from the adopted Work manifest and Gallery index. This made the extra persisted target lookup redundant. Build and activation retain their selected presentation reads. [Original reference concept](../deliveries/Semantic_Tokens_Concept.md) · [Consumer studies](../deliveries/UAC_3_Findings.md) · [Lookup retirement](../deliveries/Catalogue_Authoring_In_Docs_Viewer.md) · [Current source forms](../reference/Document_And_Catalogue_References.md)
