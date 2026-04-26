---
doc_id: scripts-docs-live-rebuild-watcher
title: "Docs Live Rebuild Watcher"
added_date: 2026-04-24
last_updated: 2026-04-26
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
- `_docs_src_analysis/**/*.md` -> `analysis`
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
- uses targeted docs-search updates for source changes at or below the targeted threshold when affected doc ids can be computed from parsed snapshots
- falls back to a full same-scope docs-search rebuild when affected ids are ambiguous
- skips a duplicate same-scope pass when a docs-management write has already rebuilt that source change and left a short-lived watcher suppression marker

## Optional Flags

- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--bundle-bin /path/to/bundle`: override bundle executable path
- `--poll-seconds 1.0`: polling interval
- `--debounce-seconds 1.0`: quiet window before rebuild
- `--targeted-search-threshold 5`: maximum changed file count for targeted docs-search updates; use `-1` to target whenever the affected ids are safe

## What It Runs

When the watcher sees a change for one scope, it runs:

```bash
./scripts/build_docs.rb --scope <scope> --write
./scripts/build_search.rb --scope <scope> --write --only-doc-ids <ids> --remove-missing
```

When the changed-file count exceeds `--targeted-search-threshold`, or when the parsed snapshot cannot safely identify affected ids, the search step falls back to:

```bash
./scripts/build_search.rb --scope <scope> --write
```

That means a source change under one docs root keeps both:

- the current scope docs-viewer JSON
- the current scope docs-search artifact

in sync without touching the other docs scopes.

## Change Types

The watcher treats these Markdown changes as rebuild triggers:

- create
- edit
- delete
- rename

It does this by comparing the current `.md` file set, file mtimes, and file sizes on each poll.
Studio and Library watch only root-level `.md` files. Analysis watches nested `.md` files under `_docs_src_analysis/`.

For targeted search, it also keeps a parsed per-scope source snapshot from the last successful watcher rebuild. The snapshot maps filenames to front-matter-derived values including `doc_id`, `title`, `parent_id`, `published`, and `viewable`. The watcher does not assume filename equals `doc_id`.

Targeted affected-id rules:

- added file: target the new `doc_id`
- edited file: target the current `doc_id`
- deleted file: target the previous `doc_id`
- `doc_id` changed: target both old and new ids
- `title` changed: target the doc plus direct children, because child search records include `parent_title`
- `parent_id` changed: target only the changed doc under the current search schema
- parse failure, invalid docs tree, missing parsed snapshot, or threshold overflow: run full same-scope docs search

## Operational Notes

- `bin/dev-studio` starts this watcher by default
- `bin/dev-studio` no longer performs a default startup docs/docs-search rebuild; startup rebuilds are opt-in through `DOCS_STARTUP_REBUILD_SCOPES`
- `DOCS_WATCH_TARGETED_SEARCH_THRESHOLD` controls the default targeted threshold when the watcher is started through `bin/dev-studio`
- manual rebuild commands remain available and are still the fallback path when you want explicit control
- because the watcher rebuilds from source-root changes only, generated output writes do not loop back into new watcher-triggered rebuilds
- when the localhost docs-management server writes a source doc and rebuilds the same scope itself, it now leaves a short-lived suppression marker under `var/docs/watch-suppressions/`; the watcher uses that marker to avoid a redundant second rebuild for the same source change
- `var/` is excluded from Jekyll so transient watcher-suppression marker writes do not trigger Jekyll serve regenerations or file-watch stat races

## Related References

- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)
