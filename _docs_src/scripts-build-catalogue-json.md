---
doc_id: scripts-build-catalogue-json
title: "Scoped JSON Catalogue Build"
added_date: 2026-04-18
last_updated: 2026-04-27
parent_id: scripts
sort_order: 70
---
# Scoped JSON Catalogue Build

Script:

```bash
./scripts/catalogue_json_build.py --work-id 00001
```

This helper is the Phase 5 JSON-source rebuild entrypoint for focused work and series scopes.

It also supports a focused moment scope used by the first Studio moments import page.

## Common Runs

Preview the scoped build:

```bash
./scripts/catalogue_json_build.py --work-id 00001
```

Run the scoped build:

```bash
./scripts/catalogue_json_build.py --work-id 00001 --write
```

Include an additional series when membership changed and the previous series page also needs rebuild:

```bash
./scripts/catalogue_json_build.py --work-id 00001 --extra-series-ids 004 --write
```

Preview a scoped series build:

```bash
./scripts/catalogue_json_build.py --series-id 004
```

Run a scoped series build:

```bash
./scripts/catalogue_json_build.py --series-id 004 --write
```

Preview a single moment import scope:

```bash
./scripts/catalogue_json_build.py --moment-file keys.md
```

Run the moment import scope:

```bash
./scripts/catalogue_json_build.py --moment-file keys.md --write
```

## Current Behavior

The helper:

- reads canonical JSON source from `assets/studio/data/catalogue/`
- resolves the current work record and its current series ids
- unions any `--extra-series-ids`
- lets the generator render optional work and series prose from `_docs_src_catalogue/works/<work_id>.md` and `_docs_src_catalogue/series/<series_id>.md`
- passes the generator's narrow `--refresh-published` mode so selected published records can be recomputed without forcing unchanged writes
- runs the internal `generate_work_pages.py` JSON engine with a narrow `--only` selection:
  - `work-pages`
  - `work-json`
  - `series-pages`
  - `series-index-json`
  - `works-index-json`
  - `recent-index-json`
- then runs `build_search.rb --scope catalogue`

For `--moment-file`, the helper:

- resolves moment metadata from `assets/studio/data/catalogue/moments.json`
- resolves moment prose from `_docs_src_catalogue/moments/<moment_id>.md`
- validates the moment filename, metadata, and required prose source
- runs the internal `generate_work_pages.py` engine with `--only moments --moment-ids <moment_id> --refresh-published`
- then runs `build_search.rb --scope catalogue`

Force behavior:

- normal scoped builds do not pass `--force`; unchanged generated payloads and aggregate indexes are skipped by content version
- `--force` remains available for intentional full rewrites and also passes force through to catalogue search
- already-published records do not get a refreshed `published_date` unless they transition from `draft` to `published`

The helper does not:

- copy media for moment imports
- build srcset derivatives
- rebuild unrelated works
- scan the moments folder for changes

## Purpose

This is the command-path companion to the Studio `Save + Rebuild` action on `/studio/catalogue-work/` and the file-driven moments import flow on `/studio/catalogue-moment-import/`.

It keeps Phase 5 narrow:

- source save remains separate from rebuild
- rebuild scope is explicit
- canonical source JSON stays the only write target for metadata edits

## Related References

- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Build Activity](/docs/?scope=studio&doc=build-activity)
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
