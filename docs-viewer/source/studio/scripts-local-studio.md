---
doc_id: scripts-local-studio
title: Local Runners
added_date: 2026-04-22
last_updated: 2026-06-13
parent_id: local-setup
viewable: true
---
# Local Runners

Scripts:

```bash
bin/local-all
bin/local-admin
bin/local-studio
bin/local-analytics
bin/site-preview
bin/site-validate
docs-viewer/bin/docs-viewer
```

## Purpose

Local Studio, Local Admin, Local Analytics, public static preview, and Docs Viewer have separate launcher commands.

`bin/local-studio` 
- starts the Local Studio app for Studio catalogue routes and APIs
- the docs live rebuild watcher
- Python startup maintenance tasks.

The docs live rebuild watcher is not the Docs Viewer web service; it only watches source Markdown and rebuilds generated docs/search payloads after source changes.

`bin/local-analytics`
- starts the standalone Local Analytics app for tag and Data Sharing routes/APIs.

`bin/local-admin`
- starts the Local Admin app for cross-repo operations.

`docs-viewer/bin/docs-viewer`
- starts the standalone Docs Viewer web service that owns the `/docs/` manage-mode page.

`bin/site-preview` and `bin/site-validate`
- public static-site commands that use `site/` and `site-tools/config/site-tools.json`.
- `bin/site-preview` serves the checked-in static deploy root directly.
- `bin/site-validate` checks deploy-root requirements without generating or copying files.

`bin/local-all`
- orchestration runner

Run `bin/local-studio` for Studio and run `bin/site-preview` in a separate terminal when Studio links need a live public-site preview host.
Run `bin/local-admin` when working only on Admin routes.
Run `bin/local-analytics` when working only on Analytics or Data Sharing.
Run `bin/local-all` when a local session needs the sibling services supervised together.

Each command:

- changes into the repo root
- loads `.env.local` when present
- uses the repo's preferred Python executable for local app runners and maintenance tasks
- otherwise falls back to the corresponding executable on `PATH`

## Local Configuration

These runner scripts do not currently take general CLI flags, except for public-site preview behavior documented below.

For local runs, configure repo-specific defaults in `.env.local`.

Values in that file are loaded before defaults are evaluated and win over inherited shell values.

If `.env.local` is absent, the runner falls back to process environment variables.

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
- `ADMIN_APP_ENABLED`
  default: `1`
  used by `bin/local-all`; set to `0` to skip the Local Admin child process
- `ADMIN_APP_HOST`
  default: `127.0.0.1`
- `ADMIN_APP_PORT`
  default: `8768`
- `ADMIN_APP_ACCESS_LOG`
  default: `0`
  set to `1`, `on`, `true`, or `yes` to print one HTTP access log line for each Local Admin app request
- `ANALYTICS_APP_ENABLED`
  default: `1`
  used by `bin/local-all`; set to `0` to skip the Local Analytics child process
- `ANALYTICS_APP_HOST`
  default: `127.0.0.1`
- `ANALYTICS_APP_PORT`
  default: `8766`
- `ANALYTICS_APP_ACCESS_LOG`
  default: `0`
  set to `1`, `on`, `true`, or `yes` to print one HTTP access log line for each Local Analytics app request
- `DOCS_WATCH_ENABLED`
  default: `1`
- `DOCS_WATCH_POLL_SECONDS`
  default: `1.0`
- `DOCS_WATCH_DEBOUNCE_SECONDS`
  default: `1.0`
- `DOCS_WATCH_TARGETED_SEARCH_THRESHOLD`
  default: `5`
  controls the maximum changed file count for watcher-targeted docs-search updates; use `-1` to target whenever affected ids are safe
- `SITE_ENABLED`
  default: `1`
  used by `bin/local-all`; set to `0` to skip the public-site preview child process
- `SITE_HOST`
  default: `127.0.0.1`
  used by `bin/site-preview` and preflighted by `bin/local-all` when `SITE_ENABLED` is not `0`
- `SITE_PORT`
  default: `4000`
  used by `bin/site-preview` and preflighted by `bin/local-all` when `SITE_ENABLED` is not `0`
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
export STUDIO_APP_PORT=8765
export STUDIO_APP_ACCESS_LOG=0
export ADMIN_APP_PORT=8768
export ADMIN_APP_ACCESS_LOG=0
export ANALYTICS_APP_PORT=8766
export ANALYTICS_APP_ACCESS_LOG=0
export DOCS_WATCH_DEBOUNCE_SECONDS=1.5
export DOCS_WATCH_TARGETED_SEARCH_THRESHOLD=8
```

## Startup Sequence

### Start All

Before it starts any child process, `bin/local-all` loads `.env.local`, resolves the configured public preview, Local Studio, Local Admin, Local Analytics, and Docs Viewer web service host/port settings, and checks that enabled service ports are both distinct and available.
If a configured port is unavailable or two services are configured for the same binding, the runner exits before starting any service.

After preflight, `bin/local-all` starts:

1. `bin/site-preview` when `SITE_ENABLED` is not `0`
2. `bin/local-studio`
3. `bin/local-admin` when `ADMIN_APP_ENABLED` is not `0`
4. `bin/local-analytics` when `ANALYTICS_APP_ENABLED` is not `0`
5. `docs-viewer/bin/docs-viewer`

The runner prints the public-site preview, Local Studio app, Local Admin app, Local Analytics app, and Docs Viewer web service URLs, or the disabled reason for skipped optional children.
If any child process exits, `bin/local-all` prints which service exited, stops the remaining children, and exits with a non-zero status for clean early exits or the failing child status otherwise.

### Local Studio

Before it starts long-running processes, `bin/local-studio` checks that the Local Studio app port is available when the app server is enabled.
If the port is unavailable, the runner exits immediately with a message naming `STUDIO_APP_PORT`.

`bin/local-studio` does not run startup docs/docs-search rebuilds or startup catalogue lookup export.
The local Studio app catalogue API refreshes derived lookup payloads after catalogue writes.

After startup preflight succeeds, it starts the long-running local processes below.

## Running Services

### Local Studio App

- command:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/studio_app_server.py --host "$STUDIO_APP_HOST" --port "$STUDIO_APP_PORT"
```

- default URL: `http://127.0.0.1:8765/studio/`

- mounts `/studio/`, retained Studio catalogue route shells, `/health`, `/studio/runtime-config.json`, and local catalogue APIs
- does not serve `/analytics/`, `/analytics/api/...`, `/docs/`, `/docs-viewer/...` assets, Docs Viewer generated reads, Docs Viewer management APIs, `/ui-catalogue/...`, or Data Sharing APIs
- links to Docs Viewer manage mode through the configured Docs Viewer web service URL
- can be disabled with `STUDIO_APP_ENABLED=0`
- access logging is quiet by default; set `STUDIO_APP_ACCESS_LOG=1` or pass `--access-log` to the app server for detailed request logging
- related doc: [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- route inventory: [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)
- endpoint inventory: [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis)

### Public Static Preview

Explicit public-site preview command:

```bash
bin/site-preview
```

It validates `site/`, then serves that checked-in static root with Python's HTTP server.

Explicit public-site validation command:

```bash
bin/site-validate
```

It runs:

```bash
$HOME/miniconda3/bin/python3 site-tools/site_validate.py
```

Both public-site commands use `site-tools/config/site-tools.json` by default and do not start local Studio services.

### Local Analytics App

Explicit Local Analytics command:

```bash
bin/local-analytics
```

It runs:

```bash
$HOME/miniconda3/bin/python3 analytics-app/app/server/analytics_app/analytics_app_server.py --host "$ANALYTICS_APP_HOST" --port "$ANALYTICS_APP_PORT"
```

- default URL: `http://127.0.0.1:8766/analytics/`
- owns Analytics tag routes under `/analytics/...`
- owns Analytics tag APIs under `/analytics/api/...`
- owns Data Sharing routes under `/analytics/data-sharing/...`
- owns Data Sharing APIs under `/analytics/api/data-sharing/...`
- uses `ANALYTICS_APP_HOST`, `ANALYTICS_APP_PORT`, and `ANALYTICS_APP_ACCESS_LOG`
- stays independent of Local Studio; `bin/local-all` only supervises it as a sibling child process
- intentionally does not provide compatibility aliases for old `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, or `/studio/api/data-sharing/...` paths

### Admin App

Explicit Admin command:

```bash
bin/local-admin
```

It runs:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/admin_app_server.py --host "$ADMIN_APP_HOST" --port "$ADMIN_APP_PORT"
```

- default URL: `http://127.0.0.1:8768/admin/`
- owns Admin pages under `/admin/...`
- owns Admin APIs under `/admin/api/...`
- uses `ADMIN_APP_HOST`, `ADMIN_APP_PORT`, and `ADMIN_APP_ACCESS_LOG`
- stays independent of Local Studio; `bin/local-all` only supervises it as a sibling child process
- intentionally does not provide compatibility aliases for old `/studio/audits/...`, `/studio/risk/...`, `/studio/activity/...`, `/studio/ui-catalogue/...`, or `/ui-catalogue/...` paths
- related doc: [Local Admin App](/docs/?scope=studio&doc=local-admin-app)

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

### Admin Operations

The Admin app owns the active browser-facing audit, risk, activity, and testing pages and APIs under `/admin/...`.
There is no standalone audit HTTP service fallback in `bin/local-studio`.
For direct automation, call:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/audit_runner.py --audit-id route-ready-state
```

Related doc: [Audit Runner](/docs/?scope=studio&doc=audit-runner).

### Docs Live Rebuild Watcher

The docs live rebuild watcher is a background rebuild helper started by `bin/local-studio`.
It is separate from the Docs Viewer web service.

- command:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_live_rebuild_watcher.py --poll-seconds "$DOCS_WATCH_POLL_SECONDS" --debounce-seconds "$DOCS_WATCH_DEBOUNCE_SECONDS"
```

- watches `docs-viewer/source/studio/*.md` as `studio`
- watches `docs-viewer/source/analysis/*.md` as `analysis`
- watches `docs-viewer/source/library/*.md` as `library`
- rebuilds same-scope docs payloads plus same-scope docs search after source changes
- can be disabled with `DOCS_WATCH_ENABLED=0`
- uses targeted docs-search updates for safe small source changes and full same-scope search rebuilds for threshold overflow or ambiguous source state
- related doc: [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

If you disable the watcher or want an explicit manual rebuild, use:

```bash
./docs-viewer/build/build_docs.py --scope studio --write
./docs-viewer/build/build_search.py --scope studio --write
./docs-viewer/build/build_docs.py --scope library --write
./docs-viewer/build/build_search.py --scope library --write
```

## What It Also Prints

At startup the runner prints quick links for:

- Start All service URLs when `bin/local-all` is used
- Local Studio App
- Local Admin App
- Local Analytics App
- Local Studio API ownership
- Docs Live Watcher status
- Series Tag Editor in Local Analytics:
  - `http://127.0.0.1:8766/analytics/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

`bin/local-all` and `bin/local-studio` both trap `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, `bin/local-all` stops the public-site preview when enabled, Local Studio runner, Local Admin runner, Local Analytics runner, and Docs Viewer service before exiting.

When you press `Ctrl+C` in `bin/local-studio`, it:

- stops the Local Studio App when enabled
- stops the Docs Live Rebuild Watcher when enabled
- waits for those child processes before exiting

If any `bin/local-all` child process exits unexpectedly, the runner stops the remaining children and reports the child name and exit status.
If either `bin/local-studio` child process exits unexpectedly, that runner stops monitoring and exits after waiting on the failed process.
