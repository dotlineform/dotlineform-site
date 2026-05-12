---
doc_id: docs-viewer-portable-setup
title: Docs Viewer Portable Setup
added_date: 2026-05-11
last_updated: "2026-05-12 10:25"
parent_id: docs-viewer
sort_order: 15
---
# Docs Viewer Portable Setup

This document answers two practical questions from the current implementation state:

- what must be copied into an existing Jekyll project to use the Docs Viewer
- how to set up a new Library-style docs scope with one local management view and one read-only public view

It intentionally describes the current repo as it is now.
The extraction plan for making these steps shorter and more self-contained lives in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).

## Current Shape

The Docs Viewer is not a standalone plugin yet.
It is a shared Jekyll include, browser runtime, generated JSON format, build script, and optional localhost management server.

Current live scopes:

- `studio`: source docs in `_docs/`, managed at `/docs/?scope=studio&mode=manage`, read at `/docs/?scope=studio`
- `library`: source docs in `_docs_library/`, managed at `/docs/?scope=library&mode=manage`, read at `/library/`
- `analysis`: source docs in `_docs_analysis/`, managed at `/docs/?scope=analysis&mode=manage`, read at `/analysis/`

The public `/library/` and `/analysis/` routes are read-only.
They should not expose `?mode=manage`, management CSS, management JS, localhost write endpoints, or Docs Import.

The `/docs/` route is the local management shell.
It can switch the active scope with the `scope` query parameter.

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

- `_includes/docs_import_shell.html`

The route adapter includes wrap `docs_viewer_shell.html` with the right public or management flags.
Examples in this repo are:

- `docs/index.md`
- `library/index.md`
- `analysis/index.md`

Use `docs_viewer_readonly_route.html` for public corpus routes such as `/library/` and `/analysis/`.
Use `docs_viewer_management_route.html` for the local `/docs/` management shell.
That adapter renders management markup only when `docs_viewer_management_enabled: true`; the public config leaves the flag false, while `_config.dev-studio.yml` enables it for `bin/dev-studio`.

### Browser Runtime

Copy the shared viewer runtime files:

- `assets/docs-viewer/js/docs-viewer.js`
- `assets/docs-viewer/js/docs-viewer-data.js`
- `assets/docs-viewer/js/docs-viewer-tree.js`
- `assets/docs-viewer/js/docs-viewer-search.js`
- `assets/docs-viewer/js/docs-viewer-favourites.js`

For management mode, also copy:

- `assets/docs-viewer/js/docs-viewer-management.js`
- `assets/docs-viewer/js/docs-viewer-management-client.js`
- `assets/docs-viewer/js/docs-viewer-drag-drop.js`

For Docs Import inside the management modal, also copy:

- `assets/docs-viewer/js/docs-html-import.js`

### CSS

Copy:

- `assets/docs-viewer/css/docs-viewer-management.css`
- `assets/docs-viewer/css/docs-viewer.css`

The host site should still load its own base stylesheet for tokens, prose rules, responsive media defaults, and the `.content` contract used by generated docs HTML.
The viewer include now loads Docs Viewer-owned CSS for the shell, controls, index, search, results, bookmarks, status pills, management surfaces, and the transitional Docs Import form/control primitives.
Management mode no longer loads `assets/studio/css/studio.css`.

### Config And UI Text

Copy:

- `assets/docs-viewer/data/docs-viewer-config.json`
- `assets/docs-viewer/data/ui-text.json`

`assets/docs-viewer/data/docs-viewer-config.json` is generated from `scripts/docs/docs_scopes.json`.
It is required by the browser runtime and now includes the browser-safe Docs Viewer settings such as recently-added limits, hidden-doc styling, hidden-doc emoji, and per-scope UI-status options.
Each configured scope also carries its Docs Viewer search policy and search index URL in this browser config.
The viewer does not keep a hardcoded fallback scope list.
Docs Import copy is nested in `assets/docs-viewer/data/ui-text.json` under `docs_html_import`.

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
- `scripts/docs/build_docs.rb`
- `scripts/docs/docs_scopes.json`
- `scripts/jekyll_markdown_renderer.rb`

For inline docs search, copy:

- `scripts/build_search.rb`
- `scripts/docs/build_search.rb`
- `scripts/search/adapter_registry.json`

`scripts/build_search.rb` is a compatibility dispatcher.
Configured docs scopes route to `scripts/docs/build_search.rb`, while the Catalogue adapter remains separate in this repo.
Adding a new docs scope should only require adding that scope to `scripts/docs/docs_scopes.json`, rebuilding docs data, and then running the same search command for the new scope.

The target direction is tracked in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).

### Management Server

For local manage mode, copy the docs-management server support:

- `scripts/docs/docs_management_server.py`
- `scripts/docs/docs_management_routes.py`
- `scripts/docs/docs_scope_config.py`
- `scripts/docs/docs_source_model.py`
- `scripts/docs/docs_management_mutations.py`
- `scripts/docs/docs_write_rebuild.py`
- `scripts/docs/docs_generated_reads.py`
- `scripts/docs/docs_import_source_service.py`
- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_activity.py`
- `scripts/docs/docs_watch_suppression.py`

Optional adjacent docs tools:

- `scripts/docs/docs_live_rebuild_watcher.py`
- `scripts/docs/docs_broken_links.py`
- `scripts/docs/docs_export.py`
- `scripts/docs/docs_import.py`

The management server is local-only and should bind to loopback.
It is not part of the public static site.
Generated-data reads, source writes, import targets, and rebuild commands use `scripts/docs/docs_scopes.json` as the docs scope contract.

## Source Docs Required Shape

Each scope has a source root, currently configured in `scripts/docs/docs_scopes.json`.

Current roots:

- `_docs/` for `studio`
- `_docs_library/` for `library`
- `_docs_analysis/` for `analysis`

Each source doc is Markdown with optional YAML front matter.
Important fields:

- `doc_id`: stable viewer id; defaults to the file stem when omitted
- `title`: display title; falls back to the first H1 or humanized filename
- `parent_id`: parent document id; blank means top-level
- `sort_order`: numeric sibling ordering
- `summary`: optional short summary
- `ui_status`: optional viewer status pill
- `published`: `false` removes the doc from generated viewer data
- `hidden`: `true` keeps the doc generated but hidden from read-only public views
- `last_updated`: display/search metadata
- `added_date`: recently-added metadata

A minimal root doc for a new Library-style scope looks like:

```md
---
doc_id: library
title: Library
added_date: 2026-05-11
last_updated: "2026-05-11"
parent_id: ""
sort_order: 10
hidden: false
---
# Library

Start writing here.
```

## Setup Procedure For A New Library-Style Scope

Use this when adding a scope that behaves like the current `library` scope:
a public read-only route plus local management through `/docs/`.

### 1. Choose Scope Values

Decide:

- scope id: for example `research`
- source root: for example `_docs_research`
- media path prefix: for example `docs/research`
- generated docs output: `assets/data/docs/scopes/research`
- generated search output: `assets/data/search/research/index.json`
- read-only route: for example `/research/`
- root doc id: for example `research`

Use lowercase scope ids.
The current JavaScript assumes simple scope strings.

### 2. Add The Source Root

Create the source directory and at least one root doc:

- `_docs_research/research.md`

The root doc's `doc_id` should match the scope config's `default_doc_id`.

### 3. Register The Scope For Docs Builds

Add a scope entry to `scripts/docs/docs_scopes.json`:

```json
{
  "scope_id": "research",
  "source": "_docs_research",
  "media_path_prefix": "docs/research",
  "output": "assets/data/docs/scopes/research",
  "viewer_base_url": "/research/",
  "include_scope_param": false,
  "default_doc_id": "research",
  "allow_nested_source": false,
  "non_loadable_doc_ids": [],
  "manage_only_tree_root_ids": [],
  "show_updated_date": false,
  "allow_unresolved_parent_ids": true
}
```

Use `include_scope_param: false` for a public route that only ever reads one scope.
Use `include_scope_param: true` only when the configured route should publish links with an explicit scope query.

Running `./scripts/build_docs.rb --write` updates `assets/docs-viewer/data/docs-viewer-config.json` from this source config.

### 4. Add The Read-Only Route

Create a Jekyll page such as `research/index.md`:

```liquid
---
layout: default
title: "Research"
section: research
permalink: /research/
---

{% include docs_viewer_readonly_route.html
  search_placeholder='search research'
  search_aria_label='Search research'
%}
```

The route path is matched to `viewer_base_url` in the generated Docs Viewer browser config.
Do not pass `allow_management`, `allow_scope_query`, or `management_base_url` on public read-only routes.
The read-only adapter intentionally fixes those values to false.

Read-only route adapter inputs:

- `viewer_base_url`: optional override; defaults to the page permalink or URL
- `viewer_scope`: optional fixed scope hint; normally omitted so the route is matched from `viewer_base_url`
- `default_doc_id`: optional route-local fallback; normally omitted so scope config owns the default
- `enable_search`: optional `false` to hide search controls
- `search_placeholder`: optional search input placeholder
- `search_aria_label`: optional search input label

Read-only canonical URL behavior:

- `doc` selects the active document; missing or invalid values normalize to the scope's default doc
- `q` activates inline docs search and is preserved while search is active
- `scope` is ignored on read-only routes and normalized away
- `mode` is ignored on read-only routes and normalized away
- generated links use the route's `viewer_base_url`

### 5. Add The Scope To The Management Shell

The current management shell is `docs/index.md`.
In local Studio runs, it renders `/docs/` through `docs_viewer_management_route.html` with:

- `allow_management=true`
- `allow_scope_query=true`
- `management_base_url='http://127.0.0.1:8789'`

Public builds keep `docs_viewer_management_enabled: false`, so the same route adapter emits the read-only shell and ignores `mode=manage` without loading management CSS or localhost server configuration.

The management scope selector and browser route map come from `assets/docs-viewer/data/docs-viewer-config.json`.
Adding a configured scope no longer requires editing `_includes/docs_viewer_shell.html` or `assets/docs-viewer/js/docs-viewer.js`.
If the new scope needs UI-status pills, add the status options to the `docs_viewer.ui_statuses_by_scope` section in `scripts/docs/docs_scopes.json`, then rerun the docs build so `assets/docs-viewer/data/docs-viewer-config.json` is regenerated.

Management route adapter inputs:

- `viewer_base_url`: optional override; defaults to the page permalink or URL
- `viewer_scope`: optional fixed initial scope hint
- `default_doc_id`: optional route-local fallback
- `management_base_url`: optional localhost server base URL; defaults to `http://127.0.0.1:8789`
- `enable_search`: optional `false` to hide search controls
- `search_placeholder`: optional search input placeholder
- `search_aria_label`: optional search input label

Management canonical URL behavior:

- `scope` selects the active configured docs scope
- `mode=manage` enables local management features when the localhost server is available
- missing `scope` normalizes to the configured default scope
- `doc` selects the active document in the selected scope
- `q` activates inline docs search for the selected scope
- `/docs/` is the only management-capable shell in this install pattern

### 6. Add Search Support

If the read-only route should have inline search, make sure the scope exists in `scripts/docs/docs_scopes.json`.
The Docs Viewer search builder derives its input and output paths from that scope config:

- input docs index: `assets/data/docs/scopes/<scope>/index.json`
- search output: `assets/data/search/<scope>/index.json`

Then build search with:

```sh
./scripts/build_search.rb --scope research --write
```

### 7. Build Docs Data

Build the viewer JSON:

```sh
./scripts/build_docs.rb --scope research --write
```

Build the search JSON if search is enabled:

```sh
./scripts/build_search.rb --scope research --write
```

After this, the public route should be able to fetch:

- `/assets/data/docs/scopes/research/index.json`
- `/assets/data/docs/scopes/research/by-id/research.json`
- `/assets/data/search/research/index.json`

### 8. Start Local Management

Run the docs-management server locally.
In this repo the normal path is through the Studio dev runner; standalone usage is the same server script:

```sh
./scripts/docs/docs_management_server.py --port 8789
```

This standalone server start is the portable local-management entrypoint.
It requires a project root with `_config.yml`, configured docs scopes in `scripts/docs/docs_scopes.json`, the Docs Viewer build/search scripts, and the Python/Ruby dependencies used by those scripts.

Then open:

```text
/docs/?scope=research&mode=manage&doc=research
```

Docs Import reads the configured scope list and source roots from `scripts/docs/docs_scopes.json`.
Imported media token paths use each scope's `media_path_prefix`, so a new arbitrary scope does not require patching the importer for basic create/overwrite imports.

### 9. Verify The Public Route

Open:

```text
/research/?doc=research
```

Confirm:

- the tree loads
- the root doc loads
- search loads if configured
- `?mode=manage` is ignored or normalized away on the public route
- no management controls are rendered
- no management-only CSS or import JavaScript is fetched

## Related Planning

Use this page as the current install guide.
Use [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) for the ordered work to reduce hardcoded scope lists, move docs search under Docs Viewer ownership, extract CSS/config, and package the local management/import surface.
