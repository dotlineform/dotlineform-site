---
draft: false
doc_id: d-20261126-124843-51565b
title: Catalogue R2 Video Delivery
added_date: "2026-11-26 12:48:43"
last_updated: "2026-11-26"
summary: Published and accepted the first Catalogue film with inline R2 playback and in-place package replacement.
ui_status: done
parent_id: d-20260419-000000-d2e47b
---
# Catalogue R2 Video Delivery

*Balance machine 1* went live on 26 November 2026 as the first Catalogue film with inline playback from R2. The [completed HLS pilot](Catalogue_HLS_Video_Pilot.md) supplies the encoding and playback evidence. Its live page, poster and R2 package are available for comparison.

## Film And Poster

- Studio saved *balance machine 1* as film Work `05248` in Series `150` with a duration of 4:09 and the project note's year display `2003, 2011`. Work `04813` identifies the same-title digital C-type print. The film and related prints can be grouped through existing Catalogue relationships. [Catalogue identities and metadata](../reference/Catalogue_Source_Model.md#relationships-and-identity)
- The film uses `projects/balance machine/balance machine 1.m4v` beneath `$DOTLINEFORM_PROJECTS_BASE_DIR`, with its embedded stereo soundtrack and accepted original edge marks. Its selected image is `balance machine 1 poster.jpg` in the same project. The existing image workflow supplies the poster and thumbnail, so a poster edit is independent of the video encode. [Work media authoring](../reference/Catalogue_Save_And_Refresh.md#work-media-authoring)

## Prepared Package Identity And Replacement

The film's Work ID identifies one HLS package containing both playback renditions. Its public master playlist is `works/video/<work-id>/master.m3u8` on the configured R2 media host. Successful preparation selects a complete package for that Work. Publishing a replacement writes its files to the same Work paths during the normal per-Work media transfer. Files a replacement playlist no longer references follow the existing manual cleanup policy for unreferenced Work media. Revisit uninterrupted playback during replacement if site readership warrants it. [Work media publication](../reference/Catalogue_Save_And_Refresh.md#storage-and-selection)

## Delivered Workflow

**Save → Prepare video → Refresh Catalogue → Regenerate → Publish** carries the selected original, completed package and playback reference through the normal Work publication workflow. Studio shows elapsed time during preparation. The Catalogue Entry plays inline using the selected poster and the browser's controls. [Current Work media workflow](../reference/Catalogue_Save_And_Refresh.md#prepare-video) · [Catalogue Entry token](../reference/Document_And_Catalogue_References.md#build-and-runtime-resolution)

## Completion

- [x] The author confirmed the elapsed-time display during **Prepare video**. Local service evidence confirms the preparation and Refresh handoff.
- [x] The film is registered and the approved poster and selected video reach the correct Work through Studio, Working, Publish and the deployed Catalogue.
- [x] A second preparation and Publish replaced files at the same Work playlist URL.
- [x] The author confirmed inline playback in Manage, site-preview and Public, with Safari desktop and iPhone coverage.
- [x] The author confirmed that seeking works in the inline player.
- [x] The author confirmed that print `04813` still displays its image normally.

## Publication And Acceptance

Studio Save, Prepare video and Refresh Catalogue completed for Work `05248`. Regenerate created its Catalogue document and queued the poster and all 89 HLS files. The generated Work references `05248/master.m3u8`. The local media route returned the master, rendition playlist, initialization file and segment with the expected content types. FFmpeg decoded both video and audio renditions to the end through that route.

Publish completed on 26 November 2026. Work `05248` cleared from the queue, and the public payload carries its own playlist reference. Site content backup `10cdc52bb6` recorded the publication, and `8bfef7187e` recorded the delivery code. The author reported deployment and confirmed playback in Manage, site-preview and Public on desktop Safari and iPhone.

The author confirmed the timer during a second preparation from the same original. The repeat Publish rewrote 83 segments and the master playlist in Preview. The public master and a sampled segment had modification times from that Publish at their original R2 paths. The committed Work payload stayed byte-identical.

Prepare resolves only the chosen Projects source and records the files from its fresh encode directory. Refresh and Regenerate carry those exact files through the existing queues. Publish uses the existing confined media paths and selected-transfer verification. Replacement adds no R2 inventory scan or automatic orphan cleanup. Poster-only and metadata-only edits keep their existing preparation path.

## Live Review

Record broader browser coverage, audio and motion observations, and bandwidth drop and recovery during live use as devices and conditions are available. Use the retained pilot stream for comparison when diagnosing playback.

Use the [video inventory](../_working/Video_Inventory_And_Source_Organisation.md) to select the next cuts and estimate package storage before expanding live use. The measured pilot used about 22 MB per minute across both renditions. [Catalogue Video In Media View](Catalogue_Video_In_Media_View.md) records the accepted playback in the selected Work pane and the decisions for a later inline player in ordinary documents. Revisit controls beyond the browser's standard controls as live use informs them.

## Video Segment Cleanup Follow-on

The current R2 orphan report covers document-owned media. After a successful replacement Publish, manually compare the R2 keys under the exact `works/video/<work-id>/` prefix with the published master playlist, its rendition playlists and their referenced segments and initialization files. Review the extra keys before deleting them. [R2 orphan report scope](../reference/Media_And_Asset_Handling.md#r2-orphan-report)

If replacements become frequent, consider a read-only report for a selected Work that lists the exact unused keys for manual review.
