---
doc_id: site-request-risk-evidence-producers-task-3-orchestrator
title: Risk Evidence Producers Task 3 Orchestrator
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 3 Orchestrator

This is the delivery specification for Batch 3 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 3: Build report orchestrator

Summary: Add the JSON-request runner that validates targets and executes allowlisted report scripts.

| ID | status | action |
| --- | --- | --- |
| 3.1 | done | Add `admin-app/checks/run_reports.py`. |
| 3.2 | done | Accept a JSON run request from `--request <path>` or standard input. |
| 3.3 | done | Support dry-run and write-run modes. |
| 3.4 | done | Validate scope, family ids, area ids, route ids, report ids, and report options through the registry. |
| 3.5 | done | Create run-level artifacts under `var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/`. |
| 3.6 | done | Invoke report scripts with explicit argv lists and record command metadata. |
| 3.7 | done | Preserve per-report status so one failed report does not erase completed report output. |

## Steer for these tasks

- The orchestrator is the only supported multi-report entry point.
- Browser-provided command strings, shell flags, environment values, arbitrary paths, and output roots remain prohibited.
- Dry runs must resolve the execution plan without writing run artifacts.

## Deliverables

- `admin-app/checks/run_reports.py`
- run request validation
- run-level artifact writing
- command metadata recording

## Implementation and policy guidance

- Report scripts are invoked by path and argv list, not shell command text.
- Failed reports should remain visible in run summaries alongside completed reports.
- Run directories live only under ignored `var/admin/checks/`.

## Proposed verification set

- Focused orchestrator tests for dry-run, write-run, validation, failed-report behavior, and artifact shape.
- Python syntax check for `run_reports.py`.

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/checks/admin_checks_config.py admin-app/checks/run_reports.py admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_run_reports.py`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_target_map_resolver.py admin-app/tests/python/test_run_reports.py`
- `printf '%s\n' '{"scope":"docs-viewer","families":[],"areas":[],"routes":[],"reports":["files"],"options":{"files":{"limit":5}},"write":false}' | $HOME/miniconda3/bin/python3 admin-app/checks/run_reports.py --json`

Focused pytest result: 14 passed.
The real config dry-run resolved the `docs-viewer` / `files` plan, merged the default `sort: lines_desc` option, reported 440 selected files for the scope, and did not write run artifacts.

## follow-on tasks

- Batch 4 plugs the `files` producer into the orchestrator.
- The orchestrator now invokes report scripts with this internal argv contract:

```text
<python> <script> --config <config> --run-manifest <manifest> --report-id <report-id> --output-dir <report-dir>
```

- Batch 4 should make `admin-app/checks/reports/files.py` read the run manifest and write `report.json` and `report.md` under the provided output directory.
- Batch 4 can use the existing orchestrator dry-run immediately; write runs for the real `files` report will fail until `files.py` exists.

## task close

- Batch 3 is complete.
- Added `admin-app/checks/run_reports.py`.
- Added focused orchestrator tests in `admin-app/tests/python/test_run_reports.py`.
- Hardened `validate_run_request()` so unknown top-level keys are rejected and `write` must be a JSON boolean.
