---
doc_id: studio-static-route-template
title: Studio Static Route Template
added_date: 2026-06-25
last_updated: 2026-06-25
parent_id: studio
viewable: true
---
# Studio Static Route Template

Studio follows the same frontend-owned route model as Admin and Analytics, with a static HTML shell and route templates rather than Python-owned route markup.

In this document, "static route template" means a checked-in HTML template under `studio/app/frontend/routes/`.
This is separate from `studio/app/frontend/js/studio-static-route.js`, which is the initializer for static or reference routes after a template has mounted.

The model is:

- Python owns static serving, runtime config, local API dispatch, and local Catalogue API adapters
- `studio/app/frontend/studio-shell.html` owns the outer Studio document shell
- each Studio route owns a static HTML template under `studio/app/frontend/routes/`
- each route keeps a JavaScript entrypoint for behavior and interactivity
- shared helpers own config, route templates, route state, theme, navigation, transport, modals, and repeated dynamic UI

## Structure

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
    catalogue-work-detail.html
    catalogue-moment.html

  js/
    studio-app.js
    studio-route-registry.js
    studio-route-templates.js
    studio-route-state.js
    studio-static-route.js
    project-state.js
    bulk-add-work.js
    catalogue-status.js
    catalogue-work-editor.js
```

Each route config entry should identify the stable template and behavior module:

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

Studio route templates participate in [Route Ready State](/docs/?scope=studio&doc=route-ready-state) with Studio attributes.
Template examples should show the route root and initial ready/busy baseline, while shared semantics stay in the Route Ready State doc.

Route templates own stable DOM:

```html
<div
  class="studioPage catalogueWorkPage"
  id="catalogueWorkRoot"
  hidden
  data-studio-route="catalogue-work"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="studioUi__panel studioUi__panel--editor"></section>
</div>
```

Route scripts own behavior:

```js
const root = document.getElementById("catalogueWorkRoot");
initializeStudioRouteState(root, { route: "catalogue-work" });
bindCatalogueWorkEvents(root);
loadCatalogueWorkRoute();
```

Route scripts should update readiness through `studio/app/frontend/js/studio-route-state.js`.
Static or reference routes may use `studio/app/frontend/js/studio-static-route.js` after their template mounts.
JavaScript should still render genuinely dynamic UI such as search results, record fields, previews, modals, status text, API responses, and generated summaries.
Stable page skeletons should be HTML templates.
