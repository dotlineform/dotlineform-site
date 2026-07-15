---
doc_id: admin
title: Admin
added_date: 2026-06-06
last_updated: 2026-07-15
parent_id: ""
viewable: true
---
# Admin

Admin is the local operational review app. [Admin Overview](/docs/?scope=studio&doc=admin-overview) explains its execution, authority, extension, and weak-spot model.

## Use Admin

- [Audits](/docs/?scope=studio&doc=audits) — run an allowlisted maintenance audit and inspect structured findings.
- [Checks](/docs/?scope=studio&doc=admin-checks) — run configured evidence reports against a selected repo target.
- [Activity](/docs/?scope=studio&doc=activity) — review normalized actions emitted by local apps and services.
- [Testing](/docs/?scope=studio&doc=testing) — choose verification; `/admin/testing/` shows recent check-run summaries.

## Operate And Change Admin

- [Local Admin App](/docs/?scope=studio&doc=local-admin-app) — server, routes, APIs, runtime config, and safety boundary.
- [Admin Config JSON](/docs/?scope=studio&doc=config-admin-config-json) — route registry and runtime projection.
- [Local Runners](/docs/?scope=studio&doc=scripts-local-studio) — start Admin alone or with sibling apps.
- [Risk Review Method](/docs/?scope=studio&doc=risk-analysis-policy) — turn evidence into a bounded improvement, not a permanent dashboard inventory.

## Code Authority

- `admin-app/app/frontend/` — shell, route templates, controllers, transport, and route state.
- `admin-app/app/server/admin_app/` — runtime config, API adapters, allowlists, and confined local reads/writes.
- `admin-app/checks/` — checks configuration, target resolution, audits, and report producers.
- `admin-app/commands/run_checks.py` — verification profiles and run summaries.
- `admin-app/tests/` — server, config, report, runner, and route contracts.
- `var/admin/` — ignored activity, checks, audit, and test-run output.

Exact routes, report IDs, audit IDs, and payload fields belong in focused references or code, not on this entry page.
