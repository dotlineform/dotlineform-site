---
doc_id: scripts-catalogue-write-server-build-lookup
title: Catalogue Write Server Build And Lookup
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: scripts-catalogue-write-server
sort_order: 4200
---
# Catalogue Write Server Build And Lookup

## Scoped Build Media

`POST /catalogue/build-preview`, `POST /catalogue/build-apply`, and the shared publication apply path use the scoped JSON catalogue build helper for work, work-detail, and moment media tasks.

For work, work-detail, and moment scopes, the build helper:

- resolves the source image from canonical catalogue JSON and `DOTLINEFORM_PROJECTS_BASE_DIR`
- copies the source image into `var/catalogue/media/<kind>/make_srcset_images/` using the public catalogue id as the filename stem
- generates primary and thumbnail srcset derivatives into `var/catalogue/media/<kind>/srcset_images/`
- copies generated thumbnail derivatives into `assets/works/img/`, `assets/work_details/img/`, or `assets/moments/img/`
- removes staged thumbnail derivatives after the asset-folder copy succeeds
- leaves generated primary derivatives staged under `var/catalogue/media/` for remote media publishing

The write server reports generated/current/blocked media ids in the nested build response. It does not upload primary images to R2.

`POST /catalogue/build-apply` also accepts `media_only: true` for work, work-detail, and moment image refreshes. In media-only mode the helper stages the configured source image, regenerates local thumbnails and staged primary variants, and then stops before page/json generation and catalogue search. Studio sends `force: true` for the readiness-panel refresh action so the derivatives are regenerated even when current output timestamps already look fresh.

## Moment Import

`POST /catalogue/moment/save` saves existing moment metadata in `assets/studio/data/catalogue/moments.json`. Optional `apply_build: true` requests the same-scope public update only when the saved moment status is `published`; draft moment saves remain source-only and return a `build_skipped` reason if a public update was requested. Changed moment-save responses report `moment_build_invalidation` for moment runtime/search build planning; they do not use `lookup_refresh` because moments do not write Studio catalogue lookup payloads.

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
- permanent prose target is `_docs_catalogue/moments/<moment_id>.md`
- metadata is validated from the submitted metadata plus any existing `assets/studio/data/catalogue/moments.json` record
- submitted import status is normalized to `draft`; publishing happens through `POST /catalogue/publication-apply` after import
- staged prose is imported as Markdown body source
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration

`POST /catalogue/moment/import-apply` accepts the same request shape.

Apply behavior:

- writes body-only prose to `_docs_catalogue/moments/<moment_id>.md`
- writes canonical draft moment metadata to `assets/studio/data/catalogue/moments.json`
- creates the normal catalogue JSON backup bundle for the metadata write
- does not run local media generation, the scoped moment generator, or the catalogue search rebuild
- records Studio Activity when a non-dry-run import writes source
- when the request includes valid Studio activity context from `/studio/catalogue-moment/`, writes one unified Studio activity row for `import-source-data`

## Derived Lookup Refresh

Current behavior after successful canonical writes:

- the server refreshes the derived Studio lookup payloads under `assets/studio/data/catalogue_lookup/`
- single work, work-detail, and series saves first use the catalogue field registry to decide whether `studio-lookup` is affected
- `studio/services/catalogue/catalogue_lookup_refresh.py` derives the precise lookup write set from current serializer dependencies in `studio/services/catalogue/catalogue_lookup.py`
- when the changed fields affect only the focused lookup record, the server rewrites only that record file
- when changes affect search payloads or related summaries, the server rewrites only the focused derived payload set needed for those fields
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
- keep the catalogue field registry as the authority for whether a changed field affects `studio-lookup`
- keep serializer field descriptors beside the lookup payload builders, so lookup precision follows the payload contract instead of a second field-to-invalidation registry
- the current moment-build dependency mapping remains separate because moment save artifacts are runtime/search outputs, not Studio lookup payloads
  - series fields can affect `series/<series_id>.json`, `series_search.json`, and related work lookup records where `series_summary` embeds the series title
  - work-owned `downloads` and `links` changes refresh the focused work lookup record through the work-save path
- refresh execution lives in `studio/services/catalogue/catalogue_lookup_refresh.py`, which calls the existing `studio/services/catalogue/catalogue_lookup.py` builders and writers and returns the Studio-facing `lookup_refresh` result payload shape
- single work, work-detail, and series saves all use registry-derived lookup refresh planning
- keep parent/id move-style or mixed-class cases on `full` fallback until later tasks
- changed work-save responses now include `lookup_refresh.mode` so the UI and local operators can tell whether the server used `single-record`, `targeted-multi-record`, or `full`
- changed detail/series save responses now include the same `lookup_refresh` metadata
- changed moment-save responses include `moment_build_invalidation` instead of `lookup_refresh`; moment publication and delete flows do not emit or perform Studio lookup refresh work
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
  "record": {
    "detail_uid": "00001-001",
    "work_id": "00001",
    "detail_id": "001",
    "section_id": "00001-1",
    "section_title": "Details",
    "details_subfolder": "details",
    "title": "Updated detail title",
    "project_filename": "updated-detail.jpg",
    "status": "draft"
  }
}
```

Request behavior:

- `detail_uid` must resolve to an existing canonical detail record
- optional `apply_build: true` requests a parent-work site update as part of the save response
- `record` may be partial, but all keys must be known work-detail source fields
- legacy detail `project_subfolder` is rejected; use `details_subfolder` for source media folders and `section_title` for public grouping labels
- `record.detail_uid`, `record.work_id`, and `record.detail_id` must remain consistent with the target record
- `record.section_id` is read-only once present and must not be changed
- the parent `work_id` must exist in canonical source JSON

`POST /catalogue/work-detail/create` expects:

```json
{
  "work_id": "01942",
  "detail_id": "001",
  "record": {
    "title": "Detail title",
    "section_title": "Details",
    "details_subfolder": "details",
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
- `section_title` is required
- `section_id` is generated by the server as `[work_id]-1`, `[work_id]-2`, and so on
- legacy detail `project_subfolder` is rejected
- the server derives and validates the normalized `detail_uid`

Bulk workbook imports in `work_details` mode apply the same parent-published rule. Rows whose parent work is still draft are blocked in preview with `parent_work_unpublished`. Detail import rows use `details_subfolder` and `section_title`; non-empty legacy `project_subfolder` cells are blocked in preview. The preview response includes `importable_sections` so generated `section_id` values, section titles, and grouped detail counts are visible before apply.

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
- writes one aggregated Studio Activity entry that records import counts rather than one entry per imported record
- when the request includes valid Studio activity context from `/studio/bulk-add-work/`, writes unified Studio activity rows for `import-source-data` and `rebuild-lookups`

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
      "series_ids": ["009", "031"]
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

Field-aware preview request:

```json
{
  "work_id": "00001",
  "changed_fields": ["duration"]
}
```

`changed_fields` may be an array or comma-separated string. `record_family` is optional and can be used when the scope is ambiguous, for example a work-scoped detail preview.

It returns the planned scoped build:

- `work_ids`
- `series_ids`
- `generate_only`
- `rebuild_search`
- `generate_local_media`
- `field_plan` when `changed_fields` was supplied
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

Build preview and save-time `apply_build` for single work, work-detail, series, and moment saves now use the catalogue field registry path from `studio_config.json` to narrow build scopes from the changed field set:

- fields in one registry rule use that rule's target artifact families
- editor-only work fields can skip public build work
- local media generation and catalogue search are skipped unless the selected rule includes `local-media` or `catalogue-search`
- `field_plan.explanations[]` names the selected artifact families, changed fields, matched rule ids, fallback state, and concise registry reason
- unknown fields, mixed rule classes, bulk saves, create/delete operations, imports, publication actions, and series saves that also alter member work records keep conservative fallback

The direct `POST /catalogue/build-apply` endpoint still uses the explicit broad request shape unless called through save-time `apply_build`.
The save-time follow-through logic for work, work-detail, series, and moment saves is shared through `studio/services/catalogue/catalogue_save_build.py`; the endpoint handlers still choose the target work, detail, series, or moment build scope and append any Studio Activity build rows.

The apply endpoint updates:

- `var/studio/activity/activity_log.json` when valid Studio activity context is supplied for a covered action
