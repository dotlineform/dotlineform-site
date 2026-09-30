---
draft: false
doc_id: d-20260930-195002-b3417e
title: Related Links
added_date: "2026-09-30 19:50:02"
last_updated: "2026-09-30 21:39:26"
summary: Proposed author-inserted related-links directive, a sorted list with selected collection icons, and build-time relationship snapshots in document JSON.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Related Links

Status: related-links directive proposal; the collection config and Index icons are implemented in [Collection Icons Delivery](Collection_Icons_Delivery.md), with visual review pending. This feature is parented to [Planned Features](Planned_Features.md).

## Authoring Decision

An author manually inserts a related-links directive in the Source Editor where the list should appear. The directive requests the document's computed related links; the author does not maintain the individual entries. Its exact source syntax remains to be chosen.

Without the directive, the document has no related-links section. If the directive resolves to no qualifying links, it produces no visible heading, list or empty-state message. An Info panel presentation is a possible later enhancement.

## Initial Presentation

Use the document's normal content width, section heading and bulleted links. Combine incoming and outgoing document relationships into one plain list, sorted A–Z by displayed title, with exact collection/document identity providing a stable tie-break. Repeated and reciprocal links to the same target appear once; distinct documents with the same title remain distinct. Omit the document itself.

All participating collections use the same list. The presentation has no collection groups, direction labels, counts, cards or enclosing panel. Relationships come from supported authored document links; sharing a Subject or a Catalogue association does not add entries by itself. The original mock-up below remains a plain sorted list; the selected icon refinement is recorded separately.

## Rendered Mock-up

The following is an illustrative document excerpt. The titles link to existing Studio documentation so the mock-up can be viewed as ordinary rendered Markdown. The list represents the directive's generated output, rather than a list maintained in the example document's source.

---

### Document linking

Document links connect this explanation with supporting material. Related documents are listed below for further reading.

#### Related links

- [Builder](Builder.md)
- [Context Navigation](Document_Context_Navigation.md)
- [Links View](Links_View.md)
- [Source Editor Scripts](Source_Editor_Scripts.md)

---

## Selected Icons And Collection Configuration

The user selected the following artwork in [Insert Icon](/docs/?doc=d-20260930-204328-7e9969). Each related link uses the icon for its target's collection; the icon does not affect sorting or document identity.

| Target owner | SVG filename stem |
| --- | --- |
| Catalogue (`catalogue`) | `dlf-catalogue` |
| Concepts (`concepts`) | `dlf-concept` |
| Works (`works`, displayed as Context) | `dlf-context` |
| Moments (`moments`) | `dlf-moment` |
| Ordinary document | `dlf-doc` |

An extensionless `icon` value is implemented on each collection record in the existing workspace configuration, such as `"icon": "dlf-context"` for Works. [Source Organisation](Source_Organisation.md#collection-icons) owns this contract. The proposed related-links builder will read this same mapping and use the implemented [Icon Tokens](Icon_Tokens.md) renderer to embed the artwork. Ordinary targets will use `dlf-doc`.

The Index panel now marks collection report hosts with their configured collection icon, supplied through the existing browser configuration projection. Related links will share that artwork for documents within the collection. Collection icons identify collection ownership; Subject artwork remains separate. The [collection icon delivery](Collection_Icons_Delivery.md) records static verification, code review and the pending manual visual check.

## Generated Data And Freshness

The builder expands the directive into a static section in the document's generated JSON. The reader displays that prepared content without fetching a separate relationship record, collection manifest or neighbouring document to populate the list. Links retain exact document identities and follow the existing portable local/public document-routing rules.

Saving a referring document can update relationship records while leaving the referred document's embedded section unchanged. Ordinary saves retain their targeted build scope; they do not rebuild neighbouring document content merely to refresh this presentation. A full Docs Build refreshes the related-links sections across the complete configured document set that can contribute relationships, including participating collections. Link additions, removals and title changes become visible in the refreshed sections.

A full build must resolve the complete authored relationship set before expanding any related-links directive. Reading existing relationship files while rendering documents would risk embedding the previous build's results or making incoming links depend on build order. Reuse the build's loaded inputs and completed relationship result for expansion.

Generated related-links sections must not contribute authored relationships or backlinks. Otherwise an incoming-link listing could manufacture a reciprocal relationship. Literal directive examples in code remain examples and do not render a section.

Publish performs the same relationship resolution and directive expansion over its captured eligible document set. Public sections therefore contain only documents in that prepared snapshot. Distribution copies the completed content without deriving relationships again.

## Next Refinement

The collection config and Index icons are implemented. Choose the related-links directive syntax and its complete delivery. [Builder](Builder.md) owns current relationship maintenance; [Links View](Links_View.md) describes the existing generic presentation. Runtime changes, treatment of the existing Links toolbar action, insertion-menu support and any separately specified test work remain for that implementation decision.
