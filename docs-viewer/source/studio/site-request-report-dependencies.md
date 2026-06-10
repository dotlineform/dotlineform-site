---
doc_id: site-request-report-dependencies
title: Report Dependencies
added_date: 2026-06-09
last_updated: 2026-06-09
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Report Dependencies

This document describes a possible later extension to [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Purpose

Some future reports may need to compile evidence produced by other reports.

For example, a `file-profile` report could answer:

```text
For this selected file, what evidence do we know across the checks system?
```

That report might need data from:

- `files` for line count, byte size, and family metadata
- `target-map` for scope, area, route, shared dependency, and boundary data
- a future [Git History Report](/docs/?scope=studio&doc=site-request-report-git-history) for recent changes
- a future [Imports Report](/docs/?scope=studio&doc=site-request-report-imports) for dependency references
- a future [Tests Report](/docs/?scope=studio&doc=site-request-report-tests) for test or smoke coverage links

The report should not duplicate those producers' logic.
It should read their JSON artifacts and compile a focused summary.

## Config Shape

This should be an extension to the `reports` section of `admin-app/checks/config/admin-checks.json`.

Example:

```json
{
  "reports": {
    "file-profile": {
      "label": "File Profile",
      "script": "admin-app/checks/reports/file_profile.py",
      "description": "Combined evidence for one selected file.",
      "requires": ["files", "target-map", "git-history", "imports"],
      "default_options": {},
      "allowed_options": {
        "path": {
          "type": "string"
        }
      }
    }
  }
}
```

`requires` must contain only allowlisted report ids from the same config file.
The browser must not be able to submit arbitrary producer chains, script paths, shell commands, or output paths.

## Orchestrator Behavior

If report dependencies are added, `admin-app/checks/run_reports.py` should:

1. Validate requested report ids through the existing registry.
2. Expand config-defined dependencies before execution.
3. Preserve dependency order so required reports run before dependent reports.
4. Record which reports were requested directly and which were run as dependencies.
5. Run each dependency through the normal report producer contract.
6. Pass the final run manifest to the dependent report so it can locate dependency artifacts.
7. Mark the dependent report as skipped or failed when any required dependency fails.
8. Preserve completed dependency artifacts even if the dependent summary report fails.

The expanded plan for a request such as:

```json
{
  "scope": "docs-viewer",
  "reports": ["file-profile"],
  "options": {
    "file-profile": {
      "path": "docs-viewer/runtime/js/docs-viewer-management.js"
    }
  }
}
```

might execute:

```text
files
target-map
git-history
imports
file-profile
```

The run summary should make the expansion visible.

## Artifact Contract

Each dependency remains a normal report and writes its own artifacts:

```text
var/admin/checks/<run-id>/
  files/
    report.json
    report.md
    report.csv
  target-map/
    report.json
    report.md
  file-profile/
    report.json
    report.md
```

The dependent report reads JSON artifacts from the same run directory.
It should not read previous run directories unless a later request explicitly defines cross-run comparison behavior.

The stable join key for file-level report data should be the repo-relative `path`.

## File Profile Report

`file-profile` is the likely first use case for dependencies.

Its input would be a selected repo-relative file path, validated against the selected run scope.
Its output could compile:

- file path
- scope, family, areas, and routes
- direct or shared target membership
- line count and byte size
- recent change evidence
- imports or dependency references
- related tests or smoke checks
- boundary flags or target-map findings

This should remain a separate report.
Do not add these drilldown fields to the `files` markdown report just to support exploratory analysis.
For broad file lists, `report.csv` is the pragmatic manual analysis path.

## Open Design Points

- whether dependency reports are always displayed in Admin or can be collapsed under the dependent report
- whether a dependency can be satisfied by an existing artifact from the same run only, or from a named previous run
- how strict the orchestrator should be when an optional dependency fails
- whether dependent reports can request narrower options for their dependencies
- how the API should expose direct-requested reports versus dependency-only reports

## Non-Goals

- no browser-defined dependency graphs
- no arbitrary script execution
- no dependency resolution outside `admin-checks.json`
- no cross-run joins until explicitly specified
- no UI drilldown scope creep in the v1 `files` report
