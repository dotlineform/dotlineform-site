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

- refresh the Studio docs payloads used by the Docs Viewer
- refresh the derived catalogue lookup payloads used by the catalogue editors
- start the Jekyll site
- start the local Studio write services used by the current admin UI

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
- `CATALOGUE_WRITE_PORT`
  default: `8788`
- `DOCS_MANAGEMENT_PORT`
  default: `8789`

Example:

```bash
JEKYLL_PORT=4001 CATALOGUE_WRITE_PORT=8798 DOCS_MANAGEMENT_PORT=8799 bin/dev-studio
```

The Tag Write Server is currently started on fixed port `8787`.

## Startup Sequence

Before it starts any long-running servers, `bin/dev-studio` runs two write steps:

1. `./scripts/build_docs.rb --scope studio --write`
2. `./scripts/export_catalogue_lookup.py --write`

That means a fresh `bin/dev-studio` run updates:

- Studio docs-viewer JSON under `assets/data/docs/scopes/studio/`
- derived catalogue lookup JSON under `assets/studio/data/catalogue_lookup/`

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
./scripts/studio/tag_write_server.py
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

## What It Also Prints

At startup the runner prints quick links for:

- Jekyll root
- Tag Write Server
- Catalogue Write Server
- Docs Management Server
- Series Tag Editor:
  - `http://127.0.0.1:4000/studio/series-tag-editor/?series=<series_id>`

## Shutdown Behavior

The runner traps `EXIT`, `INT`, and `TERM`.

When you press `Ctrl+C`, it:

- stops Jekyll
- stops the Tag Write Server
- stops the Catalogue Write Server
- stops the Docs Management Server
- waits for those child processes before exiting

If any one of the child processes exits unexpectedly, the runner stops monitoring and exits after waiting on that failed process.

## What It Does Not Do

`bin/dev-studio` does not currently:

- run `./scripts/build_search.rb`
- run `./scripts/catalogue_json_build.py`
- rebuild catalogue or public search artifacts on startup
- start a separate frontend asset server

If you need docs search updated after docs changes, run:

```bash
./scripts/build_search.rb --scope studio --write
```

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
