---
draft: false
doc_id: d-20260930-221742-069a8a
title: Related Links Delivery
added_date: "2026-09-30 22:17:42"
last_updated: "2026-11-18"
summary: Deliver the editable related-links directive and retire the separate per-document Links view.
ui_status: in-progress
parent_id: d-20260930-195002-b3417e
---
# Related Links Delivery

The editable directive shipped and the separate per-document Links view was retired. The recorded manual acceptance for the directive remains open. The later pinning delivery has its own acceptance record. [Current Related Links behaviour](../reference/Related_Links.md) · [Info panel delivery](../deliveries/Info_Panel_Links_And_Pinning_Delivery.md)

On 2026-10-01, saving `10,000` exposed a build-order defect: Links JSON already named `compressed` while the generated section still omitted it. Moving the shared refresh before rendering fixed the exact Works build, which wrote only the document payload and showed `3 symbols` and `compressed`. The ordinary-document dry run covered 42 sources and reported no payload or relationship changes. Focused lint, syntax, site projection and validation passed in the delivery. A later targeted build verified `kylie`'s Gallery `084` row, kept the inline search query and removed the former relationship from both endpoints. [Consolidated delivery record](../deliveries/Media_View_And_Document_Relationships_Review.md)

- [ ] Record local acceptance of directive insertion, editable or absent heading, icon/list appearance, outgoing additions/removals, empty sections, exact navigation and incoming-link freshness after Full Build. Review Gallery activation from the document and pin, including Back.
- [ ] Close out this record after the user review. The retired-view test contracts are tracked independently. [Test follow-ups](Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)
