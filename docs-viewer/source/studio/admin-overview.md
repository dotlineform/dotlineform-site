---
doc_id: admin-overview
title: Admin Overview
added_date: 2026-07-15
last_updated: 2026-07-15
parent_id: admin
viewable: true
---
# Admin Overview

## What Admin Is

Admin is a loopback-only app for running and reviewing cross-repository operational evidence. It does not own Studio authoring, Analytics data, Docs Viewer management, or the public site; it inspects those boundaries through allowlisted checks and generated local reports.

## Capabilities

- launch server-side allowlisted audits;
- target configured repo scopes/families/areas/routes and run allowlisted reports;
- read and delete confined local checks snapshots;
- review normalized activity emitted by sibling apps;
- review recent check-profile summaries.

## Execution Path

```text
browser /admin route
  -> Admin server serves admin-shell.html
  -> admin-app.js loads runtime config
  -> route registry resolves template + script
  -> route controller calls one Admin API adapter
  -> adapter validates ID/options/path
  -> audit, report orchestrator, or local summary reader
  -> ignored artifact under var/admin/ or structured response
```

Stable HTML belongs in route templates. Route scripts own async loading, result rendering, and commands. Python owns filesystem access, process execution, configuration validation, and allowlists.

## Authority Boundaries

### Routes And Runtime Config

`admin-app/app/frontend/config/admin-config.json` is the checked route registry. `admin_app_config.py` validates it and adds service endpoints plus local output-path metadata at `/admin/runtime-config.json`.

### Audits

`audit_runner.py` is the audit allowlist and direct execution boundary. The browser sends an audit ID only; it cannot supply command text, paths, flags, environment, or working directory.

### Checks

`admin-checks.json` owns target policy. `admin-checks-reports.json` owns report registration, default options, and allowed option schemas. `target_map_resolver.py` provides the shared resolution implementation. `run_reports.py` executes validated report plans.

### Activity And Testing

Activity is written by domain services through the shared activity contract and stored under `var/admin/activity/`. Testing summaries are written by `run_checks.py` under `var/admin/test-runs/`. The Admin routes are read models over those outputs, not their producers.

## Extension Method

- New route: add template/script and register it in `admin-config.json`.
- New audit: add a deterministic check and explicit server-side allowlist entry.
- New checks report: add a focused producer, registry entry, config validation, artifacts, and tests.
- New local artifact reader: expose a narrow ID-based API confined to one known root.
- New cross-app evidence: update the target map and run its audit; do not give the browser repo-wide path selection.

## Known Weak Spots

- Route templates and CSS/DOM identifiers still carry historical `studio*` and `tagStudio*` naming even though lifecycle attributes are Admin-owned.
- `admin_app_config.py` projects the route registry into both `app.routes` and runtime `views`, creating two shapes for the same route data.
- The checks target map is hand-maintained policy and already contains inventory-only paths for retired surfaces; the target-map audit is essential, and an inventory row is not proof of an active route.
- Checks, audits, Activity, and Testing have related but separate artifact/result shapes rather than one normalized operational-result model.
- The risk method is documentation guidance, not a live Admin risk dashboard. Current action should live in a change request or checks run, not an empty per-app inventory page.

## Where To Look First

- route or navigation issue: `admin-config.json`, `admin-route-registry.js`, route template/script;
- API or safety issue: the matching `admin_*_api.py` adapter and server tests;
- target-map issue: checks config, resolver, audit, and target-map report;
- report issue: report registry, producer, orchestrator artifacts, and focused tests;
- lifecycle issue: `admin-route-state.js` and the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state).
