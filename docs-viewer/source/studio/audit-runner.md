---
doc_id: audit-runner
title: Audit Runner
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: admin
---
# Audit Runner

Script:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/audit_runner.py --audit-id route-ready-state
```

- Normal local sessions do not start a standalone audit service because the Admin app server owns the active audit HTTP surface through `admin-app/app/server/admin_app/admin_audit_api.py`.
- For Codex automation, call `admin-app/app/server/admin_app/audit_runner.py` directly instead of starting a sibling localhost service.
- Risk-related audits follow the same rule: use the Admin app server and allowlisted audit runner, not a separate risk server.

## Purpose

The audit runner owns the allowlisted maintenance audit registry and direct audit execution behavior.
The active Admin browser endpoints are served by `admin-app/app/server/admin_app/admin_audit_api.py`, which imports the runner module.

The first allowlisted audit is:

- `route-ready-state`

List allowlisted audits:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/audit_runner.py --list
```

Run the default ready-state audit:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/audit_runner.py --audit-id route-ready-state
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/admin/api/audits/health` | service availability check in the Admin app |
| `GET` | `/admin/api/audits/audits` | list allowlisted audit IDs and labels in the Admin app |
| `POST` | `/admin/api/audits/audits/run` | run one allowlisted audit by ID in the Admin app |

Run request:

```json
{
  "audit_id": "route-ready-state"
}
```

The response includes `status`, `exit_code`, `summary`, `totals`, `findings`, timestamps, and raw `stdout` / `stderr`.

Audit failures are returned as successful service responses with `status: "failed"` and a non-zero `exit_code`. Invalid audit IDs return a request error.

When the request includes valid Admin activity context from `/admin/audits/`, the Admin API appends one unified activity row with script purpose `run audit`. The detail items include the audit label, pass/warn/fail status, error and warning counts, and duration.

## Security Boundary

- accepts audit IDs only, not command text
- runs command arguments from a server-side allowlist
- does not accept browser-controlled paths, flags, environment, or working directories
- runs commands without a shell
- writes only minimal local logs under `var/admin/audits/logs/`
- writes unified activity rows only through the fixed local activity feed paths
