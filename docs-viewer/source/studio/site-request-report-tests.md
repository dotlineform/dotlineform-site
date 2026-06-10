---
doc_id: site-request-report-tests
title: Tests Report
added_date: 2026-06-09
last_updated: 2026-06-09
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Tests Report

This document describes a possible future report for [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Purpose

The `tests` report would provide evidence about test and smoke coverage links for files selected by a checks run.

Primary review question:

```text
Which selected files have no discovered test or smoke-check link?
```

Secondary evidence:

- which selected files have obvious related tests or smoke checks
- which test files target a selected route, area, or service
- which test or smoke commands are relevant to a file-profile summary

This report should describe evidence links.
It should not claim full code coverage unless a later coverage tool is explicitly integrated.

## Inputs

- selected scope, family, area, and route filters from the run manifest
- selected files resolved through `target_map_resolver.py`
- configured test roots and smoke-test roots
- optional report options for matching strictness

Possible options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `20` | Maximum files shown per Markdown section. |
| `include_smokes` | `true` | Include Playwright or route smoke checks. |
| `include_unit_tests` | `true` | Include Python or app-local unit tests. |
| `match_mode` | `conservative` | Select conservative filename matching or broader reference scanning. |

## Output

Artifacts:

```text
var/admin/checks/<run-id>/tests/
  report.json
  report.md
  report.csv
```

Required JSON fields:

- `path`
- `related_tests[]`
- `related_smokes[]`
- `matched_by[]`
- `test_count`
- `smoke_count`
- `has_related_test`
- `has_related_smoke`
- `has_any_discovered_link`
- `unlinked_reason`

The stable join key for file-level consumers should be repo-relative `path`.

Required per-link fields:

- `path`
- `kind`
- `match_kind`
- `confidence`

`match_kind` should be one of:

- `configured-target`
- `filename-token`
- `path-reference`
- `route-reference`
- `area-reference`

## Markdown Shape

The Markdown should prioritize missing evidence and keep linked evidence brief.

Sections:

- summary counts
- selected files with no discovered test or smoke link
- selected files with smoke links only
- selected files with the most discovered links

Example:

```text
No discovered test link
File                              Family        Area
--------------------------------  ------------  ----------------
docs-viewer-management.js         runtime-js    management
```

## Calculation Method

The first implementation should combine deterministic config links with conservative discovery:

1. Resolve the selected file set.
2. Read test and smoke roots from config or report options.
3. Link files to tests by configured route or area relationships where available.
4. Link files to tests by filename tokens and explicit path references.
5. Record unmatched selected files as visible evidence.

The report should avoid broad claims.
`has_related_test: false` means no configured or discovered test link was found, not that the file is definitely untested.

## Verification

Focused tests should cover:

- configured route or area test links
- filename-token matches
- explicit path-reference matches
- unmatched selected files
- smoke-only links
- `match_mode` validation
- Markdown output with no wide Markdown tables

## Dependency Use

`file-profile` or other compound reports could depend on `tests` to show likely test and smoke coverage links for one selected file.

The `tests` report should remain independent and reusable.
It should not know about the file-profile report.

## Non-Goals

- no statement coverage in the first version
- no mutation testing
- no automatic pass/fail test execution
- no claim that discovered links prove behavioral coverage
- no browser-provided test command execution
