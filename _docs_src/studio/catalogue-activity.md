---
doc_id: catalogue-activity
title: Catalogue Activity
last_updated: 2026-04-17
parent_id: studio
sort_order: 34
---

# Catalogue Activity

This document describes the Studio page at `/studio/catalogue-activity/`.

## Purpose

The page is a lightweight activity surface for the JSON-led catalogue source pipeline.

It gives quick access to recent catalogue source saves and validation failures without requiring the curator to inspect CLI output or raw JSONL logs.

## Current Inputs

The page reads:

- `assets/studio/data/catalogue_activity.json`

That feed is updated by the Catalogue Write Server when it records source-save and validation-failure events.

The fuller local journal lives outside published route data under:

- `var/studio/catalogue/logs/catalogue_activity.jsonl`

The write-server operational log remains:

- `var/studio/catalogue/logs/catalogue_write_server.log`

## Current Entry Shape

Each feed entry includes:

- UTC timestamp
- kind
- operation
- status
- short summary
- affected work, series, and work-detail id groups
- log reference

IDs are sampled in the published feed rather than dumped in full.

## Boundaries

What this page is for:

- recent source-save awareness
- validation-failure visibility
- a single place to add import and JSON-source build activity as later phases land

What it is not for:

- field-level diffs
- full operational debugging
- public recently-added history

## Related References

- **[Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)**
- **[Build Activity](/docs/?scope=studio&doc=build-activity)**
- **[Catalogue Status](/docs/?scope=studio&doc=catalogue-status)**
- **[New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)**
