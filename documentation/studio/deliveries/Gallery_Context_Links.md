---
draft: false
doc_id: d-20261109-210438-b1418b
title: Gallery Context Links
added_date: "2026-11-09 21:04:38"
last_updated: "2026-11-09"
summary: Link Gallery Media View to Context documents through authored Gallery references and direct Work membership.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Gallery Context Links

## Current And Next State

Development closed on 2026-11-09 after the user accepted the Working presentation and requested closeout. Publish transferred the eligible Context manifest into the tracked site, and `33c8925d6c` contains that manifest and the projected runtime. The live site still served the prior Context manifest and Media View runtime at closeout. Deploy Public and a live Gallery check remain release steps. [Catalogue Media View](../Catalogue_Media_View.md#gallery-presentations) owns the reader contract. Retain this delivery pending release and manual archive.

Context is expected to contain tens of thematic documents. The editorial path is Library ↔ Context ↔ Media View ↔ Catalogue. This guides authoring, while the automatic association producer explicitly selects the `works` collection.

## Requirements

- A Context document (`works`) qualifies for a Gallery when an authored Gallery Media View token names that exact Gallery ID, or when an authored Catalogue Work image or Work Media View token names a Work in that Gallery's direct membership. Use the complete Gallery member list across all pages. A Gallery with zero Works can still have direct document references.
- Combine the two matches into one row per Context document. Show its document title and use its exact collection and document ID. Sort A–Z by displayed title, with document ID breaking ties. Show the same **Context** list regardless of how the Gallery was opened. Omit the section when it has no rows.
- Working includes its saved drafts. Public uses the Context documents eligible under the existing Working publication policy. The existing [Related Links](../Related_Links.md) directive controls placement on the document side. Gallery-to-Context discovery uses authored references whether or not the document includes that directive.
- Keep the match rule to exact authored Catalogue targets and direct Gallery membership. Series-based relevance, report searches and document-to-document relationships belong to their separate owners.

## Deliverables And Ownership

| Owner | Deliverable |
| --- | --- |
| Docs Build | Carry distinct Work and Gallery target IDs already parsed for each Context document into compact reader data alongside document identity and title. A selected document operation replaces that document's contribution, including when the last reference is removed or the document is deleted. |
| Working publication preparation | Use the existing eligible Context membership to prepare public reference data and queue the completed artifact with its owning output. Publish transfers those bytes through the existing queue. |
| Gallery Media View | Reuse the selected Gallery record's ID and full direct membership. The browser matches the compact Docs data, orders the rows and opens exact Context destinations through normal document navigation. The existing Back action returns to the Gallery's caller. |

The existing Context manifest carries the references. Generation renders the selected collection items once, then enriches their new manifest rows before public preparation and writes. The selected row replacement also removes a deleted row or a removed last reference. Public preparation carries the new field through its existing eligibility and manifest queue. Working revalidates the saved manifest on Gallery entry so later saves are visible in the same session.

For Public, reuse Context data already loaded by the viewer or fetch the compact data on the first Gallery open, in parallel with the Gallery record. Retain it for subsequent galleries and pages in that viewer session. Each thematic document contributes its identity, title and distinct target IDs. Keeping those facts in a Docs-owned output lets one document edit, rename or eligibility change update one projection even when many Galleries link to it.

Gallery membership comes from the exact Gallery record that Media View already loads. Once an updated Gallery record reaches the viewer, the match follows its membership without rebuilding Context documents or loading the member Work documents. The [Catalogue Media View](../Catalogue_Media_View.md#gallery-presentations) and [Related Links](../Related_Links.md#generated-data-and-freshness) documents describe the existing inputs.

## Reader Flow

Open a Gallery from the Catalogue report, a Work or a Context link. Its Media View shows the Context links below the Gallery title, independent of thumbnail paging. The Context icon marks document links, and the stacked-image icon marks Gallery links in Work Media View. Following a title opens that exact Context document. A Context document can provide its own way into the Gallery through an inline Media View link or its Related Links section.

For Working review, draft [kylie](/docs/?collection=works&doc=d-20261109-191549-f0d87d) should appear on Gallery `084`, *kylie structures*, through its direct token. [3 symbols](/docs/?collection=works&doc=d-20260801-212422-df11f3) should appear on *3 symbols* and *3 symbols - cards* through Work image references. Public review uses eligible documents and confirms that the draft is absent.

## Delivery Steps

- [x] **GCL.0 Readiness.** Selected the existing Context manifest and existing publication handoff. The collection render now supplies the completed rows before preparation. Public shares a session read and Working revalidates on entry.
- [x] **GCL.1 Generate and hand off the Docs data.** The targeted *kylie* dry run scanned one source and selected one manifest update. Initial Context-only generation processed seven sources, changed the management manifest and queued the eligible public manifest. Document by-ID JSON and relationships were unchanged. The eligible manifest is 1,182 bytes and excludes the draft. A targeted Catalogue dry run for Work `00520` predicted no changes.
- [x] **GCL.2 Display the links.** Saved-data inspection confirmed *kylie* for Gallery `084` and *3 symbols* for `005` and `319`. Focused lint, public runtime projection and site validation passed. The user reviewed the Working links and accepted the final spacing. Navigation, pagination, duplicates, empty results and membership changes were not individually reported.
- [x] **GCL.3 Code review.** The [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) traced new and replaced rows, empty associations, eligibility and reader failure. The producer uses rendered references once and touches only the selected rows. The browser uses the supplied member IDs and manifest order. It needs no Work document reads, additional index or second eligibility filter. A failed Context read leaves the Gallery available and clears the failed public read for the next open. Exact route identity checks stay with the existing document link owner.
- [x] **GCL.4 Closeout.** Recorded Working acceptance and reconciled the durable Catalogue Media View document. The prepared and tracked public Context manifests match, and the Context manifest queue entry has cleared.

## Follow-On

Consider a document-level **Related galleries** picker for an essay, note or other Context document that belongs with a Gallery without an inline reference. Reuse exact Gallery IDs from the existing picker data and save the selection in the document's canonical metadata. Build would carry those selections into the same Gallery-to-Context data, and `[[links|…]]` could show the selected Galleries alongside the document's other related links. A Gallery backlink would work even when the Context document has no directive. Agree the authoring control, label resolution and removal behavior in the picker delivery.
