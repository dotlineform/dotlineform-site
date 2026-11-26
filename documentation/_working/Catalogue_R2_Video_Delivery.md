---
draft: false
doc_id: d-20261126-124843-51565b
title: Catalogue R2 Video Delivery
added_date: "2026-11-26 12:48:43"
last_updated: "2026-11-26"
summary: Register the first film Work and deliver its inline video through the Catalogue publication workflow and R2.
ui_status: active
parent_id: d-20261118-235100-64ad2e
---
# Catalogue R2 Video Delivery

Deliver *balance machine 1* as the first Catalogue film with inline playback. R2 is the selected host. The [completed HLS pilot](../deliveries/Catalogue_HLS_Video_Pilot.md) supplies the encoding and playback evidence. Its live page, poster and R2 package are available for comparison during this delivery.

## Film And Poster

- Studio saved *balance machine 1* as film Work `05248` in Series `150` with a duration of 4:09 and the project note's year display `2003, 2011`. Work `04813` identifies the same-title digital C-type print. The film and related prints can be grouped through existing Catalogue relationships. [Catalogue identities and metadata](../reference/Catalogue_Source_Model.md#relationships-and-identity)
- Use `projects/balance machine/balance machine 1.m4v` beneath `$DOTLINEFORM_PROJECTS_BASE_DIR`, with its embedded stereo soundtrack and accepted original edge marks. Select `balance machine 1 poster.jpg` in the same project using **Choose image**. The existing image workflow supplies the poster and thumbnail, so a poster edit is independent of the video encode. [Work media authoring](../reference/Catalogue_Save_And_Refresh.md#work-media-authoring)

## Prepared Package Identity And Replacement

The film's Work ID identifies one HLS package containing both playback renditions. Its public master playlist is `works/video/<work-id>/master.m3u8` on the configured R2 media host. Successful preparation selects a complete package for that Work. Publishing a replacement writes its files to the same Work paths during the normal per-Work media transfer. Files a replacement playlist no longer references follow the existing manual cleanup policy for unreferenced Work media. Revisit uninterrupted playback during replacement if site readership warrants it. [Work media publication](../reference/Catalogue_Save_And_Refresh.md#storage-and-selection)

## Delivery Steps

1. Let the author choose the original video in Studio and **Save** its selection on the film Work alongside the poster. The browser owns the selection and draft, and the local service persists the saved choices using the Projects-relative `video_source` field. [Work media roots](../reference/Catalogue_Media_Pipeline_Config.md#work-media-sources)
2. Add **Prepare video** for the selected saved Work. The editor shows **Preparing video** and the elapsed time while it waits, then reports the duration and that the package is ready, or reports the phase that failed. The local service resolves the saved video through the existing Projects resolver, runs FFmpeg and stages the complete package for that Work on success. The pilot encode took about 62 seconds.
3. Extend the exact Work handoff. **Refresh Catalogue** carries the selected prepared package into Working. **Regenerate** adopts the playback reference into that Work's Catalogue document and queues its selected video artifacts. **Publish** transfers the package with the Work's document and poster effects, using the existing R2 host and the content types proven by the pilot. [Catalogue workflow and publication](../reference/Catalogue_Save_And_Refresh.md#current-workflow) · [Per-Work Publish](../reference/Catalogue_Save_And_Refresh.md#per-work-publish)
4. Play the published film inline with the browser's video controls, the selected poster and adaptive HLS. Use the Catalogue Work's prepared playback reference and the existing identity-only Catalogue Entry token. The public player follows the normal code projection and Pages workflow. [Catalogue Entry token](../reference/Document_And_Catalogue_References.md#build-and-runtime-resolution) · [Public runtime projection](../development/Verification.md#docs-viewer-site-code-projection)

## Completion

- [ ] **Prepare video** shows the preparation phase and elapsed time for the selected saved film. **Refresh Catalogue** can hand off the package once preparation completes.
- [ ] The film is registered and the approved poster and selected video reach the correct Work through Studio, Working, Publish and the deployed Catalogue.
- [ ] A deliberate replacement publishes the new package at the same Work playlist URL.
- [ ] Verify inline start and seeking on the available desktop and iPhone paths, and confirm that a still Work continues to render through its normal image path.

## Local Evidence And Next Action

Studio Save, Prepare video and Refresh Catalogue completed for Work `05248`. Regenerate created its Catalogue document and queued the poster and all 89 HLS files. The generated Work references `05248/master.m3u8`. The local media route returned the master, rendition playlist, initialization file and segment with the expected content types. FFmpeg decoded both video and audio renditions to the end through that route. The next acceptance steps are Studio elapsed-time display and inline playback in Manage, followed by Publish, Deploy Public and the desktop and iPhone checks above.

Prepare resolves only the chosen Projects source and records the files from its fresh encode directory. Refresh and Regenerate carry those exact files through the existing queues. Publish uses the existing confined media paths and selected-transfer verification. Replacement adds no R2 inventory scan or automatic orphan cleanup. Poster-only and metadata-only edits keep their existing preparation path.

## Live Review

Record broader browser coverage, audio and motion observations, and bandwidth drop and recovery during live use as devices and conditions are available. Use the retained pilot stream for comparison when diagnosing playback.

Use the [video inventory](Video_Inventory_And_Source_Organisation.md) to select the next cuts and estimate package storage before expanding live use. The measured pilot used about 22 MB per minute across both renditions. Media View playback and player controls beyond the browser's standard controls are candidates for a later delivery as live use informs them.

## Video Segment Cleanup Follow-on

The current R2 orphan report covers document-owned media. After a successful replacement Publish, manually compare the R2 keys under the exact `works/video/<work-id>/` prefix with the published master playlist, its rendition playlists and their referenced segments and initialization files. Review the extra keys before deleting them. [R2 orphan report scope](../reference/Media_And_Asset_Handling.md#r2-orphan-report)

If replacements become frequent, consider a read-only report for a selected Work that lists the exact unused keys for manual review.
