---
doc_id: site-request-studio-javascript-app-shell-slice-1
title: Studio JavaScript App Shell Slice 1 Tasks
added_date: "2026-05-30 20:30"
last_updated: "2026-05-30 21:25"
ui_status: done
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 1 Tasks

This is the first implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 1 is a contract slice.
It should define and verify the route registry and browser shell contract without migrating a Studio route yet.

## Status

### just done

- Chose `app.routes` in `studio/app/frontend/config/studio-config.json` as the Studio route registry.
- Added route-registry validation in `studio/app/server/studio/studio_app_config.py`.
- Derived runtime `app.runtime.views` from the route registry instead of Python `STUDIO_VIEWS`.
- Added `studio/app/frontend/js/studio-route-registry.js` as the browser-side shell contract helper for slice 2.
- Updated focused Python and browser-module checks.
- Updated owning runtime/request docs.

### inventory notes

- Before this slice, route shell metadata was duplicated across Python `STUDIO_VIEWS`, `paths.routes` in `studio-config.json`, `external_links.docs_viewer.doc_ids`, the generated `DEFAULT_STUDIO_CONFIG` in `studio-config.js`, and route-specific Python view helpers that supplied body roots and ready-state attributes.
- The route registry now owns route id, label, title, path, script, doc id, navigation visibility, shell type, and ready-state route id.
- `paths.routes` now remains for public/content paths such as `/works/`, `/series/`, `/library/`, and `/analysis/`.
- Python route view helpers still own route-specific body HTML until each route migrates.
- The `/studio/` home link columns remain static Python view data and are not part of slice 1.

### steer for slice 2

- Start with Project State as the first migrated route candidate.
- Keep Analytics, Data Sharing, Docs Viewer, and UI Catalogue outside this Studio shell migration.
- Preserve current Studio URLs, backend API endpoints, ready-state attributes, static allowlists, write allowlists, and activity behavior.
- Treat Ruby/Jekyll retirement as a separate future request; do not mix it into this slice.

### baseline verification set

Run only the checks warranted by each touched slice.
For slice 1 close-out, the expected verification set is:

- focused Python tests for Studio runtime config and route metadata
- focused JavaScript syntax checks for any new shell/registry modules
- focused browser-module smoke if a new browser module is added
- stale-reference scan for route metadata duplication introduced by the slice
- `git diff --check`

Codex sandbox note: browser/module smokes that start a temporary localhost server need elevated permissions even when the product code is healthy.

### general steer

- This slice should produce a durable contract, not a partial route migration.
- Prefer a small route-registry shape that can be extended in later slices.
- Do not add compatibility aliases for old Studio Analytics/Data Sharing routes.
- Do not move write authority into the browser.
- Avoid introducing a framework; the shell should be plain JavaScript until the ownership boundary is proven.
- Capture evidence for a later framework checkpoint, but do not choose or install a framework in slice 1.

## Target Contract To Decide

The slice should answer these questions before route migration starts:

- Where does Studio route metadata live: `app.routes`, `app.runtime.routes`, or another named config key?
- Which fields are required for a shell-rendered route?
- How does JavaScript resolve the active route from the current URL?
- Does a route module export a mount function, or does slice 2 keep side-effect route boot for the first migrated route?
- Which shell types are needed initially?
- How are Docs Viewer doc links built from `external_links.docs_viewer` and route `doc_id`?
- What validation catches missing route metadata, duplicate paths, missing scripts, or missing doc IDs?
- What evidence should slices 2 and 3 collect to decide whether vanilla JavaScript remains sufficient or a framework evaluation is warranted?

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory the current Studio route-shell metadata in `studio/app/server/studio/studio_app_config.py`, `studio/app/server/studio/studio_app_views.py`, catalogue view helpers, and `studio/app/frontend/config/studio-config.json`. Record which fields are duplicated between Python, config, and route JavaScript. |
| 2 | done | Choose the route-registry location and schema. The registry should cover route id, label, title, path, script, doc id, navigation visibility, shell type, and ready-state route id without moving route behavior yet. |
| 3 | done | Add validation for the registry shape. Validation should catch duplicate route ids/paths, missing scripts for shell-routed pages, missing Docs Viewer doc ids, unsupported shell types, and stale route ids that no current Studio route serves. |
| 4 | done | Add the smallest browser-side shell contract module or design stub needed for slice 2. It should define expected inputs/outputs and helper responsibilities without taking over an active route yet. |
| 5 | done | Define the framework checkpoint evidence to collect in slices 2 and 3, including route-module lifecycle complexity, duplicated render/state helpers, modal/form orchestration pressure, build-step need, and smoke-test impact. |
| 6 | done | Update owning docs for the decided route-registry and shell-contract boundary, including this tracker and the parent request. Do not rebuild docs payloads manually; let the watcher update generated payloads if running. |
| 7 | done | Run slice verification: focused Python config tests, JavaScript syntax/module checks if new JS is added, stale-reference scan for duplicated route metadata, and `git diff --check`. |
| 8 | done | Close slice 1 with a handoff to slice 2: selected first route candidate, migration prerequisites, acceptance checks, framework-checkpoint evidence to collect, generated-payload status, and known risks. |

## Slice 2 Handoff Requirements

Before slice 2 starts, this doc should identify:

- First route to migrate: Project State.
- Route shell fields needed: `project_state.label`, `title`, `path`, `script`, `doc_id`, `shell_type`, and `ready_state_route_id`.
- Python shell code expected to move in slice 2: `project_state_view()` body markup in `studio/app/server/studio/studio_app_views.py`; the generic `studio_route_view()` wrapper should remain until more routes migrate.
- Route module boot contract to preserve: `studio/app/frontend/js/project-state.js` can keep side-effect route boot for slice 2 unless that route proves a mount export is materially simpler. It must still load config/UI text, probe catalogue availability, wire Run/Open controls, and set `data-studio-ready` / `data-studio-busy` through the existing route-state helpers.
- Smoke test: extend or add a focused Project State route smoke that loads `/studio/project-state/?mode=manage`, waits for the route root, verifies `data-studio-ready="true"`, and verifies the Docs Viewer `i` link resolves through route `doc_id`.
- Framework evidence to collect: route-shell code size, route-specific DOM construction complexity, repeated render/state helpers, modal/form orchestration pressure, whether side-effect boot causes ordering problems, whether a build step would reduce or increase smoke-test friction, and how much test setup is needed to verify route mounting.
- Fallback plan: if Project State needs server-rendered markup longer than expected, keep `shell_type: "python"`, record the blocker here, and choose Audits as the next low-risk candidate rather than widening the migration.

## Slice 1 Closeout

Verification completed:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_config.py studio/app/server/studio/studio_app_views.py studio/tests/python/test_studio_app_server.py studio/tests/smoke/studio_operational_route_modules.py studio/tests/smoke/local_studio_navigation_adapter.py studio/tests/smoke/local_studio_app_docs_viewer.py`
- `node --check studio/app/frontend/js/studio-config.js`
- `node --check studio/app/frontend/js/studio-navigation.js`
- `node --check studio/app/frontend/js/studio-route-registry.js`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py -q`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/studio_operational_route_modules.py --site-root .`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_navigation_adapter.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_docs_viewer.py`
- `rg -n "external_links\\.docs_viewer\\.doc_ids|doc_ids\\]|doc_ids\\.|\\\"doc_ids\\\"" docs-viewer/source/studio studio/app studio/tests`
- `git diff --check`

Generated payload status: docs watcher regenerated Studio docs/search payloads while source docs were edited; those generated updates were not manually rebuilt by Codex.

Known risks:

- Local Studio still has Python-rendered route bodies, so route body markup duplication will only reduce once slices 2-5 migrate routes.
- `studio-config.js` still carries a fallback copy of the route registry for static/default config behavior; keep it aligned with checked-in JSON until a generated/default-config strategy replaces the copy.
- The static `/studio/` home link columns still duplicate route labels and paths. Leave that out of slice 2 unless the shell renderer needs home-link metadata.
