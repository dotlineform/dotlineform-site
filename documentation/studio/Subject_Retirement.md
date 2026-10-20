---
draft: false
doc_id: d-20261020-152027-c9f3a8
title: Subject Retirement
added_date: "2026-10-20 15:20:27"
last_updated: "2026-10-20"
summary: Retire Folder placeholders, reserve draft for active authoring, and derive Projects associations from Catalogue references.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Subject Retirement

Status: delivery proposal with the token-only Projects boundary, Work Document Coverage retirement and separate Thumb workflow agreed. The Thumb workflow applies consistently to every authored collection, with all existing document-owned thumbnails removed at cutover. Retirement implementation has not started. The [Projects Metadata Snapshot](deliveries/Projects_Metadata_Snapshot.md) first delivery is implemented and retains Subject-based associations. [Subject Associations](data_model/subject-associations.md) records the current contract.

The [Subject Retirement Delivery](deliveries/Subject_Retirement_Delivery.md) contains the ordered implementation steps, verification budgets, cutover/reset and completion gates. This overview retains the rationale, examples and agreed behavior.

## Intended Result

The authoring aim is for `draft: true` to mean **this document is actively being authored**. Most Folder-subject documents instead represent **a document might be needed here**. The user is gradually deleting those placeholders and saving useful notes in the physical project folders. Those notes do not need a placeholder in the Docs collection.

Retiring Folder subjects is therefore expected to have little lasting impact on the retained collection. Preserving their current report coverage or converting every placeholder into Catalogue references is not a migration requirement. Cleanup remains the user's gradual editorial process; this proposal does not automate it or change `draft` publication behavior.

Projects should show documents related to the Series represented in physical project folders, using authored outbound Catalogue token references. Both Work relationships and Gallery mentions establish an association; the report does not classify the relationship type. A Work reference reaches its Series; a Gallery reference reaches explicitly associated Series. Those Series reach folders through their member Works' project-folder assignments. Show each document once per relevant row and retain unmatched physical folders.

Subject currently means source `work_id` or `folder_path`, projected as scalar `subject` in management metadata. Replacing Projects' placement is one part of retiring that mechanism; the remaining consumers below must also be resolved.

## Existing Reference Inputs For Projects

Projects can obtain both Work and Gallery token targets from the existing document JSON's `catalogue.references`. It does not need to read Links JSON. The comparison below explains the existing formats; changing Related Links is not part of Subject retirement.

| Product | Work token | Gallery token | Owning code |
| --- | --- | --- | --- |
| Per-document Links record, used by Related Links | Adds an outgoing link to the Work's Catalogue document; self-references are omitted. | Adds no document relationship. | [`links_builder.py`, `_DocumentRefresh.references()`](../../docs-viewer/build/docs_builder/links_builder.py) accepts only `token.target_type == "work"`; [`links_model.py`](../../docs-viewer/build/docs_builder/links_model.py) represents endpoints as collection/document IDs. |
| Document by-ID payload, `catalogue.references` | Retains a typed `catalogue-work` target. | Retains a typed `catalogue-gallery` target. | [`semantic_tokens.py`, `catalogue_reference()` and `resolve_semantic_tokens()`](../../docs-viewer/build/docs_builder/semantic_tokens.py) collect both kinds; [`payloads.py`, `item_entry()`](../../docs-viewer/build/docs_builder/payloads.py) attaches them to the document. |

This is an intentional boundary, not missing relationship data to repair: a Work has a Catalogue subdocument; a Gallery opens Media View and has no corresponding Gallery document endpoint. Related Links navigates to documents, while `catalogue.references` records authored presentation occurrences. Those occurrences preserve target identity and options, not Series membership. Gallery targets should continue to open Media View without becoming Related Links entries. See [Related Links](Related_Links.md#generated-data-and-freshness) and [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation).

For an **illustrative** document containing these two tokens:

```text
[[catalogue:media:work:00635|10,000 (1)]]
[[catalogue:media:gallery:001|10,000]]
```

Its by-ID payload retains both targets:

```json
{
  "catalogue": {
    "schema": "docs_catalogue_presentation_v1",
    "references": [
      {"reference_id": "c1", "target": {"kind": "catalogue-work", "id": "00635"}, "presentation": "media", "options": {"label": "10,000 (1)"}},
      {"reference_id": "c2", "target": {"kind": "catalogue-gallery", "id": "001"}, "presentation": "media", "options": {"label": "10,000"}}
    ]
  }
}
```

The corresponding Links record has this outgoing entry, with no Gallery entry:

```json
{
  "outgoing": [
    {"collection": "catalogue", "doc_id": "00635", "title": "10,000 (1)"}
  ]
}
```

These are excerpts, omitting unrelated fields. The `[[links|]]` directive only displays the computed relationships; its presence does not determine whether references are recorded. A Gallery-only document can therefore have `catalogue.references` without any Links record of its own.

For a **real saved Work example**, [10,000](/docs/?collection=works&doc=d-20260801-212422-43b47c) uses Work image tokens for `00635` and `03181`. Both IDs occur in its `catalogue.references` and outgoing Links. Inspect these files relative to `$DOTLINEFORM_DOCS_BASE_DIR`; the Gallery token above is illustrative, not an addition to this document:

- Source: `working/source/collections/works/documents/d-20260801-212422-43b47c.md`.
- Payload: `working/generated/collections/works/documents/by-id/d-20260801-212422-43b47c.json`.
- Links: `working/generated/documents/links-by-id/d-20260801-212422-43b47c.json`.

## Proposed Next Delivery

Projects Refresh should use the existing Context manifest for document discovery, read each selected by-ID payload once and collect distinct `catalogue.references[].target` identities: `catalogue-work` and `catalogue-gallery`. An omitted `catalogue` envelope supplies no references. Keep only the consumed identity facts in Projects' own snapshot, without extending shared manifests/indexes. Python owns gathering and persistence; the browser retains the relationship joins and report presentation. Continue with Context documents unless broader collection coverage is agreed.

Studio Refresh already produces the other inputs: `working/generated/catalogue/private/work-sources.json` supplies Work → Series/folder facts, and `working/generated/catalogue/series-galleries-index.json` supplies explicit Series → Gallery pairs. The latter currently includes Gallery `001` under Series `001`. Use those explicit pairs rather than infer Series from Gallery member Works. Reverse the pairs for Gallery → Series lookup. [Catalogue Report Inputs](Catalogue_Report_Inputs.md) and [Series and Galleries](Reports.md#current-reports) describe the owners.

This is a token-based association rule: plain Markdown links to Catalogue documents are not included in `catalogue.references` and would not contribute to Projects. Supporting those links would be a separate requirement. Refresh needs no Links JSON, source-token reparse or rendered-HTML scan. Incoming links, generated Related Links lists and chains through other documents do not create membership. Documents retained for actual authoring should use relevant Work/Gallery tokens; deleted Folder placeholders need no replacement association.

## Retirement Scope

- **Work Document Coverage — retirement agreed:** remove the report and its private generated input/producer and maintenance wiring as part of this delivery. It measures Series-level coverage, not individual Work gaps. Projects retains its physical-folder boundary; the former report's all-Series audit, including empty Series and those without a matching folder, will not be recreated. See [coverage rules](Works_Report_Concept_And_Architecture.md#coverage-rule) and [`works-report-data.js`](../../docs-viewer/runtime/js/reports/works-report-data.js).
- **Authored collection thumbnails — shared manual approach agreed:** apply the same document-level Thumb action to Library, Context (`works`), Concepts and Moments. Exclude Catalogue, whose documents and thumbnails are Catalogue-owned rather than authored through this workflow. Remove Context's Subject-based Catalogue-thumbnail fallback in [`docs-collection-browsing.js`, `prepareRecord()`](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js). It currently reuses Catalogue Work thumbnails and creates no separate Context thumbnail files.
- **Authoring and generated metadata:** after those consumers are replaced, retire Assign Subject, its source fields, validation and management/public Subject projections through their [documented owners](data_model/subject-associations.md#active-consumer-owners). Source migration and removal require an agreed delivery.

### Manual Thumbnail Authoring

Thumbnail ownership is completely separate from tokens. Agreed workflow for all authored collections:

1. A document-level **Thumb** menu item opens one modal showing the current thumbnail and a Work search/selection, reusing the existing [Catalogue target picker](../../docs-viewer/runtime/js/management/source-editor/catalogue-target-picker.js).
2. **Apply** copies the selected Work's current Catalogue thumbnail into the document's existing `<doc_id>-thumb.webp` identity, creating or replacing its bytes. Document ownership and naming do not change.
3. **Delete thumbnail** removes the document's current thumbnail, without requiring a Work selection. The action is unavailable when no thumbnail exists.

The browser owns search, selection and modal state. Python owns the selected thumbnail copy/removal, affected generated metadata and normal exact publication effects. Apply/Delete complete as document actions; they do not wait for Source Save or edit Markdown. Choosing a Work here selects image bytes only: persist no source Work ID, relationship or dependency, and create no Projects or Related Links association. The modal shows the stored document thumbnail without needing to identify its original Work. Changing or deleting the source Work or its thumbnail has no effect on the independent document copy; that copy remains until its document's thumbnail is explicitly replaced/deleted or the document itself is deleted.

Retire the authored `thumbnail:` field. The saved `<doc_id>-thumb.webp` asset owns thumbnail presence; keep generated `has_thumbnail` metadata for readers. The action carries its completed effects, and explicit Build reads exact owned thumbnail presence when regenerating metadata/media references. Browsers and Publish consume the prepared handoff without file probes or freshness checks. This is a shared document-owned thumbnail model across authored collections; Catalogue thumbnails keep their existing independent lifecycle.

Remove Create thumb from [Add/Edit image](../../docs-viewer/runtime/js/management/source-editor/source-editor-media.js) and retire its thumbnail-only [pending-upload](../../docs-viewer/runtime/js/management/source-editor/source-editor-pending-media.js) and [Source Save](../../docs-viewer/services/docs_source_media_service.py) plumbing. Add/Edit Catalogue image needs no thumbnail control. Image insertion, editing, replacement and deletion affect only their normal media; tokens neither own nor report the document thumbnail.

### Existing Thumbnail Reset

Delete all existing document-owned thumbnails in the four authored collections as part of the delivery, including previously manually created thumbnails. Remove obsolete `thumbnail:` declarations and reconcile affected generated thumbnail metadata/media references. Use configured media owners and the ordinary publication handoff to queue exact Preview/public thumbnail removals; Publish remains a separate action. Catalogue Work thumbnails and body images are outside this reset.

Do not preserve or automatically recreate existing authored thumbnails from Subjects, tokens or previous choices. The user will manually create Moments and Context thumbnails with the new Thumb action after delivery; the same action is available consistently in Library and Concepts.

This proposal changes no runtime behavior or existing Subjects.
