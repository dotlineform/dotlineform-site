---
doc_id: site-request-admin-checks-reports
title: Admin Checks Reports
added_date: 2026-05-31
last_updated: 2026-06-10
ui_status: in-progress
parent_id: change-requests
---
# Admin Checks Reports

Status: planned responsibility reports

## Summary

This request is about responsibility and ownership evidence in the Admin-owned checks system.
It is not a catch-all request for every future checks report.

The Admin-owned checks system runs allowlisted evidence reports, stores structured artifacts, and exposes read-only report results in Admin.

The system is described in [Checks](/docs/?scope=studio&doc=admin-checks) and its child docs.

- Admin owns the checks system, including the CLI runner, report scripts, local API, UI route, and ignored local artifacts.
- The new route is `/admin/checks/`.
- The new API namespace is `/admin/api/checks/`.
- `admin-app/checks/reports/` is the only location for report producer scripts.
- The orchestrator is the only supported entry point for multi-report runs.

The system is report-oriented:

- a report is the user-facing output
- metrics are the measured fields used to produce a report
- producers are report scripts that collect metrics and render one report
- a run is one orchestrated execution of one or more reports against one scope

Production reports so far:

- `files` for line count, byte size, and CSV-friendly file inventory evidence
- `target-map` for configured ownership, shared dependency, and boundary evidence

Possible future responsibility reports are captured as child documents.
Each report should answer one narrow review question and write its own JSON evidence.
A later compound report can join those artifacts, but the narrow reports should not become broad risk dashboards.

Operational, runtime, payload, generated-artifact, and performance report requests belong in [Admin Checks Operational Reports](/docs/?scope=studio&doc=site-request-admin-checks-operational-reports) unless their primary question is responsibility evidence.

## Implementable Report Requests

The next report requests should move toward a consistent implementation contract:

- report id and producer path
- one primary review question
- selected file set source
- bounded options from `admin-app/checks/config/admin-checks-reports.json`
- required JSON fields
- Markdown section shape
- focused fixture tests
- explicit non-goals

These report requests are most relevant to detecting files or families that may still be carrying mixed responsibilities:

```text
Question                                      Evidence report
--------------------------------------------  ----------------
Which files are unusually large?              files
Which files cross configured ownership?       target-map
Which files import across boundaries?         imports
Which files are imported by many files?       imports
Which files changed often recently?           git-history
Which files expose broad code surfaces?       code-surface
Which files lack discovered test links?       tests
Which files contain configured smell tokens?  static-searches
```

The combined architectural question is:

```text
Which files or families show repeated evidence of mixed responsibility?
```

That should be answered by a later dependency report that reads existing `report.json` artifacts.
It should not force each narrow report to calculate a broad risk score.

## Out Of Scope

This request should not absorb checks just because they can run through the same Admin Checks machinery.
Separate requests should own reports whose primary question is:

- whether generated payloads are large, valid, or structurally broad
- whether route smoke profiles have recent runtime evidence
- whether a route, payload, or browser workflow has specific performance metrics
- whether build artifacts are fresh or complete

Those reports may still use the same runner and UI, but they answer different product questions.

## Risk Policy

The ambition is that these reports will contribute to assessing the risks present in the repo apps.

- Risk policy is described in [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).

---
