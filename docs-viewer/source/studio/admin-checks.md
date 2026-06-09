---
doc_id: admin-checks
title: Checks
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: ""
parent_id: admin
---
# Admin Checks

Admin Checks is the durable home for the `/admin/checks/` report system.

The system is separate from the current [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack), which remains tied to the existing `/admin/risk/` implementation until that route is deliberately retired.

## Purpose

Admin Checks runs allowlisted reports against configured repo scopes and stores local report artifacts for review in Admin.

The first v1 report is [Admin Checks Files Report](/docs/?scope=studio&doc=admin-checks-report-files).
Subsequent reports should get their own child docs once implemented.

## Ownership

- Admin owns the checks route, API, orchestrator, report scripts, config, and ignored local artifacts.
- The local route is `/admin/checks/`.
- The API namespace is `/admin/api/checks/`.
- The report orchestrator is `admin-app/checks/run_reports.py`.
- Report scripts live under `admin-app/checks/reports/`.
- Checks config lives at `admin-app/checks/config/admin-checks.json`.

## Config

```text
admin-app/checks/config/admin-checks.json
```

Top-level keys:

```json
{
  "config_id": "admin-checks",
  "version": 1,
  "scopes": {},
  "families": {},
  "areas": {},
  "routes": {},
  "reports": {}
}
```

The config defines:

- `scopes` - the apps: scope ids, labels, included path prefixes, and exclusions
- `families` - the technical layers: file family ids and path/pattern rules
- `areas` - the functional/workflow areas and path/pattern rules
- `routes` - UI/API route targets: route ids, URLs, API path links, and path/pattern rules
- `reports` - report ids, scripts, labels, defaults, and allowed options

Routes may be `mapped` or `inventory-only`.
Mapped routes are reviewed route targets and can be selected by normal checks runs.
Inventory-only routes are deterministic route inventory entries that are visible to the audit but are not ready for route-scoped evidence runs.

The browser may receive safe projected metadata from this config.
The browser must not receive arbitrary local paths, command strings, environment values, or unvalidated report options.

## Targeting Model

Checks use layered targeting:

```text
scope
  -> file family
  -> functional area
  -> route
```

`scope` is the safety boundary.
Families, areas, and routes are optional filters within the selected scope.

Target filters are intersected for a run:

- selecting only a scope includes the scoped files after exclusions
- selecting families narrows to technical/layer targets
- selecting areas narrows to functional/workflow targets
- selecting routes narrows to UI/API route targets

Explicitly configured shared dependencies can be included for selected `areas` or `routes`, e.g. specific docs viewer runtime files, data sharing files.

Files that match a scope but no configured family are reported as `_unclassified`.
Those findings are mapping data and can be used by later risk reports when relevant.

## Target Map Audit

The target-map architecture note is [Admin Checks Target Map Architecture](/docs/?scope=studio&doc=admin-checks-target-map-architecture).

The target map is maintained by:

```text
admin-app/checks/audit_target_map.py
```

The audit resolves `admin-checks.json` against real repo files and can write:

```text
var/admin/checks/target-map-audit/
  target-map.json
  target-map.md
```

The audit is used to maintain the config map and review drift.
It is not itself a v1 report producer.
The deferred report request is [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map).

Run the target-map audit when adding new routes, feature areas, app layers, or significant file moves.

## Run Requests

The orchestrator accepts a JSON run request from a file path or standard input.

Example:

```json
{
  "scope": "docs-viewer",
  "families": ["runtime-js", "services"],
  "areas": ["search"],
  "routes": [],
  "reports": ["files"],
  "options": {
    "files": {
      "limit": 20,
      "sort": "lines_desc"
    }
  },
  "write": true
}
```

Rules:

- scope, family, area, route, and report ids are allowlisted by config
- report options are validated against allowed options
- report scripts are invoked by path and argv list
- browser-provided command strings, shell flags, environment values, arbitrary paths, and output roots are prohibited
- dry runs resolve the plan without writing run artifacts
- write runs create ignored local artifacts under `var/admin/checks/`

## Artifacts

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
    report.csv  [optional]
```

Run-level artifacts:

- `manifest.json`: run id, targets, reports, options, repo commit, created timestamp, command contract version, status, and target-match counts
- `commands.json`: orchestrator/report argv lists, working directories, timestamps, exit codes, duration, and safe output references
- `run-summary.json`: machine-readable per-report status, artifact paths, warnings, errors, totals, and omitted reports
- `run-summary.md`: compact human-readable summary for Admin display

Report-level artifacts:

- `report.json`: raw report metrics and selected target metadata
- `report.md`: structured human-readable report
- `report.csv`: optional full row export for reports that list files or similarly tabular records

## Markdown Display

Keep markdown display simple.
The API reads markdown artifacts and returns raw strings such as `summary_markdown` or `report_markdown`.
The browser escapes those strings and displays them as preformatted text.

Do not add server-side markdown-to-HTML rendering or browser markdown rendering unless a later request changes this contract.

## Snapshot Deletion

The Admin Checks UI may delete a selected local run snapshot.
Deletion must:

- validate the run id
- reject paths outside the checks runs root
- delete only ignored local artifacts under `var/admin/checks/`
- never delete source files or arbitrary local paths
