---
doc_id: site-request-risk-evidence-producers-report-runtime-checks
title: Runtime Checks Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Runtime Checks Report

This document describes a possible future report for [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

## Summary

Report id: `runtime-checks`

Source prior art: `admin-app/checks/risk_evidence_pack.py` `collect_runtime_checks` and `admin-app/commands/run_checks.py`.

Purpose: link selected checks targets to allowlisted runtime profile results without letting the browser submit arbitrary commands.

Likely metrics:

- requested profile ids
- profile exit codes
- run-check summary paths
- deferred or omitted runtime evidence reasons

Likely target layers:

- scope
- route where a profile maps to a route smoke

Verification needs:

- allowlist validation for profile ids
- fixture command runner tests for passed, failed, and deferred profiles
- safe summary-path reporting

Non-goals:

- no arbitrary command execution
- no Lighthouse or browser automation until a URL/server contract is specified
