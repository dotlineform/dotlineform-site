---
doc_id: data-models-studio
title: Scope
added_date: 2026-04-19
last_updated: "2026-05-06 20:51"
parent_id: studio
viewable: true
---
# Studio Scope

This document covers the current checked-in data model for the Studio scope.

## local service-backed activity data

- `var/studio/activity/activity_log.json`
- `var/studio/activity/activity_log.jsonl`

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