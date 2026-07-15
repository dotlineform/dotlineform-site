---
doc_id: audits
title: Audits
added_date: 2026-06-07
last_updated: 2026-07-15
parent_id: admin
viewable: true
---
# Audits

## Workflow

`/admin/audits/` lists the audits registered by `admin-app/app/server/admin_app/audit_runner.py`.

1. The route probes the audit API and loads the server-side allowlist.
2. Run posts one audit ID plus normalized Admin activity context.
3. The runner executes its fixed argv without a shell.
4. The response separates status, exit code, counts, findings, timing, stdout, and stderr.
5. The route keeps results visible and records the user-initiated audit in Activity.

Audit failure is a valid execution result, not an HTTP transport failure. Unknown IDs or invalid requests are request errors.

## Ownership

- route controller: `admin-app/app/frontend/js/admin-audits.js`
- browser endpoints: `admin-transport.js`
- HTTP adapter: `admin_audit_api.py`
- allowlist and execution: `audit_runner.py`
- audit implementations: `admin-app/checks/`

The browser never sends commands, paths, flags, environment, or working directories.

## Extension And Weak Spots

Add only deterministic maintenance checks with structured output and a clear reason to run them interactively. Register the audit server-side and cover both direct runner and API behavior.

The route includes a fallback audit list for unavailable/malformed list responses. That improves resilience but duplicates allowlist metadata in the browser; the server registry remains authoritative.

The route uses `#studioAuditsRoot` with Admin-prefixed ready/busy attributes. The historical DOM name is not an ownership signal.
