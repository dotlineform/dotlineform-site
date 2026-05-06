---
doc_id: scripts-studio-audit-service
title: Studio Audit Service
added_date: 2026-05-03
last_updated: "2026-05-06 20:35"
parent_id: studio
sort_order: 36
---
# Studio Audit Service

Script:

```bash
./scripts/studio/audit_service.py --port 8790
```

`bin/dev-studio` starts this service automatically.

## Purpose

The audit service is a localhost-only read service for allowlisted Studio maintenance audits.

The first allowlisted audit is:

- `studio-ready-state`

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | service availability check |
| `GET` | `/audits` | list allowlisted audit IDs and labels |
| `POST` | `/audits/run` | run one allowlisted audit by ID |

Run request:

```json
{
  "audit_id": "studio-ready-state"
}
```

The response includes `status`, `exit_code`, `summary`, `totals`, `findings`, timestamps, and raw `stdout` / `stderr`.

Audit failures are returned as successful service responses with `status: "failed"` and a non-zero `exit_code`. Invalid audit IDs return a request error.

## Security Boundary

- binds only to `127.0.0.1`
- allows CORS only from `http://localhost:*` and `http://127.0.0.1:*`
- accepts audit IDs only, not command text
- runs command arguments from a server-side allowlist
- does not accept browser-controlled paths, flags, environment, or working directories
- runs commands without a shell
- writes only minimal local logs under `var/studio/audits/logs/`

## Related References

- [Studio Audits](/docs/?scope=studio&doc=studio-audits)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
