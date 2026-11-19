---
draft: false
doc_id: d-20260927-223812-8042fc
title: Catalogue Save And Refresh
added_date: "2026-09-27 22:38:12"
last_updated: "2026-11-18"
summary: Current Catalogue Save, local Refresh, reader freshness and recovery boundaries.
ui_status: stable
parent_id: d-20260519-000000-a0da45
---
# Catalogue Save, Refresh, Regenerate and Publish

Studio owns canonical Works, Series, Galleries and memberships in `studio/data/canonical/catalogue/`. Docs Viewer adopts refreshed Work facts into each Catalogue document and publishes completed selections. Follow the two examples in [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md). [Work Editor](Catalogue_Work_Editor.md) · [Canonical source model](Catalogue_Source_Model.md)

## Current Workflow

| Step | Replace the image of an existing Work | Rename a Gallery used by Works |
| --- | --- | --- |
| **Save in Studio** | Confirm the image and Save. Persist the Work, prepare its image set in Projects staging and select its exact Work ID and image effect. The editor can show the staged image immediately. | Edit the Gallery title and choose OK. Save the definition and select the Gallery and shared files. Select Work metadata for the direct members and Works in Series explicitly related to that Gallery. |
| **Refresh Catalogue in Studio** | Hand the selected ready image set and Work record to Working, clear the staging flag and remove the staged copies. Mark the Work ready for Regenerate. | Update the Gallery record, compact Gallery index, report-search projection and affected Series–Gallery title rows. Forward public shared selections directly to the publication queue. Refresh the affected Work records and mark those entries ready for Regenerate. |
| **Regenerate in Docs Viewer Manage** | Adopt the refreshed Work record and media facts into the same Catalogue document ID. Queue the document and selected image set. | Adopt the new Gallery title into the affected Works' Catalogue documents and queue those documents. The rename adds no media effects to any existing selections. |
| **Publish in Docs Viewer Manage** | Apply the Work document and selected image set to Preview and configured destinations. The Work queue entry clears on completion. | Distribute the selected Work documents first and the shared Gallery artifacts in the final Catalogue phase. Deploy the updated Pages snapshot separately. |

A Gallery **Description** or marker edit selects the Gallery and `galleries/report-search.json` at Save. The report file contains these presentation fields. Refresh can preserve an unchanged Gallery by-ID file while still forwarding its Gallery selection. This edit adds no Work to Regenerate. Search and Recent have their own explicit preparation action. [Shared projections](Catalogue_Indexes_And_Payloads.md#generated-read-models) · [Publish and deploy](../guide/Publish_And_Deploy.md)

To locate a stale result, check the surface that owns it. Studio shows saved fields and staged media. After Refresh, Working has the new media bytes and Gallery records, while the existing Catalogue document may still carry its previous Work facts or Gallery labels. Regenerate updates that document. Public Gallery and Work JSON come from the deployed Pages snapshot, and public Work media comes from the configured asset destinations. [Reader data and destinations](#storage-and-selection)

## Save Boundary

The editor owns the draft, field completion, membership choices and selected image/upload intent. Python persists canonical changes and prepares selected files. The editor adopts the returned saved records; normal Save does not do another Work lookup. A post-write failure can leave a valid saved Work with unfinished local media or queue effects. Use the reported ID and phase, correct the selected input or destination and continue on the existing Work. In batch creation, use the reported created IDs instead of repeating Create. [Write service](../../studio/services/catalogue/catalogue_write_service.py) · [Work Editor](Catalogue_Work_Editor.md#create-and-save)

### Work Media Authoring

**Choose image** confirms a Projects original. New Works, changed image inputs and explicitly confirmed selections prepare a complete primary rendition and thumbnail set. Successful Save exposes it under Projects `dotlineform-site/catalogue/media-staging/`. `image_staged` selects that set and each managed download has its own `staged` flag. False selects the Working copy. `media_version` changes when existing rendition bytes differ. First media at a fresh ID starts at 1. A reused ID with differing existing bytes can advance the version. Refresh and Publish carry the version through unchanged.

**Add file** holds a native upload in the draft. Save normalizes its name under the exact Work ID and retains its label. Selecting the same derived filename replaces its bytes and keeps the edited label. Use a distinct basename for a second attachment. A label edit or removal does not recheck unchanged attachments. **Choose source folder** relinks original locations without requesting image processing. [Work Editor media](Catalogue_Work_Editor.md#persistent-media) · [Attachment owner](../../studio/services/catalogue/catalogue_work_attachments.py)

## Updates Queue

`working/catalogue-updates-pending.json` uses `catalogue_updates_pending_v5`. Current Work records carry `metadata`, `image`, `file_names` and `refreshed`; deletions carry exact owned media descriptors. Save merges known effects by ID. New work starts at `refreshed: false` and a later edit can return a ready entry to false. Work Delete captures its media descriptors before removing canonical data and memberships. Its staged-file cleanup uses those same selections.

Gallery/Series current and deleted IDs and explicit shared filenames are independent of Work readiness. `created_galleries` selects complete initial member projection. `gallery_member_works` carries exact title, identity or membership changes for existing Gallery rows. A Gallery rename or relevance edit can queue Work adoption without replacing unrelated saved member rows. [Pending updates owner](../../studio/services/catalogue/catalogue_pending_updates.py) · [Gallery save owner](../../studio/services/catalogue/catalogue_gallery_service.py)

## Refresh Boundary

Refresh consumes false-readiness Work entries and exact shared selections. Per Work, it updates the private report row, hands off selected image/download bytes, updates the Work record when its content version changes, saves cleared staging flags and removes the staged files just copied. It then persists `refreshed: true`. A deletion removes the selected Working record and media. Already-ready Works stay in the queue for Regenerate. Selection comes from the queue; the saved content version only avoids an unchanged record write.

Shared projection merges selected rows into saved indexes. Refresh moves eligible public shared selections into the publication queue before clearing them from updates. Private report outputs remain in Working. The success timestamp advances only on complete Refresh. On failure, the reported Work or shared target and phase identify the next repair. If staging cleanup fails after flags clear, the Working copies remain ready for the next transfer check and leftover staged files require manual inspection. Missing required shared output calls for explicit maintenance. [Refresh owner](../../studio/services/catalogue/catalogue_refresh_service.py)

### Private Report Input Maintenance

Use the focused command for an intentional schema/projection change or to restore missing required saved output. Run from the repository root with the project interpreter. Each option writes only its named output family and leaves unrelated pending selections and lifecycle times with their existing owners. Finish unrefreshed Work handoffs before private-input maintenance.

| Command option for `python3 studio/services/catalogue/catalogue_json_build.py --write` | Output |
| --- | --- |
| `--private-report-inputs` | `private/work-sources.json`, `private/work-resources.json`, `private/series.json` |
| `--compact-indexes` | Compact Work and Gallery ID/title indexes |
| `--series-galleries` | Public relationship index and private Series–Gallery report |
| `--gallery-records` | Exact Gallery records and selected Gallery deletions |

[Maintenance command](../../studio/services/catalogue/catalogue_json_build.py) · [Read models](Catalogue_Indexes_And_Payloads.md)

## Regenerate Timing

**Regenerate** starts immediately in the Catalogue collection and presents the result after generation and the collection refresh settle. It refuses pending shared Refresh work and otherwise consumes only Work entries already marked refreshed. It reads their exact Working Work and relationship data, creates or retitles sources as needed, rebuilds unchanged-title documents without rewriting their source, and applies selected deletions. Regenerate writes each completed publication selection before clearing that Work's update entry. Correct the failed source/build/queue phase and rerun the owner for remaining entries. [Regeneration service](../../docs-viewer/services/docs_catalogue_regeneration.py)

Use `python3 docs-viewer/build/reconcile_catalogue_design.py --write` for deliberate Catalogue template/design reconciliation. It preserves unrelated false-readiness entries and selects document changes, with existing media effects carried forward. Full Working Build excludes Catalogue bulk generation. Its exact dependency renders can queue document-only Docs effects. Catalogue-facing Source and standalone document Rebuild are unavailable in the normal UI. A referring document's inline presentation follows its own build and publication lifecycle. [Generated data contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation)

## Storage And Selection

`working/catalogue-publish-pending.json` uses `catalogue_publish_pending_v5`. It has current/deleted Work maps, current/deleted Gallery and Series IDs, and explicit shared filenames. A current Work carries `metadata`, `image` and `file_names`. Regenerate merges existing image and still-referenced download selections. Removing a download reference cancels its unneeded pending transfer; older unreferenced bytes are a manual cleanup decision.

| Work artifact | Working/Preview relative location | Public destination |
| --- | --- | --- |
| Catalogue document | Generated Working collection by-ID, then Preview collection by-ID | `site/assets/data/docs/catalogue/by-id/<id>.json` |
| Primary images | `assets/works/primary/` | Configured R2 `works/img/` |
| Thumbnails | `assets/works/thumbs/` | `site/assets/data/catalogue/works/thumbs/` |
| Downloads | `assets/works/media/files/` | Configured R2 `works/files/` |

The Work handoff record `works/index/<id>.json` is a Working Regenerate input. The public Work document carries its adopted fields. Catalogue has no ordinary document-media namespace. [Workspace locations](../../docs-viewer/config/workspace/docs-workspace.json)

## Per-Work Publish

One **Publish** consumes both prepared queues. It processes Catalogue Work units, then selected Docs units, then Catalogue shared output. Each Work unit prepares its portable document from the adopted Working payload, applies its selected writes/removals to Preview and repository/R2 destinations, verifies the selected transfers and clears on success. Exact matching remote objects can be reused. Referring Docs units may select a required inline Work rendition and reuse completed transfers. Upstream readiness and discovery preparation have their own actions. Empty publication queues return immediately. [Publish orchestrator](../../docs-viewer/services/docs_publish.py) · [Catalogue transfers](../../docs-viewer/services/docs_catalogue_publication.py)

Work `last_published_at_utc` advances when the last Work unit completes. Shared-only Publish leaves it unchanged. An error in a later unit leaves successful earlier effects complete.

## Final Shared Output

The Catalogue inventory selects exact Gallery by-ID files and named shared indexes. Series completion represents aggregate effects with no Series by-ID artifact. Public Catalogue document manifests and Search/Recent are distinct Docs shared selections. A later Publish can apply a completed Gallery definition even while associated Work updates still await Regenerate. Finish both paths first when the release should show consistent definitions and Work links. [Public Catalogue inventory](../../docs-viewer/config/workspace/catalogue-artifacts.json)

## Failure And Timing

Use the phase and target to locate the failed owner. Correct that input or destination and rerun the relevant action for its remaining selections. Local and remote effects already completed stay in place. Readiness, successful Refresh time and Work publication time describe their own operations. Public content follows the tracked repository snapshot, while selected R2 changes take effect during Publish. Inspect the updated snapshot with `bin/site-preview`, then commit, push and deploy as separate actions. [Design rationale](../design/Catalogue_Authoring_And_Adoption.md) · [Delivery evidence](../deliveries/Catalogue_Changed_Regeneration_Delivery.md#later-lifecycle-evidence)
