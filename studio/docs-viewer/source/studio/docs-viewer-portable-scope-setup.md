---
doc_id: docs-viewer-portable-scope-setup
title: Docs Viewer Portable Scope Setup
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: docs-viewer-portable-setup
sort_order: 3300
---
# Docs Viewer Portable Scope Setup

## Setup Procedure For A New Library-Style Scope

Use this when adding a scope that behaves like the current `library` scope:
a public read-only route plus local management through `/docs/`.

### 1. Choose Scope Values

Decide:

- scope id: for example `research`
- source root: for example `_docs_research`
- media path prefix: for example `docs/research`
- import media storage: usually `repo_assets` for a new portable install without remote media
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
  "allow_unresolved_parent_ids": true,
  "import_media_storage": {
    "storage_mode": "repo_assets",
    "repo_assets_path_prefix": "assets/docs/research",
    "repo_assets_public_path_prefix": "/assets/docs/research"
  }
}
```

Use `include_scope_param: false` for a public route that only ever reads one scope.
Use `include_scope_param: true` only when the configured route should publish links with an explicit scope query.

Running `./scripts/build_docs.rb --write` updates `assets/docs-viewer/data/docs-viewer-config.json` from this source config.
`repo_assets` makes Docs Import copy imported images and files below `assets/docs/research/` and write literal `/assets/docs/research/...` links.
Use `staging_manual` instead when imported media should stay in `var/docs/import-staging/` until you manually copy it to the configured `media_path_prefix`.

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
- `management_base_url='/studio/api/docs'` in the local Studio app shell

Public builds keep `docs_viewer_management_enabled: false`, so the same route adapter emits the read-only shell and ignores `mode=manage` without loading management CSS or localhost server configuration.
The dev Studio Jekyll overlay points generated reads and management actions at the local Studio app default, `http://127.0.0.1:8765/studio/api/docs`, rather than the standalone Docs management process.

The management scope selector and browser route map come from `assets/docs-viewer/data/docs-viewer-config.json`.
Adding a configured scope no longer requires editing `_includes/docs_viewer_shell.html` or `assets/docs-viewer/js/docs-viewer.js`.
If the new scope needs UI-status menu options, add them to the `docs_viewer.ui_statuses_by_scope` section in `scripts/docs/docs_scopes.json`, then rerun the docs build so `assets/docs-viewer/data/docs-viewer-config.json` is regenerated.

Management route adapter inputs:

- `viewer_base_url`: optional override; defaults to the page permalink or URL
- `viewer_scope`: optional fixed initial scope hint
- `default_doc_id`: optional route-local fallback
- `management_base_url`: optional local management API base URL; defaults to the site `docs_viewer_management_base_url` setting when configured, otherwise blank
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

Run the local Studio app for management.
Docs management is served through `/studio/api/docs/...`; there is no standalone Docs Management server entrypoint.
The project still needs `_config.yml`, configured docs scopes in `scripts/docs/docs_scopes.json`, the Docs Viewer build/search scripts, and the Python/Ruby dependencies used by those scripts.

Then open:

```text
/docs/?scope=research&mode=manage&doc=research
```

Docs Import reads the configured scope list and source roots from `scripts/docs/docs_scopes.json`.
Imported media behavior follows each scope's `import_media_storage` settings.
New portable installs should usually start with `repo_assets`; existing remote-token workflows can keep `staging_manual` and `media_path_prefix`.

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
