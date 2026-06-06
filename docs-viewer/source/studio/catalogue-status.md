---
doc_id: catalogue-status
title: Catalogue Drafts
added_date: 2026-04-18
last_updated: "2026-06-02"
parent_id: studio
viewable: true
---
# Catalogue Drafts

This document describes the Studio drafts page at `/studio/catalogue-status/`.
The route shell is now hosted by the local Studio app server rather than Jekyll.

Family views:

- `/studio/catalogue-status/`
- `/studio/catalogue-status/?family=works`
- `/studio/catalogue-status/?family=work_details`
- `/studio/catalogue-status/?family=moments`

## Purpose

The page lists canonical catalogue source records whose normalized `status` is `draft`.

It is the recovery surface for draft catalogue records created without publishing in the same session.

## Route Ready State

The page root `#catalogueStatusRoot` implements the shared Studio ready-state contract:

- `data-studio-ready="false"` during initial draft-family loading
- `data-studio-ready="true"` after all draft families have loaded or the local service has reached a stable unavailable state
- `data-studio-busy="false"` because this route has no route-level commands
- `data-studio-mode="empty|list"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

## Current Inputs

The page reads canonical source JSON through the local Studio app catalogue API:

- `GET /studio/api/catalogue/read?key=catalogue_works`
- `GET /studio/api/catalogue/read?key=catalogue_work_details`
- `GET /studio/api/catalogue/read?key=catalogue_series`
- `GET /studio/api/catalogue/read?key=catalogue_moments`

The logical keys are configured through `studio/app/frontend/config/studio-config.json` under `paths.data.studio`.
The canonical source files now live under `studio/data/canonical/catalogue/`, and public Jekyll output excludes Studio-only catalogue source data.

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
The local route preserves the selected `family` filter when family filters are changed.

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
- **[Studio Activity](/docs/?scope=studio&doc=studio-activity)**
- **[Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)**
- **[Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)**
