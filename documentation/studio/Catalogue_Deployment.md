---
draft: false
doc_id: d-20260909-205938-3569d6
title: Catalogue Deployment
added_date: "2026-09-09 20:59:38"
last_updated: "2026-10-19"
summary: Queued Work publication, separate Preview media, exact repository/R2 deployment and final shared output.
parent_id: d-20260902-102745-8379ea
---
# Catalogue Deployment

## Current Lifecycle

Studio Save persists canonical metadata, stages prepared media and queues known changes. Refresh completes selected Working outputs; Catalogue Regenerate completes saved documents and forwards exact publication selections. Direct Catalogue Source Save/Rebuild controls remain absent from the UI. Their shared generation owner still prepares and queues document-only completion for explicit service/CLI generation. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns upstream effects and design maintenance.

One empty-body `POST /docs/publish` action processes queued Catalogue Works, Docs document/media units and selected shared output. `docs_publish.py` carries the resolved workspace and both parsed publication queues through completion. It never runs Refresh, Regenerate or a full document build, reads the updates queue, filters eligibility or scans destinations. Empty publication queues return without artifact reads, transfers, removals or timestamp writes.

## Storage And Selection

[Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) owns the existing Docs root, independent Working/Preview asset roots and public destinations. Catalogue declares `document_media: false`: its document collection has no Docs media namespace. Work primaries, thumbnails and downloads retain separate Work-media owners.

| Material | Working/Preview owner | Public destination |
| --- | --- | --- |
| Work metadata | `working/generated/catalogue/works/index/<id>.json`, then `preview/catalogue/works/index/<id>.json` | `site/assets/data/catalogue/works/index/<id>.json` |
| Catalogue document | Existing `working/generated/collections/catalogue/documents/by-id/<id>.json`, then `preview/collections/catalogue/documents/by-id/<id>.json` | `site/assets/data/docs/catalogue/by-id/<id>.json` |
| Primary images | `<stage>/assets/works/primary/` | Configured R2 `works/img/` |
| Thumbnails | `<stage>/assets/works/thumbs/` | `site/assets/data/catalogue/works/thumbs/` |
| Downloads | `<stage>/assets/works/media/files/` | Configured R2 `works/files/` |

Studio staging remains Projects-owned and project originals retain their owner. Local readers use Working media; public readers use configured repository/R2 destinations. Operational staging/queue fields are private.

The [Catalogue artifact inventory](../../docs-viewer/config/workspace/catalogue-artifacts.json) allows Work/Gallery by-ID JSON and explicit public system files. Publish reads only selected finished files. Unselected Catalogue output, private reports, public report configuration and archive files retain their bytes.

## Per-Work Publish

`working/catalogue-publish-pending.json` uses `catalogue_publish_pending_v5`. Current/deleted Work maps retain exact IDs, image-set booleans and download filename lists; current records also carry `metadata`. Shared Gallery/Series arrays and `shared_outputs` remain independent. No record contains `preview_done` or another resume flag.

```json
{
  "header": {
    "schema": "catalogue_publish_pending_v5",
    "last_published_at_utc": null
  },
  "current_works": {
    "00008": {
      "metadata": true,
      "image": true,
      "file_names": ["00008-notes.pdf"]
    }
  },
  "deleted_works": {},
  "current_galleries": ["003"],
  "deleted_galleries": [],
  "current_series": [],
  "deleted_series": [],
  "shared_outputs": ["galleries/galleries_index.json", "works/works_index.json"]
}
```

The common generation handoff prepares public Catalogue documents upstream and merges completed Regenerate/design-maintenance or explicit Catalogue CLI IDs into one carried Catalogue queue, preserving existing media selections. Regenerate carries its preparation state and publication queue through the operation rather than reloading them for each Work. Full Working Build excludes Catalogue from bulk generation and does not add Work selections. Exact Catalogue dependency renders use the Docs queue for document-only publication, without selecting Work JSON or media.

`docs_catalogue_publication.py` invokes the shared `docs_catalogue_static.py` preparer for the current Work document before applying refreshed metadata, prepared document and selected image/download bytes to Preview/distribution. Working Work metadata bytes are reused between preparation and physical JSON publication. Preparation alone adds no blanket image/download transfer to a Work unit; its queue selection remains authoritative. Deletion uses retained exact identities and requires no Working input. It never means deletion of canonical Work records or project originals. Removing a download reference cancels its pending transfer but does not automatically remove previously stored unreferenced bytes.

Queued Docs documents may independently require Work renditions/files returned by static preparation. These remain Work-owned transfer inputs within that document unit, without a second queue entry. `docs_catalogue_media_transfer.py` applies exact selected objects and reuses completed owner/object effects across both unit families. A missing input or failed transfer retains the current unit; successful earlier effects remain complete. Prepared Catalogue documents include their own embedded Media View presentation. Physical Work/Series–Gallery JSON distribution remains in place even though the public document renderer no longer reads it.

Selected remote media uses exact-object size/ETag comparison to skip matching uploads and verifies changed transfers/removals. No remote listing or ownership scan runs. Only successful document/metadata/media completion removes that Work entry, before the next Work begins.

`last_published_at_utc` retains its Work-queue meaning: the final successfully distributed Work records completion when the Work maps become empty. Initially empty or shared-only operations preserve it, and a later shared failure does not erase completed Work publication. The Docs queue has its own independent completion timestamp.

## Final Shared Output

Refresh forwards completed Gallery/Series effects and only public system files from the inventory. Current Gallery IDs select exact `galleries/index/<id>.json` writes; deleted Gallery IDs select exact removal. Series IDs represent already prepared aggregate effects and create no Series by-ID artifact. Each shared selection is removed only after its own required Preview/repository completion.

Document generation separately prepares and queues ordinary navigation, eligible Selected and public collection manifests, including the Catalogue document manifest. Catalogue Work/media selections retain their domain queue. Exact dependency and collection-host eligibility effects are document-only Docs selections; they never imply Work JSON/media publication or canonical Work deletion. Host Draft/Delete changes remain design-time-owned.

Full Working Build generates and queues Recent; explicit Search builds queue their existing exact bytes. Publish only transfers queued shared output and does not run an unconditional final pass, rebuild discovery, parse canonical source, produce media or verify a whole snapshot. Selected current document JSON is parsed for static Catalogue preparation; deletes/shared-only units bypass it. [Builder](Builder.md#publish-preparation) owns the upstream document handoff.

## Failure And Timing

The first error stops Publish and reports phase, target, completed units and partial-unit effects. Successful writes/removals and persisted queue removals remain complete; failed/unprocessed selections stay pending. Diagnosis/correction and whether another Publish will work are manual decisions. There is no safe-retry guarantee, persisted checkpoint, recovery procedure, rollback, authoring lock, backup tree or second publication ledger.

The browser remains busy through the awaited request and reports the returned error. Publish does not write Working Recent, refresh browser Recent or reload capabilities. Repository/R2 effects remain non-atomic, so temporary item/shared or public-media/site differences are possible. Review repository output through `bin/site-preview`; Git commit/push and GitHub Pages deployment remain separate actions.

Cutover on 2026-10-15 used the user's completed Full Build/Publish and empty queues. Internal public preparation completed for 5,192 documents, including 4,947 eligible documents, with the new Docs queue empty and Catalogue time retained. Focused source lint, syntax/import diagnostics and bounded redundancy/defensive review provide static evidence only. Tests, browser scenarios, new live Publish behavior, remote transfers, partial failures and manual acceptance remain unexercised. Older accepted Catalogue add/delete observations apply to the former publication path.
