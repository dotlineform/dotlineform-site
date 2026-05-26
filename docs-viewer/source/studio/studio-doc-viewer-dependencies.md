---
doc_id: studio-doc-viewer-dependencies
title: Studio Docs Viewer Dependencies
added_date: 2026-05-25
last_updated: 2026-05-26
ui_status: paused
parent_id: change-requests
sort_order: 10024
viewable: true
---
# Studio Docs Viewer Dependencies

status: cleanup tasks done apart from data sharing which is a separate request

This is a review note and cleanup task list, not a change request.
It records the remaining narrow places where Local Studio should know about the standalone Docs Viewer service after Data Sharing architecture work is split out.

Data Sharing service ownership is intentionally out of scope here.
That architecture decision is tracked by [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture).

## Target Boundary

Studio should depend on Docs Viewer only for links:

- the top navigation Docs link
- Studio page implementation/document links rendered as `doc_href`

Studio should not publish or consume Docs Viewer service API endpoints for generated reads, import operations, source opening, capabilities, or Data Sharing workflows as part of this cleanup.
The Data Sharing endpoint removal depends on the separate architecture request.

## Current Link Boundary

The Studio-side link owner is `studio/app/server/studio/studio_docs_viewer_integration.py`.
It validates `DOCS_VIEWER_BASE_URL` as loopback HTTP with an explicit port, then builds manage-mode Docs Viewer URLs such as `/docs/?scope=studio&doc=...&mode=manage`.

`studio/app/server/studio/studio_app_config.py` publishes these link values through `/studio/runtime-config.json`:

- `app.runtime.views[]`: Studio navigation targets and page implementation doc links
- `STUDIO_VIEWS["docs"].path`: the configured Docs Viewer manage route for top navigation
- `STUDIO_VIEWS[*].doc_href`: configured Docs Viewer links for Studio page documentation

## Active Studio Link Locations

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

Docs Viewer management itself:

- route: configured Docs Viewer service `/docs/?mode=manage`
- owner: `docs-viewer/services/docs_viewer_service.py`
- Local Studio only links to this route; it does not render or serve it.

## Cleanup Tasks

1. Completed: remove the configured Docs Viewer import route from Studio config.
   `paths.routes.docs_html_import` appears to be a Studio config/test artifact, while Docs Viewer owns `/docs/?mode=manage&import=1`.
   Removed from:
   - `studio/app/frontend/config/studio-config.json`
   - `studio/app/frontend/js/studio-config.js`
   - `studio/app/server/studio/studio_docs_viewer_integration.py`
   - `studio/tests/python/test_studio_app_server.py`

2. Completed: remove `paths.routes.docs_page`.
   Active navigation uses `runtime.views["docs"].path`, and current references suggest `docs_page` is also config/test-only.
   It was removed from Studio config and tests.

3. Completed: remove the inert Docs Viewer script entry from the Studio view registry.
   `STUDIO_VIEWS["docs"]["script"]` still points to `/docs-viewer/runtime/js/docs-viewer.js`, but Local Studio should not render the Docs Viewer page.
   The Docs view is now a navigation target only.

4. Partially completed: reduce `studio_docs_viewer_integration.py` to link helpers.
   Kept:
   - `docs_viewer_base_url`
   - `validate_docs_viewer_base_url`
   - `docs_viewer_url`
   - `docs_viewer_manage_url`
   - doc-link and nav-link rewriting

   Removed import-route and broad Docs Viewer management endpoint construction.
   The remaining `docs_viewer_service_endpoints()` function exposes only the endpoints current Data Sharing still consumes; remove it after the Data Sharing architecture request lands.

5. Partially completed: remove frontend Docs Viewer service transport.
   Removed `DOCS_MANAGEMENT_ENDPOINTS`, `probeDocsManagementHealth()`, and non-Data-Sharing endpoint fallback mutation.
   `DATA_SHARING_ENDPOINTS` still points at the configured Docs Viewer service until [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture) replaces it with same-origin Studio endpoints.

6. Completed: update runtime config tests to assert the intended boundary.
   The focused server test now asserts:
   - Docs nav view points to the configured Docs Viewer manage URL
   - page `doc_href` links point to configured Docs Viewer URLs
   - no `docs_html_import` route is present in Studio config
   - `app.runtime.services.docs` contains only the temporary Data Sharing service contract

7. Ongoing: keep Data Sharing out of this cleanup slice.
   Remove Data Sharing endpoint assertions from this note only after [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture) lands or defines the replacement same-origin Studio endpoints.

## Verification

Focused checks for the link-only cleanup:

```bash
rg -n "docs_html_import|DOCS_MANAGEMENT_ENDPOINTS|app.runtime.services.docs|services.docs|DOCS_VIEWER_BASE_URL" studio
$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py
```

Data Sharing smoke checks belong to the separate architecture request if endpoint ownership changes in the same implementation batch.

## Related Docs

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture)
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Docs Viewer Shell Extraction Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction-tasks)
