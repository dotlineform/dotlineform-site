---
doc_id: catalogue-moment-import
title: Catalogue Moment Import
last_updated: 2026-04-18
parent_id: studio
sort_order: 45
---

# Catalogue Moment Import

This page adds the first Studio-backed moments workflow.

Route:

- `/studio/catalogue-moment-import/`

## Purpose

This is the Phase 2 narrow moments entry flow.

It is intentionally file-driven:

- the user specifies one canonical moment markdown filename such as `keys.md`
- Studio previews the resolved source file and validates the current front matter
- apply runs a targeted import/publish flow for that one moment and rebuilds catalogue search

This page does not create prose files, does not edit prose content, and does not scan the `moments/` folder for changes.

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
3. call `POST /catalogue/moment/import-preview`
4. show resolved source metadata and validation errors
5. call `POST /catalogue/moment/import-apply`
6. show the targeted build result and link to the public moment page

## Source Model

Canonical moment metadata lives in the external source file:

- `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md`

Current assumptions:

- `moment_id` is the filename stem
- required front matter remains `title`, `status`, and `date`
- `date_display`, `published_date`, and `image_file` remain part of the live source model
- missing source images are acceptable in this phase

The page uses the existing runtime behavior where missing images simply produce no hero image on the public moment page.

## Apply Behavior

Apply does not write front matter directly from the browser.

Instead it delegates to the existing generator path:

- `catalogue_json_build.py --moment-file <filename> --write`
- `generate_work_pages.py --only moments --moment-ids <moment_id> --write`
- `build_search.rb --scope catalogue`

This means:

- the source markdown file remains canonical
- the generator is still responsible for publishing the moment
- the generator may update front matter such as `status`, `published_date`, and normalized `image_file`

## Out Of Scope

- folder scanning for new or changed moments
- browser-side create/edit for moment prose or front matter
- srcset generation
- R2-backed or cloud-native media handling

## Related References

- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)
