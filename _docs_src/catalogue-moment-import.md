---
doc_id: catalogue-moment-import
title: "Catalogue Moment Import"
added_date: 2026-04-18
last_updated: 2026-04-27
parent_id: studio
sort_order: 190
---
# Catalogue Moment Import

This page adds the first Studio-backed moments workflow.

Route:

- `/studio/catalogue-moment-import/`

## Purpose

This is the Phase 2 narrow moments entry flow.

It is intentionally file-driven:

- the user specifies one staged moment Markdown filename such as `keys.md`
- Studio collects the moment metadata on the page
- Studio previews the staged body-only prose source
- apply imports prose, writes canonical moment metadata, runs a targeted moment rebuild, and rebuilds catalogue search

This page does not scan external moment folders for changes and does not manage moment media/srcset generation.

## Current Behavior

The page is implemented by:

- `studio/catalogue-moment-import/index.md`
- `assets/studio/js/catalogue-moment-import.js`

Shared runtime dependencies:

- `assets/studio/js/studio-config.js`
- `assets/studio/js/studio-transport.js`
- `scripts/studio/catalogue_write_server.py`

Current page flow:

1. probe the local catalogue write service
2. accept a filename-only input
3. accept moment metadata fields
4. call `POST /catalogue/moment/import-preview`
5. show resolved source metadata, staged prose state, and validation errors
6. call `POST /catalogue/moment/import-apply`
7. show the targeted build result and link to the public moment page

## Source Model

Canonical moment metadata lives in:

- `assets/studio/data/catalogue/moments.json`

Canonical moment prose lives in:

- `_docs_src_catalogue/moments/<moment_id>.md`

Staged prose enters through:

- `var/docs/catalogue/import-staging/moments/<moment_id>.md`

Current assumptions:

- `moment_id` is the filename stem
- staged and permanent prose files are body-only Markdown with no canonical metadata front matter
- required metadata is entered on the Studio page
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration
- missing source images are acceptable in this phase

The page uses the existing runtime behavior where missing images produce no hero image on the public moment page.

## Apply Behavior

Apply writes:

- body-only prose to `_docs_src_catalogue/moments/<moment_id>.md`
- moment metadata to `assets/studio/data/catalogue/moments.json`

Then it delegates to the existing generator path:

- `catalogue_json_build.py --moment-file <filename> --write`
- `generate_work_pages.py --only moments --moment-ids <moment_id> --write`
- `build_search.rb --scope catalogue`

This means:

- source Markdown no longer owns canonical moment metadata
- generated runtime JSON remains generated, not canonical
- the generator does not write moment prose front matter
- local media generation is skipped for this import path

## Out Of Scope

- folder scanning for new or changed moments
- browser-side prose editing beyond importing staged Markdown
- srcset generation or media-image import/edit behavior
- R2-backed or cloud-native media handling

## Related References

- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)
