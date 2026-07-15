---
doc_id: audit-runner
title: Audit Runner
added_date: 2026-06-07
last_updated: 2026-07-15
parent_id: admin
---
# Audit Runner

## Role

`audit_runner.py` is the allowlist and process boundary behind `/admin/audits/`. It turns a stable audit ID into fixed server-owned command arguments and normalizes the structured result for the Admin API.

Only `route-ready-state` is currently registered. The registry in code is the exhaustive authority.

## Execution Path

```text
Admin Audits route
  -> POST audit_id to Admin audit API
  -> audit_runner allowlist lookup
  -> fixed argv, cwd, and structured-output mode
  -> audit subprocess without a shell
  -> normalized result + optional Admin activity row
```

The browser cannot provide command text, paths, flags, environment, or working directory.

## Direct Use

List or run the current allowlist without starting a separate service:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/audit_runner.py --list
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/audit_runner.py --audit-id route-ready-state
```

The active HTTP surface belongs to `admin_app_server.py` and `admin_audit_api.py`. There is no standalone audit server to start.

## Extension Method

A new Admin audit needs:

- a deterministic script with structured JSON output;
- one explicit `AuditDefinition` in `build_audit_registry()`;
- a concise UI label and description;
- focused runner/API tests;
- a reason it is an operator-triggered audit rather than a normal check-profile step or an Admin Checks report.

Keep the registry small. Direct maintenance audits and configurable evidence reports are different workflows; do not make one generic command launcher.

## Artifacts And Failure Semantics

- the subprocess result is returned even when the audit reports failure;
- invalid IDs and invalid structured output are request/runtime errors;
- minimal runner logs live under `var/admin/audits/logs/`;
- an Admin-originated run may append a normalized activity entry.

Endpoint paths and response fields are projected by `admin_app_config.py` and implemented by `admin_audit_api.py`; read those files when an exact contract matters.
