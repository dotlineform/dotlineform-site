---
doc_id: docs-viewer-portable-files
title: Portable File Manifest
added_date: 2026-05-19
last_updated: 2026-05-29
parent_id: docs-viewer-portable-setup
viewable: true
---
# Docs Viewer Portable File Manifest

## Files To Copy

These lists are the current copy set during the shell extraction, not the final standalone package boundary.
Reusable Docs Viewer runtime, CSS, config defaults, and UI text now live under `docs-viewer/`.
Docs Import is part of that package boundary when management mode is enabled.

### Viewer Shell

Copy:

- `docs-viewer/shell/docs-viewer-shell.html`
- `_includes/docs_viewer_shell.html`
- `_includes/docs_viewer_readonly_route.html`

If management mode should include Docs Import, also copy:

- the Docs Import modal markup embedded in `_includes/docs_viewer_shell.html`

The route adapter includes wrap `docs_viewer_shell.html` with the right public or management flags.
Examples in this repo are:

- `library/index.md`
- `analysis/index.md`

Use `docs_viewer_readonly_route.html` for public corpus routes such as `/library/` and `/analysis/`.
Use `docs-viewer/shell/docs-viewer-shell.html` through the standalone Docs Viewer service for the local `/docs/` management shell.
The standalone service renders route context and app-shell mounts only when `DOCS_VIEWER_MANAGEMENT_ENABLED` enables the management shell in `var/local/site.env`; the browser app shell renders the header controls, index panel chrome, management shell hosts, and action controls into those mounts.
The retired Jekyll `docs/index.md` management adapter should not be restored.

### Browser Runtime

Copy the shared viewer runtime files:

- `docs-viewer/runtime/js/docs-viewer.js`
- `docs-viewer/runtime/js/docs-viewer-app-boot.js`
- `docs-viewer/runtime/js/docs-viewer-app-composition.js`
- `docs-viewer/runtime/js/docs-viewer-app-session.js`
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- `docs-viewer/runtime/js/docs-viewer-app-shell.js`
- `docs-viewer/runtime/js/docs-viewer-app-context.js`
- `docs-viewer/runtime/js/docs-viewer-asset-url.js`
- `docs-viewer/runtime/js/docs-viewer-route-config.js`
- `docs-viewer/runtime/js/docs-viewer-access.js`
- `docs-viewer/runtime/js/docs-viewer-service-context.js`
- `docs-viewer/runtime/js/docs-viewer-config-service.js`
- `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`
- `docs-viewer/runtime/js/docs-viewer-document-index-state.js`
- `docs-viewer/runtime/js/docs-viewer-top-bar-renderer.js`
- `docs-viewer/runtime/js/docs-viewer-viewer-toolbar-renderer.js`
- `docs-viewer/runtime/js/docs-viewer-panel-layout.js`
- `docs-viewer/runtime/js/docs-viewer-view-state.js`
- `docs-viewer/runtime/js/docs-viewer-view-context.js`
- `docs-viewer/runtime/js/docs-viewer-hosted-views.js`
- `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`
- `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`
- `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`
- `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`
- `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`
- `docs-viewer/runtime/js/docs-viewer-config-controller.js`
- `docs-viewer/runtime/js/docs-viewer-data.js`
- `docs-viewer/runtime/js/docs-viewer-document-controller.js`
- `docs-viewer/runtime/js/docs-viewer-tree.js`
- `docs-viewer/runtime/js/docs-viewer-sidebar.js`
- `docs-viewer/runtime/js/docs-viewer-index-panel.js`
- `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`
- `docs-viewer/runtime/js/docs-viewer-search.js`
- `docs-viewer/runtime/js/docs-viewer-search-controller.js`
- `docs-viewer/runtime/js/docs-viewer-bookmarks.js`
- `docs-viewer/runtime/js/docs-viewer-favourites.js`
- `docs-viewer/runtime/js/docs-viewer-render.js`
- `docs-viewer/runtime/js/docs-viewer-report-service.js`
- `docs-viewer/runtime/js/docs-viewer-reports.js`
- `docs-viewer/runtime/js/docs-viewer-router.js`
- `docs-viewer/runtime/js/reports/`

For management mode, also copy:

- `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`
- `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`
- `docs-viewer/runtime/js/docs-viewer-management.js`
- `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js`
- `docs-viewer/runtime/js/docs-viewer-management-actions.js`
- `docs-viewer/runtime/js/docs-viewer-management-capabilities.js`
- `docs-viewer/runtime/js/docs-viewer-management-client.js`
- `docs-viewer/runtime/js/docs-viewer-management-config.js`
- `docs-viewer/runtime/js/docs-viewer-management-interactions.js`
- `docs-viewer/runtime/js/docs-viewer-management-modal-shell.js`
- `docs-viewer/runtime/js/docs-viewer-management-modals.js`
- `docs-viewer/runtime/js/docs-viewer-management-parent-picker.js`
- `docs-viewer/runtime/js/docs-viewer-management-render.js`
- `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js`
- `docs-viewer/runtime/js/docs-viewer-drag-drop.js`

For Docs Import inside the management modal, also copy:

- `docs-viewer/runtime/js/docs-html-import.js`
- `docs-viewer/runtime/js/docs-html-import-modals.js`
- `docs-viewer/runtime/js/docs-html-import-render.js`
- `docs-viewer/runtime/js/docs-html-import-workflow.js`

### CSS

Copy:

- `docs-viewer/static/css/docs-viewer-base.css`
- `docs-viewer/static/css/docs-viewer.css`
- `docs-viewer/static/css/docs-viewer-reports.css`
- `docs-viewer/static/css/docs-viewer-management.css`

The host site should still load its own base stylesheet for tokens, prose rules, responsive media defaults, and the `.content` contract used by generated docs HTML.
The viewer include now loads Docs Viewer-owned CSS for the portable base contract, shell, controls, index, search, results, bookmarks, status menu, report components, management surfaces, and the transitional Docs Import form/control primitives.
Public read-only routes may intentionally inherit public host CSS; standalone/local Docs Viewer shells should not require public `assets/css/main.css`.

### Config And UI Text

Copy:

- `docs-viewer/config/defaults/docs-viewer-config.json`
- `docs-viewer/config/defaults/docs-viewer-public-config.json`
- `docs-viewer/config/defaults/docs-viewer-service.json`
- `docs-viewer/config/routes/docs-viewer-routes.json`
- `docs-viewer/config/ui-text/ui-text.json`
- `docs-viewer/config/reports/reports.json`
- `assets/data/docs/reports.json`

`docs-viewer/config/routes/docs-viewer-routes.json` is the browser-safe route-config registry.
Route shells should point at it with `data-route-config-url` and identify themselves with `data-route-id`.
For standalone local manage mode, the Docs Viewer service serves this registry path with local loopback management/generated-read base URLs injected at request time.

`docs-viewer/config/defaults/docs-viewer-config.json` is projected from `docs-viewer/config/scopes/docs_scopes.json`.
It is required by the browser runtime and now includes the browser-safe Docs Viewer settings such as recently-added limits, hidden-doc styling, hidden-doc emoji, and per-scope UI-status options.
Each configured scope also carries its Docs Viewer search policy and search index URL in this browser config.
The viewer does not keep a hardcoded fallback scope list.
Docs Import copy is nested in `docs-viewer/config/ui-text/ui-text.json` under `docs_html_import`.
Settings-modal copy is also owned by `docs-viewer/config/ui-text/ui-text.json`.
`docs-viewer/config/reports/reports.json` is the source report metadata registry.
`assets/data/docs/reports.json` is the browser-visible report metadata projection.
It lists report ids, titles, descriptions, access defaults, and presets.
The executable report module allowlist remains in `docs-viewer/runtime/js/docs-viewer-reports.js`, so changing the JSON alone cannot make the viewer import an arbitrary module.

### Generated Data Outputs

Each docs scope needs generated viewer JSON:

- `assets/data/docs/scopes/<scope>/index.json`
- `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`

If inline docs search is enabled, each scope also needs:

- `assets/data/search/<scope>/index.json`

These files are generated outputs.
Copy them only if you are copying existing built content; otherwise generate them from source docs.

### Build Scripts

Copy:

- `docs-viewer/build/build_docs.py`
- `docs-viewer/config/scopes/docs_scopes.json`
- `studio/shared/python/markdown_renderer.py`

For inline docs search, copy:

- `docs-viewer/build/build_search.py`

Docs Viewer search scopes use `docs-viewer/build/build_search.py` directly.
The Catalogue search builder remains separate in this repo.
Adding a new docs scope should only require adding that scope to `docs-viewer/config/scopes/docs_scopes.json`, rebuilding docs data, and then running the Docs Viewer search builder for the new scope.

The target direction is tracked in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).

### Python Dependencies

Copy or recreate the Python dependency contract:

- `requirements.txt`

Install those pinned packages in the Python environment used to run the Docs Viewer build scripts, local management server, and Docs Import.
For the current repo, the Docs Viewer-specific import stack in `requirements.txt` is:

- `beautifulsoup4`: builds the HTML import parse tree
- `lxml`: parser backend used by Beautiful Soup
- `bleach`: sanitizer dependency for the Docs HTML import boundary
- `Pillow`: converts Markdown package images to 800px-max WebP outputs during Docs Import

`requirements.txt` is the Python script dependency contract.
It does not replace `Gemfile`, `Gemfile.lock`, or `.ruby-version`, which still own the Ruby/Jekyll build stack.
It also does not mean every package is required for a read-only static viewer route.
The parser/sanitizer/conversion packages are essential when the portable install includes Docs Import or the management server's import endpoints.

For the full dependency-role explanation, see [Docs Viewer Dependencies](/docs/?scope=studio&doc=docs-viewer-dependencies).

### Management Service

For local manage mode, copy the Docs Viewer service support:

- `docs-viewer/bin/docs-viewer`
- `docs-viewer/services/docs_viewer_service.py`
- `docs-viewer/services/docs_management_service.py`
- `docs-viewer/services/docs_management_routes.py`
- `docs-viewer/services/docs_management_context.py`
- `docs-viewer/services/docs_management_read_service.py`
- `docs-viewer/services/docs_management_capabilities_service.py`
- `docs-viewer/services/docs_management_mutation_service.py`
- `docs-viewer/services/docs_management_import_service.py`
- `docs-viewer/services/docs_management_source_service.py`
- `docs-viewer/services/docs_management_broken_links_service.py`
- `docs-viewer/services/docs_scope_config.py`
- `docs-viewer/services/docs_source_model.py`
- `docs-viewer/services/docs_management_mutations.py`
- `docs-viewer/services/docs_write_rebuild.py`
- `docs-viewer/services/docs_generated_reads.py`
- `docs-viewer/services/docs_import_source_service.py`
- `docs-viewer/services/docs_html_import.py`
- `docs-viewer/services/docs_activity.py`
- `docs-viewer/services/docs_watch_suppression.py`

Optional adjacent docs tools:

- `docs-viewer/services/docs_live_rebuild_watcher.py`
- `docs-viewer/services/docs_broken_links.py`
- `docs-viewer/services/docs_export.py`
- `docs-viewer/services/docs_import.py`

The management service is local-only and should be exposed only through the loopback-bound standalone Docs Viewer service.
It is not part of the public static site.
The v1 service reads host, port, base URL, and capability flags from `var/local/site.env`.
Generated-data reads, source writes, import targets, and rebuild commands use `docs-viewer/config/scopes/docs_scopes.json` as the docs scope contract.
The local management package also includes the read-only source config report and the Settings modal.
The report inspects configured source, browser, and generated projections.
The Settings modal writes only allowlisted source config fields; the first portable field is scoped `show_updated_date`, which saves to `docs-viewer/config/scopes/docs_scopes.json` and triggers a same-scope docs rebuild.
For the full config split and media-storage choices, see [Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer).
