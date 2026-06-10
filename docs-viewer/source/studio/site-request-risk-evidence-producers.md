---
doc_id: site-request-risk-evidence-producers
title: Risk Evidence Producers Request
added_date: 2026-05-31
last_updated: 2026-06-10
ui_status: in-progress
parent_id: change-requests
---
# Risk Evidence Producers Request

Status:

- spec locked for implementation
- implementation tasks are listed in this document
- no v1 open questions remain

## Summary

Replace the current risk evidence pack with an Admin-owned checks system that runs allowlisted evidence reports, stores structured artifacts, and exposes read-only report results in Admin.

The new system is report-oriented:

- a report is the user-facing output
- metrics are the measured fields used to produce a report
- producers are report scripts that collect metrics and render one report
- a run is one orchestrated execution of one or more reports against one scope

The first production report is `files` for line count and file size evidence.
The `target-map` report is intentionally deferred to [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map) so v1 can prove the checks system with the simplest useful report first.
A later dependency model for compound reports is captured as an option in [Risk Evidence Producers Report Dependencies](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-dependencies).
Possible future dependency reports are captured as options in [Git History Report](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-git-history), [Imports Report](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-imports), and [Tests Report](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-tests).

## Current Implementation

- risk policy described in [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).
- initial implementation of [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack).
- metrics and reports are listed in [Risk Evidence Pack Metrics](/docs/?scope=studio&doc=risk-evidence-pack-metrics). However the current list is a mix of reported fields, derived fields and metadata.
- the risk evidence pack is run on `/admin/risk/`, however this is mainly surfacing summary information and doesn't clearly differentiate between metrics and reports.
- current scripts were written to support inventories of the apps, to measure the risk associated with each script family. these inventories have been retired pending review of the risk policy and implementation.

## New Implementation

Before considering whether any new 'risk inventories' need to be defined, we need to create a structured way of collecting and reporting evidence.

key features of the new implementation:

- risk evidence is surfaced in reports which are defined as a combination of metrics
- scripts for producing reports are all saved in a single location, `admin-app/checks/reports`
- each script is responsible for producing artifacts for one report only.
- there is a single orchestrator script which calls the report scripts. the reports to run should be passed to the orchestrator as JSON, enabling one or many reports to be run sequentially.
- report artifacts for a run are saved in `var/admin/checks/<date-time>-<scope>/<report>`
- the UI lists the reports available, the scope/script family to run them against (e.g. studio, docs viewer) and any other report-specific options.
- the UI displays a read-only view of the run summary and (by selecting a report in the run) the report results (all markdown files).

the implementation will in principle be able to report on the entire repo:

- the apps Studio, Analytics, Docs Viewer, Admin
- all documents
- git history
- logs
- all test files and artifacts
- the public site

some reports by their nature may necessarily have smaller scope. scopes will be defined by folder and file level inclusion in `admin-app/checks/config/admin-checks.json`.

## Locked Specification

### Ownership

- Admin owns the checks system, including the CLI runner, report scripts, local API, UI route, and ignored local artifacts.
- The new route is `/admin/checks/`.
- The new API namespace is `/admin/api/checks/`.
- Existing `/admin/risk/` code is reusable prior art only. It should not define the final artifact paths, API names, route names, or report contract for the new system.
- Existing `/admin/risk/` remains available until the new checks system has replicated or intentionally discarded its useful capabilities.

### Source Layout

```text
admin-app/checks/
  config/
    admin-checks.json
  run_reports.py
  reports/
    files.py
```

`admin-app/checks/reports/` is the only location for report producer scripts.
The orchestrator is the only supported entry point for multi-report runs.

### Run Contract

The orchestrator command should accept a JSON run request from either a file path or standard input.
The JSON request is the complete run plan and should include:

```json
{
  "scope": "docs-viewer",
  "families": ["runtime-js", "services"],
  "areas": ["search"],
  "routes": [],
  "reports": ["files"],
  "options": {
    "files": {
      "limit": 50,
      "sort": "lines_desc"
    }
  },
  "write": true
}
```

Rules:

- scope and report ids must be allowlisted from `admin-app/checks/config/admin-checks.json`
- family, area, and route ids must be allowlisted under the selected scope when provided
- report options must be validated against the selected report's allowed option schema
- browser-provided command strings, shell flags, environment values, arbitrary paths, and output roots are prohibited
- report scripts are invoked by path and argv list, not by shell command text
- dry runs must print the resolved plan and output paths without writing artifacts
- write runs must create a new run directory under `var/admin/checks/`
- a failed report should not hide completed report artifacts from the same run; the run summary records per-report status

### Targeting Model

The checks system uses layered targeting:

```text
scope
  -> file family
  -> functional area
  -> route
```

`scope` is the top-level safety boundary for a run.
It answers which app or repo area can be inspected.
All lower-level targets must resolve inside the selected scope after exclusions are applied.

`file family` is a technical or layer boundary inside a scope.
It separates files by implementation role, such as frontend runtime, backend services, build scripts, tests, source docs, generated payload definitions, or route shells.
Families should be deterministic and mostly non-overlapping so reports can produce useful totals.
Files that match the selected scope but no configured family should be reported as `_unclassified`.

`functional area` is a product, workflow, or feature boundary inside a scope.
It can cross technical layers.
Examples include search, management, import/export, bookmarks, config, activity, testing, catalogue save/build, docs build/import/export, or media derivation.
Functional areas can be many-to-many because one file may support more than one feature.

`route` is a UI or API route boundary inside a scope.
It can include frontend route files, server route handlers, API adapters, route config, UI text, tests, smoke checks, and docs.
Route targets are useful when the risk question is about a specific user-facing surface such as `/admin/checks/`, `/admin/risk/`, `/library/`, or a Docs Viewer management route.

Run target filters are intersected:

- selecting only `scope` includes all files in that scope after exclusions
- selecting `families` narrows the scope to those technical families
- selecting `areas` narrows the scope to those functional areas
- selecting `routes` narrows the scope to those route targets
- selecting multiple target layers includes files that satisfy all selected layers, plus explicitly configured shared dependencies for the selected area or route

Reports should record both direct target matches and shared dependency matches so a route or area report can distinguish owned files from shared files.

### Target Map Audit And Maintenance

The initial target map should be produced from a one-off audit of real repo files, then maintained by a repeatable guardrail.
The config should not become a hand-maintained per-file inventory.
Prefer path and filename patterns for stable ownership boundaries, with explicit shared dependencies or overrides only where pattern rules are not clear enough.

Add a target-map audit script:

```text
admin-app/checks/audit_target_map.py
```

The audit resolves `admin-app/checks/config/admin-checks.json` and writes or prints:

```text
var/admin/checks/target-map-audit/
  target-map.json
  target-map.md
```

The audit should report:

- files included by each scope after exclusions
- each file's resolved file family, or `_unclassified`
- files matching multiple families
- functional areas matched by each file
- route targets matched by each file
- shared dependencies included by each area or route
- configured patterns that match no files
- files that look route-related or area-related but are not mapped
- generated, cache, dependency, build, and local run paths excluded by scope rules

Report interpretation:

- target-map findings are mapping data, not automatic pass/fail results
- `_unclassified` files should remain visible as report data and can be highlighted by later risk reports when they matter
- multi-family, cross-area, cross-route, stale-pattern, and likely-unmapped findings should be available for review without forcing the audit itself to decide product risk
- shared dependencies must be explicit so area and route reports do not silently pull in broad app surfaces
- subsequent risk reports can choose which target-map findings to treat as actionable evidence for a specific policy question

The target-map audit should be part of the maintenance path for adding new routes, new feature areas, new app layers, or significant file moves.
Reviewing the target map is also a risk check in its own right.
It can identify scripts, config, route files, and shared helpers that cross too many boundaries or have unclear ownership.
The v1 audit does not expose this as a normal report.
The later `target-map` report is specified in [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map).

### Checks Config

`admin-app/checks/config/admin-checks.json` defines:

- `config_id: "admin-checks"` and a numeric `version`
- source ownership metadata for the Admin checks config contract

- scope ids, labels, and included path prefixes
- scope exclusions for generated artifacts, caches, dependencies, local outputs, and ignored runtime folders
- file family ids, labels, included path prefixes/patterns, and exclusions
- functional area ids, labels, included path prefixes/patterns, tags, shared dependencies, and optional route links
- route ids, labels, URL/path metadata, included path prefixes/patterns, API path links, smoke-test links, and shared dependencies
- report ids, labels, script paths, description text, default options, and allowed options
- report-specific scope restrictions when a report cannot run against every scope

Initial scope ids:

- `admin`
- `analytics`
- `docs-viewer`
- `public-site`
- `studio`
- `all`

Initial v1 target ids should stay small enough to verify against the real tree:

- families: `runtime-js`, `runtime-assets`, `services`, `build`, `source-docs`, `config`, `tests`, `admin-route`, `public-route`
- areas: `search`, `management`, `import-export`, `config`, `activity`, `catalogue`, `docs-build`
- routes: `/admin/checks/`, `/admin/risk/`, `/library/`, `/analysis/`, plus a representative Docs Viewer management route selected after the v1 target-map audit proposes the route map

Example target config shape:

```json
{
  "scopes": {
    "docs-viewer": {
      "label": "Docs Viewer",
      "include": ["docs-viewer/"],
      "exclude": ["docs-viewer/**/__pycache__/**"],
      "families": {
        "runtime-js": {
          "label": "Runtime JavaScript",
          "include": ["docs-viewer/runtime/js/"]
        },
        "services": {
          "label": "Services",
          "include": ["docs-viewer/services/"]
        },
        "build": {
          "label": "Build scripts",
          "include": ["docs-viewer/build/"]
        },
        "tests": {
          "label": "Tests and smokes",
          "include": ["docs-viewer/tests/"]
        }
      },
      "areas": {
        "search": {
          "label": "Search",
          "include": [
            "docs-viewer/runtime/js/*search*",
            "docs-viewer/services/*search*",
            "docs-viewer/build/*search*",
            "docs-viewer/tests/**/*search*"
          ],
          "shared": ["docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js"],
          "routes": ["library", "analysis"]
        }
      },
      "routes": {
        "library": {
          "label": "Library",
          "path": "/library/",
          "include": [
            "library.html",
            "docs-viewer/runtime/js/docs-viewer*.js",
            "docs-viewer/config/scopes/library*.json"
          ],
          "areas": ["search"]
        }
      }
    }
  }
}
```

### Artifact Contract

Each write run creates:

```text
var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/
  commands.json
  manifest.json
  run-summary.json
  run-summary.md
  <report>/
    report.json
    report.md
```

Run-level artifacts:

- `manifest.json`: run id, scope, selected families, selected areas, selected routes, requested reports, selected options, repo commit, created timestamp, command contract version, status, direct target matches, shared dependency matches, and unclassified match counts
- `commands.json`: orchestrator and report command argv lists, working directories, start/end timestamps, exit codes, duration, stdout/stderr artifact references, and safe excerpts
- `run-summary.json`: machine-readable per-report status, artifact paths, warnings, errors, totals, and omitted reports
- `run-summary.md`: compact human-readable summary for Admin display and future linking from risk analysis documents

Report-level artifacts:

- `report.json`: raw report metrics, selected scope, selected families, selected areas, selected routes, applied options, included roots, excluded roots, totals, warnings, and report status
- `report.md`: structured human-readable report

### Markdown Display Contract

Keep markdown display simple, matching the current `/admin/risk/` pattern.
The API reads the markdown artifact and returns it as a raw string field, such as `summary_markdown` or `report_markdown`.
The browser escapes that string and displays it in a preformatted block.
Do not add server-side markdown-to-HTML rendering or a browser markdown renderer in v1.

### Admin UI Contract

The `/admin/checks/` UI should:

- list available reports, scopes, file families, functional areas, and routes from the checks API
- allow one scope, optional families, optional areas, optional routes, and one or more reports to be selected
- render report-specific options from allowlisted metadata
- support dry run and write run actions
- list recent runs from `var/admin/checks/`
- display `run-summary.md`
- display a selected report's `report.md`
- display markdown as escaped preformatted text, not rendered HTML
- delete a selected local run snapshot after confirmation
- show per-report status, warnings, and failed-report messages without exposing arbitrary local files

The UI can create a new validated run and delete a selected local run snapshot.
Snapshot deletion must follow the existing safe run-id validation pattern from Admin risk runs and only delete ignored local artifacts under `var/admin/checks/`.

### First Report

`files` measures file count, total line count, total byte size, and per-file line/size rows for a selected scope.

Default `files` behavior:

- include source/config/documentation files selected by scope config
- exclude generated payloads, dependency folders, caches, local run outputs, and build outputs
- sort by line count descending
- render a markdown table and terminal-style summary
- write `files/report.json` and `files/report.md`

Required metrics:

| Metric | Description |
| --- | --- |
| `totals.files` | Included file count. |
| `totals.lines` | Total line count across included files. |
| `totals.bytes` | Total byte size across included files. |
| `files[].path` | Repo-relative path. |
| `files[].lines` | Line count for the file. |
| `files[].bytes` | Byte size for the file. |
| `files[].family` | File family from scope config, or `_unclassified`. |
| `files[].areas` | Functional area ids matched by the file. |
| `files[].routes` | Route ids matched by the file. |
| `files[].target_match` | Whether the row matched directly, as a shared dependency, or as `_unclassified`. |

## Approach

- keep the current implementation and route because it contains reusable ideas and code
- start a new implementation for data collection and reporting
- develop a new UI at `/admin/checks/`
- when the new system is working and has effectively replicated or discarded the current risk evidence capabilities, the current implementation and route will be retired. scripts and artifacts that no longer serve an active role will be deleted. legacy reporting data and folder paths will be deleted.

## Durable Documentation

[Admin Checks](/docs/?scope=studio&doc=admin-checks) is the durable technical home for the new checks system.
It owns the config, runner, route/API, artifact locations, target-map audit, markdown display, snapshot deletion, and report documentation structure.

Each implemented report should have a child doc under [Admin Checks](/docs/?scope=studio&doc=admin-checks).
The v1 report doc is [Admin Checks Files Report](/docs/?scope=studio&doc=admin-checks-report-files).

Do not update [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack) as the durable home for this work.
That document remains tied to the current `/admin/risk/` implementation until `/admin/risk/` is deliberately retired.
After v1, this request should become a tracker for subsequent report child requests rather than the owner of technical checks contracts.

## Artifacts

- Each run saves summary files in `var/admin/checks/<date-time>-<scope>/`
    - `commands.json`
    - `manifest.json`
    - `run-summary.json`
    - `run-summary.md`
- each report in a run saves files in `var/admin/checks/<date-time>-<scope>/<report>/`
    - `report.json` - raw data
    - `report.md` - structured report

The artifact contract in [Locked Specification](#locked-specification) is the implementation contract. This section is retained as the original artifact sketch.

## First Report Sketch

The first report sketch was for file metrics: line count and file size.
The locked v1 implementation keeps this as the only report producer.

```
    Report:     files
    Scope:      docs-viewer

    files:      x
    total lc:   x
    total size: x

     lc        size  file
     ------------------------------------------------------------------------- 
     997       36K  ./docs-viewer/runtime/js/docs-viewer-management.js
     905       32K  ./docs-viewer/runtime/js/docs-viewer-app-runtime.js
     562       28K  ./docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js
     536       20K  ./docs-viewer/runtime/js/docs-html-import.js
     510       20K  ./docs-viewer/runtime/js/docs-viewer-management-actions.js
     451       20K  ./docs-viewer/runtime/js/docs-viewer-management-modals.js
     443       16K  ./docs-viewer/runtime/js/docs-viewer-route-workflow.js
     417       16K  ./docs-viewer/runtime/js/docs-viewer-search-controller.js
     390       16K  ./docs-viewer/runtime/js/docs-viewer-config-controller.js
```

## Acceptance Criteria

- `/admin/checks/` can list configured scopes and reports.
- `/admin/checks/` can list configured file families, functional areas, and routes for the selected scope.
- The checks API exposes health, configured reports/scopes/target layers, recent runs, run summaries, and report markdown for safe run/report ids.
- `admin-app/checks/audit_target_map.py` resolves configured scopes, families, areas, routes, shared dependencies, `_unclassified` files, stale patterns, and exclusions from real repo files.
- The v1 target map is produced from an audit result rather than from an unverified hand-written list.
- A dry run resolves a JSON request into a validated execution plan without writing artifacts.
- A write run for `{"scope": "docs-viewer", "reports": ["files"]}` writes the locked artifact tree under `var/admin/checks/`.
- A filtered write run can target a selected file family, functional area, or route while remaining inside the selected scope.
- A validated delete action can remove one local checks run snapshot under `var/admin/checks/` and cannot delete outside that root.
- The `files` report emits both machine-readable metrics and a human-readable markdown report.
- Report script paths, scope ids, report ids, options, and artifact reads are all allowlisted or validated.
- The browser cannot pass shell command text, arbitrary paths, environment values, or unvalidated report options.
- The existing `/admin/risk/` route is still available until the closeout task retires it deliberately.
- Source docs are updated, but Docs Viewer generated payloads are not rebuilt unless that follow-through is explicitly requested.

## Implementation Tasks

| ID | status | title |
| --- | --- | --- |
| 1 | done | [Produce v1 target map audit](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-1-target-map-audit) |
| 2 | done | [Define checks config, target layers, and report registry](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-2-checks-config) |
| 3 | planned | [Build report orchestrator](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-3-orchestrator) |
| 4 | planned | [Implement `files` report producer](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-4-report-producers) |
| 5 | planned | [Add Admin checks API](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-5-admin-checks-api) |
| 6 | planned | [Add `/admin/checks/` UI](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-6-admin-checks-ui) |
| 7 | done | [Add focused tests and verification commands](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-7-tests) |
| 8 | planned | [Review legacy `/admin/risk/` capabilities and frame child requests](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-8-legacy-risk-review) |
| 9-12 | planned | [Docs, cleanup, verification, and closeout](/docs/?scope=studio&doc=site-request-risk-evidence-producers-task-9-12-closeout) |

## Open Questions

None.
V1 implementation decisions are resolved in this request.
