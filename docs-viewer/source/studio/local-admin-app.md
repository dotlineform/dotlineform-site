---
doc_id: local-admin-app
title: Local Admin App
added_date: 2026-06-06
last_updated: 2026-07-15
parent_id: admin
viewable: true
---
# Local Admin App

## Server Boundary

Start Admin with `bin/local-admin`, through `bin/local-all`, or directly:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/admin_app_server.py --port 8768
```

The server binds to loopback by default, serves the Admin shell and allowlisted assets, validates the route registry, exposes runtime config, and dispatches narrow operational APIs. It does not proxy sibling-app routes.

## Active Routes

| Route | Purpose |
| --- | --- |
| `/admin/` | operations landing page |
| `/admin/audits/` | allowlisted audit launcher/results |
| `/admin/checks/` | configured report runs and snapshot review |
| `/admin/activity/` | unified activity feed |
| `/admin/testing/` | recent check-run summaries |

The exact route/template/script registry is `admin-config.json`.

## API Groups

- `/admin/api/audits/` — health, audit list, and ID-only run.
- `/admin/api/checks/` — report metadata, run creation, recent runs, summaries/reports, and confined snapshot deletion.
- `/admin/api/activity/` — health and read-only feed.
- `/admin/api/testing/` — health, recent runs, and focused summary reads.

POST/DELETE requests accept loopback origins only. Request bodies are capped. Run/report/audit IDs are validated, and resolved artifact paths must remain below their fixed roots.

## Runtime Config

`/admin/runtime-config.json` combines:

- the validated checked route registry;
- code-owned service endpoint maps;
- asset version;
- local output-path metadata for Activity, Checks, and Testing.

Browser modules use `admin-config.js`, `admin-route-registry.js`, `admin-route-templates.js`, and `admin-transport.js` rather than embedding server bindings independently.

## Output Ownership

- `var/admin/activity/` — feed and journal written by domain workflows;
- `var/admin/checks/` — report runs and target-map audit output;
- `var/admin/test-runs/` — check-profile summaries/logs;
- `var/admin/audits/logs/` — compact audit runner logs.

These are ignored local artifacts. Reading or deleting one family does not authorize arbitrary filesystem access.

## Verification

Focused server/config/API tests live under `admin-app/tests/python/`; route smokes live under `admin-app/tests/smoke/`. The `admin-smoke` profile is for route boot and API reachability, not every report interaction.
