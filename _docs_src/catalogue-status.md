---
doc_id: catalogue-status
title: "Catalogue Status"
added_date: 2026-04-18
last_updated: 2026-04-18
parent_id: studio
sort_order: 50
---
# Catalogue Status

This document describes the Studio page at `/studio/catalogue-status/`.

## Purpose

The page lists canonical catalogue source records whose `status` is not `published`.

It is an early JSON-pipeline maintenance surface. The goal is to make draft, blank, and otherwise non-published source records visible without opening `works.xlsx`.

## Current Inputs

The page reads canonical source JSON directly:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`
- `assets/studio/data/catalogue/work_files.json`
- `assets/studio/data/catalogue/work_links.json`

The browser paths are configured through `assets/studio/data/studio_config.json`.

## Current Behavior

The page:

- loads all five source record families
- filters to rows where normalized status is not `published`
- groups counts by record family
- supports a simple search across id, status, title, and parent/reference fields
- shows id, type, status, title, and reference columns
- supports header-click sorting on `id`, `type`, `status`, `title`, and `reference`
- links each row into the focused editor for its record family when that editor exists

It remains a review surface rather than an editor. Editing still happens on the focused record pages.

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
