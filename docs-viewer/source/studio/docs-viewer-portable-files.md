---
doc_id: docs-viewer-portable-files
title: Portable File Manifest
added_date: 2026-05-19
last_updated: 2026-06-22
parent_id: docs-viewer-portable-setup
viewable: true
---
# Docs Viewer Portable File Manifest

## Files To Copy

- These lists are the current copy set during the shell extraction, not the final standalone package boundary.
- Reusable Docs Viewer runtime, CSS, config defaults, and UI text live under `docs-viewer/`.
- Docs Import is part of that package boundary when management mode is enabled.

### Viewer Shell

Copy:

- `docs-viewer/shell/docs-viewer-manage.html`
- `docs-viewer/templates/public-route/index.html`

If management mode should include Docs Import, also copy:

- `docs-viewer/runtime/js/import/`
- the management UI text used by Docs Import

Current public route shell examples in this repo are:

- `site/library/index.html`
- `site/analysis/index.html`

Use `docs-viewer/templates/public-route/index.html` to create new public corpus routes such as `/research/`.
In this repo, New Scope renders that template into `site/<route>/index.html` during the local lifecycle write action.

Use `docs-viewer/shell/docs-viewer-manage.html` through the standalone Docs Viewer service for the local `/docs/` management shell.

The standalone service serves the static shell and dynamic route config separately; the browser app shell reads route state through `data-*` attributes and renders the header controls, index panel chrome, management shell hosts, and action controls into those mounts.

### Browser Runtime

Copy the shared viewer runtime files:

- `site/docs-viewer/runtime/js/public/docs-viewer-public.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-session.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-shell.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-asset-url.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-access.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-service-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-config-service.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-document-index-state.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-top-bar-renderer.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-view-state.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-view-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-hosted-views.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-metadata-info-view.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-runtime-lazy-controller.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-config-controller.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-data.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-tree.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-sidebar.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-index-panel.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-index-panel-renderer.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-search.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-search-controller.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-bookmarks.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-favourites.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-render.js`
- `docs-viewer/runtime/js/reports/docs-viewer-report-service.js`
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-router.js`
- `docs-viewer/runtime/js/reports/`

For management mode, also copy:

- `docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js`
- `docs-viewer/runtime/js/management/docs-viewer-management.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-action-workflow.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-actions.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-capabilities.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-client.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-config.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-interactions.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-modal-shell.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-modals.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-parent-picker.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-render.js`
- `docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js`
- `docs-viewer/runtime/js/management/docs-viewer-drag-drop.js`

For Docs Import inside the management modal, also copy:

- `docs-viewer/runtime/js/import/docs-html-import.js`
- `docs-viewer/runtime/js/import/docs-html-import-modals.js`
- `docs-viewer/runtime/js/import/docs-html-import-render.js`
- `docs-viewer/runtime/js/import/docs-html-import-workflow.js`

### CSS

Copy:

- `site/docs-viewer/static/css/docs-viewer.css`
- `docs-viewer/static/css/docs-viewer-reports.css`
- `docs-viewer/static/css/docs-viewer-manage.css`

The host site should still load its own base stylesheet for tokens, prose rules, responsive media defaults, and the `.content` contract used by generated docs HTML.

The public viewer include loads Docs Viewer-owned CSS for the portable base contract, public shell, controls, index, search, results, and bookmarks through `/docs-viewer/static/css/docs-viewer.css`, backed by `site/docs-viewer/static/css/docs-viewer.css`.

The local manage shell loads the basic viewer stylesheet, report stylesheet, management stylesheet, and transitional Docs Import form/control primitives.

Public read-only routes may intentionally inherit public host CSS; standalone/local Docs Viewer shells should not require public `site/assets/css/main.css`.

### Config And UI Text

Copy:

- `docs-viewer/config/defaults/docs-viewer-config.json`
- `docs-viewer/config/defaults/docs-viewer-public-config.json`
- `docs-viewer/config/defaults/docs-viewer-service.json`
- `docs-viewer/config/routes/docs-viewer-routes.json`
- `docs-viewer/config/reports/reports.json`
- `site/assets/data/docs/public-reports.json`

`docs-viewer/config/routes/docs-viewer-routes.json` is the browser-safe manage/local route-config registry.
`site/docs-viewer/config/routes/docs-viewer-public-routes.json` is the browser-safe public route-config registry served at `/docs-viewer/config/routes/docs-viewer-public-routes.json`.
Public and manage route UI copy is design-time runtime text in the Docs Viewer JavaScript modules.
Route shells should point at the appropriate registry with `data-route-config-url` and identify themselves with `data-route-id`.

For standalone local manage mode, the Docs Viewer service serves this registry path with local loopback management/generated-read base URLs injected at request time.

`docs-viewer/config/defaults/docs-viewer-config.json` is projected from `docs-viewer/config/scopes/docs_scopes.json`.

It is required by the browser runtime and now includes the browser-safe Docs Viewer settings such as recently-added limits, non-viewable-doc styling, non-viewable-doc emoji, and per-scope UI-status options.

Each configured scope also carries its Docs Viewer search policy and search index URL in this browser config.

The viewer does not keep a hardcoded fallback scope list.

Local/manage copy is design-time runtime text owned by the management and import JavaScript modules.

`docs-viewer/config/reports/reports.json` is the source report metadata registry.

`site/assets/data/docs/public-reports.json` is the public browser-visible report metadata projection.

It lists only report ids, titles, descriptions, access defaults, and presets that have been explicitly promoted for public routes.
Executable report module allowlists remain in `docs-viewer/runtime/js/reports/docs-viewer-reports.js` and `site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js`, so changing JSON alone cannot make the viewer import an arbitrary module.

### Generated Data Outputs

Each docs scope needs generated viewer JSON.
The storage root depends on the scope mode.

Repo-backed local and public scopes use working generated output under:

- `docs-viewer/generated/docs/<scope>/index-tree.json`
- `docs-viewer/generated/docs/<scope>/recently-added.json`
- `docs-viewer/generated/docs/<scope>/by-id/<doc_id>.json`
- `docs-viewer/generated/search/<scope>/index.json`

Public read-only scopes also publish reviewed snapshots under:

- `site/assets/data/docs/scopes/<scope>/index-tree.json`
- `site/assets/data/docs/scopes/<scope>/recently-added.json`
- `site/assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`
- `site/assets/data/search/<scope>/index.json`

External local scopes keep working source and generated data outside the repo under:

- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`
- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/docs/<scope>/`
- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/search/<scope>/index.json`

These files are generated outputs. Copy them only if you are copying existing built content; otherwise generate them from source docs.
External local generated outputs are not public static-site files and should be read through the standalone Docs Viewer service.

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
It does not mean every package is required for a read-only static viewer route.
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

The management service is local-only and should be exposed only through the loopback-bound standalone Docs Viewer service. It is not part of the public static site.

The v1 service reads host, port, base URL, and capability flags from `var/local/site.env`.

Generated-data reads, source writes, import targets, and rebuild commands use `docs-viewer/config/scopes/docs_scopes.json` as the docs scope contract.

The local management package also includes the read-only source config report and the Settings modal. The report inspects configured source, browser, and generated projections.

The Settings modal exposes the active scope's `default_doc_id`. Scope-level display controls should write only allowlisted source config fields and rebuild affected generated docs scopes when browser payloads need to stay in sync.

For the full config split and media-storage choices, see [Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer).
