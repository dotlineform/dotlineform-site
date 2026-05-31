---
doc_id: site-request-risk-evidence-producers
title: Risk Evidence Producers Request
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Risk Evidence Producers Request

Status:

- in progress

## Summary

Complete the remaining Studio risk evidence producers without turning [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) into an implementation tracker.

The evidence-pack document should describe the current durable contract.
This request owns producer implementation tasks, deferred producer decisions, and child docs that specify how runtime/browser, route exposure, and producer-roadmap work should proceed.

## Goals

- keep the evidence-pack doc focused on current commands, artifacts, API behavior, and integration rules
- implement the missing `route-exposure.json` producer
- define checked-in browser target configuration before adding browser-target or Lighthouse execution
- replace the broad Lighthouse boolean with allowlisted target selection
- keep all producer execution behind Local Studio and command-line allowlists
- preserve run artifacts under `var/studio/risk/runs/<run-id>/`
- detect scripts and generated artifacts that lack an active runtime, report, build, test, or operator-workflow consumer

## Non-Goals

- allowing arbitrary browser-provided URLs, commands, paths, or environment values
- requiring Lighthouse for every risk run
- storing bulky browser traces, screenshots, or Lighthouse HTML reports in checked-in generated data
- replacing app inventories with generated reports
- creating a generic command runner

## Child Producer Specs

- [Studio Risk Evidence Producer Roadmap](/docs/?scope=studio&doc=studio-risk-evidence-producer-roadmap)
- [Studio Risk Runtime Browser Evidence](/docs/?scope=studio&doc=studio-risk-runtime-browser-evidence)
- [Studio Risk Route Exposure Evidence](/docs/?scope=studio&doc=studio-risk-route-exposure-evidence)

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Define the risk evidence run directory and artifact contract in [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack). |
| 2 | done | Implement `studio/checks/risk_evidence_pack.py` with dry-run and write modes. |
| 3 | done | Add static file metrics, import/export scan, static searches, generated payload scan, and git touch-count producers. |
| 4 | done | Wrap existing JavaScript inventory guardrail output as transition evidence. |
| 5 | in progress | Add optional runtime producer hooks for existing smokes, Playwright, and Lighthouse when a targeted question requires them. Existing smoke profiles are allowlisted through `studio/commands/run_checks.py`; Lighthouse remains deferred until a safe URL contract exists. |
| 6 | deferred | Define the compact `studio/data/generated/risk/` summary shape only if a Studio route needs to read current risk evidence. The first route reads summaries through the narrow Local Studio API, so no checked-in generated read model is needed yet. |
| 7 | done | Add a Local Studio risk route or extend Audits only after the command-line evidence pack is useful. The route work is tracked in [Studio Risk Route Request](/docs/?scope=studio&doc=site-request-studio-risk-route). |
| 8 | done | Migrate legacy inventory rerun instructions into evidence-pack producers, starting with Python/Ruby script-family metrics in `script-family-inventory.json`. |
| 9 | planned | Implement [Studio Risk Route Exposure Evidence](/docs/?scope=studio&doc=studio-risk-route-exposure-evidence) and write `route-exposure.json`. |
| 10 | planned | Implement the browser target contract from [Studio Risk Runtime Browser Evidence](/docs/?scope=studio&doc=studio-risk-runtime-browser-evidence). |
| 11 | deferred | Implement Lighthouse collection after the allowlisted target config and local runner dependency decision are complete. |
| 12 | planned | Expose checked-in browser target ids from the risk API before adding Studio route controls for target selection. |
| 13 | planned | Add summary support for route exposure warnings and browser target/Lighthouse results. |
| 14 | planned | Decide whether subjective notes need a Studio UI capture flow or should remain file-based JSONL. |
| 15 | planned | Add a script/generated-artifact purpose check that reports whether each candidate has an active workflow consumer. Ownership alone is not enough; speculative or duplicated generated outputs should be flagged for removal, producer cleanup, or contract redesign. |

## Acceptance Criteria

- [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) describes current implemented behavior, not the task backlog
- route exposure evidence is generated from checked-in source/config and summarized in run output
- runtime/browser evidence uses checked-in target ids, not arbitrary URLs
- Lighthouse has a stable local dependency/invocation decision before execution is enabled
- Local Studio risk UI exposes only backend-provided allowlisted options
- generated artifacts and scripts are assessed for active consumption, not only source ownership
