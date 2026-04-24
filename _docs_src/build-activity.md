---
doc_id: build-activity
title: "Build Activity"
added_date: 2026-04-18
last_updated: 2026-04-18
parent_id: studio
sort_order: 90
---
# Build Activity

This document describes the current Studio page at `/studio/build-activity/`.

## Purpose

The page is a curator-facing history of recent catalogue build runs.

It is intended to answer three practical questions:

- what changed recently
- did the last few catalogue builds behave as expected
- what concrete scope did each rebuild target

It is not the canonical engineering log for scripts and it is not yet a public-facing site history surface.

## Current Inputs

The page reads:

- `assets/studio/data/build_activity.json`

That feed is generated from:

- successful non-dry-run `build_catalogue.py` runs
- scoped JSON-source rebuilds triggered by the Studio catalogue workflow

The published feed is a capped summary view. The fuller local journal lives outside the published assets under:

- `var/build_activity/build_catalogue.jsonl`

## Current Entry Shape

Each entry now includes:

- UTC timestamp
- run label
- run status
- scope label
- result label
- short summary text
- source change groups when the run came from a JSON-source scoped rebuild
- workbook change groups
- media change groups
- planned action counts
- result flags such as planner state updates

IDs are intentionally sampled in the published feed rather than dumped in full.

Current planner mode labels:

- `full`
- `bootstrap`
- `incremental`

Historical planner labels came from the retired workbook-led pipeline. Current scoped JSON build entries use the JSON-led rebuild flow and share this same activity surface.

## Current Boundaries

What this page is for:

- quick curator memory of recent build activity
- checking that planner targeting looks plausible
- checking what a scoped JSON-source rebuild touched after a Studio edit
- spotting whether a run was a no-op, targeted rebuild, or larger rebuild
- jumping back into the relevant editor or follow-on review route from a build row

What it is not for:

- low-level debugging of script output
- reviewing every copied file or generated artifact
- serving as the public site’s visitor-facing “recent updates” feed

## Related References

- **[Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)** for the live scoped rebuild entrypoint
- **[New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)** for the current workflow boundary
- **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the Studio route shell and page inventory
- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for the shared Studio config boundary
