---
doc_id: site-request-admin-checks-reports
title: Admin Checks Reports
added_date: 2026-05-31
last_updated: 2026-06-10
ui_status: in-progress
parent_id: change-requests
---
# Admin Checks Reports

Status: planned additional reports

## Summary

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

The first production report is `files` for line count and file size evidence.

Possible future dependency reports are captured as child documents.

## Risk Policy

The ambition is that these reports will contribute to assessing the risks present in the repo apps.

- Risk policy is described in [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).

---
