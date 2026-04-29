---
doc_id: catalogue-moment-editor
title: "Catalogue Moment Editor"
added_date: 2026-04-27
last_updated: 2026-04-29
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
- saving source JSON without changing publication status
- publishing draft moments through a dedicated `Publish` command
- unpublishing public moments through a dedicated `Unpublish` command
- deleting one moment and its generated site artifacts after preview/confirmation
- checking permanent prose, staged prose, and source-image readiness
- refreshing local moment image derivatives from the displayed source image path without changing source metadata
- importing staged moment prose from `var/docs/catalogue/import-staging/moments/<moment_id>.md`

Use [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import) for introducing a moment from a staged prose file.

## Editable Fields

- `title`
- `date`
- `date_display`
- `published_date`
- `source_image_file`
- `image_alt`

`status` is visible with the Readonly Display treatment. Change publication state with `Publish` or `Unpublish`; do not edit status directly.

The editor does not edit prose inline. Moment prose remains body-only Markdown under `_docs_src_catalogue/moments/<moment_id>.md`.

## Save And Publication

`Save` calls `POST /catalogue/moment/save` with the current record hash for stale-write protection.

`Save` does not change publication status. Draft moment saves remain source-only. Published moment saves request the internal public update path so saved changes appear in generated public moment artifacts without exposing a separate update command.

`Publish` and `Unpublish` call the shared publication preview/apply endpoints:

- `POST /catalogue/publication-preview`
- `POST /catalogue/publication-apply`

`Publish` requires valid moment metadata and readiness for the public moment surface, then changes source status to `published` and runs the scoped public update. `Unpublish` changes source status back to `draft`, ignores unsaved form edits after confirmation, removes generated moment page/json/search output, and updates `assets/data/moments_index.json`.

The internal scoped public update rebuilds:

- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- catalogue search
- local moment media derivatives when the configured source image is available

The moment media readiness panel also exposes `Refresh media` when the configured source image exists. That action calls the scoped build endpoint with `media_only: true` and `force: true`, so it refreshes thumbnails and staged primary variants from the displayed source path without saving metadata or rebuilding page/json/search outputs. The result message is `Thumbnails updated; primary variants staged for publishing.`

## Delete

`Delete` calls `POST /catalogue/delete-preview` with `kind: "moment"` and the current record hash.
If the preview has no blockers or validation errors, the page asks for confirmation and then calls `POST /catalogue/delete-apply`.

The Studio delete removes:

- the canonical moment metadata record from `assets/studio/data/catalogue/moments.json`
- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- matching published moment thumbnails under `assets/moments/img/`
- matching repo-local staged media under `var/catalogue/media/moments/`
- the moment entry from `assets/data/moments_index.json`
- the catalogue search record, by rebuilding catalogue search after the delete

It does not delete canonical prose under `_docs_src_catalogue/moments/`, canonical source images under `DOTLINEFORM_PROJECTS_BASE_DIR`, or remote media already uploaded outside the repo.

## Staged Prose Import

`Import staged prose` checks:

- `var/docs/catalogue/import-staging/moments/<moment_id>.md`

The staged file must be body-only Markdown with no front matter. Existing permanent prose requires overwrite confirmation when the staged content differs.

Importing prose does not change `moments.json`. Publish the moment or save an already published moment to update generated runtime payloads.

## Related References

- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
