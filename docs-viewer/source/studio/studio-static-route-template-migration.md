---
doc_id: studio-static-route-template-migration
title: Studio Static Route Template Migration
added_date: 2026-06-21
last_updated: 2026-06-21
parent_id: studio-runtime
viewable: true
---
# Studio Static Route Template Migration

Studio should use frontend-owned route markup without hiding stable page structure inside Python or JavaScript string factories.
The target model is:

- the local Python server owns static serving, runtime config, local API dispatch, and local filesystem operations
- `studio/app/frontend/studio-shell.html` owns the outer app document shell
- each route owns a static HTML template under `studio/app/frontend/routes/`
- each route has a JavaScript entrypoint for behavior and interactivity
- shared helpers own API calls, route state, modals, data loading, formatting, and repeated dynamic UI

This keeps stable route structure as HTML while preserving the current browser-owned Studio app shell.

## Target Structure

```text
studio/app/frontend/
  studio-shell.html
  routes/
    studio-home.html
    project-state.html
    bulk-add-work.html
    catalogue-field-registry.html
    catalogue-status.html
    studio-works.html
    catalogue-series.html
    catalogue-work.html

  js/
    studio-app.js
    studio-route-registry.js
    studio-route-templates.js
    project-state.js
    bulk-add-work.js
    catalogue-work-editor.js
```

Each route config entry should identify both the stable template and the route controller:

```json
{
  "path": "/studio/catalogue-work/",
  "template": "/studio/app/frontend/routes/catalogue-work.html",
  "script": "/studio/app/frontend/js/catalogue-work-editor.js",
  "shell_type": "html-template",
  "ready_state_route_id": "catalogue-work"
}
```

## Route Boundary

A route template owns stable DOM:

```html
<div id="catalogueWorkRoot" data-studio-route="catalogue-work">
  <section class="studioPanel">
    <form id="catalogueWorkForm"></form>
  </section>
</div>
```

The route script owns behavior:

```js
const root = document.getElementById("catalogueWorkRoot");
initializeRouteState(root);
bindFormEvents(root);
loadRecord();
```

JavaScript should still render dynamic repeated content when the data shape requires it, such as search results, editor sections, action rows, modals, and status output.
Stable page skeletons should live in route templates.

## Current State

Studio already uses a static outer shell:

- `studio/app/frontend/studio-shell.html`
- `studio/app/server/studio/studio_app_server.py` serves that shell for configured Studio routes
- `studio/app/frontend/js/studio-app.js` resolves the route, renders shared chrome, and imports the route script

Route body markup now lives in static route templates under `studio/app/frontend/routes/`.
`studio/app/frontend/js/studio-route-templates.js` fetches and validates the configured template before the route script boots.

## Task List

- [x] Move the outer Studio app shell out of Python and into `studio/app/frontend/studio-shell.html`.
- [x] Serve configured Studio routes from `studio/app/frontend/config/studio-config.json` instead of a hardcoded Python route list.
- [x] Remove `studio/app/server/studio/studio_app_views.py`.
- [x] Remove `STUDIO_SERVED_ROUTE_PATHS` and validate configured shell routes by config shape instead.
- [x] Add `template` fields to active Studio route entries in `studio-config.json`.
- [x] Add `studio/app/frontend/js/studio-route-templates.js` to fetch and validate route templates.
- [x] Update `studio-app.js` so it loads the route template before importing the route script.
- [x] Move `studio-home-shell.js` markup into `routes/studio-home.html`.
- [x] Move `project-state-shell.js` markup into `routes/project-state.html`.
- [x] Move `bulk-add-work-shell.js` markup into `routes/bulk-add-work.html`.
- [x] Move `catalogue-field-registry-shell.js` markup into `routes/catalogue-field-registry.html`.
- [x] Move `catalogue-status-shell.js` markup into `routes/catalogue-status.html`.
- [x] Move `studio-works-shell.js` markup into `routes/studio-works.html`.
- [x] Move `catalogue-series-shell.js` markup into `routes/catalogue-series.html`.
- [x] Move `catalogue-work-shell.js` markup into `routes/catalogue-work.html`.
- [x] Retire the old route-body renderer module after every route body is template-backed.
- [x] Update route smoke tests to assert template-backed route bodies rather than route-local shell modules.
- [x] Update Studio runtime docs and route inventory after the template migration is complete.

## Closeout Notes

The migration changed active Studio routes to `shell_type: "html-template"` and added template paths under `studio/app/frontend/routes/`.
The browser shell now renders shared chrome, fetches the route template, then imports the configured route script.
Dynamic values that used to be injected by shell modules are now applied during route initialization: Studio home links are rendered by `studio-home.js`, Bulk Add Work reads the workbook path from runtime config, and catalogue editor media attributes are projected onto route roots from runtime config before media preview state is refreshed.

Focused verification completed:

- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_server.py studio/app/server/studio/studio_app_config.py`
- `node --check` on changed Studio frontend modules
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/studio_operational_route_modules.py --site-root .`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_navigation_adapter.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_project_state_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_bulk_add_work_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_status_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_studio_works_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`

## Verification

Focused checks should include:

```bash
$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_server.py studio/app/server/studio/studio_app_config.py
$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py
$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_project_state_route.py
$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_editor_routes.py
```

Run route-specific browser smokes for every template migrated in a given change.
