---
doc_id: admin-checks-reports
title: Reports
added_date: 2026-06-09
last_updated: 2026-06-10
parent_id: admin-checks
---
# Admin Checks Reports

This section describes the reports that surface admin checks metrics through the route `/admin/checks/`.

Implemented reports:

| Report | Status | Durable doc |
| --- | --- | --- |
| `files` | implemented | [Files Report](/docs/?scope=studio&doc=admin-checks-report-files) |
| `target-map` | implemented | [Target Map Report](/docs/?scope=studio&doc=admin-checks-report-target-map) |

## Markdown Report Design

Admin Checks reports can capture broad evidence, but the Markdown artifact should stay focused on immediate review.
Use `report.json` for complete structured data and `report.csv` when a report needs full-field spreadsheet review.

Markdown reports should:

- answer a small set of named review questions
- avoid Markdown tables by default
- use fenced `text` blocks with space-padded columns when alignment helps
- prefer short identifiers, such as filenames, when scoped paths repeat the same prefix
- limit wide record lists and point to `report.json` or `report.csv` for complete data
- include only the fields needed to answer the section's question

Markdown tables are acceptable only when the table is narrow and purposeful.
As a rule of thumb, keep them to three columns, or four when the extra columns are short consistent values like counts or sizes.
If a section needs more columns than that, redesign the section around the question it is answering or move the detail to JSON/CSV.
