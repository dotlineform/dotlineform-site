---
doc_id: site-request-risk-evidence-producers-task-4-report-producers
title: Risk Evidence Producers Task 4 Files Report Producer
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 4 Files Report Producer

This is the delivery specification for Batch 4 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 4: Implement `files` report producer

Summary: Implement the v1 proof-of-concept `files` report. The durable reference for this report is [Files Report](/docs/?scope=studio&doc=admin-checks-report-files).

| ID | status | action |
| --- | --- | --- |
| 4.1 | done | Add `admin-app/checks/reports/files.py`. |
| 4.2 | done | Read the selected scope from resolved config rather than duplicating path rules. |
| 4.3 | done | Apply selected family, area, and route filters through the shared target resolver. |
| 4.4 | done | Count included files, lines, and bytes. |
| 4.5 | done | Produce `report.json`, `report.md`, and `report.csv`. |
| 4.6 | done | Support the initial `files` options `limit` and `sort`. |
| 4.7 | done | Include focused unit tests for path inclusion/exclusion, line/byte counting, sorting, and markdown rendering. |

## Steer for these tasks

- Each report script owns artifacts for one report only.
- The target resolver should be shared with the target-map audit and orchestrator.
- `files` is the only v1 report; `target-map` is deferred to [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map).

## Batch 3 handoff

Batch 3 added `admin-app/checks/run_reports.py`.
The orchestrator validates the JSON run request through `admin_checks_config.py`, checks that selected families, areas, and routes resolve inside the selected scope through `target_map_resolver.py`, merges report default options, and writes run artifacts under `var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/`.

Report scripts are invoked with this internal argv contract:

```text
<python> <script> --config <config> --run-manifest <manifest> --report-id <report-id> --output-dir <report-dir>
```

For `files.py`, read selected targets and merged options from the run manifest.
Write these artifacts under the provided output directory:

```text
report.json
report.md
report.csv
```

The orchestrator marks a report as failed when the script exits non-zero or exits zero without the required JSON and markdown artifacts.
Dry-runs work now for the configured `files` report; write-runs for the real `files` report will fail until this batch adds `admin-app/checks/reports/files.py`.

## Deliverables

- `admin-app/checks/reports/files.py`
- report JSON, markdown, and CSV outputs
- focused producer tests

## Implementation and policy guidance

- Keep markdown rendering simple: scripts write `.md`; API/browser display is handled later.
- Keep generated payloads, dependencies, caches, and local run outputs excluded by config.
- Do not duplicate path rules inside producers.

## Proposed verification set

- Focused producer tests for `files`.
- Orchestrator write run for `files` after Batch 3 is available.

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/checks/reports/files.py admin-app/tests/python/test_files_report.py admin-app/checks/run_reports.py admin-app/tests/python/test_run_reports.py`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_files_report.py admin-app/tests/python/test_run_reports.py admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_target_map_resolver.py`
- `printf '%s\n' '{"scope":"docs-viewer","families":[],"areas":[],"routes":[],"reports":["files"],"options":{"files":{"limit":5,"sort":"lines_desc"}},"write":true}' | $HOME/miniconda3/bin/python3 admin-app/checks/run_reports.py`

Focused pytest result: 18 passed.
The orchestrator write run passed and wrote `var/admin/checks/20260609-194626-docs-viewer`.
The produced `files` report recorded 440 files, 86,437 lines, and 3,518,142 bytes for the broad Docs Viewer scope.

## follow-on tasks

- Batch 5 exposes these reports through the Admin checks API.
- Batch 5 should read `run-summary.json`, `run-summary.md`, `files/report.json`, `files/report.md`, and optionally `files/report.csv` from `var/admin/checks/<run-id>/`.
- Batch 5 should treat report markdown as a raw string for display and should not render markdown to HTML server-side.
- Batch 5 can use the written run `var/admin/checks/20260609-194626-docs-viewer` as a local fixture shape example, but the API tests should create their own temporary run artifacts.

## task close

- Batch 4 is complete.
- Added `admin-app/checks/reports/files.py`.
- Added focused producer tests in `admin-app/tests/python/test_files_report.py`.
- Confirmed the Batch 3 orchestrator can execute the real `files` report in write mode.
