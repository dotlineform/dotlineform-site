---
doc_id: site-request-risk-evidence-producers-report-script-family-inventory
title: Script Family Inventory Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Script Family Inventory Report

This document describes a possible future report for [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

## Summary

Report id: `script-family-inventory`

Source prior art: `admin-app/checks/risk_evidence_pack.py` `collect_script_family_inventory`.

Purpose: summarize Python and Ruby script concentration by active family roots.

Likely metrics:

- Python and Ruby file counts
- total lines by family
- largest file per family
- largest included script files

Likely target layers:

- scope
- family

Verification needs:

- fixture roots for Python, Ruby, tests, smokes, and cache exclusions
- deterministic largest-file ordering tests

Non-goals:

- no return to old ad hoc terminal rerun blocks
- no inclusion of test and smoke files unless a later request changes the scope
