---
doc_id: catalogue-moment-editor
title: "Catalogue Moment Editor"
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: user-guide
sort_order: 182
---
# Catalogue Moment Editor

Route:

- `/studio/catalogue-moment/`
- focused record selection uses `?moment=<moment_id>`

This page edits one existing canonical moment metadata record from `assets/studio/data/catalogue/moments.json`.

## Use This Page For

- opening an existing moment by `moment_id` or title
- editing moment metadata fields
- saving source JSON only
- optionally running a scoped moment rebuild immediately
- checking permanent prose, staged prose, and source-image readiness
- importing staged moment prose from `var/docs/catalogue/import-staging/moments/<moment_id>.md`

Use [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import) for introducing a moment from a staged prose file.

## Editable Fields

- `title`
- `status`
- `date`
- `date_display`
- `published_date`
- `source_image_file`
- `image_alt`

The editor does not edit prose inline. Moment prose remains body-only Markdown under `_docs_src_catalogue/moments/<moment_id>.md`.

## Save And Rebuild

`Save` calls `POST /catalogue/moment/save` with the current record hash for stale-write protection.

When `Update site now` is checked, save also runs the scoped moment build. Otherwise the page marks the public moment as pending until `Update site now` is run.

The scoped update rebuilds:

- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- catalogue search
- local moment media derivatives when the configured source image is available

## Staged Prose Import

`Import staged prose` checks:

- `var/docs/catalogue/import-staging/moments/<moment_id>.md`

The staged file must be body-only Markdown with no front matter. Existing permanent prose requires overwrite confirmation when the staged content differs.

Importing prose does not change `moments.json`; run `Update site now` afterward to publish the prose into generated runtime payloads.

## Related References

- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
