---
doc_id: admin-static-route-template-migration
title: Admin Static Route Template Migration
added_date: 2026-06-22
last_updated: 2026-06-22
parent_id: admin
viewable: true
---
# Admin Static Route Template Migration

Admin should follow the same frontend-owned route model as Studio and Analytics, with a static HTML shell and route templates rather than Python-owned route markup.
The goal is to remove Admin route HTML from Python while keeping stable page structure in `.html` files.

The target model is:

- Python owns static serving, runtime config, local API dispatch, local filesystem reads/writes, and local report/test-run operations
- `admin-app/app/frontend/admin-shell.html` owns the outer Admin document shell
- each Admin route owns a static HTML template under `admin-app/app/frontend/routes/`
- each route keeps a JavaScript entrypoint for behavior and interactivity
- shared helpers own API calls, route state, theme, navigation, lists, modals, and repeated dynamic UI

## Target Structure

```text
admin-app/app/frontend/
  admin-shell.html
  routes/
    admin-home.html
    admin-audits.html
    admin-checks.html
    admin-activity.html
    admin-testing.html

  js/
    admin-app.js
    admin-route-registry.js
    admin-route-templates.js
    admin-home.js
    admin-audits.js
    admin-checks.js
    admin-activity.js
    admin-testing.js
```

Each route config entry should identify the stable template and behavior module:

```json
{
  "path": "/admin/checks/",
  "template": "/admin/app/frontend/routes/admin-checks.html",
  "script": "/admin/app/frontend/js/admin-checks.js",
  "shell_type": "html-template"
}
```

## Route Boundary

Route templates own stable DOM:

```html
<div
  class="tagStudioPage studioChecksPage"
  id="studioChecksRoot"
  hidden
  data-admin-route="admin-checks"
  data-admin-ready="false"
  data-admin-busy="false"
>
  <div class="studioChecksTop"></div>
</div>
```

Route scripts own behavior:

```js
const root = document.getElementById("studioChecksRoot");
initializeAdminRouteState(root, { route: "admin-checks" });
bindChecksEvents(root);
loadChecksReports();
```

JavaScript should still render genuinely dynamic UI such as recent runs, report output, activity feed entries, audit rows, testing run summaries, status text, modal content, and API results.
Stable page skeletons should be HTML templates.

## Current State

Completed on 2026-06-22:

- `admin_app_server.py` serves `admin-shell.html` for configured Admin route paths.
- `admin-config.json` owns each route path, static template, behavior module, and `shell_type`.
- static route templates live under `admin-app/app/frontend/routes/`.
- browser boot is owned by `admin-app/app/frontend/js/admin-app.js`, `admin-route-registry.js`, and `admin-route-templates.js`.
- `admin_app_config.py` resolves shell routes from config and no longer uses `ADMIN_SERVED_ROUTE_PATHS`.
- `admin-home.html` owns static home links directly.
- `admin_app_views.py` was deleted.

## Previous State

Admin had the same pre-migration shape Analytics had before its static route migration:

- `admin_app_server.py` had a hardcoded route dispatch list
- `admin_app_views.py` owned both the app document shell and route body HTML
- `admin_app_config.py` validated routes against `ADMIN_SERVED_ROUTE_PATHS`
- `admin_home_view()` rendered home links in Python from Admin route config and UI text
- route scripts assumed the server-rendered DOM already existed

This caused frontend layout work to require Python view edits and server restarts.
The migration made Admin route markup frontend-owned and config-driven.

## Admin Home

`admin_home_view()` previously rendered grouped home links in Python using `admin-home.json` plus route metadata from `admin-config.json`.
That was unnecessary for a stable local landing route whose links are not materially different from Analytics or Studio home links.

`admin-home.html` now owns the static home link groups directly.
`admin-home.js` stays limited to route-ready state and any small behavior that is actually needed at runtime.

## Task List

- [x] Add `admin-app/app/frontend/admin-shell.html`.
- [x] Add `admin-app/app/frontend/js/admin-app.js` as the browser app bootstrap.
- [x] Add `admin-app/app/frontend/js/admin-route-registry.js` to resolve route config from `admin-config.json`.
- [x] Add `admin-app/app/frontend/js/admin-route-templates.js` to fetch and validate route templates.
- [x] Add `template` and `shell_type` fields to `admin-app/app/frontend/config/admin-config.json`.
- [x] Change `admin_app_server.py` so configured Admin routes return the static Admin shell.
- [x] Remove the hardcoded per-route view calls from `admin_app_server.py`.
- [x] Remove `ADMIN_SERVED_ROUTE_PATHS` from `admin_app_config.py`.
- [x] Add `admin_shell_route_paths()` based on `admin-config.json`.
- [x] Move `admin_home_view()` markup into `routes/admin-home.html`.
- [x] Move `admin_audits_view()` markup into `routes/admin-audits.html`.
- [x] Move `admin_checks_view()` markup into `routes/admin-checks.html`.
- [x] Move `admin_activity_view()` markup into `routes/admin-activity.html`.
- [x] Move `admin_testing_view()` markup into `routes/admin-testing.html`.
- [x] Delete `admin_app_views.py` after every route template is migrated.
- [x] Update Admin check inventories that reference `admin_app_views.py`.
- [x] Update quick-profile syntax inventories that reference `admin_app_views.py` if the file is deleted.
- [x] Update tests to assert static shell/template behavior instead of Python-rendered route HTML.
- [x] Run Admin home and operational route smokes.

## Suggested Migration Order

1. Build the common static shell and template loader without changing route behavior.
2. Migrate `admin-testing`, the smallest route.
3. Migrate `admin-audits`.
4. Migrate `admin-activity`.
5. Migrate `admin-checks`.
6. Migrate `admin-home` as a static link template.
7. Delete the Python view file and hardcoded route map.

## Verification

Focused checks should include:

```bash
$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/admin_app_server.py admin-app/app/server/admin_app/admin_app_config.py admin-app/commands/run_checks.py
$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_app_server.py
$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_home_route.py
$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_operations_routes.py
```

Run route-specific browser smokes for every template migrated in a given change.
