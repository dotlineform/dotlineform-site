---
doc_id: site-request-report-subjective-notes
title: Subjective Notes Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Subjective Notes Report

This document describes a possible future report for [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Summary

Report id: `subjective-notes`

Source prior art: legacy risk evidence optional JSONL note copying.

Purpose: attach manually written review observations to a checks run without mixing judgement into measured report artifacts.

Likely metrics:

- note count
- invalid JSONL line count
- notes grouped by scope, route, or file when fields are present

Likely target layers:

- scope
- family, area, route, or file path when supplied in each note

Verification needs:

- JSONL parsing fixtures for valid and invalid lines
- safe-path validation for local note source files
- markdown escaping for note text

Non-goals:

- no browser-provided file paths outside an allowlisted local notes area
- no replacing structured evidence reports with manual judgement
