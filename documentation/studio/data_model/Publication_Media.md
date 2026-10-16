---
draft: false
doc_id: d-20261016-184501-3117db
title: Publication Media
added_date: "2026-10-16 18:45:01"
last_updated: "2026-10-16"
summary: The purpose of publication-media.json, what maintains it, when it changes and how it differs from the Publish queue.
parent_id: d-20260911-152718-b21705
---
# Publication Media

`publication-media.json` records the media currently used by saved Working documents. It remembers the previously saved media list, so the next Save can compare it with the edited document and identify exactly which owned files have been removed.

## Location And Owner

| Item | Description |
| --- | --- |
| Location | `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/documents/publication-media.json` |
| Maintained by | Working document generation: the build that produces a document's saved reader output. |
| Coverage | Ordinary and configured collection documents that own document media, including Draft documents. |
| Public or private | Private Working state. The file is not copied to Preview or the public site. |

There is one workspace file. Named collections have records inside it rather than separate copies of the file.

## What It Records

Document records are under `documents`, keyed by document ID. Each record has two fields:

| Field | Meaning |
| --- | --- |
| `collection` | The configured collection ID, or an empty string for ordinary documents. |
| `media` | The saved source's media references, grouped by type (`img`, `svg`, `files`, `html`, `thumbs`). Each list contains unique relative file identities. The independent thumbnail assignment is included. Draft documents retain their references. |

For example:

```json
{
  "collection": "works",
  "media": {
    "img": ["d-20260801-212422-60f1db/cards-face.webp"]
  }
}
```

Generation uses this same list to select eligible publication media and compare previous/current owned references for removal. It does not extract a second list from rendered HTML. There are no separate authored-media, producer-companion or diagram-production records. Diagrams imported as SVG use the ordinary `svg` list.

The top-level `ignored` list records the publication exclusions last applied by the owning build. Ordinary Save/Rebuild uses that saved policy; explicit complete document builds read changes to the exclusion policy.

This is a reference record, not a directory inventory. It does not list every stored file or identify every orphan. A document with no remaining media may have no record.

## What Updates It

| Action | Effect on this file |
| --- | --- |
| Source Save | Builds the saved document and updates its media record, including changes made with Add/Edit Image or Add file. |
| Exact document Rebuild | Recomputes the selected document's record from its saved source. |
| Import or another source-writing action | Updates records when its document-generation step completes. |
| Draft change | Runs exact generation. Owned media remains recorded; Draft alone does not remove it. |
| Collection build or complete Working Build | Updates records for the documents it builds. Targeted builds preserve unselected records. |
| Document deletion | Removes the deleted document's record. Whole-document media cleanup remains manual. |

The file is written only when its recorded contents change. Saving an unrelated text edit can therefore leave its contents and modification time unchanged.

Choosing a file or applying a token in the unsaved Source buffer does not update it. Neither does Publish, Docs Media Refresh, Search/Recent refresh or simply opening a document. Editing Markdown outside the application needs an explicit document Rebuild; there is no filesystem watcher.

## When The Update Happens

For Source Save, the order is:

1. Write the selected new/replacement media and save the source.
2. Build the document and compare its previous/current owned media references.
3. Save the exact pending publication effects in the Publish queue.
4. Complete selected Working media removals, then save the new record in `publication-media.json`.

Save waits for this handoff. If a selected removal fails, the previous record remains available and the error reports completed effects; the queued public removal is retained.

## Difference From The Publish Queue

| File | Question it answers |
| --- | --- |
| `publication-media.json` | What media does this saved document currently use? |
| `working/docs-publish-pending.json` | What document/media writes or removals must the next Publish apply? |

For example, saving a Draft document with a new image records that image here and stores it in Working, but does not queue its public upload. Removing an old owned image can still queue that exact public removal. This is why a Draft document can have current images in `publication-media.json` while its Publish queue entry contains only removals.

Publish consumes and clears completed queue selections. It does not update `publication-media.json`.

## Inspection And Maintenance

Read this file to inspect saved media ownership. Change document references through Source Save or an explicit Rebuild after external source edits. Although this is generated data, its previous-reference baseline is needed for removal decisions, so it should not be treated as a disposable cache or edited manually.

[Media And Asset Handling](../Media_And_Asset_Handling.md#saved-ownership-and-exact-removals) explains the detailed lifecycle. The maintaining code is [docs_publication_preparation.py](../../../docs-viewer/services/docs_publication_preparation.py).
