---
doc_id: scripts-audit-studio-ready-state
title: Studio Ready-State Audit
added_date: 2026-05-03
last_updated: 2026-06-06
parent_id: admin
---
# Studio Ready-State Audit

Script:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict
```

Run this after changing Studio route shells, dashboard shells, static/reference pages, or route-ready helper scripts.

Structured output for the Admin audit API:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict --json
```

## Purpose

The audit keeps the shared Studio ready-state contract from drifting as pages evolve. It is especially aimed at static/reference pages: those pages can expose a basic ready signal today, but if they later gain async data, service checks, commands, or additional route scripts, they should move to a route-specific ready/busy implementation.

## Checks

- every ready root starts with `data-studio-ready="false"` and `data-studio-busy="false"`
- static routes declare `data-studio-static-route` and load `studio-static-route.js`
- Studio module entry scripts are detected from direct module script tags
- a route does not mix static ready markers with route-specific ready markers
- strict mode fails when a static route loads another module script

## `--strict`

Use strict mode for normal verification:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict
```

Strict mode exits non-zero for warnings as well as errors. Without `--strict`, warnings are informational and errors still fail the run.

The `quick` profile in `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` includes this audit in strict mode.

`--json` emits the same pass/fail status, counts, totals, and findings as structured JSON for the Admin audit route and API under `/admin/audits/`.
