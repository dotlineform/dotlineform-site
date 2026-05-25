# Docs Viewer Tests

Docs Viewer-owned focused tests live here after the shell/service extraction.

- `python/` contains pytest checks for Docs Viewer service modules, source models, generated reads, management workflows, imports, exports, and rebuild helpers.
- `smoke/` contains Playwright smoke scripts for the Docs Viewer service, public read-only installs, management UI, and browser runtime modules.

Repo-level check profiles remain in `studio/commands/run_checks.py` so Codex and local workflows can still run the usual commands:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs
```

Studio-owned integration tests stay under `studio/tests/`.
