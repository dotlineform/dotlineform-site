---
doc_id: scripts-tag-write-server
title: "Tag Write Server"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: scripts
sort_order: 90
---
# Tag Write Server

Script:

```bash
./scripts/studio/tag_write_server.py
```

## Optional Flags

- `--port 8787`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--dry-run`: validate and return a response without writing files

## Endpoints And Behavior

Exposed endpoints:

- `GET /health`
- `POST /save-tags`
- `POST /import-tag-registry`
- `POST /import-tag-aliases`
- `POST /delete-tag-alias`
- `POST /mutate-tag-alias-preview`
- `POST /mutate-tag-alias`
- `POST /promote-tag-alias-preview`
- `POST /promote-tag-alias`
- `POST /import-tag-assignments-preview`
- `POST /import-tag-assignments`
- `POST /demote-tag-preview`
- `POST /demote-tag`
- `POST /mutate-tag-preview`
- `POST /mutate-tag`

Tag Studio save behavior:

- the Tag Studio page probes `/health`
- shows `Save mode: Local server` when available
- shows `Save mode: Offline session` when unavailable or when a staged local row already exists for the current series
- `POST /save-tags` expects assignment objects in `tags`
  - series save payload: `{ "series_id": "<series>", "tags": [...] }`
  - work override save payload: `{ "series_id": "<series>", "work_id": "<work_id>", "keep_work": true|false, "tags": [...] }`
  - tag rows use `{ "tag_id": "<group>:<slug>", "w_manual": 0.3|0.6|0.9, "alias"?: "<alias>" }`
  - `alias` is optional historical data only and is not treated as canonical
- saves write `assets/studio/data/tag_assignments.json` with object-only tag rows
- saves are diff-based in the Series Tag Editor
- when multiple work pills are selected, the active work's current override set is used as the persisted state for all selected work pills
- work override saves strip tags already inherited from `series[*].tags`
- `keep_work: false` plus empty tags deletes `series[*].works[work_id]`
- `keep_work: true` allows an explicit work row with `tags: []`
- offline-session staging stores full normalized series rows in browser `localStorage`, including optional historical `alias`
- the Series Tags page can export that session as JSON or preview and apply it through the local server
- assignment import preview and apply compares full normalized rows, including `alias`, and resolves conflicts per series via `overwrite` or `skip`

Tag Registry behavior:

- probes `/health`
- shows `Import mode: Local server` when available
- shows `Import mode: Patch` when unavailable
- tag edit and delete require local server mode
- `New tag` opens a create modal with group pills, slug entry, optional description, and duplicate checks
- local mode uses `POST /import-tag-registry` with `mode: add`
- patch mode emits an add-tag row snippet

Registry import and mutation behavior:

- supported import modes:
  - `add`
  - `merge`
  - `replace`
- successful imports include `summary_text`
- import requests may include `import_filename`; server logs basename only
- `POST /mutate-tag`
  - `action: edit` updates canonical tag description
  - `action: delete` removes the tag
- delete cascades into `tag_assignments.json` and `tag_aliases.json`
- aliases that become 1:1 self-maps are removed automatically
- `POST /mutate-tag-preview` returns the same impact stats without writing files
- tag demotion:
  - triggered from the registry list
  - preview via `POST /demote-tag-preview`
  - apply via `POST /demote-tag`
  - demotion removes the canonical tag, creates alias mappings, and rewrites assignments and alias target refs
  - patch fallback emits ordered manual steps only

Tag Aliases behavior:

- probes `/health`
- shows `Import mode: Local server` when available
- shows `Import mode: Patch` when unavailable
- alias delete uses `POST /delete-tag-alias` in local mode
- patch mode generates manual snippets with `aliases_to_remove`
- alias edit modal supports description and selected canonical tags, with max 4 tags and max 1 per group
- local mode uses `POST /mutate-tag-alias`
- patch mode emits ordered `set_alias` and `remove_alias_key` steps
- `New alias` uses `POST /import-tag-aliases` with `mode: add` in local mode
- patch mode emits an add-alias fragment snippet
- alias promote:
  - choose target group at action time
  - preview via `POST /promote-tag-alias-preview`
  - apply via `POST /promote-tag-alias`
  - canonical tag id becomes `<group>:<alias-slug>`
  - if canonical already exists, the alias key is removed only
- alias import modes:
  - `add`
  - `merge`
  - `replace`
- successful alias imports include `summary_text` and `import_filename` basename only

## Security Constraints

- binds to loopback only
- CORS allows loopback origins only
- write target is allowlisted to:
  - `assets/studio/data/tag_assignments.json`
  - `assets/studio/data/tag_registry.json`
  - `assets/studio/data/tag_aliases.json`
- timestamped backups are created in `var/studio/backups/`
  - `tag_assignments.json.bak-YYYYMMDD-HHMMSS`
  - `tag_registry.json.bak-YYYYMMDD-HHMMSS`
  - `tag_aliases.json.bak-YYYYMMDD-HHMMSS`

## Source And Target Artifacts

Source and target JSON artifacts:

- `assets/studio/data/tag_assignments.json`
- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_aliases.json`

Backup target:

- `var/studio/backups/`

Operational log target:

- `var/studio/logs/tag_write_server.log`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Studio](/docs/?scope=studio&doc=studio)
- [Series Tags](/docs/?scope=studio&doc=series-tags)
- [Tag Editor](/docs/?scope=studio&doc=tag-editor)
