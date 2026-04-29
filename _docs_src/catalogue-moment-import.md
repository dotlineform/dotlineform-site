---
doc_id: catalogue-moment-import
title: "Catalogue Moment Import"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: studio
sort_order: 190
---
# Catalogue Moment Import

Moment import now lives inside [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor).

Route:

- `/studio/catalogue-moment-import/`

The route is retained only as a compatibility bridge. It redirects to `/studio/catalogue-moment/` and preserves `?file=<filename>` when a staged-file link already has one.

## Purpose

This document records the import contract that is now implemented on the single Moment editor page.

It is intentionally file-driven:

- the user specifies one staged moment Markdown filename such as `keys.md`
- Studio collects the moment metadata in the shared Moment editor metadata fields
- Studio previews the staged body-only prose source
- apply imports prose and writes canonical draft moment metadata

This page does not scan external moment folders for changes.

After apply, the editor opens the imported draft record for review, save, publish, unpublish, or delete.

## Current Behavior

The current single-page flow is implemented by:

- `studio/catalogue-moment/index.md`
- `assets/studio/js/catalogue-moment-editor.js`

The legacy bridge route is:

- `studio/catalogue-moment-import/index.md`

Shared runtime dependencies:

- `assets/studio/js/studio-config.js`
- `assets/studio/js/studio-transport.js`
- `scripts/studio/catalogue_write_server.py`

Current page flow:

1. probe the local catalogue write service
2. enter new/import mode with `New` or `?file=<filename>`
3. accept a filename-only input above the shared metadata fields
4. accept moment metadata in the same fields used for existing moments
5. call `POST /catalogue/moment/import-preview`
6. show resolved source metadata, staged prose state, local media state, and validation errors
7. call `POST /catalogue/moment/import-apply`
8. show the imported draft source result and open the draft moment in the editor

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
- imported moments are always written with `status: draft`
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration
- source images resolve from `DOTLINEFORM_PROJECTS_BASE_DIR/moments/images/<source_image_file>`
- missing source images block local media generation for the moment but do not block prose/metadata import

The page uses the existing runtime behavior where missing images produce no hero image on the public moment page until the image source is restored and the scoped build is rerun.

## Apply Behavior

Apply writes:

- body-only prose to `_docs_src_catalogue/moments/<moment_id>.md`
- draft moment metadata to `assets/studio/data/catalogue/moments.json`

Apply does not publish the moment and does not run the scoped public update. The editor opens the imported draft automatically; use `Publish` there when it is ready.

Publishing later delegates to the existing generator path:

- `catalogue_json_build.py --moment-file <filename> --write`
- `generate_work_pages.py --only moments --moment-ids <moment_id> --write`
- `build_search.rb --scope catalogue`

This means:

- source Markdown no longer owns canonical moment metadata
- generated runtime JSON remains generated, not canonical
- the generator does not write moment prose front matter
- local moment media generation uses the same scoped build path as works and work details
- renamed source images are staged under `var/catalogue/media/moments/make_srcset_images/`
- primary and thumbnail derivatives are generated under `var/catalogue/media/moments/srcset_images/`
- generated thumbnails are copied into `assets/moments/img/`
- generated primary derivatives remain staged for remote media publishing

## Out Of Scope

- folder scanning for new or changed moments
- browser-side prose editing beyond importing staged Markdown
- browser-side image upload/edit behavior
- R2-backed or cloud-native media handling

## Related References

- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)
