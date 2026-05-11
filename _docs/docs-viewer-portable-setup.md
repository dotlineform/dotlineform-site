---
doc_id: docs-viewer-portable-setup
title: Docs Viewer Portable Setup
added_date: 2026-05-11
last_updated: "2026-05-11"
parent_id: docs-viewer
sort_order: 15
---
# Docs Viewer Portable Setup

This document answers two practical questions from the current implementation state:

- what must be copied into an existing Jekyll project to use the Docs Viewer
- how to set up a new Library-style docs scope with one local management view and one read-only public view

It intentionally describes the current repo as it is now.
The final section lists the parts that still need extraction before the Docs Viewer is a clean self-contained package.

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

### Viewer Shell

Copy:

- `_includes/docs_viewer_shell.html`

If management mode should include Docs Import, also copy:

- `_includes/docs_import_shell.html`

The include expects a page shell to pass URLs and scope settings.
Examples in this repo are:

- `docs/index.md`
- `library/index.md`
- `analysis/index.md`

### Browser Runtime

Copy the shared viewer runtime files:

- `assets/js/docs-viewer.js`
- `assets/js/docs-viewer-data.js`
- `assets/js/docs-viewer-tree.js`
- `assets/js/docs-viewer-search.js`
- `assets/js/docs-viewer-favourites.js`

For management mode, also copy:

- `assets/js/docs-viewer-management-client.js`
- `assets/js/docs-viewer-drag-drop.js`

For Docs Import inside the management modal, also copy:

- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/studio-activity-context.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/studio-modal.js`
- `assets/studio/js/studio-route-state.js`
- `assets/studio/js/studio-transport.js`

### CSS

Copy:

- `assets/css/docs-viewer-management.css`

Also copy or extract the Docs Viewer rules from:

- `assets/css/main.css`

Current issue:
the read-only Docs Viewer CSS is still mixed into the site-wide stylesheet.
For a clean portable install, those `.docsViewer*` rules and small utility dependencies should become their own `docs-viewer.css`.

Management mode currently also loads:

- `assets/studio/css/studio.css`

That is mainly for Docs Import and shared Studio modal/control primitives.
This is another packaging leak: management mode is not yet styled only by Docs Viewer-owned CSS.

### Config And UI Text

Copy:

- `assets/studio/data/studio_config.json`
- `assets/studio/data/ui_text/docs-viewer.json`
- `assets/studio/data/ui_text/docs-html-import.json`

Current issue:
the viewer reads `studio_config.json` for Docs Viewer settings and UI-status options, even on public docs routes.
A portable package should move those settings into Docs Viewer-owned config files or route include parameters.

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
- `scripts/search/build_search.rb`
- `scripts/search/build_config.json`

Current issue:
the search builder still hardcodes `studio`, `library`, and `analysis` in `scripts/search/build_search.rb`.
Adding a new arbitrary scope currently requires editing that script and `scripts/search/build_config.json`.

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
- generated docs output: `assets/data/docs/scopes/research`
- generated search output: `assets/data/search/research/index.json`
- read-only route: for example `/research/`
- root doc id: for example `research`

Use lowercase scope ids.
The current JavaScript assumes simple scope strings.

### 2. Add The Source Root

Create the source directory and at least one root doc:

- `_docs_research/research.md`

The root doc's `doc_id` should match the route shell's `default_doc_id`.

### 3. Register The Scope For Docs Builds

Add a scope entry to `scripts/docs/docs_scopes.json`:

```json
{
  "scope_id": "research",
  "source": "_docs_research",
  "output": "assets/data/docs/scopes/research",
  "viewer_base_url": "/research/",
  "include_scope_param": false,
  "allow_nested_source": false,
  "non_loadable_doc_ids": [],
  "manage_only_tree_root_ids": [],
  "show_updated_date": false,
  "allow_unresolved_parent_ids": true
}
```

Use `include_scope_param: false` for a public route that only ever reads one scope.
Use `include_scope_param: true` only for a multi-scope route such as `/docs/`.

### 4. Add The Read-Only Route

Create a Jekyll page such as `research/index.md`:

```liquid
---
layout: default
title: "Research"
section: research
permalink: /research/
---

{%- assign docs_index_url = '/assets/data/docs/scopes/research/index.json' | relative_url -%}
{%- assign docs_viewer_base_url = '/research/' | relative_url -%}
{%- assign docs_search_index_url = '/assets/data/search/research/index.json' | relative_url -%}

{% include docs_viewer_shell.html
  index_url=docs_index_url
  viewer_base_url=docs_viewer_base_url
  viewer_scope='research'
  include_scope_param=false
  default_doc_id='research'
  search_index_url=docs_search_index_url
  search_placeholder='search research'
  search_aria_label='Search research'
%}
```

Do not pass `allow_management`, `allow_scope_query`, or `management_base_url` on public read-only routes.

### 5. Add The Scope To The Management Shell

The current management shell is `docs/index.md`.
It already renders `/docs/` with:

- `allow_management=true`
- `allow_scope_query=true`
- `include_scope_param=true`
- `management_base_url='http://127.0.0.1:8789'`

Current hardcoded work required for a new scope:

- add an option to `_includes/docs_viewer_shell.html` scope select
- add a route entry to `DOCS_ROUTE_SCOPES` in `assets/js/docs-viewer.js`
- make sure `assets/studio/data/studio_config.json` has any status options needed for the new scope

The intended future shape is that the scope select and route map come from `scripts/docs/docs_scopes.json` or a generated browser config.

### 6. Add Search Support

If the read-only route should have inline search, update:

- `scripts/search/build_search.rb`
- `scripts/search/build_config.json`

Current hardcoded work required:

- add a scope entry with schema, output path, and source docs-index path
- add the scope to the docs-index source family in `scripts/search/build_config.json`

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

Then open:

```text
/docs/?scope=research&mode=manage&doc=research
```

Current hardcoded limitation:
Docs Import currently normalizes import scopes to `studio`, `library`, or `analysis`.
A new arbitrary scope needs `scripts/docs/docs_import_source_service.py` updated before import works for that scope.

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

## Current Self-Containment Gaps

These are the main areas to address before Docs Viewer is easy to move between Jekyll repos.

- Read-only viewer CSS is mixed into `assets/css/main.css` instead of a dedicated Docs Viewer stylesheet.
- Management mode depends on `assets/studio/css/studio.css` for importer and modal/control styling.
- Viewer config and UI copy live under `assets/studio/data/`, even for public read-only viewer routes.
- `_includes/docs_viewer_shell.html` hardcodes the management scope select options.
- `assets/js/docs-viewer.js` hardcodes known `/docs/` scope route data in `DOCS_ROUTE_SCOPES`.
- `scripts/search/build_search.rb` hardcodes docs-search scopes.
- `scripts/search/build_config.json` hardcodes docs-index source scopes.
- Docs Import accepts only the current `studio`, `library`, and `analysis` scopes.
- The management server and import flow are still a set of repo scripts rather than a small documented command package.
- Setup requires copying several Studio helper modules even when the desired feature is only Docs Viewer management.

These gaps are useful extraction targets.
The immediate architectural direction should be to make Docs Viewer own its CSS, browser config, UI text, scope list, import shell, and local management command surface.
