---
doc_id: catalogue-status
title: "Catalogue Drafts"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: studio
sort_order: 50
---
# Catalogue Drafts

This document describes the Studio drafts page at `/studio/catalogue-status/`.

Family views:

- `/studio/catalogue-status/`
- `/studio/catalogue-status/?family=works`
- `/studio/catalogue-status/?family=work_details`
- `/studio/catalogue-status/?family=moments`

## Purpose

The page lists canonical catalogue source records whose normalized `status` is `draft`.

It is the recovery surface for draft catalogue records created without publishing in the same session.

## Current Inputs

The page reads canonical source JSON directly:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`
- `assets/studio/data/catalogue/moments.json`

The browser paths are configured through `assets/studio/data/studio_config.json`.

## Current Behavior

The page:

- loads the source record families that still own publication status
- filters to rows where normalized status is `draft`
- offers four draft-family pills in this order: `series`, `works`, `work details`, `moments`
- shows draft counts by record family
- supports a simple search across id, status, title, and parent/reference fields
- shows id, type, status, title, and reference columns
- supports header-click sorting on `id`, `type`, `status`, `title`, and `reference`
- links each row into the focused editor for its record family, opening those editor links in a new browser tab so the status report stays available

It remains a review surface rather than an editor. Editing still happens on the focused record pages.

Work-owned `downloads` and `links` are not listed here because they no longer have independent `status` or `published_date` fields.

## Family Views

The default view shows draft series records. Use the family pills or `?family=<family>` to switch families.

Supported family keys:

- `series`
- `works`
- `work_details`
- `moments`

Legacy `?view=draft-works` and `?view=draft-series` URLs still map to the matching family filters.

## Boundaries

What this page is for:

- early review of records that still need publication or cleanup
- quick visibility into draft records
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
