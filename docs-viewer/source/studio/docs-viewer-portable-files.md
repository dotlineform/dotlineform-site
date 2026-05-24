---
doc_id: docs-viewer-portable-files
title: Docs Viewer Portable File Manifest
added_date: 2026-05-19
last_updated: 2026-05-20
parent_id: docs-viewer-portable-setup
sort_order: 3100
---
# Docs Viewer Portable File Manifest

## Files To Copy

These lists are the current copy set, not the desired future package boundary.
Reusable Docs Viewer runtime, CSS, and UI text now lives under `assets/docs-viewer/`.
Docs Import is part of that package boundary when management mode is enabled.

### Viewer Shell

Copy:

- `_includes/docs_viewer_shell.html`
- `_includes/docs_viewer_readonly_route.html`
- `_includes/docs_viewer_management_route.html`

If management mode should include Docs Import, also copy:

- the Docs Import modal markup embedded in `_includes/docs_viewer_shell.html`

The route adapter includes wrap `docs_viewer_shell.html` with the right public or management flags.
Examples in this repo are:

- `docs/index.md`
- `library/index.md`
- `analysis/index.md`

Use `docs_viewer_readonly_route.html` for public corpus routes such as `/library/` and `/analysis/`.
Use `docs_viewer_management_route.html` for the local `/docs/` management shell.
That adapter renders management markup only when `docs_viewer_management_enabled: true`; public Jekyll config leaves the flag false, while Local Studio serves `/docs/` management through the Python app server.

### Browser Runtime

Copy the shared viewer runtime files:

- `assets/docs-viewer/js/docs-viewer.js`
- `assets/docs-viewer/js/docs-viewer-config-controller.js`
- `assets/docs-viewer/js/docs-viewer-data.js`
- `assets/docs-viewer/js/docs-viewer-document-controller.js`
- `assets/docs-viewer/js/docs-viewer-tree.js`
- `assets/docs-viewer/js/docs-viewer-sidebar.js`
- `assets/docs-viewer/js/docs-viewer-search.js`
- `assets/docs-viewer/js/docs-viewer-search-controller.js`
- `assets/docs-viewer/js/docs-viewer-bookmarks.js`
- `assets/docs-viewer/js/docs-viewer-favourites.js`
- `assets/docs-viewer/js/docs-viewer-render.js`
- `assets/docs-viewer/js/docs-viewer-reports.js`
- `assets/docs-viewer/js/docs-viewer-router.js`
- `assets/docs-viewer/js/reports/`

For management mode, also copy:

- `assets/docs-viewer/js/docs-viewer-management.js`
- `assets/docs-viewer/js/docs-viewer-management-actions.js`
- `assets/docs-viewer/js/docs-viewer-management-capabilities.js`
- `assets/docs-viewer/js/docs-viewer-management-client.js`
- `assets/docs-viewer/js/docs-viewer-management-config.js`
- `assets/docs-viewer/js/docs-viewer-management-interactions.js`
- `assets/docs-viewer/js/docs-viewer-management-modals.js`
- `assets/docs-viewer/js/docs-viewer-management-render.js`
- `assets/docs-viewer/js/docs-viewer-scope-lifecycle.js`
- `assets/docs-viewer/js/docs-viewer-drag-drop.js`

For Docs Import inside the management modal, also copy:

- `assets/docs-viewer/js/docs-html-import.js`
- `assets/docs-viewer/js/docs-html-import-modals.js`

### CSS

Copy:

- `assets/docs-viewer/css/docs-viewer-management.css`
- `assets/docs-viewer/css/docs-viewer.css`
- `assets/docs-viewer/css/docs-viewer-reports.css`

The host site should still load its own base stylesheet for tokens, prose rules, responsive media defaults, and the `.content` contract used by generated docs HTML.
The viewer include now loads Docs Viewer-owned CSS for the shell, controls, index, search, results, bookmarks, status menu, management surfaces, and the transitional Docs Import form/control primitives.
Management mode no longer loads `assets/studio/css/studio.css`.

### Config And UI Text

Copy:

- `assets/docs-viewer/data/docs-viewer-config.json`
- `assets/docs-viewer/data/ui-text.json`
- `assets/data/docs/reports.json`

`assets/docs-viewer/data/docs-viewer-config.json` is generated from `studio/docs-viewer/config/scopes/docs_scopes.json`.
It is required by the browser runtime and now includes the browser-safe Docs Viewer settings such as recently-added limits, hidden-doc styling, hidden-doc emoji, and per-scope UI-status options.
Each configured scope also carries its Docs Viewer search policy and search index URL in this browser config.
The viewer does not keep a hardcoded fallback scope list.
Docs Import copy is nested in `assets/docs-viewer/data/ui-text.json` under `docs_html_import`.
Settings-modal copy is also owned by `assets/docs-viewer/data/ui-text.json`.
`assets/data/docs/reports.json` is the browser-visible report metadata registry.
It lists report ids, titles, descriptions, access defaults, and presets.
The executable report module allowlist remains in `assets/docs-viewer/js/docs-viewer-reports.js`, so changing the JSON alone cannot make the viewer import an arbitrary module.

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

- `scripts/build_docs.rb`
- `studio/docs-viewer/build/build_docs.rb`
- `studio/docs-viewer/config/scopes/docs_scopes.json`
- `scripts/jekyll_markdown_renderer.rb`

For inline docs search, copy:

- `scripts/build_search.rb`
- `studio/docs-viewer/build/build_search.rb`
- `scripts/search/adapter_registry.json`

`scripts/build_search.rb` is a compatibility dispatcher.
Configured docs scopes route to `studio/docs-viewer/build/build_search.rb`, while the Catalogue adapter remains separate in this repo.
Adding a new docs scope should only require adding that scope to `studio/docs-viewer/config/scopes/docs_scopes.json`, rebuilding docs data, and then running the same search command for the new scope.

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

### Management Server

For local manage mode, copy the docs-management server support:

- `studio/docs-viewer/services/docs_management_server.py`
- `studio/docs-viewer/services/docs_management_routes.py`
- `studio/docs-viewer/services/docs_scope_config.py`
- `studio/docs-viewer/services/docs_source_model.py`
- `studio/docs-viewer/services/docs_management_mutations.py`
- `studio/docs-viewer/services/docs_write_rebuild.py`
- `studio/docs-viewer/services/docs_generated_reads.py`
- `studio/docs-viewer/services/docs_import_source_service.py`
- `studio/docs-viewer/services/docs_html_import.py`
- `studio/docs-viewer/services/docs_activity.py`
- `studio/docs-viewer/services/docs_watch_suppression.py`

Optional adjacent docs tools:

- `studio/docs-viewer/services/docs_live_rebuild_watcher.py`
- `studio/docs-viewer/services/docs_broken_links.py`
- `studio/docs-viewer/services/docs_export.py`
- `studio/docs-viewer/services/docs_import.py`

The management server is local-only and should bind to loopback.
It is not part of the public static site.
Generated-data reads, source writes, import targets, and rebuild commands use `studio/docs-viewer/config/scopes/docs_scopes.json` as the docs scope contract.
The local management package also includes the read-only source config report and the Settings modal.
The report inspects configured source, browser, and generated projections.
The Settings modal writes only allowlisted source config fields; the first portable field is scoped `show_updated_date`, which saves to `studio/docs-viewer/config/scopes/docs_scopes.json` and triggers a same-scope docs rebuild.
For the full config split and media-storage choices, see [Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer).
