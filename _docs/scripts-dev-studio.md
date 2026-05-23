---
doc_id: scripts-dev-studio
title: Dev Studio Runner
added_date: 2026-04-22
last_updated: "2026-05-23"
parent_id: servers
sort_order: 2000
---
# Dev Studio Runner

Scripts:

```bash
bin/dev-studio
bin/local-studio
bin/public-site-preview
bin/public-site-build
```

## Purpose

Local Studio and public Jekyll preview now have explicit launcher commands.
`bin/local-studio` is the local Studio app launcher.
`bin/public-site-preview` and `bin/public-site-build` are public-site Jekyll commands that use `_config.yml` by default.

`bin/dev-studio` remains the integrated transition runner while Studio is still being moved out of Jekyll.
It starts both the local Studio app and the Jekyll dev preview unless Jekyll is disabled, so it should be treated as a bridge command rather than the long-term product boundary.

For a new Studio session, `bin/local-studio` is the clearest command.
It can:

- optionally refresh one or both docs/docs-search scopes before startup
- optionally refresh the derived catalogue lookup payloads used by the catalogue editors
- start the local Python Studio app server for migrated Studio views
- optionally start retired standalone write services for fallback/debug runs
- keep docs source edits synced into same-scope docs payloads and docs search while the runner is active

Use `bin/public-site-preview` alongside it when local Studio links need a running public-site preview.

`bin/dev-studio` adds Jekyll to the same process group for transition sessions that still need public preview and Studio services under one terminal.
It is intended for route-shell, UI, and localhost write-flow testing. It is not the full content-generation pipeline.
As migration proceeds, this runner should shrink rather than gain new compatibility layers.

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

The bridge command remains available:

```bash
bin/dev-studio
```

Each script:

- changes into the repo root
- loads `var/local/site.env` when present
- prefers `~/.rbenv/shims/bundle` when present
- prefers `~/miniconda3/bin/python3` when present
- otherwise falls back to `bundle` and `python3`

`bin/public-site-preview` and `bin/public-site-build` do not start Studio services.
They are Jekyll-only public-site commands.

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
- `JEKYLL_ENABLED`
  default: `1` in `bin/dev-studio`; `bin/local-studio` sets it to `0`
  set to `0` to skip Jekyll and run only the local Studio side of the runner
- `LOCAL_STUDIO_ONLY`
  internal launcher flag used by `bin/local-studio` to keep Jekyll disabled even if `var/local/site.env` has a bridge-runner override
- `STUDIO_APP_ENABLED`
  default: `1`
  set to `0` to skip the local Python Studio app server during transition
- `STUDIO_APP_HOST`
  default: `127.0.0.1`
- `STUDIO_APP_PORT`
  default: `8765`
- `AUDIT_SERVICE_PORT`
  default: `8790`
- `AUDIT_SERVICE_ENABLED`
  default: `0`
  set to `1` only for fallback/debug runs that intentionally need the standalone audit service
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
- `PUBLIC_SITE_HOST`
  default: `JEKYLL_HOST` when set, otherwise `127.0.0.1`
  used by `bin/public-site-preview`
- `PUBLIC_SITE_PORT`
  default: `JEKYLL_PORT` when set, otherwise `4000`
  used by `bin/public-site-preview`
- `PUBLIC_SITE_CONFIG`
  default: `_config.yml`
  used by `bin/public-site-preview` and `bin/public-site-build`

Example:

```bash
export DOCS_STARTUP_REBUILD_SCOPES=""
export CATALOGUE_STARTUP_LOOKUP_REBUILD=off
export JEKYLL_PORT=4001
export STUDIO_APP_PORT=8765
export AUDIT_SERVICE_PORT=8800
export AUDIT_SERVICE_ENABLED=0
export DOCS_WATCH_DEBOUNCE_SECONDS=1.5
export DOCS_WATCH_TARGETED_SEARCH_THRESHOLD=8
```

Keeping `DOCS_STARTUP_REBUILD_SCOPES=""` in `var/local/site.env` is a valid reminder that startup docs/docs-search rebuilds are intentionally off.
To run a startup rebuild locally, edit that value to a configured docs scope id such as `studio`, `library`, `analysis`, or a comma-separated combination before starting the runner.

Keeping `CATALOGUE_STARTUP_LOOKUP_REBUILD=off` in `var/local/site.env` skips the full derived catalogue lookup export during normal startup.
Set it to `1`, `on`, `true`, or `yes` when startup should refresh `assets/studio/data/catalogue_lookup/` before the local Studio app starts.

The runner reads valid docs scope ids from `scripts/docs/docs_scopes.json`.
Adding a new docs scope there makes it eligible for startup docs/docs-search rebuilds without editing `bin/dev-studio`.

## Startup Sequence

Before it starts any rebuilds or long-running servers, `bin/dev-studio` checks that the required ports are available:

1. Jekyll on `JEKYLL_HOST:JEKYLL_PORT` when `JEKYLL_ENABLED` is not `0`
2. Local Studio App on `STUDIO_APP_HOST:STUDIO_APP_PORT` when `STUDIO_APP_ENABLED` is not `0`
3. Audit Service on `127.0.0.1:AUDIT_SERVICE_PORT` only when `AUDIT_SERVICE_ENABLED` is not `0`

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
./scripts/studio/studio_app_server.py --host "$STUDIO_APP_HOST" --port "$STUDIO_APP_PORT"
```

- default URL: `http://127.0.0.1:8765/studio/`
- serves migrated local Studio views outside Jekyll
- currently mounts `/studio/`, `/docs/`, migrated analytics tag views, `/health`, `/studio/runtime-config.json`, local Docs management API routes, and local analytics tag API routes
- can be disabled during transition with `STUDIO_APP_ENABLED=0`
- related doc: [Local Studio App](/docs/?scope=studio&doc=local-studio-app)

### Jekyll

Bridge command:

```bash
bundle exec jekyll serve --config "$JEKYLL_CONFIG" --host "$JEKYLL_HOST" --port "$JEKYLL_PORT"
```

- default URL: `http://127.0.0.1:4000`
- serves the local public-site preview and any still-Jekyll-hosted transition routes when `bin/dev-studio` is used
- uses `_config.dev-studio.yml` by default as a local-only overlay to exclude generated docs/search JSON from Jekyll's watch surface
- normal public builds that use `_config.yml` alone still include generated docs/search JSON
- when launched through `bin/dev-studio`, the Jekyll process loads `scripts/jekyll_webrick_client_reset_filter.rb` through `RUBYOPT`
- that filter suppresses only WEBrick `Errno::ECONNRESET` server-log entries, which are expected when the browser closes a local connection during refreshes, rebuilds, or cancelled asset loads
- other WEBrick errors, Jekyll build warnings, and docs watcher messages remain visible
- `bin/local-studio` disables this Jekyll process

Explicit public-site preview command:

```bash
bin/public-site-preview
```

It runs:

```bash
bundle exec jekyll serve --config "$PUBLIC_SITE_CONFIG" --host "$PUBLIC_SITE_HOST" --port "$PUBLIC_SITE_PORT"
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
There is no standalone catalogue write-server fallback in `bin/dev-studio`.

### Audit Service

- command:

```bash
./scripts/studio/audit_service.py --port "$AUDIT_SERVICE_PORT"
```

- default URL: `http://127.0.0.1:8790`
- disabled by default; active Studio audit endpoints are served by the local Studio app at `/studio/api/audits/...`
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

- Jekyll root when enabled
- Local Studio App
- Audit Service status
- startup docs rebuild scopes
- startup catalogue lookup rebuild status
- Docs Live Watcher status
- Backup retention status
- Series Tag Editor:
  - `http://127.0.0.1:8765/studio/analytics/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

The runner traps `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, it:

- stops Jekyll when enabled
- stops the Local Studio App when enabled
- stops the Audit Service when enabled
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
- replace Jekyll as the public preview host
- replace `bin/local-studio`, `bin/public-site-preview`, or `bin/public-site-build` as the explicit command boundary

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
