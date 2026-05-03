---
doc_id: site-request-studio-audits-page
title: Studio Audits Page Request
added_date: 2026-05-03
last_updated: 2026-05-03
ui_status: implemented
parent_id: change-requests
sort_order: 38
---
# Studio Audits Page Request

Status:

- implemented

## Current Implementation

The first slice is implemented.

- `/studio/audits/` renders a compact Studio audit page.
- `/studio/` links to Audits from Resources.
- `assets/studio/js/studio-audits.js` loads the audit registry, probes service availability, runs an allowlisted audit, renders results, and maintains route-ready attributes.
- `scripts/studio/audit_service.py` exposes the local read-only audit service.
- `scripts/audit_studio_ready_state.py --strict --json` provides structured output for the service.
- `bin/dev-studio` starts the audit service on `AUDIT_SERVICE_PORT`, default `8790`.

Only `studio-ready-state` is wired in this slice.

## Summary

Add a small Studio Audits page that surfaces key audit checks from inside Studio and lets the local development user run allowlisted audit scripts through a loopback-only service.

The first implementation should wire only the Studio ready-state audit. The page should be designed as a narrow framework that can later include site consistency, docs broken links, CSS token, and other maintenance audits without becoming a broad QA dashboard.

## Reason

Audit scripts are useful but easy to forget during ordinary Studio work. The ready-state audit is now part of the `quick` check profile, but a Studio page would make audit state discoverable from the main Studio workflow and give future audit findings a consistent place to appear.

The Studio home page already has a Resources section. Linking an Audits page there would turn audit checks from a hidden terminal habit into a visible Studio maintenance task.

## Goals

- add `/studio/audits/` as a Studio route linked from the `/studio/` Resources section
- expose a route-ready contract on the Audits page root
- show the available audit checks and their current state
- provide a command button to run the Studio ready-state audit through a local service
- render status, exit code, finding counts, findings, and run timestamp without scraping browser console output
- keep the service command surface explicitly allowlisted
- leave space for future audits without overbuilding a formal QA product

## Non-Goals

- replacing `./scripts/run_checks.py`
- running arbitrary repo commands from the browser
- adding a hosted or public audit runner
- creating a full CI dashboard
- storing persistent audit history in tracked files
- implementing every audit script in the first slice

## Proposed Route

Route:

- `/studio/audits/`

Studio home link:

- add a Resources link from `/studio/` to `/studio/audits/`

Root contract:

- `id="studioAuditsRoot"`
- `data-studio-route="studio-audits"`
- `data-studio-ready="false"` until the page has loaded config and service status
- `data-studio-busy="true"` while an audit run is in progress
- `data-studio-mode="summary|running|result|unavailable"`
- `data-studio-service="available|unavailable"`

## Proposed UI

The first version should stay compact:

- a status area for the local audit service
- one audit row or panel for `studio-ready-state`
- a Run command button
- last run timestamp
- pass/fail status
- counts for errors and warnings
- a concise findings list when findings exist
- a terminal-output disclosure only if needed for debugging

The page should not use card-heavy marketing layout. It should follow existing Studio admin-tool patterns: clear status, direct command, compact result details, and no decorative wrapper around the whole page.

Visible runtime copy should live in `assets/studio/data/studio_config.json`.

## Audit Registry

The client should be driven by a small registry rather than hardcoding a single button flow throughout the page.

Initial audit:

| ID | Label | Command owner | Script | Strict? |
|---|---|---|---|---|
| `studio-ready-state` | Studio ready state | audit service | `scripts/audit_studio_ready_state.py` | yes |

Future candidates:

- `site-consistency`
- `docs-broken-links`
- `css-token-audit`

Future audits should be added one at a time with explicit output contracts, not by exposing a generic shell endpoint.

## Service Contract

Add a local audit service under `scripts/studio/`, following the existing Studio service pattern.

Requirements:

- bind only to loopback
- allow only localhost Studio origins
- expose explicit audit IDs rather than command strings
- run only allowlisted commands
- use the configured Python interpreter shape from the local environment where practical
- return structured JSON
- keep logs limited to audit ID, status, counts, and exit code

Suggested endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | service availability check |
| `GET` | `/audits` | list available audit IDs and labels |
| `POST` | `/audits/run` | run one allowlisted audit by ID |

Suggested request:

```json
{
  "audit_id": "studio-ready-state"
}
```

Suggested response:

```json
{
  "ok": true,
  "audit_id": "studio-ready-state",
  "status": "passed",
  "exit_code": 0,
  "started_at": "2026-05-03T00:00:00Z",
  "finished_at": "2026-05-03T00:00:01Z",
  "summary": {
    "errors": 0,
    "warnings": 0
  },
  "findings": [],
  "stdout": "{...}"
}
```

## Audit Script Output

The ready-state audit should gain a JSON output mode before the Studio page depends on it.

Suggested command:

```bash
./scripts/audit_studio_ready_state.py --strict --json
```

JSON mode should preserve the existing human-readable terminal output by default and only emit JSON when explicitly requested.

Suggested JSON shape:

```json
{
  "status": "passed",
  "totals": {
    "templates": 29,
    "ready_roots": 28,
    "static_routes": 6,
    "dashboard_routes": 4
  },
  "summary": {
    "errors": 0,
    "warnings": 0
  },
  "findings": []
}
```

Finding shape:

```json
{
  "severity": "error",
  "path": "studio/index.md",
  "message": "static route is missing studio-static-route.js"
}
```

## Security Boundaries

- Do not accept arbitrary command text from the browser.
- Do not allow request payloads to set paths, environment variables, shell flags, or working directories.
- Do not run through a shell when `subprocess` can execute an argument list directly.
- Keep the command allowlist in server code, not in browser-controlled config.
- Keep the service read-only for the first slice.
- Do not persist full audit output into tracked docs or data files.

## Implementation Tasks

1. Add JSON output to `scripts/audit_studio_ready_state.py`.
2. Add a loopback-only audit service under `scripts/studio/` with `health`, `audits`, and `audits/run` endpoints.
3. Add `studio_config.json` entries for the Audits route, labels, and status text. Endpoint URLs remain in `assets/studio/js/studio-transport.js`, matching the existing local-service boundary.
4. Add `/studio/audits/index.md` with the Studio route root and Resources navigation target.
5. Add `assets/studio/js/studio-audits.js` for service health, audit registry rendering, run command state, result rendering, and route-ready attributes.
6. Add the `/studio/audits/` link to the `/studio/` Resources section.
7. Document the new service and route in Studio/runtime/script docs.
8. Add the audit service to the local Studio runner.
9. Add targeted smoke coverage for service unavailable, passing audit, and failing audit states.
10. Update the site change log when the feature is implemented.

## Verification Matrix

| Slice | Codex-run checks | Manual checks |
|---|---|---|
| JSON audit output | Python syntax check; `./scripts/audit_studio_ready_state.py --strict`; JSON output parse check | Compare human and JSON summaries for the same run |
| Audit service | service health check; allowed audit run; invalid audit ID rejection | Confirm service binds only to loopback and logs only minimal run metadata |
| Studio page | Jekyll build; Playwright smoke for unavailable and passing states | Open `/studio/audits/`, run the audit, inspect findings display and button/busy behavior on desktop and mobile |
| Home link | Jekyll build; link presence check | Open `/studio/` and follow the Audits link from Resources |

## Benefits

- makes audit checks discoverable from the Studio workflow
- reduces dependence on remembering terminal commands
- creates a shared UI pattern for future maintenance checks
- gives ready-state audit failures a visible place to appear during Studio development

## Risks

- adding another local service increases maintenance surface
- generic command execution would be unsafe if the service boundary is widened
- parsing free-form terminal output would be brittle unless JSON output is added first
- the page could sprawl if it tries to become a full QA dashboard too early
