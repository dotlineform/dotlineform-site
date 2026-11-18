---
draft: false
doc_id: d-20260419-000000-d2e47b
title: Dev Home
added_date: "2026-04-19 00:00:00"
last_updated: "2026-11-18"
summary: Repo-wide development workflow, testing, environment, and deployment references.
parent_id: ""

---
# Dev Home

Use the [workflow guide](../guide/README.md) to understand the site, [Reference](../reference/Source_Tree_Ownership.md) to find its current owners, and this folder for development practice. The native [App](../../app/AGENTS.md) and [Processing](../Processing/README.md) retain their separate project lifecycles.

## Start A Change

1. Review [Working](../_working/README.md) for active proposals or deliveries relevant to the request.
2. Follow [Development Workflow](Development_Workflow.md) for a bounded outcome and [Development Checklist](Development_Checklist.md) for implementation and review.
3. Use [Verification](Verification.md) for focused static checks, code review and manual acceptance. Use [Test Contract Discipline](Test_Contract_Discipline.md) when a specific failure warrants a separate test proposal.

## Find An Operation

| Need | Owner |
| --- | --- |
| Run local apps, configure storage, recover startup | [Local Setup](../reference/Local_Setup.md) and [Local Runners](../reference/Local_Runners.md) |
| Find source, configuration or a service boundary | [Source Tree Ownership](../reference/Source_Tree_Ownership.md), [Configuration](../reference/Configuration_And_Extension_Points.md) and [service map](../reference/Endpoint_Overview.md) |
| Build documents, discovery or publication effects | [Builder](../reference/Builder.md) |
| Edit or maintain Catalogue data | [Source model](../reference/Catalogue_Source_Model.md) and [Save through Publish](../reference/Catalogue_Save_And_Refresh.md) |
| Import, Export or exchange packages | [Import](../reference/Docs_Import.md), [Export](../reference/Export.md) and [packages](../reference/Document_Packages.md) |
| Process or transfer media | [Media policy](../reference/Catalogue_Media_Pipeline_Config.md) and [R2 maintenance](../reference/Publish_Media_To_R2.md) |
| Change dependencies or explain a diagram | [Dependencies](Runtime_Dependencies.md) and [diagram method](Data_Models_Diagrams.md) |
| Release tracked site output | [GitHub Actions](GitHub_Actions.md) and [Publish and deploy](../guide/Publish_And_Deploy.md) |

## Documentation Shape

`reference/` explains current behaviour; `design/` preserves reusable rationale; `deliveries/` records useful completed evidence. `development/` owns live development guidance. `_working/` holds active/proposed work and writing in progress; review that directory when choosing work rather than maintaining a second feature register. Processing uses its own [folder](../Processing/README.md). Purposeful links to delivery evidence are useful when they answer a concrete question; avoid duplicating its history in current references.

The [Codex Cloud setup](../_working/Cloud_Environments.md) remains open.
