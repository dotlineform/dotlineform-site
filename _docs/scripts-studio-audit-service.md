---
doc_id: scripts-studio-audit-service
title: Studio Audit Service
added_date: 2026-05-03
last_updated: "2026-05-08 19:25"
parent_id: studio
sort_order: 8000
---
# Studio Audit Service

Script:

```bash
./scripts/studio/audit_service.py --port 8790
```

Normal `bin/dev-studio` sessions do not start this standalone service by default because the local Studio app server owns the active audit HTTP surface through `scripts/studio/studio_audit_api.py`.
Set `AUDIT_SERVICE_ENABLED=1` only for fallback/debug runs that intentionally need the old standalone process.

## Purpose

The audit service module owns the allowlisted Studio maintenance audit registry and reusable run logic.
The active local Studio endpoints are served by `scripts/studio/studio_audit_api.py`; the standalone script remains available as a localhost-only fallback/debug service.

The first allowlisted audit is:

- `studio-ready-state`

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/studio/api/audits/health` | service availability check in the local Studio app |
| `GET` | `/studio/api/audits/audits` | list allowlisted audit IDs and labels in the local Studio app |
| `POST` | `/studio/api/audits/audits/run` | run one allowlisted audit by ID in the local Studio app |
| `GET` | `/health` | standalone fallback service availability check |
| `GET` | `/audits` | standalone fallback registry read |
| `POST` | `/audits/run` | standalone fallback audit run |

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

- binds only to `127.0.0.1`
- allows CORS only from `http://localhost:*` and `http://127.0.0.1:*`
- accepts audit IDs only, not command text
- runs command arguments from a server-side allowlist
- does not accept browser-controlled paths, flags, environment, or working directories
- runs commands without a shell
- writes only minimal local logs under `var/studio/audits/logs/`
- writes unified activity rows only through the fixed local activity feed paths owned by `scripts/studio_activity.py`

## Related References

- [Studio Audits](/docs/?scope=studio&doc=studio-audits)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
