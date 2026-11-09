---
draft: false
doc_id: d-20261109-175018-2b74f1
title: Catalogue Index Gallery Results
added_date: "2026-11-09 17:50:18"
last_updated: "2026-11-09"
summary: Add compact Gallery matches to the paginated Catalogue report using a Studio Refresh projection.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Index Gallery Results

## Current And Next State

Complete. The user accepted the local result, ran Publish and confirmed the public Catalogue result after Deploy Public on 2026-11-09. Commit `1702ef2a37` carries the runtime and published search JSON together on `origin/main`. [Catalogue Indexes And Payloads](../Catalogue_Indexes_And_Payloads.md#work-and-gallery-projections) owns the shipped data contract. Retain this delivery for acceptance evidence pending manual archive.

## Results And Pagination

- For a nonempty Catalogue query, show Gallery title matches first, followed by other Galleries that contain directly matching Works, followed by the Work results in their existing sort order. Match Gallery titles with the same normalized substring rule as Work titles. Sort title matches by title and member matches by descending match count, with title and Gallery ID as tie-breakers. A Gallery appears once, in the earliest matching group.
- Count matching direct members across the full Work result set before pagination. The Work match remains the report's existing title or Work ID match. A Gallery title match contributes the Gallery itself. Its members appear as Work results only when they match the query independently. A blank query displays the ordinary Work list.
- Paginate the combined rows at the existing 20 results per page. Gallery rows use a text-sized `images.svg` icon, a bold title and no thumbnail slot. Member-derived rows add a quiet count such as `6 matching works`. A Gallery opens in the existing Media View and Back restores the query, page and opener. Work selection and management actions continue to target Work rows.

For `kylie`, the Working snapshot has 71 Work matches and three Gallery title matches. The saved direct memberships also give *colours* six matching Works and *composites (book, 2023)* and *maps* two each. Page 1 would contain those six Gallery rows and the first 14 Work rows. Page 2 would continue with Works. [Collection manifest contract](../Generated_Data_Contracts.md#collection-manifest-ownership) · [Gallery projections](../Catalogue_Indexes_And_Payloads.md#work-and-gallery-projections).

## JSON Used By The Report

`C` below is the configured Catalogue artifact root. In Working it resolves to `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. The tracked public root is `site/assets/data/catalogue/`, served at `/assets/data/catalogue/`.

| JSON | Current or proposed role |
| --- | --- |
| Working `working/generated/collections/catalogue/documents/manage-manifest.json` under `$DOTLINEFORM_DOCS_BASE_DIR` and public `site/assets/data/docs/catalogue/manifest.json` | **Current search input.** The report filters loaded Work rows by `title` or `doc_id` and uses `last_updated` for sorting. Manage loads `/docs/generated/external/catalogue/manage-manifest.json`. Public loads `/assets/data/docs/catalogue/manifest.json`. |
| `C/media-config.json` | **Current display input.** Supplies thumbnail settings for Catalogue Work rows and Gallery Media View. It carries no search terms. |
| `working/generated/collections/catalogue/documents/by-id/<work_id>.json` under `$DOTLINEFORM_DOCS_BASE_DIR` and public `site/assets/data/docs/catalogue/by-id/<work_id>.json` | **Current selection input.** Read when opening a Work or showing its Media View. The report filters the manifest without reading these documents. |
| `C/galleries/index/<gallery_id>.json` | **Current selection input.** Media View reads the chosen Gallery's title and member Work IDs/titles. Search uses the compact projection below. |
| `C/galleries/galleries_index.json`, `C/works/works_index.json`, `C/series-galleries-index.json` | **Existing Catalogue outputs outside this report's search path.** The compact Gallery index serves authoring target discovery. The compact Work index serves Work lookup and maintenance. The Series–Gallery index supplies explicit Series relationships for Work adoption. The proposal preserves these contracts. |
| `C/galleries/report-search.json` | **One additional search input.** The `catalogue_gallery_report_search_v1` payload has `galleries` mapping exact Gallery IDs to titles and `gallery_ids_by_work` mapping exact Work IDs to direct Gallery ID arrays. Empty membership rows are omitted and empty Gallery definitions remain searchable by title. Studio supplies the IDs as strings. |

The browser loads `report-search.json` once when the Catalogue report first needs Gallery search, prepares Gallery title keys once and retains the input through queries and paging. The query reuses the existing filtered Work rows to count memberships through direct ID lookups, orders the Gallery rows and combines them with the Work results. Page changes slice the prepared list. The existing report reload boundary revalidates the data when needed. Work browsing can continue while the Gallery payload loads. [Collection browsing](../../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) · [Collection report](../../../docs-viewer/runtime/js/shared/docs-collection-report.js).

Manage needs one narrow read of the saved output through its configured Catalogue provider. Public reads the same prepared file through the public route configuration. Gallery click loads the existing exact member record and thumbnail inputs. The workspace-wide Docs Viewer Search index is separate.

## Studio Refresh And Publication

1. **Select exact changes at Save.** Select the new shared output when a Gallery is created, renamed or deleted, or when a Work's direct membership changes, including Work creation/deletion with memberships. Reuse the existing Gallery identity and `gallery_member_works` selections. Gallery Delete already knows the former direct members. Carry those exact Work IDs into the member selection so Refresh can update their rows alongside deleting the Gallery definition. Work title changes flow through the Work manifest. Series-only association and media changes leave this projection untouched.
2. **Merge in Refresh.** Reuse the loaded canonical definitions and memberships from `galleries.json` and `galleries-by-work.json`. Resolve those dependencies only for the selected rows. Read the saved projection once, upsert or remove the selected Gallery definitions and replace the membership arrays for selected Works from final saved state. Remove deleted Works and rows with no remaining memberships. Preserve unselected rows and skip unchanged writes. The selection comes from Save, with one shared output identity in the existing queue.
3. **Seed and distribute.** Agree a one-time seed from a completed Studio baseline using the same projector. Register the new relative path in the Catalogue artifact inventory, and have Refresh hand the completed file to the existing shared publication queue. Publish transfers it through Preview to the tracked public Catalogue root. It has its own shared-output handoff. Regenerate still owns any independently selected Work document changes. Project and deploy the public reader with the published search file available.

[Studio shared selections](../../../studio/services/catalogue/catalogue_shared_changes.py) · [Refresh owner](../../../studio/services/catalogue/catalogue_refresh_service.py) · [Catalogue artifact inventory](../../../docs-viewer/config/workspace/catalogue-artifacts.json).

The approved Working seed ran on 2026-11-09 using `python3 studio/services/catalogue/catalogue_json_build.py --gallery-report-search --write` with the configured project interpreter. It wrote one file containing 192 Gallery titles and 5,173 Work membership rows and selected it for Publish. After Publish, Working, Preview and `site/assets/data/catalogue/galleries/report-search.json` matched byte for byte. The Docs and Catalogue publication queues were empty.

## Delivery Steps

- [x] **Readiness and implementation.** The approved slice uses one shared artifact, exact definition and membership selections, and one paginated list. Studio Refresh and the Working and public readers are wired, with Work controls and Media View Back using their existing owners.
- [x] **Code review and static checks.** The [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) traced Gallery create, rename and delete, Work membership changes, unrelated saves and selected transfer. Gallery Delete carries its known former direct members. Gallery-record maintenance preserves those candidates while search output is pending. Refresh reads one saved file and skips unchanged writes. The browser retains the prepared data, counts over Work matches, and fetches an exact Gallery record on activation. Retained checks cover configured output confinement, the browser schema boundary and current document/media selection. Focused Python and JavaScript lint, CLI argument loading, whitespace, public projection and site validation passed.
- [x] **Working seed.** Generated the report search file and verified the selected publication handoff.
- [x] **Local acceptance and Publish.** The user reported the result looked good after Publish. Individual browser scenarios and request traces were not itemised. Verified the selected file and drained publication queues.
- [x] **Public release.** Pushed `1702ef2a37` to `origin/main`. The user ran Deploy Public and confirmed the result on the public site.
