---
doc_id: admin-checks-reports
title: Reports
added_date: 2026-06-09
last_updated: 2026-07-15
parent_id: admin-checks
viewable: true
---
# Admin Checks Reports

## Implemented

- `files` — file count, line count, byte size, and target-match context; writes JSON, focused Markdown, and CSV.
- `target-map` — classification, shared dependencies, boundary flags, and pattern status; writes JSON and focused Markdown.

The report registry in `admin-checks-reports.json` is the exact inventory.

## Output Rule

- JSON holds complete structured evidence.
- Markdown answers a small set of immediate review questions.
- CSV is used for full tabular review where useful.

Avoid wide exhaustive Markdown tables. If a report cannot state what decision its Markdown helps make, it is not ready to become an implemented report.

Conceptual report ideas and sequencing belong under [Admin Checks Responsibility Reports](/docs/?scope=studio&doc=admin-checks-responsibility-reports) until delivered.
