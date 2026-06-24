---
doc_id: docs-viewer-portable-scope-setup
title: Portable Scope Setup
added_date: 2026-05-19
last_updated: 2026-06-24
parent_id: docs-viewer-portable-setup
viewable: true
---
# Docs Viewer Portable Scope Setup

## Setup Procedure For A New Library-Style Scope

Use this when adding a scope that behaves like the current `library` scope:
a public read-only route plus local management through `/docs/`.

For a local tracked scope, do not use the public `site/assets/data/` generated roots.
Use the local tracked procedure below instead.

### 1. Choose Scope Values

Decide:

- scope id: for example `research`
- source root: for example `docs-viewer/source/research`
- media path prefix: for example `docs/research`
- import media storage: usually `repo_assets` for a new portable install without remote media
- working generated docs output: `docs-viewer/generated/docs/research`
- working generated search output: `docs-viewer/generated/search/research/index.json`
- published docs output: `site/assets/data/docs/scopes/research`
- published search output: `site/assets/data/search/research/index.json`
- read-only route: for example `/research/`
- root doc id: for example `research`

Use lowercase scope ids.
The current JavaScript assumes simple scope strings.

### 2. Add The Source Root

Create the source directory and at least one root doc:

- `docs-viewer/source/research/research.md`

The root doc's `doc_id` should match the scope config's `default_doc_id`.

### 3. Register The Scope For Docs Builds

Add a scope entry to `docs-viewer/config/scopes/docs_scopes.json`:

```json
{
  "scope_id": "research",
  "scope_type": "public",
  "source": "docs-viewer/source/research",
  "media_path_prefix": "docs/research",
  "output": "docs-viewer/generated/docs/research",
  "search_output": "docs-viewer/generated/search/research/index.json",
  "publish_output": "site/assets/data/docs/scopes/research",
  "publish_search_output": "site/assets/data/search/research/index.json",
  "viewer_base_url": "/research/",
  "include_scope_param": false,
  "default_doc_id": "research",
  "non_loadable_doc_ids": [],
  "manage_only_tree_root_ids": [],
  "show_updated_date": false,
  "allow_unresolved_parent_ids": true,
  "import_media_storage": {
    "storage_mode": "repo_assets",
    "repo_assets_path_prefix": "site/assets/docs/research",
    "repo_assets_public_path_prefix": "/assets/docs/research"
  }
}
```

Use `include_scope_param: false` for a public route that only ever reads one scope.
Use `include_scope_param: true` only when the configured route should publish links with an explicit scope query.
Public read-only scopes use `docs-viewer/generated/` as their working output roots and separate `site/assets/data/` publish roots.
Local scopes use only `docs-viewer/generated/` roots, and the builders reject local scope configs that point generated docs/search output at public `site/assets/data/` roots.

Running `./docs-viewer/build/build_docs.py --write` updates `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json` from this source config.
The public config is filtered to static read-only routes, so a new `public_readonly` scope becomes available to public route config after the docs build refreshes the config and generated docs payloads.
`repo_assets` makes Docs Import copy imported images and files below `site/assets/docs/research/` and write literal `/assets/docs/research/...` links.
Use `staging_manual` instead when imported media should stay in `var/docs/import-staging/` until you manually copy it to the configured `media_path_prefix`.

### New Scope Action

The Docs Viewer New Scope action is the preferred way to create a repo-local public read-only scope.
For `publishing_mode: "public_readonly"`, it creates source/config records, working generated output, public payload snapshots, route registry records, and the tracked public route shell.
It renders the shell from `docs-viewer/templates/public-route/index.html`.

See [Public Route Shell Template](/docs/?scope=studio&doc=docs-viewer-public-route-shell-template).

### External Local Scope Action

Use the New Scope action's `external local` mode when a scope should be registered in the repo but keep its source Markdown and working generated JSON outside the repo.

External local setup requires:

- `DOTLINEFORM_PROJECTS_BASE_DIR` set in `var/local/site.env` or the process environment
- an existing readable and writable `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/` directory
- the standalone Docs Viewer service for management and generated-data reads

The modal does not ask for an external path.
For every external local scope, Docs Viewer derives:

- source root: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`
- generated docs root: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/docs/<scope>/`
- generated search output: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/search/<scope>/index.json`

Create preview and apply fail before writing if `DOTLINEFORM_PROJECTS_BASE_DIR` is unset or if `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/` does not exist.
The lifecycle action creates the scope-specific child paths under that fixed root.

The central config record remains in `docs-viewer/config/scopes/docs_scopes.json`.
For external local scopes it stores `external_data_root: "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"` plus marker-rooted source, docs output, and search output paths.
It does not store user-specific absolute paths in the repo.

External local scopes do not configure public `publish_output`, public `publish_search_output`, or a public route.
The browser reads their generated JSON through Docs Viewer service endpoints such as `/docs/generated/index-tree?scope=<scope>` and `/docs/generated/payload?scope=<scope>&doc_id=<doc>`, not through static filesystem URLs.

### 4. Add The Public Static Route

When using New Scope, this step is performed by the lifecycle action.
Current public Docs Viewer route shells are checked-in static HTML under `site/`.
New Scope renders the route shell into `site/<route>/index.html`; there is no deploy-time static-site builder or Markdown route file.

The route must also be represented in browser-safe route config:

- `docs-viewer/config/routes/docs-viewer-routes.json`
- `site/docs-viewer/config/routes/docs-viewer-public-routes.json`

The static route shell sets:

- `data-route-id="<scope>"`
- `data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"`

The route config record sets:

- `route_id`: the public route id, normally the scope id
- `route_path`: the public route path, such as `/research/`
- `default_scope_id`: the fixed scope id
- `default_doc_id`: the scope's default doc id
- `include_scope_param`: `false`
- `allow_scope_query`: `false`
- `viewer_base_url`: the public route base
- `docs_paths`: published `index-tree.json`, `recently-added.json`, and search index URLs
- `config_urls.docs_viewer`: `/docs-viewer/config/defaults/docs-viewer-public-config.json`
- `config_urls.ui_text`: `/docs-viewer/config/ui-text/public.json`

Site validation config also needs to include required public docs/search assets and route files in `site-tools/config/site-tools.json` when they are deploy-critical.

Read-only canonical URL behavior:

- `doc` selects the active document; missing or invalid values normalize to the scope's default doc
- `q` activates inline docs search and is preserved while search is active
- `scope` is ignored on read-only routes and normalized away
- `mode` is ignored on read-only routes and normalized away
- generated links use the route's `viewer_base_url`

### 5. Add The Scope To The Management Shell

The current management shell is served by `docs-viewer/services/docs_viewer_service.py` at the configured Docs Viewer service base URL.
It renders `/docs/` with:

- `data-route-id="docs-manage"`
- `data-route-config-url="/docs-viewer/config/routes/docs-viewer-routes.json"`

Public builds keep `docs_viewer_management_enabled: false`, so the same route adapter emits the read-only shell and ignores management query state without loading management CSS or localhost server configuration.
Local Studio points Docs links, generated reads, and management actions at the configured Docs Viewer service rather than hosting the shell itself.

The standalone Docs Viewer service injects `DOCS_VIEWER_BASE_URL` into the served route-config registry for local management and generated-read URLs.
The checked-in static route-config asset keeps those URLs blank so public builds do not expose localhost state.
The management scope selector and browser route map come from `docs-viewer/config/defaults/docs-viewer-config.json`.
Adding a configured scope does not require editing Docs Viewer shell markup or the Docs Viewer runtime entrypoints.
If the new scope needs metadata status options, add them to the `docs_viewer.ui_statuses_by_scope` section in `docs-viewer/config/scopes/docs_scopes.json`, then rerun the docs build so the generated Docs Viewer browser configs are regenerated.
The scope delete lifecycle action removes the matching `ui_statuses_by_scope` entry from `docs-viewer/config/scopes/docs_scopes.json` along with the scope record.
If the new scope uses a new availability type, add or update its `docs_viewer.scope_type_badges` entry so the management scope dropdown can prefix the scope name consistently.
Set the scope record `meta` to the short descriptor that should appear beside the scope id in the custom scope dropdown.

Management route adapter inputs:

- `route_id`: defaults to `docs-manage` through the management adapter
- `route_config_url`: optional override for the browser-safe route-config registry
- `enable_search`: optional `false` to hide search controls
- `search_placeholder`: optional search input placeholder
- `search_aria_label`: optional search input label

Management canonical URL behavior:

- `scope` selects the active configured docs scope
- `/docs/` enables local management features when the localhost server is available
- missing `scope` normalizes to the configured default scope
- `doc` selects the active document in the selected scope
- `q` activates inline docs search for the selected scope
- `/docs/` is the only management-capable shell in this install pattern

### 6. Add Search Support

If the read-only route should have inline search, make sure the scope exists in `docs-viewer/config/scopes/docs_scopes.json`.
The Docs Viewer search builder derives its input and output paths from that scope config:

- input docs tree: `docs-viewer/generated/docs/<scope>/index-tree.json`
- working search output: `docs-viewer/generated/search/<scope>/index.json`
- published search output: `site/assets/data/search/<scope>/index.json`

Then build search with:

```sh
./docs-viewer/build/build_search.py --scope research --write
```

### 7. Build Working Docs Data And Publish To Site Assets

Build the working viewer JSON:

```sh
./docs-viewer/build/build_docs.py --scope research --write
```

Build the working search JSON if search is enabled:

```sh
./docs-viewer/build/build_search.py --scope research --write
```

Use the `/docs/` Actions menu `Publish` command while viewing this public scope to copy the reviewed working outputs to the public route asset roots under `site/assets/data/`.
After that local copy step, the public route should be able to fetch:

- `/assets/data/docs/scopes/research/index-tree.json`
- `/assets/data/docs/scopes/research/recently-added.json`
- `/assets/data/docs/scopes/research/by-id/research.json`
- `/assets/data/search/research/index.json`

### 8. Start Local Management

Run the Docs Viewer service for management.
Docs management is served through `DOCS_VIEWER_BASE_URL`; Local Studio only links to that peer service.
The project needs configured docs scopes in `docs-viewer/config/scopes/docs_scopes.json`, the Docs Viewer build/search scripts, `site-tools/config/site-tools.json`, and the Python dependencies used by those scripts.
Public-site preview/validation parity uses `bin/site-validate` and `bin/site-preview`.

Then open:

```text
/docs/?scope=research&doc=research
```

Docs Import reads the configured scope list and source roots from `docs-viewer/config/scopes/docs_scopes.json`.
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
- management queries are ignored or normalized away on the public route
- no management controls are rendered
- no management-only CSS or import JavaScript is fetched

## Setup Procedure For A Committed Manage-Mode Scope

Use this when adding a scope that should travel with the repo for local management, but should not publish a public read-only route.
The current `studio` scope is the model for this storage contract.

Choose:

- scope id: for example `notes`
- source root: `docs-viewer/source/notes`
- generated docs output: `docs-viewer/generated/docs/notes`
- generated search output: `docs-viewer/generated/search/notes/index.json`
- management route: `/docs/?scope=notes`
- root doc id: for example `notes`

Scope config example:

```json
{
  "scope_id": "notes",
  "source": "docs-viewer/source/notes",
  "media_path_prefix": "docs/notes",
  "output": "docs-viewer/generated/docs/notes",
  "search_output": "docs-viewer/generated/search/notes/index.json",
  "viewer_base_url": "/docs/",
  "include_scope_param": true,
  "default_doc_id": "notes",
  "non_loadable_doc_ids": [],
  "manage_only_tree_root_ids": [],
  "show_updated_date": true,
  "allow_unresolved_parent_ids": false,
  "import_media_storage": {
    "storage_mode": "staging_manual",
    "repo_assets_path_prefix": "site/assets/docs/notes",
    "repo_assets_public_path_prefix": "/assets/docs/notes"
  }
}
```

Do not create a public static route shell, public route-config record, or published public payload root for a local-only scope.
The scope is loaded through the local Docs Viewer management shell, not through a public static route.

Build the generated docs and search payloads:

```sh
./docs-viewer/build/build_docs.py --scope notes --write
./docs-viewer/build/build_search.py --scope notes --write
```

After this, the local Docs Viewer service should be able to fetch:

- `/docs-viewer/generated/docs/notes/index-tree.json`
- `/docs-viewer/generated/docs/notes/recently-added.json`
- `/docs-viewer/generated/docs/notes/by-id/notes.json`
- `/docs-viewer/generated/search/notes/index.json`

Keep the generated JSON under `docs-viewer/generated/` tracked when the scope is committed.
Do not place local tracked generated runtime payloads under `site/assets/data/docs/scopes/` or `site/assets/data/search/`; those are public static payload roots.

Open:

```text
/docs/?scope=notes&doc=notes
```
