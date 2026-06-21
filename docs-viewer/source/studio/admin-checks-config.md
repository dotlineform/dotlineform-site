---
doc_id: admin-checks-config
title: Checks Config
added_date: 2026-06-08
last_updated: 2026-06-10
ui_status: ""
parent_id: admin-checks
---
# Admin Checks Config

```text
admin-app/checks/config/admin-checks.json
admin-app/checks/config/admin-checks-reports.json
```
Target-map config top-level keys: `jq 'keys' admin-app/checks/config/admin-checks.json`

```json
[
  "areas",
  "config_id",
  "families",
  "routes",
  "scopes",
  "source",
  "version"
]
```

Report registry keys: `jq 'keys' admin-app/checks/config/admin-checks-reports.json`

The config files define:

- `scopes` - the apps: scope ids, labels, included path prefixes, and exclusions
- `families` - the technical layers: file family ids and path/pattern rules
- `areas` - the functional/workflow areas and path/pattern rules
- `routes` - UI/API route targets: route ids, URLs, API path links, and path/pattern rules
- `admin-checks-reports.json` - report ids, scripts, labels, CSV artifact metadata, defaults, and allowed options

Families tell us technical layer; routes tell us surface boundary; areas tell us workflow ownership.

The family map should be close to stable and mostly path-based. Areas and routes are less deterministic because they describe product/workflow ownership, which can cut across services, runtime JS, config, docs, and tests.

The current filter model is:

```
scope first
-> then optional families
-> then optional areas
-> then optional routes
```

Those optional layers are intersected. So a run like: 

`scope=docs-viewer + family=runtime-js + area=search + route=/library/`

means “files inside Docs Viewer scope that satisfy all selected target layers, including explicit shared dependencies where configured.”

`route` is the user-facing surface:

```text
/admin/checks/
/docs/
/library/
/analysis/
```

A route answers: “where does this capability appear?”

`area` is the workflow or capability inside or across those surfaces:

```text
search
management
import-export
config
activity
catalogue
docs-build
```

An area answers: “what is the user/system trying to do?”

So a route can contain several areas. `/docs/` can involve:

```text
management
import-export
docs-build
config
activity
```

And an area can span several routes. `search` can involve:

```text
/library/
/analysis/
catalogue/search/
docs-viewer runtime/search files
build search scripts
```

## scopes

`jq -r '.scopes | keys[]' admin-app/checks/config/admin-checks.json`

```
admin
all
analytics
docs-viewer
public-site
studio
```

```
{
  "scopes": {
    "admin": {
      "label": "Admin",
      "include": [
        "admin-app/"
      ],
      "exclude": [
        "admin-app/**/__pycache__/**"
      ]
    },
    "analytics": {
      "label": "Analytics",
      "include": [
        "analytics-app/"
      ],
      "exclude": [
        "analytics-app/**/__pycache__/**",
        "analytics-app/data/canonical/"
      ]
    etc...
```

## families

`families` are complete in terms of definitions and file coverage.

```
"families": {
    "runtime-js": {
      "label": "Runtime JavaScript",
      "include": [
        "admin-app/app/frontend/js/",
        "analytics-app/app/frontend/js/",
        "assets/js/",
        "docs-viewer/runtime/js/",
        "studio/app/frontend/js/"
      ]
    },
    etc...
```

list the families:
```
jq -r '.families | keys[]' admin-app/checks/config/admin-checks.json
jq -r '.families | to_entries[] | "\(.key): \(.value.label)"' admin-app/checks/config/admin-checks.json
```

```
runtime-js: Runtime JavaScript
runtime-assets: Runtime assets
services: Services
build: Build scripts
config: Configuration
tests: Tests and smokes
admin-route: Admin routes
public-route: Public routes
```

Families are the most deterministic layer because they mostly follow technical structure:

```text
runtime-js       -> frontend JS runtime paths
runtime-assets   -> CSS/static app assets and shell/static assets
services         -> backend/service modules
build            -> build/check/command scripts
config           -> config files and config directories
tests            -> tests and smokes
admin-route      -> Admin route surface files
public-route     -> public route surface files
```

The main wrinkle is that some files legitimately match more than one family. For example, Admin frontend config can be both `config` and `admin-route`; public Docs Viewer route config can be both `config` and `public-route`. That is fine as evidence, not necessarily a problem.

Markdown source documents are not checks input.
The checks source-file discovery includes code, config, and structured data such as JSON and CSS, but excludes `*.md` files.

## areas

`areas` are used to group files into functional/workflow areas and path/pattern rules.

```
"areas": {
    "search": {
      "label": "Search",
      "include": [
        "**/*search*",
        "assets/js/search/",
        "catalogue/search/",
        "site/docs-viewer/runtime/js/shared/docs-viewer-search*",
        "docs-viewer/build/*search*",
        "docs-viewer/tests/**/*search*",
        "studio/services/catalogue/search/"
      ],
      "shared": ["site/docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js"],
      "routes": ["/library/", "/analysis/"]
    },
    etc...
```

list the areas: `jq -r '.areas | keys[]' admin-app/checks/config/admin-checks.json`

```
activity
catalogue
config
docs-build
import-export
management
search
```

- Areas are workflow/product concepts, not folder concepts.
- Areas should be a normalized cross-app vocabulary for workflows.
- They will always need more judgment than families.
- The current list is a seed, not complete.

The process for defining areas is:

1. Look at each app and list its real workflows.
   Examples: search, import/export, management, catalogue editing, activity logging, config/settings, docs build.

2. Consolidate those into repo-level area ids where the concept is meaningfully shared.
   For example, `import-export` can cover Docs Viewer imports, data-sharing exports, and Analytics review/import flows.

3. Avoid app-specific area ids unless the workflow is genuinely unique and important enough.
   Prefer `management` over `docs-viewer-management`, `config` over `studio-config`, `activity` over `admin-activity`.

4. Let one file match multiple areas when that reflects reality.
   A data-sharing config file can be both `config` and `import-export`. That is useful evidence.

5. Keep areas smaller than “whole app”, but broader than one implementation file.
   If an area only maps to one script, it may be a route or report detail instead of an area.

## routes

current config status:
```
mapped:         5
inventory-only: 40
total routes:   45
```

```
"routes": {
    "/admin/checks/": {
      "label": "Admin Checks",
      "path": "/admin/checks/",
      "include": [
        "admin-app/checks/audit_target_map.py",
        "admin-app/checks/config/",
        "admin-app/checks/reports/",
        "admin-app/checks/run_reports.py",
        "admin-app/app/frontend/js/admin-checks.js",
        "admin-app/app/frontend/config/ui-text/admin-checks.json",
        "admin-app/app/server/admin_app/admin_checks_api.py"
      ],
      "shared": ["admin-app/app/server/admin_app/admin_app_server.py"],
      "areas": ["config"]
    },
  etc...
```
Mapped routes include:

```
/admin/checks/
/analysis/
/docs/
/library/
```
The **route ids/paths themselves** should be deterministic and discoverable from source:

```text
Docs Viewer route config
Admin server route handlers
Analytics server route handlers
frontend route config
```

So we should not hand-invent route existence, we should derive or validate the route list from those route registries/server definitions.

But the **route target map** is more than the URL. It includes related files:

```text
route shell/template
frontend JS
server/API handlers
config
UI text
tests/smokes
docs
shared dependencies
```

That part often needs explicit mapping rules and review. For example, `/admin/checks/` can be discovered as a route, but the system still needs to know that these belong to it:

```text
admin-app/checks/run_reports.py
admin-app/checks/config/admin-checks.json
admin-app/app/server/admin_app/admin_checks_api.py
admin-app/app/frontend/js/admin-checks.js
admin-app/tests/...
```

So:

- **route inventory** should be deterministic/discovered
- **route ownership map** is pattern-based and reviewed
- **shared dependencies** must be explicit

Docs Viewer is different: `/docs/` is the route, while `?scope=studio&doc=...` is route state/query, not separate route ids. So keeping `/docs/` as the single route target is right.

The target-map audit is the current guardrail for comparing discovered and configured route ownership. It should report:

```text
route exists but is not mapped
mapped route no longer exists
route has handler/config files that are not included
route pattern is stale or too broad
```
