---
doc_id: site-request-analytics-app-split-tasks
title: Analytics App Split Tasks
added_date: 2026-05-30
last_updated: 2026-05-30
ui_status: urgent
parent_id: site-request-analytics-app-split
viewable: true
---
# Analytics App Split Tasks

This is the tracker for implementing [Analytics App Split Request](/docs/?scope=studio&doc=site-request-analytics-app-split).

## Status

### just done

- Split the first Analytics/Data Sharing test boundary slice:
  - moved the Studio Data Sharing API pytest to `analytics-app/tests/python/test_analytics_data_sharing_api.py`
  - added `analytics-app/tests/python/test_analytics_app_server.py` for Analytics runtime, tag read, tag write dry-run, data-sharing endpoint, and static policy checks
  - moved the active tag route and data-sharing route browser smokes to `analytics-app/tests/smoke/`
  - added an `analytics-smoke` check profile and removed Analytics/Data Sharing smokes from the `studio-smoke` profile
  - retargeted Docs Viewer/Data Sharing tests away from deleted Studio data-sharing API modules
  - retargeted the shared tags data-sharing adapter away from deleted `studio.data_sharing_adapters`
- Added the missing Analytics-owned `catalogue-public-links.js` helper used by the series tag editor route.
- Added public-preview/production site bases to the Analytics runtime config so Analytics routes can build public catalogue links without depending on Studio runtime config.
- Verified `quick` and the new `analytics-smoke` profile pass.
- Paused the running `bin/local-all` stack before file moves: public preview, Local Studio, Docs Viewer service, and docs live rebuild watcher were stopped.
- Inventoried the current Analytics/Data Sharing/UI Catalogue/thumbnail-quality route, API, frontend, config, test, and docs surfaces.
- Added a standalone Local Analytics app under `analytics-app/` with `/analytics/` routes, `/analytics/api/...` tag endpoints, `/analytics/api/data-sharing/...` endpoints, copied frontend modules/UI text, copied CSS, and `bin/local-analytics`.
- Updated `bin/local-all` so Analytics starts separately on `ANALYTICS_APP_PORT` (default `8766`).
- Removed active Analytics/Data Sharing route and API dispatch from Local Studio. Old `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, and `/studio/api/data-sharing/...` paths now fail instead of aliasing.
- Deleted the old Studio-owned Analytics/Data Sharing API adapter modules from `studio/app/server/studio/`.
- Verified the new Analytics server health/runtime/API/page smoke and verified Studio no longer exposes the old Analytics/Data Sharing routes in runtime config.

### steer for next task

- Continue task 8 with the remaining unprofiled Studio-location Analytics/Data Sharing smokes:
  - `studio/tests/smoke/local_studio_analytics_*`
  - `studio/tests/smoke/local_studio_app_tag_groups.py`
  - `studio/tests/smoke/data_sharing_prepare.py`
  - `studio/tests/smoke/data_sharing_review.py`
  - `studio/tests/smoke/data_sharing_prepare_modules.py`
  - `studio/tests/smoke/tag_registry_modules.py`
  - ready-state/modal/render smokes that still hardcode `/studio/analytics/...`
- Keep the preserved `var/studio/data-sharing/...` artifact path assertions; those remain data artifact contracts, not active Studio routes.
- Continue the smoke split before running broad checks; do not treat unprofiled old-route smokes as proof of active Studio compatibility.
- Preserve the clean cutover: do not add aliases or proxy handlers for the retired Studio paths to make old tests pass.

### baseline verification set

Run only the checks warranted by the touched slice.
The final cutover should include:

- Python syntax/import checks for new Analytics app server files and moved API adapters.
- Focused pytest for tag mutation/source/transaction modules.
- Focused pytest for data-sharing service and adapter dispatch.
- Analytics health endpoint smoke.
- Analytics tag route smoke for registry, aliases, groups, series tags, and series tag editor.
- Analytics API smoke for tag reads and representative dry-run writes.
- Analytics data-sharing smoke for prepare/review route readiness and API health.
- Studio smoke for core catalogue routes after analytics/data-sharing removal.
- Split-service checks for tests that currently cover both future Studio and Analytics responsibilities.
- Standalone UI Catalogue smoke.
- Check that thumbnail-quality is no longer exposed as an active Studio route.

Codex sandbox note: local service, browser, and temporary localhost checks will need elevated permissions even when the product code is healthy.

### general steer

- Preserve current UI, workflows, source data behavior, dry-run behavior, write allowlists, backup behavior, and compact logging.
- No compatibility aliases, proxies, dual-read paths, dual-write paths, static mount shims, or import fallbacks for retired Studio analytics/data-sharing routes.
- Do not keep old Studio paths working to make tests easier; update tests to the new owner.
- No new Analytics features in the split.
- No broad redesign, CSS class rename pass, or cosmetic cleanup.
- Decouple Studio helpers/CSS during the split where it is cheap, obvious, and does not turn the cutover into a redesign.
- If any coupling remains after the basic split is tested, write a specific follow-on task to be completed before close-out.
- UI Catalogue should become completely standalone, not Studio-hosted or with any Studio dependencies.
- Thumbnail quality should become retired tooling, not an active Studio route.
- Update source docs, not generated docs payloads, unless a separate rebuild is intentionally run.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Confirm the cutover path, identify currently running local services, and pause Studio, Docs Viewer, docs watcher, Analytics-related local routes, and public preview before file moves or route changes. |
| 2 | done | Inventory current analytics, data-sharing, UI Catalogue, thumbnail-quality, and mixed Studio/Analytics tests so the move list, retired routes, and test split are explicit before implementation starts. |
| 3 | done | Add a standalone Analytics app server and launcher using the current Studio analytics/data-sharing views, config, static serving, API adapters, CORS checks, and loopback-only behavior as the starting point. |
| 4 | done | Move or copy the current analytics and data-sharing frontend modules and UI text into Analytics-owned app paths with minimal code changes. Preserve UI behavior and current interface. |
| 5 | done | Move Analytics API ownership out of Studio, including tag health/read/write endpoints, while preserving current service behavior and write safeguards. |
| 6 | done | Move Data Sharing API ownership out of Studio, including prepare/review/apply, selectable records, returned packages, adapter dispatch, and current activity hooks. |
| 7 | done | Remove Studio analytics/data-sharing routes, nav/home links, runtime-config service endpoints, API dispatch, and static serving assumptions. Old routes should fail clearly; do not add redirects, aliases, proxy handlers, static shims, or dual-path config. |
| 8 | in progress | Split mixed Studio/Analytics tests into separate service-boundary checks before final verification. Keep Analytics checks for tags/data sharing and Studio checks for catalogue/admin route health. Rename purely Analytics checks to Analytics ownership. |
| 9 | planned | Remove the thumbnail-quality page from active Studio routes, navigation, runtime config, and smokes. Archive its page/script code in a repo-local retired tooling location, separate from the public Jekyll site |
| 10 | planned | Move UI Catalogue out of Studio routing and service startup. Keep it available as a standalone local static page or simple local HTML-server surface with its isolated CSS and JS helpers. |
| 11 | planned | Run a basic split verification pass: Analytics route/API smoke checks, tag/data-sharing pytest checks, and a small Studio catalogue/admin smoke to prove the primary split works before decoupling helper/CSS dependencies. |
| 12 | planned | Decouple any remaining Studio helper/CSS dependencies/paths/assets in Analytics. |
| 13 | planned | Update source ownership, runtime dependency, local setup, service launcher, and affected request docs to describe Studio, Analytics, Docs Viewer, UI Catalogue, retired thumbnail tooling, and public-preview boundaries. |
| 14 | planned | Run the final focused verification set and confirm no compatibility layers remain: no old route aliases, no proxy handlers, no dual-read/write fallbacks, no copied static serving shims, and no tests depending on old Studio analytics/data-sharing paths. |
| 15 | planned | Ensure durable documents in `/docs/` have been updated to explain the new service responsibilities, boundaries and architecture. This change request and task tracker will be archived and later deleted. |
| 16 | planned | Close out with moved-path summary, retired Studio routes/endpoints, verification results, generated-payload status, remaining self-contained Analytics risks, structured docs-log entries, and parent-request status updates. |

Close-out must confirm that any cleanup has not been deferred.
