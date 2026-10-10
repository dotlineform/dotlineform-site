---
draft: false
doc_id: d-20260909-205938-3569d6
title: Catalogue Deployment
added_date: "2026-09-09 20:59:38"
last_updated: "2026-10-10 10:42:03"
summary: Queued Work publication, separate Preview media, exact repository/R2 deployment and final shared output.
parent_id: d-20260902-102745-8379ea
---
# Catalogue Deployment

## Current Lifecycle

Studio Save persists canonical metadata, stages prepared media and queues known changes. Refresh transfers selected false-readiness entries to Working. Regenerate completes refreshed Catalogue documents and forwards their selections to the publication queue. Successful direct Catalogue Source Save/Rebuild contributes a metadata/document-only selection through the same merge owner, preserving existing media selections and progress. The single empty-body `POST /docs/publish` operation processes each queued Work through Preview and Deploy, then prepares and distributes shared output once. Git commit/push and GitHub Actions deployment remain separate explicit operations.

`docs_publish.py` owns orchestration. `docs_catalogue_publication.py` owns per-Work publication; `docs_prepare_preview.py` and `docs_deploy_repo.py` own the final shared pass. Publish does not run Refresh or Regenerate, inspect the updates queue, infer upstream readiness or advance image versions. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns upstream completion and explicit design maintenance.

## Storage And Selection

[Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json), schema `docs_workspace_v5`, owns storage beneath the existing Docs root. Work media has independent `assets.work_roots.working` and `assets.work_roots.preview`; ordinary document media remains shared.

| Material | Working/Preview owner | Public destination |
| --- | --- | --- |
| Work metadata | `working/generated/catalogue/works/index/<id>.json`, then `preview/catalogue/works/index/<id>.json` | `site/assets/data/catalogue/works/index/<id>.json` |
| Catalogue document | Working generated collection document, then `preview/collections/catalogue/documents/by-id/<id>.json` | `site/assets/data/docs/catalogue/by-id/<id>.json` |
| Primary images | `<stage>/assets/works/primary/` | Configured R2 `works/img/` |
| Thumbnails | `<stage>/assets/works/thumbs/` | `site/assets/data/catalogue/works/thumbs/` |
| Downloads | `<stage>/assets/works/media/files/` | Configured R2 `works/files/` |
| Document/collection media | Shared `assets/media/workspace/<type>/` and `assets/media/collections/<id>/<type>/` | Configured document repository/R2 bindings |

Studio staging is Projects-owned `catalogue/media-staging/`; project originals retain their owner. Local readers resolve Working media through unchanged `/docs/assets/works/...` identities. Public readers use repository thumbnails and configured R2 primary/download URLs. Operational staging and queue fields are private.

The [artifact inventory](../../docs-viewer/config/workspace/catalogue-artifacts.json) declares Work/Gallery by-ID directories and shared media policy, Work/Gallery indexes and Series–Gallery relation index. The final pass captures shared Working JSON and retains completed Preview Work by-ID bytes. It does not recopy all Working Work records or enumerate/hash Work media. Undeclared Catalogue files and the archive stay outside publication.

## Per-Work Publish

`working/catalogue-publish-pending.json` uses `catalogue_publish_pending_v3`. Its header is written first, with `schema` followed by nullable `last_published_at_utc`. Current and deleted maps are keyed by exact five-digit Work ID. Each entry retains an image-set selection, sorted exact download basenames and `preview_done`; current entries also carry `metadata`.

`last_published_at_utc` records completion of a nonempty Catalogue Work publication queue. The final queued Work's successful Deploy removes its entry and records that UTC time in the same queue write. Contributors, intermediate Work completions, an initially empty queue and partial failures preserve the previous timestamp. A later shared-output failure leaves the completed Catalogue timestamp intact. It starts null until the first queued Catalogue publication completes; it does not represent completion of the whole Docs Publish.

Example of completed upstream changes awaiting publication:

```json
{
  "header": {
    "schema": "catalogue_publish_pending_v3",
    "last_published_at_utc": null
  },
  "current_works": {
    "00008": {
      "metadata": true,
      "image": true,
      "file_names": ["00008-notes.pdf"],
      "preview_done": false
    }
  },
  "deleted_works": {}
}
```

Current entries have exactly `metadata`, `image`, `file_names` and `preview_done`; deletion entries omit `metadata`. The current and deleted maps are disjoint. Flags are explicit booleans and filenames are sorted distinct safe basenames. A missing or malformed queue stops publication; no old-format alias or empty fallback is provided. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#updates-queue) owns the upstream queue and readiness.

Regenerate merges completed changes before removing their updates entry. Design maintenance and successful direct Catalogue Source Save/Rebuild use the same [publication merge owner](../../studio/services/catalogue/catalogue_pending_publication.py). Current metadata/image flags accumulate with OR; filename selections combine and retain only references in the supplied refreshed Work metadata. A new record receives `preview_done: false`; an existing record keeps its initialized flag without inspection. Completed deletion or recreation replaces the opposite family's selection while preserving initialized progress. Every upstream contribution preserves the header and its last successful queue time.

Removing a download reference cancels its outstanding transfer selection and publishes the updated document/metadata. It does not automatically remove previously stored unreferenced media. Work deletion carries the exact image set and retained current download identities through Preview and Deploy. A true `preview_done` flag records interrupted Deploy, so finish that Publish before resuming authoring, Refresh or Regenerate.

When false, Preview copies the Work's refreshed metadata, completed Catalogue document and only selected image/download bytes, or removes its exact owned files for deletion. Completion sets the flag true after required Preview writes succeed. The completion receipt is invalidated before partial Preview mutation.

Deploy uses Preview bytes and the retained selection. It copies/removes exact repository metadata, documents and thumbnails, then uploads/deletes selected R2 primaries/downloads using configured prefixes. It uses no remote listing, ownership scan or newer Working media. Missing owned deletion targets count as success. Required upload inputs must exist and be nonempty; completed transfers/deletions are verified.

Only successful combined repository/R2 deployment removes the entry. Each Work completes before the next begins. A retained true flag means interrupted Deploy: correct and complete that Publish before resuming normal authoring. All upstream queue contributors preserve initialized progress without inspecting or resetting it.

## Final Shared Output

Once the queue is empty, including an initially empty queue, Publish captures eligible ordinary/collection sources, saved Search and relationship inputs. It rebuilds ordinary and other collection documents in temporary storage while retaining already completed Catalogue by-ID documents. The Catalogue list manifest is derived from retained document metadata with date-only updates. Shared Catalogue indexes and Gallery records update once. Preparation eligibility, including excluded report hosts, still owns the complete prepared document set.

Preview snapshot replacement prunes the stage-local `assets/` subtree from its file inventory. It neither scans, hashes nor deletes Work media. The completion receipt verifies snapshot JSON and document-media references; per-Work completion owns Work media effects. Distribution compares shared repository/document-media destinations once and applies its retained plan. Search bytes are copied unchanged; Recents is freshly prepared by its existing owner. Missing retained Catalogue documents require their queued regeneration or explicit design maintenance before Publish can finish.

Public document payloads retain query-only Docs links and logical `docs-media:` references. The public section remains `/analysis/`. Publish preserves independently owned `public-reports.json` and the configured archive.

## Failure And Timing

Failures report the Work and Preview/Deploy step, or the final shared-output step. Completed effects remain. Failed/unprocessed queue entries retain their selection and accurate progress; no automatic retry, rollback, backup tree or separate R2 ledger is introduced. Final-pass failure can occur after all Work entries have completed; the next explicit Publish still runs the final pass.

Repository and R2 effects are not atomic. R2 transfers precede later GitHub Actions deployment, so existing public pages may show new image bytes with older deployed commentary. That timing gap remains accepted. Review successful output through `bin/site-preview`. On 2026-10-10, the user confirmed new Work addition and subsequent deletion through the complete workflow to R2. Managed-file and other variants remain unverified, and live failure/retry behavior received source review only. The user perceived a quicker Catalogue queue Publish; no timing measurement is claimed.

These are current implemented operations. Remaining manual coverage is recorded as an evidence limit rather than a proposed workflow. Missing retained Catalogue documents require queued Regenerate or explicit design maintenance; ordinary document Rebuild, Catalogue Refresh and publication remain separate owners. Removing Catalogue document editing, exact Gallery/Series queues and incremental ordinary-document Publish are separate follow-ons.
