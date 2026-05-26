---
doc_id: studio-doc-viewer-dependencies
title: Studio Docs Viewer Dependencies
added_date: 2026-05-25
last_updated: 2026-05-26
ui_status: done
parent_id: change-requests
sort_order: 10000
viewable: true
---
# Studio Docs Viewer Dependencies

status: done

This was a review note and cleanup task list, not a change request.
It is complete: Local Studio no longer models Docs Viewer as a runtime service.
Docs Viewer remains a separate application; Studio only carries plain external Docs Viewer links in user-facing config.

## Target Boundary

Studio depends on Docs Viewer only for links:

- the top navigation Docs link
- Studio page implementation/document links rendered with `data-studio-doc-view`

Studio does not publish or consume Docs Viewer service API endpoints for generated reads, import operations, source opening, capabilities, or Data Sharing workflows.
Data Sharing uses the Studio-owned `/studio/api/data-sharing/...` boundary and adapter registry instead of Docs Viewer HTTP.

## Current Link Boundary

Docs Viewer links are plain config plus browser-side URL construction.
The user-facing config lives in `studio/app/frontend/config/studio-config.json` under `external_links.docs_viewer`.
The default link shape is base URL plus `/docs/` plus query params such as `scope`, `doc`, and `mode`.
Per-page documentation targets live in `external_links.docs_viewer.doc_ids`, keyed by Studio view ID.

`studio/app/server/studio/studio_app_config.py` publishes view metadata through `/studio/runtime-config.json`:

- `app.runtime.views[]`: Studio navigation targets
- `STUDIO_VIEWS["docs"].path`: the plain Docs Viewer target path for top navigation
- `external_links.docs_viewer.doc_ids`: user-facing Studio page documentation targets
- `external_links.docs_viewer`: the configured external Docs Viewer base and default link policy

## Active Studio Link Locations

Top navigation:

- `studio/app/server/studio/studio_app_config.py`: `STUDIO_TOP_NAV_VIEW_IDS` includes `docs`
- `studio/app/server/studio/studio_app_views.py`: `studio_nav()` renders the configured Docs Viewer link
- `studio/app/frontend/js/studio-navigation.js`: builds the external Docs Viewer URL from `external_links.docs_viewer`

Page implementation links:

- `studio/app/frontend/config/studio-config.json`: `external_links.docs_viewer.doc_ids` records the Studio page documentation target per view
- `studio/app/server/studio/studio_app_views.py`: `studio_route_view()` renders the `i` link with `data-studio-doc-view`
- `studio/app/server/studio/studio_ui_catalogue_views.py`: UI Catalogue demo pages also render `data-studio-doc-view`
- `studio/app/frontend/js/studio-navigation.js`: resolves `data-studio-doc-view` through `external_links.docs_viewer.doc_ids` and rewrites `/docs/...` anchors to the configured external Docs Viewer base when Studio navigation initializes

The current page doc-link inventory comes from `external_links.docs_viewer.doc_ids` and includes the Studio landing/dashboard routes, Analytics tag routes, Data Sharing routes, Project State, Thumbnail Quality, Bulk Add Work, Activity, Catalogue Drafts, Studio Works, Catalogue editors, and UI Catalogue demo pages.

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
   The Docs view is now a navigation target only.

4. Completed: remove the Python Docs Viewer integration helper.
   `studio/app/server/studio/studio_docs_viewer_integration.py` was removed.
   Studio no longer validates Docs Viewer URLs, shapes Docs Viewer service endpoints, or rewrites Docs Viewer links in Python.

5. Completed: remove frontend Docs Viewer service transport.
   Removed `DOCS_MANAGEMENT_ENDPOINTS`, `probeDocsManagementHealth()`, and non-Data-Sharing endpoint fallback mutation.
   `DATA_SHARING_ENDPOINTS` now resolves through `app.runtime.services.data_sharing`.

6. Completed: update runtime config tests to assert the intended boundary.
   The focused server test now asserts:
   - Docs nav view uses a plain `/docs/?mode=manage` target
   - runtime views do not publish `doc_href`
   - page doc IDs come from `external_links.docs_viewer.doc_ids`
   - no `docs_html_import` route is present in Studio config
   - `app.runtime.services.docs` is not published
   - `external_links.docs_viewer` carries the Docs Viewer base URL and link policy
   - `app.runtime.services.data_sharing` contains the replacement same-origin Studio endpoints

7. Completed: keep Data Sharing transport on the Studio API boundary.
   Data Sharing endpoint assertions now live on `app.runtime.services.data_sharing`; the Docs Viewer runtime service namespace no longer carries them.

## Verification

Focused checks for the link-only cleanup:

```bash
rg -n "docs_html_import|DOCS_MANAGEMENT_ENDPOINTS|app.runtime.services.docs|services.docs|DOCS_VIEWER_BASE_URL|studio_docs_viewer_integration" studio
$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py
```

## Related Docs

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture)
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Docs Viewer Shell Extraction Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction-tasks)
