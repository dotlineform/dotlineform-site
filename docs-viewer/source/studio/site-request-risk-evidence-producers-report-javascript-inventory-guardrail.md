---
doc_id: site-request-risk-evidence-producers-report-javascript-inventory-guardrail
title: JavaScript Inventory Guardrail Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# JavaScript Inventory Guardrail Report

This document describes a possible future report for [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

## Summary

Report id: `javascript-inventory-guardrail`

Source prior art: `admin-app/checks/javascript_inventory_guardrail.py` and the legacy risk evidence adapter.

Purpose: keep JavaScript inventory consistency and concentration evidence available as a normal checks report if the guardrail remains useful after v1 closeout.

Likely metrics:

- inventoried JavaScript file count
- files by maintenance score or category
- high-concentration route or family findings
- recent touch counts when the guardrail has git evidence

Likely target layers:

- scope
- family
- route

Verification needs:

- focused fixtures for inventory parsing and scoring buckets
- command invocation tests that use explicit argv lists and bounded output artifacts

Non-goals:

- no compatibility alias for the legacy risk artifact path
- no new scoring model in the migration request
