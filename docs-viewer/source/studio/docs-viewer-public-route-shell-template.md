---
doc_id: docs-viewer-public-route-shell-template
title: Public Route Shell Template
added_date: 2026-06-13
last_updated: 2026-06-13
parent_id: docs-viewer-public-scopes
viewable: true
---
# Public Route Shell Template

Public Docs Viewer route shells are tracked static HTML files under `site/`.
They are part of the canonical deploy root and are not generated during deploy.

New public read-only scopes use a Docs Viewer-owned creation template:

- template: `docs-viewer/templates/public-route/index.html`
- output: `site/<route>/index.html`

The template exists so New Scope can create a new route shell without copying an existing installed route such as `site/library/index.html`.
After creation, the rendered `site/<route>/index.html` file is a normal tracked source file.

## Owner

The template is owned by Docs Viewer because Docs Viewer owns public scope creation, route config, runtime boot, and the public shell contract.
Static-site validation checks the deploy root, but it does not own the template and does not render route shells.

The lifecycle renderer lives in `docs-viewer/services/docs_scope_manifest.py`.
New Scope public-readonly creation renders the template during the local write action, not during deploy.

## Render Inputs

The renderer injects only route-shell values:

- page title
- body class
- `data-route-id`
- search enabled state
- search placeholder
- search aria label

Scope behavior stays in config records rather than in copied shell logic.
The public route config owns the fixed scope, default document, viewer base URL, public generated payload URLs, UI text config, and panel settings.

## Shell Contract

The rendered shell must include:

- public site frame and base CSS
- Docs Viewer CSS: `/docs-viewer/static/css/docs-viewer.css`
- Docs Viewer root with `data-route-id`
- `data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"`
- header controls mount with:
  - `data-docs-viewer-header-controls-mount`
  - `data-enable-search`
  - `data-search-placeholder`
  - `data-search-aria-label`
- public runtime entrypoint: `/docs-viewer/runtime/js/public/docs-viewer-public.js`

The shell must not load or expose:

- management runtime modules
- import runtime modules
- report runtime modules
- management CSS
- localhost service URLs
- source-editing, import, settings, scope lifecycle, or write-capable controls

Public management access is controlled by route config and runtime access projection.
The public route shell does not use a static `data-allow-management="false"` attribute.

## New Scope Flow

For `publishing_mode: "public_readonly"`, New Scope creates or updates this file set:

- source docs under `docs-viewer/source/<scope>/`
- scope config under `docs-viewer/config/scopes/docs_scopes.json`
- working generated docs/search payloads under `docs-viewer/generated/`
- published public docs/search payload snapshots under `site/assets/data/`
- public route registry records
- rendered route shell at `site/<route>/index.html`
- scope manifest ownership records

The route shell is created from the template.
The route record is written to the existing public route registries.
The initial generated docs/search outputs are synced into the configured public `site/assets/data/...` publish roots.

## Delete Scope Flow

Delete Scope may remove a user-created public route shell only when the scope manifest records it as owned by that lifecycle action.
It also removes user-created public route records and scope-owned public docs/search payloads.

Delete Scope must not remove shared public runtime files, shared CSS, UI text, route registry files themselves, or unrelated route shells.
Delete Scope also must not remove a scope that is the `default_scope_id` for a management route.
That guard protects portable installs where public scopes may all be user-created, while the original management entry scope remains route-owned.

## Maintenance

Changing the template does not automatically rewrite installed public route shells.
Existing route shells are tracked source files and remain deploy input as-is.

When the shell contract changes, update installed route shells as an explicit source edit or through a maintenance tool that writes source files.
That maintenance step is not a deploy build process.

After changing the template, installed route shells, or lifecycle renderer, run focused lifecycle tests and public Docs Viewer smoke checks.
Use `bin/site-validate` for deploy-root validation.
