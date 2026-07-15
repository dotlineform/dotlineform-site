---
doc_id: admin-checks-static-searches-delivery
title: Static Searches Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: admin-checks-responsibility-reports
viewable: true
---
# Static Searches Report

This document describes a possible future report for [Admin Checks Responsibility Reports](/docs/?scope=studio&doc=admin-checks-responsibility-reports).

## Summary

Report id: `static-searches`

Purpose: run allowlisted text-pattern inventories for selected checks targets and report matched files as evidence for maintenance review.

Primary review question:

```text
Which selected files contain configured tokens that suggest mixed responsibilities or boundary-sensitive behavior?
```

## Inputs

- selected scope, family, area, and route filters from the run manifest
- selected files resolved through `target_map_resolver.py`
- allowlisted pattern groups from checks config

Possible options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `20` | Maximum files shown per Markdown section. |
| `sample_limit` | `3` | Maximum line samples kept per file per pattern. |
| `pattern_groups` | configured default | Allowlisted groups to run, such as `workflow_tokens`, `boundary_tokens`, or `responsibility_tokens`. |

## Output

Artifacts:

```text
var/admin/checks/<run-id>/static-searches/
  report.json
  report.md
  report.csv
```

Required JSON fields:

- matched pattern count
- matched file count
- matches grouped by pattern id and target scope
- bounded sample paths and line snippets
- per-file `match_count`
- per-file `matched_pattern_ids[]`
- per-pattern `file_count`

The stable join key for file-level consumers should be repo-relative `path`.

Required per-pattern fields:

- `pattern_id`
- `group_id`
- `label`
- `description`
- `severity_hint`
- `literal` or `regex`
- `file_count`
- `match_count`

## Markdown Shape

The Markdown should show which configured searches produced evidence, not dump every match.

Sections:

- summary counts
- files matching the most configured patterns
- pattern groups with the most matched files
- bounded line samples for high-signal patterns

Example:

```text
Files matching configured tokens
File                              Patterns  Groups
--------------------------------  --------  ----------------
docs-viewer-management.js                6  workflow,boundary
```

Likely target layers:

- scope
- family
- area
- route

## Calculation Method

The report should only run allowlisted patterns from config.
The browser must not provide search roots, shell commands, or regex source.
The producer should scan selected source files directly in Python and apply the same source-file exclusions used by target-map.

Pattern groups should start small and explicit, for example:

- `workflow_tokens`: route, modal, import, export, save, delete, build
- `boundary_tokens`: fetch, endpoint, localStorage, generated, source, mutate
- `responsibility_tokens`: render, modal, save, delete, import, export, build, route, fetch, storage, mutation, validate
- `ownership_tokens`: catalogue, docs, analytics, studio, public

These tokens are evidence only.
A match means the file contains review vocabulary, not that the file is wrong.

## Verification

- focused fixtures for pattern matching, exclusion rules, and sample limits
- safe-path tests proving report options cannot inject arbitrary search roots or patterns
- Markdown output with no wide Markdown tables
- config validation for unknown `pattern_groups`

## Non-Goals

- no browser-provided regexes
- no automatic risk judgment from a text match
- no semantic code parsing in v1
- no scan of Markdown documents
