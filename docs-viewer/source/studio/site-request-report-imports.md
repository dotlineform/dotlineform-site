---
doc_id: site-request-report-imports
title: Imports Report
added_date: 2026-06-09
last_updated: 2026-06-09
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Imports Report

This document describes a possible future report for [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Purpose

The `imports` report would provide dependency-reference evidence for files selected by a checks run.

It should answer questions such as:

- which selected files import or reference other local modules
- which selected files are imported by other files
- where cross-scope or cross-layer references appear
- which dependency references should appear in a file-profile summary

## Inputs

- selected scope, family, area, and route filters from the run manifest
- selected files resolved through `target_map_resolver.py`
- language-specific parser or scanner rules for JavaScript, Python, Ruby, and relevant config files

Possible options:

| Option | Purpose |
| --- | --- |
| `include_reverse_refs` | Include files outside the selected set that reference selected files. |
| `include_external_packages` | Include package imports, not only repo-local references. |

## Output

Artifacts:

```text
var/admin/checks/<run-id>/imports/
  report.json
  report.md
  report.csv
```

Likely JSON and CSV fields:

- `path`
- `language`
- `imports[]`
- `local_imports[]`
- `external_imports[]`
- `reverse_refs[]`
- `unresolved_refs[]`
- `cross_scope_refs[]`

The stable join key for file-level consumers should be repo-relative `path`.

## Calculation Method

The first implementation should prefer structured parsers where practical and conservative regex extraction where parser support is not yet worth the cost.

Likely source forms:

- Python `import` and `from ... import ...`
- JavaScript `import`, `export ... from`, and dynamic import strings
- Ruby `require` and `require_relative`
- local JSON/config references where they are part of route or module wiring

The report should resolve references to repo-relative paths when possible and leave unresolved references visible as evidence rather than hiding them.

## Dependency Use

`file-profile` or other compound reports could depend on `imports` to show local dependencies, reverse references, and cross-boundary references for one selected file.

The `imports` report should remain independent and reusable.
It should not know about the file-profile report.

## Non-Goals

- no complete language-server implementation
- no bundler-specific graph unless a later request requires it
- no automatic risk judgment from a dependency edge
- no browser-provided parser rules or arbitrary scan patterns
