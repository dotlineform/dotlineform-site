---
doc_id: tasks-tracker-template
title: Tasks Tracker Template
added_date: "2026-06-04 20:26"
last_updated: 2026-07-15
ui_status: planned
parent_id: dev-home
---
# [Delivery Outcome] Task Tracker

Use this only when one bounded [delivery](/docs/?scope=studio&doc=roadmap) needs coordination across sessions or owners.

Do not create a tracker merely because a change spans several files. If the rows below produce independently useful outcomes or can be prioritised separately, the delivery is too large: put those outcomes on the owning roadmap and add separate delivery documents when they become ready.

Delivery: [link]

## Delivery Boundary

- **Complete outcome:** [repeat the delivery outcome in one sentence]
- **Durable documentation owner:** [one document]
- **Must remain working throughout:** [important current behavior]

## Tasks

Keep the list short. A child task note is exceptional and should exist only when a handoff needs context that cannot fit in the row.

| ID | status | action | proof |
| --- | --- | --- | --- |
| 1 | planned | [complete implementation step] | [focused check or observable result] |

Allowed statuses: `planned`, `in progress`, `done`, `deferred`.

A deferred row must not be required for the delivery outcome. If it is required, the delivery is not complete.

## Closeout

- verify the complete delivery outcome, not only individual rows
- remove temporary, compatibility, or superseded paths introduced during delivery
- update the named durable owner and only other docs whose own contract or navigation changed
- record the focused verification result
- move new independently finishable work to the roadmap
- close this tracker with the delivery; do not keep it as permanent architecture history
