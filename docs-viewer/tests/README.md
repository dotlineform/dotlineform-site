# Docs Viewer Tests

Docs Viewer-owned focused tests live here after the shell/service extraction.

- `python/` contains pytest checks for Docs Viewer service modules, source models, generated reads, management workflows, imports, exports, and rebuild helpers.
- `smoke/` contains retained Playwright smoke scripts for Docs Viewer route boot, public read-only installs, and the standalone service manage route. Browser module-contract scripts are not required smoke targets.

Repo-level check profiles remain in `admin-app/commands/run_checks.py` so Codex and local workflows can still run the usual commands:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs
```

Studio-owned integration tests stay under `studio/tests/`.

Required Docs Viewer smoke entrypoints:

- `docs_viewer_service_manage.py`: standalone manage route boot, service generated reads, and one representative management action.
- `public_docs_viewer_readonly.py`: public Library and Analysis route boot, read-only state, and compact payload requests.

Focused route slice scripts such as `docs_viewer_routes.py` remain available for targeted route work when `/docs/` is served by an appropriate local target, but they are not part of the default Docs Viewer smoke profile.

The retired `docs_viewer_app_shell_modules.py` mega-smoke was removed because it duplicated route/config fixtures and tested too many implementation details in one browser script. Do not recreate that pattern.
