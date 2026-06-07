---
doc_id: site-request-risk-evidence-producers
title: Risk Evidence Producers Request
added_date: 2026-05-31
last_updated: 2026-06-07
ui_status: draft
parent_id: change-requests
viewable: true
---
# Risk Evidence Producers Request

Status:

- draft

## Summary

Complete the remaining Studio risk evidence producers for inclusion in [Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack).

## Goals

- keep the evidence-pack doc focused on current commands, artifacts, API behavior, and integration rules
- keep all producer execution behind Local Studio and command-line allowlists
- preserve run artifacts under `var/studio/risk/runs/<run-id>/`
- detect scripts and generated artifacts that lack an active runtime, report, build, test, or operator-workflow consumer

## Acceptance Criteria

- generated artifacts and scripts are assessed for active consumption, not only source ownership