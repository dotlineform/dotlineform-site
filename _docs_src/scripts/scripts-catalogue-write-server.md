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
- `POST /catalogue/work/save`

The first implementation only saves existing work records in canonical catalogue source JSON. It does not create works, edit work details, edit series, write prose files, write media files, generate public runtime artifacts, or rebuild search.

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

## Validation

The server validates the proposed update through the shared catalogue source loader and validator before writing. Validation checks the full catalogue source set, not only the submitted work record, so invalid series references are blocked before `works.json` is replaced.

## Security Constraints

- binds to `127.0.0.1` only
- CORS allows loopback origins only
- write target is allowlisted to canonical catalogue source JSON files under `assets/studio/data/catalogue/`
- the current save endpoint writes only `assets/studio/data/catalogue/works.json`
- timestamped backup bundles are created under `var/studio/catalogue/backups/`
- event logs are written under `var/studio/catalogue/logs/`
- logs include IDs, changed fields, status, and error summaries only; they do not include full submitted records
- source-save and validation-failure events also update `assets/studio/data/catalogue_activity.json` for the Studio Catalogue Activity page

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

Studio activity feed:

- `assets/studio/data/catalogue_activity.json`

Backup target:

- `var/studio/catalogue/backups/`

Operational log target:

- `var/studio/catalogue/logs/catalogue_write_server.log`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Catalogue Source Export](/docs/?scope=studio&doc=scripts-catalogue-source)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
