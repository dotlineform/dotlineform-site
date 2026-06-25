---
doc_id: scripts-audit-route-ready-state
title: Route Ready-State Audit
added_date: 2026-06-25
last_updated: 2026-06-25
parent_id: admin
---
# Route Ready-State Audit

Script:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

Run this after changing Studio, Admin, Analytics, or Docs Viewer route templates, shell templates, route scripts, or route-ready helper code.

Structured output for the Admin audit API:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict --json
```

## Purpose

The audit keeps active local-app templates aligned with the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state) contract.
It covers the app-prefixed ready/busy baseline for Studio, Admin, Analytics, and Docs Viewer route shells.

## Checks

- each audited template exposes exactly one app-prefixed ready-state root
- the matching busy attribute lives on the same root
- busy starts as `false`
- ready starts as `false`, except for configured static home routes that intentionally start ready
- Docs Viewer public/manage shells expose the `data-docs-viewer-ready` / `data-docs-viewer-busy` baseline

## App Selection

Run every configured app:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

Limit the audit to one app:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict --app studio
```

Valid app IDs are `studio`, `admin`, `analytics`, and `docs-viewer`.

## `--strict`

Use strict mode for normal verification:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

Strict mode exits non-zero for warnings as well as errors. Without `--strict`, warnings are informational and errors still fail the run.

The `quick` profile in `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` includes this audit in strict mode.

`--json` emits the same pass/fail status, counts, totals, and findings as structured JSON for the Admin audit route and API under `/admin/audits/`.
