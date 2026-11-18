---
draft: false
doc_id: d-20260904-173415-b28651
title: Catalogue Archive
added_date: "2026-09-04 17:34:15"
last_updated: "2026-11-18"
summary: Consolidated legacy Catalogue rationale, freeze/copy evidence and the outstanding archive-retention decision.
parent_id: d-20260613-115624-3d377c
---
# Catalogue Archive

Consolidated history of the legacy Catalogue freeze and its reader design. The snapshot remains in the tracked `site/archive/` deployment artifact. **Whether to keep it is an open follow-on decision**, recorded in the [tracker](../_working/Review_Catalogue_Archive_Retention.md). This documentation consolidation changes no site assets or remote objects.

The active Catalogue uses Docs Viewer at `/` and the current [Catalogue workflow](../reference/Catalogue_Save_And_Refresh.md). The pre-freeze route model below is historical. Original versions of UAC 1, Public Catalogue Design, Public Route Model, Public Catalogue Data Flow, Catalogue Search and Catalogue Search Policy remain in Git at `c76f6608ef` under `documentation/deliveries/`.

## Site Snapshot

The clean pre-archive revision is `519c49bbaa43ddfcdddc2521ef95bf2c4eccf95f`. On 4 September 2026, Catalogue HTML, browser modules, data, Search/Recent and thumbnails moved beneath `site/archive/`. Shared shell dependencies were copied to keep the snapshot independent of later active-site edits. Studio canonical source was retained; no separate canonical snapshot, redirect table, schema adapter or synchronized archive build was introduced.

UAC 1 temporarily made Analysis the home and exposed the archive through a footer. Later changes supersede that navigation: on 8 October About and site footers were removed, including archive footers; on 15 October the active reader moved from `/analysis/` to `/` without an alias. Archive internal navigation remains independent. Old route/stylesheet paths in the original records identify their pre-freeze revision.

## Frozen Reader And Route Rationale

| Frozen route | Data and behaviour |
| --- | --- |
| `/archive/` and `/archive/series/` | Series-led Works home; lean Series list, then exact selected Series and canonically ordered lightweight Work members |
| `/archive/works/?work=<id>` | Exact rich Work payload and relevant Series context; bare Works returns to Series |
| `/archive/work-details/?detail=<uid>` | Parent Work payload with nested sections/details; no global detail index |
| `/archive/recent/` | Frozen publication snapshots with owned destination links |
| `/archive/search/` | Frozen flat Work/Series Search index and browser policy |

Works were the primary media objects, Series supplied grouping/order, and details remained parts of a Work. A single-Work Series could open that Work directly. List/grid and year/title sorting changed presentation rather than canonical meaning. Rich Work views combined media, compact metadata, downloads/links, sections and optional prose. The restrained light/dark shell and semantic controls kept attention on artwork.

Shared URL helpers owned construction/parsing. Query values selected records and carried useful context: `series`, `work`, `detail`, `from`, `series_page`, `details_section` and `details_page`. Explicit links supplied required returns; browser history was supplementary. View/page preferences could persist locally. The old record identifies one unresolved gap: Series pagination initialized from local storage rather than the supplied `series_page`, so that query was not an effective restoration promise.

The lean Series index omitted full membership; exact Series owned order. Work payloads nested detail/section context instead of duplicating a flat Works or Details aggregate. Build-time publication selected public records. A historical `documents: [{url, title}]` envelope came from accepted document locations; those writers were later retired and are not awaiting resumption. Catalogue Moment records did not create an independent Moments route or Docs scope.

Global shell CSS and Catalogue components had separate intended owners, but older route-specific rules remained mixed into the global stylesheet. Repeated static shell markup required coordinated changes. Links represented destinations, buttons represented local view state, controls exposed accessible labels/pressed state, and image text came from titles. Responsive fit, contrast and media presentation remained manual concerns.

## Frozen Search

[Saved policy](../../site/archive/assets/data/search/policy.json), [index](../../site/archive/assets/data/search/catalogue/index.json) and [browser runtime](../../site/archive/assets/js/search/catalogue-search-runtime.js) belong to the snapshot. Search loads these saved files; it is not rebuilt from current canonical data.

The former builder read published Works/Series and a dependency registry declaring emitted-field provenance. Its `additive_only` policy could merge new records; edits/deletes required a full build. Registry terms such as `record_update`/`full_rebuild` described that retired builder, not current Docs Search.

The browser required every query token, favoured exact/prefix identity/title matches, then used structured Series/Medium context and broad `search_text` fallback. It filtered kinds, loaded fixed batches and offered optional timing instrumentation. It was not a full-text body index. The policy owned timing/thresholds, batches, labels, scopes and the index URL. JavaScript fallback defaults duplicated policy values; normalization also retained unused `tagLabels`. Similar Docs Search code was not shared. These explain the old design; [current discovery](../reference/Reader_Discovery_And_Return.md) has its own owners.

## R2 Copy

The same-bucket copy used portable rclone v1.75.0 under ignored `var/tools/rclone/`, with credentials supplied locally and no values stored in the record. Both dry runs passed against an empty destination.

| Original prefix | Copied destination | Recorded result |
| --- | --- | --- |
| `works/` | `archive/catalogue/works/` | 5,809 objects, 6m34s |
| `work_details/` | `archive/catalogue/work_details/` | 8,082 objects, 10m34s |

The historical commands were:

```bash
rclone copy "uac:${R2_BUCKET}/works/" "uac:${R2_BUCKET}/archive/catalogue/works/" --metadata --transfers 8
rclone copy "uac:${R2_BUCKET}/work_details/" "uac:${R2_BUCKET}/archive/catalogue/work_details/" --metadata --transfers 8
```

All 13,891 objects (1,749,367,336 bytes), including unlinked objects, copied server-side without reported errors in about 17m08s. HTTP metadata and original objects were preserved. Docs/home media were outside the copy. Ordinary logs/exit results lived under ignored `var/uac-1/`; no object manifest or separate checksum audit was created.

Archived image/download bases were changed to `https://media.dotlineform.com/archive/catalogue/`; local thumbnails stayed in the snapshot. The current batch did not contact or inventory that remote storage.

## Acceptance And Supersession

The initial pause was committed as `41a671abc4e712ad2478895c6c0ca1e2f8b593ac`. It exited Docs Catalogue planning/write follow-through before relocated public inputs were read, preserving independent Docs work. Forty-four focused Python cases, changed-source lint and whitespace checks were recorded for the pause/independent-operation boundaries. Snapshot preparation also reported projection/site checks and source review. Those scope-era selections are historical evidence, not a current test profile.

The user accepted local preview and, on 4 September, confirmed that Work images, detail images and downloads opened from the copied prefix. Examples were `works/img/01941-primary-1600.webp?v=1`, `work_details/img/00523-015-primary-1600.webp?v=1` and `works/files/00008-nerve.pdf`. Simplified active navigation was accepted and committed as `824254d6c`. Final review through that commit found no blocking issue. UAC 1 closed on this accepted local result; it did not establish public deployment.

The accompanying import cleanup removed 24 retry blocks across twelve Catalogue/media modules while preserving primary imports/bootstrap. Fresh-process imports, five command-help checks, targeted missing-dependency checks, 28 existing publisher/lookup/generation tests, lint and whitespace passed. No new permanent tests or live build/media/deployment operation was recorded for that cleanup.

The Catalogue pause and document-location writers were subsequently retired through the new ownership/cutover work. Current Save → Refresh → Regenerate → Publish does not regenerate this snapshot. [Retired locations](Retire_Public_Document_Locations.md) · [Current source boundaries](../reference/Source_Tree_Ownership.md) · [Separate backup proposal](../_working/R2_Workspace_Backups.md)

## Retention Decision Boundary

Keeping public archive routes, keeping the tracked snapshot for Git-only recovery, and retaining remote copied media are separate choices. The [follow-on](../_working/Review_Catalogue_Archive_Retention.md) must settle them and the remaining validation/link dependencies. [Site validation configuration](../../site-tools/config/site-tools.json) still requires archive assets. Consolidating the documentation does not authorize deleting those files, changing required-file inventory, removing remote prefixes or deploying a withdrawal.
