# Docs Viewer Tests

Docs Viewer-owned focused tests live here after the shell/service extraction.

- `python/` contains pytest checks for Docs Viewer service modules, source models, generated reads, management workflows, imports, exports, and rebuild helpers.
- `smoke/` contains Playwright smoke scripts for the Docs Viewer service, public read-only installs, management UI, browser runtime modules, and focused route behavior slices.

Repo-level check profiles remain in `studio/commands/run_checks.py` so Codex and local workflows can still run the usual commands:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs
```

Studio-owned integration tests stay under `studio/tests/`.

Focused route smoke entrypoints:

- `docs_viewer_route_navigation.py`: route navigation, internal link interception, history, and Library route path behavior.
- `docs_viewer_route_index_panel.py`: index-panel collapse/expand/restore behavior and expanded tree navigation.
- `docs_viewer_route_search_missing_hash.py`: search-route state, missing-doc routing, history recovery, and hash-target behavior.
- `docs_viewer_routes.py`: aggregate wrapper for the focused route smoke slices.

These focused route entrypoints need a target that serves `/docs/`. A temporary public Jekyll build may only expose public `/library/` and `/analysis/` routes.
