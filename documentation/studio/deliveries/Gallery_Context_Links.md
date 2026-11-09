---
draft: false
doc_id: d-20261109-210438-b1418b
title: Gallery Context Links
added_date: "2026-11-09 21:04:38"
last_updated: "2026-11-09"
summary: Link Gallery Media View to Context documents through authored Gallery references and direct Work membership.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Gallery Context Links

## Current And Next State

Proposed under [Planned Features](../Planned_Features.md). The first delivery adds automatic **Context** links to Gallery Media View in Working and Public. The agreed match rules are below. Readiness needs to settle how Docs Build carries the reference facts through its selected document and publication paths. The document-level Gallery picker follows as a separate authoring decision.

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

The preferred carrier to evaluate at readiness is the existing Context manifest. It already supplies titles, selected row replacement and public membership projection. Today it is prepared before body references are available, so confirm how to carry the completed references into that projection without another parse, per-document reads or a second manifest pass. If that requires broad changes to generation, evaluate one compact Docs-owned artifact on the existing publication queue. Choose one carrier. Reuse already loaded reader data where available and settle how Gallery reads pick up completed Context saves during the same viewer session.

Gallery membership comes from the exact Gallery record that Media View already loads. Once an updated Gallery record reaches the viewer, the match follows its membership without rebuilding Context documents or loading the member Work documents. The [Catalogue Media View](../Catalogue_Media_View.md#gallery-presentations) and [Related Links](../Related_Links.md#generated-data-and-freshness) documents describe the existing inputs.

## Reader Flow

Open a Gallery from the Catalogue report, a Work or a Context link. Its Media View shows a compact **Context** list alongside the Gallery information, independent of thumbnail paging. Following a title opens that exact Context document. A Context document can provide its own way into the Gallery through an inline Media View link or its Related Links section.

For Working review, draft [kylie](/docs/?collection=works&doc=d-20261109-191549-f0d87d) should appear on Gallery `084`, *kylie structures*, through its direct token. [3 symbols](/docs/?collection=works&doc=d-20260801-212422-df11f3) should appear on *3 symbols* and *3 symbols - cards* through Work image references. Public review uses eligible documents and confirms that the draft is absent.

## Delivery Steps

- [ ] **GCL.0 Readiness.** Confirm the reference carrier, the existing selected Save/Rebuild/Import/Delete and eligibility paths that maintain it, and the reader's load and refresh boundary. Agree the initial Context-only generation and public release order. Stop for review if the change requires a wider generation or publication refactor.
- [ ] **GCL.1 Generate and hand off the Docs data.** Carry completed references into targeted and full Context output. Cover title changes, last-reference removal, deletion and eligibility changes through existing operation owners. Inspect selected generated output and queue effects with a targeted dry run and an agreed initial Working generation.
- [ ] **GCL.2 Display the links.** Render deduplicated exact Context destinations in Gallery Media View. Confirm direct and Work-derived matches, empty results, a document matched through both rules, page changes and normal navigation. Use focused lint, the public runtime projection and site validation, plus manual review in Working and public preview. Confirm that a Gallery membership change affects the next read of the updated Gallery record.
- [ ] **GCL.3 Code review.** Apply the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) to the selected build, reader requests, eligibility handoff and missing-data behavior. Record the selected evidence and any implementation decisions. Test changes need their own agreed specification.
- [ ] **GCL.4 Closeout.** Record Working and public acceptance, move shipped behavior to Catalogue Media View and retain this proposal until its release and picker follow-on have been reconciled. Publish and public deployment have their usual separate gates.

## Follow-On

Consider a document-level **Related galleries** picker for an essay, note or other Context document that belongs with a Gallery without an inline reference. Reuse exact Gallery IDs from the existing picker data and save the selection in the document's canonical metadata. Build would carry those selections into the same Gallery-to-Context data, and `[[links|…]]` could show the selected Galleries alongside the document's other related links. A Gallery backlink would work even when the Context document has no directive. Agree the authoring control, label resolution and removal behavior in the picker delivery.
