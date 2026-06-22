---
doc_id: admin-static-route-template
title: Admin Static Route Template
added_date: 2026-06-22
last_updated: 2026-06-22
parent_id: admin
viewable: true
---
# Admin Static Route Template

Admin follows the same frontend-owned route model as Studio and Analytics, with a static HTML shell and route templates rather than Python-owned route markup.

The model is:

- Python owns static serving, runtime config, local API dispatch, local filesystem reads/writes, and local report/test-run operations
- `admin-app/app/frontend/admin-shell.html` owns the outer Admin document shell
- each Admin route owns a static HTML template under `admin-app/app/frontend/routes/`
- each route keeps a JavaScript entrypoint for behavior and interactivity
- shared helpers own API calls, route state, theme, navigation, lists, modals, and repeated dynamic UI

## Structure

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