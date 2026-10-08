---
draft: false
doc_id: d-20260930-195002-b3417e
title: Related Links
added_date: "2026-09-30 19:50:02"
last_updated: "2026-10-08 20:05:36"
summary: Author-inserted related-links directive, a sorted list with collection icons, and build-time relationship snapshots in document JSON.
ui_status: in-progress
parent_id: d-20260428-000000-f5ff18
---
# Related Links

Status: implemented, with manual acceptance pending in [Related Links Delivery](Related_Links_Delivery.md). Collection config and Index icons are recorded in [Collection Icons Delivery](Collection_Icons_Delivery.md). This feature is parented to [Planned Features](Planned_Features.md).

## Authoring Decision

An author manually inserts a related-links directive in the Source Editor where the list should appear. The directive requests the document's computed related links; the author does not maintain the individual entries. The source form is:

```text
[[links|]]
```

`links` identifies the directive; the text after `|` supplies its optional, editable plain-text heading. `[[links|]]` renders the list without a heading; whitespace-only text also omits the heading. Put the directive on its own line. **Directives → Insert related links** inserts the heading-free default form above and places the caret between `|` and `]]` for an optional heading. For example, `[[links|Further reading]]` uses “Further reading” as its heading. A supplied heading renders as H2 in Catalogue documents and H3 elsewhere; Markdown punctuation and HTML-looking heading text remain plain text. Fenced and indented code examples remain literal.

Without the directive, the document has no related-links section. If the directive resolves to no qualifying links, it produces no visible heading, list, pin or empty-state message. Local/public readers add **Pin related links** beside a non-empty section's optional H2/H3 heading; heading-free directives retain the pin. [Info Panel](Info_Panel.md) owns capture, navigation, replacement and Close. Exports and Docs Review keep the static list without a pin.

## Initial Presentation

Use the document's normal content width and section heading, with a collection icon beside each link and no bullet markers or list indentation. Combine incoming and outgoing document relationships into one plain list, sorted A–Z by case-folded displayed title, with exact collection/document identity providing a stable tie-break. Repeated and reciprocal links to the same target appear once; distinct documents with the same title remain distinct. Omit the document itself.

All participating collections use the same list. The presentation has no collection groups, direction labels, counts, cards or enclosing panel. Relationships come from supported authored document links; sharing a Subject or a Catalogue association does not add entries by itself. The original mock-up below remains a plain sorted list; the selected icon refinement is recorded separately.

## Rendered Mock-up

The following is an illustrative document excerpt. The titles link to existing Studio documentation so the mock-up can be viewed as ordinary rendered Markdown. The list represents the directive's generated output, rather than a list maintained in the example document's source.

---

### Document linking

Document links connect this explanation with supporting material. Related documents are listed below for further reading.

<section data-docs-related-links="true">

### Related links

- [Builder](Builder.md)
- [Context Navigation](Document_Context_Navigation.md)
- [Related Links](Related_Links.md)
- [Source Editor Scripts](Source_Editor_Scripts.md)

</section>

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

An extensionless `icon` value belongs to each collection record in the existing workspace configuration, such as `"icon": "dlf-context"` for Works. [Source Organisation](Source_Organisation.md#collection-icons) owns this contract. The related-links builder reads this same mapping and uses the [Icon Tokens](Icon_Tokens.md) renderer to embed decorative artwork. Ordinary targets use `dlf-doc`.

The Index panel now marks collection report hosts with their configured collection icon, supplied through the existing browser configuration projection. Related links will share that artwork for documents within the collection. Collection icons identify collection ownership; Subject artwork remains separate. The [collection icon delivery](Collection_Icons_Delivery.md) records static verification, code review and the pending manual visual check.

## Generated Data And Freshness

The builder expands the directive into a static section in the document's generated JSON. The reader displays that prepared content without fetching a separate relationship record, collection manifest or neighbouring document to populate the list. Links retain exact document identities and follow the existing portable local/public document-routing rules.

Saving a referring document can update relationship records while leaving the referred document's embedded section unchanged. Ordinary saves retain their targeted build scope; they do not rebuild neighbouring document content merely to refresh this presentation. A full Docs Build refreshes the related-links sections across the complete configured document set that can contribute relationships, including participating collections. Link additions, removals and title changes become visible in the refreshed sections.

Each Working document build first runs the existing incremental Links maintenance for its selected documents. That refresh preserves the saved incoming summaries and updates outgoing summaries from current authored links. The related section then uses the same refreshed version-4 record written to `links-by-id`, so adding or removing an outgoing link is reflected in that document's current build. A dry run uses the same refreshed records in memory without writing them. Section expansion does not discover relationships or add a source graph; the existing per-collection build orchestration remains in place.

Supported Catalogue Work image, Entry and Media View tokens contribute ordinary document relationships to their Work's Catalogue subdocument. Gallery Media View tokens contribute none. Catalogue sources use the Work's Entry, a blank line and `[[links|context]]`; the self-targeting Entry is omitted from the graph. `context` supplies only the Catalogue heading for the existing directive and does not change relationship ownership or the ordinary authoring default. A Catalogue page can therefore show the documents that reference its Work through incoming links without generating outgoing relationships from the displayed list. Downloads and external `work.links` stay in Entry's combined resource list and do not supply document relationships. A directive alone creates no Links record, and an empty list produces no section. Full Docs rebuilds render Catalogue after the contributing documents and use the final document-JSON comparison to detect changes in the embedded list; no separate Links-file change detector is needed.

Targeted saves rebuild only their selected document content, after refreshing its relationship record and affected neighbours. A document build includes all incoming links already recorded when it runs. Later edits to other documents can change that incoming list without rebuilding this document's content; a subsequent document build or full Docs Build refreshes its embedded section. Working relationships do not filter sources or targets by draft state, ordinary `unpublishable.json` membership or inherited publication exclusion. Removing an old filter requires an explicit complete relationship reconciliation to restore suppressed references; panel opening adds no scan or rebuild.

Use **Edit doc → Rebuild** in the local rendered reader to refresh the displayed document's embedded Related links from current relationship records without a source edit. The action preserves source dates, rebuilds only that document, omits Search and reloads the exact ordinary or collection target after completion. It does not rebuild neighbouring document content; [Runtime](Docs_Viewer_Runtime.md#document-action-context-and-toolbar-placement) owns the action and service contract.

Generated related-links sections must not contribute authored relationships. Otherwise an incoming-link listing could manufacture a reciprocal relationship. Literal directive examples in code remain examples and do not render a section.

Related Links supersedes Documents Linking Here and its separate backlinks concept. The `docs_backlinks` report, reverse-link builder and payload, browser setting and local API are retired. Incoming and outgoing presentation continues to use the existing persisted per-document Links records and build-time section snapshot; no replacement reverse-link index is maintained.

Publish captures the persisted relationship JSON alongside its existing inputs. Body eligibility selects the records whose owners are prepared, while their incoming/outgoing target rows remain intact. The temporary Preview build expands those captured records without target-readiness reads, filtering or warnings; distribution copies the completed content without deriving relationships again. A public section may retain a title/link for a destination whose body was omitted by draft or ignore policy. Following it uses the normal unavailable-document response. The author owns the decision to finish/include the destination or change the reference.

## Runtime And Refinement

The per-document Links toolbar action, separate Content Detail presentation and `/docs/links` read endpoint are retired without aliases. The reader mounts the generated section as ordinary document content. Its pin opens the [Info Panel](Info_Panel.md) with the loaded title, optional summary and a copy of that same list; the panel fetches no relationship data. The local workspace Links diagnostic report retains its aggregate data and exact-target helpers. [Builder](Builder.md) owns relationship maintenance and persisted-record expansion. Interaction and layout acceptance remain manual; test work requires its own agreed specification under [Testing](Testing.md).
