---
doc_id: series-tags
title: Series Tags
added_date: 2026-03-31
last_updated: 2026-07-15
parent_id: analytics
---
# Series Tags

## Capability

`/analytics/series-tags/` is the cross-series assignment review. It shows coverage/status, links into the one-series editor, and manages the structured offline assignment session.

The page does not directly edit table rows. Editing happens in [Tag Editor](/docs/?scope=studio&doc=tag-editor); this route aggregates staged changes and reconciles them with canonical assignments.

## Data Path

```text
public series index
  + canonical assignments
  + registry/group config
  + browser offline session
  -> coverage/status table
  -> selected series editor link
```

Coverage scoring is implemented by `analysis-tag-scoring.js` using `analysis.groups` and `analysis.rag` from Analytics config.

## Offline Session Workflow

1. Tag Editor stages changed series/work rows in browser storage when direct save is unavailable or a staged series already exists.
2. Series Tags reads that versioned session and can copy/download or clear it.
3. Import sends the session file to the server for preview against the original base snapshot and current canonical row.
4. Missing/invalid series are skipped; changed canonical rows become explicit conflicts.
5. The user chooses overwrite or skip per conflict, then applies.
6. Successfully reconciled local entries are cleared only if the staged row still matches the imported file.

This is optimistic reconciliation, not background sync. The preview/apply service is authoritative.

## Code Map

- template/controller: `series-tags.html`, `series-tags.js`
- report/table: `series-tags-render.js`, `analysis-tag-scoring.js`
- session format/storage: `tag-assignments-offline.js`, `tag-assignments-offline-session.js`
- import UI/service: `series-tags-import-workflow.js`, `series-tags-modals.js`
- server preview/apply: `tag_assignment_service.py`, `tag_write_api/assignments.py`

The route uses Analytics ready/busy state; preview/apply are busy commands and session/import modal state is reflected in route mode.

## Weak Spots

- Browser storage is machine/profile-local and deliberately not canonical.
- Offline changes and direct server changes can overlap, requiring user conflict resolution.
- Coverage status combines canonical assignment data with generated catalogue indexes; either side can be stale.
- The export/import session format is a real contract and should change only with versioned normalization and tests.
