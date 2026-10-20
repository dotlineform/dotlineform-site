---
draft: false
doc_id: d-20261020-152027-c9f3a8
title: Subject Retirement
added_date: "2026-10-20 15:20:27"
last_updated: "2026-10-20"
summary: Retire Folder placeholders, reserve draft for active authoring, and derive Projects associations from Catalogue references.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Subject Retirement

Status: complete; the user accepted closeout on 2026-10-20. Source cleanup, thumbnail reset and Projects snapshot cutover are complete. Manual Projects/Thumb interactions remain unverified in the recorded evidence and continue through normal use. [Reports](Reports.md), [Media And Asset Handling](Media_And_Asset_Handling.md#assigned-document-thumbnails) and [Generated Data Contracts](Generated_Data_Contracts.md) own shipped behavior. This document retains the authoring rationale and reference examples pending manual archive.

Ordinary Index documents retain SVG icons; Catalogue retains its separate media owner. Publish, commit and push were not performed by Codex as part of this delivery.

## Intended Result

The authoring aim is for `draft: true` to mean **this document is actively being authored**. Most Folder-subject documents instead represent **a document might be needed here**. The user is gradually deleting those placeholders and saving useful notes in the physical project folders. Those notes do not need a placeholder in the Docs collection.

Retiring Folder subjects is therefore expected to have little lasting impact on the retained collection. Preserving their current report coverage or converting every placeholder into Catalogue references is not a migration requirement. Cleanup remains the user's gradual editorial process; this delivery does not automate it or change `draft` publication behavior.

Projects shows documents related to the Series represented in physical project folders, using authored outbound Catalogue token references. Both Work relationships and Gallery mentions establish an association; the report does not classify the relationship type. A Work reference reaches its Series; a Gallery reference reaches explicitly associated Series. Those Series reach folders through their member Works' project-folder assignments. Show each document once per relevant row and retain unmatched physical folders.

Document `work_id`/`folder_path` declarations and generated scalar `subject` are retired. Canonical Catalogue Work identity and Work-to-Series membership retain their existing meaning.

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

## Projects Association Boundary

Projects Refresh uses the Context manifest for discovery, reads each selected by-ID payload once and collects distinct `catalogue.references[].target` identities: `catalogue-work` and `catalogue-gallery`. An omitted envelope supplies no references. Consumed facts live only in Projects' snapshot; shared manifests/indexes are not extended. Python gathers/persists facts, while the browser owns joins and presentation. Context-only coverage remains the accepted boundary.

Studio Refresh already produces the other inputs: `working/generated/catalogue/private/work-sources.json` supplies Work → Series/folder facts, and `working/generated/catalogue/series-galleries-index.json` supplies explicit Series → Gallery pairs. The latter currently includes Gallery `001` under Series `001`. Use those explicit pairs rather than infer Series from Gallery member Works. Reverse the pairs for Gallery → Series lookup. [Catalogue Report Inputs](Catalogue_Report_Inputs.md) and [Series and Galleries](Reports.md#current-reports) describe the owners.

This is a token-based association rule: plain Markdown links to Catalogue documents are not included in `catalogue.references` and would not contribute to Projects. Supporting those links would be a separate requirement. Refresh needs no Links JSON, source-token reparse or rendered-HTML scan. Incoming links, generated Related Links lists and chains through other documents do not create membership. Documents retained for actual authoring should use relevant Work/Gallery tokens; deleted Folder placeholders need no replacement association.

## Retirement Scope

- **Work Document Coverage — retired:** registry, loader, endpoint, private producer/artifact/maintenance and host are removed. Projects retains its physical-folder boundary and does not recreate an all-Series audit. The [historical report design](Works_Report_Concept_And_Architecture.md) remains a retirement reference.
- **Authored collection thumbnails — implemented:** Library, Context, Concepts and Moments share the independent Thumb action. Context has no Subject-derived Catalogue-thumbnail alternative. Catalogue and ordinary Index artwork keep their separate owners.
- **Authoring and metadata — retired:** Assign Subject, source Subject/thumbnail declarations, validation/customisation/context paths, scalar projections, image-token thumbnail controls and thumbnail-only Source Save uploads are removed.

### Manual Thumbnail Authoring

Thumbnail ownership is completely separate from tokens. Agreed workflow for all authored collections:

1. A document-level **Thumb** menu item opens one modal showing the current thumbnail and a Work search/selection, reusing the existing [Catalogue target picker](../../docs-viewer/runtime/js/management/source-editor/catalogue-target-picker.js).
2. **Apply** copies the selected Work's current Catalogue thumbnail into the document's existing `<doc_id>-thumb.webp` identity, creating or replacing its bytes. Document ownership and naming do not change.
3. **Delete thumbnail** removes the document's current thumbnail, without requiring a Work selection. The action is unavailable when no thumbnail exists.

The browser owns search, selection and modal state. Python owns the selected thumbnail copy/removal, affected generated metadata and normal exact publication effects. Apply/Delete complete as document actions; they do not wait for Source Save or edit Markdown. Choosing a Work here selects image bytes only: persist no source Work ID, relationship or dependency, and create no Projects or Related Links association. The modal shows the stored document thumbnail without needing to identify its original Work. Changing or deleting the source Work or its thumbnail has no effect on the independent document copy; that copy remains until its document's thumbnail is explicitly replaced/deleted or the document itself is deleted.

The authored `thumbnail:` field is retired. The saved `<doc_id>-thumb.webp` asset owns thumbnail presence; keep generated `has_thumbnail` metadata for readers. The action carries its completed effects, and explicit Build reads exact owned thumbnail presence when regenerating metadata/media references. Browsers and Publish consume the prepared handoff without file probes or freshness checks. This is a shared document-owned thumbnail model across authored collections; Catalogue thumbnails keep their existing independent lifecycle.

Create thumb is removed from [Add/Edit image](../../docs-viewer/runtime/js/management/source-editor/source-editor-media.js) along with its thumbnail-only [pending-upload](../../docs-viewer/runtime/js/management/source-editor/source-editor-pending-media.js) and [Source Save](../../docs-viewer/services/docs_source_media_service.py) plumbing. Add/Edit Catalogue image needs no thumbnail control. Image insertion, editing, replacement and deletion affect only their normal media; tokens neither own nor report the document thumbnail.

### Existing Thumbnail Reset

Cutover deleted all 40 existing document-owned thumbnails in the four authored collections, including manually created files: two Context and 38 Moments. Library/Concepts had none. It removed 39 `thumbnail:` declarations and reconciled generated metadata, with exact public removals queued for separate Publish. Catalogue thumbnails and body images were preserved.

Do not preserve or automatically recreate existing authored thumbnails from Subjects, tokens or previous choices. The user will manually create Moments and Context thumbnails with the new Thumb action after delivery; the same action is available consistently in Library and Concepts.

Implementation and data cutover are complete; manual Projects and Thumb interaction remain unverified. No tests or browser automation were created, changed or run.
