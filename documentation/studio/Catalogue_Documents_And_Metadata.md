---
draft: false
doc_id: d-20261002-214356-1ea4a2
title: Catalogue Documents And Metadata
added_date: "2026-10-02 21:43:56"
last_updated: "2026-10-02 21:43:56"
summary: Define a distinct Catalogue Entry token and review Work metadata so Catalogue documents provide complete public records with proper document semantics.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Documents And Metadata

Status: proposed feature, parented to [Planned Features](Planned_Features.md). This document records the intended outcome, the current gaps and decisions needed before implementation. It does not approve token implementation, field removal, data migration or publication.

## Intended Outcome

A Catalogue document is the definitive document for a Work. Its title defines the document, its image illustrates the Work, and its metadata describes the Work. It should remain meaningful when read on the public site or exported outside Docs Viewer.

Retained descriptive Work metadata should be available in the public Catalogue document. A field appearing only in a Manage report is a gap to resolve, rather than a reason to keep it private. For a field that cannot reasonably be public, first ask whether it belongs in this system at all. Remove unnecessary fields; make useful retained fields public. No particular field removal has been agreed yet.

The authoring and rendering model should express this purpose explicitly through a separate **Catalogue Entry** token. **Catalogue Image** remains an image inserted into body content, with an optional figure caption. The builder executes each token's declared meaning without changing an image token's semantics according to the collection hosting the document.

## Current Findings

Catalogue regeneration currently produces a Work image token followed by `[[links|related links]]`. The Work title is repeated in document front matter and the figure caption, but the caption renders as a styled span inside `figcaption`, rather than a document heading. The figure's selected metadata is limited to displayed year, medium description, physical dimensions and Catalogue number.

The local [Catalogue Works report](/docs/?doc=d-20260810-222148-99daec) has Work, Year, Title, Series and Storage columns, plus Medium type and Medium caption in its expanded presentation. Its generated metadata is local-only. [Catalogue Works](Catalogue_Works.md) describes this current contract; its instructions to keep storage context private are current implementation guidance that this proposal would replace if a different field policy is approved.

The public consumer Work JSON contains more information than the Catalogue document renders. Artist, duration, medium type, pixel dimensions, links and downloads are already projected when populated. Conversely, storage location and provenance are omitted from that projection. Series identity is projected, but a Series title is not included in the complete Work record. These are different problems: missing presentation, missing projection, and separately resolved relationship labels.

“Public consumer projection” below means the generated Work JSON intended for public readers. It does not establish that the latest generated values have been published or deployed. Empty optional values are omitted from that JSON.

## Work Metadata Inventory

This inventory was checked against the canonical Work fields, active editor definitions, generated Work projection, private report projection and image-token renderer on 2026-10-02. “Catalogue body” refers to the generated figure and Related links content, rather than all metadata used elsewhere in Docs Viewer.

| Field or relationship | Public consumer projection today | Catalogue body today | Proposed treatment or decision |
| --- | --- | --- | --- |
| `work_id` | Exact five-digit identity | Catalogue number | Retain as the document identity and visible Catalogue number; preserve leading zeroes. |
| `title` | Work title | Figure caption; also document metadata title | Retain as the document's H1, with its visual style controlled separately. |
| `year`, `year_display` | Numeric year and display text | Display text only | Retain the distinction if numeric sorting and a richer displayed date are both needed; show the readable date without duplicating it as another visible number. |
| `medium_type` | Present when populated | Omitted; available in expanded Manage report | Decide whether the category has a distinct browsing/classification purpose. If retained, expose it as Work metadata; if redundant, remove it through its consumers. |
| `medium_caption` | Present when populated | Medium description | Retain useful medium description. Label it **Medium** or **Medium description** in an Entry, rather than treating it as the document's caption. Decide separately whether the source field name needs changing. |
| `height_cm`, `width_cm`, `depth_cm` | Present when populated | Height × width, with depth when supplied; requires height and width | Retain supported physical measurements with clear units and dimension order. Decide how partial measurements should display and whether depth is needed. |
| `duration` | Present when populated | Omitted | Decide whether time-based Works are in scope. If retained, display duration and define its units/format; otherwise remove the unused field. |
| `artist` | Present when populated | Omitted | Decide whether authorship varies per Work or belongs to shared Catalogue context. Retain and display it where it carries information; remove a redundant per-Work field if authorship is defined elsewhere. |
| `provenance` | Omitted | Omitted; not in Catalogue Works report | Review the existing value and intended meaning. Retain as public provenance if useful and suitable; remove it if it has no role in a public Work record. |
| `storage_location` | Omitted | Omitted; available as Storage in Manage report | Decide whether physical storage belongs in the public Catalogue. If it is confidential inventory administration, the preferred outcome is removal from this system rather than a private Catalogue-only field. |
| `series_id` and Series title | ID present; title not in complete Work record | Not rendered by the figure; grouping/Subject uses separate ownership | Retain the meaningful Series relationship and make its readable title available to the document builder/public record without depending on the private report. Keep grouping identity separate from an ordinary document link. |
| Direct Gallery memberships | Gallery identities and titles in `galleries` | Not rendered by the figure; accessible in Media View | Decide where the Entry displays these relationships so the document does not require Media View to reveal them. Reuse existing memberships and Gallery targets. |
| Series-related Galleries | Separate generated Series–Gallery index | Accessible through Media View, rather than figure metadata | Preserve the distinction between direct membership and relevance through a Series; decide whether to include this derived context in the Entry. |
| `links` | URL/label entries when populated | Omitted by the figure | Display retained authored external resources as links. Keep them distinct from Docs Viewer document relationships. |
| `downloads` | Filename/label entries with generated public URLs | Omitted by the figure | Make retained download resources available from the document. Export packaging is a separate consumer requirement. |
| `width_px`, `height_px` | Present when populated | Omitted | Decide whether these are reader-facing image properties or technical rendition inputs. Their role must be explicit; do not confuse image pixels with physical Work dimensions. |
| `media_source_id`, `project_folder`, `project_subfolder`, `project_filename` | Omitted | Omitted | These resolve the source image for the production pipeline. Review under the technical-data boundary below; they are not a reason to keep descriptive Work metadata private. |
| `media_version` | Present when populated | Omitted | Retain the technical image revision needed by media readers; it is not a descriptive Catalogue line. |
| Docs Viewer document relationships | Maintained by the separate Links owner; Work JSON currently initializes `documents` empty | Rendered by the Related links directive | Preserve the existing Links authority. Do not create a second manually maintained relationship list inside the Entry token or reinterpret external `links` as document relationships. |

### Population Snapshot

The read-only canonical snapshot contains 4,616 Works. Storage location is populated for 481 Works; provenance for one. Artist, duration and depth are empty for every Work. Both medium fields and both year fields are populated for every Work. Physical height and width are each populated for 1,935 Works. Four Works have downloads and three have external links.

These counts describe populated values, not usefulness, validity or permission to publish. Empty fields are candidates for removal only after deciding their intended capability. Populated fields require a value review before removal or wider publication; no storage or provenance values are reproduced in this planning document. In particular, `medium_type` and `medium_caption` can serve different purposes even though both are populated.

### Technical Data Boundary To Agree

The proposed public-data rule applies to descriptive metadata and reader resources. Image production also needs source selection, filenames, measurements and image revisions. Those values support making the public Work record; they do not all need to become visible lines in that record.

Confirm this distinction explicitly. A retained technical field must have a concrete pipeline consumer and belong to that production/configuration owner. It must not become a catch-all exemption for private Work descriptions, storage notes or provenance. Remove unused technical fields as well. Public image URLs and useful image properties can remain public without exposing local source locations. Do not attempt to publish the raw canonical record merely to make the descriptive record complete.

## Catalogue Entry Semantics And Authoring

The Entry has one fixed semantic purpose: render the principal record of one Work. A possible spelling is `[[catalogue:entry:work:03565]]`; the exact syntax and any presentation options remain to be agreed. The token stores Work identity and necessary presentation choices, while the generated Work record remains the authority for title and metadata. It does not store a second editable copy of those values.

| Capability | Catalogue Image | Catalogue Entry |
| --- | --- | --- |
| Purpose | Illustrate body content | Present a Work as a document |
| Title role | Optional figure caption | Required principal document heading |
| Metadata role | Optional selected caption information | Complete retained descriptive Work metadata and resources |
| Authoring labels | Image, caption, placement | Entry, Work title, metadata, layout |
| Heading behavior | Does not define the document title | Emits the Work H1 explicitly |

The Entry title should be an `h1` even when the chosen appearance is 16px bold. Give it a dedicated Entry style that can reuse the body-size token; do not change its heading level to achieve a visual size, or rely on a collection-specific reinterpretation of the Image token. Subsequent Entry sections should use the appropriate heading hierarchy, such as H2 for Related links, while their visual size can remain independently controlled. [W3C heading guidance](https://www.w3.org/WAI/tutorials/page-structure/headings/) explains the structural role.

The image remains a figure/media control with appropriate alt text. Descriptive name/value metadata can use a definition list, and resources/relationships can use meaningful link lists. The Work heading belongs to the Entry/document structure, not inside a figure caption. The preferred layout may still place image and text beside each other.

**Add/Edit Catalogue Entry** must explain these roles honestly. It should not offer **Use Work title for caption**, describe the Work title as a caption, or let a generated Entry omit retained descriptive metadata through the Image token's existing checkbox. Any retained layout controls affect presentation only. Confirm the authoring rule for one principal Entry per document; authors illustrating another document should continue to use Catalogue Image. The generic builder must not infer different semantics from the host collection.

Reuse existing Work lookup, exact identity validation, image resolution, Media View activation and token relationship extraction. The new token must participate in existing relationship handling, including suppression of a Work document's self-reference. A separate semantic token does not require another media pipeline, Work store or relationship graph. Existing Image tokens in ordinary documents remain valid because they retain their own purpose.

## Data And Build Ownership

Use one descriptive Work model for public records, Catalogue documents and any management table. A Manage report may remain a useful local editing/reporting interface, but it should no longer be the only reader of retained Work information. Manage presentation and private descriptive data are separate decisions; making a field public does not require publishing the Manage report itself.

| Owner | Required change |
| --- | --- |
| Studio canonical source and Work editor | Remove only agreed fields, retain validated useful metadata and define field meanings/units. Keep editing authoritative here. |
| Refresh Catalogue | Project every retained descriptive field and necessary relationship label into public-capable generated data. Reconcile affected report projections and schemas rather than maintaining another private version of the Work description. |
| Catalogue Regenerate and document Build | Emit Entry tokens and resolve their complete content from captured generated data. Avoid a runtime fetch of private report metadata. |
| Docs Viewer runtime | Present generated document content and reuse existing media/resource readers. Public readers require no Studio API. |
| Publish and distribution | Carry the approved public projection and rendered documents through the existing completed Preview and publication inventory. Do not publish raw source or the private report aggregate by accident. |
| Static/export consumers | Preserve title, metadata, relationships and usable media independently of the interactive viewer. Review their own transformations and resource preparation. |

[Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) remains the lifecycle authority: Save changes canonical data; Refresh generates reader data; Regenerate updates Catalogue sources and builds documents; Publish distributes the completed snapshot. This feature should fit those boundaries rather than introducing implicit Refresh, Regenerate or Search work into Publish.

Retain exact Work/document identities, routes and existing date policy. Generated body or formatting maintenance preserves document dates; a Work-derived title change advances `last_updated`. Full reconciliation currently owns replacement of generated Catalogue bodies, so determine whether any manually added body content needs preservation before the token conversion.

## Export Implications

A proper H1 makes the Work title available to heading-aware consumers, but does not automatically create an EPUB table of contents. An EPUB exporter must deliberately construct navigation, choose the document/chapter structure and, when compiling several Works, handle any required heading-level transformation. See the [EPUB navigation specification](https://www.w3.org/TR/epub-33/#sec-nav-toc).

Current document-package heading extraction recognizes HTML heading elements and removes a first heading matching the document metadata title from its returned section-heading list. Review that behavior as part of the consumer contract; changing a caption to H1 should not accidentally duplicate or discard the Work title in export navigation. [Export](Export.md) owns the current static HTML workflow. A new EPUB exporter is not part of this proposal's implementation by default.

The existing Work image markup is populated by the interactive media reader. A semantically complete Entry must also have an explicit static-image/resource preparation policy for portable output; changing only the title tag does not make an exported image usable. Define whether export includes downloadable resources or retains links, and whether compiled output includes all relationship context. Those choices need their own bounded implementation scope.

## Decisions Needed

- [ ] Agree the descriptive-versus-technical data boundary and the rule that retained descriptive metadata is public.
- [ ] Review `storage_location` and the one populated provenance value; decide retain publicly, remove, or move administration out of this system.
- [ ] Decide whether artist, duration and depth have a real supported purpose despite currently being empty.
- [ ] Decide whether medium type and medium description remain separate fields, and whether any labels or source names need changing.
- [ ] Agree readable dates, duration units and partial-dimension display without collapsing useful numeric/display distinctions.
- [ ] Agree the Entry's metadata order, section hierarchy, resource presentation and treatment of direct versus Series-related Galleries.
- [ ] Confirm token syntax, honest modal labels, principal-Entry authoring rule and the independent title style.
- [ ] Agree portable image/resource requirements and whether EPUB is a later consumer delivery.

## Proposed Implementation Sequence

1. **Field decisions and data model:** review actual values only where needed; agree removals, public additions and meanings. Update canonical/editor/projection/report owners together for each approved change, with an explicit disposition for any removed populated data.
2. **Entry token and rendered document:** implement the explicit token, shared resolution, modal and semantic markup. Reconcile generated Catalogue sources with one intentional full Regenerate/Build after the global rendering/body contract changes. Preserve ordinary Image tokens without aliases or context forks.
3. **Public and static consumers:** review the public projection and rendered metadata, then deliver any agreed export preparation. Publication, Git actions and deployment remain separate explicit operations.

The result is complete when every retained descriptive field has a defined public representation, each Catalogue document has the correct Work heading and metadata, authoring describes the token's real purpose, and retained consumers read the agreed model. Field removal must leave no active editor, projection or report references; generated data must be reconciled after schema changes. Manual review owns visual fit. Any executable verification or test work will be selected and specified proportionately when implementation is approved, following [Test Contract Discipline](Test_Contract_Discipline.md).

## Inspection Basis

The current field and ownership findings come from [canonical Work fields](../../studio/services/catalogue/catalogue_source.py), [Work editor definitions](../../studio/app/frontend/js/catalogue-work-fields.js), [public scalar projection](../../studio/services/catalogue/catalogue_generation_records.py), [complete Work assembly](../../studio/services/catalogue/generate_work_pages.py), [private report projection](../../studio/services/catalogue/catalogue_works_metadata.py), [Catalogue body generation](../../docs-viewer/services/docs_catalogue_work_record.py), [token rendering](../../docs-viewer/build/docs_builder/semantic_tokens.py), [regeneration](../../docs-viewer/services/docs_catalogue_regeneration.py) and [rendered heading extraction](../../docs-viewer/services/docs_document_packages/rendered_content.py). Population counts came from a read-only inspection of canonical `works.json`; no source or generated Catalogue data was changed.
