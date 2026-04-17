---
doc_id: build-activity
title: Build Activity
last_updated: 2026-04-17
parent_id: studio
sort_order: 35
---

# Build Activity

This document describes the current Studio page at `/studio/build-activity/`.

## Purpose

The page is a lightweight curator-facing history of recent catalogue build runs.

It is intended to answer two practical questions:

- what changed recently
- did the last few catalogue builds behave as expected

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

Each entry currently includes:

- UTC timestamp
- run status
- planner mode
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

Those labels are defined by the catalogue pipeline rather than the Studio page itself. See **[Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)** for the current meanings.

## Current Boundaries

What this page is for:

- quick curator memory of recent build activity
- checking that planner targeting looks plausible
- checking what a scoped JSON-source rebuild touched after a Studio edit
- spotting whether a run was a no-op, targeted rebuild, or larger rebuild

What it is not for:

- low-level debugging of script output
- reviewing every copied file or generated artifact
- serving as the public site’s visitor-facing “recent updates” feed

## Related References

- **[Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)** for the current planner and build entrypoint
- **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the Studio route shell and page inventory
- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for the shared Studio config boundary
