---
doc_id: site-request-studio-risk-route
title: Studio Risk Route Request
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: done
parent_id: site-request-risk-analysis-inventory-redesign
viewable: true
---
# Studio Risk Route Request

Status:

- done

## Summary

Add a Local Studio route for running allowlisted risk evidence producers and reading their generated summaries.

Proposed route:

- `/studio/risk/?mode=manage`

The route should make risk evidence production discoverable from Studio without introducing a new server or generic command runner.

## Reason

Risk analysis now has a central policy, dashboard, app inventories, operations boundary, and evidence-pack contract.
The next likely usability problem is that risk scripts and audit functions remain terminal-only unless surfaced through Studio.

A Studio route can provide a simple user-facing way to:

- list available risk evidence producers
- run an allowlisted evidence pack
- see whether the run passed, warned, or failed
- display the generated `summary.md` or `summary.json`
- open safe detailed artifacts
- record the run in Studio Activity when a report is written

## Goals

- add `/studio/risk/?mode=manage` as a Local Studio app route
- keep the route under the existing Studio app shell
- expose only allowlisted risk producers and safe options
- run `studio/checks/risk_evidence_pack.py` through a Local Studio API adapter after the command-line runner exists
- write run artifacts under `var/studio/risk/runs/<run-id>/`
- read and render generated summaries from the run directory
- optionally expose a compact current summary from `studio/data/generated/risk/` if the UI needs a stable read model
- append a unified Studio Activity row when a user-initiated run writes a report

## Non-Goals

- creating a new server
- replacing `/studio/audits/`
- replacing `/studio/activity/`
- replacing app inventories with generated dashboards
- exposing arbitrary command text, shell flags, environment variables, or filesystem paths to the browser
- building a generic local file browser
- running Lighthouse or broad browser profiles by default

## Relationship To Existing Routes

Existing routes remain:

- `/studio/audits/?mode=manage`: compact allowlisted audit launcher
- `/studio/activity/?mode=manage`: unified activity review

The proposed route adds:

- `/studio/risk/?mode=manage`: risk evidence production and report review

If implementation shows that `/studio/audits/` can naturally host the first version without becoming confusing, this request may start as an Audits-page extension.
The target product boundary remains a risk evidence surface, not a broad QA dashboard.

## Security Boundary

The browser may send:

- producer id
- app id
- area slug
- booleans for allowlisted optional producer groups such as runtime checks
- an optional user-facing note or run label

The browser must not send:

- command text
- shell flags
- arbitrary paths
- environment values
- unchecked artifact paths

The Python adapter resolves commands, working directories, output paths, and producer options server-side.

## Proposed API

All endpoints are hosted by the Local Studio app server.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/studio/api/risk/health` | risk API availability |
| `GET` | `/studio/api/risk/producers` | list allowlisted evidence producers and safe options |
| `GET` | `/studio/api/risk/runs` | list recent risk evidence runs with compact metadata |
| `POST` | `/studio/api/risk/runs` | start one allowlisted evidence run |
| `GET` | `/studio/api/risk/runs/<run-id>/summary` | read `summary.md` or `summary.json` for a completed run |
| `DELETE` | `/studio/api/risk/runs/<run-id>` | delete one local run snapshot directory |

The first implementation exposes this endpoint list in `studio/app/server/studio/studio_risk_api.py`.
The route UI uses it for producer discovery, validated dry runs and write runs, recent-run listing, summary reads, and local snapshot deletion.

## Proposed UI

The first version should be compact and operational:

- service status
- producer selector
- app selector
- area input
- safe option toggles
- Run button
- latest run status
- warnings/errors
- rendered summary
- links to safe artifacts when available

The page should not become a terminal-output viewer.
Raw logs may be available through a disclosure only when they are safe and useful for debugging.

## Output Contract

The route reads the run-directory contract defined in [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack):

- `manifest.json`
- `commands.json`
- `summary.md`
- `summary.json`
- producer-specific artifacts
- optional `artifacts/` details

The route should prefer `summary.json` for state and `summary.md` for readable report display.

## Activity Contract

A successful user-initiated write run should append one Studio Activity row.

The row should include:

- app
- area
- producer id
- run id
- summary path
- warning count
- failed producer count

Preview, dry-run, cancelled, and read-only summary views should not append activity rows.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Implement the command-line evidence pack runner from [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack). The runner can write a useful `summary.md` and `summary.json`. |
| 2 | done | Add a Local Studio risk API adapter with allowlisted producer listing, run creation, recent-run listing, and summary read behavior. Keep command and path resolution server-owned. |
| 3 | done | Add the `/studio/risk/?mode=manage` route registry entry, shell module, route controller, UI text, and Studio home/admin navigation link. |
| 4 | done | Render service state, producer controls, safe options, latest run status, and summary display. |
| 5 | done | Append unified Studio Activity rows for user-initiated write runs that produce reports. |
| 6 | done | Add focused Python tests for the risk API adapter and module/browser smoke checks for the route ready state and run-summary flow. |
| 7 | done | Update [Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations), [Local Studio App](/docs/?scope=studio&doc=local-studio-app), and [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard) after implementation. |

## Acceptance Criteria

- Studio exposes a user-facing risk evidence route without a new server
- browser requests cannot choose arbitrary commands or paths
- risk reports are written under `var/studio/risk/runs/<run-id>/`
- generated summaries can be read and displayed from the route
- app inventories can cite the generated run summary
- Studio Activity records user-initiated written runs
