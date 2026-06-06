---
doc_id: data-models-studio
title: Scope
added_date: 2026-04-19
last_updated: 2026-06-06
parent_id: studio
viewable: true
---
# Studio Scope

This document covers the current checked-in data model for the Studio scope.

## Local Service-Backed Activity Data

Unified activity is now Admin-owned and written under:

- `var/admin/activity/activity_log.json`
- `var/admin/activity/activity_log.jsonl`

Studio catalogue workflows can still append activity rows through `studio/shared/python/studio_activity.py`, but the route/API surface is `/admin/activity/` and `/admin/api/activity/feed`.

## Config

- `studio/app/frontend/config/studio-config.json`
- `studio/app/frontend/js/studio-config.js`

## `work_storage_index.json`

Purpose:

- provide Studio-only work storage lookups without putting curator-only storage data into the public `works_index.json`

Current content families:

- header metadata
- `works` map keyed by `work_id`
- per-work storage values only where storage is populated

Current consumers:

- `/studio/studio-works/`

Why it is separate:

- `storage` is useful to the curator but does not belong in the current public works summary index
- the Studio works page needs one lightweight bulk lookup, not one per-work JSON fetch per row
