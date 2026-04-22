---
doc_id: scripts-dev-studio
title: "Dev Studio Runner"
last_updated: 2026-04-22
parent_id: scripts
sort_order: 15
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
- refresh the derived catalogue lookup payloads used by the catalogue editors
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
- prefers `~/.rbenv/shims/bundle` when present
- prefers `~/miniconda3/bin/python3` when present
- otherwise falls back to `bundle` and `python3`

## Optional Environment Overrides

The runner does not currently take CLI flags. It is configured through environment variables:

- `JEKYLL_HOST`
  default: `127.0.0.1`
- `JEKYLL_PORT`
  default: `4000`
- `TAG_WRITE_PORT`
  default: `8787`
- `CATALOGUE_WRITE_PORT`
  default: `8788`
- `DOCS_MANAGEMENT_PORT`
  default: `8789`
- `DOCS_STARTUP_REBUILD_SCOPES`
  default: blank
  accepted values: `studio`, `library`, or `studio,library`
- `DOCS_WATCH_ENABLED`
  default: `1`
- `DOCS_WATCH_POLL_SECONDS`
  default: `1.0`
- `DOCS_WATCH_DEBOUNCE_SECONDS`
  default: `1.0`

Example:

```bash
DOCS_STARTUP_REBUILD_SCOPES=studio JEKYLL_PORT=4001 TAG_WRITE_PORT=8797 CATALOGUE_WRITE_PORT=8798 DOCS_MANAGEMENT_PORT=8799 DOCS_WATCH_DEBOUNCE_SECONDS=1.5 bin/dev-studio
```

That form applies the environment overrides to that one `bin/dev-studio` run only.

If you want the variable available by default in your shell, add an export to your shell startup file instead, for example:

```bash
export DOCS_STARTUP_REBUILD_SCOPES=""
```

Then you can either:

- run `bin/dev-studio` and keep the startup docs/docs-search rebuild scopes blank
- or temporarily override the exported value for one run with `DOCS_STARTUP_REBUILD_SCOPES=studio bin/dev-studio`

## Startup Sequence

Before it starts any rebuilds or long-running servers, `bin/dev-studio` checks that the required ports are available:

1. Jekyll on `JEKYLL_HOST:JEKYLL_PORT`
2. Tag Write Server on `127.0.0.1:TAG_WRITE_PORT`
3. Catalogue Write Server on `127.0.0.1:CATALOGUE_WRITE_PORT`
4. Docs Management Server on `127.0.0.1:DOCS_MANAGEMENT_PORT`

If any port is unavailable, the runner exits immediately with a message naming the affected service and environment variable override.

After that preflight, `bin/dev-studio` runs the startup write steps below:

1. if `DOCS_STARTUP_REBUILD_SCOPES` is set, it runs:
   - `./scripts/build_docs.rb --scope <scope> --write`
   - `./scripts/build_search.rb --scope <scope> --write`
   for each listed docs scope
2. `./scripts/export_catalogue_lookup.py --write`

That means a fresh `bin/dev-studio` run always updates:

- derived catalogue lookup JSON under `assets/studio/data/catalogue_lookup/`

If `DOCS_STARTUP_REBUILD_SCOPES` is set, it also updates:

- scope-matching docs-viewer JSON under `assets/data/docs/scopes/<scope>/`
- scope-matching docs-search JSON under `assets/data/search/<scope>/`

After those startup writes succeed, it starts the long-running local processes below.

## Running Services

### Jekyll

- command:

```bash
bundle exec jekyll serve --host "$JEKYLL_HOST" --port "$JEKYLL_PORT"
```

- default URL: `http://127.0.0.1:4000`
- serves the local site and Studio routes

### Tag Write Server

- command:

```bash
./scripts/studio/tag_write_server.py --port "$TAG_WRITE_PORT"
```

- default URL: `http://127.0.0.1:8787`
- related doc: [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)

### Catalogue Write Server

- command:

```bash
./scripts/studio/catalogue_write_server.py --port "$CATALOGUE_WRITE_PORT"
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

### Docs Live Rebuild Watcher

- command:

```bash
./scripts/docs/docs_live_rebuild_watcher.py --poll-seconds "$DOCS_WATCH_POLL_SECONDS" --debounce-seconds "$DOCS_WATCH_DEBOUNCE_SECONDS"
```

- watches `_docs_src/*.md` as `studio`
- watches `_docs_library_src/*.md` as `library`
- rebuilds same-scope docs payloads plus same-scope docs search after source changes
- can be disabled with `DOCS_WATCH_ENABLED=0`
- related doc: [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## What It Also Prints

At startup the runner prints quick links for:

- Jekyll root
- Tag Write Server
- Catalogue Write Server
- Docs Management Server
- startup docs rebuild scopes
- Docs Live Watcher status
- Series Tag Editor:
  - `http://127.0.0.1:4000/studio/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

The runner traps `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, it:

- stops Jekyll
- stops the Tag Write Server
- stops the Catalogue Write Server
- stops the Docs Management Server
- stops the Docs Live Rebuild Watcher when enabled
- waits for those child processes before exiting

If any one of the child processes exits unexpectedly, the runner stops monitoring and exits after waiting on that failed process.

## What It Does Not Do

`bin/dev-studio` does not currently:

- run `./scripts/catalogue_json_build.py`
- rebuild any docs/docs-search scope on startup unless `DOCS_STARTUP_REBUILD_SCOPES` is set
- rebuild catalogue or public search artifacts on startup
- start a separate frontend asset server

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
