---
doc_id: site-request-report-static-searches
title: Static Searches Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Static Searches Report

This document describes a possible future report for [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Summary

Report id: `static-searches`

Source prior art: retired legacy risk evidence pack `collect_static_searches` producer.

Purpose: run allowlisted text-pattern inventories for selected checks targets and report matched files as evidence for maintenance review.

Likely metrics:

- matched pattern count
- matched file count
- matches grouped by pattern id and target scope
- bounded sample paths and line snippets

Likely target layers:

- scope
- family
- area
- route

Verification needs:

- focused fixtures for pattern matching, exclusion rules, and sample limits
- safe-path tests proving report options cannot inject arbitrary search roots or patterns

Non-goals:

- no browser-provided regexes
- no automatic risk judgment from a text match
