---
doc_id: site-request-risk-evidence-producers
title: Risk Evidence Producers Request
added_date: 2026-05-31
last_updated: 2026-06-10
ui_status: paused
parent_id: change-requests
---
# Risk Evidence Producers Request

Status: planned additional reports

## Summary

Replace the retired risk evidence pack with an Admin-owned checks system that runs allowlisted evidence reports, stores structured artifacts, and exposes read-only report results in Admin.

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

## Retired Legacy Risk Implementation

- Risk policy is described in [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).
- The legacy risk evidence pack docs, script, `/admin/risk/` route, `/admin/api/risk/...` API, and `var/admin/risk/` output root are retired.
- Legacy metrics and reports were a mix of reported fields, derived fields, and metadata. They should not define the final artifact paths, API names, route names, or report contract for the new system.
- Useful prior-art ideas have been split into focused child docs under this request.

## New Checks Implementation

The system is described in [Checks](/docs/?scope=studio&doc=admin-checks) and its child docs.

- Admin owns the checks system, including the CLI runner, report scripts, local API, UI route, and ignored local artifacts.
- The new route is `/admin/checks/`.
- The new API namespace is `/admin/api/checks/`.
- `admin-app/checks/reports/` is the only location for report producer scripts.
- The orchestrator is the only supported entry point for multi-report runs.
---
