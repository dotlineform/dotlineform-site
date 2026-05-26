---
doc_id: studio-doc-viewer-dependencies
title: Studio Docs Viewer Dependencies
added_date: 2026-05-25
last_updated: 2026-05-26
ui_status: draft
parent_id: change-requests
sort_order: 10024
viewable: true
---
# Studio Docs Viewer Dependencies

This is a review note, not a change request.
It records the current places where Local Studio depends on the standalone Docs Viewer service so future cleanup or operational work can start from an explicit map.

Studio no longer hosts the Docs Viewer shell or proxies `/studio/api/docs/...`.
It now connects to Docs Viewer as a peer local service using `DOCS_VIEWER_BASE_URL` from `var/local/site.env`, with a default of `http://127.0.0.1:8776`.

## Current Dependency Boundary

The Studio-side integration owner is `studio/app/server/studio/studio_docs_viewer_integration.py`.
It validates the Docs Viewer service base URL as loopback HTTP with an explicit port, then builds:

- manage-mode viewer URLs such as `/docs/?scope=studio&doc=...&mode=manage`
- top-level Docs Viewer links for Studio navigation
- generated data read endpoints
- source-file opening endpoints
- Data Sharing document endpoints
- health and capabilities endpoints

`studio/app/server/studio/studio_app_config.py` publishes these values through `/studio/runtime-config.json`:

- `app.runtime.views[]`: Studio navigation targets and page implementation doc links
- `app.runtime.services.docs`: the configured Docs Viewer service endpoints
- `paths.routes.docs_page`: the configured Docs Viewer manage route
- `paths.routes.docs_html_import`: the configured Docs Viewer import route

Browser modules apply those runtime endpoints through `studio/app/frontend/js/studio-transport.js`.
If a route has not loaded runtime config yet, the browser fallback points at `http://127.0.0.1:8776`.

## Studio Page Locations

Top navigation:

- `studio/app/server/studio/studio_app_config.py`: `STUDIO_TOP_NAV_VIEW_IDS` includes `docs`
- `studio/app/server/studio/studio_app_views.py`: `studio_nav()` renders the configured Docs Viewer link
- `studio/app/frontend/js/studio-navigation.js`: runtime view navigation can route to the configured Docs Viewer URL

Page implementation links:

- `studio/app/server/studio/studio_app_config.py`: `STUDIO_VIEWS[*].doc_href` records the Studio page documentation target
- `studio_app_config.studio_views()` rewrites `/docs/?...` `doc_href` values to the configured Docs Viewer service URL
- `studio/app/server/studio/studio_app_views.py`: `studio_route_view()` renders the `i` link for normal Studio pages
- `studio/app/server/studio/studio_ui_catalogue_views.py`: UI Catalogue demo pages also render configured `doc_href` links

The current page doc-link inventory comes from `STUDIO_VIEWS` and includes the Studio landing/dashboard routes, Analytics tag routes, Data Sharing routes, Project State, Thumbnail Quality, Bulk Add Work, Activity, Catalogue Drafts, Studio Works, Catalogue editors, and UI Catalogue demo pages.

Data Sharing Prepare:

- route: `/studio/data-sharing/prepare/?mode=manage`
- page controller: `studio/app/frontend/js/data-sharing-prepare.js`
- generated docs index reader: `studio/app/frontend/js/data-sharing-prepare-docs.js`
- package prepare POST: `studio/app/frontend/js/data-sharing-prepare-service.js`
- Docs Viewer endpoints used: `/health`, `/docs/generated/index`, `/data-sharing/prepare`

Data Sharing Review:

- route: `/studio/data-sharing/review/?mode=manage`
- page controller: `studio/app/frontend/js/data-sharing-review.js`
- apply workflow: `studio/app/frontend/js/data-sharing-review-apply.js`
- Docs Viewer endpoints used: `/health`, `/data-sharing/returned-packages`, `/data-sharing/review`, `/data-sharing/apply`

Project State:

- route: `/studio/project-state/?mode=manage`
- page controller: `studio/app/frontend/js/project-state.js`
- Local Studio endpoint used for report generation: `/studio/api/catalogue/project-state-report`
- Local Studio endpoint used for local report opening: `/studio/api/catalogue/project-state-open-report`
- The route can run the report and open the latest Markdown snapshot when the Catalogue service is available.

Docs Viewer management itself:

- route: configured Docs Viewer service `/docs/?mode=manage`
- owner: `docs-viewer/services/docs_viewer_service.py`
- Local Studio only links to this route; it does not render or serve it.

## Service Endpoints Studio Knows About

`app.runtime.services.docs` currently advertises:

- `base`
- `health`
- `capabilities`
- `generated_index`
- `generated_search`
- `import_source`
- `import_source_files`
- `import_html`
- `import_html_files`
- `open_source`
- `data_sharing_prepare`
- `data_sharing_returned_packages`
- `data_sharing_review`
- `data_sharing_apply`

Not every Studio route uses every endpoint.
The broad list exists so shared Studio browser modules can use one runtime service contract.

## Review Issues

1. The all-services runner exists, but route copy and smoke coverage should stay aligned with it.
   Studio has several useful links and actions that require Docs Viewer to be running; `bin/local-all` starts Live Preview, Local Studio, and Docs Viewer together for that workflow.

2. Browser fallback endpoints can hide runtime-config mistakes.
   `studio-transport.js` falls back to `http://127.0.0.1:8776` if runtime config is unavailable or not applied.
   This keeps local defaults practical, but a non-default `DOCS_VIEWER_BASE_URL` depends on each route loading config and calling `configureStudioTransport()` before probing or posting.

3. The dependency names still mix old and new language.
   Frontend constants such as `DOCS_MANAGEMENT_ENDPOINTS` still describe Docs Viewer endpoints as "management" endpoints.
   That is understandable historically, but future cleanup should keep the distinction clear: Studio consumes the Docs Viewer service; Docs Viewer owns management.

4. `STUDIO_VIEWS["docs"]["script"]` still names the Docs Viewer runtime module even though Local Studio should not render the Docs Viewer page.
   This appears inert because the Docs view is now a peer-service navigation target, but it is a small contract smell in the Studio view registry.

5. Data Sharing is intentionally cross-boundary.
   Studio owns the visible Data Sharing route shells and adapter registry UI, while Docs Viewer owns document package endpoints and source writes.
   This is workable, but changes to Data Sharing should keep the adapter boundary explicit so document writes do not drift back into Studio-hosted Docs Viewer routes.

6. Service unavailability is route-specific.
   Docs navigation links fail normally when the service is stopped; Data Sharing document workflows show unavailable-service states; Project State no longer depends on Docs Viewer for local report opening.
   This is reasonable, but user-facing copy and smoke coverage need to stay aligned as the start-all workflow lands.

## Related Docs

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Docs Viewer Shell Extraction Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction-tasks)
