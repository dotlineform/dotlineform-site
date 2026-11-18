---
draft: false
doc_id: d-20261117-213339-b5aa67
title: Site Workflow Guide Triage
added_date: "2026-11-17 21:33:39"
last_updated: "2026-11-18"
summary: Working inventory of the 290 Studio documents reviewed before the Site Workflow Guide delivery.
parent_id: d-20261117-213339-8c181b
---
# Site Workflow Guide Triage

Snapshot from 17 November 2026. Treat each row as a candidate and record its final disposition during the delivery. Retire this inventory at closeout. [Site Workflow Guide delivery](Site_Workflow_Guide.md)

This is a first-pass recommendation for the 290 Markdown files directly under `documentation/studio/`. It leaves the four deliveries, the archive, and the `data_model/` and `tokens/` owners outside the disposition list. Links from those active folders were considered when checking dependencies. The scan predates any moves, deletions or rewrites for this delivery.

| Disposition | Files | What to do |
| --- | ---: | --- |
| Keep current | 60 | Keep the operating guide or required policy in the active library. Use the executable owner for exact behavior. |
| Review | 96 | Review accuracy, continued relevance or overlap. Fix the useful guide or merge it into one owner before moving the rest. |
| Archive | 94 | Move significant decisions, migrations and useful design history out of current guidance once links are reconciled. |
| Delete candidate | 40 | Remove an obsolete procedure, duplicate delivery or tombstone after checking unique surviving information and redirecting its references. |

## What the scan establishes

Every top-level file was inventoried. The first pass read front matter, opening text, filenames and references from Studio Markdown, then compared selected high-impact claims and deletion examples with the current code, configuration and maintained guides. This is a disposition list, not a line-by-line verification of all 290 documents. Last-updated dates and status are signals only. There are 39 files with no recorded inbound Markdown paths or document ID/parent references in the scanned Studio tree. The counts do not measure readership or usage outside that tree.

The present model has one configured Docs workspace. Working owns source, generation and ready publication effects. Publish applies selected files and removals to Preview and configured destinations. GitHub Pages deploys tracked `site/` separately. Studio remains the Catalogue authoring owner, with Refresh producing Working data and Regenerate adopting the selected Work changes. The current Search contract describes Portfolio and collection Search scopes, which are distinct from the retired document workspace scopes. These are the strongest checks against stale operating instructions. [docs-workspace.json](../../../docs-viewer/config/workspace/docs-workspace.json) · [Source Organisation](../Source_Organisation.md) · [Builder](../Builder.md) · [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) · [Docs Search Index](../Docs_Search_Index.md)

Drift found in the 17 November scan. See the entry-point rows below for the current disposition.

- Dev Home located Studio Markdown in the retired repository scope tree. Docs Viewer and its former Overview sent readers to obsolete scope operations and configuration. [Dev Home](../Dev_Home.md) · [Docs Viewer](../Docs_Viewer.md)
- Source Tree Ownership still describes an external Published snapshot and Deploy Repo. Parts of Docs Viewer Runtime accurately describe the reader, but its Publish row still calls for an automatic Recent refresh. The current Recent contract gives discovery its own explicit refresh/build and gives Publish only queued bytes. [Source Tree Ownership](../Source_Tree_Ownership.md) · [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) · [Generated Data Contracts](../Generated_Data_Contracts.md)
- The former Site Overview mixed the active root Docs Viewer with routes from the frozen Catalogue. The archived Catalogue retains its search policy beneath `site/archive/`. [Site](../Site.md) · [Catalogue Archive](../Catalogue_Archive.md) · [policy.json](../../../site/archive/assets/data/search/policy.json)

## Using This Inventory

The **First pass** markers in Delete candidates identify the 13 clear retirements from the original review. Recheck path links, document ID links and `parent_id` dependents when handling each batch. The 60 Keep rows identify useful authorities and references to draw from. Reassess how many the smaller guide actually needs to link to.

## Keep current (60)

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Broken_Links_Script.md](../Broken_Links_Script.md) | 10 / 0 | Saved Broken Links audit and procedure. |
| [Browser_Smoke_Testing.md](../Browser_Smoke_Testing.md) | 2 / 0 | Required browser-check policy and evidence boundary. |
| [Builder.md](../Builder.md) | 45 / 0 | Working generation, Book TOC, eligibility, publication preparation and discovery. |
| [Button_Placement.md](../Button_Placement.md) | 1 / 0 | Keep as the focused reference for button placement. |
| [CSS_Ownership.md](../CSS_Ownership.md) | 5 / 0 | Shared reader style ownership. |
| [Catalogue_Archive.md](../Catalogue_Archive.md) | 5 / 0 | Operational reference for the frozen Catalogue archive; its historical subject is intentional. |
| [Catalogue_Deployment.md](../Catalogue_Deployment.md) | 31 / 0 | Retain as the exact reference for selected Catalogue transfers, completion and failure timing. The guide covers the operator's release sequence. |
| [Catalogue_Field_Registry.md](../Catalogue_Field_Registry.md) | 4 / 0 | Catalogue field and output families. |
| [Catalogue_Indexes_And_Payloads.md](../Catalogue_Indexes_And_Payloads.md) | 14 / 0 | Current generated Work and Gallery payloads. |
| [Catalogue_Media_Pipeline_Config.md](../Catalogue_Media_Pipeline_Config.md) | 7 / 0 | Keep as the focused reference for catalogue media pipeline config. |
| [Catalogue_Media_View.md](../Catalogue_Media_View.md) | 27 / 0 | Retain the Work/Gallery adapter, Context links and exact grid return rules. Chapter 5 carries the reader workflow. |
| [Catalogue_Save_And_Refresh.md](../Catalogue_Save_And_Refresh.md) | 37 / 0 | Retain as the exact reference for queue state, selection, media handoff and Regenerate completion. Chapter 3 carries the walkthroughs. |
| [Catalogue_Services.md](../Catalogue_Services.md) | 3 / 0 | Keep as the focused reference for catalogue services. |
| [Catalogue_Shuffle_Randomness.md](../Catalogue_Shuffle_Randomness.md) | 2 / 0 | Shuffle stock origin, replacement and reader behavior. |
| [Catalogue_Work_Editor.md](../Catalogue_Work_Editor.md) | 12 / 0 | Retain for Work editor, bulk editing, media selection and Gallery dialog details. |
| [Catalogue_Works.md](../Catalogue_Works.md) | 8 / 0 | Keep as the focused reference for catalogue works. |
| [Development_Checklist.md](../Development_Checklist.md) | 17 / 0 | Repository implementation guardrails. |
| [Development_Workflow.md](../Development_Workflow.md) | 5 / 0 | Development lifecycle and delivery workflow. |
| [Docs_Images_And_Assets.md](../Docs_Images_And_Assets.md) | 2 / 0 | Retain the native image and download procedure. Corrected its Delete instruction with chapter 2. The existing-media examples still need review for retired scope paths. |
| [Docs_Import.md](../Docs_Import.md) | 7 / 2 | Retain collection import and the return handoff. Reconcile the older `publishable` discussion with the current Draft and Working eligibility rules. |
| [Docs_Search_Index.md](../Docs_Search_Index.md) | 8 / 0 | Search artifact format and eligibility. |
| [Docs_Search_Tokenizer.md](../Docs_Search_Tokenizer.md) | 2 / 0 | Search term normalization. |
| [Docs_Viewer_Search.md](../Docs_Viewer_Search.md) | 8 / 2 | Retain for exact Search scope switching, query and result controls. Chapter 5 routes readers to it. |
| [Document_Diagrams.md](../Document_Diagrams.md) | 9 / 0 | Keep as the focused reference for document diagrams. |
| [Document_Identity.md](../Document_Identity.md) | 2 / 0 | Stable document identity. |
| [Document_Image_Detail.md](../Document_Image_Detail.md) | 3 / 0 | Current opt-in image detail procedure. |
| [Export.md](../Export.md) | 10 / 0 | Current collection HTML export and media behavior. |
| [File_Picker.md](../File_Picker.md) | 2 / 0 | Keep as the focused reference for file picker. |
| [Folder_Picker.md](../Folder_Picker.md) | 2 / 0 | Keep as the focused reference for folder picker. |
| [Generated_Data_Contracts.md](../Generated_Data_Contracts.md) | 30 / 0 | Generated artifact and reader data contracts. |
| [Generated_Read_Endpoints.md](../Generated_Read_Endpoints.md) | 2 / 0 | Read-only generated API boundary. |
| [GitHub_Actions.md](../GitHub_Actions.md) | 3 / 0 | Public workflow entry point. YAML remains authoritative. |
| [HTML_Import_Mapping.md](../HTML_Import_Mapping.md) | 3 / 0 | Keep as the focused reference for html import mapping. |
| [Icon_Tokens.md](../Icon_Tokens.md) | 5 / 0 | Keep as the focused reference for icon tokens. |
| [Local_Runners.md](../Local_Runners.md) | 3 / 0 | Retain for choosing a runner, default URLs and service supervision. Chapter 6 uses this reference for local and public checks. |
| [Local_Setup_Public_Site_Preview.md](../Local_Setup_Public_Site_Preview.md) | 2 / 0 | Retain for the static preview wrapper, options and deploy-root checks. |
| [Media_And_Asset_Handling.md](../Media_And_Asset_Handling.md) | 38 / 0 | Media ownership, attachment procedures and R2 report. |
| [Package_Export_Metadata.md](../Package_Export_Metadata.md) | 2 / 0 | Prepare/return provenance contract. |
| [Package_Prepare.md](../Package_Prepare.md) | 12 / 0 | Collection package procedure. |
| [Package_Prepare_Profiles.md](../Package_Prepare_Profiles.md) | 4 / 0 | Package profile shapes. |
| [Package_Prepare_Script.md](../Package_Prepare_Script.md) | 4 / 0 | Working package producer. |
| [Planned_Features.md](../Planned_Features.md) | 25 / 53 | Current plan and proposal routing. |
| [Public_Docs_Route_Shell.md](../Public_Docs_Route_Shell.md) | 1 / 0 | Active public root route shell. |
| [Pytest.md](../Pytest.md) | 0 / 0 | Required pytest policy reference. Confirm selected fixtures against current owners. |
| [Record_List_And_Actions.md](../Record_List_And_Actions.md) | 3 / 0 | Keep as the focused reference for record list and actions. |
| [Related_Links.md](../Related_Links.md) | 28 / 2 | Authored Related Links representation and generation. |
| [Reports.md](../Reports.md) | 25 / 1 | Current report inventory and procedures. Review individual report evidence separately. |
| [Run_Checks.md](../Run_Checks.md) | 6 / 0 | Retain exact lint, profile runner and projection commands. Chapter 6 explains why the example uses the projection and route checks. |
| [Search_Fields.md](../Search_Fields.md) | 3 / 0 | Keep as the focused reference for search fields. |
| [Search_List.md](../Search_List.md) | 2 / 0 | Keep as the focused reference for search list. |
| [Selectable_List.md](../Selectable_List.md) | 2 / 0 | Keep as the focused reference for selectable list. |
| [Shared_UI.md](../Shared_UI.md) | 1 / 6 | Keep as the focused reference for shared ui. |
| [Source_Editor_Endpoints.md](../Source_Editor_Endpoints.md) | 11 / 0 | Source editor request and response owner. |
| [Source_Mutation_Endpoints.md](../Source_Mutation_Endpoints.md) | 4 / 0 | Working mutation endpoint reference. |
| [Source_Organisation.md](../Source_Organisation.md) | 46 / 0 | Canonical storage and publication owners. |
| [Sub_Scope_Index_Architecture.md](../Sub_Scope_Index_Architecture.md) | 18 / 1 | Current collection browsing and Book structure; some historical sections should be checked before changing older behavior. |
| [Test_Contract_Discipline.md](../Test_Contract_Discipline.md) | 28 / 0 | Binding test scope and coverage policy. |
| [Testing.md](../Testing.md) | 26 / 5 | Required testing guide and evidence limits. |
| [Toolbar_Icons.md](../Toolbar_Icons.md) | 4 / 0 | Keep as the focused reference for toolbar icons. |
| [Word_Import_Style_Mapping.md](../Word_Import_Style_Mapping.md) | 2 / 0 | Keep as the focused reference for word import style mapping. |

## Needs review (96)

### Entry points

Repair the reader’s route to maintained owners. Check all scope, storage, deployment and capability claims against current configuration. Consolidate hub pages that send readers to the same destination.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Dev_Home.md](../Dev_Home.md) | 0 / 9 | Retained and updated. Routes readers to the workflow guide and chapter 6, names the current Studio documentation root and keeps the development references. |
| [Docs_Viewer.md](../Docs_Viewer.md) | 5 / 49 | Retained and updated as the task and reference entry point. Its opening now carries the three-surface overview and links to the guide and Runtime. |
| `Docs_Viewer_Overview.md` | 2 / 0 | Retired after checking repository and Working source paths, document IDs and parent references. [Docs Viewer](../Docs_Viewer.md) covers orientation, [Runtime](../Docs_Viewer_Runtime.md) covers route authority and [Docs Review](../Docs_Review.md) covers the package workflow. |
| [Docs_Viewer_Runtime.md](../Docs_Viewer_Runtime.md) | 40 / 5 | Retained. Corrected the explicit discovery and Publish completion rows and removed the retired full-rebuild and Settings guidance from that section. |
| [Site.md](../Site.md) | 2 / 6 | Retained and updated. Routes to the active root reader, the publication guide and the separately identified frozen Catalogue references. |
| `Site_Overview.md` | 1 / 0 | Retired after checking repository and Working source paths, document IDs and parent references. [Site](../Site.md) and the guide cover the active site and release, [Site Shell Runtime](../Site_Shell_Runtime.md) covers shell ownership, and [Catalogue Archive](../Catalogue_Archive.md) covers the old routes. |
| [Source_Tree_Ownership.md](../Source_Tree_Ownership.md) | 9 / 0 | Retained as the directory and cross-project ownership reference. Updated Working and Preview storage, direct publication destinations and the native app boundary. The workflow guide carries the release sequence. |
| [Studio.md](../Studio.md) | 2 / 19 | Retained and updated. Routes to the Catalogue chapter and the current Work Editor and Series controls. |
| [Studio_Overview.md](../Studio_Overview.md) | 2 / 0 | A front door still includes former Detail authoring and draft/status capabilities. Compare the exact Studio route registry. |
| [Sub_Scopes.md](../Sub_Scopes.md) | 0 / 3 | Check the sub scopes guidance against the owning implementation or current plan. |
| [System_Architecture.md](../System_Architecture.md) | 1 / 7 | Check the system architecture guidance against the owning implementation or current plan. |

### Configuration, execution and operator commands

Check shown paths, procedure and interface names against the current scripts, config and router. Keep one responsibility per guide. Review remote-write and recovery instructions before using them.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Cloud_Environments.md](../Cloud_Environments.md) | 3 / 0 | Check the cloud environments guidance against the owning implementation or current plan. |
| [Configuration_And_Extension_Points.md](../Configuration_And_Extension_Points.md) | 16 / 0 | Check the configuration and extension points guidance against the owning implementation or current plan. |
| [Configuration_Map.md](../Configuration_Map.md) | 3 / 0 | Check the configuration map guidance against the owning implementation or current plan. |
| [Dependencies.md](../Dependencies.md) | 0 / 0 | Check the dependencies guidance against the owning implementation or current plan. |
| [Endpoint_Overview.md](../Endpoint_Overview.md) | 5 / 9 | Check the endpoint overview guidance against the owning implementation or current plan. |
| [Health_And_Capabilities_Endpoints.md](../Health_And_Capabilities_Endpoints.md) | 1 / 0 | Check the health and capabilities endpoints guidance against the owning implementation or current plan. |
| [Local_Setup.md](../Local_Setup.md) | 3 / 6 | Check the local setup guidance against the owning implementation or current plan. |
| [Local_Setup_Environment.md](../Local_Setup_Environment.md) | 1 / 0 | Check the local setup environment guidance against the owning implementation or current plan. |
| [Local_Setup_GitHub_And_Codex_Notes.md](../Local_Setup_GitHub_And_Codex_Notes.md) | 1 / 0 | Check the local setup github and codex notes guidance against the owning implementation or current plan. |
| [Local_Setup_Recovery.md](../Local_Setup_Recovery.md) | 1 / 0 | Check the local setup recovery guidance against the owning implementation or current plan. |
| [Local_Setup_Toolchain.md](../Local_Setup_Toolchain.md) | 1 / 0 | Check the local setup toolchain guidance against the owning implementation or current plan. |
| [Local_Studio_APIs.md](../Local_Studio_APIs.md) | 6 / 0 | Check the local studio apis guidance against the owning implementation or current plan. |
| [Local_Studio_App.md](../Local_Studio_App.md) | 5 / 1 | Check the local studio app guidance against the owning implementation or current plan. |
| [Local_Studio_Routes.md](../Local_Studio_Routes.md) | 4 / 0 | Check the local studio routes guidance against the owning implementation or current plan. |
| [Management_Services.md](../Management_Services.md) | 2 / 3 | Check the management services guidance against the owning implementation or current plan. |
| [Projection_Contract.md](../Projection_Contract.md) | 6 / 0 | Check the projection contract guidance against the owning implementation or current plan. |
| [Projection_Contract_Validation.md](../Projection_Contract_Validation.md) | 2 / 0 | Check the projection contract validation guidance against the owning implementation or current plan. |
| [Publish_Media_To_R2.md](../Publish_Media_To_R2.md) | 8 / 0 | R2 write/delete runbook. Verify the real command, targets and authority against the tool before retaining it as operating guidance. |
| [Route_Dispatch_Scripts.md](../Route_Dispatch_Scripts.md) | 1 / 0 | Check the route dispatch scripts guidance against the owning implementation or current plan. |
| [Route_Ready_State.md](../Route_Ready_State.md) | 3 / 0 | Check the route ready state guidance against the owning implementation or current plan. |
| [Runtime_Dependencies.md](../Runtime_Dependencies.md) | 4 / 0 | Check the runtime dependencies guidance against the owning implementation or current plan. |
| [Runtime_Module_Ownership.md](../Runtime_Module_Ownership.md) | 8 / 0 | Check the runtime module ownership guidance against the owning implementation or current plan. |
| [Scripts.md](../Scripts.md) | 1 / 0 | Check the scripts guidance against the owning implementation or current plan. |
| [Scripts_Overview.md](../Scripts_Overview.md) | 2 / 8 | Check the scripts overview guidance against the owning implementation or current plan. |
| [Service_Entrypoints.md](../Service_Entrypoints.md) | 1 / 0 | Check the service entrypoints guidance against the owning implementation or current plan. |
| [Site_Consistency_Audit.md](../Site_Consistency_Audit.md) | 2 / 0 | Check whether commands and checks describe the frozen Catalogue or the active public site. The difference matters for operation. |
| [Site_Shell_Runtime.md](../Site_Shell_Runtime.md) | 1 / 0 | Check the site shell runtime guidance against the owning implementation or current plan. |
| [Studio_Config_JSON.md](../Studio_Config_JSON.md) | 3 / 0 | Check the studio config json guidance against the owning implementation or current plan. |
| [Studio_Domain_Config.md](../Studio_Domain_Config.md) | 2 / 1 | Check the studio domain config guidance against the owning implementation or current plan. |
| [Studio_Read_And_Save_Flow.md](../Studio_Read_And_Save_Flow.md) | 2 / 0 | Check the studio read and save flow guidance against the owning implementation or current plan. |
| [Studio_Runtime.md](../Studio_Runtime.md) | 7 / 2 | Check the studio runtime guidance against the owning implementation or current plan. |
| [UI_Status.md](../UI_Status.md) | 0 / 0 | Check the ui status guidance against the owning implementation or current plan. |

### Docs authoring, routing and packages

Check the current Working, collection-aware API and UI. Consolidate overlapping endpoint or report pages around the owning procedure. Mark accepted legacy examples and unreviewed test coverage as historical.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Audit_Scripts.md](../Audit_Scripts.md) | 1 / 0 | Check the audit scripts guidance against the owning implementation or current plan. |
| [Broken_Links.md](../Broken_Links.md) | 5 / 0 | Check the broken links guidance against the owning implementation or current plan. |
| [Create_And_Import_Endpoints.md](../Create_And_Import_Endpoints.md) | 3 / 0 | Check the create and import endpoints guidance against the owning implementation or current plan. |
| [Doc_Navigation.md](../Doc_Navigation.md) | 5 / 3 | Retain the hierarchy feature and its child proposal for review. [Runtime](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns current reader navigation and sequence behaviour. |
| [Docs_Import_Architecture.md](../Docs_Import_Architecture.md) | 6 / 0 | Sub-scope/stage import examples coexist with useful conversion and persistence design. Compare them with current collection import and Review. |
| [Docs_Review.md](../Docs_Review.md) | 8 / 0 | The main Review workflow is useful. Reconcile residual scope/stage terms and the current return-import boundary with Docs Import before relying on exact payload examples. |
| [Docs_Review_Endpoints.md](../Docs_Review_Endpoints.md) | 3 / 0 | Check the docs review endpoints guidance against the owning implementation or current plan. |
| [Import_Scripts.md](../Import_Scripts.md) | 1 / 0 | Check the import scripts guidance against the owning implementation or current plan. |
| [Info_Panel.md](../Info_Panel.md) | 6 / 0 | Check the info panel guidance against the owning implementation or current plan. |
| [Management_Operations.md](../Management_Operations.md) | 5 / 0 | Check the management operations guidance against the owning implementation or current plan. |
| [Package_Return_Parser.md](../Package_Return_Parser.md) | 1 / 0 | Check parser inputs against the current exact collection/return-package contract and keep implementation named in Docs Import. |
| [Package_Return_Review.md](../Package_Return_Review.md) | 0 / 0 | Check the package return review guidance against the owning implementation or current plan. |
| [Panel_Hosts_And_Control_Surfaces.md](../Panel_Hosts_And_Control_Surfaces.md) | 4 / 0 | Check the panel hosts and control surfaces guidance against the owning implementation or current plan. |
| [Publication_Ignore_List.md](../Publication_Ignore_List.md) | 3 / 0 | Check the publication ignore list guidance against the owning implementation or current plan. |
| [Read_And_Config_Scripts.md](../Read_And_Config_Scripts.md) | 1 / 0 | Check the read and config scripts guidance against the owning implementation or current plan. |
| [Rebuild_And_Audit_Endpoints.md](../Rebuild_And_Audit_Endpoints.md) | 1 / 0 | Check the rebuild and audit endpoints guidance against the owning implementation or current plan. |
| [Rebuild_Follow_Through_Scripts.md](../Rebuild_Follow_Through_Scripts.md) | 1 / 0 | Check the rebuild follow through scripts guidance against the owning implementation or current plan. |
| [Related_Galleries.md](../Related_Galleries.md) | 1 / 0 | Check the related galleries guidance against the owning implementation or current plan. |
| [Reorder_Docs.md](../Reorder_Docs.md) | 3 / 0 | Check the reorder docs guidance against the owning implementation or current plan. |
| [Report_Block_Tokens.md](../Report_Block_Tokens.md) | 2 / 0 | Check the report block tokens guidance against the owning implementation or current plan. |
| [Report_Capability_And_Composition.md](../Report_Capability_And_Composition.md) | 1 / 0 | Check the report capability and composition guidance against the owning implementation or current plan. |
| [Selected_Documents.md](../Selected_Documents.md) | 1 / 0 | Check the selected documents guidance against the owning implementation or current plan. |
| [Semantic_Tokens.md](../Semantic_Tokens.md) | 7 / 5 | Check the semantic tokens guidance against the owning implementation or current plan. |
| [Semantic_Tokens_Architecture.md](../Semantic_Tokens_Architecture.md) | 24 / 0 | Check the semantic tokens architecture guidance against the owning implementation or current plan. |
| [Semantic_Tokens_Concept.md](../Semantic_Tokens_Concept.md) | 0 / 0 | Check the semantic tokens concept guidance against the owning implementation or current plan. |
| [Semantic_Tokens_Source_Editor_UI.md](../Semantic_Tokens_Source_Editor_UI.md) | 7 / 0 | Check the semantic tokens source editor ui guidance against the owning implementation or current plan. |
| [Source_Editor_Scripts.md](../Source_Editor_Scripts.md) | 21 / 0 | Check the source editor scripts guidance against the owning implementation or current plan. |
| [Source_Mutation_Scripts.md](../Source_Mutation_Scripts.md) | 2 / 0 | Check the source mutation scripts guidance against the owning implementation or current plan. |
| [Target_Lookup.md](../Target_Lookup.md) | 3 / 0 | Check the target lookup guidance against the owning implementation or current plan. |
| [Toolbar_Icon_Mapping.md](../Toolbar_Icon_Mapping.md) | 5 / 0 | Check the toolbar icon mapping guidance against the owning implementation or current plan. |
| [Toolbar_Model.md](../Toolbar_Model.md) | 5 / 0 | Check the toolbar model guidance against the owning implementation or current plan. |

### Catalogue and cross-domain ownership

Retain the useful concepts and diagrams. Bring authoring, storage, relationship, media and publication claims into line with current code and the app boundaries. Move old workflows into their history when appropriate.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Catalogue_Architecture.md](../Catalogue_Architecture.md) | 5 / 3 | Retain the canonical and generated-data ownership map. Updated Projects staging and the Refresh/Regenerate handoff, and linked the chapter for examples. |
| [Catalogue_Data_Model_Map.md](../Catalogue_Data_Model_Map.md) | 0 / 0 | Check the catalogue data model map guidance against the owning implementation or current plan. |
| [Catalogue_Series_Management.md](../Catalogue_Series_Management.md) | 4 / 0 | Retain the Series browsing, membership and dialog reference at the current Work Editor route. |
| [Catalogue_Source_Model.md](../Catalogue_Source_Model.md) | 17 / 1 | Retain the canonical Catalogue source contract and reconcile old Subject and editor-policy references against Studio and the field registry. |
| [Data_Models_Diagrams.md](../Data_Models_Diagrams.md) | 1 / 3 | Check the data models diagrams guidance against the owning implementation or current plan. |
| [Knowledge_System_Vision.md](../Knowledge_System_Vision.md) | 1 / 0 | Check the knowledge system vision guidance against the owning implementation or current plan. |
| [Local_Authoring_And_Publication.md](../Local_Authoring_And_Publication.md) | 2 / 0 | Keep the rationale for separate service owners if useful. Its description of live Tag APIs and scope-snapshot publication is historical. |
| [Processing.md](../Processing.md) | 2 / 1 | Keep the Processing boundary legible. Check any integration instructions against the separate Processing project’s owner. |
| [Shared_Artifact_Patterns.md](../Shared_Artifact_Patterns.md) | 1 / 0 | Check the shared artifact patterns guidance against the owning implementation or current plan. |
| [Shared_Icons.md](../Shared_Icons.md) | 7 / 3 | Check the shared icons guidance against the owning implementation or current plan. |
| [Works_Editor_Icon_Mapping.md](../Works_Editor_Icon_Mapping.md) | 3 / 0 | Check the works editor icon mapping guidance against the owning implementation or current plan. |

### Ideas and unfinished proposals

Check whether the proposal is still wanted, superseded or already planned elsewhere. Preserve approved implementation constraints and active routing. Park useful ideas without treating them as shipped instructions.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Catalogue_Hosting_And_Storage_Options.md](../Catalogue_Hosting_And_Storage_Options.md) | 1 / 0 | Check the catalogue hosting and storage options guidance against the owning implementation or current plan. |
| [Catalogue_Images_In_Export_And_Review.md](../Catalogue_Images_In_Export_And_Review.md) | 2 / 0 | Check the catalogue images in export and review guidance against the owning implementation or current plan. |
| [Docs_Search_Relevance.md](../Docs_Search_Relevance.md) | 2 / 0 | Compare historical relevance proposals against the current Search policy before scheduling any work. |
| [Docs_Viewer_App_Roadmap.md](../Docs_Viewer_App_Roadmap.md) | 1 / 0 | Check the docs viewer app roadmap guidance against the owning implementation or current plan. |
| [Document_Link_Strength.md](../Document_Link_Strength.md) | 2 / 0 | Check the document link strength guidance against the owning implementation or current plan. |
| [Independent_Canonical_Documents.md](../Independent_Canonical_Documents.md) | 1 / 0 | Check the independent canonical documents guidance against the owning implementation or current plan. |
| [Public_Docs_Source_Repository.md](../Public_Docs_Source_Repository.md) | 0 / 0 | Prior public-source repository proposal carries an urgent flag. Decide explicitly whether it is still wanted before retaining or archiving. |
| [Public_Mobile_Experience.md](../Public_Mobile_Experience.md) | 1 / 0 | Older mobile plan. Transfer any unique reader journeys to the linked Mobile Layouts delivery before archiving. |
| [R2_Workspace_Backups.md](../R2_Workspace_Backups.md) | 1 / 0 | Check the r2 workspace backups guidance against the owning implementation or current plan. |
| [Search.md](../Search.md) | 0 / 3 | Retained as the Search entry point and parent. Replaced the retired scope and Catalogue routes with links to the chapter, current Search owners and the frozen archive. |
| [Search_Build_Pipeline.md](../Search_Build_Pipeline.md) | 3 / 0 | Removed retired commands and routed to [Builder](../Builder.md#working-rebuild), [Docs Search Index](../Docs_Search_Index.md) and the Catalogue Archive. Reconcile the legacy Projection Contract and Docs Data links in their respective batches before retiring this page. |

## Archive candidates (94)

The subject column describes what the file records. Advice and status inside an archived document may describe an older operating model.

### Original Analysis, Catalogue and UAC work

Retain design or migration context. Use the current Catalogue editor, source, browse, generated and deployment guides for active behavior. Keep linked UAC/Analysis families together when moving them.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Analysis_And_Catalogue_Presentation.md](../Analysis_And_Catalogue_Presentation.md) | 10 / 18 | Present accepted Analysis documents and current Catalogue data through Docs Viewer while retaining the legacy Cata… |
| [Analysis_Catalogue_Architecture.md](../Analysis_Catalogue_Architecture.md) | 1 / 0 | Define the frozen Catalogue archive and the proposed document, token, projection, Search and publication architect… |
| [Analysis_Catalogue_Concept.md](../Analysis_Catalogue_Concept.md) | 9 / 0 | Present canonical Works in Media View, with tokens and associated documents providing authored routes to discussio… |
| [Analysis_Catalogue_Delivery_Sequence.md](../Analysis_Catalogue_Delivery_Sequence.md) | 9 / 0 | Complete token and presentation work in Working, then review and implement Pre-publish/Publish before a separate D… |
| [Analysis_Catalogue_Done.md](../Analysis_Catalogue_Done.md) | 0 / 23 | Historical baseline or decision record. |
| [Analysis_Media_In_R2.md](../Analysis_Media_In_R2.md) | 3 / 0 | Restore legacy Moments media to Working and make R2 mirror the accepted Analysis media structure. |
| [Catalogue_And_Analysis_Storage_Layout.md](../Catalogue_And_Analysis_Storage_Layout.md) | 2 / 0 | Keep canonical Catalogue data and projections separate from the retained Analysis Works document collection, accep… |
| [Catalogue_Authoring_In_Docs_Viewer.md](../Catalogue_Authoring_In_Docs_Viewer.md) | 1 / 0 | Establish shared local assets and stage-owned Catalogue JSON before report changes; Save prepares Working data, Pr… |
| [Catalogue_CSS.md](../Catalogue_CSS.md) | 1 / 0 | Define a versioned Work and Work Detail HTML/CSS component that preserves essential presentation in interactive Do… |
| [Catalogue_Changed_Regeneration_Delivery.md](../Catalogue_Changed_Regeneration_Delivery.md) | 0 / 0 | Reconcile Catalogue documents with new, changed and deleted Works using a durable update list, targeted Regenerate… |
| [Catalogue_Collection_Browsing.md](../Catalogue_Collection_Browsing.md) | 1 / 0 | Make the public Catalogue collection usable with browser-owned search, a short typing delay, latest-edited orderin… |
| [Catalogue_Context_Navigation.md](../Catalogue_Context_Navigation.md) | 0 / 0 | Navigation from one work to the next is currently defined by their place in a series of works. Works can be ordere… |
| [Catalogue_Data_Model.md](../Catalogue_Data_Model.md) | 8 / 0 | Define the five document subject choices, the composite Detail identity and Studio's data-quality ownership within… |
| [Catalogue_Documents_And_Metadata.md](../Catalogue_Documents_And_Metadata.md) | 1 / 0 | Define a Regenerate-owned Catalogue Entry token with a Work H1, metadata and resource list, followed by the separa… |
| [Catalogue_Image_Token_Metadata_Delivery.md](../Catalogue_Image_Token_Metadata_Delivery.md) | 1 / 0 | Work-derived alt text, optional title caption and metadata for Catalogue images across targeted, full and captured… |
| [Catalogue_Navigation.md](../Catalogue_Navigation.md) | 5 / 3 | Require URL-carried gallery context for Catalogue document navigation, separate from Series membership and Media F… |
| [Catalogue_Navigation_Implementation.md](../Catalogue_Navigation_Implementation.md) | 2 / 0 | Explain current Catalogue query-driven navigation, ordered JSON inputs and page-local caching, and how to reuse th… |
| [Catalogue_Per_Work_Detail_Source.md](../Catalogue_Per_Work_Detail_Source.md) | 1 / 0 | Retired by the Gallery conversion on 2026-09-23. Converted images are independent Works; Gallery identity and memb… |
| [Catalogue_Report_Inputs.md](../Catalogue_Report_Inputs.md) | 2 / 0 | Refresh-owned Catalogue report inputs implemented, reviewed and closed; further verification continues during norm… |
| [Catalogue_Search.md](../Catalogue_Search.md) | 2 / 2 | This page records the historical known-item and metadata lookup for Works and Series. Its static runtime and data … |
| [Catalogue_Search_Policy.md](../Catalogue_Search_Policy.md) | 2 / 0 | site/assets/data/search/policy.json configures the public /catalogue/search/ route. |
| [Catalogue_Series_Publication.md](../Catalogue_Series_Publication.md) | 1 / 0 | Superseded proposal. Catalogue Deployment owns the current model without draft or published Works and Series. |
| [Catalogue_Work_Document_Links.md](../Catalogue_Work_Document_Links.md) | 0 / 0 | Use each Work ID as its Catalogue document ID, link to that document directly from Media View, and make Docs viewe… |
| [Catalogue_Work_Regeneration.md](../Catalogue_Work_Regeneration.md) | 1 / 0 | Completed Catalogue Work-record generation, full collection delivery and retained list navigation; accepted for cl… |
| [Catalogue_Works_Browsing_And_Search.md](../Catalogue_Works_Browsing_And_Search.md) | 3 / 1 | Refactor Catalogue Works to Studio-generated metadata with targeted entry updates after Save; Docs Viewer owns fil… |
| [Collection_Search_And_Site_Search.md](../Collection_Search_And_Site_Search.md) | 6 / 4 | Separate collection search, shared site-search and Recents coverage, and proposed editorial stars for a curated ho… |
| [Public_Catalogue_Data_Flow.md](../Public_Catalogue_Data_Flow.md) | 1 / 0 | Runtime map from public catalogue routes to static payloads, route modules, and source/build ownership. |
| [Public_Catalogue_Design.md](../Public_Catalogue_Design.md) | 1 / 0 | Durable product and presentation model for the public Works, Series, Work detail, recent, and catalogue search exp… |
| [Public_Route_Model.md](../Public_Route_Model.md) | 1 / 0 | Stable public catalogue shells, URLs, query state, URL ownership, and extension rules. |
| [UAC_1_Freeze_Legacy_Catalogue.md](../UAC_1_Freeze_Legacy_Catalogue.md) | 3 / 0 | Archive the current Catalogue site and R2 media while pausing Catalogue work and its Docs write follow-through. |
| [UAC_2_Catalogue_Examples.md](../UAC_2_Catalogue_Examples.md) | 2 / 0 | Prepared the external Catalogue output folders with representative JSON records and thumbnails for subsequent Docs… |
| [UAC_3A_Catalogue_Media_View.md](../UAC_3A_Catalogue_Media_View.md) | 1 / 0 | Retain the accepted single-Work proof and extend it with a small Series gallery to test interaction, data and toke… |
| [UAC_3B_Series_Works_Report.md](../UAC_3B_Series_Works_Report.md) | 2 / 0 | Show a small live Works-in-Series report inside an Analysis Works sub-document using the current report mechanism … |
| [UAC_3C_Detail_Subjects.md](../UAC_3C_Detail_Subjects.md) | 2 / 0 | Add exact Detail subjects and enable subject assignment directly in Analysis Works through the existing subject ed… |
| [UAC_3_Findings.md](../UAC_3_Findings.md) | 2 / 0 | Accepted Stage 3 conclusions support Stage 4 simplification; remaining consumer and selection questions need the f… |
| [UAC_3_Tokens_Reports_And_Data_Model.md](../UAC_3_Tokens_Reports_And_Data_Model.md) | 9 / 6 | Further token and specialised-tool design waits for Analysis stage structure/UI and resolution of the possible Cat… |
| [UAC_4_Catalogue_Data_And_Editors.md](../UAC_4_Catalogue_Data_And_Editors.md) | 5 / 0 | Completed canonical Catalogue and editor simplification; retain this delivery as the handoff for Stage 5 Studio ou… |
| [UAC_5_Studio_Catalogue_Output.md](../UAC_5_Studio_Catalogue_Output.md) | 4 / 0 | Complete Studio Catalogue output, accepted full data and durable guidance; ready for further Docs Viewer design. |
| [Works_Report_Concept_And_Architecture.md](../Works_Report_Concept_And_Architecture.md) | 2 / 0 | Refresh-owned Series membership and generated Context documents supply local Work Document Coverage. |

### Retired scope, source and publication migrations

Retain decision and cutover history. Treat scope/stage recipes and old storage paths as historical. Route current readers to Source Organisation, Builder and Catalogue Deployment.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Archive_Documents.md](../Archive_Documents.md) | 0 / 0 | Replace general document Copy and Move with Archive to Notes Working, including selected parents' descendants auto… |
| [Core_Definition_Baseline_v1.md](../Core_Definition_Baseline_v1.md) | 0 / 0 | Accepted initial boundary for shared Docs Viewer product behavior, composition-owned integrations, and the evidenc… |
| [Cross_System_Relationship_Map.md](../Cross_System_Relationship_Map.md) | 0 / 0 | distinguish subject aboutness, semantic mentions, Tag associations, Project State, Working-owned Copy/Delete/Publi… |
| [Deploy_And_Public_Cutover_Delivery.md](../Deploy_And_Public_Cutover_Delivery.md) | 2 / 0 | Deploy accepted Analysis documents and independent current Catalogue output into the tracked public site, verify t… |
| [Docs_Projection_Map.md](../Docs_Projection_Map.md) | 0 / 0 | show main-scope, sub-scope, management, search, and explicitly published Docs Viewer projections |
| [Document_Concept_And_Moment_IDs.md](../Document_Concept_And_Moment_IDs.md) | 2 / 0 | Accepted cleanup of Concept and Moment IDs, group metadata and dependent controls, preserving document identity, c… |
| [Document_Content_And_Metadata.md](../Document_Content_And_Metadata.md) | 4 / 0 | Separate Markdown content from canonical JSON metadata, with explicit ownership of document properties, collection… |
| [Document_Sub_Scope_Metadata.md](../Document_Sub_Scope_Metadata.md) | 2 / 0 | Automatically record sub-scope membership in document front matter across every scope, with destination-owned crea… |
| [Embedded_Detail_Documents.md](../Embedded_Detail_Documents.md) | 1 / 0 | Durable source, payload, URL, manifest, lifecycle, and runtime contract for report-hosted detail documents outside… |
| [External_Media_Workspace.md](../External_Media_Workspace.md) | 0 / 0 | retained originals, private managed media, and explicit public media projections through one external scope-namesp… |
| [Moment_IDs_And_Subjects.md](../Moment_IDs_And_Subjects.md) | 1 / 0 | Give the 56 original Moments stable three-digit identities and integrate them with document subjects. |
| [Pre_Publish_And_Publish_Delivery.md](../Pre_Publish_And_Publish_Delivery.md) | 2 / 0 | Restore source-driven Pre-publish preparation and acceptance through Publish without migrating existing snapshots. |
| [Preview_Stage_Consolidation.md](../Preview_Stage_Consolidation.md) | 3 / 0 | Replace Pre-publish and local Published with one read-only Preview snapshot prepared from Working. |
| [Processing_Project_Setup.md](../Processing_Project_Setup.md) | 1 / 0 | Bring the existing unfinished Processing projects into this repository, recover how they work, and establish a mai |
| [Public_Scopes.md](../Public_Scopes.md) | 4 / 0 | Local-to-public document and media URL flow plus management-isolation guarantees for public read-only routes. |
| [Public_Work_JSON_Review.md](../Public_Work_JSON_Review.md) | 2 / 0 | Complete and user-accepted; live Manage Work resolution and shared static preparation for Publish, Export and Prep… |
| [Publish_Workflow.md](../Publish_Workflow.md) | 7 / 0 | Distinguish accepted document publication from independent deployment of current Catalogue consumer data. |
| [Publishing_Workflow_Analysis_Media_Namespace.md](../Publishing_Workflow_Analysis_Media_Namespace.md) | 2 / 0 | Complete: both Analysis stages use one logical media namespace, 348 Working tokens are migrated, and exact stage r… |
| [Publishing_Workflow_Concept.md](../Publishing_Workflow_Concept.md) | 7 / 1 | purpose of dotlineform scope is to hold original 'working' documents. it is for: |
| [Publishing_Workflow_Content_Alignment.md](../Publishing_Workflow_Content_Alignment.md) | 1 / 0 | Complete: Works and Concepts are aligned, authoring content is consolidated in Working, and the stage review and d… |
| [Publishing_Workflow_Stage_Structure_And_UI.md](../Publishing_Workflow_Stage_Structure_And_UI.md) | 4 / 0 | Complete: Analysis stages and aligned content are active, Working document operations and stage-specific report re… |
| [Remove_Stage_Context_From_Search.md](../Remove_Stage_Context_From_Search.md) | 1 / 0 | Make Search JSON independent of stage and navigation routes before changing Search coverage or build ownership. |
| [Restore_Moments_In_Analysis.md](../Restore_Moments_In_Analysis.md) | 1 / 0 | Restore 56 Moments documents into an Analysis Working sub-scope, retaining their identities, R2 images and poetry … |
| [Retire_Studio_Tags.md](../Retire_Studio_Tags.md) | 3 / 0 | Retire Studio Tag management, adopt document-owned concept_id declarations and rename the semantic token domain to… |
| [Scope_Lifecycle.md](../Scope_Lifecycle.md) | 2 / 0 | Historical scope lifecycle design; scope and whole-collection lifecycle UI and services are retired. |
| [Search_Improvements.md](../Search_Improvements.md) | 0 / 2 | This feature is about improving the search relevance across Docs Viewer scopes by refining search policy, querying… |
| [Separate_Document_Content_Metadata.md](../Separate_Document_Content_Metadata.md) | 0 / 0 | Separate Markdown content from canonical JSON metadata, with explicit ownership of document properties, collection… |
| [Single_Publish_Delivery.md](../Single_Publish_Delivery.md) | 0 / 0 | Keep Working and Preview inside one Publish pipeline, remove stage context from Docs Viewer readers and authoring,… |
| [Sub_Scope_Customisation_Architecture.md](../Sub_Scope_Customisation_Architecture.md) | 1 / 0 | define the default docs_subscope report, unified registered aspects, access-safe projection, exact targets, browse… |
| [Sub_Scope_Documents_And_Media_Structure.md](../Sub_Scope_Documents_And_Media_Structure.md) | 2 / 0 | Give each sub-scope its own documents and media through the local Source, Generated and Published lifecycle. |
| [Sub_Scope_Public_And_Manage_Manifests.md](../Sub_Scope_Public_And_Manage_Manifests.md) | 2 / 0 | Historical public and Manage manifest design and Concepts customisation; current manifest ownership lives in Gener… |
| [Subject_Retirement.md](../Subject_Retirement.md) | 4 / 0 | Retire Folder placeholders, reserve draft for active authoring, and derive Projects associations from Catalogue re… |

### Reader, authoring and report deliveries

Retain design evidence or original acceptance context after checking the current owner. Remove active guidance that duplicates the latest reader, authoring and report contracts. Move the delivery as history without recasting it as a procedure.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Cross_Collection_Semantic_References.md](../Cross_Collection_Semantic_References.md) | 3 / 0 | Include sub-scope semantic-token occurrences in the existing scope-level token index and show their exact source d… |
| [Doc_Relationships.md](../Doc_Relationships.md) | 12 / 2 | Record eligible document relationships in separate links-by-id files during Working, including drafts, with coordi… |
| [Docs_Search_Relevance_Delivery.md](../Docs_Search_Relevance_Delivery.md) | 0 / 0 | test a few bounded corpus-adaptive signals for one shared relevance policy only after the completed all-scope full… |
| [Document_Context_Navigation.md](../Document_Context_Navigation.md) | 7 / 0 | Propose previous/next navigation through the scope-level document hierarchy; sub-scope and Catalogue navigation ar… |
| [Document_Relationships_Delivery.md](../Document_Relationships_Delivery.md) | 3 / 0 | Accepted and closed on 2026-09-10. Scope-wide Analysis Working document links and Links View are complete; durable… |
| [Document_Rendering_And_Projection.md](../Document_Rendering_And_Projection.md) | 0 / 0 | Remove redundant Working public-manifest generation and dependencies while preserving existing rendering and field… |
| [Document_View_And_Return_Navigation_Delivery.md](../Document_View_And_Return_Navigation_Delivery.md) | 1 / 1 | Completed exact document reader, independent Index, committed list updates and two retained views with one immedia… |
| [Gallery_Design.md](../Gallery_Design.md) | 7 / 0 | Record the resolved Media View gallery design, its durable destination and the separately owned public distributio… |
| [Gallery_List_Design.md](../Gallery_List_Design.md) | 6 / 0 | Design an insertable, bounded list of a Series' Works or a Work's Details, driven by document subject, with shared… |
| [Image_Token_Delivery.md](../Image_Token_Delivery.md) | 1 / 0 | Make shared Add image insert an editable semantic image token, with builder-owned presentation and no migration of… |
| [Info_Panel_Links_And_Pinning_Delivery.md](../Info_Panel_Links_And_Pinning_Delivery.md) | 3 / 0 | Open an always-pinned document panel from the generated related-links section, showing only its title, optional su… |
| [Links_View.md](../Links_View.md) | 5 / 0 | Historical single-document Links presentation, superseded by Related Links in generated document content. |
| [Links_View_Semantic_Tokens_Delivery.md](../Links_View_Semantic_Tokens_Delivery.md) | 1 / 0 | Superseded media-entry proposal. Info Panel Related Links And Pinning now owns document-only semantic connections,… |
| [Media_Links_And_Series_Galleries_Delivery.md](../Media_Links_And_Series_Galleries_Delivery.md) | 1 / 0 | Complete Work, Detail and Series Media View links and Catalogue-backed Series galleries while preserving Work/Deta… |
| [Media_View_Text_Links_And_Catalogue_Images.md](../Media_View_Text_Links_And_Catalogue_Images.md) | 4 / 0 | Accepted Work text links and Work/Detail images using current Catalogue data and shared Media View activation; clo… |
| [Moments_Images_And_Thumbnails_Delivery.md](../Moments_Images_And_Thumbnails_Delivery.md) | 0 / 0 | Enhance shared Add image with document-based naming and optional thumbnails in a registered thumbs media family, a… |
| [Public_Index_Search_Scopes.md](../Public_Index_Search_Scopes.md) | 1 / 0 | Shared Manage and Public search coverage, with a scope button in the main Index that shows the destination of the … |
| [Related_Links_Delivery.md](../Related_Links_Delivery.md) | 1 / 0 | Deliver the editable related-links directive and retire the separate per-document Links view. |
| [Reorder_Docs_Delivery.md](../Reorder_Docs_Delivery.md) | 2 / 0 | Deliver canonical ordinary document hierarchy and order with one Position modal, complete document-operation integ… |
| [Route_Ready_State_Audit.md](../Route_Ready_State_Audit.md) | 2 / 0 | Do current Studio and Docs Viewer templates expose one consistent app-owned ready/busy root? |
| [Save_Build_Optimisations.md](../Save_Build_Optimisations.md) | 1 / 0 | Status: **complete**. Steps 1–5 are delivered and reviewed. On 2026-10-07 the user retired Documents Linking Here … |
| [Scope_Links_Delivery.md](../Scope_Links_Delivery.md) | 1 / 0 | Aggregate prepared Analysis Working document relationships into links.json at scope rebuild and display a local tw… |
| [Source_Editor_And_Token_Modals_Delivery.md](../Source_Editor_And_Token_Modals_Delivery.md) | 2 / 0 | Edit complete Markdown including front matter and reopen token modals with existing values, removing Source's meta… |

## Delete candidates (40)

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Analysis_Broken_Links_Report.md](../Analysis_Broken_Links_Report.md) | 2 / 0 | Superseded Analysis Working audit delivery. [Broken Links Script](../Broken_Links_Script.md) |
| [Analysis_Documents.md](../Analysis_Documents.md) | 1 / 0 | **First pass.** Retired report marker. The implementation and host were removed; the catalogue of current reports has its own owner. [Reports](../Reports.md) |
| [Bulk_Add_Work.md](../Bulk_Add_Work.md) | 0 / 0 | **First pass.** Retired Excel-based bulk authoring. The supported Work import procedure is independent. [Catalogue Work Editor](../Catalogue_Work_Editor.md) |
| [Catalogue_Drafts.md](../Catalogue_Drafts.md) | 0 / 0 | **First pass.** Outdated recovery recipe for `/studio/catalogue-status/` and canonical Work/Series drafts. [Catalogue Deployment](../Catalogue_Deployment.md) |
| [Catalogue_Search_Build_Config.md](../Catalogue_Search_Build_Config.md) | 2 / 0 | Registry path refers to the former standalone Catalogue search builder. Retain the legacy search context via Catalogue Archive. [Catalogue Archive](../Catalogue_Archive.md) |
| [Catalogue_Subject_Shortcut.md](../Catalogue_Subject_Shortcut.md) | 0 / 0 | **First pass.** The Subject-based picker shortcut was retired. Current picker and thumbnail behavior have maintained owners. [Semantic Tokens Source Editor UI](../Semantic_Tokens_Source_Editor_UI.md) |
| [Catalogue_Token_Links_Delivery.md](../Catalogue_Token_Links_Delivery.md) | 0 / 0 | Completed token-to-relationship delivery. The surviving relationship and token rules have maintained owners. [Semantic Tokens Architecture](../Semantic_Tokens_Architecture.md) |
| [Collection_Icons_Delivery.md](../Collection_Icons_Delivery.md) | 2 / 0 | Collection icon implementation record. Shared configured icon rules now live in source organisation guidance. [Source Organisation](../Source_Organisation.md) |
| [Context_Actions_Menu.md](../Context_Actions_Menu.md) | 0 / 0 | Superseded Actions menu delivery. It still lists removed workspace operations. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Copy_Working_Search_Into_Preview.md](../Copy_Working_Search_Into_Preview.md) | 2 / 0 | Completed handoff for copying saved Search through publication. Current Search adds scoped output and owns exact queued bytes. [Docs Search Index](../Docs_Search_Index.md) |
| [Current_Copy_To_Analysis_And_Publish_Actions.md](../Current_Copy_To_Analysis_And_Publish_Actions.md) | 2 / 0 | **First pass.** Describes the retired Copy to Analysis route and publication workflow. [Source Organisation](../Source_Organisation.md) |
| [Docs_Data.md](../Docs_Data.md) | 0 / 0 | **First pass.** Documents a removed repository Studio scope source tree. [Source Organisation](../Source_Organisation.md) |
| [Docs_Media_Report_Refactor.md](../Docs_Media_Report_Refactor.md) | 0 / 0 | Superseded report refactor. Saved inspection, refresh and Finder behavior have a current owner. [Media And Asset Handling](../Media_And_Asset_Handling.md) |
| [Document_Actions_And_Toolbar.md](../Document_Actions_And_Toolbar.md) | 1 / 0 | Completed action/toolbar delivery. Redirect any remaining placement links to the current runtime. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Document_Edit_Menu.md](../Document_Edit_Menu.md) | 0 / 0 | Superseded Edit menu delivery. Current controls and retired Subject history are documented elsewhere. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Document_Index_Navigation_Delivery.md](../Document_Index_Navigation_Delivery.md) | 0 / 0 | Completed Index shortcut delivery. Exact navigation and saved list state are covered by Runtime. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Document_List_Date_Precision.md](../Document_List_Date_Precision.md) | 0 / 0 | Completed browser day-precision change. The manifest and Recent contracts describe current date fields. [Generated Data Contracts](../Generated_Data_Contracts.md) |
| [Document_View_And_Return_Navigation_Handoff.md](../Document_View_And_Return_Navigation_Handoff.md) | 1 / 0 | **First pass.** Temporary implementation handoff for an accepted navigation delivery. The runtime contract and separate delivery history remain available. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Gallery_And_Series_Definition_Editing.md](../Gallery_And_Series_Definition_Editing.md) | 0 / 0 | The current Work Editor guide describes definitions, Series relevance and deletion controls. This delivery predates the Gallery Browser refinements. [Catalogue Work Editor](../Catalogue_Work_Editor.md) |
| [Icon_Tokens_Delivery.md](../Icon_Tokens_Delivery.md) | 1 / 0 | Separate Icon Tokens delivery record. The maintained token guide carries authoring and export behaviour. [Icon Tokens](../Icon_Tokens.md) |
| [Index_Context_Menu.md](../Index_Context_Menu.md) | 0 / 0 | Old Index menu record describes commands that later moved to Collection Actions. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Index_Search_And_Recent.md](../Index_Search_And_Recent.md) | 0 / 0 | Completed Index/Search/Recent handoff. Current Search scopes and the shared reader have a maintained owner. [Docs Viewer Search](../Docs_Viewer_Search.md) |
| [Links_View_Design.md](../Links_View_Design.md) | 1 / 0 | Completed design proof for a retired view. Preserve the separate Links View history and route users to Related Links. [Related Links](../Related_Links.md) |
| [Public_Work_JSON_Handoff.md](../Public_Work_JSON_Handoff.md) | 1 / 0 | **First pass.** Explicitly retired Work JSON handoff. Use the durable contracts for current behavior and retain the larger review for history. [Generated Data Contracts](../Generated_Data_Contracts.md) |
| [Publishable_Field.md](../Publishable_Field.md) | 1 / 0 | **First pass.** Describes the retired `publishable` field as a current requirement. The replacement is explicit Draft plus the ordinary publication exclusion list. [Source Organisation](../Source_Organisation.md) |
| [Retire_Public_Document_Locations.md](../Retire_Public_Document_Locations.md) | 3 / 0 | Retired public location index and Catalogue URL refresh. The exact by-ID routing contract already covers the result. [Generated Data Contracts](../Generated_Data_Contracts.md) |
| [Scope_Configured_Authoring_Controls.md](../Scope_Configured_Authoring_Controls.md) | 4 / 0 | Superseded scope-based availability plan. Current action context and toolbar placement are maintained in Runtime. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) |
| [Scope_Lifecycle_Endpoints.md](../Scope_Lifecycle_Endpoints.md) | 2 / 0 | Former scope CRUD request and response examples. Endpoints are explicitly retired; keep the separate lifecycle design if historical context matters. [Source Organisation](../Source_Organisation.md) |
| [Search_Field_Styling_Delivery.md](../Search_Field_Styling_Delivery.md) | 0 / 0 | Completed styling delivery. The reusable Search Field guide owns the current control. [Search Fields](../Search_Fields.md) |
| [Semantic_Tokens_Report.md](../Semantic_Tokens_Report.md) | 4 / 0 | **First pass.** A tombstone for the retired Semantic Tokens report. Current token parsing and relationship behavior have a maintained guide. [Semantic Tokens Architecture](../Semantic_Tokens_Architecture.md) |
| [Series_Tag_Editor.md](../Series_Tag_Editor.md) | 1 / 0 | Retired Studio Tag editor. Preserve the retirement decision in the Tags retirement record if needed. [Retire Studio Tags](../Retire_Studio_Tags.md) |
| [Series_Tags.md](../Series_Tags.md) | 0 / 0 | Retired Studio Tag data model. Preserve the cutover record in the archive rather than keeping this as live instructions. [Retire Studio Tags](../Retire_Studio_Tags.md) |
| [Source_Config_Endpoints.md](../Source_Config_Endpoints.md) | 1 / 0 | **First pass.** Tombstone for removed settings endpoints. The exact design-time default belongs in the current configuration guide. [Configuration And Extension Points](../Configuration_And_Extension_Points.md) |
| [Source_Config_Report.md](../Source_Config_Report.md) | 0 / 0 | **First pass.** Small tombstone for the removed Source Config report and host. [Reports](../Reports.md) |
| [Source_Editor_Toolbar.md](../Source_Editor_Toolbar.md) | 1 / 0 | Completed Source toolbar change. Source directives and control ownership have a separate maintained owner. [Source Editor Scripts](../Source_Editor_Scripts.md) |
| [Sub_Scope_Report_Reparenting.md](../Sub_Scope_Report_Reparenting.md) | 1 / 0 | Former stage-bound report reparenting fix. Current placement and host authority belong to Working navigation and collection registration. [Source Organisation](../Source_Organisation.md) |
| [Subject_Associations_Manifest_Delivery.md](../Subject_Associations_Manifest_Delivery.md) | 0 / 0 | Completed removal of Subject-associations artifacts. Keep the larger Subject retirement record for cutover history. [Subject Retirement](../Subject_Retirement.md) |
| [Usage_Index.md](../Usage_Index.md) | 1 / 0 | **First pass.** Retired usage-index marker. Current token and relationship authorities cover the surviving behavior. [Semantic Tokens Architecture](../Semantic_Tokens_Architecture.md) |
| [Work_List_And_Bulk_Gallery_Editing.md](../Work_List_And_Bulk_Gallery_Editing.md) | 0 / 0 | Earlier bulk membership delivery. The Work Editor now documents both Series replacement and Gallery net changes. [Catalogue Work Editor](../Catalogue_Work_Editor.md) |
| [Works_Collection_Browsing.md](../Works_Collection_Browsing.md) | 0 / 0 | Superseded Works browsing delivery. Current Context/collection list behavior and report ownership are documented separately. [Sub Scope Index Architecture](../Sub_Scope_Index_Architecture.md) |
