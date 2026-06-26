---
doc_id: audits
title: Audits
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: admin
---
# Audits

Route:

- `/admin/audits/`

The audit page surfaces local maintenance audits inside Admin.

The first version lists the route ready-state audit and provides a Run command. Results show pass/fail state, exit code, warning/error counts, run timestamp, findings when present, and a collapsible raw output block for debugging.

## Runtime

The page uses:

- `admin-app/app/frontend/js/admin-audits.js`
- `admin-app/app/frontend/js/admin-transport.js`
- `admin-app/app/server/admin_app/admin_audit_api.py`
- `admin-app/app/server/admin_app/audit_runner.py`
- `admin-app/checks/audit_route_ready_state.py`

Visible runtime copy is code-owned by the Admin frontend modules.

The local service endpoint definitions live in `admin-app/app/frontend/js/admin-transport.js`, matching the Admin transport pattern.
The active browser endpoints are hosted by the Admin app server under `/admin/api/audits/...`.

## Ready State

The route root is `#studioAuditsRoot`.

The page exposes:

- `data-studio-route="studio-audits"`
- `data-studio-ready`
- `data-studio-busy`
- `data-studio-mode="summary|running|result|unavailable"`
- `data-studio-service="available|unavailable"`

The page marks busy while an audit run is in progress and returns to ready after the service response or request failure settles.

## Service Behavior

When the local app audit API is unavailable, the page stays readable, disables the Run command, and exposes `data-studio-service="unavailable"`.

When the service is available, the page fetches `/admin/api/audits/audits` to list allowlisted audits. It currently expects:

- `route-ready-state`

Running the audit posts only the audit ID to `/admin/api/audits/audits/run`. The browser never sends command text, paths, shell flags, environment variables, or working directories.
