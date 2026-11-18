---
draft: false
doc_id: d-20260422-000000-c3135c
title: Studio Read And Save Flow
added_date: "2026-04-22 00:00:00"
last_updated: "2026-11-18"
summary: How the Studio editor reads canonical Catalogue data and completes a local mutation before Working refreshes its reader data.
parent_id: d-20260423-000000-d015e6

---
# Studio Read And Save Flow

## Configuration Flow

```text
studio-config.json
  -> studio_app_config.py validates routes
  + environment, pipeline.json, Python runtime constants
  -> /studio/runtime-config.json
  -> studio-config.js caches the browser payload
  -> shell, navigation, data helpers, and route scripts consume focused values
```

[Studio Config JSON](Studio_Config_JSON.md) owns the source and runtime-projection boundary. Route copy and option lists remain code-owned unless they are genuine shared configuration.

## Read Flow

Studio routes probe catalogue health before server-owned work:

```text
route boots
  -> health probe
  -> server available: use allowlisted /studio/api/catalogue/read
  -> unavailable workflow: show unavailable state and disable mutation controls
```

`studio-data.js` owns allowlisted Catalogue server reads through the browser transport's named endpoint. The Work editor requires the local service for its current workflow; there is no offline editing or offline save mode.

The editor reads canonical records and lookups through the Catalogue API. Thumbnails served from the generated-output route are a separate read. [Local Studio APIs](Local_Studio_APIs.md#catalogue-reads) lists the server-owned keys and addresses.

## Save Flow

```text
editor action
  -> browser prepares the exact mutation request
  -> catalogue service client / studio-transport.js
  -> Catalogue API adapter dispatches to the write service
  -> focused service validates and writes canonical source
  -> local completion prepares required media and queues known effects
  -> editor applies returned records and memberships
```

The [browser editor](../../studio/app/frontend/js/catalogue-work-editor.js) owns selections and form input. The [API adapter](../../studio/app/server/studio/studio_catalogue_api.py) delegates to the [write service](../../studio/services/catalogue/catalogue_write_service.py), which dispatches to the Work, Series, bulk edit and delete owners and completes the local effects. The required identity and revision fields depend on the operation. [Catalogue operations](Local_Studio_APIs.md#catalogue-operations)

## From Save To The Reader

Save returns the canonical editor state and queues the effects for Working. Required converted images and native uploads go into Projects-owned media staging. A saved change with incomplete local completion is reported separately from a rejected mutation. [Save boundary](Catalogue_Save_And_Refresh.md#save-boundary)

Refresh Catalogue takes the pending effects into Working reader JSON and ready media. Regenerate turns refreshed Work changes into built Catalogue documents and forwards their completed publication selections. Publish transfers queued output. [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md) · [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#current-workflow)
