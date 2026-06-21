---
doc_id: analytics-static-route-template-migration
title: Analytics Static Route Template Migration
added_date: 2026-06-21
last_updated: 2026-06-21
parent_id: analytics
viewable: true
---
# Analytics Static Route Template Migration

Analytics should follow the same frontend-owned route model as Studio, but with static HTML route templates rather than large JavaScript string renderers.
The goal is to remove route HTML from Python while keeping stable page structure in `.html` files.

The target model is:

- Python owns static serving, runtime config, local API dispatch, Data Sharing API dispatch, and local filesystem operations
- `analytics-app/app/frontend/analytics-shell.html` owns the outer app document shell
- each Analytics route owns a static HTML template under `analytics-app/app/frontend/routes/`
- each route keeps a JavaScript entrypoint for behavior and interactivity
- shared helpers own API calls, route state, modals, lists, formatting, and repeated dynamic UI

## Target Structure

```text
analytics-app/app/frontend/
  analytics-shell.html
  routes/
    analytics-home.html
    tag-groups.html
    tag-registry.html
    tag-aliases.html
    series-tags.html
    series-tag-editor.html
    data-sharing-prepare.html
    data-sharing-review.html

  js/
    analytics-app.js
    analytics-route-registry.js
    analytics-route-templates.js
    tag-registry.js
    data-sharing-prepare.js
```

Each route config entry should identify the stable template and behavior module:

```json
{
  "path": "/analytics/data-sharing/prepare/",
  "template": "/analytics/app/frontend/routes/data-sharing-prepare.html",
  "script": "/analytics/app/frontend/js/data-sharing-prepare.js",
  "shell_type": "html-template"
}
```

## Route Boundary

Route templates own stable DOM:

```html
<div
  class="analyticsPage dataSharingPreparePage"
  id="dataSharingPrepareRoot"
  hidden
  data-analytics-ready="false"
  data-analytics-busy="false"
>
  <div class="analytics__panel dataSharingPreparePage__panel"></div>
</div>
```

Route scripts own behavior:

```js
const root = document.getElementById("dataSharingPrepareRoot");
initializeAnalyticsRouteState(root, { route: "data-sharing-prepare" });
bindPrepareEvents(root);
loadPrepareConfig();
```

JavaScript should still render genuinely dynamic UI such as result lists, modal content, import previews, Data Sharing records, and validation output.
Stable page skeletons should be HTML templates.

## Current State

Analytics currently differs from Studio:

- `analytics_app_server.py` has a hardcoded route dispatch list
- `analytics_app_views.py` owns both the app document shell and route body HTML
- `analytics_app_config.py` validates routes against `ANALYTICS_SERVED_ROUTE_PATHS`
- route scripts assume the server-rendered DOM already exists

This causes frontend layout work to require Python view edits and server restarts.
The migration should make route markup frontend-owned and config-driven.

## Special Case: Series Tag Editor

`series_tag_editor_view()` currently injects pipeline and media data into HTML attributes.
Before that route can move to a static template, those values should be exposed through `runtime_config()` or loaded through an Analytics config helper.

The route script should then apply the data attributes or read the values directly from config during initialization.

## Task List

- [ ] Add `analytics-app/app/frontend/analytics-shell.html`.
- [ ] Add `analytics-app/app/frontend/js/analytics-app.js` as the browser app bootstrap.
- [ ] Add `analytics-app/app/frontend/js/analytics-route-registry.js` to resolve route config from `analytics-config.json`.
- [ ] Add `analytics-app/app/frontend/js/analytics-route-templates.js` to fetch and validate route templates.
- [ ] Add `template` and `shell_type` fields to `analytics-app/app/frontend/config/analytics-config.json`.
- [ ] Change `analytics_app_server.py` so configured Analytics routes return the static Analytics shell.
- [ ] Remove the hardcoded per-route view calls from `analytics_app_server.py`.
- [ ] Remove `ANALYTICS_SERVED_ROUTE_PATHS` from `analytics_app_config.py`.
- [ ] Add `analytics_shell_route_paths()` based on `analytics-config.json`.
- [ ] Move `analytics_home_view()` markup into `routes/analytics-home.html`.
- [ ] Move `tag_groups_view()` markup into `routes/tag-groups.html`.
- [ ] Move `tag_registry_view()` markup into `routes/tag-registry.html`.
- [ ] Move `tag_aliases_view()` markup into `routes/tag-aliases.html`.
- [ ] Move `series_tags_view()` markup into `routes/series-tags.html`.
- [ ] Move `data_sharing_prepare_view()` markup into `routes/data-sharing-prepare.html`.
- [ ] Move `data_sharing_review_view()` markup into `routes/data-sharing-review.html`.
- [ ] Move series-tag-editor media and pipeline data into runtime config.
- [ ] Move `series_tag_editor_view()` markup into `routes/series-tag-editor.html`.
- [ ] Delete `analytics_app_views.py` after every route template is migrated.
- [ ] Update Admin check inventories that reference `analytics_app_views.py`.
- [ ] Update tests to assert static shell/template behavior instead of Python-rendered route HTML.
- [ ] Run route smokes for tag routes, series routes, and Data Sharing prepare/review.

## Suggested Migration Order

1. Build the common static shell and template loader without changing route behavior.
2. Migrate `tag-groups`, the smallest route.
3. Migrate `tag-registry` and `tag-aliases`.
4. Migrate `series-tags`.
5. Migrate Data Sharing prepare and review.
6. Migrate `series-tag-editor` after moving injected media/pipeline data into runtime config.
7. Delete the Python view file and hardcoded route map.

## Verification

Focused checks should include:

```bash
$HOME/miniconda3/bin/python3 -m py_compile analytics-app/app/server/analytics_app/analytics_app_server.py analytics-app/app/server/analytics_app/analytics_app_config.py
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_analytics_app_server.py
$HOME/miniconda3/bin/python3 analytics-app/tests/smoke/local_analytics_app_tag_routes.py
$HOME/miniconda3/bin/python3 analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py
```

Run route-specific browser smokes for every template migrated in a given change.
