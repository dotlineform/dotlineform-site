---
doc_id: site-request-docs-viewer-route-config-handoff-tasks
title: Docs Viewer Route Config Handoff Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: in-progress
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12130
viewable: true
---
# Docs Viewer Route Config Handoff Tasks

This is the tracker for the next app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should move Docs Viewer route boot from many route-shell `#docsViewerRoot` data attributes toward a durable browser-safe route config record.
The intended end state is that route shells are closer to "mount plus route id/config URL" while `docs-viewer/runtime/js/docs-viewer-app-context.js` and `docs-viewer/runtime/js/docs-viewer-route-config.js` resolve the app's route context from config first and preserve current data attributes only as migration fallback.

This slice is structural app-shell work.
It should not implement source editing, semantic-reference views, activity views, panel toolbar generalization, new info views, third-party visualization modules, plugin architecture, or backend write behavior.
Those feature layers are tracked by separate change requests.

## Status

### just done

- Completed [Docs Viewer Info Panel Metadata View Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-info-panel-metadata-view-tasks).
- Added the visible info-panel shell, hosted-view lifecycle host, selected-document hosted-view context helper, and public-safe `metadata-info` hosted view.
- Preserved public read-only and local manage-mode behavior while keeping current route data attributes as boot-time migration input.

### steer for next task

- Deliver the route config handoff so route shells no longer need to carry every boot-time route, access, generated-data, and config URL field as individual data attributes.
- Treat `docs-viewer/runtime/js/docs-viewer-route-config.js` as the durable route-config resolver and `docs-viewer/runtime/js/docs-viewer-app-context.js` as the route-context assembler.
- Prefer a browser-safe generated or static config record that can describe `/docs/`, `/library/`, and `/analysis/` consistently.
- Keep current shell data attributes as a compatibility fallback during this slice unless removing one is proven safe by route-level smoke coverage.
- Preserve current public read-only behavior, management-mode behavior, scope switching, search/recent behavior, reports, bookmarks, and info-panel behavior.
- Do not add new feature-layer UI while doing this migration.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-context.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-route-config.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
  - any changed route-config, shell, config-loader, or route-context modules
- Focused module smoke checks:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for explicit route config resolution, config-first boot fallback, route id/config URL handling, missing config, malformed config, and data-attribute compatibility fallback
- Route/public read-only checks when route shells, generated config paths, or public route boot behavior changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
  - a focused desktop/mobile public smoke for `/library/` and `/analysis/` route boot, document selection, search/recent, info-panel open/close, and report loading where applicable
- Management checks when `/docs/` route config, management access projection, generated-data reads, or service shell output changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .` only if metadata modal refs, management modal shell, or editable metadata flows are touched
- Config/build checks when config generators or defaults change:
  - focused syntax checks for changed Python/Ruby config scripts with the configured interpreter
  - dry-run or focused builder verification before any write run, unless the slice explicitly requires generated config output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when the product code is healthy.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice should reduce route-shell assumptions and make the Docs Viewer easier to explain as one JavaScript app with public and local-editing contexts.
- Keep route config browser-safe. It may describe generated/static asset URLs, route intent, access defaults, panel defaults, and hosted-view records; it must not expose credentials, local filesystem paths, or write authority.
- Backend reachability and write availability remain capability-flow concerns, not browser-side route-config authority.
- Prefer direct browser reads for browser-safe generated/static config. Do not add a backend read endpoint unless the data is protected, local-only, or unavailable as a static asset.
- Keep `docs-viewer.js` readable as the compatibility boot orchestrator. Do not move route-config fetching, fallback, or validation logic into ad hoc local helpers inside it.
- Keep public read-only behavior first-class. `/library/` and `/analysis/` should not load management CSS or management-only JS.
- Keep local `/docs/` management behavior first-class. Manage-mode detection, generated-data reads through the service, action gating, and report behavior must continue to work.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current route config inputs and consumers: `_includes/docs_viewer_shell.html`, `docs-viewer/shell/docs-viewer-shell.html`, public route front matter/includes for `/library/` and `/analysis/`, local `/docs/` service shell generation, `docs-viewer-app-context.js`, `docs-viewer-route-config.js`, `docs-viewer-config-controller.js`, scope config defaults, public config defaults, router helpers, tests, and portable setup docs. Deliverable: short implementation note identifying which fields belong in durable route config, which remain scope config, and which remain backend capability state. |
| 2 | planned | Define the route config product surface. Include route id/type, default scope/doc, viewer base URL, generated base URL where public-safe, docs/search path records, config/UI/report URLs, scope-query policy, management intent defaults, panel defaults, hosted-view records, and migration fallback behavior. Exclude credentials, local filesystem paths, write authority, source editor feature state, semantic-reference feature state, and backend reachability. |
| 3 | planned | Decide the config source and ownership boundary: generated/static route config asset, existing Docs Viewer config default extension, inline JSON script record, or shell-provided route config URL. Prefer the smallest browser-safe config source that makes route shells thinner without creating a second config model. |
| 4 | planned | Extend `docs-viewer-route-config.js` so it can resolve route config from the chosen config record shape and keep current data-attribute fallback behavior. Keep validation/normalization in this focused owner rather than adding it to `docs-viewer.js`. |
| 5 | planned | Extend `docs-viewer-app-context.js` to assemble route context from config-first inputs and expose the same current route-context contract to downstream controllers. Preserve current public/manage access projection semantics. |
| 6 | planned | Thin the shared and standalone route shells only as far as the new config handoff supports safely. Keep required mounts and minimal route-config locator data. Do not remove compatibility data attributes until route-level verification proves fallback behavior and config-first behavior. |
| 7 | planned | Update config defaults or generation scripts if route config records are emitted from existing Docs Viewer config/scope config. Use dry-run behavior first and document generated-output ownership. |
| 8 | planned | Preserve scope switching in `/docs/?mode=manage`: selected scope should still update generated docs/search paths, default docs, viewer base URL, bookmark scope, and route history behavior without relying on removed shell attributes. |
| 9 | planned | Preserve public read-only `/library/` and `/analysis/`: route boot, document rendering, hash navigation, search/recent behavior, reports, bookmarks, info panel, and absence of management-only CSS/JS. |
| 10 | planned | Preserve local `/docs/` management behavior: manage-mode detection, management capability messages, generated-data reads, status pills, bookmark toggle, metadata edit flow, report rendering, browser history behavior, management action gating, and info panel. |
| 11 | planned | Add focused module smoke coverage for explicit route config resolution, config-first context assembly, data-attribute fallback, malformed or missing config behavior, access projection, route/scope projection, and hosted-view records. |
| 12 | planned | Add or update route-level browser smoke coverage for public and manage route boot after shell thinning. Verify document selection, search/recent, report loading, info panel open/close, and URL behavior. |
| 13 | planned | Run targeted verification for changed JS, route shell output, public read-only behavior, manage-mode behavior, Jekyll build, and any changed config generators. Record skipped checks and why. |
| 14 | planned | Update owning docs after implementation. At minimum update this tracker, the app-shell request, Docs Viewer runtime docs, runtime boundary docs, portable setup docs if route install instructions change, config docs if config ownership changes, and Docs Viewer JavaScript inventory notes if ownership or risk materially changes. |
| 15 | planned | Create a structured docs-log entry when the slice is complete and record the entry id in this tracker. |

The closeout for this slice should confirm:

- route shells are measurably thinner or have a documented path to becoming mount-plus-config shells
- route config resolves from a durable browser-safe record before falling back to legacy data attributes
- `docs-viewer.js` remains orchestration-only for this responsibility
- public read-only routes still avoid management-only assets and write-capable state
- local manage mode still gets backend capability checks from the management flow, not from static route config
- current index, document, search/recent, report, bookmark, info-panel, public read-only, and management behavior still works
- source editor, editable metadata, semantic-reference views, activity views, panel toolbar generalization, third-party visualization modules, and plugin architecture remain separate feature-layer work
