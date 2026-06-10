---
doc_id: admin-checks
title: Checks
added_date: 2026-06-08
last_updated: 2026-06-10
ui_status: ""
parent_id: admin
---
# Admin Checks

Admin Checks is the durable home for the `/admin/checks/` report system.

## Purpose

Admin Checks runs allowlisted reports against configured repo scopes and stores local report artifacts for review in Admin.

Implemented reports include [Admin Checks Files Report](/docs/?scope=studio&doc=admin-checks-report-files) and [Admin Checks Target Map Report](/docs/?scope=studio&doc=admin-checks-report-target-map).
Subsequent reports should get their own child docs once implemented.
Future report request docs live under [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports) until a report is implemented and promoted into this durable Admin Checks section.

## Ownership

- Admin owns the checks route, API, orchestrator, report scripts, config, and ignored local artifacts.
- The local route is `/admin/checks/`.
- The API namespace is `/admin/api/checks/`.
- The report orchestrator is `admin-app/checks/run_reports.py`.
- Report scripts live under `admin-app/checks/reports/`.
- Checks config lives at `admin-app/checks/config/admin-checks.json`.
- Local report artifacts live under `var/admin/checks/`.

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
- `reports` - report ids, scripts, labels, CSV artifact metadata, defaults, and allowed options

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

The run-scoped target-map report is [Target Map Report](/docs/?scope=studio&doc=admin-checks-report-target-map).

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
  "reports": ["files", "target-map"],
  "options": {
    "files": {
      "limit": 20,
      "sort": "lines_desc"
    },
    "target-map": {
      "limit": 20,
      "pattern_limit": 20
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

## API

The local Admin checks API is registered under:

```text
/admin/api/checks/
```

Endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/admin/api/checks/health` | Service health, config id, config version, runs root, and configured reports. |
| `GET` | `/admin/api/checks/reports` | Safe metadata for scopes, families, areas, routes, reports, defaults, and allowed options. |
| `GET` | `/admin/api/checks/runs` | Recent run summaries under `var/admin/checks/`. |
| `POST` | `/admin/api/checks/runs` | Create a dry run or write run from a validated JSON run request. |
| `GET` | `/admin/api/checks/runs/<run-id>/summary` | Read `run-summary.json` and raw `run-summary.md`. |
| `GET` | `/admin/api/checks/runs/<run-id>/reports/<report-id>` | Read `report.json`, raw `report.md`, and optional CSV artifact metadata. |
| `DELETE` | `/admin/api/checks/runs/<run-id>` | Delete one local run snapshot under `var/admin/checks/`. |

The API validates run ids and report ids before reading or deleting local artifacts.
It rejects paths that resolve outside the checks runs directory.
It does not expose arbitrary local file reads, shell command strings, environment values, script paths, or output roots.

## Artifacts

Each write run creates:

```text
var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/
  manifest.json
  commands.json
  run-summary.json
  run-summary.md
  <report>/
    report.json
    report.md
    report.csv  [optional]
```

Run-level artifacts:

- `manifest.json`: run id, run directory, config path, selected targets, reports, options, write flag, created and finished timestamps, command contract version, status, manifest path, and target-match counts
- `commands.json`: orchestrator/report argv lists, working directories, timestamps, exit codes, duration, status, stdout/stderr excerpts, and errors when present
- `run-summary.json`: machine-readable per-report status, artifact paths, errors, totals, selected targets, target-match counts, and run status
- `run-summary.md`: compact human-readable summary for Admin display

Report-level artifacts:

- `report.json`: raw report metrics and selected target metadata
- `report.md`: structured human-readable report
- `report.csv`: optional full row export for reports that list files or similarly tabular records

## Verification

The focused Admin Checks profile is:

```text
admin-app/commands/run_checks.py --profile admin-checks
```

It runs the target-map resolver, config validation, orchestrator, `files` report, `target-map` report, and checks API tests.

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
