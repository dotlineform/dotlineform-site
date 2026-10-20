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

Status: proposal; retirement implementation is not yet approved. The [Projects Metadata Snapshot](deliveries/Projects_Metadata_Snapshot.md) first delivery is implemented and retains Subject-based associations. [Subject Associations](data_model/subject-associations.md) records the current contract.

## Intended Result

The authoring aim is for `draft: true` to mean **this document is actively being authored**. Most Folder-subject documents instead represent **a document might be needed here**. The user is gradually deleting those placeholders and saving useful notes in the physical project folders. Those notes do not need a placeholder in the Docs collection.

Retiring Folder subjects is therefore expected to have little lasting impact on the retained collection. Preserving their current report coverage or converting every placeholder into Catalogue references is not a migration requirement. Cleanup remains the user's gradual editorial process; this proposal does not automate it or change `draft` publication behavior.

Projects should show documents related to the Series represented in physical project folders, using authored outbound Catalogue references. A Work reference reaches its Series; a Gallery reference reaches explicitly associated Series. Those Series reach folders through their member Works' project-folder assignments. Show each document once per relevant row and retain unmatched physical folders.

Subject currently means source `work_id` or `folder_path`, projected as scalar `subject` in management metadata. Replacing Projects' placement is one part of retiring that mechanism; the remaining consumers below must also be resolved.

## The Work/Gallery Gap

Two generated products preserve different information:

| Product | Work token | Gallery token | Owning code |
| --- | --- | --- | --- |
| Per-document Links record, used by Related Links | Adds an outgoing link to the Work's Catalogue document; self-references are omitted. | Adds no document relationship. | [`links_builder.py`, `_DocumentRefresh.references()`](../../docs-viewer/build/docs_builder/links_builder.py) accepts only `token.target_type == "work"`; [`links_model.py`](../../docs-viewer/build/docs_builder/links_model.py) represents endpoints as collection/document IDs. |
| Document by-ID payload, `catalogue.references` | Retains a typed `catalogue-work` target. | Retains a typed `catalogue-gallery` target. | [`semantic_tokens.py`, `catalogue_reference()` and `resolve_semantic_tokens()`](../../docs-viewer/build/docs_builder/semantic_tokens.py) collect both kinds; [`payloads.py`, `item_entry()`](../../docs-viewer/build/docs_builder/payloads.py) attaches them to the document. |

This is intentional: a Work has a Catalogue subdocument; a Gallery opens Media View and has no corresponding Gallery document endpoint. Related Links is a document graph, while `catalogue.references` records authored presentation occurrences. The latter preserves target identity and options, not the target's Series membership. See [Related Links](Related_Links.md#generated-data-and-freshness) and [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation).

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

Projects Refresh should gather outbound Catalogue-document links from Links records and Work/Gallery token targets from by-ID payloads, deduplicating targets. Keep those facts in Projects' own snapshot, without extending shared manifests/indexes. Python owns gathering and persistence; the browser retains the relationship joins and report presentation. Continue with Context documents unless broader collection coverage is agreed.

Studio Refresh already produces the other inputs: `working/generated/catalogue/private/work-sources.json` supplies Work → Series/folder facts, and `working/generated/catalogue/series-galleries-index.json` supplies explicit Series → Gallery pairs. The latter currently includes Gallery `001` under Series `001`. Use those explicit pairs rather than infer Series from Gallery member Works. Reverse the pairs for Gallery → Series lookup. [Catalogue Report Inputs](Catalogue_Report_Inputs.md) and [Series and Galleries](Reports.md#current-reports) describe the owners.

Use authored outbound references, including ordinary links to Catalogue documents. Incoming links, generated Related Links lists and chains through other documents should not create Projects membership. Documents retained for actual authoring should use relevant Work/Gallery references; deleted Folder placeholders need no replacement association.

## Remaining Retirement Decisions

- **Work Document Coverage:** [`works-report-data.js`, `placeDocument()`](../../docs-viewer/runtime/js/reports/works-report-data.js) currently places documents using Work Subjects. Decide its replacement association rule.
- **Context thumbnails:** [`docs-collection-browsing.js`, `prepareRecord()`](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) uses a Work Subject when no authored thumbnail exists. Decide the independent thumbnail selection rule.
- **Authoring and generated metadata:** after those consumers are replaced, retire Assign Subject, its source fields, validation and management/public Subject projections through their [documented owners](data_model/subject-associations.md#active-consumer-owners). Source migration and removal require an agreed delivery.

This proposal changes no runtime behavior or existing Subjects.
