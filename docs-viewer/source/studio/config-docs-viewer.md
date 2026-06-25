---
doc_id: config-docs-viewer
title: Config
added_date: 2026-05-12
last_updated: 2026-06-12
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Config

Docs Viewer configuration is split by audience.

## Host settings

Local Docs Viewer service host, port, base URL, and capability flags are host runtime settings in `var/local/site.env`, not checked-in Docs Viewer defaults.

## Public Site Config

[needs updating]

## Source Scope Config

`docs-viewer/config/scopes/docs_scopes.json` is the source-side Docs Viewer config.
It is checked in and is read by docs builds, docs search builds, Docs Import, the standalone Docs Viewer service, live rebuild watching, generated-data reads, and source-write validation.

In local manage mode, [Docs Viewer Source Config Report](/docs/?scope=studio&doc=docs-viewer-source-config-report) reads this source config through the Docs Viewer service and shows it alongside browser and generated projections.
The report is read-only; source edits still go through source JSON edits or explicit manage-mode write controls.

- The Docs Viewer service still exposes a source-config settings contract for guarded source config writes.
- The current `/docs/` manage-mode Settings modal has no active editable fields; future scope-level toolbar/display controls should use an explicit settings contract rather than ad hoc route-local state.
- The settings contract does not create a new settings layer; it describes guarded edits to the existing source config.

Each scope entry owns:

- `scope_id`: stable scope key, such as `studio`, `library`, or `analysis`
- `scope_type`: display and ownership type, such as `public` or `local`
- `source`: Markdown source root for that scope
- `media_path_prefix`: token path prefix used by <code>&#91;&#91;media:...&#93;&#93;</code> links
- `output`: generated docs JSON output root
- `viewer_base_url`: public route base for the scope
- `include_scope_param`: whether route links should include `?scope=<scope>`
- `default_doc_id`: default document for the scope
- `non_loadable_doc_ids`: tree nodes that should not load as documents
- `manage_only_tree_root_ids`: tree roots excluded from public routes
- `show_updated_date`: legacy generated viewer option retained in scope config; selected-document date display now belongs to the info panel metadata view
- `allow_unresolved_parent_ids`: whether unknown parent ids are tolerated
- `import_media_storage`: Docs Import media save behavior for that scope

## Import Media Storage

`import_media_storage.storage_mode` supports three values:

- `repo_assets`: copy imported media into a repo-owned public assets folder and write literal public links
- `staging_manual`: keep extracted media under `var/docs/import-staging/` and write media tokens for manual copying
- `r2_upload`: reserved for a future remote upload backend and unavailable until that backend exists

`repo_assets` is the default recommendation for new portable installs that do not have remote media infrastructure.
Use these folder conventions unless the host site has a stronger reason to choose different paths:

- `site/assets/docs/<scope>/img/<filename>`
- `site/assets/docs/<scope>/files/<filename>`

For `repo_assets`, configure:

```json
{
  "import_media_storage": {
    "storage_mode": "repo_assets",
    "repo_assets_path_prefix": "site/assets/docs/library",
    "repo_assets_public_path_prefix": "/assets/docs/library"
  }
}
```

Image and file imports then write links like:

```md
![Example](/assets/docs/library/img/example.png)
[Download Example](/assets/docs/library/files/example.pdf)
```

For `staging_manual`, configure:

```json
{
  "media_path_prefix": "docs/library",
  "import_media_storage": {
    "storage_mode": "staging_manual",
    "repo_assets_path_prefix": "site/assets/docs/library",
    "repo_assets_public_path_prefix": "/assets/docs/library"
  }
}
```

Docs Import writes links like:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.png&#93;&#93;)</code></pre>

The local service stages inline extracted media under `var/docs/import-staging/` and reports the `media_path` that must be copied manually.
Staged source image and file imports also remain manual-copy flows in this mode.

`r2_upload` is intentionally config-shaped but not operational.
Do not put R2 credentials or any other remote credentials in `docs-viewer/config/scopes/docs_scopes.json`, generated browser config, docs source, or UI text.
Future remote upload support should read credentials from environment variables or platform secrets and fail closed when the backend is unavailable.

## Local Service

Standalone local service defaults and schema live in `docs-viewer/config/defaults/docs-viewer-service.json` and `docs-viewer/config/schema/docs-viewer-service.schema.json`.

## Browser Config

`docs-viewer/config/routes/docs-viewer-routes.json` is the browser-safe manage/local route-config registry.
`site/docs-viewer/config/routes/docs-viewer-public-routes.json` is the browser-safe public route-config registry served at `/docs-viewer/config/routes/docs-viewer-public-routes.json`.

- Route registries are checked in and read by `site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js` before the app shell builds route context.
- Shared and standalone route shells should carry only `data-route-id` and `data-route-config-url` for boot route context.
- Inline route-config scripts and legacy route data attributes such as `data-index-url`, `data-viewer-scope`, and `data-management-base-url` are not route-config inputs.

Each route record owns:

- route id and route path
- route type, such as `public` or `manage`
- default scope
- viewer base URL and scope-query policy
- generated docs/search URL defaults
- Docs Viewer config, route-owned UI text, and report registry URLs
- static access intent, panel defaults, and hosted-view records

Static public route config must not contain credentials, local filesystem paths, or write authority.
For the local `/docs/` shell, `docs-viewer/services/docs_viewer_service.py` serves the manage/local registry URL with loopback management and generated-read base URLs injected from service config.
The same service maps the public route registry URL to the site-owned public registry so `/docs/` and public routes see the same public config owner.
Backend reachability and write availability still come from the service capability flow, not from static route config.

`docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json` are generated by `./docs-viewer/build/build_docs.py --write`.

It exposes browser-safe settings only:

- default scope id
- each scope's viewer base URL
- each scope's type, used with `docs_viewer.scope_type_badges` for scope selector prefixes
- scope route policy such as `include_scope_param`
- default document id, sourced from scope config rather than route config
- generated docs index URL
- docs search index URL and search policy
- viewer display settings under `docs_viewer`

The full config includes every configured Docs Viewer scope for the local manage shell.
The public config includes only static public read-only route scopes: entries whose source scope config has `include_scope_param: false` and a route base outside `/docs/`.
Public route files such as `site/library/index.html` and `site/analysis/index.html` are tracked static shells.
New public route shells render from `docs-viewer/templates/public-route/index.html`, identify themselves with `data-route-id`, and read the public route registry from `/docs-viewer/config/routes/docs-viewer-public-routes.json`.
The generated public config lets those pages resolve their scope from `viewer_base_url`.

Do not hand-edit `docs-viewer-config.json` or `docs-viewer-public-config.json`, because they are generated files.
After changing `docs-viewer/config/scopes/docs_scopes.json`, rerun the docs build for the affected scope or scopes so both generated browser configs stay current.

`docs_viewer.scope_type_badges` maps scope types to selector display labels and emoji.
Each browser scope record may also include `meta`, a short user-configured descriptor shown in the custom scope menu beside the scope id.
The Docs Viewer scope dropdown prefixes each scope id with the configured emoji for its `scope_type` and shows the per-scope `meta` value when present.
Use type-level badges for shared meaning such as public versus local availability, not per-scope branding.
Use per-scope `meta` for compact operational context such as `public scope` or `local management`.

## UI Text

`site/docs-viewer/config/ui-text/public.json` owns public read-only Docs Viewer copy and is served at `/docs-viewer/config/ui-text/public.json`.
It currently includes only reader-facing public-entrypoint text consumed during public route execution.

`docs-viewer/config/ui-text/manage.json` owns local/manage Docs Viewer copy, including management actions, settings, import workflow, scope lifecycle, status mutation, source-management, and manage-only modal text.

Route records choose the bundle through `config_urls.ui_text`.

- Do not point public route records at the manage bundle, and do not keep shared compatibility UI-text paths for retired bundles.
- Do not put Studio-only copy or workflow-specific service contracts in either UI text bundle.
