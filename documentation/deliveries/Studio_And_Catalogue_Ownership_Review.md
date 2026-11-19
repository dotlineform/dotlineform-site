---
draft: false
doc_id: d-20261118-191221-27e940
title: Studio And Catalogue Ownership Review
added_date: "2026-11-18 19:12:21"
last_updated: "2026-11-18"
summary: Preserved Catalogue source migrations, Studio retirement evidence, thumbnail diagnosis and report acceptance limits.
parent_id: d-20261118-151521-a0f9c3
---
# Studio and Catalogue ownership review

The 2026-11-18 review consolidated sixteen Studio pages into five Reference owners for the app, source model, services, media pipeline and private Works report. It corrected stale revision, route, staging and validation claims against current code. The original pages remain in Git at `c76f6608ef` under `documentation/studio/`. [Current implementation](../reference/Catalogue_Services.md) · [Design](../design/Studio_And_Catalogue_Ownership.md)

## Source migrations

The completed Gallery conversion allocated new Work IDs in exact Detail UID order and section Gallery IDs in exact section order. Its reviewed plan recorded source hashes and local/R2 media mappings. The converter was retired after cutover. Converted records are ordinary Works, with their membership expressed through the current canonical stores. [Detail migration and transaction evidence](Catalogue_Per_Work_Detail_Source.md)

On 2026-10-07, canonical cleanup removed `artist` and `provenance` from 4,618 Works, including the sole populated provenance value. The Medium migration preserved corrected descriptions in `medium` and retired the separate category, introducing generated `work_record_v10`. Version 11 later removed the always-empty generated `documents` array. On 2026-10-12, cleanup removed 2,678 `links: null` fields while preserving actual resources and other source values. [Current fields and resource representation](../reference/Catalogue_Source_Model.md#metadata-and-ordering)

## Studio retirement evidence

The 2026-10-11 frontend and text cleanups removed unused modules, obsolete preview/readiness mounts and text registries. Focused lint, syntax, static readiness and import/export review passed. The shared text cleanup projected three changed public modules and passed projection/site validation. Browser boot, live Save/Refresh and broad test profiles were outside that evidence. The former frontend, text and server-config test scopes are available in `documentation/_working/testing/Testing.md` at the recovery revision. [Site test retirement](Review_Test_Policy_And_Checks.md#recovery)

Persisted lookup retirement removed the obsolete `test_metadata_only_save_refreshes_revision_and_reassignment_refreshes_both_series` case, its deleted exporter and related compile/profile entries. The approved cleanup used static/reference review. The remaining lookup builders serve live canonical reads. The former Catalogue service test scope is available in the same historical Testing record.

The 2026-10-24 Series creation/URL correction had focused lint and source review. Creating a Series preserved the Work draft, while committed browsing choices updated the URL. Reload, definition operations and unsaved prompts remained manual evidence gaps. [Current Series behavior](../reference/Studio.md#browser-responsibility)

## Thumbnail colour diagnosis

On 2026-10-25, Work `02014`, an sRGB 3024×3024 JPEG, reproduced a green cast in the 96 px thumbnail while its larger primary remained correct. A BGRA intermediate showed the tint before WebP encoding. Selecting YUV420 corrected temporary output. The final `yuv420p|yuva420p` choice preserved the alpha-capable path and matched the reviewed YUV420 results for that opaque source. Both production thumbnail functions passed direct conversion diagnostics, lint and compilation. Other source formats, transparency and the full Save/Refresh interaction remained unverified. [Current conversion and regeneration](../reference/Catalogue_Media_Pipeline_Config.md#thumbnail-colour-conversion)

## Catalogue Works report

The report's v3 metadata conversion used the complete private generator and direct saved-reader/browser-data diagnostics, preserving empty queues and lifecycle timestamps. The later local transport change exercised the production dispatcher against saved metadata. The Source image change regenerated private metadata and checked literal path composition and five/seven-column TSV through the production data owner.

Recorded user review covers Work title Save, expanded presentation, sorting, links and improved search responsiveness. Pagination toggle, detailed clipboard/resize/restore behavior and failure scenarios retain manual evidence gaps. The retired site suite included a contract test that asserted canonical API reads and a retired navigation fragment. [Current report](../reference/Catalogue_Works.md) · [Site test retirement](Review_Test_Policy_And_Checks.md)

## Current verification

This batch traced browser and HTTP dispatch, canonical stores, Save media/version completion, queue dependency selection, Refresh readiness and the returned editor state. It checked Markdown paths, anchors, identities and whitespace. Live Save/Refresh, browser interaction and runtime tests remain outside this documentation review.
