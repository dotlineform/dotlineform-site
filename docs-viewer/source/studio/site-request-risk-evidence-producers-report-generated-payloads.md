---
doc_id: site-request-risk-evidence-producers-report-generated-payloads
title: Generated Payloads Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Generated Payloads Report

This document describes a possible future report for [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

## Summary

Report id: `generated-payloads`

Source prior art: retired legacy risk evidence pack `collect_generated_payloads` producer.

Purpose: inventory generated JSON payload size, count, and shape evidence for selected target surfaces.

Likely metrics:

- payload file count and total bytes
- counts and bytes grouped by generated root
- largest payloads
- JSON validity, top-level type, top-level keys, and array item counts

Likely target layers:

- scope
- area
- route where generated payload roots clearly support one route

Verification needs:

- fixture generated roots with valid and invalid JSON
- bounded largest-payload ordering tests
- safe generated-root allowlist validation

Non-goals:

- no rebuild of generated payloads
- no schema migration or cleanup
