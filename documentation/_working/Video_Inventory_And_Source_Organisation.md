---
draft: false
doc_id: d-20261122-131045-1f936c
title: Video Inventory And Source Organisation
added_date: "2026-11-22 13:10:45"
last_updated: "2026-11-22"
summary: Reconcile Catalogue film Works, local video sources and published cuts, and agree a consistent Projects layout.
ui_status: proposed
parent_id: d-20261118-235100-64ad2e
---
# Video Inventory And Source Organisation

Review the videos project by project before choosing cuts for the Catalogue. Establish which local files match the Vimeo and YouTube uploads, which local sources are still missing or unconfirmed, and where to keep confirmed files in Projects. The inventory supplies source sizes and runtimes for a wider R2 rollout. The completed HLS pilot established the first source for Catalogue video. [Catalogue HLS Video Pilot](../deliveries/Catalogue_HLS_Video_Pilot.md)

## Where The Inventory Lives

| What you are reviewing | Where it belongs |
| --- | --- |
| **Source footage, exports and extracts** | Keep the files in their project folders. Start the project note with a short description of the source footage, soundtracks, finished exports and extracts that are available. |
| **Which file matches which cut or upload** | Use the existing project Markdown note, such as `_by the river.md`, as the working record. Keep the candidate paths, Vimeo and YouTube URLs, confirmed matches, missing sources, cut selection decisions and next actions here. Record a Work ID once the cut is registered. |
| **What you have registered for readers** | Use `works.json` for each registered cut's Work ID, Series, Medium, Duration and visitor-facing Links. The Work's selected Catalogue image supplies its poster. Use the optional Projects-relative video source to register the selected local file once confirmed. [Catalogue source model](../reference/Catalogue_Source_Model.md#metadata-and-ordering) · [First film and poster](../deliveries/Catalogue_R2_Video_Delivery.md#film-and-poster) |

When you register a distinct cut, give it its own Work ID. A short cut and a long cut get separate Works, with their own durations, selected sources and matching platform links. Different exports of the same edit are candidates for the same Work. Use ordinary Gallery membership to group the cuts for readers, and keep them in the same Series where appropriate. [Catalogue identities and relationships](../reference/Catalogue_Source_Model.md#relationships-and-identity) · [Gallery editing](../reference/Catalogue_Work_Editor.md)

## Table In The Project Note

Keep the note in the project root using the existing `_<project folder name>.md` convention. For example, `by the river/` contains `_by the river.md`. The underscore makes the note easy to spot in Finder when sorted by name. The note keeps its location as video and soundtrack files move between subfolders. Update the relative paths in its table when files move.

After the source description, use one row per cut under review. Use file names relative to the project folder, including subfolders where needed. Record the video file's dimensions in pixels as width × height, for example `1280 × 720`. Fill the soundtrack column when a separate source audio file exists. Add the Work ID when the cut is registered and link it to the exact dotlineform Catalogue page where available. List the Vimeo and YouTube URLs for that cut in the same cell. Leave unknown fields blank and record the open question in the notes.

```md
| Video file | Duration | Dimensions | Soundtrack file | Title | Work ID | External URLs | Publish notes | Source notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | |
```

- **Publish notes** record what readers can actually see or play. For example, “Catalogue Work shows the poster and links to Vimeo” or “Video plays on dotlineform and YouTube.”
- **Source notes** record where the file came from, whether it matches the published cut, and any work still needed. For example, “2011 HandBrake export, confirmed match to Vimeo,” “Vimeo-generated download, local original unconfirmed” or “Needs content review and conversion for playback.” Keep alternate candidate files in the source description until you choose one for the row.

## Review In Manage

Start with the current **Projects** report in Docs Viewer Manage. It associates project folders with saved Catalogue data and links to each folder. Follow the folder link and open the underscored note in the project root. Use its table to match exact video files to Works. If the first pass shows that a video-specific report would save work, it could list candidate files, compare them with registered video sources and link directly to the project note. [Reports and inspection](../reference/Reports.md#inspection-and-consumption-boundaries)

Use **Catalogue Medium** to find registered film Works and **Work Links** to review saved platform URLs. Confirm external publication against the Vimeo and YouTube libraries during reconciliation. For dotlineform publication, check the deployed Catalogue page when the release status matters. Keep any outstanding source or publication checks in the project note. [Existing reports](../reference/Reports.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Reconcile Local Files And Published Cuts

1. Open the project folder from Manage, then open its note and review the local video candidates alongside the Vimeo and YouTube libraries. Include uploads that have no Catalogue link and local films that have no known upload. Use the note to capture questions about identity, source and which cuts to present.
2. Match by film and cut. Use titles, durations and variant notes to narrow the candidates, then compare the picture and soundtrack when the match is ambiguous. Confirm the best available local source for each cut, including a finished export where it is the surviving copy. Update the Work for a cut already registered, or create its Work when you decide to register it. A cut published on both platforms can carry both links on its Work.
3. For a published cut with no confirmed local source, record the open question and platform URLs in the project note. If the cut is registered, keep its reader-facing platform links on the Work and leave the local video source blank. Check the platform's download options and record whether a recovered file is the source upload or a platform-generated copy when known. [Vimeo source file storage](https://help.vimeo.com/hc/en-us/articles/46427284891537-Store-your-source-files-on-Vimeo)

Start with these examples to settle how we identify distinct cuts and choose a source. The durations below come from saved project notes and Catalogue metadata.

| Project | First review |
| --- | --- |
| **nerve forms** | Identify the finished cuts among the exports and extracts. Work `00581` describes the print. Work `00008`, the book *nerve*, has a Vimeo link labelled *nerve forms*. |
| **by the river** | The project note records separate **6:43** and **6:52** cuts with separate Vimeo links. Confirm which cut Work `05058` represents, since it records **6:52** and links to the video labelled **6:43**. Register the other cut as its own Work if you choose to include it in the Catalogue, then group them in a Gallery. |
| **a world of non-linearity** | The project note lists a local **33:20** file labelled *original* and a **10:15** Vimeo cut. Confirm whether a matching local file exists for the cut linked by Work `04968`. |

## Proposed Projects Layout

Start with the convention already used in *by the river*. Use `<project>/video/` for finished copies and `<project>/source video/` for source footage where it exists. Keep filenames that distinguish meaningful cuts. Confirm the file-to-Work matches before agreeing moves or renames, then update the affected Catalogue paths to point to the selected files. [Configured Work media roots](../reference/Catalogue_Media_Pipeline_Config.md#work-media-sources)

## Completion Gates

- [ ] Reconcile the first three projects using the current Projects report and the project-note table. Agree the folder and naming convention and decide whether a video-specific report would help before broadening the review.
- [ ] Review the remaining local projects and both platform libraries. Keep cut decisions and unresolved sources in the project notes, save confirmed sources and reader-facing links for registered cuts on their own Works, and group related cuts with a Gallery.
- [ ] Measure the confirmed local source file sizes directly when totalling the inventory. Use the total bytes, combined runtime of the selected cuts and unresolved source count to plan the wider R2 rollout. [Measured pilot estimate](../deliveries/Catalogue_HLS_Video_Pilot.md#video-inventory-and-hosting-estimates)
