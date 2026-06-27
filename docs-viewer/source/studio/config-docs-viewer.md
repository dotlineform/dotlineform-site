---
doc_id: config-docs-viewer
title: Config
added_date: 2026-05-12
last_updated: 2026-06-25
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Config

Docs Viewer configuration is split by owner and audience.

There are three main config shapes:

- Source scope config: `docs-viewer/config/scopes/docs_scopes.json`
- Local browser config: `docs-viewer/config/defaults/docs-viewer-config.json`
- Public browser config: `docs-viewer/config/defaults/docs-viewer-public-config.json`

The source scope config is the authoring and build registry.
It can describe Markdown source roots, generated output roots, local service behavior, public route policy, and management-only behavior.

The local browser config is the browser-safe projection for the local `/docs/` manage shell.
It includes the configured scopes that the local viewer needs to list, load, search, and manage.

The public browser config is the browser-safe projection for static public routes.
It includes only public read-only scopes and excludes local service and management details.

The public browser config also has a deploy-root copy:

- `site/docs-viewer/config/defaults/docs-viewer-public-config.json`

That copy exists because `site/` is the public preview and GitHub Pages root.
Static public pages must be able to load their config from the same tree that is served publicly.

The configs stay separate because they have different consumers:

- Build and service code need source-side paths and authoring policy.
- Browser runtime code needs URLs and display metadata.
- Public static pages must not receive local-only scopes or management capability.
- The deploy root needs a physical public copy rather than depending on runtime projection.

The projection flow is:

1. Edit the source scope config.
2. Run the docs build.
3. The build writes the local browser config.
4. The build writes the public browser config.
5. The build mirrors the public browser config into `site/`.

The projection code lives in `docs-viewer/build/docs_builder/browser_config.py`.
The build command entry point is `docs-viewer/build/build_docs.py`.

## Host settings

Local Docs Viewer service host, port, base URL, and capability flags are host runtime settings in `.env.local`, not checked-in Docs Viewer defaults.

## Public Site Config

Public site config is the public browser projection plus its deploy-root mirror.

The canonical generated file is:

- `docs-viewer/config/defaults/docs-viewer-public-config.json`

The static served copy is:

- `site/docs-viewer/config/defaults/docs-viewer-public-config.json`

The public projection is intentionally narrower than the local browser config.
It includes public route scopes such as `library`, `analysis`, and `moments`.
It does not include local-only scopes, management endpoints, source paths, or write capability.

Public route shells load this config through the public route registry.
They resolve their scope from `viewer_base_url`, so they do not need local service discovery.

## Source Scope Config

`docs-viewer/config/scopes/docs_scopes.json` is the source-side Docs Viewer config.
It is checked in and is read by docs builds, docs search builds, Docs Import, the standalone Docs Viewer service, live rebuild watching, generated-data reads, and source-write validation.

In local manage mode, [Docs Viewer Source Config Report](/docs/?scope=studio&doc=docs-viewer-source-config-report) reads this source config through the Docs Viewer service and shows it alongside browser and generated projections.
The report is read-only; source edits still go through source JSON edits or explicit manage-mode write controls.

- The Docs Viewer service still exposes a source-config settings contract for guarded source config writes.
- The `/docs/` manage-mode Settings modal exposes the active scope's `default_doc_id` through that contract.
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

Standalone local service defaults live in:

- `docs-viewer/config/defaults/docs-viewer-service.json`

The service schema lives in:

- `docs-viewer/config/schema/docs-viewer-service.schema.json`

## Route Config

The manage/local route-config registry is:

- `docs-viewer/config/routes/docs-viewer-routes.json`

The public route-config registry is:

- `site/docs-viewer/config/routes/docs-viewer-public-routes.json`

The public registry is served at `/docs-viewer/config/routes/docs-viewer-public-routes.json`.

- Route registries are checked in and read by `site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js` before the app shell builds route context.
- Shared and standalone route shells should carry only `data-route-id` and `data-route-config-url` for boot route context.
- Inline route-config scripts and legacy route data attributes such as `data-index-url`, `data-viewer-scope`, and `data-management-base-url` are not route-config inputs.

Each route record owns:

- route id and route path
- route type, such as `public` or `manage`
- default scope
- viewer base URL and scope-query policy
- generated docs/search URL defaults
- Docs Viewer config and report registry URLs
- static access intent, panel defaults, and hosted-view records

Static public route config must not contain credentials, local filesystem paths, or write authority.
For the local `/docs/` shell, `docs-viewer/services/docs_viewer_service.py` serves the manage/local registry URL with loopback management and generated-read base URLs injected from service config.
The same service maps the public route registry URL to the site-owned public registry so `/docs/` and public routes see the same public config owner.
Backend reachability and write availability still come from the service capability flow, not from static route config.

## Browser Config

The local browser config is:

- `docs-viewer/config/defaults/docs-viewer-config.json`

The public browser config is:

- `docs-viewer/config/defaults/docs-viewer-public-config.json`

Both files are generated by `./docs-viewer/build/build_docs.py --write`.

They expose browser-safe settings only:

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

Do not hand-edit generated browser configs.
After changing `docs-viewer/config/scopes/docs_scopes.json`, rerun the docs build for the affected scope or scopes so both generated browser configs stay current.

`docs_viewer.scope_type_badges` maps scope types to selector display labels and emoji.
Each browser scope record may also include `meta`, a short user-configured descriptor shown in the custom scope menu beside the scope id.
The Docs Viewer scope dropdown prefixes each scope id with the configured emoji for its `scope_type` and shows the per-scope `meta` value when present.
Use type-level badges for shared meaning such as public versus local availability, not per-scope branding.
Use per-scope `meta` for compact operational context such as `public scope` or `local management`.

## UI Text

Docs Viewer public and local/manage copy is hardcoded as design-time runtime text in the relevant JavaScript modules.

- Do not add shared compatibility UI-text paths for retired bundles.
- Do not add config-time UI text bundles for ordinary Docs Viewer labels.
