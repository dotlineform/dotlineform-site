---
doc_id: site-request-studio-javascript-app-shell-slice-1
title: Studio JavaScript App Shell Slice 1 Tasks
added_date: "2026-05-30 20:30"
last_updated: "2026-05-30 20:30"
ui_status: planned
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 1 Tasks

This is the first implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 1 is a contract slice.
It should define and verify the route registry and browser shell contract without migrating a Studio route yet.

## Status

### just done

- Created this slice tracker.
- Parent request now records the six-slice sequence:
  - route registry and shell contract
  - minimal JS shell plus one low-risk route
  - operational routes batch
  - catalogue support routes
  - catalogue editor family
  - Python shell-rendering retirement

### steer for next task

- Start with an inventory of current Python route shell metadata and current browser route assumptions.
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
| 1 | planned | Inventory the current Studio route-shell metadata in `studio/app/server/studio/studio_app_config.py`, `studio/app/server/studio/studio_app_views.py`, catalogue view helpers, and `studio/app/frontend/config/studio-config.json`. Record which fields are duplicated between Python, config, and route JavaScript. |
| 2 | planned | Choose the route-registry location and schema. The registry should cover route id, label, title, path, script, doc id, navigation visibility, shell type, and ready-state route id without moving route behavior yet. |
| 3 | planned | Add validation for the registry shape. Validation should catch duplicate route ids/paths, missing scripts for shell-routed pages, missing Docs Viewer doc ids, unsupported shell types, and stale route ids that no current Studio route serves. |
| 4 | planned | Add the smallest browser-side shell contract module or design stub needed for slice 2. It should define expected inputs/outputs and helper responsibilities without taking over an active route yet. |
| 5 | planned | Define the framework checkpoint evidence to collect in slices 2 and 3, including route-module lifecycle complexity, duplicated render/state helpers, modal/form orchestration pressure, build-step need, and smoke-test impact. |
| 6 | planned | Update owning docs for the decided route-registry and shell-contract boundary, including this tracker and the parent request. Do not rebuild docs payloads manually; let the watcher update generated payloads if running. |
| 7 | planned | Run slice verification: focused Python config tests, JavaScript syntax/module checks if new JS is added, stale-reference scan for duplicated route metadata, and `git diff --check`. |
| 8 | planned | Close slice 1 with a handoff to slice 2: selected first route candidate, migration prerequisites, acceptance checks, framework-checkpoint evidence to collect, generated-payload status, known risks, and whether a structured docs-log entry is warranted. |

## Slice 2 Handoff Requirements

Before slice 2 starts, this doc should identify:

- the first route to migrate
- the route shell fields it needs
- the Python shell code expected to be removed in that slice
- the route module boot contract to preserve
- the smoke test that proves the migrated route reaches ready state
- the framework-checkpoint evidence slice 2 should collect
- the fallback plan if the route requires server-rendered markup that should not move yet
