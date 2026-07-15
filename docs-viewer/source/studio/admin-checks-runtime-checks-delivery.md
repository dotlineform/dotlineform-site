---
doc_id: admin-checks-runtime-checks-delivery
title: Runtime Checks Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: admin-checks-operational-reports
viewable: true
---
# Runtime Checks Report

This document describes a possible future report for [Admin Checks Operational Reports](/docs/?scope=studio&doc=admin-checks-operational-reports).

## Summary

Report id: `runtime-checks`

Purpose: link selected checks targets to allowlisted runtime profile results without letting the browser submit arbitrary commands.

Primary review question:

```text
Which selected targets have recent allowlisted runtime evidence, and which do not?
```

## Inputs

- selected scope, family, area, and route filters from the run manifest
- runtime profile mappings from checks config
- existing Admin test-run summaries where a profile has already run

Possible options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `20` | Maximum profile rows shown in Markdown. |
| `max_age_hours` | `24` | Freshness window for existing runtime evidence. |
| `profile_groups` | configured default | Allowlisted runtime profile groups to inspect. |

## Output

Artifacts:

```text
var/admin/checks/<run-id>/runtime-checks/
  report.json
  report.md
```

Required JSON fields:

- requested profile ids
- profile exit codes
- run-check summary paths
- deferred or omitted runtime evidence reasons
- profile freshness status
- target-to-profile mappings
- missing evidence count
- failed evidence count

Required per-profile fields:

- `profile_id`
- `target_type`
- `target_id`
- `status`
- `last_run_id`
- `last_finished_at`
- `age_hours`
- `summary_path`
- `omitted_reason`

## Markdown Shape

The Markdown should show runtime evidence gaps first.

Sections:

- summary counts
- selected targets without fresh runtime evidence
- failed runtime evidence
- fresh passed evidence

Example:

```text
Missing runtime evidence
Target                            Profile             Reason
--------------------------------  ------------------  ----------------
route./docs/                      docs-viewer-smoke   no recent run
```

Likely target layers:

- scope
- route where a profile maps to a route smoke

## Calculation Method

The first version should read existing test-run summaries rather than launching commands.
Launching allowlisted profiles can be a later mode only after the command and server lifecycle contract is explicit.
Profile mappings must come from config, not browser request payloads.

## Verification

- allowlist validation for profile ids
- fixture command runner tests for passed, failed, and deferred profiles
- safe summary-path reporting
- freshness-window tests
- Markdown output with no wide Markdown tables

## Non-Goals

- no arbitrary command execution
- no Lighthouse or browser automation until a URL/server contract is specified
- no automatic server start in v1
- no broad runtime risk score
