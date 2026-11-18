---
draft: false
doc_id: d-20260423-000000-d015e6
title: Studio
added_date: "2026-04-23 00:00:00"
last_updated: "2026-11-18"
summary: Entry point for using, operating, and changing the local catalogue authoring app.
parent_id: ""

---

# Studio

Studio is the local Catalogue authoring app. Open `/studio/catalogue-work/` with `bin/local-studio`. The Work editor contains the Series and Gallery workflows. It reads saved canonical records, owns the draft and completes Save before the separate Refresh action prepares Working reader output. [Work editor](Catalogue_Work_Editor.md) · [Implementation trace](Catalogue_Services.md) · [Local startup](Local_Runners.md)

## Browser Boot

The sole registered route is `catalogue_work_editor`, with template `catalogue-work.html`, script `catalogue-work-editor.js` and ready-state ID `catalogue-work`. The server serves `studio-shell.html` at the registered path. `studio-app.js` loads runtime config, resolves the route, fetches its template, mounts the header and body, then imports the configured script. [Route source](../../studio/app/frontend/config/studio-config.json) · [Shell composition](../../studio/app/frontend/js/studio-app.js)

`catalogue-editor-route-boot.js` initializes route readiness, loads the cached config and probes Catalogue health. `catalogue-work-editor.js` loads Work and Series search maps, Gallery definitions, media-source choices and Refresh status. A failed health or required read produces unavailable state. The route owns ready/busy projection through `studio-route-state.js`. [Boot owner](../../studio/app/frontend/js/catalogue-editor-route-boot.js) · [Editor composition](../../studio/app/frontend/js/catalogue-work-editor.js)

## Configuration And Routes

`studio-config.json` owns `app.routes`. Each record declares label, title, path, template, script, nav, shell type and ready-state ID. `studio_app_config.py` validates required fields, unique paths, `/studio/` containment, `html-template` shell type and template/script existence. The source JSON currently contains only the Work editor route. [Validator and projector](../../studio/app/server/studio/studio_app_config.py)

The served `/studio/runtime-config.json` adds the asset version, media URLs, pipeline variants/encoding, local site bases and runtime route copies. `studio-config.js` caches that browser payload and exposes `app.routes`. The editor consumes projected media and pipeline values. Edit the checked registry or its server input when changing these settings. [Browser loader](../../studio/app/frontend/js/studio-config.js) · [Media configuration](Catalogue_Media_Pipeline_Config.md) · [Configuration owners](Configuration_And_Extension_Points.md#find-the-owner)

## Browser Responsibility

Stable forms and mounts belong in the route template. Dynamic records, previews, draft changes, selection and membership choices belong in focused browser modules. `catalogue-work-actions.js` owns Save orchestration. `catalogue-work-fields.js` owns draft/request fields. Definition dialogs and saved choice updates live in `catalogue-work-definitions.js` and the Series/Gallery modal owners. `studio-transport.js` names endpoint addresses, while `catalogue-editor-service-client.js` shapes calls. [Save owner](../../studio/app/frontend/js/catalogue-work-actions.js) · [Client](../../studio/app/frontend/js/catalogue-editor-service-client.js)

The left Series browser selects a saved member list independently of the open Work's assignment. Its `series` URL value and the open `work` value can coexist. Definition OK saves immediately. Work Save persists assignment or membership changes. New Series preserves the current Work draft. Delete is offered for an empty Series using the browser's complete saved Work map. [Series browser](../../studio/app/frontend/js/catalogue-work-series-browser.js) · [Definition and membership behavior](Catalogue_Work_Editor.md#gallery-and-series-definitions)

## Server Responsibility

`studio_app_server.py` owns loopback HTTP, bounded JSON/multipart intake, static/media routes and response status. `studio_catalogue_api.py` dispatches allowlisted canonical reads, media selection and domain operations. Catalogue services own exact target checks, canonical transactions, selected media preparation and queue effects. The browser supplies completed authoring choices. [Server](../../studio/app/server/studio/studio_app_server.py) · [API adapter](../../studio/app/server/studio/studio_catalogue_api.py) · [Operations](Catalogue_Services.md#api-surface)

## Change The Owner

A field change follows source definition and serialization, the editor and its consuming projections. A route change follows the registered template/script and server validation. A Save or Refresh change follows the operation trace and the state it carries forward. Public Docs Viewer reads the separately published output through its own entrypoint. [Canonical model](Catalogue_Source_Model.md) · [Save and Refresh completion](Catalogue_Save_And_Refresh.md) · [Design rationale](../design/Studio_And_Catalogue_Ownership.md) · [Delivery evidence](../deliveries/Studio_And_Catalogue_Ownership_Review.md)
