---
doc_id: scripts-catalogue-write-server
title: "Catalogue Write Server"
last_updated: 2026-04-22
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
- `POST /catalogue/bulk-save`
- `POST /catalogue/delete-preview`
- `POST /catalogue/delete-apply`
- `POST /catalogue/work/create`
- `POST /catalogue/work/save`
- `POST /catalogue/work-detail/create`
- `POST /catalogue/work-detail/save`
- `POST /catalogue/import-preview`
- `POST /catalogue/import-apply`
- `POST /catalogue/work-file/create`
- `POST /catalogue/work-file/save`
- `POST /catalogue/work-file/delete`
- `POST /catalogue/work-link/create`
- `POST /catalogue/work-link/save`
- `POST /catalogue/work-link/delete`
- `POST /catalogue/series/create`
- `POST /catalogue/series/save`
- `POST /catalogue/build-preview`
- `POST /catalogue/build-apply`

The current implementation can create draft work, work-detail, work-file, work-link, and series records, can import new work/work-detail records from `data/works.xlsx`, can bulk-save existing work/work-detail records, saves existing work/work-detail/work-file/work-link/series records in canonical catalogue source JSON, and can run a scoped JSON-source rebuild for one work or one series scope. It does not write prose files, write media files, or write back into Excel.

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
- successful response includes changed counts, changed ids, normalized changed records, and rebuild targets
- optional `apply_build: true` runs the same scoped update sequence immediately and returns nested build status plus any remaining targets when that update sequence fails part-way through

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

Request behavior:

- returns a delete summary, affected records, blockers, and validation errors
- work delete preview includes dependent detail/file/link source records
- work delete blocks when the work is still used as `primary_work_id` by a series
- series delete preview includes affected member works

`POST /catalogue/delete-apply` accepts the same shape plus optional `expected_record_hash` and then:

- re-runs delete preview and blocks when preview is not clean
- writes the canonical source JSON files needed for that delete
- refreshes derived lookup payloads after non-dry-run writes
- records one aggregated Catalogue Activity entry for the delete operation

After successful canonical writes, the server also refreshes the derived Studio lookup payloads under `assets/studio/data/catalogue_lookup/`.

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
- optional `apply_build: true` requests a same-scope site update as part of the save response
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
- `saved_at_utc` when a non-dry-run write changed the source file
- `backups` when a non-dry-run write changed the source file

## Derived Lookup Refresh

Current behavior after successful canonical writes:

- the server refreshes the derived Studio lookup payloads under `assets/studio/data/catalogue_lookup/`
- current implementation always runs a full lookup refresh
- this is intentionally conservative and keeps lookup/search payloads aligned without needing per-field dependency logic

Why the current refresh is broad:

- a single source edit can affect more than one derived lookup family
- work saves can affect:
  - the focused work lookup record
  - work search
  - series member summaries
  - detail/file/link work summaries
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
- the first work-field invalidation registry now lives in server code; a later task will decide whether that registry should remain in code or move into JSON/config
- the current dependency mapping now also explicitly includes moments, with `title`, `date`, and `date_display` treated as the fields that currently affect both moment runtime data and catalogue search
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
- `detail_id` must be unique within that work
- blank or missing `status` is normalized to `draft`
- `title` is required
- the server derives and validates the normalized `detail_uid`

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

`POST /catalogue/work-file/save` expects:

```json
{
  "file_uid": "00008:nerve",
  "expected_record_hash": "optional-current-record-sha256",
  "record": {
    "filename": "nerve.pdf",
    "label": "nerve.pdf",
    "status": "published",
    "published_date": "2026-04-01"
  }
}
```

Request behavior:

- `file_uid` must resolve to an existing canonical file record
- optional `apply_build: true` requests a parent-work site update as part of the save response
- `filename` and `label` are required
- `record` may be partial, but all keys must be known work-file source fields
- the parent `work_id` must remain valid
- `expected_record_hash`, when provided, must match the current stored file hash or the server returns `409 Conflict`

`POST /catalogue/work-file/create` expects:

```json
{
  "work_id": "01942",
  "record": {
    "filename": "new-file.pdf",
    "label": "new-file.pdf",
    "status": "draft"
  }
}
```

Request behavior:

- parent `work_id` must already exist
- blank or missing `status` is normalized to `draft`
- `filename` and `label` are required
- the server derives and validates the normalized `file_uid`

`POST /catalogue/work-link/save` expects:

```json
{
  "link_uid": "00457:bandcamp",
  "expected_record_hash": "optional-current-record-sha256",
  "record": {
    "url": "https://dotlineform.bandcamp.com/album/intuition",
    "label": "Bandcamp",
    "status": "published",
    "published_date": "2026-04-01"
  }
}
```

Request behavior:

- `link_uid` must resolve to an existing canonical link record
- optional `apply_build: true` requests a parent-work site update as part of the save response
- `url` and `label` are required
- `record` may be partial, but all keys must be known work-link source fields
- the parent `work_id` must remain valid
- `expected_record_hash`, when provided, must match the current stored link hash or the server returns `409 Conflict`

`POST /catalogue/work-link/create` expects:

```json
{
  "work_id": "01942",
  "record": {
    "url": "https://example.com/work",
    "label": "Reference link",
    "status": "draft"
  }
}
```

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
- optional `apply_build: true` requests a same-scope site update as part of the save response
- `work_updates` is limited to changed membership rows for affected works
- each changed work keeps the submitted `series_ids` order; the server does not sort it
- draft source saves may omit `primary_work_id`
- `primary_work_id`, when present, must still be a member of the series after the proposed membership writes
- the server validates the full source set before writing `series.json` and `works.json`

`POST /catalogue/series/create` expects:

```json
{
  "series_id": "099",
  "record": {
    "title": "New draft series",
    "series_type": "primary",
    "status": "draft",
    "sort_fields": "work_id"
  }
}
```

Request behavior:

- `series_id` must not already exist
- blank or missing `status` is normalized to `draft`
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

- any series included in the requested build scope must have a valid `primary_work_id`
- draft series without `primary_work_id` can be saved in source JSON, but build preview/apply returns a validation error until they are publishable

`POST /catalogue/build-apply` accepts the same shapes and then runs:

- `generate_work_pages.py --source json` for the selected work and affected series ids
- or `generate_work_pages.py --source json` for the selected series and affected works
- `build_search.rb --scope catalogue --write`

The apply endpoint updates:

- `assets/studio/data/build_activity.json`
- `assets/studio/data/catalogue_activity.json`

## Validation

The server validates the proposed update through the shared catalogue source loader and validator before writing. Validation checks the full catalogue source set, not only the submitted work record, so invalid series references are blocked before `works.json` is replaced.

## Security Constraints

- binds to `127.0.0.1` only
- CORS allows loopback origins only
- write target is allowlisted to canonical catalogue source JSON files under `assets/studio/data/catalogue/`
- current save endpoints write only canonical catalogue source JSON under `assets/studio/data/catalogue/`, including `works.json`, `work_details.json`, `work_files.json`, `work_links.json`, and `series.json`
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
