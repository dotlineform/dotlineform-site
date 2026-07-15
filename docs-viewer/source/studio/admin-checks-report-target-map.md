---
doc_id: admin-checks-report-target-map
title: Target Map Report
added_date: 2026-06-10
last_updated: 2026-07-15
parent_id: admin-checks-reports
viewable: true
---
# Target Map Report

## Questions

For the selected checks target:

- which files are unclassified or match several boundaries;
- which files are explicit shared dependencies;
- which route/area mappings may be missing;
- which configured patterns are stale or unexpectedly broad?

Report ID `target-map` is produced by `admin-app/checks/reports/target_map.py`.

## Method

The producer reads the validated run manifest and calls the shared target-map resolver. It does not own path matching or config policy.

The result contains selected file classifications, family/area/route counts, shared dependencies, review flags, and pattern status. `limit` and `pattern_limit` control only the focused Markdown presentation; complete evidence remains in JSON.

## Outputs

```text
var/admin/checks/<run-id>/target-map/
  report.json
  report.md
```

Markdown uses compact summaries and narrow text blocks to answer the review questions. It should not reproduce every field or every selected file.

## Interpretation

The report is evidence, not a failure policy:

- multi-family or cross-route files may be legitimate infrastructure;
- `_unclassified` means missing family mapping, not necessarily misplaced code;
- a stale pattern usually means config maintenance is needed;
- a broad pattern may be intentional but deserves ownership review;
- likely-unmapped hints require code/context inspection before config change.

Use [Target Map Architecture](/docs/?scope=studio&doc=admin-checks-target-map-architecture) to distinguish this selected report from the whole-config maintenance audit.
