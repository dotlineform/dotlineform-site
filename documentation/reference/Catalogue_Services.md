---
draft: false
doc_id: d-20260422-000000-fb2894
title: Catalogue Services
added_date: "2026-04-22 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6
---

# Catalogue Services

Studio's browser owns the draft, selection, authoring feedback and membership choices. Python owns exact source persistence, image/file preparation, Working projection and transfer. Start with the user action and follow the values already resolved by its owner. [Browser and route ownership](Studio.md) · [Canonical source](Catalogue_Source_Model.md)

## Follow A Work Save And Refresh

For an existing Work such as `00008`, change a field or confirm a replacement image, then Save.

| Step | Owner and completed state |
| --- | --- |
| Capture Save | `catalogue-work-actions.js` validates the draft and captures exact Work ID, authored `record`, Gallery choices and media intent. `catalogue-editor-service-client.js` sends JSON or multipart for pending native attachments. |
| Dispatch | `studio_app_server.py` bounds/decodes the request. `studio_catalogue_api.py` delegates `/work/save` to `catalogue_write_service.py`. |
| Persist | `catalogue_work_service.py` reads Works and memberships, prepares the candidate through `catalogue_source_mutation.py`, and writes changed maps through `catalogue_transactions.py`. It carries previous/current records and known shared effects onward. |
| Complete Save | `catalogue_output_service.py` selects changed image inputs, explicit image confirmation and added/replaced downloads. `catalogue_output_media.py` prepares exact bytes. `catalogue_media_version.py` persists measured dimensions, version and staging flags with prepared media. Completion merges exact Work/shared effects into the updates queue and supplies the final saved editor records. |
| Display Save | The browser adopts returned records into the draft baseline, search/member maps and preview. It marks Refresh needed from the result. A normal successful Save needs no second Work lookup. |
| Request Refresh | `catalogue-work-editor.js::runCatalogueRefresh` sends one empty-body `POST /studio/api/catalogue/refresh`. It requires a settled clean draft and keeps the operation busy through the returned records and preview update. |
| Prepare Working | `catalogue_refresh_service.py` reads the queue and uses `catalogue_refresh_inputs.py` to load each required canonical map once. It updates selected saved projections, hands off selected media, clears staged flags, cleans copied staging files and persists Work readiness. Completed shared public selections enter the publication queue before their update selections clear. |

[Save controller](../../studio/app/frontend/js/catalogue-work-actions.js) · [Write dispatcher](../../studio/services/catalogue/catalogue_write_service.py) · [Save completion](../../studio/services/catalogue/catalogue_output_service.py) · [Refresh owner](../../studio/services/catalogue/catalogue_refresh_service.py)

Projects `catalogue/media-staging/` holds Save's prepared bytes. Refresh transfers them to Docs `working/assets/works/` and writes reader JSON under `working/generated/catalogue/`. A ready Work remains queued for Docs Viewer Regenerate. The browser adopts Refresh's returned records so its preview follows the cleared staging flags. [Queue fields, reader timing and publication](Catalogue_Save_And_Refresh.md)

## Follow A Shared Definition Change

Series title Save runs through `catalogue_series_service.py`. It reads Series once, reads Works for a changed title, persists the definition and supplies affected member IDs and private Series/report selections to completion. Series creation reads the Series map and creates an empty definition. Choosing it in the Work form supplies a later assignment.

Gallery Save runs through `catalogue_gallery_service.py`. A title or relevance change uses direct memberships and old/new relevance endpoints to select affected Works. Description/marker changes select the Gallery/report presentation. Definitions, membership and relevance have separate source stores, and the mutation carries its exact shared effects through the same Save completion. [Series service](../../studio/services/catalogue/catalogue_series_service.py) · [Gallery service](../../studio/services/catalogue/catalogue_gallery_service.py) · [Known-effect selection](../../studio/services/catalogue/catalogue_shared_changes.py)

Refresh merges selected rows into existing Gallery, compact, relationship and private report projections. Explicit creation/member candidates distinguish initial Gallery content from changes to saved member rows. The queue already supplies the selection. Refreshed Work facts feed the later Catalogue document operation. [Detailed lifecycle](Catalogue_Save_And_Refresh.md#updates-queue)

## API Surface

The Catalogue adapter serves these paths beneath `/studio/api/catalogue`.

| Method and suffix | Purpose |
| --- | --- |
| GET `/health`, `/read` | Service availability and allowlisted live canonical/search reads. Focused `/read` requests use `key` and `record_id`. |
| POST `/work/lookup` | Exact selected Work records from an `ids` array. |
| GET `/project-media` | Configured source identities and confined folder/file choices. |
| POST `/project-media/open`, `/project-media/preview` | Open a selected local original or return a disposable image preview. |
| POST `/work/create`, `/work/create-batch`, `/work/save` | Individual or confirmed subfolder Work intake and Save. |
| POST `/bulk-save` | Apply explicit changes to selected Work records and memberships. |
| POST `/series/create`, `/series/save` | Definition creation or title edit. |
| POST `/gallery/create`, `/gallery/save`, `/gallery/delete` | Shared Gallery definition/relevance operations. |
| POST `/delete-apply` | Exact Work IDs, or the UI-confirmed empty Series. |
| GET `/refresh-status`, POST `/refresh` | Queue-derived readiness/time, and synchronous empty-body Refresh. |

The app additionally serves GET `/health` and `/studio/runtime-config.json`. Requests resolve their filesystem owner on the server. Project-media paths retain confinement and selected input checks. [API dispatch](../../studio/app/server/studio/studio_catalogue_api.py) · [Bounded upload parser](../../studio/app/server/studio/studio_catalogue_upload.py)

## Persistence And Failure

The source transaction stages selected JSON bytes and replaces target files, attempting restoration if replacement fails. Media finalization uses that transaction owner for prepared bytes and changed media metadata. Canonical editing and the later local completion are separate phases. [Transaction implementation](../../studio/services/catalogue/catalogue_transactions.py)

Save completion sets `saved: true` after canonical success and can return `save_completion.status: failed` for unfinished media, editor-response or queue/staging effects. The browser adopts saved state and reports the remaining failure. Correct the reported cause on the existing ID. For a created batch, use its returned created IDs before retrying. [Save result handling](../../studio/app/frontend/js/catalogue-save-result.js) · [Recovery](Catalogue_Save_And_Refresh.md#save-boundary)

Refresh persists per-Work readiness after that Work's required handoff. Its shared output may be partially written before a later error. The error names Work/shared target and phase, and the last-success time advances only after full completion. Fix that phase and rerun the owning operation. Explicit repair handles missing saved shared baselines. [Refresh recovery and repair](Catalogue_Save_And_Refresh.md#refresh-boundary)
