---
draft: false
doc_id: d-20260424-000000-15b6f2
title: Studio Runtime
added_date: 2026-04-24 00:00:00
last_updated: "2026-10-11 00:00:00"
summary: Browser shell, route registry, template, route-script, shared-helper, and sibling-app runtime boundaries for Local Studio.
parent_id: d-20260423-000000-d015e6

---
# Studio Runtime

## Purpose

This document owns the Local Studio browser execution model. The [route inventory](Local_Studio_Routes.md) owns exact mounted pages; [Local Studio App](Local_Studio_App.md) owns the Python server; [Local Studio APIs](Local_Studio_APIs.md) owns endpoint inventory.

## Browser Boot

```text
studio-shell.html
  -> studio-app.js loads runtime config
  -> studio-route-registry.js resolves window.location
  -> studio-route-templates.js fetches the configured HTML template
  -> Studio shell mounts shared chrome and route markup
  -> configured route script imports and boots
  -> route script owns ready/busy state, reads, writes, and dynamic UI
```

The Python server serves the outer shell at Studio's sole page, `/studio/catalogue-work/`. It does not render route body markup or choose route behavior. The header title links directly to the Work editor, alongside the theme toggle. The former Home and field-registry pages and their dedicated assets are retired.

## Ownership Layers

| layer | owner | responsibility |
| --- | --- | --- |
| source registry | `studio-config.json` `app.routes` | route identity, path, template, script, shell type, nav flag, ready-state id |
| runtime validation | `studio_app_config.py` | reject invalid routes and add local runtime values |
| outer document | `studio-shell.html` | config and asset-version metadata plus `#studioApp` mount |
| app composition | `studio-app.js` | config load, route resolution, shared header/title, template mount, route import |
| stable route DOM | `studio/app/frontend/routes/*.html` | page roots, panels, forms, static controls, and dynamic mounts |
| route behavior | configured route script | data loading, events, dynamic rendering, modals, service calls, ready/busy projection |
| shared browser behavior | focused `studio-*` and catalogue helpers | config, routing, templates, theme, transport, data, editor primitives |

Stable markup belongs in route templates. Repeated records, API results, previews, status text, and other data-dependent UI belong in JavaScript.

## Route Registry Contract

Every active Studio route uses `shell_type: html-template` and declares:

- `label`
- `title`
- `path`
- `template`
- `script`
- `nav`
- `ready_state_route_id`

Server validation checks required fields, duplicate paths, supported shell type, `/studio/` containment, and template/script existence. The browser normalizes the validated record but does not widen it.

The server also copies route records into `app.runtime.views`; the current browser resolves routes directly from `app.routes`.

## Shared Runtime Boundaries

- `studio-config.js` loads the runtime payload and exposes the route registry and code-owned text accessors.
- `studio-route-state.js` owns `data-studio-ready` and `data-studio-busy` projection.
- `studio-data.js` owns shared JSON loading and allowlisted Catalogue server reads.
- `studio-transport.js` owns the current Catalogue endpoint constants, route health probe, JSON reads/writes and multipart writes.
- focused catalogue editor modules own editor state, selection, fields, actions, modals, media, and services.

The route shell remains orchestration. Do not add domain workflows to `studio-app.js` or Python-rendered HTML.

## Sibling Apps

Studio does not host Docs Viewer or retired Analytics/Data Sharing routes. It may build links to Docs Viewer or the public site, but it does not receive their config registries, runtime modules, APIs, or write capability.

The public site likewise does not load the Studio runtime. The current Studio editor has no public Catalogue navigation control; public Catalogue pages use their own site runtime.

## Frontend Retirement

The 2026-10-11 cleanup removed six unused or obsolete modules, unused route/transport/modal/record/media/message/selection helpers, three unused message-controller getters and 90 obsolete UI-text entries. The shell still loads its configured Catalogue Editor through the validated route registry; editor selection, forms, Save, Refresh, deletion, media picking and active confirmation/definition/embedded-item modals retain their current owners.

The old build-preview/readiness state had no producer. Its empty readiness/runtime/build-impact mounts, rendering calls and readiness styles are removed together with the unused build-target fields. Ready/busy lifecycle projection remains in `studio-route-state.js` and the active Catalogue route owners. [Testing](Testing.md#studio-frontend-retirement) records the approved removal of the stale static-home audit exception and the bounded verification selection.

Verification and final review on 2026-10-11: changed-source JavaScript/Python lint, Python syntax, the Studio-only static ready-state audit and whitespace checks passed. Read-only source tracing reached all 43 retained frontend modules with no missing imports/exports or unreferenced module bindings. The live Refresh preview import was restored after lint identified it; final diff review confirmed the active confirmation modal and ready/busy owners remain connected, with no unresolved findings in this cleanup. Browser boot/interaction, live Save/Refresh/Publish, pytest and broad profiles were not exercised. No frontend cache directory was present. These local-only assets have no tracked public-code projection.

## Extension Method

For a new route:

1. create the stable HTML template and focused route script
2. add one validated `app.routes` record
3. keep domain reads/writes behind existing focused browser and service owners
4. project ready/busy state through the shared route-state helper
5. add a route-boot smoke only for the durable shell/module/service boundary

For shared browser behavior, add or extend the smallest owner. Do not turn the route registry into executable policy or add another shell type without a real rendering model.

## Weak Spots

- `app.routes` and `app.runtime.views` duplicate the same route records at runtime; the projected `views` and `sites` fields have no current Studio browser consumer.

Exact code ownership for catalogue routes belongs in their workflow documents and modules, not another runtime module inventory here.
