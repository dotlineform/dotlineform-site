# Docs Viewer Tests

Docs Viewer-owned focused tests live here after the shell/service extraction.

- `python/` contains pytest checks for Docs Viewer service modules, source models, generated reads, management workflows, imports, exports, and rebuild helpers.
- `smoke/` contains four retained Playwright boundaries plus one small shared route harness. It is not a browser unit-test directory.

Repo-level check profiles live in `tests/run_checks.py` so Codex and local workflows can run coordinated evidence without assigning it to an application:

```bash
$HOME/miniconda3/bin/python3 tests/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 tests/run_checks.py --profile docs
```

Studio-owned integration tests stay under `studio/tests/`.

Retained Docs Viewer smoke entrypoints:

- `docs_viewer_service_manage.py`: standalone Manage route boot and configured service projection.
- `docs_viewer_service_review.py`: Docs Review route boot, package-provider reads, and API-authority boundary.
- `public_docs_viewer_readonly.py`: public Analysis route boot, compact payload reads, and absence of local capability.
- `docs_viewer_external_inline_mermaid_route.py`: external-local scope build, lazy Mermaid loading, and browser rendering.

`docs_viewer_route_smoke_support.py` owns only temporary server startup and ready-document waiting. Executable smokes must not become fixture libraries for other workflow tests.

UI behavior is accepted manually unless a retained boundary above is the actual risk. Do not recreate browser module-contract suites, real-route workflow matrices, or broad narrative smokes.
