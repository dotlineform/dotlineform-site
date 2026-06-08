---
doc_id: site-request-risk-evidence-producers
title: Risk Evidence Producers Request
added_date: 2026-05-31
last_updated: 2026-06-07
ui_status: draft
parent_id: change-requests
viewable: true
---
# Risk Evidence Producers Request

Status:

- draft

## Summary

We need to replace the current risk evidence pack with a new script and reporting structure. This will continue to be owned by Admin app.

## Current Implementation

- risk policy described in [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).
- initial implementation of [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack).
- metrics and reports are listed in [Risk Evidence Pack Metrics](/docs/?scope=studio&doc=risk-evidence-pack-metrics). However the current list is a mix of reported fields, derived fields and metadata.
- the risk evidence pack is run on `/admin/risk/`, however this is mainly surfacing summary information and doesn't clearly differentiate between metrics and reports.
- current scripts were written to support inventories of the apps, to measure the risk associated with each script family. these inventories have been retired pending review of the risk policy and implementation.

## New Implementation

Before considering whether any new 'risk inventories' need to be defined, we need to create a structured way of collecting and reporting evidence.

key features of the new implementaion:

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

some reports by their nature may necessarily have smaller scope. scopes will be defined by folder and file level inclusion in a `checks-config.json` file.

## Approach

- keep the current implementation and route because it contains reusable ideas and code
- start a new implementation for data collection and reporting
- develop a new UI at `/admin/checks/`
- when the new system is working and has effectively replicated or discarded the current risk evidence capabilities, the current implementation and route will be retired. scripts and artifacts that no longer serve an active role will be deleted. legacy reporting data and folder paths will be deleted.

## Artifacts

- Each run saves summary files in `var/admin/checks/<date-time>-<scope>/`
    - `commands.json`
    - `manifest.json`
    - `run-summary.json`
    - `run-summary.md`
- each report in a run saves files in `var/admin/checks/<date-time>-<scope>/<report>/`
    - `report.json` - raw data
    - `report.md` - structured report

## First Report

The first report to be produced contains file metrics: line count and file size.

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