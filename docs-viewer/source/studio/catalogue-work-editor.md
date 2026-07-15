---
doc_id: catalogue-work-editor
title: Catalogue Work Editor
added_date: 2026-04-22
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Work Editor

## What It Does

Use `/studio/catalogue-work/` to create, find, edit, publish, unpublish, or delete catalogue Works.

The same route has three modes:

- `?work=<work_id>` opens one Work.
- `?mode=new` creates a draft Work.
- a comma-delimited or numeric-range selection opens bulk edit mode.

The editor also owns Work-level downloads, links, media selection, and detail-section management. It does not edit Work prose or provide individual detail-record editing.

Canonical metadata lives in `studio/data/canonical/catalogue/works.json`. Detail sections live in per-Work files under `studio/data/canonical/catalogue/work_details/`.

## Main Workflow

### Open Or Create

- Search uses the generated Work search projection, then opening a record requests a focused `catalogue_work_record` projection from the local catalogue API.
- New mode creates a draft source record only. `?series=<series_id>` may preselect one Series.
- Required fields and editable-field rules come from the catalogue field registry and `catalogue-work-fields.js`; the documentation does not duplicate that changing inventory.
- Draft Works remain recoverable from [Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status).

### Edit And Save

1. The browser keeps the full canonical record as its editable baseline and uses the focused projection for generated context.
2. `Save` validates the draft and sends the normalized patch plus an expected record hash.
3. The catalogue service rejects stale writes, validates the complete source set, and writes canonical JSON atomically.
4. Derived Studio lookups are refreshed according to the field registry and lookup serializer dependencies.
5. A published Work also receives its scoped public update; a draft save remains source-only.
6. The editor reloads the focused projection and reports source, build, and media outcomes separately.

There is no offline save path. If the local catalogue API is unavailable, editing commands are disabled rather than queued in the browser.

### Publish, Unpublish, And Delete

- `Publish` is available only for a clean saved draft that meets publication requirements and belongs to at least one published Series.
- `Unpublish` ignores uncommitted form changes after confirmation, changes the canonical status to draft, and removes the Work from public output.
- `Delete` uses preview and apply requests. The service reports blockers, removes dependent detail and Work-owned metadata in the canonical transaction, cleans generated/public artifacts, and then removes exact remote media variants.
- Bulk mode does not allow delete.

The server owns all dependency checks and cleanup planning. Browser confirmations are not an authority for whether a mutation is safe.

## Bulk Editing

Bulk mode accepts explicit Work IDs, ranges, or a mixture of both.

- Untouched fields preserve each record's value.
- A touched empty field clears that field across the selection.
- Series membership supports exact replacement or `+id` and `-id` operations.
- Detail, download, link, publication, media, and delete controls are intentionally hidden.
- Canonical source is written once for the combined change; published Works receive the corresponding scoped public update.

Bulk behavior is implemented as a separate transaction shape, not repeated single-record saves.

## Detail Sections

The Work editor treats details as a Work-owned aggregate:

- sections own their title, subfolder, ordering, and detail-sort rules;
- details are nested below a section in the Work's canonical detail file;
- the browser groups details by section and supports focused detail search;
- section creation writes the section and selected detail records together, then builds and publishes their primary media;
- section deletion removes the section and all of its details, then removes their exact remote variants.

Individual detail create, edit, and delete commands are intentionally absent. The aggregate workflow matches the source structure and avoids a second editor for rare record-level mutations. See [Catalogue Per-Work Detail Source](/docs/?scope=studio&doc=catalogue-per-work-detail-source) for the data boundary.

## Project And Published Media

The project-media picker searches direct project folders and one optional direct subfolder below `DOTLINEFORM_PROJECTS_BASE_DIR/projects`. The server rejects absolute paths, traversal, hidden names, and nested subfolder paths; the browser never receives absolute filesystem paths.

`Refresh media` is a local regeneration workflow. It may use unsaved project-media fields to stage a preview, but it does not write canonical metadata or advance the confirmed media version.

For an eligible published Work, `Save` continues into the R2 media-publish workflow:

1. preview validates the complete required local primary set and compares it with R2;
2. the user confirms a new upload or explicitly acknowledges replacement;
3. apply repeats the version and comparison guards before any remote write;
4. a complete successful upload promotes the canonical media version and rebuilds the focused public Work JSON;
5. cancellation, drift, conflict, or partial failure remains a visible pending action that `Save` can retry.

Credentials, local paths, object keys, checksums, and signed requests remain server-side. See [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2) for the media-owned publishing contract.

## Runtime Ownership

The browser implementation is grouped by responsibility under `studio/app/frontend/js/`:

- `catalogue-work-editor.js`, `catalogue-work-editor-state.js`, and `catalogue-work-editor-events.js` coordinate the route.
- `catalogue-work-form.js` and `catalogue-work-fields.js` own field presentation and record shaping.
- `catalogue-work-selection.js` owns search, URL selection, and mode changes.
- `catalogue-work-actions.js` and `catalogue-work-action-records.js` coordinate source, publication, build, and delete commands.
- `catalogue-work-sections.js`, `catalogue-work-detail-browser.js`, and `catalogue-work-editor-modals.js` own the Work-owned secondary surfaces.
- `catalogue-project-media-picker.js` and `catalogue-work-media-publish.js` own the two media workflows.
- `catalogue-editor-service-client.js` is the browser transport boundary.

Server dispatch begins in `studio/app/server/studio/studio_catalogue_api.py`. Canonical mutation behavior lives in the focused services under `studio/services/catalogue/`, with the accepted POST paths registered by `catalogue_write_service.py`.

## Extension And Weak Spots

When adding a capability, choose its existing owner before extending the route coordinator. A field belongs in the field registry and field adapter; a mutation belongs in a focused server service; a cross-step browser workflow belongs in an action or modal module.

Known pressure points:

- the route and action coordinators are still large because this page combines several workflows;
- the editor supports both single-record and bulk transaction shapes;
- source save, public build, and remote media publication are deliberately separate failure boundaries even when `Save` composes them;
- the focused Work projection contains generated context as well as canonical data, so the canonical record must remain the stale-write baseline.

The route exposes the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state) contract on `#catalogueWorkRoot`. Focused smoke coverage begins in `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`; use the code and tests for the exact current field and endpoint inventory.
