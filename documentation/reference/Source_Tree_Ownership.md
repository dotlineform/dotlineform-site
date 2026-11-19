---
draft: false
doc_id: d-20260524-214228-7247ef
title: Source Tree Ownership
added_date: "2026-05-24 21:42:28"
last_updated: "2026-11-19"
parent_id: ""

---
# Source Tree Ownership

Use this map to choose the source owner before following its domain reference. The [workflow guide](../guide/How_The_Site_Fits_Together.md) explains how the apps fit together; [Projection Contract](Projection_Contract.md) follows their completed data and runtime outputs.

## Repository Shape

| Root | Owns |
| --- | --- |
| `studio/` | Local Catalogue authoring app, canonical Work/Series/Gallery relationships, media services and Studio tests |
| `docs-viewer/` | Canonical reader runtime/styles, local services, configuration, builders, import/export, document packages and Docs tests |
| `shared/frontend/` | Reviewed browser primitives and their styles; callers retain domain state and transport |
| `site/` | Tracked Pages deploy artifact: public shells/assets, published data and explicit runtime projection |
| `site-tools/` | Deploy-root validation, runtime projection command/inventory and site-level tooling config |
| `app/` | Separate native Mac/iPad project; [App README](../../app/README.md) and [instructions](../../app/AGENTS.md) own its lifecycle |
| `tooling/lint/` | Repository lint pins, rules and adopted source boundaries |
| `var/` | Ignored local logs, caches, reports and working output |

`DOTLINEFORM_DOCS_BASE_DIR` selects the existing external Docs workspace. `DOTLINEFORM_PROJECTS_BASE_DIR` independently selects project/media inputs, Catalogue staging and document packages. [Configured storage](Source_Organisation.md#storage-and-roles) owns exact source/generated/assets/Preview paths.

## Studio Boundary

Studio browser composition lives in `studio/app/frontend/`, server/API adapters in `studio/app/server/`, and local presentation in `studio/app/assets/`. `studio/services/{catalogue,media}/` owns required persistence, generation and media work. `studio/data/canonical/catalogue/` owns the five editable stores; `studio/data/config/catalogue/` owns the checked field/artifact inventory. [Studio](Studio.md) · [Canonical model](Catalogue_Source_Model.md) · [Save/Refresh operations](Catalogue_Services.md)

Entrypoints establish imports through [studio_python_paths.py](../../studio/shared/python/studio_python_paths.py). Domain modules use the established `catalogue.*`, `media.*` and shared imports directly; dependency failures propagate rather than retrying another package name. Studio's live editor projections read canonical source. Refresh separately prepares Working Catalogue output. [Save through publication](Catalogue_Save_And_Refresh.md)

## App Boundaries

Docs Viewer owns the public reader, local Manage and package Review compositions. Working source/generated data and Preview belong to the configured external workspace. Domain references own their persistence and completion details. [Docs Viewer](Docs_Viewer.md) · [Source organisation](Source_Organisation.md) · [Local service map](Endpoint_Overview.md)

The public site serves [site/index.html](../../site/index.html) and the committed files under `site/`. Shared/public runtime is edited under `docs-viewer/`; the [explicit inventory](../../site-tools/config/site-code-update.json) projects its public subset plus shared Search Field into `site/docs-viewer/` and `site/shared/`. Local-only membership in a source directory grants no public adoption. [Public shell](Public_Docs_Route_Shell.md) owns installed-shell/template and projection maintenance; [Publish and deploy](../guide/Publish_And_Deploy.md) separates runtime release from content transfer.

The legacy Catalogue snapshot and its dedicated R2 copy were retired; the live site is the current design reference. [Catalogue Archive](../deliveries/Catalogue_Archive.md#retirement-and-r2-cleanup) retains the historical rationale and retirement evidence. The active reader and publication pipeline use their current owners.

### Processing

The standalone Processing repository owns the Java sketches, documentation, checks, renders and exports. A Docs Viewer document collection has its own configured ownership. [Dotlineform Processing](https://github.com/dotlineform/dotlineform-processing)

Processing work media belongs beneath `$DOTLINEFORM_PROJECTS_BASE_DIR/processing/<project-id>/`. In Studio, choose the `processing` media source to select a finished render for a Work. The existing Catalogue workflow prepares and publishes that selection. [Media-source identities](Catalogue_Media_Pipeline_Config.md#work-media-sources) · [Catalogue workflow](Catalogue_Save_And_Refresh.md)

### Retired Analytics Boundary

The standalone Analytics tree, runner, routes/APIs, configuration and checks are retired. Docs Viewer owns integrated document packages; Concepts are authored documents. Do not restore `/analytics/...`, `/studio/analytics/...`, `/studio/data-sharing/...` or `/analytics/data-sharing/...` compatibility paths.

## Source, Generated, And Working Data

Canonical source and checked policy feed operation-owned local/public read models. Document generation prepares eligible completed effects; Publish transfers the selected data/media; runtime projection independently prepares code/configuration for the tracked deploy root. Logs and reports stay with their operational owner. [Current handoffs](Projection_Contract.md#working-and-public-outputs) · [Why these artifacts are separate](../design/Shared_Artifact_Patterns.md)

## Development Rules

[Development Checklist](../development/Development_Checklist.md) owns placement, shared-frontend, compatibility and lint-adoption rules. [Verification](../development/Verification.md) owns focused static commands and public runtime projection. This reference maps current roots and handoffs.
