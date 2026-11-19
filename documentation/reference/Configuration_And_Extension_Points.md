---
draft: false
doc_id: d-20260512-142027-54b354
title: Configuration And Extension Points
added_date: "2026-05-12 14:20:27"
last_updated: "2026-11-18"
summary: Map of the configuration, registries, generated projections, code definitions, and capability checks that drive Docs Viewer workflows.
parent_id: d-20260424-000000-50b63f

---

# Configuration And Extension Points

Use the owner below for the setting being changed. The browser receives URLs and display metadata. Python resolves filesystem roots and performs writes. Runtime code registers executable views, controls, importers and report loaders.

## Find The Owner

| Concern | Maintained owner |
| --- | --- |
| Docs workspace storage, collections, report-host IDs, default document, Search policy and public destinations | [`docs-workspace.json`](../../docs-viewer/config/workspace/docs-workspace.json), loaded by [`docs_workspace_config.py`](../../docs-viewer/services/docs_workspace_config.py). |
| Local Docs process flags and bindings | [Service defaults](../../docs-viewer/config/defaults/docs-viewer-service.json), environment and explicit runner arguments. [Local startup](Local_Setup.md#environment). |
| Docs app kind, features, panel defaults and data/config URLs | [Full route registry](../../docs-viewer/config/routes/docs-viewer-routes.json) and independently maintained [public route registry](../../site/docs-viewer/config/routes/docs-viewer-public-routes.json). |
| Studio routes and Catalogue editor settings | [Studio config](../../studio/app/frontend/config/studio-config.json). Its [server projector](../../studio/app/server/studio/studio_app_config.py) adds browser-safe media URLs and pipeline settings at `/studio/runtime-config.json`. [Studio contract](Studio.md#configuration-and-routes). |
| Catalogue fields and original-media pipeline | [Field registry](../../studio/data/config/catalogue/catalogue-field-registry.json) and [pipeline](../../_data/pipeline.json). [Catalogue domain](Catalogue_Source_Model.md#field-changes). |
| Reports, Catalogue token forms and package profiles | [Reports](Reports.md), [document/Catalogue references](Document_And_Catalogue_References.md) and [document packages](Document_Packages.md). Their data registries select allowlisted implementations. |
| Static validation and shared public-code projection | [Site tools](../../site-tools/config/site-tools.json) and [site-code inventory](../../site-tools/config/site-code-update.json). [Public projection](Projection_Contract.md). |

## Workspace And Target Contracts

`docs_workspace_v10` describes storage beneath the existing `DOTLINEFORM_DOCS_BASE_DIR`. Working owns source, generation and ready media. Preview stores selected finished publication artifacts. `DOTLINEFORM_PROJECTS_BASE_DIR` independently supplies project originals, staging and exchange folders. Loading configuration creates no workspace. An unavailable root fails visibly. [Storage layout](Source_Organisation.md#storage-and-roles) · [Startup recovery](Local_Setup.md#recover-the-failed-owner)

The top-level `default_doc_id` supplies the same default to Manage and Public. Choose an ordinary document available to both readers. A blank setting uses the first Index root. The loader checks ID syntax. The public validator checks the projected default's by-ID file. Deletion leaves the setting intact, so a maintainer must change it if the default is retired. [Default-document walkthrough](../guide/Change_The_System_Safely.md)

Working registers collections with exact IDs, titles, host IDs and required `document_media` booleans. Hosts and collection registration are design-time responsibilities. A false media declaration, as in Catalogue, leaves Work media with its separate owner. Document actions carry an immutable `doc_id` and optional exact `collection`. Source and ordinary authoring use Working. Collection records are flat, while Book curation has separate ordering. [Collection ownership](Collections_And_Books.md) · [Media ownership](Media_And_Asset_Handling.md)

The workspace also owns private report output locations, explicit repository/R2 destinations and registered media families. These storage and credential bindings stay server-side. Eligibility and generation use the configuration upstream of the publication queue. Publish consumes its prepared effects. [Report lifecycle](Reports.md) · [Generation and publication](Builder.md#publish-preparation)

## Builder And Local Service Integration

After changing workspace display settings, defaults, collection registration or public destinations, run the config-only projector from the repository root with the project interpreter.

```bash
python3 docs-viewer/build/build_browser_config.py
bin/site-code-update
bin/site-code-update --check
bin/site-validate
```

The first command resolves the configured workspace and writes the local and public `docs_viewer_config_v4` browser files. It leaves document, Search, media and publication output alone. The next command copies manifest-listed public files into `site/`. Inspect the exact diff before checking the projection and deploy root. Reload the local reader. Release public configuration with the reviewed committed site snapshot. [Generated browser projections](#source-config-becomes-browser-config)

A policy or rendering change can separately require document generation or Search refresh at its owner. Changing a startup flag requires restarting the affected service. [Exact build and Full Working Build](Builder.md) · [Discovery refresh](Reader_Discovery_And_Return.md#build-and-publication) · [Local process settings](Local_Setup.md#environment)

## Source Config Becomes Browser Config

`docs-viewer/build/docs_builder/browser_config.py` derives these files from the workspace.

- `docs-viewer/config/defaults/docs-viewer-config.json` supplies Working reader and collection URLs.
- `docs-viewer/config/defaults/docs-viewer-public-config.json` supplies public destinations and collection metadata.
- `bin/site-code-update` copies the public file to `site/docs-viewer/config/defaults/docs-viewer-public-config.json`.

Edit the owning workspace settings and regenerate these projections. The full and public route registries are separately edited records. Keep their shared public route aligned. The site-code inventory copies selected runtime, styles and public browser defaults, while the public route registry is owned directly under `site/`. [Projector](../../docs-viewer/build/docs_builder/browser_config.py) · [Projection inventory](../../site-tools/config/site-code-update.json)

## How A Workflow Becomes Available

Trace the shell's entrypoint, resolved route and feature list, code registration, provider/service context, required backend capability and exact action policy. A visible management setting alone cannot enable an operation. The Docs service injects loopback service addresses and enabled flags into its served route registry. Public starts from its static registry and read-only composition. [Runtime owners](Runtime_Module_Ownership.md#trace-a-failure) · [Health and capabilities](Local_Setup.md#service-health-and-capabilities)

## Extension Points

Add a report through its registry and allowlisted loader. Add views or controls through the relevant entrypoint and shared registry. Add document actions through the existing action resolver, which already receives the exact document or collection. Add a source format through its converter and normalized import owner. Config can select registered behavior. New execution, storage or publication models require an agreed code change. [Report composition](Reports.md#composition-and-capabilities) · [Import boundary](Docs_Import.md#implementation-boundary) · [Runtime responsibilities](Runtime_Module_Ownership.md)

[Design reasoning](../design/Runtime_Configuration_And_Recovery.md) explains the projection and authority boundaries. [Review evidence](../deliveries/Runtime_Configuration_And_Recovery_Review.md) records the earlier cutovers and current verification limits.
