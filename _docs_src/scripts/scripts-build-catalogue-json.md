---
doc_id: scripts-build-catalogue-json
title: Scoped JSON Catalogue Build
last_updated: 2026-04-17
parent_id: scripts
sort_order: 55
---

# Scoped JSON Catalogue Build

Script:

```bash
python3 ./scripts/catalogue_json_build.py --work-id 00001
```

This helper is the Phase 5 JSON-source rebuild entrypoint for a focused work scope.

## Common Runs

Preview the scoped build:

```bash
python3 ./scripts/catalogue_json_build.py --work-id 00001
```

Run the scoped build:

```bash
python3 ./scripts/catalogue_json_build.py --work-id 00001 --write
```

Include an additional series when membership changed and the previous series page also needs rebuild:

```bash
python3 ./scripts/catalogue_json_build.py --work-id 00001 --extra-series-ids 004 --write
```

## Current Behavior

The helper:

- reads canonical JSON source from `assets/studio/data/catalogue/`
- resolves the current work record and its current series ids
- unions any `--extra-series-ids`
- runs `generate_work_pages.py --source json` with a narrow `--only` selection:
  - `work-pages`
  - `work-json`
  - `series-pages`
  - `series-index-json`
  - `works-index-json`
  - `recent-index-json`
- then runs `build_search.rb --scope catalogue`

The helper does not:

- copy media
- build srcset derivatives
- rebuild unrelated works
- rebuild moments

## Purpose

This is the command-path companion to the Studio `Save + Rebuild` action on `/studio/catalogue-work/`.

It keeps Phase 5 narrow:

- source save remains separate from rebuild
- rebuild scope is explicit
- canonical source JSON stays the only write target for metadata edits

## Related References

- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Build Activity](/docs/?scope=studio&doc=build-activity)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
