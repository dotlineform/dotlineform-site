---
doc_id: analytics-static-route-template
title: Analytics Static Route Template
added_date: 2026-06-21
last_updated: 2026-06-25
parent_id: analytics
viewable: true
---
# Analytics Static Route Template

The model is:

- Python owns static serving, runtime config, local API dispatch, Data Sharing API dispatch, and local filesystem operations
- `analytics-app/app/frontend/analytics-shell.html` owns the outer app document shell
- each Analytics route owns a static HTML template under `analytics-app/app/frontend/routes/`
- each route keeps a JavaScript entrypoint for behavior and interactivity
- shared helpers own API calls, route state, modals, lists, formatting, and repeated dynamic UI

## Structure

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

Analytics route templates participate in [Route Ready State](/docs/?scope=studio&doc=route-ready-state) with Analytics attributes.
Template examples should show the route root and initial ready/busy baseline, while shared semantics stay in the Route Ready State doc.

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

Route scripts should update readiness through `analytics-app/app/frontend/js/analytics-route-state.js`.
JavaScript should still render genuinely dynamic UI such as result lists, modal content, import previews, Data Sharing records, and validation output. Stable page skeletons should be HTML templates.
