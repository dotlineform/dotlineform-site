---
doc_id: scripts-dev-studio
title: Dev Studio Runner
added_date: 2026-04-22
last_updated: "2026-05-12 10:50"
parent_id: servers
sort_order: 2000
---
# Dev Studio Runner

Script:

```bash
bin/dev-studio
```

## Purpose

`bin/dev-studio` is the integrated local Studio runner for everyday development.

For a new local session, it is the simplest way to:

- optionally refresh one or both docs/docs-search scopes before startup
- optionally refresh the derived catalogue lookup payloads used by the catalogue editors
- start the local Python Studio app server for migrated Studio views
- start the Jekyll site
- start the local Studio write services used by the current admin UI
- keep docs source edits synced into same-scope docs payloads and docs search while the runner is active

It is intended for route-shell, UI, and localhost write-flow testing. It is not the full content-generation pipeline.

## Default Command

Run from `dotlineform-site/`:

```bash
bin/dev-studio
```

The script:

- changes into the repo root
- loads `var/local/site.env` when present
- prefers `~/.rbenv/shims/bundle` when present
- prefers `~/miniconda3/bin/python3` when present
- otherwise falls back to `bundle` and `python3`

## Local Configuration

The runner does not currently take CLI flags.
For local runs, configure repo-specific defaults in `var/local/site.env`.
Values in that file are loaded before defaults are evaluated and win over inherited shell values.
If `var/local/site.env` is absent, the runner falls back to process environment variables.

- `JEKYLL_HOST`
  default: `127.0.0.1`
- `JEKYLL_PORT`
  default: `4000`
- `JEKYLL_CONFIG`
  default: `_config.yml,_config.dev-studio.yml`
- `STUDIO_APP_ENABLED`
  default: `1`
  set to `0` to skip the local Python Studio app server during transition
- `STUDIO_APP_HOST`
  default: `127.0.0.1`
- `STUDIO_APP_PORT`
  default: `8765`
- `CATALOGUE_WRITE_PORT`
  default: `8788`
- `DOCS_MANAGEMENT_PORT`
  default: `8789`
- `AUDIT_SERVICE_PORT`
  default: `8790`
- `DOCS_STARTUP_REBUILD_SCOPES`
  default: blank
  accepted values: configured docs scope ids from `scripts/docs/docs_scopes.json`, or comma-separated combinations
- `CATALOGUE_STARTUP_LOOKUP_REBUILD`
  default: `off`
  accepted enabled values: `1`, `on`, `true`, or `yes`
- `DOCS_WATCH_ENABLED`
  default: `1`
- `DOCS_WATCH_POLL_SECONDS`
  default: `1.0`
- `DOCS_WATCH_DEBOUNCE_SECONDS`
  default: `1.0`
- `DOCS_WATCH_TARGETED_SEARCH_THRESHOLD`
  default: `5`
  controls the maximum changed file count for watcher-targeted docs-search updates; use `-1` to target whenever affected ids are safe
- `DOTLINEFORM_BACKUP_RETENTION`
  default: `on`
  set to `off` or `0` to skip the startup Studio backup retention cleanup

Example:

```bash
export DOCS_STARTUP_REBUILD_SCOPES=""
export CATALOGUE_STARTUP_LOOKUP_REBUILD=off
export JEKYLL_PORT=4001
export STUDIO_APP_PORT=8765
export CATALOGUE_WRITE_PORT=8798
export DOCS_MANAGEMENT_PORT=8799
export AUDIT_SERVICE_PORT=8800
export DOCS_WATCH_DEBOUNCE_SECONDS=1.5
export DOCS_WATCH_TARGETED_SEARCH_THRESHOLD=8
```

Keeping `DOCS_STARTUP_REBUILD_SCOPES=""` in `var/local/site.env` is a valid reminder that startup docs/docs-search rebuilds are intentionally off.
To run a startup rebuild locally, edit that value to a configured docs scope id such as `studio`, `library`, `analysis`, or a comma-separated combination before starting the runner.

Keeping `CATALOGUE_STARTUP_LOOKUP_REBUILD=off` in `var/local/site.env` skips the full derived catalogue lookup export during normal startup.
Set it to `1`, `on`, `true`, or `yes` when startup should refresh `assets/studio/data/catalogue_lookup/` before the write server starts.

The runner reads valid docs scope ids from `scripts/docs/docs_scopes.json`.
Adding a new docs scope there makes it eligible for startup docs/docs-search rebuilds without editing `bin/dev-studio`.

## Startup Sequence

Before it starts any rebuilds or long-running servers, `bin/dev-studio` checks that the required ports are available:

1. Jekyll on `JEKYLL_HOST:JEKYLL_PORT`
2. Local Studio App on `STUDIO_APP_HOST:STUDIO_APP_PORT` when `STUDIO_APP_ENABLED` is not `0`
3. Catalogue Write Server on `127.0.0.1:CATALOGUE_WRITE_PORT`
4. Docs Management Server on `127.0.0.1:DOCS_MANAGEMENT_PORT`
5. Audit Service on `127.0.0.1:AUDIT_SERVICE_PORT`

If any port is unavailable, the runner exits immediately with a message naming the affected service and environment variable override.

After that preflight, `bin/dev-studio` runs the startup write steps below:

1. if `DOTLINEFORM_BACKUP_RETENTION` is not `off` or `0`, it runs:
   - `./scripts/studio/studio_backup_retention.py --write --quiet`
2. if `DOCS_STARTUP_REBUILD_SCOPES` is set, it runs:
   - `./scripts/build_docs.rb --scope <scope> --write`
   - `./scripts/build_search.rb --scope <scope> --write`
   for each listed docs scope
3. if `CATALOGUE_STARTUP_LOOKUP_REBUILD` is enabled, it runs:
   - `./scripts/catalogue/export_catalogue_lookup.py --write`

That means a default `bin/dev-studio` run skips startup docs/docs-search rebuilds and startup catalogue lookup export.
The catalogue write server still refreshes derived lookup payloads after catalogue writes.

If `CATALOGUE_STARTUP_LOOKUP_REBUILD` is enabled, startup also updates:

- derived catalogue lookup JSON under `assets/studio/data/catalogue_lookup/`

By default it also prunes local Studio backup files under `var/studio/backups/` and `var/studio/catalogue/backups/`.
Backup retention keeps the newest backups per target file; see [Studio Backup Retention](/docs/?scope=studio&doc=scripts-studio-backup-retention).

If `DOCS_STARTUP_REBUILD_SCOPES` is set, it also updates:

- scope-matching docs-viewer JSON under `assets/data/docs/scopes/<scope>/`
- scope-matching docs-search JSON under `assets/data/search/<scope>/`

After those startup writes succeed, it starts the long-running local processes below.

## Running Services

### Local Studio App

- command:

```bash
./scripts/studio/studio_app_server.py --host "$STUDIO_APP_HOST" --port "$STUDIO_APP_PORT"
```

- default URL: `http://127.0.0.1:8765/studio/`
- serves migrated local Studio views outside Jekyll
- currently mounts `/studio/`, `/studio/analytics/tag-groups/`, `/docs/`, `/health`, `/studio/runtime-config.json`, and the first Docs generated-read API routes
- can be disabled during transition with `STUDIO_APP_ENABLED=0`
- related doc: [Local Studio App](/docs/?scope=studio&doc=local-studio-app)

### Jekyll

- command:

```bash
bundle exec jekyll serve --config "$JEKYLL_CONFIG" --host "$JEKYLL_HOST" --port "$JEKYLL_PORT"
```

- default URL: `http://127.0.0.1:4000`
- serves the local site and unmigrated Studio routes during the transition
- uses `_config.dev-studio.yml` by default as a local-only overlay to exclude generated docs/search JSON from Jekyll's watch surface
- normal public builds that use `_config.yml` alone still include generated docs/search JSON
- when launched through `bin/dev-studio`, the Jekyll process loads `scripts/jekyll_webrick_client_reset_filter.rb` through `RUBYOPT`
- that filter suppresses only WEBrick `Errno::ECONNRESET` server-log entries, which are expected when the browser closes a local connection during refreshes, rebuilds, or cancelled asset loads
- other WEBrick errors, Jekyll build warnings, and docs watcher messages remain visible

### Catalogue Write Server

- command:

```bash
./scripts/catalogue/catalogue_write_server.py --port "$CATALOGUE_WRITE_PORT"
```

- default URL: `http://127.0.0.1:8788`
- related doc: [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

### Docs Management Server

- command:

```bash
./scripts/docs/docs_management_server.py --port "$DOCS_MANAGEMENT_PORT"
```

- default URL: `http://127.0.0.1:8789`
- related doc: [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

### Audit Service

- command:

```bash
./scripts/studio/audit_service.py --port "$AUDIT_SERVICE_PORT"
```

- default URL: `http://127.0.0.1:8790`
- related doc: [Studio Audit Service](/docs/?scope=studio&doc=scripts-studio-audit-service)

### Docs Live Rebuild Watcher

- command:

```bash
./scripts/docs/docs_live_rebuild_watcher.py --poll-seconds "$DOCS_WATCH_POLL_SECONDS" --debounce-seconds "$DOCS_WATCH_DEBOUNCE_SECONDS"
```

- watches `_docs/*.md` as `studio`
- watches `_docs_library/*.md` as `library`
- rebuilds same-scope docs payloads plus same-scope docs search after source changes
- can be disabled with `DOCS_WATCH_ENABLED=0`
- uses targeted docs-search updates for safe small source changes and full same-scope search rebuilds for threshold overflow or ambiguous source state
- related doc: [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## What It Also Prints

At startup the runner prints quick links for:

- Jekyll root
- Local Studio App
- Catalogue Write Server
- Docs Management Server
- Audit Service
- startup docs rebuild scopes
- startup catalogue lookup rebuild status
- Docs Live Watcher status
- Backup retention status
- Series Tag Editor:
  - `http://127.0.0.1:8765/studio/analytics/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

The runner traps `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, it:

- stops Jekyll
- stops the Local Studio App when enabled
- stops the Catalogue Write Server
- stops the Docs Management Server
- stops the Audit Service
- stops the Docs Live Rebuild Watcher when enabled
- waits for those child processes before exiting

If any one of the child processes exits unexpectedly, the runner stops monitoring and exits after waiting on that failed process.

## What It Does Not Do

`bin/dev-studio` does not currently:

- run `./scripts/catalogue/catalogue_json_build.py`
- rebuild any docs/docs-search scope on startup unless `DOCS_STARTUP_REBUILD_SCOPES` is set
- rebuild catalogue lookup artifacts on startup unless `CATALOGUE_STARTUP_LOOKUP_REBUILD` is enabled
- rebuild public search artifacts on startup
- start a separate frontend asset server
- replace Jekyll as the host for all Studio routes; unmigrated routes still use the Jekyll process during transition

If you disable the watcher or want an explicit manual rebuild, use:

```bash
./scripts/build_docs.rb --scope studio --write
./scripts/build_search.rb --scope studio --write
./scripts/build_docs.rb --scope library --write
./scripts/build_search.rb --scope library --write
```

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
