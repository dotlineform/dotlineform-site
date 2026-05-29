---
doc_id: scripts-studio-audit-service
title: Studio Audit Runner
added_date: 2026-05-03
last_updated: "2026-05-23"
parent_id: audit
viewable: true
---
# Studio Audit Runner

Script:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/audit_runner.py --audit-id studio-ready-state
```

Normal Studio sessions do not start a standalone audit service because the local Studio app server owns the active audit HTTP surface through `studio/app/server/studio/studio_audit_api.py`.
For Codex automation, call `studio/app/server/studio/audit_runner.py` directly instead of starting a sibling localhost service.

## Purpose

The audit runner owns the allowlisted Studio maintenance audit registry and direct audit execution behavior.
The active local Studio browser endpoints are served by `studio/app/server/studio/studio_audit_api.py`, which imports the runner module.
The retired `studio/app/server/studio/audit_service.py` HTTP wrapper is no longer part of the local development stack.

The first allowlisted audit is:

- `studio-ready-state`

List allowlisted audits:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/audit_runner.py --list
```

Run the default ready-state audit:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/audit_runner.py --audit-id studio-ready-state
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/studio/api/audits/health` | service availability check in the local Studio app |
| `GET` | `/studio/api/audits/audits` | list allowlisted audit IDs and labels in the local Studio app |
| `POST` | `/studio/api/audits/audits/run` | run one allowlisted audit by ID in the local Studio app |

Run request:

```json
{
  "audit_id": "studio-ready-state"
}
```

The response includes `status`, `exit_code`, `summary`, `totals`, `findings`, timestamps, and raw `stdout` / `stderr`.

Audit failures are returned as successful service responses with `status: "failed"` and a non-zero `exit_code`. Invalid audit IDs return a request error.

When the request includes valid Studio activity context from `/studio/audits/?mode=manage`, the local app API appends one unified Studio activity row with script purpose `run audit`. The detail items include the audit label, pass/warn/fail status, error and warning counts, and duration.

## Security Boundary

- accepts audit IDs only, not command text
- runs command arguments from a server-side allowlist
- does not accept browser-controlled paths, flags, environment, or working directories
- runs commands without a shell
- writes only minimal local logs under `var/studio/audits/logs/`
- writes unified activity rows only through the fixed local activity feed paths owned by `scripts/studio_activity.py`

## Related References

- [Studio Audits](/docs/?scope=studio&doc=studio-audits)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
