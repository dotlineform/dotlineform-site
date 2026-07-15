---
doc_id: admin-checks-code-surface-delivery
title: Code Surface Report
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: admin-checks-responsibility-reports
viewable: true
---
# Code Surface Report

This document describes a possible future report for [Admin Checks Responsibility Reports](/docs/?scope=studio&doc=admin-checks-responsibility-reports).

## Summary

Report id: `code-surface`

Purpose: measure how much callable or importable surface selected source files expose.

Primary review question:

```text
Which selected files expose unusually broad public or top-level code surfaces?
```

This report is intended to catch files that are becoming broad owner modules even when they do not yet look suspicious by size, target-map ownership, or import boundaries.

## Inputs

- selected scope, family, area, and route filters from the run manifest
- selected files resolved through `target_map_resolver.py`
- parser or conservative scanner support for Python, JavaScript, CSS, and JSON where useful

Possible options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `20` | Maximum files shown per Markdown section. |
| `include_private` | `false` | Include private/internal symbols in JSON counts. |
| `language_detail` | `true` | Keep language-specific detail fields in `report.json`. |

## Output

Artifacts:

```text
var/admin/checks/<run-id>/code-surface/
  report.json
  report.md
  report.csv
```

Required JSON fields:

- `path`
- `language`
- `export_count`
- `top_level_function_count`
- `top_level_class_count`
- `top_level_constant_count`
- `handler_count`
- `route_or_endpoint_count`
- `public_method_count`
- `symbol_count`
- `surface_flags[]`

The stable join key for file-level consumers should be repo-relative `path`.

Required per-symbol fields:

- `name`
- `kind`
- `visibility`
- `line`
- `exported`

`surface_flags[]` should use small evidence labels such as:

- `many-exports`
- `many-top-level-functions`
- `many-handlers`
- `many-routes-or-endpoints`
- `many-public-methods`
- `large-public-surface`

## Markdown Shape

The Markdown should show a small ranked review list, not every symbol.

Sections:

- summary counts
- files with many exports
- files with many top-level functions or classes
- files with many handlers, routes, or endpoints

Example:

```text
Broad code surfaces
File                              Exports  Symbols  Flags
--------------------------------  -------  -------  ----------------------
docs-viewer-management.js              18       64  many-exports,handlers
```

## Calculation Method

The first implementation should prefer built-in parsers where practical:

- Python: `ast` for functions, classes, methods, constants, and route-like decorators
- JavaScript: conservative scanner for `export`, top-level `function`, top-level `class`, and assigned handler functions
- CSS: custom property and selector counts only if useful for surface review
- JSON: top-level key counts only when config files are selected

The report should not attempt complete semantic analysis.
It should count visible surface evidence consistently and leave interpretation to a later dependency report.

## Verification

Focused tests should cover:

- Python exported functions, classes, methods, and route-like decorators
- JavaScript named exports, default exports, functions, classes, and handler-like assignments
- private/internal symbol exclusion
- CSV row shape
- Markdown output with no wide Markdown tables
- option validation through `admin-checks-reports.json`

## Dependency Use

`mixed-responsibility` could depend on `code-surface` to detect files that expose broad behavior even when they remain inside one configured target.

`file-profile` could depend on `code-surface` to summarize a selected file's public and top-level symbols.

The `code-surface` report should remain independent and reusable.
It should not know about those dependent reports.

## Non-Goals

- no full language-server implementation
- no call graph construction
- no statement-level complexity metrics in v1
- no automatic risk score
- no scan of Markdown documents
