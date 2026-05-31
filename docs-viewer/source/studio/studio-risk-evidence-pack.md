---
doc_id: studio-risk-evidence-pack
title: Studio Risk Evidence Pack
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: studio-risk-operations
viewable: true
---
# Studio Risk Evidence Pack

This document defines the target artifact contract for producing app risk inventories.

The goal is that every deterministic bullet in [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy) can point to:

- a repeatable command or script
- a machine-readable artifact
- a human-readable summary
- a stable place where the output is saved
- the app inventory or change request that used the evidence

## Current Status

Status: target contract.

The current repo already has some evidence producers, such as `studio/checks/javascript_inventory_guardrail.py`, `studio/commands/run_checks.py`, app smokes, builder diagnostics, and generated payload indexes.
The next implementation step is to collect those existing producers behind a consistent risk evidence run.

## Output Location

Default ignored output root:

```text
var/studio/risk/
```

Each run should write to:

```text
var/studio/risk/runs/<run-id>/
```

Recommended run id:

```text
YYYYMMDD-HHMMSS-<slug>
```

Example:

```text
var/studio/risk/runs/20260531-143000-docs-viewer-runtime/
```

If Studio needs to read a compact current summary, write a generated read model to:

```text
studio/data/generated/risk/
```

Do not put bulky logs, screenshots, traces, or profiler exports under `studio/data/generated/risk/`.
Those belong in the ignored run directory.

## Run Directory Contract

Each run directory should contain:

| Artifact | Purpose |
| --- | --- |
| `manifest.json` | Run id, app, area, command version, repo commit, timestamp, operator, and selected evidence producers. |
| `commands.json` | Exact command lines, working directories, environment flags that are safe to record, exit codes, and elapsed times. |
| `summary.md` | Human-readable summary suitable for linking from an app inventory or change request. |
| `summary.json` | Machine-readable summary grouped by app, area, indicator, evidence source, and close-out relevance. |
| `static-metrics.json` | File counts, line counts, import/export counts, dependency direction, and grouped ownership metrics. |
| `static-searches.json` | Repeatable search patterns, matched paths, counts, and excerpts where useful. |
| `route-exposure.json` | Public/local/runtime route exposure, app ownership, loaded script/config surfaces, and retired-path findings. |
| `generated-payloads.json` | Generated payload counts, sizes, schema versions, index counts, changed/removed records, and relevant builder diagnostics. |
| `git-history.json` | Recent touch counts grouped by app, area, file family, and file. |
| `runtime-checks.json` | Node, Python, Ruby/Jekyll, pytest, smoke, Playwright, Lighthouse, or browser-devtools-derived results used by the run. |
| `subjective-notes.jsonl` | User feedback, reviewer notes, confidence, affected app/area, and proposed follow-up. |
| `artifacts/` | Optional detailed logs, screenshots, traces, Lighthouse reports, profiler exports, or raw command outputs. |

Only create an artifact when that evidence type was actually collected.
The manifest should list omitted evidence types so absence is explicit.

## Evidence Producers

The first risk evidence runner should wrap existing producers before adding new analysis.

Initial producers:

| Producer | Command source | Output |
| --- | --- | --- |
| JavaScript inventory guardrail | `studio/checks/javascript_inventory_guardrail.py --json` | Legacy JavaScript inventory consistency and concentration metrics. |
| Check profiles | `studio/commands/run_checks.py --profile <profile>` | Existing check summaries and logs under `var/test-runs/`; copy or link the relevant summary into the risk run. |
| Static file metrics | new risk runner helper | File counts, line counts, and grouped totals by app and file family. |
| Import/export scan | new risk runner helper | Dependency direction and cross-app coupling evidence. |
| Static searches | new risk runner helper | Configurable `rg` patterns for stale paths, broad state, retired modules, endpoints, generated paths, and ownership smells. |
| Generated payload scan | new risk runner helper | Payload sizes, counts, schemas, index sizes, and changed/removed diagnostics where available. |
| Git touch counts | new risk runner helper | Recent edit concentration grouped by app, area, family, and file. |
| Runtime/browser checks | existing smoke scripts, Playwright, Lighthouse when targeted | Runtime evidence only when the risk question needs it. |
| Subjective notes | manually maintained JSONL or command option | User feedback and reviewer judgement as labelled non-deterministic evidence. |

## Command Shape

Target command:

```bash
$HOME/miniconda3/bin/python3 studio/checks/risk_evidence_pack.py --app docs-viewer --area runtime --write
```

Optional flags:

```text
--app <public-site|studio|analytics|docs-viewer|all>
--area <slug>
--run-id <id>
--include-runtime
--include-lighthouse
--include-subjective-notes <path>
--write
```

Dry-run behavior:

- without `--write`, print the planned producers and output paths
- with `--write`, create the run directory and write artifacts
- never mutate source files
- never run arbitrary browser-provided commands

## Inventory Integration

App inventories should cite evidence packs in the `Evidence` column when deterministic evidence is used.

Example:

```md
Evidence pack: `var/studio/risk/runs/20260531-143000-docs-viewer-runtime/summary.md`
```

If a compact current summary is exposed through Local Studio later, the inventory may link to the Studio route or generated read model as well.
The ignored run directory remains the source of detailed evidence.

## Activity Integration

Risk evidence runs initiated from a Studio UI should append a unified activity row when they write a run directory or generated summary.

The activity detail should include:

- app
- area
- run id
- evidence producers
- summary path
- warnings or failed producer count

Command-line Codex runs do not need to append activity unless they are invoked through the Local Studio API or a future Studio risk route.

## Non-Goals

- replacing app inventories with generated reports
- treating deterministic metrics as automatic priorities
- storing bulky local evidence in checked-in generated data
- creating a new server for risk evidence
- making a generic command runner

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Define the risk evidence run directory and artifact contract. |
| 2 | planned | Implement `studio/checks/risk_evidence_pack.py` with dry-run and write modes. |
| 3 | planned | Add static file metrics, import/export scan, static searches, generated payload scan, and git touch-count producers. |
| 4 | planned | Wrap existing JavaScript inventory guardrail output as transition evidence. |
| 5 | planned | Add optional runtime producer hooks for existing smokes, Playwright, and Lighthouse when a targeted question requires them. |
| 6 | planned | Define the compact `studio/data/generated/risk/` summary shape only if a Studio route needs to read current risk evidence. |
| 7 | planned | Add a Local Studio risk route or extend Audits only after the command-line evidence pack is useful. Track the route work in [Studio Risk Route Request](/docs/?scope=studio&doc=site-request-studio-risk-route). |
