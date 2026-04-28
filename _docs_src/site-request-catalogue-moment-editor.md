---
doc_id: site-request-catalogue-moment-editor
title: "Catalogue Moment Editor Request"
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: change-requests
sort_order: 150
---
# Catalogue Moment Editor Request

Status:

- implemented in first pass

## Summary

This change request covers the missing first-class Studio editor for existing moment records.

Moments now have the same core source pieces as the rest of the catalogue:

- metadata in `assets/studio/data/catalogue/moments.json`
- prose in `_docs_src_catalogue/moments/<moment_id>.md`
- staged prose import from `var/docs/catalogue/import-staging/moments/`
- local image generation through `var/catalogue/media/moments/`
- public runtime payloads under `_moments/`, `assets/moments/index/`, and `assets/data/moments_index.json`

The remaining gap is a normal edit page for reopening an existing moment, changing metadata, checking prose/media readiness, and running the scoped rebuild.

## Goal

Add a Studio route:

- `/studio/catalogue-moment/?moment=<moment_id>`

The page should let the user edit existing moment metadata without reusing the import page as a general-purpose editor.

The target workflow should feel consistent with the current work, work-detail, and series editors:

- search/open one moment by `moment_id`
- edit canonical source metadata
- save source JSON only
- optionally update the public site immediately
- preview scoped rebuild impact
- show prose readiness
- import staged prose when needed
- show source image/media readiness
- trigger local thumbnail/srcset generation through the existing scoped build path

## Current State

Current moment workflows:

- `/studio/catalogue-moment-import/` creates or updates a moment from one explicit staged Markdown file plus submitted metadata
- moment import writes body-only prose into `_docs_src_catalogue/moments/`
- moment import writes metadata into `assets/studio/data/catalogue/moments.json`
- `catalogue_json_build.py --moment-file <moment_id>.md` rebuilds the moment, media, and catalogue search
- `/studio/catalogue/` links to `Import Moment`

Current gap:

- there is no `/studio/catalogue-moment/` route
- the dashboard has no `Edit Moment` entry
- existing moments cannot be reopened in a purpose-built editor
- metadata edits require the import page or direct JSON editing
- prose/media readiness is not visible for an existing moment outside the import flow

## Proposed Direction

Create a dedicated moment editor rather than stretching the import page.

The import page should remain the workflow for introducing or replacing a moment from a staged prose file. The edit page should be the workflow for routine maintenance of a moment that already exists in canonical metadata.

The first implementation should not add browser-side prose editing. Prose changes should use the same explicit staged import pattern already established for work, series, and moment imports.

The first implementation should not upload primary images to remote media storage. Local generation should continue to stage primary derivatives under `var/catalogue/media/moments/`.

## Source Contract

Canonical metadata:

- `assets/studio/data/catalogue/moments.json`

Canonical prose:

- `_docs_src_catalogue/moments/<moment_id>.md`

Staged prose:

- `var/docs/catalogue/import-staging/moments/<moment_id>.md`

Local media staging:

- `var/catalogue/media/moments/make_srcset_images/<moment_id>.<ext>`
- `var/catalogue/media/moments/srcset_images/`

Published thumbnail assets:

- `assets/moments/img/<moment_id>-thumb-96.webp`
- `assets/moments/img/<moment_id>-thumb-192.webp`

Generated runtime artifacts:

- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- `assets/data/search/catalogue/index.json`

## Initial Editable Fields

The first editor should support the fields already used by the import page:

- `title`
- `status`
- `date`
- `date_display`
- `published_date`
- `source_image_file`
- `image_alt`

Derived/read-only context should include:

- `moment_id`
- public URL
- generated page status
- generated JSON status
- moments index membership
- source image status
- local media status
- prose source status

## User Flow

Single-record edit flow:

1. User opens `/studio/catalogue-moment/`.
2. User searches for a `moment_id` or arrives with `?moment=<moment_id>`.
3. Page loads canonical moment metadata from `assets/studio/data/catalogue/moments.json`.
4. Page loads generated/runtime context when available.
5. Page shows current metadata fields.
6. Page shows canonical prose source readiness for `_docs_src_catalogue/moments/<moment_id>.md`.
7. Page shows staged prose readiness for `var/docs/catalogue/import-staging/moments/<moment_id>.md`.
8. Page shows media readiness for the configured `source_image_file`.
9. User saves metadata.
10. Server writes `moments.json` with a normal catalogue backup.
11. Page offers `Update site now` when runtime output is pending.
12. Scoped update runs local media generation, moment generation, and catalogue search rebuild.

Staged prose flow:

1. User places body-only Markdown at `var/docs/catalogue/import-staging/moments/<moment_id>.md`.
2. Page shows `Import staged prose` when the staged file is valid.
3. User confirms overwrite when permanent prose already exists and differs.
4. Server writes `_docs_src_catalogue/moments/<moment_id>.md`.
5. Page marks the moment as needing a scoped update.

## Non-Goals

Out of scope for the first implementation:

- browser-side prose editing
- creating new moments without the import page
- deleting moments
- bulk moment editing
- remote/R2 primary image upload
- image upload or image file browsing from the browser
- changing public moment JSON schema
- changing public moment layout behavior
- scanning external moment folders

## Benefits

Expected benefits:

- existing moments become maintainable through Studio instead of direct JSON edits
- moment metadata edits use the same save/rebuild mental model as works and details
- prose and media readiness become visible outside the import flow
- moment import can stay focused on staged-file ingestion
- future delete/bulk/edit-prose work has a natural route to extend

## Risks And Tradeoffs

Main risks:

- this adds another Studio editor surface and should reuse existing editor patterns rather than inventing a moment-specific UI system
- moment prose is required for publishable moments, so the editor needs clear readiness states
- source image edits can make media generation pending or blocked
- save-only metadata changes may leave generated runtime output stale until the scoped update runs

The main tradeoff is between a narrow metadata editor and a full prose/media authoring tool.

This request chooses the narrow editor first so the existing source contracts are editable without bundling a larger authoring system into the same change.

## Proposed Implementation Tasks

### Task 1. Define Moment Editor Route And Docs

Status:

- ready

Create the route shell and documentation hooks:

- add `studio/catalogue-moment/index.md`
- set permalink to `/studio/catalogue-moment/`
- add a page doc such as `_docs_src/catalogue-moment-editor.md`
- add the route to `studio_config.json` route lookup
- add an `Edit Moment` link to `/studio/catalogue/`
- add the editor doc to the User Guide list
- add the route to Studio runtime/docs references where route inventories are maintained

Acceptance checks:

- `/studio/catalogue-moment/` renders in the Studio shell
- the catalogue dashboard links to the page
- the page links to its docs-viewer reference

### Task 2. Add Moment Lookup And Save Endpoints

Status:

- ready

Extend `scripts/studio/catalogue_write_server.py` with moment editor endpoints.

Recommended endpoints:

- `POST /catalogue/moment/preview`
- `POST /catalogue/moment/save`

The endpoints should:

- validate `moment_id`
- load and normalize the current metadata record
- validate editable metadata fields
- use expected-record-hash stale-write protection
- write `assets/studio/data/catalogue/moments.json`
- create normal catalogue JSON backups
- return changed fields, record hash, normalized record, and rebuild-needed state
- keep moment prose writes separate from metadata save

Acceptance checks:

- save rejects unknown fields
- save rejects stale hashes
- save writes only `moments.json`
- dry-run mode reports intended writes without modifying files

### Task 3. Add Moment Build Preview And Apply Support

Status:

- ready

Reuse the existing scoped build path:

- `build_scope_for_moment(...)`
- `run_moment_scoped_build(...)`
- `catalogue_json_build.py --moment-file <moment_id>.md`

The editor should be able to preview and apply:

- local media generation
- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- catalogue search rebuild

Acceptance checks:

- preview reports local media counts and prose readiness
- apply runs the scoped moment build
- missing image source blocks only the media step
- missing required prose blocks publishable moment updates

### Task 4. Add Staged Prose Import Action

Status:

- ready

Reuse the moment import validation behavior for an editor-local action.

The editor should:

- check `var/docs/catalogue/import-staging/moments/<moment_id>.md`
- validate body-only Markdown
- reject front matter
- accept existing `<pre class="moment-text">...</pre>` wrappers
- compare against `_docs_src_catalogue/moments/<moment_id>.md`
- require overwrite confirmation when needed
- write the permanent prose source without changing metadata

Acceptance checks:

- missing staged prose is shown as a readiness state
- valid staged prose enables `Import staged prose`
- overwrite confirmation is required for changed existing prose
- metadata JSON is not changed by prose import

### Task 5. Build The Moment Editor Frontend

Status:

- ready

Create a dedicated JS module, likely:

- `assets/studio/js/catalogue-moment-editor.js`

The frontend should follow existing catalogue editor patterns:

- single-record search/open
- `?moment=<moment_id>` URL state
- canonical source baseline
- dirty-state tracking
- save-only and `Update site now` flows
- metadata field validation
- current runtime summary rail
- prose readiness panel
- media readiness panel
- result/status messaging through `studio_config.json` copy

Acceptance checks:

- edit/save round trip works for a draft test moment
- unchanged save is a no-op
- stale write conflict is visible and recoverable
- `Update site now` shows nested build/media/search results
- mobile layout remains usable

### Task 6. Update Navigation, Docs, And Generated Docs Data

Status:

- ready

Update supporting docs and generated payloads:

- Studio route inventory
- User Guide index
- Catalogue dashboard docs
- Catalogue write server docs
- Scoped catalogue build docs if endpoint behavior changes
- Studio config/save-flow docs
- Site change log
- generated docs payloads under `assets/data/docs/scopes/studio/`
- Studio docs search payload

Acceptance checks:

- `./scripts/build_docs.rb --scope studio --write`
- `./scripts/build_search.rb --scope studio --write`
- Jekyll build passes

### Task 7. Verification Pass

Status:

- ready

Run targeted checks:

- Python syntax check for changed scripts
- write-server dry-run smoke for moment preview/save
- write-server dry-run smoke for staged prose import
- scoped moment build preview
- scoped moment build dry-run
- browser smoke for `/studio/catalogue-moment/` on desktop and mobile
- sanitization scan for changed files

Manual checks:

- open an existing moment
- edit metadata and save
- import staged prose
- run `Update site now`
- confirm public moment page and `/series/` moments mode show expected metadata/image state
