---
draft: false
doc_id: d-20261117-213339-8c181b
title: Site Workflow Guide
added_date: "2026-11-17 21:33:39"
last_updated: "2026-11-18"
summary: Completed six-chapter guide to the site's workflows, with supporting references consolidated and design history preserved.
ui_status: done
parent_id: d-20260419-000000-d2e47b
---
# Site Workflow Guide

The [Site Workflow Guide](../guide/README.md) covers the six main workflows, their owners and the decisions behind them. It is the entry point from the repository README and Studio Dev Home.

## Closeout

Closed on 18 November 2026. Reviewed all six chapters as a newcomer and as a maintainer changing the default document. The isolated change exercised config generation, public projection, missing-target diagnosis and recovery. Final cleanup consolidated Manage service references, moved current import architecture into Docs Import and corrected local capability, media and public shell guidance. [Walkthrough evidence](Site_Workflow_Guide_Triage.md#guide-walkthrough)

The 290-file inventory is settled and archived. It records 136 retained references or independent proposals, 137 archived records and 17 retirements. Independent implementation proposals and existing manual acceptance gates retain their own owners. The supporting-library pass used source, document identity, link and whitespace checks. It made no runtime, user-data, test or publication changes. [Final inventory](Site_Workflow_Guide_Triage.md)

## Contents And Progress

| Chapter | Covers | Chapter status | Delivered cleanup |
| --- | --- | --- | --- |
| 1. [How the site fits together](../guide/How_The_Site_Fits_Together.md) | The public site, Studio, Docs Viewer, and their sources and projections. | Done | First-run path now includes runner addresses, required workspace roots and the Manage setting. |
| 2. [Author and organise documents](../guide/Author_And_Organise_Documents.md) | Working, collections, Books, media, links and exact document generation. | Done | Walkthrough corrected retired media paths, thumbnail ownership and recovery after Source Save. |
| 3. [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md) | Works, Series, Galleries and Save → Refresh → Regenerate. | Done | Updated the canonical data-model map and current operation references. Archived the earlier storage, data-model, report and regeneration records. |
| 4. [Publish and deploy](../guide/Publish_And_Deploy.md) | What Working prepares, what Publish transfers, and when GitHub Pages changes. | Done | Walkthrough distinguishes code-only release, content Publish, recovery and the separate Pages gate. |
| 5. [Find and read things](../guide/Find_And_Read_Things.md) | Index, Search, Recent, Catalogue browsing and Media View. | Done | Frozen reader, standalone Search, navigation proposals and UAC presentation studies archived. Current browsing and return guidance stays with the guide and reader owners. |
| 6. [Change the system safely](../guide/Change_The_System_Safely.md) | Where to make a change, how to check it, and how to recover when a workflow fails. | Done | Default-document projection and missing-target recovery exercised in a disposable copy. Reader interaction stays a manual check. |

Repository Markdown is the first readable edition. A PDF or EPUB could follow through the separate export work. [Export Book](../_working/Export_Book.md)

## What A Chapter Should Carry

Explain how to carry out the workflow, who owns each consequential step, and what the reader should expect to change. Put the reason for an important decision beside the rule it explains. Include the tradeoff or the condition that would make us reconsider it when the record supports one. For example, Working prepares eligible files and Publish consumes those completed selections so distribution can run without redoing authoring and generation. [Publish preparation](../reference/Builder.md#publish-preparation)

Verify current behaviour against the owning code, configuration and maintained references. Use delivery notes and commits to recover why a decision was made. Record an open question when the rationale is uncertain. Link to specialist references and code for exact schemas, commands and extension details. Keep one maintained owner for a procedure.

## Cleanup In Batches

Each workflow batch established the maintained owner before retiring duplicate guidance. The archive preserves original decisions, experiments, delivery evidence and limitations so later work can recover why the design changed. [Final inventory](Site_Workflow_Guide_Triage.md)

## Delivery Steps

- [x] **Capture the outcome.** Record the audience, draft contents, proposed destination and triage before changes to the existing document set.
- [x] **Choose the cleanup order.** Work by workflow, starting with the entry page and chapters 1 and 4.
- [x] **Check the first batch.** Identify the current owners and decision records for chapters 1 and 4 before writing.
- [x] **Draft the first batch.** Add the guide entry page and draft chapters 1 and 4.
- [x] **Write and link the guide.** Give readers a clear path from the repository and Studio entry points to each workflow. Check each chapter's instructions and rationale against its sources.
- [x] **Walk the complete guide.** Review it as a new reader and as someone changing a workflow. Fix the gaps found and record the evidence in the inventory.
- [x] **Consolidate the supporting library.** Carry forward unique current procedures and significant reasoning before retiring old copies. Check paths, links, document and parent IDs.
- [x] **Close the delivery.** Settle the supporting-library dispositions and archive the inventory.
