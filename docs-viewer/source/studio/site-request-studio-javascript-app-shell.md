---
doc_id: site-request-studio-javascript-app-shell
title: Studio JavaScript App Shell Request
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: paused
parent_id: change-requests
sort_order: 12000
viewable: true
---
# Studio JavaScript App Shell Request

Status:

- proposed, paused because doing docs viewer first, then revisit this.

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
- Data Sharing package preparation, returned-package review, apply flows, and adapter execution
- analytics tag writes and source JSON mutation
- audit and report execution through allowlisted adapters
- local file opening where browser security cannot do it directly
- static path allowlists and local-service security boundaries
- activity log writes
- structured validation that protects source data

The browser should never gain a generic "write this path" or "run this command" API. A JavaScript app shell changes UI ownership; it does not weaken the write boundary.

## Config Boundary

Config should become the normal user-facing source for app shell metadata.

Candidate shape:

```json
{
  "app": {
    "routes": {
      "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/studio/analytics/tag-groups/",
        "script": "/studio/app/frontend/js/tag-groups.js",
        "doc_id": "tag-groups",
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

1. Finish removing Python-owned link shaping.
   Runtime views should not publish `doc_href`; page doc targets should remain in config and resolve in JS.

2. Move route metadata out of Python view tables.
   Introduce a config-owned route registry for labels, titles, paths, doc IDs, scripts, navigation visibility, and shell type.

3. Add a minimal JS app shell renderer.
   It should render the shared Studio header, doc link, route heading, common content wrapper, and route mount point from config.

4. Migrate one low-risk route to the JS shell.
   A good first candidate is a read-heavy or compact admin page with a stable route-ready contract. The goal is to prove the shell pattern, not to redesign the page.

5. Migrate route families in batches.
   Candidate batches:
   - Analytics tag pages
   - admin pages such as Audits, Activity, Project State, Thumbnail Quality
   - Data Sharing prepare/review
   - Catalogue editor pages
   - UI Catalogue demo pages

6. Retire Python route shell helpers after the last migrated route no longer needs them.

## First Slice

The first implementation should be deliberately narrow.

Suggested first slice:

- add a config route registry for a small set of routes
- add a JS shell renderer that can render one route from that registry
- keep the existing Python app server and APIs unchanged
- migrate one simple route to use the JS shell
- prove that the route still exposes the same ready-state attributes
- prove that the page doc link is built entirely from `external_links.docs_viewer`

The first slice is successful when a route shell can be removed from Python without changing that route's URL or backend API.

## Open Questions

- Should route metadata live under `app.routes`, `app.runtime.views`, or a new top-level `routes` key?
- Should route modules export a standard `mount(root, config, context)` function, or should the shell continue loading scripts by side effect for the first phase?
- Should there be separate shell types for normal Studio pages, full-page editor pages, and UI Catalogue demos?
- How much route markup should be config-driven versus created by route modules?
- What is the smallest route that proves the pattern without forcing a framework decision?

## Verification

Focused checks for the first implementation should include:

```bash
$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py
node --check studio/app/frontend/js/studio-app.js
$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_navigation_adapter.py
```

Browser smoke expectations:

- route shell renders from JS
- route-specific module still reaches ready state
- Docs Viewer doc link resolves from `external_links.docs_viewer`
- runtime config does not publish Python-built page doc links
- Python write/API endpoints behave unchanged
