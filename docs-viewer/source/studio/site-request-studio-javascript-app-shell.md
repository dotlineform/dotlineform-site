---
doc_id: site-request-studio-javascript-app-shell
title: Studio JavaScript App Shell Request
added_date: 2026-05-26
last_updated: "2026-05-30 20:30"
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Studio JavaScript App Shell Request

Status:

- in progress
- The first implementation tracker is [Studio JavaScript App Shell Slice 1 Tasks](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell-slice-1).

## Summary

Move Local Studio toward a JavaScript-owned app shell.

The target shape is not "remove Python." The target is a clearer boundary:

- JavaScript owns Studio UI composition, route shells, navigation, doc links, route mounting, and client-side state.
- User-facing config owns labels, route metadata, external link bases, per-page Docs Viewer doc IDs, UI text, and feature settings.
- Python owns loopback APIs, write services, filesystem access, backups, validation, reports, allowlisted command execution, and source-data reads that should not be browser-file reads.

This would replace the current mixed shell model where Python renders HTML route shells and JavaScript then repairs or enhances parts of those shells after load.

## Reason

Recent Data Sharing and Docs Viewer boundary work made the direction clearer.

Studio and Docs Viewer are separate concepts. Studio should not know how Docs Viewer works internally; it should only know the configured external Docs Viewer link target and the doc IDs it wants to open. The latest link cleanup moved Docs Viewer service endpoints out of Studio and moved page documentation targets into `external_links.docs_viewer.doc_ids`.

However, the current implementation is still mixed:

- Python renders route HTML.
- Python decides the route shell structure.
- JavaScript owns most route behavior after load.
- Config owns some user-facing settings.
- JavaScript sometimes rewrites shell output that Python emitted only as a placeholder.

That mixed ownership adds conceptual overhead. When a feature changes, it is not always obvious whether the owning layer is Python view rendering, runtime config, route JavaScript, or static config. A JavaScript-owned app shell would make the boundary simpler: Python provides data and write APIs; JavaScript builds the Studio application.

## Goals

- make JavaScript the owner of Studio route shell composition
- keep Python as the trusted local backend for writes and filesystem operations
- move route shell metadata into user-facing config where it is reasonable to edit without code changes
- keep route modules small and focused on route behavior rather than page-frame boilerplate
- reduce Python HTML string rendering for ordinary Studio pages
- make Docs Viewer links, public-site links, and Studio internal links resolve through one browser-side navigation layer
- make future Studio routes easier to add without copying Python shell templates
- preserve current URLs and route-ready contracts during migration

## Non-Goals

- replacing Python write services with browser filesystem writes
- exposing arbitrary shell commands to the browser
- converting Studio into a public hosted app
- introducing a large framework before the ownership boundary is proven
- rewriting every route in one implementation batch
- changing catalogue, analytics, audit, or Data Sharing API semantics as part of the shell migration
- moving Analytics, Data Sharing, Docs Viewer, or UI Catalogue routes back under Studio
- removing server-side static-file policy, write allowlists, or backup behavior

## Target Architecture

The target Local Studio stack should look like this:

```text
Browser JavaScript
  - app shell
  - route registry
  - header/navigation
  - doc links
  - route mount points
  - route modules
  - client-side state and validation

User-facing config
  - route ids, labels, paths, scripts, and doc ids
  - external link bases
  - UI text
  - feature settings

Python local app server
  - loopback HTTP process
  - static asset serving
  - runtime config endpoint
  - local read/write APIs
  - filesystem mutation, backups, validation, activity records
  - allowlisted command and report adapters
```

Python may still serve a minimal HTML bootstrap page for Studio routes, but it should not need route-specific shell templates for ordinary pages. The bootstrap can be mostly static:

```html
<main id="studioApp"></main>
<script type="module" src="/studio/app/frontend/js/studio-app.js"></script>
```

JavaScript would then read runtime config, resolve the active route, render the common shell, mount the route-specific content root, and load or invoke the route module.

## Python Boundary

Python remains necessary and useful for write services.

Python should continue to own:

- catalogue writes, imports, publication updates, delete/apply flows, and backups
- audit and report execution through allowlisted adapters
- local file opening where browser security cannot do it directly
- static path allowlists and local-service security boundaries
- activity log writes
- structured validation that protects source data

Analytics tag writes and Data Sharing workflows are now owned by the standalone Local Analytics app.
Docs Viewer management remains owned by the standalone Docs Viewer service.
The Studio app shell should link to those peers through config when needed, not host or proxy their routes.

The browser should never gain a generic "write this path" or "run this command" API. A JavaScript app shell changes UI ownership; it does not weaken the write boundary.

## Config Boundary

Config should become the normal user-facing source for app shell metadata.

Candidate shape:

```json
{
  "app": {
    "routes": {
      "project_state": {
        "label": "project state",
        "title": "Project State",
        "path": "/studio/project-state/?mode=manage",
        "script": "/studio/app/frontend/js/project-state.js",
        "doc_id": "project-state-page",
        "nav": true
      }
    }
  },
  "external_links": {
    "docs_viewer": {
      "base_url": "http://127.0.0.1:8776",
      "docs_path": "/docs/",
      "default_mode": "manage",
      "doc_scope": "studio"
    }
  }
}
```

The exact schema can differ, but the principle should hold:

- route IDs and labels are config data
- doc IDs are config data
- external bases are config data
- Python should not hardcode page documentation targets
- Python should not need to know which doc explains which Studio page

## Benefits

- clearer ownership: UI shell in JS, writes in Python
- fewer cross-language changes for route-label, doc-link, and shell changes
- less Python HTML string rendering
- simpler Docs Viewer boundary because Docs links are just config plus JS URL construction
- easier route consistency because one JS shell can render common header, doc link, ready-state wrapper, and route mount
- safer backend because Python APIs can focus on validation and mutation instead of UI concerns
- better incremental migration path for future routes and UI framework work
- easier testing of shell behavior in browser smokes rather than comparing Python-rendered templates

## Risks

- a JS shell can become a framework by accident if route ownership is not kept small
- route boot order can become fragile if scripts assume server-rendered DOM that no longer exists
- migration can temporarily increase duplication if Python and JS shells coexist too long
- browser smokes become more important because first paint depends more heavily on JS
- config schema changes need validation so route metadata failures fail clearly

Mitigations:

- migrate one route family at a time
- keep the first JS shell renderer small and vanilla
- maintain existing route URLs and route-ready attributes during each migration
- add focused smoke coverage for shell boot, doc-link resolution, and route ready state
- keep Python APIs unchanged while shell ownership moves

## Proposed Approach

Do this incrementally rather than as a rewrite.

### Slice 1: Route registry and shell contract

Define the config-owned Studio route registry shape and the browser-side shell contract.
This slice should decide names, metadata fields, validation expectations, and testing surfaces before route markup moves.
It should not migrate a route yet.

Use [Studio JavaScript App Shell Slice 1 Tasks](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell-slice-1) as the task tracker.

### Slice 2: Minimal JS shell and one low-risk route

Add the smallest useful `studio-app.js` shell renderer and migrate one low-risk Studio route.
Good candidates are compact operational routes such as Project State, Activity, or Audits.
The route URL, backend API calls, and `data-studio-ready` contract must remain unchanged.

### Slice 3: Operational routes batch

Move compact non-catalogue route shells once the first route proves the pattern.
Likely batch:

- Audits
- Activity
- Project State
- Bulk Add Work

### Slice 4: Catalogue support routes

Move established catalogue support routes whose behavior is less form-heavy than the editor family.
Likely batch:

- Catalogue Status
- Catalogue Field Registry
- Studio Works

### Slice 5: Catalogue editor family

Move Work, Work Detail, Series, and Moment editor shells.
This is the highest-risk batch because these routes have more state, modals, selection flows, and write workflows.
Split this slice if the editor family proves too broad for one verified batch.

### Framework evaluation checkpoint

Consider a frontend framework only after slices 2 or 3 prove the JavaScript shell boundary.
The decision should be evidence-led:

- keep vanilla JavaScript if the shell remains small and route modules mount cleanly
- evaluate a framework if the migration starts recreating framework-like responsibilities such as component lifecycle, routed layout state, nested view composition, render diffing, modal orchestration, or repeated form-state machinery
- use the catalogue editor family as the main complexity signal before committing to a framework

Any candidate framework must:

- work with local static/module serving or justify its build step clearly
- preserve Python as the write/API authority
- coexist incrementally with existing route modules
- keep route-ready smoke testing straightforward
- avoid making simple operational Studio pages materially heavier

### Slice 6: Retire Python shell rendering

Remove route-specific Python shell helpers and view tables that are no longer needed.
Tighten static/runtime config tests, update source ownership and runtime docs, and refresh JavaScript inventory rows.

### Optional follow-up slices

- Navigation/app polish if the migration exposes inconsistent grouping, page titles, or shell variants.
- Framework adoption, only if the checkpoint shows vanilla JS is becoming a local framework by accident.
- Analytics shell backport only after the Studio shell pattern is stable and clearly worth sharing.

Ruby/Jekyll dependency retirement should stay separate.
It affects public site generation, Docs Viewer Markdown rendering, docs rebuild/watch flows, import validation, and publish parity, so it needs its own inventory and target-contract request before implementation.

## First Slice

The first implementation slice is a contract slice, not a route migration.
It should add the route registry shape, decide how the JS app shell will mount route modules, and prove the metadata can be validated and consumed without changing current route behavior.

The first slice is successful when the repo has a tested route-registry and shell-contract foundation for migrating one low-risk route in slice 2.

## Open Questions

- Should route metadata live under `app.routes`, `app.runtime.views`, or a new top-level `routes` key?
- Should route modules export a standard `mount(root, config, context)` function, or should the shell continue loading scripts by side effect for the first phase?
- Should there be separate shell types for normal Studio pages, full-page editor pages, and operational report pages?
- How much route markup should be config-driven versus created by route modules?
- What is the smallest route that proves the pattern without forcing a framework decision?

## Verification

Focused checks for the first implementation should include:

```bash
$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py
node --check <new-or-changed-studio-shell-module>.js
```

Contract expectations:

- route registry validates required metadata
- route doc links are resolvable from `external_links.docs_viewer`
- route script paths and served route paths stay internally consistent
- runtime config does not introduce Python-built page doc links
- Python write/API endpoints are unchanged

Browser smoke expectations for slice 2 and later:

- migrated route shell renders from JS
- route-specific module reaches ready state
- Docs Viewer doc link resolves from `external_links.docs_viewer`
- runtime config does not publish Python-built page doc links
- Python write/API endpoints behave unchanged
