---
draft: false
doc_id: d-20261117-213339-8c181b
title: Site Workflow Guide
added_date: "2026-11-17 21:33:39"
last_updated: "2026-11-18"
summary: Create a small definitive guide to the site's workflows and retain the reasoning behind its main design decisions.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Site Workflow Guide

Create a short, definitive guide in `documentation/guide/` with one entry page and a small set of workflow chapters. It should help the product owner and coding collaborators see how the site works, find the owner of a change, and answer why the system works this way. The same guide should be readable in the public repository by a technically skilled newcomer.

## Where To Resume

**Completed this batch.** Wrote and reviewed chapter 2, [Author and organise documents](../../guide/Author_And_Organise_Documents.md). Retired Docs Viewer Overview and Site Overview after checking links, document IDs and parent references. Recorded their maintained replacements in the [working triage inventory](Site_Workflow_Guide_Triage.md#entry-points).

**Next visit.** Draft chapter 3 from the Studio Catalogue editor, Refresh and Regenerate owners. Follow a Work and a shared definition change through preparation to the publication queue. Use the chapter to identify which older Catalogue operating guides still have a distinct purpose.

## Contents And Progress

| Chapter | Covers | Chapter status | Cleanup to track |
| --- | --- | --- | --- |
| 1. [How the site fits together](../../guide/How_The_Site_Fits_Together.md) | The public site, Studio, Docs Viewer, and their sources and projections. | Done | Entry points and Source Tree Ownership updated. Docs Viewer Overview and Site Overview consolidated and retired. |
| 2. [Author and organise documents](../../guide/Author_And_Organise_Documents.md) | Working, collections, Books, media, links and exact document generation. | Done | Linked specialist references and corrected the media guide's Delete instruction. Older authoring references still need triage. |
| 3. Maintain the Catalogue | Works, Series, Galleries and Save → Refresh → Regenerate. | Queued | Review overlapping Catalogue guides and historical authoring instructions. |
| 4. [Publish and deploy](../../guide/Publish_And_Deploy.md) | What Working prepares, what Publish transfers, and when GitHub Pages changes. | Done | Runtime guidance corrected. Review the older publication references for consolidation. |
| 5. Find and read things | Index, Search, Recent, Catalogue browsing and Media View. | Queued | Review old scope, search and navigation guidance against current reader workflows. |
| 6. Change the system safely | Where to make a change, how to check it, and how to recover when a workflow fails. | Queued | Review setup, tooling and verification guides for overlapping procedures. |

At the end of each visit, update the relevant rows and leave the next concrete action and any decision it depends on under **Where To Resume**. Link each chapter here when its draft exists. Mark a chapter **Done** once its workflow, rationale and links have been reviewed. Record individual file dispositions in the [working triage inventory](Site_Workflow_Guide_Triage.md) and summarise any outstanding cleanup in the table.

Treat the chapter order as the first contents list for a book. Repository Markdown is the first readable edition. A PDF or EPUB could follow through the separate export work. [Export Book](Export_Book.md)

## What A Chapter Should Carry

Explain how to carry out the workflow, who owns each consequential step, and what the reader should expect to change. Put the reason for an important decision beside the rule it explains. Include the tradeoff or the condition that would make us reconsider it when the record supports one. For example, Working prepares eligible files and Publish consumes those completed selections so distribution can run without redoing authoring and generation. [Publish preparation](../Builder.md#publish-preparation)

Verify current behaviour against the owning code, configuration and maintained references. Use delivery notes and commits to recover why a decision was made. Record an open question when the rationale is uncertain. Link to specialist references and code for exact schemas, commands and extension details. Keep one maintained owner for a procedure.

## Cleanup In Batches

The first pass identified 60 useful references, 96 files to review, 94 archive candidates, and 40 deletion candidates. The file-level recommendations and their dependencies are in the [working triage inventory](Site_Workflow_Guide_Triage.md).

Use workflow batches. Draft the affected chapters, then update, consolidate, archive or delete old files as their replacement owner becomes clear. The scan found that docs in the 60-file keep set link to 32 review candidates, 10 archive candidates and one deletion candidate. Working by workflow lets those links follow the new authority as it is established. Use the 60-file set for evidence and retain specialist references with a distinct purpose. The 13 clearest retirements remain an early cleanup batch after link checks.

## Delivery Steps

- [x] **Capture the outcome.** Record the audience, draft contents, proposed destination and triage before changes to the existing document set.
- [x] **Choose the cleanup order.** Work by workflow, starting with the entry page and chapters 1 and 4.
- [x] **Check the first batch.** Identify the current owners and decision records for chapters 1 and 4 before writing.
- [x] **Draft the first batch.** Add the guide entry page and draft chapters 1 and 4.
- [ ] **Write and link the guide.** Give readers a clear path from the repository and Studio entry points to each workflow. Check each chapter's instructions and rationale against its sources.
- [ ] **Consolidate the supporting library.** Carry forward unique current procedures and significant reasoning before retiring old copies. Check relative links, document ID references and parent references for each move or deletion. Preserve the title and ID of any retained or moved Studio document.
- [ ] **Review and close.** Walk the guide as a new reader and as someone changing a workflow. Confirm that each chapter points to its maintained authority, settle the remaining review queue and retire the working inventory.
