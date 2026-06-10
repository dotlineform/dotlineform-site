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
Studio home navigation is rendered by the JavaScript Studio app shell, not Python or Jekyll/Liquid page data.
The local home exposes Studio-owned catalogue links through `studio-home-shell.js` by grouping route IDs from `app.routes`; route labels and base paths come from the runtime route registry, while the home layout owns grouping, order, and route-specific query-string defaults.
The shared Studio top navigation is separate from that home link list.
Every local Studio shell, including `/studio/`, shows the same compact top row: `dotlineform studio` on the left, with `docs` plus the light/dark toggle right-aligned.

## JavaScript Shell Pattern

Catalogue-maintenance Studio route shells are hosted by the local app.
For active JavaScript-shell routes, Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, route-local `*-shell.js` modules render the body markup, and the route controller keeps route boot and behavior.

Current JavaScript-shell route families:

- Project State:
  `project-state-shell.js` renders the body and `project-state.js` owns route behavior.
- Bulk Add Work:
  `bulk-add-work-shell.js` renders the body and `bulk-add-work.js` owns route behavior.
- Catalogue Field Registry:
  `catalogue-field-registry-shell.js` renders the body and `catalogue-field-registry-review.js` owns route behavior.
- Catalogue Drafts:
  `catalogue-status-shell.js` renders the body and `catalogue-status.js` owns route behavior.
- Studio Works:
  `studio-works-shell.js` renders the body and `studio-works.js` owns route behavior.
- Catalogue editors:
  route-local editor `*-shell.js` modules render the body and the existing editor controllers own route behavior.

The Catalogue Series, Work, Work Detail, and Moment editor route shells are hosted by the local app at plain `/studio/.../` paths.
The editor shell media attributes are projected in the browser from `app.runtime.media` and `app.runtime.pipeline`.
They reuse the existing vanilla editor modules and call local-app catalogue API endpoints under `/studio/api/catalogue/...`.

## Retired Local Routes

The former Catalogue dashboard page is retired.
Its links now live on the `/studio/` home page, and metrics belong on the individual pages where they are relevant.

The old Jekyll shells and Python-rendered bodies for these active local routes have been retired:

- `/studio/project-state/`
- `/studio/bulk-add-work/`
- `/studio/catalogue-field-registry/`
- `/studio/catalogue-status/`
- `/studio/studio-works/`
- `/studio/catalogue-series/`
- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-moment/`

The Thumbnail Quality route shell is no longer an active Local Studio route.
`/studio/thumbnail-quality/?mode=manage`, `POST /studio/api/catalogue/thumbnail-quality-preview`, and static thumbnail-quality preview data under `/studio/data/generated/thumbnail-quality/` are retired and intentionally have no Studio aliases, proxies, or static-serving shims.
The retired implementation has been archived under `studio/retired/thumbnail-quality/` for reference outside public Jekyll output.

Analytics tag and Data Sharing routes moved out of Local Studio.
Active route shells are served by `bin/local-analytics` under `/analytics/...`.
Retired Studio paths such as `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, and `/studio/api/data-sharing/...` intentionally have no aliases, proxies, or static shims.

Audit, risk, activity, testing, and UI Catalogue routes moved out of Local Studio.
Active route shells are served by `bin/local-admin` under `/admin/...`.
Retired Studio paths such as `/studio/audits/...`, `/studio/risk/...`, `/studio/activity/...`, and `/studio/ui-catalogue/...` intentionally have no aliases, proxies, or static shims.

## Sibling Route Surfaces

Docs Viewer, Admin, and Analytics/Data Sharing are sibling local apps with their own route shells.

- Docs Viewer manage mode is served by the standalone Docs Viewer service, not Local Studio.
- Public `/library/` and `/analysis/` are public read-only Docs Viewer routes, not Local Studio routes.
- Local Admin serves `/admin/...`, including `/admin/audits/`, `/admin/checks/`, `/admin/activity/`, `/admin/testing/`, and `/admin/ui-catalogue/...`.
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
