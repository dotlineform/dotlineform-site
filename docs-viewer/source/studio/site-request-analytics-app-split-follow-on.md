---
doc_id: site-request-analytics-app-split-follow-on
title: Follow on work
added_date: "2026-05-30 17:24"
last_updated: "2026-05-30 17:24"
ui_status: in-progress
parent_id: site-request-analytics-app-split
---
# Follow on work

This sets out the work required following completion of [Analytics App Split Request](/docs/?scope=studio&doc=site-request-analytics-app-split).

This was a 'lift and shift' of analytics out of studio, so it left gaps which prevent Analytics being a self-contained module.

- Analytics needs access to Studio owned catalogue data for tags, but it should access this data using it's own helpers, not Studios.
- Data Sharing currently touches documents and tags. Analytics should own the workflow for Data Sharing, but Docs Viewer can remain the focused owner for document conversion/source helpers.

The purpose of this split was not just to simplify Studio, it was to move towards Analytics becoming a self-contained app. This follows the direction being taken with Docs Viewer.

These tasks now need implementing:

## Tasks

- Analytics still intentionally preserves `tagStudio*` frontend class/function naming from the lift-and-shift. This needs to be changed to e.g. `analytics*`.
- Canonical tag source data remains under `studio/data/canonical/analytics/...` - it needs to be moved to `analytics/...`.
- Data Sharing artifacts remain under `var/studio/data-sharing/...` - they need to be moved to `var/analytics/...`.
- Analytics still uses focused helper modules under `studio/services/analytics/`; those helpers are domain services, not Studio route/API ownership. Analytics needs to be decoupled from relying on Studio helpers.
- The JavaScript inventory now records the post-split app boundaries, but a full rescored inventory refresh remains future maintenance work.