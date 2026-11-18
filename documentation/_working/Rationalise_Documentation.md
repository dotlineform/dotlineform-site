---
draft: false
doc_id: d-20261118-151521-a0f9c3
title: Rationalise Documentation
added_date: "2026-11-18 15:15:21"
last_updated: "2026-11-18"
summary: Consolidate Studio documentation by the questions it answers and record progress by review batch.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Rationalise Documentation

Make the repository docs quicker to use during development. Give current behaviour one maintained home, compile reusable design reasoning by domain, and keep completed delivery records when they preserve useful evidence. Review the remaining `documentation/studio/` material in batches. A batch is small enough to trace from a real question to the code or record that answers it. File count and word count help find overlap. Each retained passage should answer a question a developer could reasonably ask.

## What the documentation is for

> why does media view works page not have related links?

| Question behind the question | Where to look | What the docs should supply |
| --- | --- | --- |
| Has something broken, or have I missed a step? | `documentation/reference/` | What a Work in Media View currently shows, where its links come from, when they update, and what to check if expected links are missing. |
| Did we decide that Related Links did not make sense there? | `documentation/design/` | The decision, if recorded, with the relevant tradeoff. Compile the reasoning about Work Media View, Catalogue documents and other places where relationships are shown. |
| Did we run out of time and leave it as a follow-on? | `documentation/deliveries/` | What the completed delivery shipped, what it deferred, and the evidence that distinguishes the two. Link to an open item in `documentation/_working/` when there is one. |

The example starts a review. Establish current behaviour from its owner, look for an explicit decision, and record any remaining gap with the evidence available. `documentation/_working/` holds active and proposed deliveries, this tracker, and writing in progress.

## Proposed next batches

| Batch | Questions to answer | Start with |
| --- | --- | --- |
| **Media View and document relationships** | Which links belong to a Work in Media View, a Gallery, a Catalogue document or the Info panel? Which derive from the same references? What was decided or deferred? | [Catalogue Media View](../studio/Catalogue_Media_View.md), [Related Links](../studio/Related_Links.md), [Info Panel](../studio/Info_Panel.md), [Related Galleries](../studio/Related_Galleries.md), [Related Links delivery](../studio/Related_Links_Delivery.md) |
| **Document media and thumbnails** | What happens to images, files and thumbnails on Source Save, reuse and Delete? What is available in Working, and what gets transferred at Publish? | [Media And Asset Handling](../studio/Media_And_Asset_Handling.md), [Docs Images And Assets](../studio/Docs_Images_And_Assets.md), [Publication Media notes](data_model/Publication_Media.md) |
| **Catalogue authoring and adoption** | Which changes go from Save through Refresh and Regenerate? Which read models and queue entries change, and where does recovery start? | [Catalogue Save And Refresh](../studio/Catalogue_Save_And_Refresh.md), [Catalogue Work Editor](../studio/Catalogue_Work_Editor.md), [Catalogue Indexes And Payloads](../studio/Catalogue_Indexes_And_Payloads.md), [Catalogue Deployment](../studio/Catalogue_Deployment.md) |
| **Working generation and publication** | What does an exact build write? When is complete maintenance needed? Where are eligibility, queue completion and transfer decisions made? | [Builder](../studio/Builder.md), [Generated Data Contracts](../studio/Generated_Data_Contracts.md), [Source Organisation](../reference/Source_Organisation.md), [Publish and deploy](../guide/Publish_And_Deploy.md) |
| **Reader discovery and return** | Where do Index, Search, Recent and collection lists get their results? What does Back restore, and what survives a fresh open? | [Docs Viewer Runtime](../studio/Docs_Viewer_Runtime.md), [Docs Viewer Search](../studio/Docs_Viewer_Search.md), [Collection browsing architecture](../studio/Sub_Scope_Index_Architecture.md), [Find and read things](../guide/Find_And_Read_Things.md) |
| **Collections, Books and report composition** | Where do ownership, curation, editions and report capabilities live? What should a developer read before changing a collection host or control? | [Collection and Book architecture](../studio/Sub_Scope_Index_Architecture.md), [Reports](../studio/Reports.md), [Report Capability And Composition](../studio/Report_Capability_And_Composition.md), [Book source and provenance](../reference/Source_Organisation.md#book-source-and-provenance) |

Start with Media View and document relationships. Use its findings to decide where the next boundary falls. Add batches as the remaining Studio material reveals distinct questions.

## Batch log

| Status | Batch | Outcome and evidence |
| --- | --- | --- |
| Done | **Selected Documents and Reorder Docs** | Consolidated current Star and Position behaviour in [Reference](../reference/Source_Organisation.md). Kept the choice of a nested Index and searchable Position dialog in [Design](../design/Reorder_Docs.md), and kept the unique Selected acceptance and verification evidence in [Deliveries](../deliveries/Selected_Documents.md). Shortened the three records from about 6,950 to 3,810 words. Moved the former Studio archive to `documentation/deliveries/` and checked paths, headings and document metadata. |

Add one entry when a batch settles. Record the question it answers, the maintained owner, any design decision or useful delivery evidence preserved, and checks or unresolved follow-ons. Prefer a short outcome over repeating the implementation checklist.

## Closeout

- [ ] Settle the remaining Studio documents through migration, consolidation or retirement. Check links and document identities where files move.
- [ ] Walk representative developer questions through Reference, Design and Deliveries to check that each answer is easy to find.
- [ ] Add a short note on how the docs are organised and used to the [workflow guide](../guide/README.md) and [AGENTS.md](../../AGENTS.md). Mark this delivery complete after those entry points match the finished structure.
