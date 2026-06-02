---
doc_id: catalogue-moment-editor
title: Catalogue Moment Editor
added_date: 2026-04-27
last_updated: 2026-05-22
parent_id: studio
viewable: true
---
# Catalogue Moment Editor

Route:

- `/studio/catalogue-moment/`
- focused record selection uses `?moment=<moment_id>`
- staged import mode uses `?file=<moment_id>.md`

The route shell is hosted by the local Studio app server.
The old Jekyll route shell has been retired.

This page edits one existing canonical moment metadata record from `assets/studio/data/catalogue/moments.json` through the local catalogue service.
It also imports new draft moments from staged body-only Markdown, so moment creation, review, save, publish, and unpublish now live on one Studio page.

## Use This Page For

- opening an existing moment by `moment_id` or title
- importing a new draft moment from `var/docs/catalogue/import-staging/moments/<moment_id>.md`
- editing moment metadata fields
- saving source JSON without changing publication status
- publishing draft moments through a dedicated `Publish` command
- unpublishing public moments through a dedicated `Unpublish` command
- deleting one moment and its generated site artifacts after preview/confirmation
- checking permanent prose, staged prose, and source-image readiness
- refreshing local moment image derivatives from the displayed source image path without changing source metadata
- importing staged moment prose from `var/docs/catalogue/import-staging/moments/<moment_id>.md`

## Editable Fields

- `title`
- `date`
- `date_display`
- `published_date`
- `source_image_file`
- `image_alt`

`status` is visible with the Readonly Display treatment. Change publication state with `Publish` or `Unpublish`; do not edit status directly.

The editor does not edit prose inline. Moment prose remains body-only Markdown under `_docs_catalogue/moments/<moment_id>.md`.

## Route Ready State

The page root `#catalogueMomentRoot` implements the shared Studio ready-state contract:

- `data-studio-ready="false"` during initial route setup
- `data-studio-ready="true"` after the initial empty, focused-moment, or staged-import render completes
- `data-studio-busy="true"` while save, publish, unpublish, media refresh, import preview/apply, staged-prose import, or delete commands are running
- `data-studio-mode="empty|single|import"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

## Save And Publication

`Save` calls `POST /studio/api/catalogue/moment/save` with the current record hash for stale-write protection.

`Save` does not change publication status. Draft moment saves remain source-only. Published moment saves request the internal public update path so saved changes appear in generated public moment artifacts without exposing a separate update command.

`Publish` and `Unpublish` call the shared publication preview/apply endpoints:

- `POST /studio/api/catalogue/publication-preview`
- `POST /studio/api/catalogue/publication-apply`

`Publish` requires valid moment metadata and readiness for the public moment surface, then changes source status to `published` and runs the scoped public update. `Unpublish` changes source status back to `draft`, ignores unsaved form edits after confirmation, removes generated moment page/json/search output, and updates `assets/data/moments_index.json`.

The internal scoped public update rebuilds:

- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- catalogue search
- local moment media derivatives when the configured source image is available

The moment media readiness panel also exposes `Refresh media` when the configured source image exists. That action calls the scoped build endpoint with `media_only: true` and `force: true`, so it refreshes thumbnails and staged primary variants from the displayed source path without saving metadata or rebuilding page/json/search outputs. The result message is `Thumbnails updated; primary variants staged for publishing.`

## New Moment Import

`New` switches the editor into draft import mode without leaving the page. In this mode, the existing metadata fields become the initial metadata for the new moment, `status` remains a Readonly Display value of `draft`, and the source-file field appears above the shared metadata fields.

The import flow:

1. click `New`, or open the page with `?file=<filename>`
2. enter a filename-only staged moment file, such as `keys.md`
3. enter initial metadata in the same fields used by existing moments
4. preview the staged prose and resolved metadata with `POST /studio/api/catalogue/moment/import-preview`
5. apply the import with `POST /studio/api/catalogue/moment/import-apply`
6. open the imported draft in the editor immediately after a successful apply

Runtime ownership:

- `assets/studio/js/catalogue-moment-editor.js` owns route bootstrap, generated moment lookup reads, service availability, normal edit state construction, post-import opening, dirty-state orchestration, display/action/import/selection context wiring, and route-ready state.
- `assets/studio/js/catalogue-moment-selection.js` owns Moment search matching, popup rendering, Open button resolution, popup click handling, and initial empty/focused/import route selection.
- `assets/studio/js/catalogue-moment-actions.js` owns normal edit action workflow sequencing for save, build preview refresh, publication, delete, staged prose import, media refresh, activity context shaping, confirmation formatting, and public-update outcome handling.
- `assets/studio/js/catalogue-moment-form.js` owns editable field rendering, readonly field rendering, field value reads/writes, readonly value clearing, and field validation message rendering.
- `assets/studio/js/catalogue-moment-sections.js` owns normal edit summary rendering, readiness rendering, and build-impact text rendering.
- `assets/studio/js/catalogue-moment-import.js` owns staged-file query state, import metadata reads, preview metadata seeding, import preview/apply transport sequencing, import summary/detail rendering, stale preview clearing, import control availability, and import activity context.
- `assets/studio/js/catalogue-moment-fields.js` owns field definitions, id/filename normalization, draft reads, source-record shaping, and validation.

Local app migration:

- the page shell now lives in `studio/app/server/studio/studio_app_views.py`
- the local app mounts it at `/studio/catalogue-moment/?mode=manage`
- `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py` covers the local route shell and unavailable-service state

Apply writes:

- body-only prose to `_docs_catalogue/moments/<moment_id>.md`
- draft moment metadata to `assets/studio/data/catalogue/moments.json`

Import always forces source status to `draft`. It does not publish the moment and does not run the scoped public update. Use `Publish` on the opened draft record when the moment is ready.
Successful apply also appends a unified Studio activity row for the `import moment` action with script purpose `import source data`.

The old standalone `/studio/catalogue-moment-import/` route is retired. Open `/studio/catalogue-moment/?file=<filename>` directly for staged-file links.

## Delete

`Delete` calls `POST /studio/api/catalogue/delete-preview` with `kind: "moment"` and the current record hash.
If the preview has no blockers or validation errors, the page asks for confirmation and then calls `POST /studio/api/catalogue/delete-apply`.

The Studio delete removes:

- the canonical moment metadata record through `GET /studio/api/catalogue/read?key=catalogue_moments`
- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- matching published moment thumbnails under `assets/moments/img/`
- matching repo-local staged media under `var/catalogue/media/moments/`
- the moment entry from `assets/data/moments_index.json`
- the catalogue search record, by rebuilding catalogue search after the delete

It does not delete canonical prose under `_docs_catalogue/moments/`, canonical source images under `DOTLINEFORM_PROJECTS_BASE_DIR`, or remote media already uploaded outside the repo.

## Staged Prose Import

`Import staged prose` checks:

- `var/docs/catalogue/import-staging/moments/<moment_id>.md`

The staged file is imported as Markdown body source. Existing permanent prose requires overwrite confirmation when the staged content differs.

Importing prose does not change `moments.json`. Publish the moment or save an already published moment to update generated runtime payloads.

## Related References

- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
