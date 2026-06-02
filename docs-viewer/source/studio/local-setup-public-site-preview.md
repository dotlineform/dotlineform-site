---
doc_id: local-setup-public-site-preview
title: Local Setup Public Site Preview
added_date: 2026-05-23
last_updated: 2026-05-23
parent_id: local-setup
---
# Local Setup Public Site Preview

The public Jekyll site and Local Studio use separate commands.

Use `bin/local-studio` for Studio services.
Use `bin/public-site-preview` or `bin/public-site-build` for public-site Jekyll work.

## Preview versus build

`bin/public-site-preview` starts a local Jekyll preview server.
It is the normal command when you want to open the public site in a browser while editing public pages, layouts, includes, CSS, or public assets.

```bash
bin/public-site-preview
```

The preview command runs Jekyll serve with the repo defaults:

```bash
bundle exec jekyll serve
```

`bin/public-site-build` runs a one-shot static build and exits.
Use it when you want to produce or verify the built site output without keeping a local preview server running.

```bash
bin/public-site-build
```

The build command runs:

```bash
bundle exec jekyll build
```

`bin/public-site-build` passes extra arguments through to Jekyll, so an isolated output directory can be requested like this:

```bash
bin/public-site-build --destination /tmp/dlf-jekyll-build
```

## CSS changes

`bin/public-site-preview` uses Jekyll serve, so Jekyll watches public-site source files and rebuilds changed pages and assets.
The public Jekyll config excludes local Studio docs source, UI Catalogue source, and Studio-only asset roots, so ordinary Local Studio documentation and UI Catalogue edits do not trigger public-site preview rebuilds.
For CSS changes, save the file and refresh the browser page.

This is watch-and-rebuild behavior, not hot module replacement.

Notes:

- CSS files copied directly by Jekyll are available after the next rebuild.
- Sass/SCSS files are compiled by Jekyll before the browser sees the change.
- Browser cache can hide a CSS update; hard refresh if the page still shows the old styles.
- Jekyll config changes normally require restarting `bin/public-site-preview`.

## Local-only watch excludes

The public Jekyll config excludes these local-only roots from conversion and watch:

- `docs-viewer/source/studio/`
- `docs-viewer/source/analysis/`
- `docs-viewer/source/library/`
- `_docs_catalogue/`
- `_ui_catalogue_notes/`
- `_includes/ui_catalogue_notes/`
- `docs/`
- `studio/`
- `assets/ui-catalogue/`
- `assets/docs/ui-catalogue/`
- `assets/studio/`
- `docs-viewer/generated/docs/studio/`
- `docs-viewer/generated/search/studio/`

Restart `bin/public-site-preview` after changing `_config.yml`; an already-running Jekyll process does not reload updated exclude rules.

Committed manage-mode Docs Viewer scopes should keep generated runtime JSON under `docs-viewer/generated/`.
Those payloads are for local Docs Viewer service reads, not public Jekyll preview/build output.
If another committed manage-mode scope is added, keep its generated docs/search payloads under `docs-viewer/generated/` and keep that root excluded from public Jekyll builds.

## LiveReload

Jekyll can also refresh the browser automatically after rebuilds with LiveReload:

```bash
bin/public-site-preview --livereload
```

LiveReload is useful for public-site styling work because the browser tab reloads after Jekyll rebuilds.
It is still page reload behavior, not true CSS hot injection.

LiveReload caveats:

- The page must be loaded from the Jekyll preview server.
- The LiveReload websocket must be able to connect.
- The LiveReload port can occasionally conflict with another local process.
- It only affects the public Jekyll preview; it does not start or refresh Local Studio services.
- Generated Studio or Docs Viewer payloads still depend on their own watcher/build flows.

The project wrapper keeps LiveReload off by default.
Enable it per run with `bin/public-site-preview --livereload`.
To make it the local default, set this in `var/local/site.env`:

```bash
export PUBLIC_SITE_LIVERELOAD=1
```

Use `--no-livereload` to override that local default for a single run.

## Wrapper versus raw Jekyll

`bin/public-site-preview` is intentionally a thin project wrapper around `bundle exec jekyll serve`.
It adds repo defaults, but raw `bundle exec jekyll serve` is also a supported public-preview workflow.

The wrapper:

- changes into the repo root
- loads `var/local/site.env` when present
- prefers the configured Bundler shim when available
- uses `PUBLIC_SITE_CONFIG`, defaulting to `_config.yml`
- uses `PUBLIC_SITE_HOST` or `JEKYLL_HOST`, defaulting to `127.0.0.1`
- uses `PUBLIC_SITE_PORT` or `JEKYLL_PORT`, defaulting to `4000`
- uses `PUBLIC_SITE_LIVERELOAD`, defaulting to disabled

In practice, this command:

```bash
bin/public-site-preview
```

is roughly equivalent to:

```bash
bundle exec jekyll serve \
  --config _config.yml \
  --host 127.0.0.1 \
  --port 4000
```

Use `bin/public-site-preview` when you want those defaults loaded from `var/local/site.env`.
Use raw `bundle exec jekyll serve` when you want the direct Jekyll command without repo wrapper behavior.

## Related References

- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
