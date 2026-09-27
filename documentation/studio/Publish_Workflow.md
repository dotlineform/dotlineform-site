---
draft: false
doc_id: d-20260905-141447-c33de1
title: Publish workflow
added_date: "2026-09-05 14:14:47"
last_updated: "2026-09-09 20:59:38"
summary: Distinguish accepted document publication from independent deployment of current Catalogue consumer data.
ui_status: proposed
parent_id: d-20260902-102745-8379ea
---
# Publish workflow

## Document Publication And Catalogue Deployment

Docs Publish owns the accepted Analysis document set and its document-owned output. Catalogue owns current Works, Series, Details and media; its records have no draft/published state and no separate Publish action. Their identity and availability do not depend on a document about them.

The current-Catalogue policy in [Publishing workflow concept](Publishing_Workflow_Concept.md) supersedes this note's earlier proposal to accept and freeze Catalogue dependencies inside the Analysis Published snapshot. [Catalogue Deployment](Catalogue_Deployment.md) owns the reconciled deployment boundary, implemented reader paths and remaining distribution design.

## Which Data A Reader Uses

| context | document data | Catalogue data |
| --- | --- | --- |
| Local Working | generated output for the selected document and stage | latest successfully completed external `catalogue/generated/` consumer data |
| Local Pre-publish | the selected Pre-publish document output | current external `catalogue/generated/` consumer data; document promotion does not pin Catalogue revisions |
| Public | the deployed accepted Analysis document set | current deployed Catalogue consumer data, independently of when a consuming document was published |

Studio Save completes affected generated Catalogue output. Deploying newer Catalogue data makes it available to existing public documents without rebuilding or republishing those documents. Public readers cannot see an undeployed local JSON change. If a Catalogue change alters the meaning of authored commentary, the author reviews and updates that document through the ordinary document workflow.

For example, adding a Work to Series `143` updates its generated membership. Local consumers can read that result. After the Catalogue update is deployed, an existing public Series presentation can load the new member without republication of its unchanged document. No draft Work or Series publication state is involved.

## Ownership Boundaries

Local Docs consumers must obtain Catalogue data from `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/generated/`, including the exact records and lookup data needed by tokens, reports, Media View and authoring tools. A local API may serve this output; it must not fall back to Studio canonical JSON, repository lookups or the frozen Catalogue archive. Studio retains canonical editing and generated-output ownership.

Document Build retains authored content and exact Catalogue references for current-data presentation. Document validation may report missing references or meaningful conflicts, but it must not turn those checks into acceptance of a frozen Catalogue snapshot. Public Catalogue-to-document links must respect the accepted deployed document set.

Deploy prepares the accepted document projection and the current Catalogue projection from their respective owners. It may compose those operations while permitting a Catalogue refresh without document republication. Git commit/push and Deploy Public remain explicit subsequent actions. Exact Catalogue inventory, media consistency, cleanup and caching belong to the later deployment design described in Catalogue Deployment.

## Implementation State

Catalogue publication fields and controls were removed in [UAC 4](UAC_4_Catalogue_Data_And_Editors.md); [UAC 5](UAC_5_Studio_Catalogue_Output.md) completed Studio's generated output. [Media View Text Links And Catalogue Images](Media_View_Text_Links_And_Catalogue_Images.md) has implemented current-data Work text links and the public reader seam. This is not a claim that every consumer or the complete deployment workflow has switched.

[Delivery Sequence](Analysis_Catalogue_Delivery_Sequence.md) owns the remaining token/presentation, document publishing and deployment order. [Gallery Design](Gallery_Design.md) and [Gallery List Design](Gallery_List_Design.md) must follow the current-Catalogue boundary when their production readers are implemented.
