---
doc_id: scripts-run-checks
title: Run Checks
added_date: 2026-05-01
last_updated: 2026-07-15
parent_id: dev-home
---
# Run Checks

## Role

`admin-app/commands/run_checks.py` coordinates optional repo check profiles and writes one local evidence snapshot under `var/admin/test-runs/`.

It is not a mandatory gate. Use a focused command when one owner changed; use a profile when several checks form useful evidence for one blast radius.

## Commands

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --list
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick --profile catalogue
```

`--list` and the profile definitions in code are the exact current command inventory.

## Profile Intent

- `quick` — cheap repo/config/projection/readiness/Python confidence.
- `catalogue` — catalogue Python contracts plus representative build preview.
- `docs` — Docs Viewer/Data Sharing Python contracts plus Studio docs/search generation.
- `admin-checks` — Admin Checks Python contracts.
- `admin-smoke`, `analytics-smoke`, `docs-viewer-smoke`, `studio-smoke` — app-owned browser/runtime boundaries.
- `full` — the broad configured aggregate; inspect `--list` because it does not imply every app smoke.

Do not mirror every child command here; that list changes with code.

## Outputs

Each run writes:

- `var/admin/test-runs/<run-id>/summary.md`
- `var/admin/test-runs/<run-id>/summary.json`
- one log per command

Closeout should report profile, pass/fail, and the Markdown summary path.

## Extension Method

- add a command only when it proves a durable contract;
- assign it to the app/profile that owns the behavior;
- keep expensive/niche checks focused unless routine grouped confidence is valuable;
- do not add UI choreography merely because a browser harness exists;
- keep `full` composition intentional and visible in `--list`.

[Testing](/docs/?scope=studio&doc=testing) owns evidence selection. [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing) owns browser harness rules.
