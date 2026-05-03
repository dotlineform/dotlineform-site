---
doc_id: scripts-audit-studio-ready-state
title: "Studio Ready-State Audit"
added_date: 2026-05-03
last_updated: 2026-05-03
parent_id: scripts
sort_order: 29
---
# Studio Ready-State Audit

Script:

```bash
./scripts/audit_studio_ready_state.py --strict
```

Run this after changing Studio route shells, dashboard shells, static/reference pages, or route-ready helper scripts.

Structured output for the Studio audit service:

```bash
./scripts/audit_studio_ready_state.py --strict --json
```

## Purpose

The audit keeps the shared Studio ready-state contract from drifting as pages evolve. It is especially aimed at static/reference pages: those pages can expose a basic ready signal today, but if they later gain async data, service checks, commands, or additional route scripts, they should move to a route-specific ready/busy implementation.

## Checks

- every ready root starts with `data-studio-ready="false"` and `data-studio-busy="false"`
- static routes declare `data-studio-static-route` and load `studio-static-route.js`
- dashboard routes declare `data-studio-dashboard-route` and load `studio-dashboard.js`
- a route does not mix static and dashboard ready markers
- static routes do not expose dashboard metric markers
- strict mode fails when a static route loads another module script

## `--strict`

Use strict mode for normal verification:

```bash
./scripts/audit_studio_ready_state.py --strict
```

Strict mode exits non-zero for warnings as well as errors. Without `--strict`, warnings are informational and errors still fail the run.

The `quick` profile in `./scripts/run_checks.py` includes this audit in strict mode.

`--json` emits the same pass/fail status, counts, totals, and findings as structured JSON for `/studio/audits/`.

## Related References

- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Studio Audits](/docs/?scope=studio&doc=studio-audits)
