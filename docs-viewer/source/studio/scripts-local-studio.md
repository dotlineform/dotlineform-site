---
doc_id: scripts-local-studio
title: Local Runners
added_date: 2026-04-22
last_updated: 2026-05-25
parent_id: servers
sort_order: 2000
---
# Local Runners

Scripts:

```bash
bin/local-all
bin/local-studio
bin/public-site-preview
bin/public-site-build
docs-viewer/bin/docs-viewer
```

## Purpose

Local Studio, public Jekyll preview, and Docs Viewer have separate launcher commands.
`bin/local-studio` starts the Local Studio app, Studio APIs, the docs live rebuild watcher, and optional startup maintenance tasks.
The docs live rebuild watcher is not the Docs Viewer web service; it only watches source Markdown and rebuilds generated docs/search payloads after source changes.
`bin/local-studio` does not start the Docs Viewer web service and no longer serves `/docs/`.
`docs-viewer/bin/docs-viewer` starts the standalone Docs Viewer web service that owns the `/docs/` manage-mode page.
`bin/public-site-preview` and `bin/public-site-build` are public-site Jekyll commands that use `_config.yml` by default.
`bin/local-all` is the optional host-owned orchestration runner for starting Live Preview, Local Studio, and the Docs Viewer web service together.

The old combined bridge command has been retired.
Do not use a combined Studio-plus-Jekyll runner for normal single-service work.
Run `bin/local-studio` for Studio and run `bin/public-site-preview` in a separate terminal when Studio links need a live public-site preview host.
Run `bin/local-all` when a local session needs all three services supervised together.

## Explicit Commands

Run from `dotlineform-site/`:

```bash
bin/local-all
```

This starts public-site Live Preview, Local Studio, and the Docs Viewer web service as sibling child processes.
Each underlying service can still be started independently with its own command.

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

Each command:

- changes into the repo root
- loads `var/local/site.env` when present
- uses the repo's preferred Ruby or Python executable when that command needs one
- otherwise falls back to the corresponding executable on `PATH`

`bin/public-site-preview` and `bin/public-site-build` do not start Studio services.
`bin/local-studio` does not start Jekyll.
Start the Docs Viewer web service separately with:

```bash
docs-viewer/bin/docs-viewer
```

## Local Configuration

These runner scripts do not currently take general CLI flags, except for public-site preview/build pass-through behavior documented below.
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
- `DOCS_VIEWER_HOST`
  default: `127.0.0.1`
  used by the Docs Viewer web service and preflighted by `bin/local-all`
- `DOCS_VIEWER_PORT`
  default: `8776`
  used by the Docs Viewer web service and preflighted by `bin/local-all`
- `DOCS_VIEWER_BASE_URL`
  default: `http://$DOCS_VIEWER_HOST:$DOCS_VIEWER_PORT`
  printed by `bin/local-all` and used by Studio links

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

### Start All

Before it starts any child process, `bin/local-all` loads `var/local/site.env`, resolves the configured public preview, Local Studio, and Docs Viewer web service host/port settings, and checks that those ports are both distinct and available.
If a configured port is unavailable or two services are configured for the same binding, the runner exits before starting any service.

After preflight, `bin/local-all` starts:

1. `bin/public-site-preview`
2. `bin/local-studio`
3. `docs-viewer/bin/docs-viewer`

The runner prints the public-site preview, Local Studio app, and Docs Viewer web service URLs.
If any child process exits, `bin/local-all` prints which service exited, stops the remaining children, and exits with a non-zero status for clean early exits or the failing child status otherwise.

### Local Studio

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
- mounts `/studio/`, migrated Studio route shells, `/health`, `/studio/runtime-config.json`, local Analytics APIs, local audit APIs, and local catalogue APIs
- does not serve `/docs/`, `/docs-viewer/...` assets, Docs Viewer generated reads, Docs Viewer management APIs, or Docs data-sharing document APIs
- links to Docs Viewer manage mode through the configured Docs Viewer web service URL
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

### Docs Viewer Web Service

Explicit Docs Viewer command:

```bash
docs-viewer/bin/docs-viewer
```

It runs:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_viewer_service.py
```

- default URL: `http://127.0.0.1:8776/docs/`
- owns the local `/docs/` manage-mode page
- serves Docs Viewer runtime/static assets under `/docs-viewer/...`
- serves Docs Viewer generated reads, management APIs, and Docs data-sharing document APIs
- uses `DOCS_VIEWER_HOST`, `DOCS_VIEWER_PORT`, and `DOCS_VIEWER_BASE_URL`
- stays independent of Local Studio; `bin/local-all` only supervises it as a sibling child process

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

The docs live rebuild watcher is a background rebuild helper started by `bin/local-studio`.
It is separate from the Docs Viewer web service.

- command:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_live_rebuild_watcher.py --poll-seconds "$DOCS_WATCH_POLL_SECONDS" --debounce-seconds "$DOCS_WATCH_DEBOUNCE_SECONDS"
```

- watches `docs-viewer/source/studio/*.md` as `studio`
- watches `docs-viewer/source/analysis/**/*.md` as `analysis`
- watches `docs-viewer/source/library/*.md` as `library`
- rebuilds same-scope docs payloads plus same-scope docs search after source changes
- can be disabled with `DOCS_WATCH_ENABLED=0`
- uses targeted docs-search updates for safe small source changes and full same-scope search rebuilds for threshold overflow or ambiguous source state
- related doc: [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## What It Also Prints

At startup the runner prints quick links for:

- Start All service URLs when `bin/local-all` is used
- Local Studio App
- local API ownership
- startup docs rebuild scopes
- startup catalogue lookup rebuild status
- Docs Live Watcher status
- Backup retention status
- Series Tag Editor:
  - `http://127.0.0.1:8765/studio/analytics/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

`bin/local-all` and `bin/local-studio` both trap `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, `bin/local-all` stops the public-site preview, Local Studio runner, and Docs Viewer service before exiting.

When you press `Ctrl+C` in `bin/local-studio`, it:

- stops the Local Studio App when enabled
- stops the Docs Live Rebuild Watcher when enabled
- waits for those child processes before exiting

If any `bin/local-all` child process exits unexpectedly, the runner stops the remaining children and reports the child name and exit status.
If either `bin/local-studio` child process exits unexpectedly, that runner stops monitoring and exits after waiting on the failed process.

## What It Does Not Do

`bin/local-studio` does not currently:

- start Jekyll
- start the Docs Viewer web service
- serve `/docs/` or Docs Viewer management APIs
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
