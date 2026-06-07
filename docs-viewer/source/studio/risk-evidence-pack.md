---
doc_id: risk-evidence-pack
title: Risk Evidence Pack
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: admin
---
# Risk Evidence Pack

This document defines the artifact contract for producing app risk inventories.

The goal is that every deterministic bullet in [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy) can point to:

- a repeatable command or script
- a machine-readable artifact
- a human-readable summary
- a stable place where the output is saved

## Current Status

Status: command-line runner and local Admin route implemented.

The current repo already has some evidence producers, such as:

- `admin-app/checks/javascript_inventory_guardrail.py`
- `admin-app/commands/run_checks.py`
- app smokes
- builder diagnostics
- generated payload indexes.

Producer implementation backlog is tracked in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

## Admin App API

The Admin app server exposes a narrow risk API for:

- listing producers
- creating validated runs
- listing recent runs
- reading run summaries
- deleting local run snapshots
- appending Activity rows for user-initiated write runs.

The Admin adapter lives in `admin-app/app/server/admin_app/admin_risk_api.py`.
It exposes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/admin/api/risk/health` | risk API availability |
| `GET` | `/admin/api/risk/producers` | allowlisted evidence producers and safe options |
| `GET` | `/admin/api/risk/runs` | recent risk evidence runs with compact metadata |
| `POST` | `/admin/api/risk/runs` | start one validated evidence run through `admin-app/checks/risk_evidence_pack.py` |
| `GET` | `/admin/api/risk/runs/<run-id>/summary` | read `summary.md` and `summary.json` for a completed run |
| `DELETE` | `/admin/api/risk/runs/<run-id>` | delete one local run snapshot directory under `var/admin/risk/runs/` |

The browser may choose app id, area slug, run id, dry-run mode, and allowlisted runtime options.
The browser may not provide command text, shell flags, environment values, arbitrary paths, or subjective-notes file paths.
Snapshot deletion uses the same safe run-id validation as summary reads and only removes ignored local run artifacts.

## Admin Route Page

The Admin route at `/admin/risk/` provides the UI for dry runs, write runs, recent runs, snapshot deletion, and summary review.

## Runner

The first runner now collects:

- static metrics
- static search evidence
- generated payload evidence
- git touch counts
- the JavaScript inventory guardrail
- optional subjective notes,
- allowlisted runtime check profiles 

These are saved into a local run directory.

Target command:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/risk_evidence_pack.py --app docs-viewer --area runtime --write
```

Optional flags:

```text
--app <public-site|studio|admin|analytics|docs-viewer|all>
--area <slug>
--run-id <id>
--include-runtime
--include-lighthouse
--include-subjective-notes <path>
--runtime-profile <admin-smoke|studio-smoke|ui-catalogue-smoke|analytics-smoke|docs-viewer-smoke>
--write
```

Dry-run behavior:

- without `--write`, print the planned producers and output paths
- with `--write`, create the run directory and write artifacts
- never mutate source files
- never run arbitrary browser-provided commands

Runtime profiles are allowlisted and execute through `admin-app/commands/run_checks.py`.
`--include-lighthouse` is accepted as a deferred hook but does not run Lighthouse until a safe URL contract is defined.


## Run Directory

Default ignored output root:

```text
var/admin/risk/
```

Each run should write to:

```text
var/admin/risk/runs/<run-id>/
```

Recommended run id:

```text
YYYYMMDD-HHMMSS-<slug>
```

Example:

```text
var/admin/risk/runs/20260531-143000-docs-viewer-runtime/
```

Each run directory should contain:

| Artifact | Purpose |
| --- | --- |
| `manifest.json` | Run id, app, area, command version, repo commit, timestamp, operator, and selected evidence producers. |
| `commands.json` | Exact command lines, working directories, environment flags that are safe to record, exit codes, and elapsed times. |
| `summary.md` | Human-readable summary suitable for linking from an app inventory or change request. |
| `summary.json` | Machine-readable summary grouped by app, area, indicator, evidence source, and close-out relevance. |
| `static-metrics.json` | Source/config file counts, line counts, import/export counts, dependency direction, and grouped ownership metrics. Generated and canonical data payload roots are excluded so payload size does not distort source metrics. |
| `static-searches.json` | Repeatable search patterns, matched paths, counts, scoped fixture roots, and excerpts where useful. |
| `generated-payloads.json` | Generated payload counts, sizes, schema versions, index counts, changed/removed records, and relevant builder diagnostics. |
| `config-consumers.json` | Optional future artifact that lists config keys and payload fields, owner docs, active consumers, browser-visible/server-only classification, public-projection whitelist status, and likely action. |
| `script-family-inventory.json` | Python/Ruby script-family counts, line counts, family totals, and largest-file observations migrated from the legacy script inventory rerun block. |
| `git-history.json` | Recent touch counts grouped by app, area, file family, and file. |
| `runtime-checks.json` | Optional allowlisted runtime check profile results. |
| `subjective-notes.jsonl` | User feedback, reviewer notes, confidence, affected app/area, and proposed follow-up. |
| `artifacts/` | Optional detailed logs or raw command outputs created by producer implementations. |

Only create an artifact when that evidence type was actually collected.
The manifest should list omitted evidence types so absence is explicit.

## Activity Integration

Risk evidence runs initiated from Admin should append a unified activity row when they write a run directory or generated summary.

The activity detail should include:

- app
- area
- run id
- evidence producers
- summary path
- warnings or failed producer count

Command-line Codex runs do not need to append activity unless they are invoked through the Admin API.

## Inventory Integration

App inventories should cite evidence packs in the `Evidence` column when deterministic evidence is used.

Example:

```md
Evidence pack: `var/admin/risk/runs/20260531-143000-docs-viewer-runtime/summary.md`
```

If a compact current summary is exposed through Admin, the inventory may link to the Admin route as well.
The ignored run directory remains the source of detailed evidence.

## Producers

Current producers:

| Producer | Command source | Output |
| --- | --- | --- |
| JavaScript inventory guardrail | `admin-app/checks/javascript_inventory_guardrail.py --json` | Legacy JavaScript inventory consistency and concentration metrics. |
| Check profiles | `admin-app/commands/run_checks.py --profile <profile>` | Existing check summaries and logs under `var/admin/test-runs/`; summary paths are linked from `runtime-checks.json`. |
| Static file metrics | risk runner helper | Source/config file counts, line counts, bytes, and grouped totals by app and file family. Excludes generated and canonical data payload roots. |
| Import/export scan | risk runner helper | Dependency direction and cross-app coupling evidence inside `static-metrics.json`. |
| Static searches | risk runner helper | Configurable patterns for stale paths, broad state, retired modules, endpoints, generated paths, ownership smells, and code-maintenance fixtures such as `negative_test_assertion_inventory` and `data_sharing_generated_docs_stale_path_inventory`. |

Current static-search maintenance fixtures:

| Fixture | Scope | Purpose |
| --- | --- | --- |
| `negative_test_assertion_inventory` | `admin-app/tests/`, `analytics-app/tests/`, `docs-viewer/tests/`, `studio/tests/` | Inventory negative assertions and stale-behavior phrasing so permanent tests can be reviewed against the current-contract testing rule. |
| `data_sharing_generated_docs_stale_path_inventory` | Data Sharing document services, adapter config, and focused Data Sharing test/smoke fixtures | Inventory stale generated-docs metadata path terms such as retired docs indexes, generated by-id roots, and generated-docs source labels so ordinary tests can assert the current source-metadata contract instead. |
| Generated payload scan | risk runner helper | Generated JSON payload counts, sizes, and basic shape observations. |
| Script family inventory | risk runner helper | Persistent Python/Ruby family metrics that replace the ad hoc rerun commands from the legacy script inventory. |
| Git touch counts | risk runner helper | Recent edit concentration grouped by app, area, family, and file. |
| Subjective notes | manually maintained JSONL or command option | User feedback and reviewer judgement as labelled non-deterministic evidence. |

