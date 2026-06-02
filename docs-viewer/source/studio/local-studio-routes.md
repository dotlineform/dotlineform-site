---
doc_id: local-studio-routes
title: Local Studio Routes
added_date: 2026-06-02
last_updated: 2026-06-02
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
- `/studio/audits/?mode=manage`
- `/studio/risk/?mode=manage`
- `/studio/project-state/?mode=manage`
- `/studio/bulk-add-work/?mode=manage`
- `/studio/activity/?mode=manage`
- `/studio/catalogue-field-registry/?mode=manage`
- `/studio/catalogue-status/?mode=manage`
- `/studio/studio-works/?mode=manage`
- `/studio/catalogue-series/?mode=manage`
- `/studio/catalogue-work/?mode=manage`
- `/studio/catalogue-work-detail/?mode=manage`
- `/studio/catalogue-moment/?mode=manage`

The local app owns `/studio/`.
Studio home navigation is rendered by the JavaScript Studio app shell, not Python or Jekyll/Liquid page data.
The local home exposes Studio-owned Catalogue and Admin links through `studio-home-shell.js` by grouping route IDs from `app.routes`; route labels and base paths come from the runtime route registry, while the home layout owns grouping, order, and route-specific query-string defaults.
The shared Studio top navigation is separate from that home link list.
Every local Studio shell, including `/studio/`, shows the same compact top row: `dotlineform studio` on the left, with `docs` plus the light/dark toggle right-aligned.

## JavaScript Shell Pattern

Operational Studio route shells are hosted by the local app.
For active JavaScript-shell routes, Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, route-local `*-shell.js` modules render the body markup, and the route controller keeps route boot and behavior.

Current JavaScript-shell route families:

- Studio Audits:
  `studio-audits-shell.js` renders the body and `studio-audits.js` owns route behavior.
- Studio Risk:
  `studio-risk-shell.js` renders the body and `studio-risk.js` owns route behavior.
- Project State:
  `project-state-shell.js` renders the body and `project-state.js` owns route behavior.
- Bulk Add Work:
  `bulk-add-work-shell.js` renders the body and `bulk-add-work.js` owns route behavior.
- Studio Activity:
  `activity-log-shell.js` renders the body and `activity-log.js` owns route behavior.
- Catalogue Field Registry:
  `catalogue-field-registry-shell.js` renders the body and `catalogue-field-registry-review.js` owns route behavior.
- Catalogue Drafts:
  `catalogue-status-shell.js` renders the body and `catalogue-status.js` owns route behavior.
- Studio Works:
  `studio-works-shell.js` renders the body and `studio-works.js` owns route behavior.
- Catalogue editors:
  route-local editor `*-shell.js` modules render the body and the existing editor controllers own route behavior.

The Catalogue Series, Work, Work Detail, and Moment editor route shells are hosted by the local app at their `?mode=manage` routes.
The editor shell media attributes are projected in the browser from `app.runtime.media` and `app.runtime.pipeline`.
They reuse the existing vanilla editor modules and call local-app catalogue API endpoints under `/studio/api/catalogue/...`.

## Retired Local Routes

The former Catalogue dashboard page is retired.
Its links now live on the `/studio/` home page, and metrics belong on the individual pages where they are relevant.

The old Jekyll shells and Python-rendered bodies for these active local routes have been retired:

- `/studio/audits/`
- `/studio/project-state/`
- `/studio/bulk-add-work/`
- `/studio/activity/`
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

## Sibling Route Surfaces

Docs Viewer, Analytics/Data Sharing, and UI Catalogue are sibling local apps with their own route shells.

- Docs Viewer manage mode is served by the standalone Docs Viewer service, not Local Studio.
- Public `/library/` and `/analysis/` are public read-only Docs Viewer routes, not Local Studio routes.
- Local Analytics serves `/analytics/...` and `/analytics/api/...`.
- UI Catalogue demo routes are standalone reference surfaces under `/ui-catalogue/demos/` and are not Studio route shells.

The local `/docs/` route is no longer hosted by Local Studio.
The runtime config exposes the plain Docs Viewer link target for the top-level `docs` view.
Page implementation links render with `data-studio-doc-view`; the browser resolves those targets from the matching route record's `doc_id`.
The browser builds external Docs Viewer URLs from `external_links.docs_viewer` plus the route `doc_id`.

## Page-Level Doc Links

Current page-level doc links:

- Studio Activity -> `/docs/?scope=studio&doc=studio-activity`
- Studio Audits -> `/docs/?scope=studio&doc=studio-audits`
- Bulk Add Work -> `/docs/?scope=studio&doc=bulk-add-work`
- Catalogue Moment Editor -> `/docs/?scope=studio&doc=catalogue-moment-editor`
- Catalogue Work Editor -> `/docs/?scope=studio&doc=catalogue-work-editor`
- Catalogue Work Detail Editor -> `/docs/?scope=studio&doc=catalogue-work-detail-editor`
- Catalogue Series Editor -> `/docs/?scope=studio&doc=catalogue-series-editor`
- Studio Works -> `/docs/?scope=studio&doc=studio-works`
- Studio landing and dashboards -> phased-plan and domain-plan docs
- Library Import -> `/docs/?scope=studio&doc=user-guide-docs-html-import`

## Route Checks

Current focused route shell checks:

- `studio/tests/smoke/local_studio_app_audits_route.py`
- `studio/tests/smoke/local_studio_app_risk_route.py`
- `studio/tests/smoke/local_studio_app_project_state_route.py`
- `studio/tests/smoke/local_studio_app_bulk_add_work_route.py`
- `studio/tests/smoke/local_studio_app_activity_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_status_route.py`
- `studio/tests/smoke/local_studio_app_studio_works_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`
- `studio/tests/smoke/local_studio_app_docs_viewer.py`

Docs Viewer fixture smokes cover `/docs/` manage-mode workflows through the Docs Viewer service UI.
Public `/library/` and `/analysis/` are covered by `docs-viewer/tests/smoke/public_docs_viewer_readonly.py`.
