---
draft: false
doc_id: d-20260523-222005-1085b2
title: Projection Contract
added_date: "2026-05-23 22:20:05"
last_updated: "2026-11-18"
parent_id: d-20260524-214228-7247ef

---
# Projection Contract

Canonical sources and configuration feed separate local and public projections. Keep private paths, authoring capabilities and operational state at their owning boundary. The tracked `site/` tree contains the artifact consumed by GitHub Pages. [Source Tree Ownership](Source_Tree_Ownership.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Working And Public Outputs

| Family | Editable owner and Working handoff | Public projection and exact contract |
| --- | --- | --- |
| Docs, collections and ready media | Working Markdown, source controls and configured media. Document generation prepares eligible navigation, collection manifests, by-ID documents and exact media effects. | Publish applies queued selections to Preview and configured repository or R2 destinations. [Source Organisation](Source_Organisation.md#storage-and-roles) · [Generated Data Contracts](Generated_Data_Contracts.md#current-payload-roots) |
| Catalogue | Studio canonical Works, Series, Galleries and memberships. Refresh prepares selected Working data and media. Regenerate adopts completed Work data into Catalogue documents. | Publish transfers completed Work documents, media and selected shared output. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#current-workflow) · [Catalogue publication](Catalogue_Save_And_Refresh.md#storage-and-selection) |
| Catalogue browsing and Search | Studio Refresh produces Catalogue Work/Gallery lookup data. Working explicitly builds the Docs Viewer Search scopes and Recent from their configured inputs. | Public Catalogue browsing uses the published Catalogue manifests and Gallery outputs. Portfolio Search and Recent load their own saved public files. The former standalone Catalogue Search belongs to the frozen archive. [Catalogue outputs](Catalogue_Indexes_And_Payloads.md#generated-read-models) · [Search index contract](Reader_Discovery_And_Return.md#payload-contract) · [Recent](Generated_Data_Contracts.md#recent-contract) · [Catalogue Archive](../deliveries/Catalogue_Archive.md#site-snapshot) |
| Shared reader runtime and browser configuration | `docs-viewer/` owns viewer code and styles. The browser-config generator derives local and public settings from the checked workspace configuration. | The explicit `site-code-update` inventory creates the public subset in `site/docs-viewer/`. The public reader at `/` uses that subset and published data. [Configuration projection](Configuration_And_Extension_Points.md#source-config-becomes-browser-config) · [Runtime projection](../development/Verification.md#docs-viewer-site-code-projection) |

Studio routes, live editor lookups and local report outputs serve Studio or Manage. Catalogue source paths, storage declarations and staging flags stay with their canonical or private owners. Public document and media references retain exact identities and use their configured reader destinations. [Catalogue source model](Catalogue_Source_Model.md) · [Public execution path](Docs_Viewer_Runtime.md#public-execution-path)

## Current Enforcement

The workspace configuration owns data and media locations. The Catalogue artifact inventory owns supported Catalogue public file families. The site-code inventory owns which runtime and configuration files ship publicly. Follow these owners when adding a projection and name the exact source, producer, destination and consumer. [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) · [Catalogue artifact inventory](../../docs-viewer/config/workspace/catalogue-artifacts.json) · [Site-code inventory](../../site-tools/config/site-code-update.json)

Use `bin/site-code-update --check` for projected runtime parity and `bin/site-validate` for the deploy root. Working generation decides eligibility and Publish verifies the selected operations at their configured destinations. When a public data contract changes, trace the producing field selection and inspect the affected output for source paths, storage details and authoring data. [Site validation and preview](Local_Setup.md#public-preview-and-projection) · [Publish transfer boundary](Builder.md#preview-and-deployment-boundary) · [Former projection audit](../deliveries/Projection_Contract_Validation.md)
