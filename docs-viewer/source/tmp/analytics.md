---
doc_id: analytics
title: "analytics"
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: draft
parent_id: ""
---

Keep the preserved `var/studio/data-sharing/...` artifact paths for now; those are data artifact path contracts, not active Studio routes.

Because those paths are workflow artifact storage contracts, not active Studio routes.

They appear in Data Sharing adapter config and tests as locations for exports, import staging, previews, and backups, for example:

`var/studio/data-sharing/library/exports`
`var/studio/data-sharing/tags/import-staging`
`var/studio/data-sharing/tags/backups`

Changing them during the route/service split would be a data migration: existing staged/returned packages, previews, backups, docs import/export expectations, and adapter validation would all need coordinated path changes. That is riskier than the current goal, which is to remove Studio as the route/API owner without changing data behavior.

So I kept them intentionally to preserve current workflow behavior while moving ownership to Analytics. They should probably become `var/analytics/data-sharing/...` later, but that should be a separate explicit migration with path compatibility/move rules, verification, and docs updates.