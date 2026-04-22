---
doc_id: scripts-docs-live-rebuild-watcher
title: "Docs Live Rebuild Watcher"
last_updated: 2026-04-22
parent_id: scripts
sort_order: 18
---
# Docs Live Rebuild Watcher

Script:

```bash
./scripts/docs/docs_live_rebuild_watcher.py
```

## Purpose

This script watches the docs source roots used by the shared Docs Viewer and rebuilds same-scope docs payloads plus same-scope docs search after source changes.

It is intended as a local development helper for `bin/dev-studio`, not as the primary manual rebuild command.

## Scope Detection

The watcher maps source roots directly onto docs scopes:

- `_docs_src/*.md` -> `studio`
- `_docs_library_src/*.md` -> `library`

It watches source roots only. It does not watch generated outputs under:

- `assets/data/docs/scopes/`
- `assets/data/search/`

## Default Command

Run from `dotlineform-site/`:

```bash
./scripts/docs/docs_live_rebuild_watcher.py
```

Default behavior:

- polls the source roots every `1.0` second
- debounces rebuilds for `1.0` second after the most recent source change
- runs one scope at a time
- triggers another same-scope pass if more source changes arrive during a rebuild

## Optional Flags

- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--bundle-bin /path/to/bundle`: override bundle executable path
- `--poll-seconds 1.0`: polling interval
- `--debounce-seconds 1.0`: quiet window before rebuild

## What It Runs

When the watcher sees a change for one scope, it runs:

```bash
./scripts/build_docs.rb --scope <scope> --write
./scripts/build_search.rb --scope <scope> --write
```

That means a source change under one docs root keeps both:

- the current scope docs-viewer JSON
- the current scope docs-search artifact

in sync without touching the other docs scope.

## Change Types

The watcher treats these root-level Markdown changes as rebuild triggers:

- create
- edit
- delete
- rename

It does this by comparing the current root-level `.md` file set, file mtimes, and file sizes on each poll.

## Operational Notes

- `bin/dev-studio` starts this watcher by default
- `bin/dev-studio` no longer performs a default startup docs/docs-search rebuild; startup rebuilds are opt-in through `DOCS_STARTUP_REBUILD_SCOPES`
- manual rebuild commands remain available and are still the fallback path when you want explicit control
- because the watcher rebuilds from source-root changes only, generated output writes do not loop back into new watcher-triggered rebuilds

## Related References

- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)
