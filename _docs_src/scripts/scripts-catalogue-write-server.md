---
doc_id: scripts-catalogue-write-server
title: Catalogue Write Server
last_updated: 2026-04-17
parent_id: scripts
sort_order: 71
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
- `POST /catalogue/work/create`
- `POST /catalogue/work/save`
- `POST /catalogue/work-detail/create`
- `POST /catalogue/work-detail/save`
- `POST /catalogue/series/create`
- `POST /catalogue/series/save`
- `POST /catalogue/build-preview`
- `POST /catalogue/build-apply`

The current implementation can create draft work, work-detail, and series records, saves existing work/work-detail/series records in canonical catalogue source JSON, and can run a scoped JSON-source rebuild for one work or one series scope. It does not write prose files or write media files.

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
- current save endpoints write only `assets/studio/data/catalogue/works.json`, `assets/studio/data/catalogue/work_details.json`, and `assets/studio/data/catalogue/series.json`
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
