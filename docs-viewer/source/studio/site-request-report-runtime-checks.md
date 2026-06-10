---
doc_id: site-request-report-runtime-checks
title: Runtime Checks Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Runtime Checks Report

This document describes a possible future report for [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Summary

Report id: `runtime-checks`

Source prior art: retired legacy risk evidence pack `collect_runtime_checks` producer and `admin-app/commands/run_checks.py`.

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
