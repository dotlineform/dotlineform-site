---
doc_id: catalogue-activity
title: "Catalogue Activity"
added_date: 2026-04-18
last_updated: 2026-04-18
parent_id: studio
sort_order: 60
---
# Catalogue Activity

This document describes the Studio page at `/studio/catalogue-activity/`.

## Purpose

The page is a curator-facing activity surface for the JSON-led catalogue source pipeline.

It gives quick access to recent source saves, creates, deletes, imports, and validation failures without requiring the curator to inspect CLI output or raw JSONL logs.

## Current Inputs

The page reads:

- `assets/studio/data/catalogue_activity.json`

That feed is updated from the local catalogue activity journal and is now shaped so source-side events stay on this page while rebuild outcomes move to **[Build Activity](/docs/?scope=studio&doc=build-activity)**.

The fuller local journal lives outside published route data under:

- `var/studio/catalogue/logs/catalogue_activity.jsonl`

The write-server operational log remains:

- `var/studio/catalogue/logs/catalogue_write_server.log`

## Current Entry Shape

Each feed entry now includes:

- UTC timestamp
- event label
- status
- scope label
- short summary
- follow-up / attention label
- affected work, series, work-detail, work-file, work-link, and moment groups
- log reference

IDs are sampled in the published feed rather than dumped in full.

## Boundaries

What this page is for:

- recent source-save awareness
- validation-failure visibility
- import visibility without dropping into raw logs
- direct links back into the relevant editor or next workflow step

What it is not for:

- field-level diffs
- full operational debugging
- rebuild/run history
- public recently-added history

## Related References

- **[Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)**
- **[Build Activity](/docs/?scope=studio&doc=build-activity)**
- **[Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status)**
- **[New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)**
