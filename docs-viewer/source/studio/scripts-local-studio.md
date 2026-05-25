---
doc_id: scripts-local-studio
title: Local Studio Runner
added_date: 2026-04-22
last_updated: 2026-05-25
parent_id: servers
sort_order: 2000
---
# Local Studio Runner

Scripts:

```bash
bin/local-studio
bin/public-site-preview
bin/public-site-build
```

## Purpose

Local Studio and public Jekyll preview have separate launcher commands.
`bin/local-studio` starts the local Studio app, Studio APIs, docs live watcher, and optional startup maintenance tasks.
`bin/public-site-preview` and `bin/public-site-build` are public-site Jekyll commands that use `_config.yml` by default.

The old combined bridge command has been retired.
Do not use a combined Studio-plus-Jekyll runner for normal work.
Run `bin/local-studio` for Studio and run `bin/public-site-preview` in a separate terminal only when Studio links need a live public-site preview host.

## Explicit Commands

Run from `dotlineform-site/`:

```bash
bin/local-studio
```

This starts the local Studio app without Jekyll.

For public-site preview, run:

```bash
bin/public-site-preview
```

For a public-site build, run:

```bash
bin/public-site-build
```

`bin/public-site-build` passes any extra arguments through to Jekyll, so an isolated verification build can use:

```bash
bin/public-site-build --destination /tmp/dlf-jekyll-build
```

Each script:

- changes into the repo root
- loads `var/local/site.env` when present
- prefers `~/.rbenv/shims/bundle` when present
- prefers `~/miniconda3/bin/python3` when present
- otherwise falls back to `bundle` and `python3`

`bin/public-site-preview` and `bin/public-site-build` do not start Studio services.
`bin/local-studio` does not start Jekyll.

## Local Configuration

The runner does not currently take CLI flags.
For local runs, configure repo-specific defaults in `var/local/site.env`.
Values in that file are loaded before defaults are evaluated and win over inherited shell values.
If `var/local/site.env` is absent, the runner falls back to process environment variables.

- `STUDIO_APP_ENABLED`
  default: `1`
  set to `0` to skip the local Python Studio app server
- `STUDIO_APP_HOST`
  default: `127.0.0.1`
- `STUDIO_APP_PORT`
  default: `8765`
- `STUDIO_APP_ACCESS_LOG`
  default: `0`
  set to `1`, `on`, `true`, or `yes` to print one HTTP access log line for each Local Studio app request
- `DOCS_STARTUP_REBUILD_SCOPES`
  default: blank
  accepted values: configured docs scope ids from `docs-viewer/config/scopes/docs_scopes.json`, or comma-separated combinations
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
- `PUBLIC_SITE_HOST`
  default: `JEKYLL_HOST` when set, otherwise `127.0.0.1`
  used by `bin/public-site-preview`
- `PUBLIC_SITE_PORT`
  default: `JEKYLL_PORT` when set, otherwise `4000`
  used by `bin/public-site-preview`
- `PUBLIC_SITE_CONFIG`
  default: `_config.yml`
  used by `bin/public-site-preview` and `bin/public-site-build`
- `PUBLIC_SITE_LIVERELOAD`
  default: `0`
  accepted enabled values: `1`, `on`, `true`, or `yes`
  used by `bin/public-site-preview`; can also be enabled per run with `bin/public-site-preview --livereload`

Example:

```bash
export DOCS_STARTUP_REBUILD_SCOPES=""
export CATALOGUE_STARTUP_LOOKUP_REBUILD=off
export STUDIO_APP_PORT=8765
export STUDIO_APP_ACCESS_LOG=0
export DOCS_WATCH_DEBOUNCE_SECONDS=1.5
export DOCS_WATCH_TARGETED_SEARCH_THRESHOLD=8
```

Keeping `DOCS_STARTUP_REBUILD_SCOPES=""` in `var/local/site.env` is a valid reminder that startup docs/docs-search rebuilds are intentionally off.
To run a startup rebuild locally, edit that value to a configured docs scope id such as `studio`, `library`, `analysis`, or a comma-separated combination before starting the runner.

Keeping `CATALOGUE_STARTUP_LOOKUP_REBUILD=off` in `var/local/site.env` skips the full derived catalogue lookup export during normal startup.
Set it to `1`, `on`, `true`, or `yes` when startup should refresh `assets/studio/data/catalogue_lookup/` before the local Studio app starts.

The runner reads valid docs scope ids from `docs-viewer/config/scopes/docs_scopes.json`.
Adding a new docs scope there makes it eligible for startup docs/docs-search rebuilds without editing the runner.

## Startup Sequence

Before it starts any rebuilds or long-running processes, `bin/local-studio` checks that the Local Studio app port is available when the app server is enabled.
If the port is unavailable, the runner exits immediately with a message naming `STUDIO_APP_PORT`.

After that preflight, `bin/local-studio` runs the startup write steps below:

1. if `DOTLINEFORM_BACKUP_RETENTION` is not `off` or `0`, it runs:
   - `$HOME/miniconda3/bin/python3 studio/app/server/studio/studio_backup_retention.py --write --quiet`
2. if `DOCS_STARTUP_REBUILD_SCOPES` is set, it runs:
   - `./scripts/build_docs.rb --scope <scope> --write`
   - `./scripts/build_search.rb --scope <scope> --write`
   for each listed docs scope
3. if `CATALOGUE_STARTUP_LOOKUP_REBUILD` is enabled, it runs:
   - `$HOME/miniconda3/bin/python3 studio/services/catalogue/export_catalogue_lookup.py --write`

That means a default `bin/local-studio` run skips startup docs/docs-search rebuilds and startup catalogue lookup export.
The local Studio app catalogue API refreshes derived lookup payloads after catalogue writes.

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
$HOME/miniconda3/bin/python3 studio/app/server/studio/studio_app_server.py --host "$STUDIO_APP_HOST" --port "$STUDIO_APP_PORT"
```

- default URL: `http://127.0.0.1:8765/studio/`
- serves Local Studio views outside Jekyll
- mounts `/studio/`, `/docs/`, migrated Studio route shells, `/health`, `/studio/runtime-config.json`, local Docs APIs, local Analytics APIs, local audit APIs, and local catalogue APIs
- can be disabled with `STUDIO_APP_ENABLED=0`
- access logging is quiet by default; set `STUDIO_APP_ACCESS_LOG=1` or pass `--access-log` to the app server for detailed request logging
- related doc: [Local Studio App](/docs/?scope=studio&doc=local-studio-app)

### Public Jekyll Preview

Explicit public-site preview command:

```bash
bin/public-site-preview
```

It runs:

```bash
bundle exec jekyll serve --config "$PUBLIC_SITE_CONFIG" --host "$PUBLIC_SITE_HOST" --port "$PUBLIC_SITE_PORT"
```

Pass `--livereload` to enable Jekyll LiveReload for a preview session:

```bash
bin/public-site-preview --livereload
```

Explicit public-site build command:

```bash
bin/public-site-build
```

It runs:

```bash
bundle exec jekyll build --config "$PUBLIC_SITE_CONFIG"
```

Both public-site commands use `_config.yml` by default and do not start local Studio services.

### Catalogue APIs

The local Studio app owns the active browser-facing catalogue APIs under `/studio/api/catalogue/...`.
There is no standalone catalogue write-server fallback in `bin/local-studio`.

### Audit API

The local Studio app owns the active browser-facing audit APIs under `/studio/api/audits/...`.
There is no standalone audit HTTP service fallback in `bin/local-studio`.
For direct automation, call:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/audit_runner.py --audit-id studio-ready-state
```

Related doc: [Studio Audit Runner](/docs/?scope=studio&doc=scripts-studio-audit-service).

### Docs Live Rebuild Watcher

- command:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_live_rebuild_watcher.py --poll-seconds "$DOCS_WATCH_POLL_SECONDS" --debounce-seconds "$DOCS_WATCH_DEBOUNCE_SECONDS"
```

- watches `_docs/*.md` as `studio`
- watches `_docs_library/*.md` as `library`
- rebuilds same-scope docs payloads plus same-scope docs search after source changes
- can be disabled with `DOCS_WATCH_ENABLED=0`
- uses targeted docs-search updates for safe small source changes and full same-scope search rebuilds for threshold overflow or ambiguous source state
- related doc: [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## What It Also Prints

At startup the runner prints quick links for:

- Local Studio App
- local API ownership
- startup docs rebuild scopes
- startup catalogue lookup rebuild status
- Docs Live Watcher status
- Backup retention status
- Series Tag Editor:
  - `http://127.0.0.1:8765/studio/analytics/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

The runner traps `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, it:

- stops the Local Studio App when enabled
- stops the Docs Live Rebuild Watcher when enabled
- waits for those child processes before exiting

If either child process exits unexpectedly, the runner stops monitoring and exits after waiting on that failed process.

## What It Does Not Do

`bin/local-studio` does not currently:

- start Jekyll
- run `$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py`
- rebuild any docs/docs-search scope on startup unless `DOCS_STARTUP_REBUILD_SCOPES` is set
- rebuild catalogue lookup artifacts on startup unless `CATALOGUE_STARTUP_LOOKUP_REBUILD` is enabled
- rebuild public search artifacts on startup
- start a separate frontend asset server
- replace Jekyll as the public preview host

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
