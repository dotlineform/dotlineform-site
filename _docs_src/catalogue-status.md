---
doc_id: catalogue-status
title: "Catalogue Status"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: studio
sort_order: 50
---
# Catalogue Status

This document describes the Studio page at `/studio/catalogue-status/`.

Draft-work view:

- `/studio/catalogue-status/?view=draft-works`

Draft-series view:

- `/studio/catalogue-status/?view=draft-series`

## Purpose

The page lists canonical catalogue source records whose `status` is not `published`.

It is an early JSON-pipeline maintenance surface. The goal is to make draft, blank, and otherwise non-published source records visible without opening `works.xlsx`.

## Current Inputs

The page reads canonical source JSON directly:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`

The browser paths are configured through `assets/studio/data/studio_config.json`.

## Current Behavior

The page:

- loads the source record families that still own publication status
- filters to rows where normalized status is not `published`
- offers a draft-work view for work source records whose normalized status is `draft`
- offers a draft-series view for series source records whose normalized status is `draft`
- groups counts by record family
- supports a simple search across id, status, title, and parent/reference fields
- shows id, type, status, title, and reference columns
- supports header-click sorting on `id`, `type`, `status`, `title`, and `reference`
- links each row into the focused editor for its record family, opening those editor links in a new browser tab so the status report stays available

It remains a review surface rather than an editor. Editing still happens on the focused record pages.

Work-owned `downloads` and `links` are not listed here because they no longer have independent `status` or `published_date` fields.

## Draft Works View

The `?view=draft-works` view narrows the table to draft work source records only. It shows each draft work's id, title, status, and assigned series ids in the reference column, and links the id to `/studio/catalogue-work/?work=<work_id>` in a new browser tab.

This view is the recovery surface for draft works created in the unified work editor but not published in the same session.

## Draft Series View

The `?view=draft-series` view narrows the table to draft series source records only. It shows each draft series id, title, status, and `primary_work_id` when present in the reference column, and links the id to `/studio/catalogue-series/?series=<series_id>` in a new browser tab.

This view is the recovery surface for draft series created in the unified series editor but not published in the same session.

## Boundaries

What this page is for:

- early review of records that still need publication or cleanup
- quick visibility into blank or non-published statuses
- a daily maintenance entry point while editors are added incrementally

What it is not for:

- validation diagnostics beyond status visibility
- bulk editing
- publish/rebuild actions

## Related References

- **[Studio](/docs/?scope=studio&doc=studio)**
- **[Catalogue Activity](/docs/?scope=studio&doc=catalogue-activity)**
- **[New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)**
- **[Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)**
