---
doc_id: activity
title: Activity
added_date: 2026-05-08
last_updated: 2026-07-15
parent_id: admin
viewable: true
---
# Activity

## What It Shows

`/admin/activity/` is the read-only feed of meaningful user-initiated local operations emitted by Studio, Admin, Analytics/Data Sharing, and Docs Viewer workflows.

Rows preserve three levels of context:

- the initiating page/surface;
- the user action;
- the script/service purpose and affected record groups.

Selecting a status marker opens the row's normalized detail items.

## Data Flow

```text
domain workflow
  -> shared activity context + emitter
  -> var/admin/activity/activity_log.jsonl (journal)
  -> var/admin/activity/activity_log.json (capped feed)
  -> /admin/api/activity/feed
  -> Admin Activity route
```

`studio/data/config/runtime/activity-contract.json` owns label/grouping policy. `studio/shared/python/studio_activity.py` owns shared paths and append mechanics. Domain services decide when an action is meaningful and provide their record groups/details.

## Boundary

Route loads, background watchers, and trivial local UI interactions should not create activity. User-triggered writes, publications, imports, reports, audits, and package operations are appropriate when the row helps explain a durable side effect.

Activity is an operational trace, not an event-sourcing or rollback system. Canonical data remains authoritative; missing or failed activity append must not make the source operation fictitiously incomplete.

## Weak Spots

- The shared helper still lives under `studio/shared/python/` although the feed is Admin-owned and used cross-app.
- Record-group vocabulary includes compatibility families that may outlive active UI capabilities.
- Labels come from checked config while emitters supply raw IDs/context, so contract verification is required when adding an action.

The route uses `#studioActivityRoot` with Admin-prefixed ready/busy state; the historical DOM name is not an ownership signal.
