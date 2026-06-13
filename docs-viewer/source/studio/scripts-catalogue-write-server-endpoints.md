---
doc_id: scripts-catalogue-write-server-endpoints
title: Catalogue Write Server Endpoints
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: scripts-catalogue-write-server
---
# Catalogue Write Server Endpoints

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
- `POST /catalogue/work-file/create`
- `POST /catalogue/work-file/save`
- `POST /catalogue/work-file/delete`
- `POST /catalogue/work-link/create`
- `POST /catalogue/work-link/save`
- `POST /catalogue/work-link/delete`
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
- `activity_log`

Reads are allowlisted by key. They do not expose arbitrary repository paths. The source payloads come from canonical catalogue JSON, lookup payloads are built from the current source records for the request, and activity payloads come from the capped Studio feed file. This lets Studio treat mutable catalogue and local activity data as service-backed workspace data.

`POST /catalogue/project-state-report` accepts:

```json
{
  "include_subfolders": false
}
```

It runs `$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py` through its shared Python entrypoint. It writes `var/studio/reports/project-state.md` unless the server was started with `--dry-run`, and returns summary counts plus the report path. `include_subfolders` defaults to `false`; default mode counts every direct `/projects/<project_folder>` folder. When true, the report also includes `/projects/<project_folder>/<sub-folder>` directories while still skipping detail folders.

`POST /studio/api/catalogue/project-state-open-report` opens the latest local Project State Markdown snapshot. It is restricted to `var/studio/reports/project-state.md` and accepts `editor: "default"` or `editor: "vscode"`.
When the request includes valid Studio activity context from `/studio/project-state/`, a non-dry-run write also appends one unified Studio activity row with script purpose `generate-report`, summary counts, and the report path.

`POST /catalogue/bulk-save` expects:

```json
{
  "kind": "works",
  "ids": ["00001", "00002", "00003"],
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
- work delete preview includes dependent detail records and work-owned file/link metadata
- work delete blocks when the work is still used as `primary_work_id` by a published series
- work delete clears `primary_work_id` when a draft series points at the deleted work
- series delete preview includes affected member works
- work, work-detail, and series delete previews include generated artifact, repo-local media, public JSON update, Studio JSON update, and catalogue search impact where relevant
- moment delete preview covers the canonical source metadata record plus generated moment artifacts, repo/local media cleanup, moments index update, and catalogue search rebuild

`POST /catalogue/delete-apply` accepts the same shape and then:

- re-runs delete preview and blocks when preview is not clean
- writes the canonical source JSON files needed for that delete
- for work deletes, removes generated work artifacts, generated dependent detail artifacts, published thumbnails, repo-local staged media, stale public index/search records, per-work tag overrides, and work-storage index entries, and clears draft-series `primary_work_id` references to the deleted work
- for work-detail deletes, removes generated detail artifacts, published thumbnails, repo-local staged media, and the deleted detail from the parent work runtime JSON
- for series deletes, removes generated series artifacts, removes the series from affected work runtime/index records, removes the series tag-assignment row, updates recent/public indexes, and rebuilds catalogue search
- for moment deletes, removes generated moment page/json artifacts, published thumbnails, and repo-local staged media
- for moment deletes, removes the moment from `site/assets/data/moments_index.json` and rebuilds catalogue search so the search record disappears
- refreshes derived lookup payloads after non-dry-run writes
- records one aggregated Studio Activity entry for the delete operation

After successful canonical writes, the server also refreshes the derived Studio lookup payloads under `site/assets/studio/data/catalogue_lookup/`.

`POST /catalogue/publication-preview` expects:

```json
{
  "kind": "series",
  "action": "unpublish",
  "series_id": "001"
}
```

Supported `kind` values are `work`, `work_detail`, `series`, and `moment`. Supported `action` values are:

- `publish`: change source status from `draft` to `published` and run the scoped public update
- `unpublish`: change source status from `published` to `draft` and clean generated public artifacts
- `save_published`: save metadata for a currently published record and then run the scoped public update

Preview behavior:

- returns current and target status, changed fields, affected ids, blockers, and validation errors
- reports source-write impact separately from internal public impact
- reports scoped public-update impact for `publish` and `save_published`
- reports generated artifact cleanup and public index/search impact for `unpublish`
- for series `publish`, reports attached draft work ids that will be promoted to `published`
- for `save_published`, the request must include the same partial `record` shape as the matching source save endpoint and must not change publication status

`POST /catalogue/publication-apply` accepts the same request shape and then:

- re-runs publication preview before writing
- writes the id-scoped source status or metadata update
- when publishing a series, writes the series status and all attached draft-work status promotions atomically across `series.json` and `works.json`
- refreshes Studio lookup payloads after non-dry-run source writes
- runs the scoped public update for `publish` and `save_published`
- runs deterministic generated-artifact cleanup for `unpublish`
- returns `status: "public_update_failed"` when a source write succeeds but the internal public update fails
- records Studio Activity with `publication` operation names such as `series.publish`, `series.unpublish`, and `series.save_published`
- moment `unpublish` also removes generated moment page/json artifacts, published thumbnails, repo-local staged media, the `site/assets/data/moments_index.json` entry, and the catalogue search record

Standalone work publish remains stricter than series bootstrap publish: `work.publish` is blocked unless the work already belongs to at least one published series. Publishing a series is the bootstrap path for a new draft series with draft member works.

`POST /catalogue/work/save` expects:

```json
{
  "work_id": "00001",
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

Successful responses include:

- `work_id`
- `changed`
- `changed_fields`
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

or:

```json
{
  "target_kind": "moment",
  "moment_id": "keys"
}
```

Request behavior:

- `target_kind` must be `work`, `series`, or `moment`
- work ids normalize to five digits, series ids normalize to three digits, and moment ids normalize through slug-safe moment filename rules
- the target work, series, or moment must exist in the canonical catalogue source JSON
- work prose is staged at `var/docs/catalogue/import-staging/works/<work_id>.md`
- series prose is staged at `var/docs/catalogue/import-staging/series/<series_id>.md`
- moment prose is staged at `var/docs/catalogue/import-staging/moments/<moment_id>.md`
- the preview validates UTF-8 Markdown
- the preview reports whether the permanent target already exists and whether overwrite confirmation is required

`POST /catalogue/prose/import-apply` accepts the same request shape plus:

```json
{
  "confirm_overwrite": true
}
```

Apply behavior:

- re-runs the same preview validation before writing
- writes work prose to `_docs_catalogue/works/<work_id>.md`
- writes series prose to `_docs_catalogue/series/<series_id>.md`
- writes moment prose to `_docs_catalogue/moments/<moment_id>.md`
- refuses to overwrite different existing permanent prose content unless `confirm_overwrite` is true
- intentionally does not create backup files for this prose import flow
- logs a local catalogue event when a non-dry-run import writes changed prose
