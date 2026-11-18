---
draft: false
doc_id: d-20261117-213339-b5aa67
title: Site Workflow Guide Triage
added_date: "2026-11-17 21:33:39"
last_updated: "2026-11-18"
summary: Final disposition and walkthrough evidence for the 290 Studio documents reviewed in the Site Workflow Guide delivery.
parent_id: d-20261117-213339-8c181b
---
# Site Workflow Guide Triage

Inventory opened on 17 November 2026 and closed on 18 November 2026. It records 136 retained files, 137 archived files and 17 retirements. Original categories and dependency counts remain below for context. Each row records its final disposition. [Site Workflow Guide delivery](../deliveries/Site_Workflow_Guide.md)

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

The **First pass** markers identify the earliest retirement batch. The closing pass consolidated overlapping command and import references, archived significant rationale and evidence, and kept independently useful current references and proposals. A retained delivery with an open manual acceptance gate remains reviewable under its own owner.

## Guide Walkthrough

On 18 November, the new-reader route started from the repository README and Dev Home, then followed all six chapters. It checked local startup, the ordinary document and collection choices, Catalogue Save through Regenerate, publication versus release, and the return paths from Search, Catalogue and Media View. Reader checks used the current source and tracked public artifacts. The guide now gives default addresses, names the Manage enablement setting and explains how to get back to Index Actions from a results view. [Guide contents](../../guide/README.md)

The authoring paths led to obsolete scope examples in Docs Images And Assets and outdated hierarchy and Recent notes in Builder. Those procedures now follow the configured media owner, the independent Thumb action, the authored Index order and the current discovery files. Source Organisation now identifies exact queued media removals and selected Catalogue presentation during Publish. The Docs Media R2 report remains available for manual investigation. [Docs Images And Assets](../Docs_Images_And_Assets.md) · [Builder](../Builder.md#source-contract) · [Source Organisation](../Source_Organisation.md#media-ownership)

For the maintainer's route, a disposable copy set the homepage to the already available Concepts document, `d-20260624-213316-478639`. Config-only generation put that ID in both canonical browser files, site-code-update changed one public copy, and projection and site validation passed. An intentionally missing target caused site validation to report its exact by-ID path. Restoring the original setting and regenerating all copies passed both checks again. The route-selection code was read for the bare-versus-explicit URL check. Browser interaction, live authoring, Publish and Pages deployment were outside this walkthrough. [Change the system safely](../../guide/Change_The_System_Safely.md)

## Keep current (60)

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Broken_Links_Script.md](../Broken_Links_Script.md) | 10 / 0 | Retained. Saved Broken Links audit and procedure. |
| [Browser_Smoke_Testing.md](../Browser_Smoke_Testing.md) | 2 / 0 | Retained. Required browser-check policy and evidence boundary. |
| [Builder.md](../Builder.md) | 45 / 0 | Retained for generation and selected publication. The walkthrough corrected the ordinary hierarchy, Recent date and named-collection HTML token references. |
| [Button_Placement.md](../Button_Placement.md) | 1 / 0 | Retained. Keep as the focused reference for button placement. |
| [CSS_Ownership.md](../CSS_Ownership.md) | 5 / 0 | Retained. Shared reader style ownership. |
| [Catalogue_Archive.md](../Catalogue_Archive.md) | 5 / 0 | Retained and updated as the entry point for the frozen routes, static Search, and historical reader references. Links to the guide for active browsing. |
| [Catalogue_Deployment.md](../Catalogue_Deployment.md) | 31 / 0 | Retained for exact queued transfers. Moved its parent from the archived unification feature to Catalogue Architecture. |
| [Catalogue_Field_Registry.md](../Catalogue_Field_Registry.md) | 4 / 0 | Retained. Catalogue field and output families. |
| [Catalogue_Indexes_And_Payloads.md](../Catalogue_Indexes_And_Payloads.md) | 14 / 0 | Retained for generated Work and Gallery payloads. Corrected the staging and ready-media locations. |
| [Catalogue_Media_Pipeline_Config.md](../Catalogue_Media_Pipeline_Config.md) | 7 / 0 | Retained. Keep as the focused reference for catalogue media pipeline config. |
| [Catalogue_Media_View.md](../Catalogue_Media_View.md) | 27 / 0 | Retained for the Work/Gallery adapter, Context links and exact grid return rules. Moved its parent from the archived navigation proposal to [Catalogue Architecture](../Catalogue_Architecture.md). Chapter 5 carries the reader workflow. |
| [Catalogue_Save_And_Refresh.md](../Catalogue_Save_And_Refresh.md) | 37 / 0 | Retained for queue state, media handoff and Regenerate completion. Links the original exact-ID delivery for the rationale and acceptance history. |
| [Catalogue_Services.md](../Catalogue_Services.md) | 3 / 0 | Retained. Keep as the focused reference for catalogue services. |
| [Catalogue_Shuffle_Randomness.md](../Catalogue_Shuffle_Randomness.md) | 2 / 0 | Retained. Shuffle stock origin, replacement and reader behavior. |
| [Catalogue_Work_Editor.md](../Catalogue_Work_Editor.md) | 12 / 0 | Retained. Keep for Work editor, bulk editing, media selection and Gallery dialog details. |
| [Catalogue_Works.md](../Catalogue_Works.md) | 8 / 0 | Retained. Keep as the focused reference for catalogue works. |
| [Development_Checklist.md](../Development_Checklist.md) | 17 / 0 | Retained. Repository implementation guardrails. |
| [Development_Workflow.md](../Development_Workflow.md) | 5 / 0 | Retained. Development lifecycle and delivery workflow. |
| [Docs_Images_And_Assets.md](../Docs_Images_And_Assets.md) | 2 / 0 | Retained for image and download authoring. Replaced retired scope examples with current logical paths, documented original-resolution selection and pointed thumbnail changes to Thumb. |
| [Docs_Import.md](../Docs_Import.md) | 7 / 2 | Retained for collection import and the return handoff. Corrected the obsolete `publishable` guidance to describe Draft on new authored imports. |
| [Docs_Search_Index.md](../Docs_Search_Index.md) | 8 / 0 | Retained. Search artifact format and eligibility. |
| [Docs_Search_Tokenizer.md](../Docs_Search_Tokenizer.md) | 2 / 0 | Retained. Search term normalization. |
| [Docs_Viewer_Search.md](../Docs_Viewer_Search.md) | 8 / 2 | Retained. Keep for exact Search scope switching, query and result controls. Chapter 5 routes readers to it. |
| [Document_Diagrams.md](../Document_Diagrams.md) | 9 / 0 | Retained. Keep as the focused reference for document diagrams. |
| [Document_Identity.md](../Document_Identity.md) | 2 / 0 | Retained. Stable document identity. |
| [Document_Image_Detail.md](../Document_Image_Detail.md) | 3 / 0 | Retained. Current opt-in image detail procedure. |
| [Export.md](../Export.md) | 10 / 0 | Retained. Current collection HTML export and media behavior. |
| [File_Picker.md](../File_Picker.md) | 2 / 0 | Retained. Keep as the focused reference for file picker. |
| [Folder_Picker.md](../Folder_Picker.md) | 2 / 0 | Retained. Keep as the focused reference for folder picker. |
| [Generated_Data_Contracts.md](../Generated_Data_Contracts.md) | 30 / 0 | Retained. Generated artifact and reader data contracts. |
| [Generated_Read_Endpoints.md](../Generated_Read_Endpoints.md) | 2 / 0 | Retained. Read-only generated API boundary. |
| [GitHub_Actions.md](../GitHub_Actions.md) | 3 / 0 | Retained for Pages validation, release and recovery. Corrected the PR trigger summary against the checked workflow. |
| [HTML_Import_Mapping.md](../HTML_Import_Mapping.md) | 3 / 0 | Retained. Keep as the focused reference for html import mapping. |
| [Icon_Tokens.md](../Icon_Tokens.md) | 5 / 0 | Retained. Keep as the focused reference for icon tokens. |
| [Local_Runners.md](../Local_Runners.md) | 3 / 0 | Retained for default addresses and supervision. Documented the Manage capability and how to confirm it at startup. |
| [Local_Setup_Public_Site_Preview.md](../Local_Setup_Public_Site_Preview.md) | 2 / 0 | Retained. Keep for the static preview wrapper, options and deploy-root checks. |
| [Media_And_Asset_Handling.md](../Media_And_Asset_Handling.md) | 38 / 0 | Retained. Media ownership, attachment procedures and R2 report. |
| [Package_Export_Metadata.md](../Package_Export_Metadata.md) | 2 / 0 | Retained. Prepare/return provenance contract. |
| [Package_Prepare.md](../Package_Prepare.md) | 12 / 0 | Retained. Collection package procedure. |
| [Package_Prepare_Profiles.md](../Package_Prepare_Profiles.md) | 4 / 0 | Retained. Package profile shapes. |
| [Package_Prepare_Script.md](../Package_Prepare_Script.md) | 4 / 0 | Retained. Working package producer. |
| [Planned_Features.md](../Planned_Features.md) | 25 / 53 | Retained. Current plan and proposal routing. |
| [Public_Docs_Route_Shell.md](../Public_Docs_Route_Shell.md) | 1 / 0 | Retained. Active public root route shell. |
| [Pytest.md](../Pytest.md) | 0 / 0 | Retained. Required pytest policy reference. Confirm selected fixtures against current owners. |
| [Record_List_And_Actions.md](../Record_List_And_Actions.md) | 3 / 0 | Retained. Keep as the focused reference for record list and actions. |
| [Related_Links.md](../Related_Links.md) | 28 / 2 | Retained. Authored Related Links representation and generation. |
| [Reports.md](../Reports.md) | 25 / 1 | Retained. Current report inventory and procedures. Review individual report evidence separately. |
| [Run_Checks.md](../Run_Checks.md) | 6 / 0 | Retained. Retains exact lint, profile runner and projection commands. Updated the projection note to point to the current release sequence. |
| [Search_Fields.md](../Search_Fields.md) | 3 / 0 | Retained. Keep as the focused reference for search fields. |
| [Search_List.md](../Search_List.md) | 2 / 0 | Retained. Keep as the focused reference for search list. |
| [Selectable_List.md](../Selectable_List.md) | 2 / 0 | Retained. Keep as the focused reference for selectable list. |
| [Shared_UI.md](../Shared_UI.md) | 1 / 6 | Retained. Keep as the focused reference for shared ui. |
| [Source_Editor_Endpoints.md](../Source_Editor_Endpoints.md) | 11 / 0 | Retained. Source editor request and response owner. |
| [Source_Mutation_Endpoints.md](../Source_Mutation_Endpoints.md) | 4 / 0 | Retained. Working mutation endpoint reference. |
| [Source_Organisation.md](../Source_Organisation.md) | 46 / 0 | Retained for canonical storage and publication. Corrected the selected Catalogue presentation and queued media removal descriptions. |
| [Sub_Scope_Index_Architecture.md](../Sub_Scope_Index_Architecture.md) | 18 / 1 | Retained for collection browsing and Book structure. Updated normal Catalogue Regenerate and separated the first browsing delivery's acceptance from the current publication path. |
| [Test_Contract_Discipline.md](../Test_Contract_Discipline.md) | 28 / 0 | Retained. Binding test scope and coverage policy. |
| [Testing.md](../Testing.md) | 26 / 5 | Retained. Required testing guide and evidence limits. |
| [Toolbar_Icons.md](../Toolbar_Icons.md) | 4 / 0 | Retained. Keep as the focused reference for toolbar icons. |
| [Word_Import_Style_Mapping.md](../Word_Import_Style_Mapping.md) | 2 / 0 | Retained. Keep as the focused reference for word import style mapping. |

## Needs review (96)

### Entry points

Repair the reader’s route to maintained owners. Check all scope, storage, deployment and capability claims against current configuration. Consolidate hub pages that send readers to the same destination.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Dev_Home.md](../Dev_Home.md) | 0 / 9 | Retained and updated. Routes readers to the workflow guide and chapter 6, names the current Studio documentation root and keeps the development references. |
| [Docs_Viewer.md](../Docs_Viewer.md) | 5 / 49 | Retained and updated as the task and reference entry point. Its opening now carries the three-surface overview and links to the guide and Runtime. |
| `Docs_Viewer_Overview.md` | 2 / 0 | Retired. Retired after checking repository and Working source paths, document IDs and parent references. [Docs Viewer](../Docs_Viewer.md) covers orientation, [Runtime](../Docs_Viewer_Runtime.md) covers route authority and [Docs Review](../Docs_Review.md) covers the package workflow. |
| [Docs_Viewer_Runtime.md](../Docs_Viewer_Runtime.md) | 40 / 5 | Retained. Corrected the explicit discovery and Publish completion rows and removed the retired full-rebuild and Settings guidance from that section. |
| [Site.md](../Site.md) | 2 / 6 | Retained and updated. Routes to the active root reader, the publication guide and the separately identified frozen Catalogue references. |
| `Site_Overview.md` | 1 / 0 | Retired. Retired after checking repository and Working source paths, document IDs and parent references. [Site](../Site.md) and the guide cover the active site and release, [Site Shell Runtime](../Site_Shell_Runtime.md) covers shell ownership, and [Catalogue Archive](../Catalogue_Archive.md) covers the old routes. |
| [Source_Tree_Ownership.md](../Source_Tree_Ownership.md) | 9 / 0 | Retained as the directory and cross-project ownership reference. Updated Working and Preview storage, direct publication destinations and the native app boundary. The workflow guide carries the release sequence. |
| [Studio.md](../Studio.md) | 2 / 19 | Retained and updated. Routes to the Catalogue chapter and the current Work Editor and Series controls. |
| `Studio_Overview.md` | 2 / 0 | Retired. Retired after path, document ID and parent checks. [Studio](../Studio.md) is the entry point. [Studio Runtime](../Studio_Runtime.md) and [Studio Config JSON](../Studio_Config_JSON.md) retain the route and extension guidance. |
| [Sub_Scopes.md](../archive/Sub_Scopes.md) | 0 / 3 | Archived. Introduction to the former sub-scope model. It records why collection documents are browsed through a host while keeping their own exact identities. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [System_Architecture.md](../System_Architecture.md) | 1 / 7 | Retained. Routes current ownership questions to the guide and keeps the earlier system vision as history. |

### Configuration, execution and operator commands

Check shown paths, procedure and interface names against the current scripts, config and router. Keep one responsibility per guide. Review remote-write and recovery instructions before using them.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Cloud_Environments.md](../Cloud_Environments.md) | 3 / 0 | Retained. Owns bootstrap and Codespaces notes. Names independent Docs and Projects roots. |
| [Configuration_And_Extension_Points.md](../Configuration_And_Extension_Points.md) | 16 / 0 | Retained as the exact configuration and projection reference. The walkthrough exercised its config-only command, projection and recovery in a disposable copy. |
| [Configuration_Map.md](../Configuration_Map.md) | 3 / 0 | Retained. Updated current Search and runtime projection owners and identified the older projection audit separately. |
| [Dependencies.md](../Dependencies.md) | 0 / 0 | Retained. Documents the specific packages used for Docs conversion, rendering and native media. Runtime Dependencies owns repo-wide setup. |
| [Endpoint_Overview.md](../Endpoint_Overview.md) | 5 / 9 | Retained. Current route index points to exact create/import, local folder links, Review and other endpoint owners. |
| [Health_And_Capabilities_Endpoints.md](../Health_And_Capabilities_Endpoints.md) | 1 / 0 | Retained. Verified both local GETs against the service and removed the former scope capability response. |
| [Local_Setup.md](../Local_Setup.md) | 3 / 6 | Retained as the first-run entry point. Updated the app roles and linked runner addresses. |
| [Local_Setup_Environment.md](../Local_Setup_Environment.md) | 1 / 0 | Retained for local settings. Replaced obsolete external scope roots and documented the actual environment precedence for the builder and Docs service. |
| `Local_Setup_GitHub_And_Codex_Notes.md` | 1 / 0 | Retired. Consolidated local-toolchain versus Pages guidance in [Local Setup](../Local_Setup.md). Existing repo instructions retain interpreter and command policy. |
| [Local_Setup_Recovery.md](../Local_Setup_Recovery.md) | 1 / 0 | Retained. Separate operator recovery for a broken local toolchain after macOS or Xcode changes. |
| [Local_Setup_Toolchain.md](../Local_Setup_Toolchain.md) | 1 / 0 | Retained. Machine setup and interpreter-selection details belong here, with exact dependency ownership in Runtime Dependencies. |
| [Local_Studio_APIs.md](../Local_Studio_APIs.md) | 6 / 0 | Retained for exact HTTP reads, mutation requests and adapter boundaries. Corrected Series deletion and listed the batch-create and Gallery mutations. |
| [Local_Studio_App.md](../Local_Studio_App.md) | 5 / 1 | Retained for server ownership and runtime configuration. |
| [Local_Studio_Routes.md](../Local_Studio_Routes.md) | 4 / 0 | Retained for the mounted editor route and static/API path boundaries. |
| [Management_Services.md](../archive/Management_Services.md) | 2 / 3 | Archived. Earlier standalone service and local folder-link boundary. Current Working storage and service responsibilities are mapped from Management Operations. [Maintained reference](../Configuration_And_Extension_Points.md#workspace-and-target-contracts) |
| [Projection_Contract.md](../Projection_Contract.md) | 6 / 0 | Retained as the cross-system owner map. Replaced scope-era paths and the Search Build Pipeline pointer with the current Catalogue, Docs Search, runtime projection and deploy validation owners. |
| [Projection_Contract_Validation.md](../archive/Projection_Contract_Validation.md) | 2 / 0 | Archived. Former cross-boundary projection audit and manifest. It records what the scope-era audit covered and the limits of that evidence. [Maintained reference](../Run_Checks.md) |
| [Publish_Media_To_R2.md](../Publish_Media_To_R2.md) | 8 / 0 | Retained for exact CLI maintenance. Corrected Working paths and document-ID arguments and routed normal queued distribution to [Catalogue Deployment](../Catalogue_Deployment.md). |
| [Route_Dispatch_Scripts.md](../archive/Route_Dispatch_Scripts.md) | 1 / 0 | Archived. Earlier route and adapter inventory. It records the boundary between HTTP framing and command execution. [Maintained reference](../Scripts_Overview.md) |
| [Route_Ready_State.md](../Route_Ready_State.md) | 3 / 0 | Retained. Defines root ownership and the normal ready/busy contract. The earlier audit is archived with its original scope. |
| [Runtime_Dependencies.md](../Runtime_Dependencies.md) | 4 / 0 | Retained. Repo-wide dependency and optional tool ownership, with checked manifests authoritative for versions. |
| [Runtime_Module_Ownership.md](../Runtime_Module_Ownership.md) | 8 / 0 | Retained. Traces the active browser entrypoints and module dependencies. The script map covers Python services. |
| [Scripts.md](../Scripts.md) | 1 / 0 | Retained. A cross-app command index, with current Working and Catalogue owners and historical audits out of the active command list. |
| [Scripts_Overview.md](../Scripts_Overview.md) | 2 / 8 | Retained. Consolidated the active Manage service, dispatch, read, rebuild and import owners in one code map. |
| [Service_Entrypoints.md](../archive/Service_Entrypoints.md) | 1 / 0 | Archived. Detailed service-launcher reference from the earlier script inventory. The current runnable commands and module dispatch are in Local Runners and the consolidated owner map. [Maintained reference](../Scripts_Overview.md) |
| [Site_Consistency_Audit.md](../archive/Site_Consistency_Audit.md) | 2 / 0 | Archived. Audit of the former standalone Catalogue site. The commands below are historical, including scope-era series, Detail and tag checks. [Maintained reference](../Run_Checks.md) |
| [Site_Shell_Runtime.md](../Site_Shell_Runtime.md) | 1 / 0 | Retained. Tracks current root and 404 shell assets, early theme bootstrap and separation from the frozen Catalogue. |
| [Studio_Config_JSON.md](../Studio_Config_JSON.md) | 3 / 0 | Retained for the checked route registry, runtime configuration projection and extension guidance. |
| [Studio_Domain_Config.md](../Studio_Domain_Config.md) | 2 / 1 | Retained. Routes to the focused field registry and distinguishes its inventory from current Save and Refresh selection. |
| [Studio_Read_And_Save_Flow.md](../Studio_Read_And_Save_Flow.md) | 2 / 0 | Retained and updated for canonical reads, Studio mutation completion and the separate Working handoff. |
| [Studio_Runtime.md](../Studio_Runtime.md) | 7 / 2 | Retained for browser boot, route ownership and extension. |
| [UI_Status.md](../UI_Status.md) | 0 / 0 | Retained. Corrected the free-text status and current artwork mapping. Draft remains a separate readiness field. |

### Docs authoring, routing and packages

Check the current Working, collection-aware API and UI. Consolidate overlapping endpoint or report pages around the owning procedure. Mark accepted legacy examples and unreviewed test coverage as historical.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Audit_Scripts.md](../archive/Audit_Scripts.md) | 1 / 0 | Archived. Former Broken Links adapter and corpus audit script map. Its current operator and implementation references are gathered under Broken Links. [Maintained reference](../Scripts_Overview.md) |
| [Broken_Links.md](../Broken_Links.md) | 5 / 0 | Retained. Report entry points to the saved Working audit and its maintained procedure. |
| [Create_And_Import_Endpoints.md](../Create_And_Import_Endpoints.md) | 3 / 0 | Retained. Documents exact local Working create, native import and staged import routes. Removed scope-transfer examples. |
| [Doc_Navigation.md](../Doc_Navigation.md) | 5 / 3 | Retained. Tracks the completed Index ordering work and separate ordinary-tree navigation proposal. |
| [Docs_Import_Architecture.md](../archive/Docs_Import_Architecture.md) | 6 / 0 | Archived. Original import architecture and conversion delivery. It preserves the rationale for closed source discovery, normalized intent, preview and per-operation media preparation. The active import guide carries the current Working contract. [Maintained reference](../Docs_Import.md#implementation-boundary) |
| [Docs_Review.md](../Docs_Review.md) | 8 / 0 | Retained. Owns the independent package-local reader and the boundary between inspecting and explicitly importing a return. |
| [Docs_Review_Endpoints.md](../Docs_Review_Endpoints.md) | 3 / 0 | Retained. Exact package-rooted Review capabilities, file reads, Build and source opening are distinct from Manage. |
| [Import_Scripts.md](../archive/Import_Scripts.md) | 1 / 0 | Archived. Earlier staged-import script map. It preserves the separation between the route adapter, format converters and checked apply. [Maintained reference](../Scripts_Overview.md) |
| [Info_Panel.md](../Info_Panel.md) | 6 / 0 | Retained. Current generated Related Links pinning, content, host lifetime and editor boundary. |
| [Management_Operations.md](../Management_Operations.md) | 5 / 0 | Retained. Exact local write, deletion and recovery boundaries, with a consolidated local folder-link section and retired Subject instructions removed. |
| [Package_Return_Parser.md](../Package_Return_Parser.md) | 1 / 0 | Retained. Documents the current staged parser CLI and result codes. Review and apply retain independent owners. |
| [Package_Return_Review.md](../archive/Package_Return_Review.md) | 0 / 0 | Archived. Earlier returned-package flow with former scope selectors. It records why a complete package is parsed before read-only review and canonical application are treated as separate operations. [Maintained reference](../Scripts_Overview.md) |
| [Panel_Hosts_And_Control_Surfaces.md](../Panel_Hosts_And_Control_Surfaces.md) | 4 / 0 | Retained. Panel lifecycle, view registration and stable control hosts are separate from placement recipes. |
| [Publication_Ignore_List.md](../archive/Publication_Ignore_List.md) | 3 / 0 | Archived. Preserves the retirement of the publishable field and the Unpublishable report’s implementation and verification evidence. |
| [Read_And_Config_Scripts.md](../archive/Read_And_Config_Scripts.md) | 1 / 0 | Archived. Former GET and scope-config module map. Use the workspace and endpoint references for live names and capabilities. [Maintained reference](../Configuration_And_Extension_Points.md#workspace-and-target-contracts) |
| [Rebuild_And_Audit_Endpoints.md](../Rebuild_And_Audit_Endpoints.md) | 1 / 0 | Retained the current exact-document Rebuild, discovery refresh and private Broken Links requests. Removed the scope-wide HTTP recipe. |
| [Rebuild_Follow_Through_Scripts.md](../archive/Rebuild_Follow_Through_Scripts.md) | 1 / 0 | Archived. Former build-follow-through inventory. It preserves the split between committed writes, generation and discovery before the broad Rebuild action was removed. [Maintained reference](../Scripts_Overview.md) |
| [Related_Galleries.md](../Related_Galleries.md) | 1 / 0 | Retained as an independent delivery awaiting its recorded local review. Current reader and source rules live in Catalogue Media View and Catalogue Source Model. |
| [Reorder_Docs.md](../Reorder_Docs.md) | 3 / 0 | Retained. Exact Position semantics and the rationale for one nested order. Source Organisation owns its persisted format. |
| [Report_Block_Tokens.md](../Report_Block_Tokens.md) | 2 / 0 | Retained. Points authors to the sole checked report registry and gives its token form. |
| [Report_Capability_And_Composition.md](../Report_Capability_And_Composition.md) | 1 / 0 | Retained. Owns public versus local report module, data and stylesheet boundaries. |
| [Selected_Documents.md](../Selected_Documents.md) | 1 / 0 | Retained. Owns the Star workflow and its relationship to Selected metadata, generation and queued publication. |
| [Semantic_Tokens.md](../Semantic_Tokens.md) | 7 / 5 | Retained. Author entry point for current token types and editor actions. |
| [Semantic_Tokens_Architecture.md](../Semantic_Tokens_Architecture.md) | 24 / 0 | Retained. Owns source grammar, resolution, generated relationships and static/public projection. |
| [Semantic_Tokens_Concept.md](../archive/Semantic_Tokens_Concept.md) | 0 / 0 | Archived. Original semantic-token study. It preserves the reasoning for stable identity, explicit presentation intent and editable occurrences while the supported grammar lives with the current architecture. [Maintained reference](../Semantic_Tokens_Architecture.md) |
| [Semantic_Tokens_Source_Editor_UI.md](../Semantic_Tokens_Source_Editor_UI.md) | 7 / 0 | Retained. Owns exact Source modal interaction and occurrence editing; parser and generated data stay with Architecture. |
| [Source_Editor_Scripts.md](../Source_Editor_Scripts.md) | 21 / 0 | Retained. Traces source sessions, Directives and exact editor completion through code owners. |
| [Source_Mutation_Scripts.md](../Source_Mutation_Scripts.md) | 2 / 0 | Retained. Maps exact New, Draft, Star, Position and Delete modules. Removed obsolete Subject authoring from the current summary. |
| [Target_Lookup.md](../Target_Lookup.md) | 3 / 0 | Retained. Exact generated Catalogue chooser payload and the decision to retire the redundant persisted lookup. |
| [Toolbar_Icon_Mapping.md](../Toolbar_Icon_Mapping.md) | 5 / 0 | Retained as a separate proposal. The shipped toolbar token and placement references remain the current owners. |
| [Toolbar_Model.md](../Toolbar_Model.md) | 5 / 0 | Retained. Explains placement across app, active reader, collection and editing controls. |

### Catalogue and cross-domain ownership

Retain the useful concepts and diagrams. Bring authoring, storage, relationship, media and publication claims into line with current code and the app boundaries. Move old workflows into their history when appropriate.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Catalogue_Architecture.md](../Catalogue_Architecture.md) | 5 / 3 | Retained for canonical and generated-data ownership. Corrected required Series membership and linked the maintained data-model map and Media View reference. |
| [Catalogue_Data_Model_Map.md](../Catalogue_Data_Model_Map.md) | 0 / 0 | Retained and updated. Traces Series membership, direct Gallery membership and Series–Gallery relevance through Save, Refresh, Regenerate and Publish. |
| [Catalogue_Series_Management.md](../Catalogue_Series_Management.md) | 4 / 0 | Retained. Series browsing, membership and definition dialog at the current Work Editor route. |
| [Catalogue_Source_Model.md](../Catalogue_Source_Model.md) | 17 / 1 | Retained for the canonical family and validation contracts. Corrected Series mutation, ready-media and maintenance details and linked the Detail migration record. |
| [Data_Models_Diagrams.md](../Data_Models_Diagrams.md) | 1 / 3 | Retained for diagram conventions. Links the updated Catalogue source and projection map. |
| [Knowledge_System_Vision.md](../archive/Knowledge_System_Vision.md) | 1 / 0 | Archived. Earlier cross-system vision for Studio, Analytics, Data Sharing and the public Analysis reader. It preserves the design goals and experiments that led to a shared reader with independent sources. [Maintained reference](../../guide/How_The_Site_Fits_Together.md) |
| [Local_Authoring_And_Publication.md](../archive/Local_Authoring_And_Publication.md) | 2 / 0 | Archived. Preserves the decision to run Studio and Docs Viewer as sibling services and the rationale for earlier publication timing. |
| [Processing.md](../Processing.md) | 2 / 1 | Retained. Website-facing pointer to the separate Processing project and its configured project-media boundary. |
| [Shared_Artifact_Patterns.md](../Shared_Artifact_Patterns.md) | 1 / 0 | Retained. Cross-app rationale for splitting editable source, preparation and consumer artifacts. |
| [Shared_Icons.md](../Shared_Icons.md) | 7 / 3 | Retained as the cross-app icon proposal and rationale. Toolbar Icons and Icon Tokens own shipped behavior. |
| [Works_Editor_Icon_Mapping.md](../Works_Editor_Icon_Mapping.md) | 3 / 0 | Retained. Exact adopted Studio action-to-artwork mapping and accepted exceptions. |

### Ideas and unfinished proposals

Check whether the proposal is still wanted, superseded or already planned elsewhere. Preserve approved implementation constraints and active routing. Park useful ideas without treating them as shipped instructions.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Catalogue_Hosting_And_Storage_Options.md](../Catalogue_Hosting_And_Storage_Options.md) | 1 / 0 | Retained as a distinct architecture proposal. Current Studio ownership and publication remain with Catalogue Architecture. |
| [Catalogue_Images_In_Export_And_Review.md](../archive/Catalogue_Images_In_Export_And_Review.md) | 2 / 0 | Archived. Earlier proposal for Work and Detail presentation in static consumers. It keeps the proposed export/Review tradeoffs before the shared adopted-Work contract shipped. [Maintained reference](../Catalogue_Media_View.md) |
| [Docs_Search_Relevance.md](../archive/Docs_Search_Relevance.md) | 2 / 0 | Archived. Earlier corpus-adaptive relevance proposal. It preserves possible scoring signals and evaluation rationale. Any future comparison starts from the current Portfolio and collection corpora. [Maintained reference](../Docs_Viewer_Search.md) |
| [Docs_Viewer_App_Roadmap.md](../Docs_Viewer_App_Roadmap.md) | 1 / 0 | Retained as the independent Mac and iPad capability roadmap. The browser workflow guide does not decide native scope. |
| [Document_Link_Strength.md](../Document_Link_Strength.md) | 2 / 0 | Retained as an independent proposal for authored directional relationships. Current Related Links remain unweighted. |
| [Independent_Canonical_Documents.md](../Independent_Canonical_Documents.md) | 1 / 0 | Retained as the independent one-time seeding proposal, preserving the distinction between provenance and synchronisation. |
| [Public_Docs_Source_Repository.md](../archive/Public_Docs_Source_Repository.md) | 0 / 0 | Archived. Earlier authoring-source hosting proposal with retired scope paths. It preserves allowlist-only release and independent repository ownership as design considerations for any renewed proposal. [Maintained reference](../Source_Organisation.md#storage-and-roles) |
| [Public_Mobile_Experience.md](../archive/Public_Mobile_Experience.md) | 1 / 0 | Archived. Earlier mobile exploration. Its reader journeys were carried into Mobile Layouts. It preserves the original public/mobile and local-desktop boundaries. [Maintained reference](../CSS_Ownership.md) |
| [R2_Workspace_Backups.md](../R2_Workspace_Backups.md) | 1 / 0 | Retained as a separate recovery proposal. Updated the source selection to the current Working boundary. |
| [Search.md](../Search.md) | 0 / 3 | Retained as the Search entry point and parent. Replaced the retired scope and Catalogue routes with links to the chapter, current Search owners and the frozen archive. |
| `Search_Build_Pipeline.md` | 3 / 0 | Retired. Deleted after both remaining inbound routes were reconciled and document-ID and parent references were checked. [Projection Contract](../Projection_Contract.md) distinguishes active Catalogue browsing, Docs discovery and the frozen archive. [Builder](../Builder.md#working-rebuild) and [Docs Search Index](../Docs_Search_Index.md) own active Search. |

## Archive candidates (94)

The subject column describes what the file records. Advice and status inside an archived document may describe an older operating model.

### Original Analysis, Catalogue and UAC work

Retain design or migration context. Use the current Catalogue editor, source, browse, generated and deployment guides for active behavior. Keep linked UAC/Analysis families together when moving them.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Analysis_And_Catalogue_Presentation.md](../archive/Analysis_And_Catalogue_Presentation.md) | 10 / 18 | Archived. Unification feature record. It keeps the rationale for a shared reader with independent Catalogue and document authorities, and the sequence of decisions that led to adoption. |
| [Analysis_Catalogue_Architecture.md](../archive/Analysis_Catalogue_Architecture.md) | 1 / 0 | Archived. Early architecture for the former Analysis reader. It records the reasoning for keeping authored navigation, Catalogue membership and presentation references independent. |
| [Analysis_Catalogue_Concept.md](../archive/Analysis_Catalogue_Concept.md) | 9 / 0 | Archived. Presentation study. It records the decision to let one exact Work support its own media presentation and any number of separately authored discussions. |
| [Analysis_Catalogue_Delivery_Sequence.md](../archive/Analysis_Catalogue_Delivery_Sequence.md) | 9 / 0 | Archived. Early unification delivery sequence. It records why the frozen public site, local integration and final deployment were treated as separate steps. |
| [Analysis_Catalogue_Done.md](../archive/Analysis_Catalogue_Done.md) | 0 / 23 | Archived. Historical closeout group for the unification deliveries. Its child records retain implementation and acceptance evidence. |
| [Analysis_Media_In_R2.md](../archive/Analysis_Media_In_R2.md) | 3 / 0 | Archived. Historical media migration. The October 2026 release and authorized cleanup are recorded below, alongside the byte-preservation and reference checks that preceded deletion. |
| [Catalogue_And_Analysis_Storage_Layout.md](../archive/Catalogue_And_Analysis_Storage_Layout.md) | 2 / 0 | Archived. Early storage design. It records why canonical Catalogue records, authored documents, replaceable output and the frozen archive had separate owners. |
| [Catalogue_Authoring_In_Docs_Viewer.md](../archive/Catalogue_Authoring_In_Docs_Viewer.md) | 1 / 0 | Archived. Retains the CSI storage and publication decisions, Work 00008 acceptance and recovery evidence limits. Current operations live in [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) and [Catalogue Deployment](../Catalogue_Deployment.md). |
| [Catalogue_CSS.md](../archive/Catalogue_CSS.md) | 1 / 0 | Archived. Presentation pilot. It records why a Work component used scoped styles and shared presentation rules across hosts instead of inheriting the old site's page CSS. |
| [Catalogue_Changed_Regeneration_Delivery.md](../archive/Catalogue_Changed_Regeneration_Delivery.md) | 0 / 0 | Archived. Accepted targeted Regenerate delivery. It records the decision to carry exact changed and deleted Work IDs and consume entries after successful work, preserving partial completion for diagnosis. Its former modes and receipt are superseded. |
| [Catalogue_Collection_Browsing.md](../archive/Catalogue_Collection_Browsing.md) | 1 / 0 | Archived. Preserves the first Catalogue list delivery and user review. [Collection browsing architecture](../Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) owns the current behavior. |
| [Catalogue_Context_Navigation.md](../archive/Catalogue_Context_Navigation.md) | 0 / 0 | Archived. Archived with its parent proposal. Records the original Series-based sequence distinction. |
| [Catalogue_Data_Model.md](../archive/Catalogue_Data_Model.md) | 8 / 0 | Archived. Early document-Subject and Detail model. It records why exact identity, membership and document association were treated separately. The later Gallery conversion retired Details, and Subject Retirement records the document-side changes. |
| [Catalogue_Documents_And_Metadata.md](../archive/Catalogue_Documents_And_Metadata.md) | 1 / 0 | Archived. Accepted Catalogue Entry delivery. It records why the Work presentation uses one identity-only token plus a separate Related links directive, and preserves the Work 00008 pilot and full reconciliation evidence. |
| [Catalogue_Image_Token_Metadata_Delivery.md](../archive/Catalogue_Image_Token_Metadata_Delivery.md) | 1 / 0 | Archived. Accepted image-metadata delivery. It records why Work-derived alt text and optional title captions resolve from Catalogue data during document Build, with the original acceptance and its limits. |
| [Catalogue_Navigation.md](../archive/Catalogue_Navigation.md) | 5 / 3 | Archived. Archived the URL-context proposal. Retains its distinction between membership and a browsing sequence. Current navigation links point to the collection and Media View owners. |
| [Catalogue_Navigation_Implementation.md](../archive/Catalogue_Navigation_Implementation.md) | 2 / 0 | Archived. Archived with its parent proposal. Retains the frozen reader's loaded-sequence and caching design. |
| [Catalogue_Per_Work_Detail_Source.md](../archive/Catalogue_Per_Work_Detail_Source.md) | 1 / 0 | Archived. Historical Detail migration source and transaction-check record. It preserves why the converter used exact entity identities and how the Gallery conversion retired the old source. |
| [Catalogue_Report_Inputs.md](../archive/Catalogue_Report_Inputs.md) | 2 / 0 | Archived. Accepted private report input migration. It records why six readers share Refresh-owned Catalogue inputs while keeping independent report outputs and live filesystem work. |
| [Catalogue_Search.md](../archive/Catalogue_Search.md) | 2 / 2 | Archived. Retains the published Work and Series selection, ranking design and former build dependency policy. |
| [Catalogue_Search_Policy.md](../archive/Catalogue_Search_Policy.md) | 2 / 0 | Archived. Maps the browser policy to its frozen JSON and JavaScript. |
| [Catalogue_Series_Publication.md](../archive/Catalogue_Series_Publication.md) | 1 / 0 | Archived. Superseded per-Series draft and publication proposal. It preserves the design considered before Catalogue publication adopted queued completed output and dropped record-level publication state. |
| [Catalogue_Work_Document_Links.md](../archive/Catalogue_Work_Document_Links.md) | 0 / 0 | Archived. Proposal and delivery record for exact Work document IDs and portable reader paths. It preserves the rationale for direct document targets without a Catalogue-to-document lookup table. |
| [Catalogue_Work_Regeneration.md](../archive/Catalogue_Work_Regeneration.md) | 1 / 0 | Archived. Initial Catalogue document generation. It records the approved bounded pilot, full-collection acceptance and decisions about source identity and navigation. The workflow below used the former preview/apply action. |
| [Catalogue_Works_Browsing_And_Search.md](../archive/Catalogue_Works_Browsing_And_Search.md) | 3 / 1 | Archived. Retains the CWF report conversion and browsing decisions. [Catalogue Works](../Catalogue_Works.md#data-and-ownership) describes the current Refresh-owned input. |
| [Collection_Search_And_Site_Search.md](../archive/Collection_Search_And_Site_Search.md) | 6 / 4 | Archived. Earlier decisions about collection search, portfolio discovery, Recent and editorial curation. The shipped scope and reader contracts have since changed. [Maintained reference](../Docs_Viewer_Search.md) |
| [Public_Catalogue_Data_Flow.md](../archive/Public_Catalogue_Data_Flow.md) | 1 / 0 | Archived. Retains the pre-freeze payload and module map. |
| [Public_Catalogue_Design.md](../archive/Public_Catalogue_Design.md) | 1 / 0 | Archived. Retains the pre-freeze presentation and reader design. |
| [Public_Route_Model.md](../archive/Public_Route_Model.md) | 1 / 0 | Archived. Retains former paths, query state and route decisions. |
| [UAC_1_Freeze_Legacy_Catalogue.md](../archive/UAC_1_Freeze_Legacy_Catalogue.md) | 3 / 0 | Archived. Completed freeze of the legacy reader, Search, Recent and media. This delivery records the cutover evidence and the decision to keep the historic site independent. |
| [UAC_2_Catalogue_Examples.md](../archive/UAC_2_Catalogue_Examples.md) | 2 / 0 | Archived. Historical sample-data preparation for the initial consumer studies. It records the selected records and artefacts used before full Catalogue output was available. |
| [UAC_3A_Catalogue_Media_View.md](../archive/UAC_3A_Catalogue_Media_View.md) | 1 / 0 | Archived. Media View proof. It records the accepted single-Work presentation, the small gallery extension and the interaction decisions tested before the full Catalogue cutover. |
| [UAC_3B_Series_Works_Report.md](../archive/UAC_3B_Series_Works_Report.md) | 2 / 0 | Archived. Stopped Series report study. It records what the bounded report proved about generated member data and exact Media View targets. |
| [UAC_3C_Detail_Subjects.md](../archive/UAC_3C_Detail_Subjects.md) | 2 / 0 | Archived. Detail Subject experiment. It preserves the reason for a directly resolvable composite identity and the assignment evidence before Details and the old Subject workflow were retired. |
| [UAC_3_Findings.md](../archive/UAC_3_Findings.md) | 2 / 0 | Archived. Evidence from the consumer studies. It records the distinction between author-selected links, inline images and Media View, and why schema changes waited for a demonstrated consumer need. |
| [UAC_3_Tokens_Reports_And_Data_Model.md](../archive/UAC_3_Tokens_Reports_And_Data_Model.md) | 9 / 6 | Archived. Consumer research handoff. It records the proofs, pauses and unresolved questions about tokens, reports and shared generated data at the time. |
| [UAC_4_Catalogue_Data_And_Editors.md](../archive/UAC_4_Catalogue_Data_And_Editors.md) | 5 / 0 | Archived. Completed source and editor cutover. It records the decisions to remove draft state and simplify Series and Work data before rebuilding the consumer projections. |
| [UAC_5_Studio_Catalogue_Output.md](../archive/UAC_5_Studio_Catalogue_Output.md) | 4 / 0 | Archived. Completed full-data handoff. It records why consumers used generated Catalogue records and the sample-to-full validation evidence. |
| [Works_Report_Concept_And_Architecture.md](../archive/Works_Report_Concept_And_Architecture.md) | 2 / 0 | Archived. Earlier Works coverage design using refresh-owned placement and generated Context rows. Its implementation and tradeoffs predate retirement of Work Document Coverage. [Maintained reference](../Reports.md) |

### Retired scope, source and publication migrations

Retain decision and cutover history. Treat scope/stage recipes and old storage paths as historical. Route current readers to Source Organisation, Builder and Catalogue Deployment.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Archive_Documents.md](../archive/Archive_Documents.md) | 0 / 0 | Archived. Delivery record for the former cross-workspace Archive operation. It preserves the selected-subtree, media-transfer and destination-first completion decisions and the original verification limits. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Core_Definition_Baseline_v1.md](../archive/Core_Definition_Baseline_v1.md) | 0 / 0 | Archived. Accepted initial reader extraction baseline. It preserves the shared-core and composition boundary and the evidence required before moving code. [Maintained reference](../Generated_Data_Contracts.md) |
| [Cross_System_Relationship_Map.md](../archive/Cross_System_Relationship_Map.md) | 0 / 0 | Archived. Earlier relationship map. It keeps the distinction between aboutness, mentions, project state and lineage before later relationship retirements. [Maintained reference](../Generated_Data_Contracts.md) |
| [Deploy_And_Public_Cutover_Delivery.md](../archive/Deploy_And_Public_Cutover_Delivery.md) | 2 / 0 | Archived. Preserves the proposed Deploy Repo cutover and its explicit acceptance and release gates. |
| [Docs_Projection_Map.md](../archive/Docs_Projection_Map.md) | 0 / 0 | Archived. Preserves the earlier scope-era artifact map and its design boundaries. |
| [Document_Concept_And_Moment_IDs.md](../archive/Document_Concept_And_Moment_IDs.md) | 2 / 0 | Archived. Accepted removal of redundant Concept and Moment identities. It preserves the rationale for exact document IDs and the reference-preservation evidence. [Maintained reference](../Related_Links.md) |
| [Document_Content_And_Metadata.md](../Document_Content_And_Metadata.md) | 4 / 0 | Retained as the one metadata-separation proposal. The implemented Index order already has its own canonical owner. |
| [Document_Sub_Scope_Metadata.md](../archive/Document_Sub_Scope_Metadata.md) | 2 / 0 | Archived. Accepted backfill of the former destination-owned sub-scope field. It preserves the reason for deriving membership at creation and import boundaries. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Embedded_Detail_Documents.md](../archive/Embedded_Detail_Documents.md) | 1 / 0 | Archived. Earlier report-hosted document design. It preserves the decision that report discovery can differ while content, identity and rendering remain first class. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [External_Media_Workspace.md](../archive/External_Media_Workspace.md) | 0 / 0 | Archived. Preserves the rationale for separating retained originals, managed media and public copies. |
| [Moment_IDs_And_Subjects.md](../archive/Moment_IDs_And_Subjects.md) | 1 / 0 | Archived. Earlier allocation of Moment identities. It preserves the historic IDs and reasoning before that separate identity scheme was retired. [Maintained reference](../Related_Links.md) |
| [Pre_Publish_And_Publish_Delivery.md](../archive/Pre_Publish_And_Publish_Delivery.md) | 2 / 0 | Archived. Preserves implementation and verification evidence for the former preparation and acceptance workflow. |
| [Preview_Stage_Consolidation.md](../archive/Preview_Stage_Consolidation.md) | 3 / 0 | Archived. Preserves the decision and evidence for consolidating the former local publication snapshots. |
| [Processing_Project_Setup.md](../archive/Processing_Project_Setup.md) | 1 / 0 | Archived. Historical repository incorporation and setup record for the separate Processing project. Current project and media boundaries belong to its owner. [Maintained reference](../Processing.md) |
| [Public_Scopes.md](../archive/Public_Scopes.md) | 4 / 0 | Archived. Preserves the former scoped public routing and reader-isolation contract. |
| [Public_Work_JSON_Review.md](../archive/Public_Work_JSON_Review.md) | 2 / 0 | Archived. Accepted Work JSON and reader-preparation delivery. It preserves the rationale for runtime Manage resolution and selected static preparation in Publish, Export and packages. [Maintained reference](../Generated_Data_Contracts.md) |
| [Publish_Workflow.md](../archive/Publish_Workflow.md) | 7 / 0 | Archived. Preserves the decision to keep Catalogue authority independent of an accepted document snapshot. |
| [Publishing_Workflow_Analysis_Media_Namespace.md](../archive/Publishing_Workflow_Analysis_Media_Namespace.md) | 2 / 0 | Archived. Earlier Analysis media namespace cutover. It preserves the one-logical-identity decision and the accepted token migration. [Maintained reference](../Media_And_Asset_Handling.md) |
| [Publishing_Workflow_Concept.md](../archive/Publishing_Workflow_Concept.md) | 7 / 1 | Archived. Preserves the earlier Working and Pre-publish design and the current-Catalogue decision that informed it. |
| [Publishing_Workflow_Content_Alignment.md](../archive/Publishing_Workflow_Content_Alignment.md) | 1 / 0 | Archived. Preserves the accepted content alignment and source migration evidence. |
| [Publishing_Workflow_Stage_Structure_And_UI.md](../archive/Publishing_Workflow_Stage_Structure_And_UI.md) | 4 / 0 | Archived. Preserves acceptance and implementation evidence for the former stage-aware UI and storage cutover. |
| [Remove_Stage_Context_From_Search.md](../archive/Remove_Stage_Context_From_Search.md) | 1 / 0 | Archived. Search stage-context retirement. It preserves the decision to keep postings and identity separate from reader URLs and storage roles. [Maintained reference](../Configuration_And_Extension_Points.md#workspace-and-target-contracts) |
| [Restore_Moments_In_Analysis.md](../archive/Restore_Moments_In_Analysis.md) | 1 / 0 | Archived. Accepted restoration of the original Moments documents and media. It preserves source identity and reader presentation evidence. [Maintained reference](../Media_And_Asset_Handling.md) |
| [Retire_Studio_Tags.md](../archive/Retire_Studio_Tags.md) | 3 / 0 | Archived. Accepted retirement of Studio Tags. It records the original migration of editorial associations to Docs-owned identities before Concept tokens also changed. [Maintained reference](../Related_Links.md) |
| [Scope_Lifecycle.md](../archive/Scope_Lifecycle.md) | 2 / 0 | Archived. Design for the retired multi-scope lifecycle. It preserves the explicit preview, applied effects and refusal to infer an external workspace. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Search_Improvements.md](../archive/Search_Improvements.md) | 0 / 2 | Archived. Earlier Search goals and relevance decision history. The shipped discovery policy is maintained separately. [Maintained reference](../Docs_Viewer_Search.md) |
| `Separate_Document_Content_Metadata.md` | 0 / 0 | Retired. The later [metadata-separation proposal](../Document_Content_And_Metadata.md) already preserves its direction, rationale and open questions, and incorporates the completed Index-order decision. |
| [Single_Publish_Delivery.md](../archive/Single_Publish_Delivery.md) | 0 / 0 | Archived. Preserves the accepted removal of browser stage context and the single Publish implementation evidence. |
| [Sub_Scope_Customisation_Architecture.md](../archive/Sub_Scope_Customisation_Architecture.md) | 1 / 0 | Archived. Earlier collection-report customisation design. It records the rationale for shared presentation with capabilities supplied by the owning composition. [Maintained reference](../Reports.md) |
| [Sub_Scope_Documents_And_Media_Structure.md](../archive/Sub_Scope_Documents_And_Media_Structure.md) | 2 / 0 | Archived. Accepted split of collection document and media ownership. It preserves the reasons for independently scoped paths and safe removal. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Sub_Scope_Public_And_Manage_Manifests.md](../archive/Sub_Scope_Public_And_Manage_Manifests.md) | 2 / 0 | Archived. Former collection manifest and Concepts contribution delivery. It records why public browsing and private Manage metadata have distinct owners. [Maintained reference](../Generated_Data_Contracts.md) |
| [Subject_Retirement.md](../archive/Subject_Retirement.md) | 4 / 0 | Archived. Accepted removal of old Subject authoring and Folder placeholders. It preserves the rationale for deriving project associations from exact Catalogue references. [Maintained reference](../Related_Links.md) |

### Reader, authoring and report deliveries

Retain design evidence or original acceptance context after checking the current owner. Remove active guidance that duplicates the latest reader, authoring and report contracts. Move the delivery as history without recasting it as a procedure.

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Cross_Collection_Semantic_References.md](../archive/Cross_Collection_Semantic_References.md) | 3 / 0 | Archived. Former semantic occurrence index and report delivery. It records how exact document identity was carried across collections before the index was retired. [Maintained reference](../Related_Links.md) |
| [Doc_Relationships.md](../archive/Doc_Relationships.md) | 12 / 2 | Archived. Original relationship design. It preserves the distinction between authored links and generated relationship records and the history of scope aggregation. [Maintained reference](../Related_Links.md) |
| [Docs_Search_Relevance_Delivery.md](../archive/Docs_Search_Relevance_Delivery.md) | 0 / 0 | Archived. Unimplemented evaluation plan for the former full-text corpora. It preserves the rationale for bounded comparisons and proportionate evidence. [Maintained reference](../Docs_Viewer_Search.md) |
| [Document_Context_Navigation.md](../Document_Context_Navigation.md) | 7 / 0 | Retained as the distinct ordinary-Index traversal proposal. Shipped Book and collection navigation remain independent. |
| [Document_Relationships_Delivery.md](../archive/Document_Relationships_Delivery.md) | 3 / 0 | Archived. Accepted early document relationship and Links View delivery. It preserves the initial relationship-record boundaries and acceptance. [Maintained reference](../Related_Links.md) |
| [Document_Rendering_And_Projection.md](../archive/Document_Rendering_And_Projection.md) | 0 / 0 | Archived. Completed rendering and projection simplification. It preserves the rationale for deriving reader output from completed document effects instead of duplicate generation. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Document_View_And_Return_Navigation_Delivery.md](../archive/Document_View_And_Return_Navigation_Delivery.md) | 1 / 1 | Archived. Accepted reader navigation delivery. It records why the reader keeps one caller and remembers the Index and report states independently. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Gallery_Design.md](../archive/Gallery_Design.md) | 7 / 0 | Archived. Accepted Series gallery experiment. It records the decisions on ordered input, per-selection loading and returning to the invoking page that informed the later Work and Gallery views. |
| [Gallery_List_Design.md](../archive/Gallery_List_Design.md) | 6 / 0 | Archived. Stopped gallery-list proposal. It records why visual browsing and metadata lookup had different requirements, and the limits of the bounded Series report proof. |
| [Image_Token_Delivery.md](../archive/Image_Token_Delivery.md) | 1 / 0 | Archived. Accepted semantic image-token delivery. It preserves editable authoring and builder-owned presentation without rewriting older authored images. [Maintained reference](../Media_And_Asset_Handling.md) |
| [Info_Panel_Links_And_Pinning_Delivery.md](../archive/Info_Panel_Links_And_Pinning_Delivery.md) | 3 / 0 | Archived. Accepted Info panel pinning delivery. It preserves why a generated compact list and the retained pin are separate from authoring, with the manual acceptance record. [Maintained reference](../Info_Panel.md) |
| [Links_View.md](../archive/Links_View.md) | 5 / 0 | Archived. Former separate per-document Links interface. It preserves its presentation and navigation decisions before they moved into generated document content. [Maintained reference](../Related_Links.md) |
| [Links_View_Semantic_Tokens_Delivery.md](../archive/Links_View_Semantic_Tokens_Delivery.md) | 1 / 0 | Archived. Stopped proposal for media entries in the former Links View. It preserves why media and document connection displays took different paths. [Maintained reference](../Related_Links.md) |
| [Media_Links_And_Series_Galleries_Delivery.md](../archive/Media_Links_And_Series_Galleries_Delivery.md) | 1 / 0 | Archived. Accepted Work/Detail and Series media delivery. It preserves gallery loading and explicit caller-return decisions from before the Gallery conversion. [Maintained reference](../Catalogue_Media_View.md) |
| [Media_View_Text_Links_And_Catalogue_Images.md](../archive/Media_View_Text_Links_And_Catalogue_Images.md) | 4 / 0 | Archived. Accepted move to exact Catalogue media targets in authored documents. It preserves early Work and Detail presentation evidence and separate static-consumer design. [Maintained reference](../Catalogue_Media_View.md) |
| [Moments_Images_And_Thumbnails_Delivery.md](../archive/Moments_Images_And_Thumbnails_Delivery.md) | 0 / 0 | Archived. Completed Moments image and thumbnail migration. It preserves the migration inventory and upload decisions before Thumb became independent. [Maintained reference](../Media_And_Asset_Handling.md) |
| [Public_Index_Search_Scopes.md](../archive/Public_Index_Search_Scopes.md) | 1 / 0 | Archived. Accepted shared Manage and Public Search delivery. It preserves the scope switch, retained reader behavior and local publication evidence. [Maintained reference](../Docs_Viewer_Search.md) |
| [Related_Links_Delivery.md](../Related_Links_Delivery.md) | 1 / 0 | Retained as its separate acceptance record. Related Links and Runtime own the shipped workflow. |
| [Reorder_Docs_Delivery.md](../archive/Reorder_Docs_Delivery.md) | 2 / 0 | Archived. Accepted ordinary Index Position delivery. It preserves the nested-order decision, affected document operations and the acceptance evidence. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Route_Ready_State_Audit.md](../archive/Route_Ready_State_Audit.md) | 2 / 0 | Archived. Route-ready audit record. It preserves the exact startup and busy-state evidence from the former audit. [Maintained reference](../Run_Checks.md) |
| [Save_Build_Optimisations.md](../archive/Save_Build_Optimisations.md) | 1 / 0 | Archived. Completed performance work. It preserves the evidence for carrying parsed inputs through generation, removing duplicated operations and retaining explicit maintenance. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Scope_Links_Delivery.md](../archive/Scope_Links_Delivery.md) | 1 / 0 | Archived. Accepted scope-wide Links aggregation delivery. It records the reporting approach before the workspace and relationship graph changed. [Maintained reference](../Related_Links.md) |
| [Source_Editor_And_Token_Modals_Delivery.md](../archive/Source_Editor_And_Token_Modals_Delivery.md) | 2 / 0 | Archived. Accepted complete-source editor and token-modal delivery. It preserves source authority, exact capture during editing and its verified limits. [Maintained reference](../Semantic_Tokens_Architecture.md) |

## Delete candidates (40)

| File | Links / ID refs | Recommendation |
| --- | ---: | --- |
| [Analysis_Broken_Links_Report.md](../archive/Analysis_Broken_Links_Report.md) | 2 / 0 | Archived. Accepted Analysis Working audit delivery. It records why Broken Links operates independently of relationship generation and the original local evidence. [Maintained reference](../Broken_Links_Script.md#saved-local-report) |
| `Analysis_Documents.md` | 1 / 0 | Retired. **First pass.** Deleted. Publication Ignore List now points to [Source Organisation](../Source_Organisation.md#operations) and [Builder](../Builder.md#publish-preparation) for current eligibility. [Reports](../Reports.md#current-reports) records the former report and host retirement. |
| `Bulk_Add_Work.md` | 0 / 0 | Retired. **First pass.** Deleted. The [Work Editor](../Catalogue_Work_Editor.md#import-a-project-subfolder) records the Excel retirement and current import. The original implementation and verification record is in Git at `8a56846b09`. |
| `Catalogue_Drafts.md` | 0 / 0 | Retired. **First pass.** Deleted. The [Catalogue editor cutover](../archive/UAC_4_Catalogue_Data_And_Editors.md) records why the draft route and fields were removed. [Catalogue Deployment](../Catalogue_Deployment.md) owns current publication. |
| `Catalogue_Search_Build_Config.md` | 2 / 0 | Retired. Retired after path, document ID and parent checks. The former field-dependency registry and additive-only build policy are recorded in [Catalogue Search](../archive/Catalogue_Search.md#former-build-dependencies). |
| `Catalogue_Subject_Shortcut.md` | 0 / 0 | Retired. **First pass.** Deleted. Carried its explicit-token decision and two converted identities into [Subject Retirement](../archive/Subject_Retirement.md#retirement-scope). [Semantic Tokens Source Editor UI](../Semantic_Tokens_Source_Editor_UI.md) owns current controls. |
| [Catalogue_Token_Links_Delivery.md](../archive/Catalogue_Token_Links_Delivery.md) | 0 / 0 | Archived. Accepted document-relationship adoption for Work tokens. It preserves the decision to retire the duplicate occurrence index and suppress self-links. [Maintained reference](../Related_Links.md) |
| [Collection_Icons_Delivery.md](../Collection_Icons_Delivery.md) | 2 / 0 | Retained for the open manual visual acceptance. Source Organisation owns the implemented icon mapping. |
| [Context_Actions_Menu.md](../archive/Context_Actions_Menu.md) | 0 / 0 | Archived. Earlier Actions menu delivery before workspace lifecycle and selected actions changed. It records how actions resolved exact targets and showed their availability. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Copy_Working_Search_Into_Preview.md](../archive/Copy_Working_Search_Into_Preview.md) | 2 / 0 | Archived. Preserves the decision to give Working ownership of Search generation and the original exact-byte copy evidence. |
| [Current_Copy_To_Analysis_And_Publish_Actions.md](../archive/Current_Copy_To_Analysis_And_Publish_Actions.md) | 2 / 0 | Archived. **First pass.** Archived the September 2026 implementation baseline and redirected its design references. [Publish and deploy](../../guide/Publish_And_Deploy.md) owns the current workflow. |
| `Docs_Data.md` | 0 / 0 | Retired. **First pass.** Deleted. [Source Organisation](../Source_Organisation.md) and [Generated Data Contracts](../Generated_Data_Contracts.md) own the current workspace. [Cross-System Relationship Map](../archive/Cross_System_Relationship_Map.md) retains the former lineage design. Its removal also cleared an inbound link to the retired Search Build Pipeline page. |
| [Docs_Media_Report_Refactor.md](../archive/Docs_Media_Report_Refactor.md) | 0 / 0 | Archived. Saved Docs Media report refactor. It preserves the deliberate separation of inspection, presentation, Finder activation and manual review. [Maintained reference](../Media_And_Asset_Handling.md) |
| [Document_Actions_And_Toolbar.md](../archive/Document_Actions_And_Toolbar.md) | 1 / 0 | Archived. Accepted toolbar placement delivery. It preserves the layout and action-context decisions that informed the current controls. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Document_Edit_Menu.md](../archive/Document_Edit_Menu.md) | 0 / 0 | Archived. Earlier shared Edit menu delivery. It records the grouping and authoring decisions before control labels and placement evolved. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Document_Index_Navigation_Delivery.md](../archive/Document_Index_Navigation_Delivery.md) | 0 / 0 | Archived. Collection index shortcut and per-tab state delivery. It preserves the navigation and restoration behavior tested at the time. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Document_List_Date_Precision.md](../archive/Document_List_Date_Precision.md) | 0 / 0 | Archived. Accepted calendar-day list projection delivery. It records why browser ordering can use days while keeping exact source and by-ID timestamps. [Maintained reference](../Generated_Data_Contracts.md) |
| [Document_View_And_Return_Navigation_Handoff.md](../archive/Document_View_And_Return_Navigation_Handoff.md) | 1 / 0 | Archived. **First pass.** Archived the exact verification and acceptance limits and updated the completed delivery’s evidence link. [Docs Viewer Runtime](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns current navigation. |
| [Gallery_And_Series_Definition_Editing.md](../archive/Gallery_And_Series_Definition_Editing.md) | 0 / 0 | Archived. Earlier Gallery/Series definition editor delivery. It preserves separate definition and membership decisions and its original implementation status. [Maintained reference](../Catalogue_Media_View.md) |
| [Icon_Tokens_Delivery.md](../Icon_Tokens_Delivery.md) | 1 / 0 | Retained for the open manual authoring and visual acceptance. Icon Tokens owns the implemented grammar and behavior. |
| [Index_Context_Menu.md](../archive/Index_Context_Menu.md) | 0 / 0 | Archived. Original Index context menu delivery. It preserves exact-target and open-in-editor decisions before the controls were reorganised. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Index_Search_And_Recent.md](../archive/Index_Search_And_Recent.md) | 0 / 0 | Archived. Accepted retained Index views and return handoff. It preserves the reason to keep discovery controls independent of the open document. [Maintained reference](../Docs_Viewer_Runtime.md#exact-document-navigation-and-return) |
| [Links_View_Design.md](../archive/Links_View_Design.md) | 1 / 0 | Archived. Accepted visual proof for the former Links View. It preserves the verified interaction and the direction before Related Links was embedded. [Maintained reference](../Related_Links.md) |
| [Public_Work_JSON_Handoff.md](../archive/Public_Work_JSON_Handoff.md) | 1 / 0 | Archived. **First pass.** Archived the Publish, Export and Prepare Package evidence and updated the review’s link. [Generated Data Contracts](../Generated_Data_Contracts.md#catalogue-reference-and-presentation) owns current presentation. |
| `Publishable_Field.md` | 1 / 0 | Retired. **First pass.** Deleted. Local Authoring And Publication now points to [Source Organisation](../Source_Organisation.md#operations) for eligibility and to [Publication Ignore List](../archive/Publication_Ignore_List.md#original-delivery-direction) for the field’s retirement. |
| [Retire_Public_Document_Locations.md](../archive/Retire_Public_Document_Locations.md) | 3 / 0 | Archived. Retirement of the obsolete location index and Catalogue document URL refresh. It records the transition to exact reader-owned by-ID locations. [Maintained reference](../Generated_Data_Contracts.md) |
| [Scope_Configured_Authoring_Controls.md](../archive/Scope_Configured_Authoring_Controls.md) | 4 / 0 | Archived. Superseded per-scope authoring availability proposal. It records the decisions about exact action context and earlier breadcrumb changes. [Maintained reference](../Configuration_And_Extension_Points.md#workspace-and-target-contracts) |
| [Scope_Lifecycle_Endpoints.md](../archive/Scope_Lifecycle_Endpoints.md) | 2 / 0 | Archived. Request/response examples for retired scope CRUD endpoints. The record preserves the original boundary between planning and application. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Search_Field_Styling_Delivery.md](../archive/Search_Field_Styling_Delivery.md) | 0 / 0 | Archived. Completed Search Field styling delivery. It preserves the visual acceptance and chosen shared interaction roles. [Maintained reference](../Search_Fields.md) |
| `Semantic_Tokens_Report.md` | 4 / 0 | Retired. **First pass.** Deleted. Replaced report references with [Semantic Tokens Architecture](../Semantic_Tokens_Architecture.md#document-relationships-and-audit) and [Reports](../Reports.md#current-reports). Retained the former host ID and September delivery evidence in the surviving records. |
| [Series_Tag_Editor.md](../archive/Series_Tag_Editor.md) | 1 / 0 | Archived. Former Series Tag editor. It preserves historical editing and persistence details alongside the Tag retirement record. [Maintained reference](../Semantic_Tokens_Architecture.md) |
| [Series_Tags.md](../archive/Series_Tags.md) | 0 / 0 | Archived. Former Series Tag data model. It preserves the old data relationships and the reason to keep the migration record. [Maintained reference](../Semantic_Tokens_Architecture.md) |
| `Source_Config_Endpoints.md` | 1 / 0 | Retired. **First pass.** Deleted. User Facing Rules now links to [design-time workspace configuration](../Configuration_And_Extension_Points.md#workspace-and-target-contracts). [Reports](../Reports.md#current-reports) preserves the retired endpoint names. |
| `Source_Config_Report.md` | 0 / 0 | Retired. **First pass.** Deleted. [Reports](../Reports.md#current-reports) already records the report, service and host retirement. |
| [Source_Editor_Toolbar.md](../archive/Source_Editor_Toolbar.md) | 1 / 0 | Archived. Earlier Source toolbar consolidation. It records the decisions behind shared directives and local control placement. [Maintained reference](../Semantic_Tokens_Architecture.md) |
| [Sub_Scope_Report_Reparenting.md](../archive/Sub_Scope_Report_Reparenting.md) | 1 / 0 | Archived. Former report-host reparenting fix. It records why placement and collection identity were kept independent. [Maintained reference](../Source_Organisation.md#document-and-collection-identity) |
| [Subject_Associations_Manifest_Delivery.md](../archive/Subject_Associations_Manifest_Delivery.md) | 0 / 0 | Archived. Completed removal of a duplicate Subject association projection. It preserves why existing management manifests were sufficient at that stage. [Maintained reference](../Related_Links.md) |
| `Usage_Index.md` | 1 / 0 | Retired. **First pass.** Deleted. Semantic Tokens routes to the [current relationship and audit boundary](../Semantic_Tokens_Architecture.md#document-relationships-and-audit). [Cross-collection delivery](../archive/Cross_Collection_Semantic_References.md) preserves the former usage-index evidence. |
| [Work_List_And_Bulk_Gallery_Editing.md](../archive/Work_List_And_Bulk_Gallery_Editing.md) | 0 / 0 | Archived. Accepted bulk membership editing delivery. It records why explicit Gallery changes and existing local completion belong together. [Maintained reference](../Catalogue_Media_View.md) |
| [Works_Collection_Browsing.md](../archive/Works_Collection_Browsing.md) | 0 / 0 | Archived. Completed first Works browsing delivery. It preserves the staged reader and private metadata evidence before the Context and Catalogue boundaries changed. [Maintained reference](../Reports.md) |
