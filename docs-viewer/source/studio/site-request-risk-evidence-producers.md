---
doc_id: site-request-risk-evidence-producers
title: Risk Evidence Producers Request
added_date: 2026-05-31
last_updated: 2026-06-10
ui_status: in-progress
parent_id: change-requests
---
# Risk Evidence Producers Request

Status: planned additional reports

## Summary

Replace the current risk evidence pack with an Admin-owned checks system that runs allowlisted evidence reports, stores structured artifacts, and exposes read-only report results in Admin.

The new system is report-oriented:

- a report is the user-facing output
- metrics are the measured fields used to produce a report
- producers are report scripts that collect metrics and render one report
- a run is one orchestrated execution of one or more reports against one scope

The first production report is `files` for line count and file size evidence.

A later dependency model for compound reports is captured as an option in [Risk Evidence Producers Report Dependencies](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-dependencies).

Possible future dependency reports are captured as options in:
- [Git History Report](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-git-history)
- [Imports Report](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-imports)
- [Tests Report](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-tests)
- [Static Searches](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-static-searches)
- [Generated Payloads](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-generated-payloads)
- [Script Family Inventory](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-script-family-inventory)
- [JavaScript Inventory Guardrail](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-javascript-inventory-guardrail)
- [Runtime Checks](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-runtime-checks)
- [Subjective Notes](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-subjective-notes).

## Legacy Risk Implementation

- risk policy described in [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).
- legacy implementation of [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack).
- legacy metrics and reports are listed in [Risk Evidence Pack Metrics](/docs/?scope=studio&doc=risk-evidence-pack-metrics). However the current list is a mix of reported fields, derived fields and metadata.
- the legacy risk evidence pack is run on `/admin/risk/`, however this is mainly surfacing summary information and doesn't clearly differentiate between metrics and reports.
- current scripts were written to support inventories of the apps, to measure the risk associated with each script family. these inventories have been retired pending review of the risk policy and implementation.
- Existing `/admin/risk/` code is reusable prior art only. It should not define the final artifact paths, API names, route names, or report contract for the new system.
- Existing `/admin/risk/` remains available until the new checks system has replicated or intentionally discarded its useful capabilities.

## New Checks Implementation

The system is described in [Checks](/docs/?scope=studio&doc=admin-checks) and its child docs.

- Admin owns the checks system, including the CLI runner, report scripts, local API, UI route, and ignored local artifacts.
- The new route is `/admin/checks/`.
- The new API namespace is `/admin/api/checks/`.
- `admin-app/checks/reports/` is the only location for report producer scripts.
- The orchestrator is the only supported entry point for multi-report runs.
---