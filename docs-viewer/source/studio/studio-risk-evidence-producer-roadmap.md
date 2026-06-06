---
doc_id: studio-risk-evidence-producer-roadmap
title: Studio Risk Evidence Producer Roadmap
added_date: 2026-05-31
last_updated: 2026-06-03
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Studio Risk Evidence Producer Roadmap

This document tracks implementation status for evidence producers named by [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) and [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

## Producer Status

| Producer | Status | Detail owner | Notes |
| --- | --- | --- | --- |
| JavaScript inventory guardrail | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Wraps `admin-app/checks/javascript_inventory_guardrail.py --json`. |
| Check profiles | implemented | [Studio Risk Runtime Browser Evidence](/docs/?scope=studio&doc=studio-risk-runtime-browser-evidence) | Existing run-check profiles are allowlisted through `--runtime-profile`. |
| Static file metrics | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Counts files, lines, bytes, and family totals. |
| Import/export scan | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Included inside `static-metrics.json`. |
| Static searches | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Uses configured regex patterns over selected app roots, including maintenance fixtures for negative-test assertion inventory and Data Sharing generated-docs stale-path inventory. |
| Generated payload scan | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Counts generated JSON payloads and basic shape. |
| Script family inventory | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Writes `script-family-inventory.json`. |
| Git touch counts | implemented | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Uses recent git history over selected app roots. |
| Runtime/browser checks | partial | [Studio Risk Runtime Browser Evidence](/docs/?scope=studio&doc=studio-risk-runtime-browser-evidence) | Run-check profiles work; direct browser target and Lighthouse collection are planned. |
| Lighthouse | deferred | [Studio Risk Runtime Browser Evidence](/docs/?scope=studio&doc=studio-risk-runtime-browser-evidence) | Needs allowlisted target config and local runner dependency decision. |
| Route exposure | planned | [Studio Risk Route Exposure Evidence](/docs/?scope=studio&doc=studio-risk-route-exposure-evidence) | Artifact is in the contract but currently omitted by the runner. |
| Script/generated artifact purpose | planned | [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers) | Should classify whether scripts and generated outputs are consumed by active workflows, not merely owned. |
| Config consumer/visibility evidence | planned | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Should classify config keys and projected payload fields by active consumer, browser-visible/server-only boundary, whitelist status, and likely keep/move/remove action. |
| Subjective notes | manual | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | JSONL copy/validation exists; review workflow can be improved later. |
| Compact generated risk summary | deferred | [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) | Not needed while Studio risk route reads run summaries through the API. |

## Near-Term Backlog

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Add checked-in browser target config and expose target listing from the risk API. |
| 2 | planned | Replace the broad `--include-lighthouse` UI/CLI model with allowlisted Lighthouse target selection. |
| 3 | planned | Implement route exposure producer and write `route-exposure.json`. |
| 4 | planned | Add summary support for route exposure warnings and browser target/Lighthouse results. |
| 5 | planned | Decide whether subjective notes need a Studio UI capture flow or should remain file-based JSONL. |
| 6 | planned | Add purpose/consumer evidence for scripts and generated artifacts so unused speculative outputs are visible before they become accepted contracts. |
| 7 | planned | Add config consumer/visibility evidence for app config, UI-text config, generated-default config, browser runtime config, and public config endpoint projections. |
| 8 | deferred | Define compact generated risk summary only if the risk route needs a stable generated read model. |

## Implementation Order

Recommended order:

1. Route exposure schema and producer.
2. Browser target config shared by route exposure and runtime/browser evidence.
3. Runtime browser target checks using Playwright for console, request, and readiness summaries.
4. Lighthouse target execution after the dependency and URL contracts are stable.
5. Script/generated artifact purpose checks that distinguish active workflow consumers from ownership-only artifacts.
6. Config consumer/visibility checks that distinguish active browser-visible fields, server-only contracts, whitelisted projections, and unconsumed keys.
7. Optional compact generated summary if the Studio route needs current-state reads beyond recent run summaries.
