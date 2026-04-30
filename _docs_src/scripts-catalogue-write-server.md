---
doc_id: scripts-catalogue-write-server
title: "Catalogue Write Server"
added_date: 2026-04-22
last_updated: 2026-04-30
parent_id: scripts
sort_order: 100
---
# Catalogue Write Server

Script:

```bash
./scripts/studio/catalogue_write_server.py
```

## Optional Flags

- `--port 8788`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--dry-run`: validate and return a response without writing source JSON

## Endpoints And Behavior

Exposed endpoints:

- `GET /health`
- `GET /catalogue/read?key=<studio_config_data_key>[&record_id=<id>]`
- `POST /catalogue/bulk-save`
- `POST /catalogue/delete-preview`
- `POST /catalogue/delete-apply`
- `POST /catalogue/publication-preview`
- `POST /catalogue/publication-apply`
- `POST /catalogue/work/create`
- `POST /catalogue/work/save`
- `POST /catalogue/work-detail/create`
- `POST /catalogue/work-detail/save`
- `POST /catalogue/import-preview`
- `POST /catalogue/import-apply`
- `POST /catalogue/series/create`
- `POST /catalogue/series/save`
- `POST /catalogue/build-preview`
- `POST /catalogue/build-apply`
- `POST /catalogue/prose/import-preview`
- `POST /catalogue/prose/import-apply`
- `POST /catalogue/moment/preview`
- `POST /catalogue/moment/save`
- `POST /catalogue/moment/import-preview`
- `POST /catalogue/moment/import-apply`
- `POST /catalogue/project-state-report`

The current implementation can serve allowlisted catalogue source and lookup payloads for Studio, can create draft work, work-detail, and series records, can import new work/work-detail records from the configured bulk-import workbook, can import staged work/series/moment prose Markdown into repo-local catalogue prose source files, can bulk-save existing work/work-detail records, saves existing work/work-detail/series/moment records in canonical catalogue source JSON, can run a scoped JSON-source rebuild for one work, one series, or one moment scope, can apply shared publication preview/apply actions for works, work details, series, and moments, and can write the local project-state report. It does not write back into Excel.

`GET /catalogue/read` is the server-backed read path for mutable catalogue editor data. It accepts the same logical keys used by `studio_config.json`, including:

- `catalogue_works`
- `catalogue_work_details`
- `catalogue_series`
- `catalogue_moments`
- `catalogue_lookup_work_search`
- `catalogue_lookup_series_search`
- `catalogue_lookup_work_detail_search`
- `catalogue_lookup_work_base` with `record_id=<work_id>`
- `catalogue_lookup_work_detail_base` with `record_id=<detail_uid>`
- `catalogue_lookup_series_base` with `record_id=<series_id>`

Reads are allowlisted by key. They do not expose arbitrary repository paths. The source payloads come from canonical catalogue JSON, and lookup payloads are built from the current source records for the request. This lets Studio treat catalogue source/lookup data as local service-backed workspace data while Jekyll excludes `assets/studio/data/catalogue/` and `assets/studio/data/catalogue_lookup/` from its served source tree.

`POST /catalogue/project-state-report` accepts:

```json
{
  "include_subfolders": false
}
```

It runs `./scripts/project_state_report.py` through its shared Python entrypoint. It writes `_docs_src/project-state.md` unless the server was started with `--dry-run`, and returns summary counts plus the report path. `include_subfolders` defaults to `false`; default mode counts every direct `/projects/<project_folder>` folder. When true, the report also includes `/projects/<project_folder>/<sub-folder>` directories while still skipping detail folders.

`POST /catalogue/bulk-save` expects:

```json
{
  "kind": "works",
  "ids": ["00001", "00002", "00003"],
  "expected_record_hashes": {
    "00001": "sha256-a",
    "00002": "sha256-b",
    "00003": "sha256-c"
  },
  "set_fields": {
    "status": "draft",
    "storage_location": "rack-3"
  },
  "series_operation": {
    "mode": "add_remove",
    "add_series_ids": ["026"],
    "remove_series_ids": ["009"]
  }
}
```

Request behavior:

- `kind` must be `works` or `work_details`
- `ids` must be a non-empty array of normalized target ids
- `expected_record_hashes` may include one hash per selected id for stale-write protection
- `set_fields` may include only the bulk-editable fields for that record kind
- work bulk save may also include `series_operation`
- work bulk `series_operation.mode` may be `replace` or `add_remove`
- the server validates the combined source write before writing the canonical JSON file once
- successful response includes changed counts, changed ids, normalized changed records, and public-update targets
- optional `apply_build: true` runs the same scoped update sequence immediately for changed work records whose saved status is `published`; draft work changes remain source-only
- nested build status includes any remaining published targets when that update sequence fails part-way through

`POST /catalogue/delete-preview` expects:

```json
{
  "kind": "work",
  "work_id": "00002"
}
```

or:

```json
{
  "kind": "work_detail",
  "detail_uid": "00001-001"
}
```

or:

```json
{
  "kind": "series",
  "series_id": "026"
}
```

or:

```json
{
  "kind": "moment",
  "moment_id": "keys"
}
```

Request behavior:

- returns a delete summary, affected records, blockers, and validation errors
- work delete preview includes dependent detail/file/link source records
- work delete blocks when the work is still used as `primary_work_id` by a published series
- work delete clears `primary_work_id` when a draft series points at the deleted work
- series delete preview includes affected member works
- work, work-detail, and series delete previews include generated artifact, repo-local media, public JSON update, Studio JSON update, and catalogue search impact where relevant
- moment delete preview covers the canonical source metadata record plus generated moment artifacts, repo/local media cleanup, moments index update, and catalogue search rebuild

`POST /catalogue/delete-apply` accepts the same shape plus optional `expected_record_hash` and then:

- re-runs delete preview and blocks when preview is not clean
- writes the canonical source JSON files needed for that delete
- for work deletes, removes generated work artifacts, generated dependent detail artifacts, published thumbnails, repo-local staged media, stale public index/search records, per-work tag overrides, and work-storage index entries, and clears draft-series `primary_work_id` references to the deleted work
- for work-detail deletes, removes generated detail artifacts, published thumbnails, repo-local staged media, and the deleted detail from the parent work runtime JSON
- for series deletes, removes generated series artifacts, removes the series from affected work runtime/index records, removes the series tag-assignment row, updates recent/public indexes, and rebuilds catalogue search
- for moment deletes, removes generated moment page/json artifacts, published thumbnails, and repo-local staged media
- for moment deletes, removes the moment from `assets/data/moments_index.json` and rebuilds catalogue search so the search record disappears
- refreshes derived lookup payloads after non-dry-run writes
- records one aggregated Catalogue Activity entry for the delete operation

After successful canonical writes, the server also refreshes the derived Studio lookup payloads under `assets/studio/data/catalogue_lookup/`.

`POST /catalogue/publication-preview` expects:

```json
{
  "kind": "series",
  "action": "unpublish",
  "series_id": "001",
  "expected_record_hash": "optional-current-record-sha256"
}
```

Supported `kind` values are `work`, `work_detail`, `series`, and `moment`. Supported `action` values are:

- `publish`: change source status from `draft` to `published` and run the scoped public update
- `unpublish`: change source status from `published` to `draft` and clean generated public artifacts
- `save_published`: save metadata for a currently published record and then run the scoped public update

Preview behavior:

- returns current and target status, current and target record hashes, changed fields, affected ids, blockers, and validation errors
- reports source-write impact separately from internal public impact
- reports scoped public-update impact for `publish` and `save_published`
- reports generated artifact cleanup and public index/search impact for `unpublish`
- for series `publish`, reports attached draft work ids that will be promoted to `published`
- for `save_published`, the request must include the same partial `record` shape as the matching source save endpoint and must not change publication status

`POST /catalogue/publication-apply` accepts the same request shape and then:

- re-runs publication preview before writing
- honors `expected_record_hash` for stale-write protection
- writes the id-scoped source status or metadata update
- when publishing a series, writes the series status and all attached draft-work status promotions atomically across `series.json` and `works.json`
- refreshes Studio lookup payloads after non-dry-run source writes
- runs the scoped public update for `publish` and `save_published`
- runs deterministic generated-artifact cleanup for `unpublish`
- returns `status: "public_update_failed"` when a source write succeeds but the internal public update fails
- records Catalogue Activity with `publication` operation names such as `series.publish`, `series.unpublish`, and `series.save_published`
- moment `unpublish` also removes generated moment page/json artifacts, published thumbnails, repo-local staged media, the `assets/data/moments_index.json` entry, and the catalogue search record

Standalone work publish remains stricter than series bootstrap publish: `work.publish` is blocked unless the work already belongs to at least one published series. Publishing a series is the bootstrap path for a new draft series with draft member works.

`POST /catalogue/work/save` expects:

```json
{
  "work_id": "00001",
  "expected_record_hash": "optional-current-record-sha256",
  "record": {
    "title": "Updated title",
    "status": "draft",
    "series_ids": ["009"]
  }
}
```

Request behavior:

- `work_id` is normalized to a five-digit work id
- optional `apply_build: true` requests a same-scope site update as part of the save response when the saved work status is `published`
- if `apply_build: true` is submitted for a draft work, the source save still succeeds but the public build request is skipped
- `record` may be a partial update, but all keys must be known work source fields
- `record.work_id`, when present, must match `work_id`
- `series_ids` may be an array or comma-separated value and is normalized through the shared series-id rules
- `status` is lowercased and blank status is stored as `null`
- unknown fields are rejected
- missing work IDs are rejected
- `expected_record_hash`, when provided, must match the current stored record hash or the server returns `409 Conflict`

Successful responses include:

- `work_id`
- `changed`
- `changed_fields`
- `record_hash`
- `record`
- `lookup_refresh` when the request changed the record
- `saved_at_utc` when a non-dry-run write changed the source file
- `backups` when a non-dry-run write changed the source file

`POST /catalogue/prose/import-preview` expects either:

```json
{
  "target_kind": "work",
  "work_id": "00008"
}
```

or:

```json
{
  "target_kind": "series",
  "series_id": "067"
}
```

Request behavior:

- `target_kind` must be `work` or `series`
- work ids normalize to five digits and series ids normalize to three digits
- the target work or series must exist in the canonical catalogue source JSON
- work prose is staged at `var/docs/catalogue/import-staging/works/<work_id>.md`
- series prose is staged at `var/docs/catalogue/import-staging/series/<series_id>.md`
- the preview validates UTF-8 Markdown and rejects prose files with front matter
- the preview reports whether the permanent target already exists and whether overwrite confirmation is required

`POST /catalogue/prose/import-apply` accepts the same request shape plus:

```json
{
  "confirm_overwrite": true
}
```

Apply behavior:

- re-runs the same preview validation before writing
- writes work prose to `_docs_src_catalogue/works/<work_id>.md`
- writes series prose to `_docs_src_catalogue/series/<series_id>.md`
- refuses to overwrite different existing permanent prose content unless `confirm_overwrite` is true
- intentionally does not create backup files for this prose import flow
- records Catalogue Activity when a non-dry-run import writes changed prose

## Scoped Build Media

`POST /catalogue/build-preview`, `POST /catalogue/build-apply`, and the shared publication apply path use the scoped JSON catalogue build helper for work, work-detail, and moment media tasks.

For work, work-detail, and moment scopes, the build helper:

- resolves the source image from canonical catalogue JSON and `DOTLINEFORM_PROJECTS_BASE_DIR`
- copies the source image into `var/catalogue/media/<kind>/make_srcset_images/` using the public catalogue id as the filename stem
- generates primary and thumbnail srcset derivatives into `var/catalogue/media/<kind>/srcset_images/`
- copies generated thumbnail derivatives into `assets/works/img/`, `assets/work_details/img/`, or `assets/moments/img/`
- leaves generated primary derivatives staged under `var/catalogue/media/` for remote media publishing

The write server reports generated/current/blocked media ids in the nested build response. It does not upload primary images to R2.

`POST /catalogue/build-apply` also accepts `media_only: true` for work, work-detail, and moment image refreshes. In media-only mode the helper stages the configured source image, regenerates local thumbnails and staged primary variants, and then stops before page/json generation and catalogue search. Studio sends `force: true` for the readiness-panel refresh action so the derivatives are regenerated even when current output timestamps already look fresh.

## Moment Import

`POST /catalogue/moment/save` saves existing moment metadata in `assets/studio/data/catalogue/moments.json`. Optional `apply_build: true` requests the same-scope public update only when the saved moment status is `published`; draft moment saves remain source-only and return a `build_skipped` reason if a public update was requested.

`POST /catalogue/moment/import-preview` expects:

```json
{
  "moment_file": "keys.md",
  "metadata": {
    "title": "keys",
    "status": "draft",
    "published_date": "",
    "date": "2024-01-01",
    "date_display": "",
    "source_image_file": "",
    "image_alt": ""
  }
}
```

Request behavior:

- `moment_file` must be a filename-only slug-safe Markdown filename
- staged prose is resolved from `var/docs/catalogue/import-staging/moments/<moment_id>.md`
- permanent prose target is `_docs_src_catalogue/moments/<moment_id>.md`
- metadata is validated from the submitted metadata plus any existing `assets/studio/data/catalogue/moments.json` record
- submitted import status is normalized to `draft`; publishing happens through `POST /catalogue/publication-apply` after import
- staged prose must be body-only Markdown and must not contain canonical metadata front matter
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration

`POST /catalogue/moment/import-apply` accepts the same request shape.

Apply behavior:

- writes body-only prose to `_docs_src_catalogue/moments/<moment_id>.md`
- writes canonical draft moment metadata to `assets/studio/data/catalogue/moments.json`
- creates the normal catalogue JSON backup bundle for the metadata write
- does not run local media generation, the scoped moment generator, or the catalogue search rebuild
- records Catalogue Activity when a non-dry-run import writes source

## Derived Lookup Refresh

Current behavior after successful canonical writes:

- the server refreshes the derived Studio lookup payloads under `assets/studio/data/catalogue_lookup/`
- `POST /catalogue/work/save` now uses the invalidation registry for the first live incremental slice
- when the changed work fields stay within the locked `single-record` first-pass set, the server rewrites only `works/<work_id>.json`
- when work changes resolve to `targeted-multi-record`, the server rewrites only the focused derived payload set needed for those fields
- `POST /catalogue/work-detail/save` and `POST /catalogue/series/save` now also use focused incremental refresh where their dependency set is explicit
- other writes still use a full lookup refresh

Why the current refresh is broad:

- a single source edit can affect more than one derived lookup family
- work saves can affect:
  - the focused work lookup record
  - work search
  - series member summaries
  - detail summaries
  - work-owned download/link summaries
- series saves can affect:
  - the focused series lookup record
  - series search
  - member-work summaries across related work records
- moments are part of the wider catalogue surface too, but their derived artifacts are:
  - `assets/moments/index/<moment_id>.json`
  - `assets/data/moments_index.json`
  - catalogue search entries built from `assets/data/moments_index.json`
  - they currently have no cross-record dependency graph comparable to work/series membership

Follow-on direction:

- keep full lookup refresh as the fallback for complex cases
- add field-based invalidation for obvious quick wins where only one record or a small known dependency set changes
- the canonical invalidation registry currently lives in the write-server code by design
- keep that registry in code unless a second consumer appears that justifies a shared JSON/config contract
- the current dependency mapping now also explicitly includes moments, with `title`, `date`, and `date_display` treated as the fields that currently affect both moment runtime data and catalogue search
- the current registry maps detail and series fields to their actual derived outputs:
  - detail fields can affect `work_details/<detail_uid>.json`, `work_detail_search.json`, and related work lookup records
  - series fields can affect `series/<series_id>.json`, `series_search.json`, and related work lookup records where `series_summary` embeds the series title
  - work-owned `downloads` and `links` changes refresh the focused work lookup record through the work-save path
- the locked first live incremental slice is narrower than the full registry:
  - start with `POST /catalogue/work/save` only
  - allow incremental writes only for work fields currently classified as `single-record`
  - work `title`, `year_display`, `status`, and `series_ids` now use the targeted-multi-record path rather than `full`
  - detail and series saves now also use targeted incremental refresh where their dependency set is explicit
  - keep parent/id move-style cases and moment writes on `full` fallback until later tasks
- changed work-save responses now include `lookup_refresh.mode` so the UI and local operators can tell whether the server used `single-record`, `targeted-multi-record`, or `full`
- changed detail/series save responses now include the same `lookup_refresh` metadata
- track that work in [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

Likely full-refresh fallback cases for the first incremental phase:

- `POST /catalogue/bulk-save`
- `POST /catalogue/delete-apply`
- `POST /catalogue/import-apply`
- create flows that introduce new ids or new parent/child membership
- mixed-field writes where dependency scope is not yet explicitly implemented

`POST /catalogue/work/create` expects:

```json
{
  "work_id": "01942",
  "record": {
    "title": "New draft work",
    "status": "draft",
    "series_ids": ["009"],
    "project_folder": "2026/new-work",
    "project_filename": "new-work.jpg"
  }
}
```

Request behavior:

- `work_id` must not already exist
- blank or missing `status` is normalized to `draft`
- `title` is required
- `series_ids` may be an array or comma-separated value
- media/prose path fields are stored as source metadata only; the server does not copy media files

`POST /catalogue/work-detail/save` expects:

```json
{
  "detail_uid": "00001-001",
  "expected_record_hash": "optional-current-record-sha256",
  "record": {
    "detail_uid": "00001-001",
    "work_id": "00001",
    "detail_id": "001",
    "title": "Updated detail title",
    "project_subfolder": "details",
    "project_filename": "updated-detail.jpg",
    "status": "draft"
  }
}
```

Request behavior:

- `detail_uid` must resolve to an existing canonical detail record
- optional `apply_build: true` requests a parent-work site update as part of the save response
- `record` may be partial, but all keys must be known work-detail source fields
- `record.detail_uid`, `record.work_id`, and `record.detail_id` must remain consistent with the target record
- the parent `work_id` must exist in canonical source JSON
- `expected_record_hash`, when provided, must match the current stored detail hash or the server returns `409 Conflict`

`POST /catalogue/work-detail/create` expects:

```json
{
  "work_id": "01942",
  "detail_id": "001",
  "record": {
    "title": "Detail title",
    "project_subfolder": "details",
    "project_filename": "detail-001.jpg",
    "status": "draft"
  }
}
```

Request behavior:

- parent `work_id` must already exist
- parent `work_id` must already be published
- `detail_id` must be unique within that work
- blank or missing `status` is normalized to `draft`
- `title` is required
- the server derives and validates the normalized `detail_uid`

Bulk workbook imports in `work_details` mode apply the same parent-published rule. Rows whose parent work is still draft are blocked in preview with `parent_work_unpublished`.

`POST /catalogue/import-preview` expects:

```json
{
  "mode": "works"
}
```

or:

```json
{
  "mode": "work_details"
}
```

Request behavior:

- workbook source is configured through `_data/pipeline.json` and currently resolves to `data/works_bulk_import.xlsx`
- `works` mode previews new work records only
- `work_details` mode previews new detail records only
- existing source records are counted as duplicates and skipped
- blocked workbook rows are reported with reasons
- preview does not write source JSON

`POST /catalogue/import-apply` accepts the same shape and then:

- re-runs the preview plan against the configured workbook path
- rejects apply when blocked workbook rows remain
- writes only importable new records into canonical source JSON
- refreshes derived lookup payloads after non-dry-run writes
- writes one aggregated Catalogue Activity entry that records import counts rather than one entry per imported record

Work-owned files and links are saved through `POST /catalogue/work/save` as the work record's `downloads` and `links` arrays. The standalone work-file and work-link write endpoints are retired and return `410 Gone`.

Request behavior:

- parent `work_id` must already exist
- blank or missing `status` is normalized to `draft`
- `url` and `label` are required
- the server derives and validates the normalized `link_uid`

`POST /catalogue/series/save` expects:

```json
{
  "series_id": "009",
  "expected_record_hash": "optional-current-record-sha256",
  "record": {
    "title": "Updated series title",
    "year": 2026,
    "year_display": "2026",
    "primary_work_id": "00001",
    "sort_fields": "work_id"
  },
  "work_updates": [
    {
      "work_id": "00001",
      "series_ids": ["009", "031"],
      "expected_record_hash": "optional-current-work-sha256"
    }
  ]
}
```

Request behavior:

- `series_id` must resolve to an existing canonical series record
- optional `apply_build: true` requests a same-scope site update as part of the save response when the saved series status is `published`
- `year` and `year_display` are required for the saved series record
- `work_updates` is limited to changed membership rows for affected works
- each changed work keeps the submitted `series_ids` order; the server does not sort it
- draft source saves may omit `primary_work_id`
- `primary_work_id`, when present, must still be a member of the series after the proposed membership writes
- `primary_work_id` is required for publication, not for draft create/save
- the server validates the full source set before writing `series.json` and `works.json`
- if `apply_build: true` is submitted for a draft series, the source save still succeeds but the public build request is skipped

`POST /catalogue/series/create` expects:

```json
{
  "series_id": "099",
  "record": {
    "title": "New draft series",
    "series_type": "primary",
    "status": "draft",
    "year": 2026,
    "year_display": "2026",
    "sort_fields": "work_id"
  }
}
```

Request behavior:

- `series_id` must not already exist
- blank or missing `status` is normalized to `draft`
- `year` and `year_display` are required
- draft creates may omit `primary_work_id`
- the server writes the new source record, refreshes derived lookup payloads, and returns the normalized saved record

`POST /catalogue/build-preview` expects either a work-scoped or series-scoped request.

Work-scoped request:

```json
{
  "work_id": "00001",
  "extra_series_ids": ["004"]
}
```

Series-scoped request:

```json
{
  "series_id": "009",
  "extra_work_ids": ["00001"]
}
```

It returns the planned scoped build:

- `work_ids`
- `series_ids`
- `generate_only`
- `rebuild_search`
- `summary`

Scoped build preconditions:

- any series included in the requested build scope must have `status: published`
- any series included in the requested build scope must have a valid `primary_work_id`
- that primary work must be a published work and must include the series in its `series_ids`
- draft series can be saved in source JSON, but build preview/apply and save-time `apply_build` do not publish them

`POST /catalogue/build-apply` accepts the same shapes and then runs:

- `generate_work_pages.py --internal-json-source-run --refresh-published` for the selected work and affected series ids
- or `generate_work_pages.py --internal-json-source-run --refresh-published` for the selected series and affected works
- `build_search.rb --scope catalogue --write`

The apply path uses refresh mode rather than broad force mode. That allows selected published records to be recomputed while unchanged generated payloads and catalogue search output still skip by content version. A request-level `force` value remains the explicit stronger rewrite path.

The apply endpoint updates:

- `assets/studio/data/build_activity.json`
- `assets/studio/data/catalogue_activity.json`

## Validation

The server validates the proposed update through the shared catalogue source loader and validator before writing. Validation checks the full catalogue source set, not only the submitted work record, so invalid series references are blocked before `works.json` is replaced.

## Security Constraints

- binds to `127.0.0.1` only
- CORS allows loopback origins only
- write target is allowlisted to canonical catalogue source JSON files under `assets/studio/data/catalogue/`
- current save endpoints write only canonical catalogue source JSON under `assets/studio/data/catalogue/`, including `works.json`, `work_details.json`, `series.json`, and `moments.json`
- standalone work-file and work-link write endpoints are retired; files and links are saved as work-owned metadata through `POST /catalogue/work/save`
- timestamped backup bundles are created under `var/studio/catalogue/backups/`
- event logs are written under `var/studio/catalogue/logs/`
- logs include IDs, changed fields, status, and error summaries only; they do not include full submitted records
- source-save and validation-failure events also update `assets/studio/data/catalogue_activity.json` for the Studio Catalogue Activity page
- scoped rebuild apply events also update both Studio activity feeds

## Dev Studio

`bin/dev-studio` starts this service alongside Jekyll and the Tag Write Server.

Default local endpoint:

```text
http://127.0.0.1:8788
```

The port can be overridden for the dev launcher:

```bash
CATALOGUE_WRITE_PORT=8798 bin/dev-studio
```

## Source And Target Artifacts

Source JSON:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`

Studio activity feed:

- `assets/studio/data/catalogue_activity.json`

Backup target:

- `var/studio/catalogue/backups/`

Derived lookup target:

- `assets/studio/data/catalogue_lookup/`

Operational log target:

- `var/studio/catalogue/logs/catalogue_write_server.log`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Catalogue Source Export](/docs/?scope=studio&doc=scripts-catalogue-source)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
