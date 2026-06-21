---
doc_id: local-studio-routes
title: Local Studio Routes
added_date: 2026-06-02
last_updated: 2026-06-06
parent_id: studio
viewable: true
---
# Local Studio Routes

This document is the active route inventory for the Local Studio app server.
Use [Studio Runtime](/docs/?scope=studio&doc=studio-runtime) for the route-shell architecture and route registry contract.
Use [Local Studio App](/docs/?scope=studio&doc=local-studio-app) for the app server boundary.
Use [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) for endpoint ownership.

## Current Mounted Routes

Active Local Studio routes:

- `/studio/`
- `/studio/project-state/`
- `/studio/bulk-add-work/`
- `/studio/catalogue-field-registry/`
- `/studio/catalogue-status/`
- `/studio/studio-works/`
- `/studio/catalogue-series/`
- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-moment/`

The local app owns `/studio/`.
Studio home navigation is rendered by the JavaScript Studio app shell.
The local home exposes Studio-owned catalogue links through `studio-home.js` by grouping route IDs from `app.routes`; route labels and base paths come from the runtime route registry, while the home template owns the stable link-list mount point.
The shared Studio top navigation is separate from that home link list.
Every local Studio shell, including `/studio/`, shows the same compact top row: `dotlineform studio` on the left, with `docs` plus the light/dark toggle right-aligned.

## Template Shell Pattern

Catalogue-maintenance Studio route shells are hosted by the local app.
For active template-backed routes, Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/studio-route-templates.js` fetches the configured body template, and the route controller keeps route boot and behavior.

Current template-backed route families:

- Project State:
  `routes/project-state.html` owns stable body markup and `project-state.js` owns route behavior.
- Bulk Add Work:
  `routes/bulk-add-work.html` owns stable body markup and `bulk-add-work.js` owns route behavior.
- Catalogue Field Registry:
  `routes/catalogue-field-registry.html` owns stable body markup and `catalogue-field-registry-review.js` owns route behavior.
- Catalogue Drafts:
  `routes/catalogue-status.html` owns stable body markup and `catalogue-status.js` owns route behavior.
- Studio Works:
  `routes/studio-works.html` owns stable body markup and `studio-works.js` owns route behavior.
- Catalogue editors:
  route-local editor templates render the stable body and the existing editor controllers own route behavior.

The Catalogue Series, Work, Work Detail, and Moment editor route shells are hosted by the local app at plain `/studio/.../` paths.
The editor shell media attributes are projected in the browser from `app.runtime.media` and `app.runtime.pipeline`.
They reuse the existing vanilla editor modules and call local-app catalogue API endpoints under `/studio/api/catalogue/...`.

## Sibling Route Surfaces

Docs Viewer, Admin, and Analytics/Data Sharing are sibling local apps with their own route shells.

- Docs Viewer manage mode is served by the standalone Docs Viewer service, not Local Studio.
- Public `/library/` and `/analysis/` are public read-only Docs Viewer routes, not Local Studio routes.
- Local Admin serves `/admin/...`, including `/admin/audits/`, `/admin/checks/`, `/admin/activity/`, and `/admin/testing/`.
- Local Analytics serves `/analytics/...` and `/analytics/api/...`.

The local `/docs/` route is no longer hosted by Local Studio.
The runtime config does not expose Docs Viewer link targets, per-route doc IDs, Docs Viewer generated-data passthroughs, or Docs Viewer static assets.
Use the standalone Docs Viewer service directly for developer documentation.

## Route Checks

Current focused route shell checks:

- `studio/tests/smoke/local_studio_app_project_state_route.py`
- `studio/tests/smoke/local_studio_app_bulk_add_work_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_status_route.py`
- `studio/tests/smoke/local_studio_app_studio_works_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`
