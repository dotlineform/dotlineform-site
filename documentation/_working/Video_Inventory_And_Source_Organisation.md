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

Review the videos project by project before choosing cuts for the Catalogue. Establish which local files match the Vimeo and YouTube uploads, which local sources are still missing or unconfirmed, and where to keep confirmed files in Projects. The inventory supplies source sizes and runtimes for hosting estimates. The manual HLS pilot can proceed with its verified source. [Catalogue HLS Video Pilot](Catalogue_HLS_Video_Pilot.md)

## Where The Inventory Lives

| What you are reviewing | Where it belongs |
| --- | --- |
| **Source footage, exports and extracts** | Keep the files in their project folders. The proposed video review in Manage lists candidate paths, durations, resolutions and sizes for inspection. |
| **Which file matches which cut or upload** | Use the existing project Markdown note, such as `_by the river.md`, as the working record. Keep the candidate paths, Vimeo and YouTube URLs, confirmed matches, missing sources, cut selection decisions and next actions here. Record a Work ID once the cut is registered. |
| **What you have registered for readers** | Use `works.json` for each registered cut's Work ID, Series, Medium, Duration and visitor-facing Links. The Work's selected Catalogue image supplies its poster. Use the proposed optional project-relative video source to register the selected local file once confirmed. [Catalogue source model](../reference/Catalogue_Source_Model.md#metadata-and-ordering) · [Film and still records](Catalogue_HLS_Video_Pilot.md#film-and-still-work-records) |

When you register a distinct cut, give it its own Work ID. A short cut and a long cut get separate Works, with their own durations, selected sources and matching platform links. Different exports of the same edit are candidates for the same Work. Use ordinary Gallery membership to group the cuts for readers, and keep them in the same Series where appropriate. [Catalogue identities and relationships](../reference/Catalogue_Source_Model.md#relationships-and-identity) · [Gallery editing](../reference/Catalogue_Work_Editor.md)

## Review In Manage

Start in the **Projects** report or a video-specific report built from the same project and Catalogue data. The proposed review view would show what exists in source folders, which cuts have been registered as Works and where their publication has been confirmed. It would distinguish a missing file at a saved source path from a Work whose local source is still unconfirmed. Open the project's Markdown note from that view to read and update the detailed decisions and next actions. The current Projects report joins project folders to saved Catalogue inputs. Listing candidate video files and opening the project note are proposed extensions. [Reports and inspection](../reference/Reports.md#inspection-and-consumption-boundaries)

Use **Catalogue Medium** to find registered film Works and **Work Links** to review saved platform URLs. Confirm external publication against the Vimeo and YouTube libraries during reconciliation. For dotlineform publication, check the deployed Catalogue page when the release status matters. Keep any outstanding source or publication checks in the project note. [Existing reports](../reference/Reports.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Reconcile Local Files And Published Cuts

1. Open the project note from Manage and review the local video candidates alongside the Vimeo and YouTube libraries. Include uploads that have no Catalogue link and local films that have no known upload. Use the note to capture questions about identity, source and which cuts to present.
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

- [ ] Reconcile the first three projects and agree the folder and naming convention before broadening the review. Confirm where the video review belongs in Manage and how it opens the project notes.
- [ ] Review the remaining local projects and both platform libraries. Keep cut decisions and unresolved sources in the project notes, save confirmed sources and reader-facing links for registered cuts on their own Works, and group related cuts with a Gallery.
- [ ] Total the bytes of confirmed local sources and the runtime of distinct cuts being considered for hosting. Carry those totals and the unresolved source count into the hosting decision. [Pilot hosting estimates](Catalogue_HLS_Video_Pilot.md#video-inventory-and-hosting-estimates)
