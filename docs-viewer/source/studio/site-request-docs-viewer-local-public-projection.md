---
doc_id: site-request-docs-viewer-local-public-projection
title: Docs Viewer Local To Public Projection
added_date: 2026-06-28
last_updated: 2026-06-28
parent_id: change-requests
viewable: true
---
# Docs Viewer Local To Public Projection

## Status

Proposed.

## Problem

Local Docs Viewer scopes such as `studio` are readable only through the local `/docs/` management app. Off the local machine, the practical options are poor:

- run the local apps in Codespaces
- browse raw Markdown files in GitHub
- rely on memory or local-only access

Those options are slower than opening a normal read-only Docs Viewer route, especially from another machine or on unreliable connectivity.

The need is not remote management. The need is a convenient read-only public/static view of selected local docs.

## Principle

Introduce a local-to-public projection workflow for Docs Viewer.

A local management scope remains local and continues to be managed through `/docs/`. A separate public read-only projection is published into `site/` so it can be served by GitHub Pages or any static host.

Example:

- local source/management scope: `studio`
- local manage route: `/docs/?scope=studio`
- public projection route: `/studio-docs/`
- public projection payload scope: `studio-docs`

The public projection should be unadvertised by default:

- no main navigation link
- no sitemap promotion unless explicitly requested
- no public index card

It is still public if deployed to `site/`. Anyone with the URL, or anyone who discovers the static files, can read it.

## Non-Goals

This request does not make `/docs/` remotely available.

It does not add authentication, remote write access, remote source editing, or a hosted management service.

It does not turn `studio` itself into a public scope.

It does not copy local service APIs, management controls, source-editor controls, import controls, settings, publishing controls, or write endpoints into the public route.

## Target Shape

The target user-facing result is a static read-only route such as:

```text
https://dotlineform.com/studio-docs/
```

The route loads the existing public Docs Viewer runtime, not the local management runtime.

Expected static files:

```text
site/studio-docs/index.html
site/assets/data/docs/scopes/studio-docs/index-tree.json
site/assets/data/docs/scopes/studio-docs/recently-added.json
site/assets/data/docs/scopes/studio-docs/by-id/<doc_id>.json
site/assets/data/search/studio-docs/index.json
```

Source working files remain owned by the local scope:

```text
docs-viewer/source/studio/
docs-viewer/generated/docs/studio/
docs-viewer/generated/search/studio/index.json
```

## Copy With Projection, Not Raw Copy

The workflow is conceptually a copy from local generated output to public static output, but it must not be a blind `cp -R`.

Generated local payloads can contain local/manage URLs such as:

```text
/docs/?scope=studio&doc=<doc_id>
/docs/generated/payload?scope=studio&doc_id=<doc_id>
```

The public projection must rewrite route and payload references so they point at the public route and public static assets:

```text
/studio-docs/?doc=<doc_id>
/assets/data/docs/scopes/studio-docs/by-id/<doc_id>.json
```

The projection should also make sure browser route config, search entries, tree content URLs, recently-added content URLs, by-id metadata URLs, and internal rewritten links all agree with the public projection route.

## Configuration Model

The local scope should stay local:

```json
{
  "scope_id": "studio",
  "scope_type": "local",
  "viewer_base_url": "/docs/",
  "include_scope_param": true
}
```

The public projection should be represented explicitly, either as a new projection registry or as a carefully constrained scope type.

Candidate projection record:

```json
{
  "projection_id": "studio-docs",
  "source_scope_id": "studio",
  "route_path": "studio-docs",
  "public_scope_id": "studio-docs",
  "publish_output": "site/assets/data/docs/scopes/studio-docs",
  "publish_search_output": "site/assets/data/search/studio-docs/index.json",
  "default_doc_id": "dev-home",
  "advertised": false
}
```

The important distinction is ownership:

- `source_scope_id` identifies the local generated data to project.
- `public_scope_id` identifies the public static payload namespace.
- `route_path` identifies the static reader route.
- `advertised: false` means the route exists but is not promoted in navigation.

Avoid modelling this as “make `studio` public”. That would blur the local management scope with the public reader install.

## Build And Publish Workflow

The workflow should be explicit from `/docs/` management or a focused script/service command.

Proposed flow:

1. Rebuild the local source scope normally.
2. Build or refresh the local search index normally.
3. Preview projection changes from local generated data to public static output.
4. Confirm and apply the projection.
5. Write/sync public route shell, public route config, public docs payloads, and public search payload.

For `studio -> studio-docs`, inputs are:

```text
docs-viewer/generated/docs/studio/
docs-viewer/generated/search/studio/index.json
```

Outputs are:

```text
site/studio-docs/index.html
site/assets/data/docs/scopes/studio-docs/
site/assets/data/search/studio-docs/index.json
site/docs-viewer/config/routes/docs-viewer-public-routes.json
site/docs-viewer/config/defaults/docs-viewer-public-config.json
```

The projection should support a dry-run/preview mode before writing, similar in spirit to existing publish/status workflows.

## Docs Viewer Work Needed

### Backend/service

Add a focused projection service, for example:

```text
docs-viewer/services/docs_public_projection.py
```

Responsibilities:

- load projection config
- validate source scope is local/manage-owned
- validate projection output stays under `site/`
- read local generated docs payloads and search index
- rewrite local/manage URLs to public read-only URLs
- compute preview diff/status
- sync projected public files
- remove stale public by-id payloads that no longer exist in the projection
- update public route registry/config if needed

The existing publish service for public scopes is a useful reference, but this workflow is not the same as publishing a normal public scope. It publishes a public projection of a local scope.

### Route shell/config

Create a public route shell from the existing public route template:

```text
site/studio-docs/index.html
```

Register it in:

```text
site/docs-viewer/config/routes/docs-viewer-public-routes.json
```

The route config must point only at public static payloads under `site/assets/data/...`.

### Payload projection

Projection must handle at least:

- `index-tree.json`
- `recently-added.json`
- `by-id/*.json`
- search index entries
- route URLs
- content URLs
- internal links that currently point back to `/docs/?scope=studio`

The first implementation can preserve the same document ids and tree structure.

### UI

Expose the workflow from local `/docs/` only if the source scope has a configured public projection.

Possible management UI:

- Actions menu item: `Publish public projection`
- preview/status modal showing pending public projection changes
- apply action with explicit confirmation
- public route link after successful publish

This should be separate from the existing public-scope `Publish` action if the semantics differ enough to avoid confusion.

### Safety checks

Before applying a projection:

- fail if output paths resolve outside `site/`
- fail if the source scope is already public unless that is explicitly supported later
- fail if route path collides with an existing public route
- fail if public scope id collides with an unrelated public scope
- warn that unadvertised still means public
- scan projected payloads for local generated-read URLs and local management URLs
- optionally scan projected payloads for obvious local filesystem paths

## Offline Plain HTML Option

There is a simpler non-public option for the same underlying need: generate a plain HTML folder from the local generated Docs Viewer payloads.

This does not use the Docs Viewer runtime, route config, JSON fetches, search runtime, or local server. It produces static HTML files that can be opened directly in a browser from the filesystem.

Example output:

```text
var/docs-offline/studio/
  index.html
  styles.css
  docs/
    dev-home.html
    scripts-cloud-environments.html
    site-request-docs-viewer-local-public-projection.html
```

The same generated bundle can optionally be copied to the public site root:

```text
site/studio-docs/
  index.html
  styles.css
  docs/
    dev-home.html
    scripts-cloud-environments.html
    site-request-docs-viewer-local-public-projection.html
```

That would make the plain HTML export available from:

```text
https://dotlineform.com/studio-docs/
```

This avoids the full Docs Viewer local-to-public scope projection workflow. There is no public Docs Viewer route config, no public scope config, no JSON payload publishing, no runtime asset dependency, and no search-index projection. It is simply a set of pre-rendered static HTML pages.

The workflow can support both destinations:

- private/offline output under `var/docs-offline/studio/`
- public static output under `site/studio-docs/`

The public copy can be produced as part of the same exporter run after the private bundle has been generated and validated.

### Plain HTML Export UI

Expose the plain HTML workflow from the existing Docs Viewer Actions button as:

```text
Export
```

There is currently no other Docs Viewer export action, so the short label is enough. The modal should make the output format and destinations clear.

Suggested modal controls:

- source scope summary, such as `studio`
- document count and default document
- destination checkboxes:
  - private offline folder: `var/docs-offline/studio/`
  - public site folder: `site/studio-docs/`
  - optional zip archive: `var/docs-offline/studio-docs.zip`
- preview button showing files that would be written, changed, and removed
- apply button that writes the selected destinations
- explicit public visibility warning when `site/studio-docs/` is selected

The backing service can be a single exporter, for example:

```text
docs-viewer/services/docs_static_html_export.py
```

Candidate request shape:

```json
{
  "scope": "studio",
  "destinations": ["offline", "site"],
  "zip": false
}
```

The service should generate the private bundle first, validate it, then copy the same generated files to selected secondary destinations such as `site/studio-docs/` or a zip archive. This keeps rendering and link rewriting in one path.

The exporter can use existing generated payloads as input:

```text
docs-viewer/generated/docs/studio/index-tree.json
docs-viewer/generated/docs/studio/by-id/<doc_id>.json
```

Each `by-id` payload already contains rendered HTML in `content_html`. The offline exporter can read that content and insert it into a small page template:

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <nav><a href="../index.html">Index</a></nav>
  <main>
    <h1>{{ title }}</h1>
    {{ content_html }}
  </main>
</body>
</html>
```

Metadata such as `title` must be HTML-escaped. `content_html` can be inserted as generated HTML from the existing Docs Viewer builder.

The root `index.html` should render a simple nested tree from `index-tree.json`, with links to `docs/<doc_id>.html`.

The shared stylesheet can stay as a local file:

```html
<link rel="stylesheet" href="styles.css">
```

or, from a document page:

```html
<link rel="stylesheet" href="../styles.css">
```

This works from direct `file://` browser access because it does not rely on `fetch()` loading local JSON.

Required rewrite behavior:

- `/docs/?scope=studio&doc=<doc_id>` -> `docs/<doc_id>.html` from the index page
- `/docs/?scope=studio&doc=<doc_id>` -> `<doc_id>.html` from a document page
- links to unknown docs can remain unchanged or be flagged in an export warning

Optional output:

- `studio-docs-offline.zip`
- public copy under `site/studio-docs/`
- copied local media/assets if the rendered docs reference files that are not already browser-reachable
- previous/next links based on tree order
- generated timestamp and source scope summary

This plain HTML option is the lowest-complexity portable format. It is not a Docs Viewer experience: no interactive tree panel, no search, no route state, no app shell, and no management context.

If current `studio` content is acceptable to publish, the public static copy may be the most pragmatic first implementation. The private `var/` output should still remain available so future non-public docs can use the same exporter without being deployed.

## Offline Docs Viewer Bundle Option

A richer offline option would copy runtime JS/CSS and JSON into a self-contained folder. That can preserve more of the Docs Viewer experience, but browser `file://` restrictions may block JavaScript `fetch()` calls to local JSON files. It would be reliable when served by a tiny local static server, but not necessarily by double-clicking `index.html`.

Because the original need is quick off-machine reading, the plain HTML option should be considered before a runtime bundle.

## Visibility And Content Risk

This feature is useful only if the projected source content is acceptable to publish.

For `studio`, that needs a deliberate content decision. The docs contain implementation notes, local operating assumptions, and request history. That may be fine for an unadvertised public route, or it may be too much.

If content is not safe to publish publicly, use one of the offline options instead of the public projection workflow.

## Verification

Automated checks should cover:

- projection config validation
- URL rewrite behavior
- stale output removal
- public route registry update
- public config update
- generated public payloads contain no `/docs/generated/...` URLs
- generated public payloads do not require `scope=studio`
- public route loads using only public runtime/config/data assets
- management runtime/assets are not loaded by `/studio-docs/`

Manual checks:

- open `/studio-docs/`
- confirm the default document loads
- confirm tree navigation works
- confirm search works if search is included
- confirm internal doc links stay on `/studio-docs/`
- confirm no management controls render

Plain HTML offline checks:

- open `var/docs-offline/studio/index.html` directly from the filesystem
- confirm the generated index links open document pages
- confirm local CSS loads
- confirm internal doc links resolve to sibling `.html` files
- confirm no JavaScript/runtime/server dependency is required

Plain HTML public-copy checks:

- open `/studio-docs/` on the public site or local static preview
- confirm the generated index links open document pages
- confirm local CSS loads from `site/studio-docs/styles.css`
- confirm internal doc links stay under `/studio-docs/`
- confirm no Docs Viewer runtime, public route config, or JSON payload fetch is required

## Open Questions

- Should the projection include every generated `studio` doc, or only docs with `viewable: true`?
- Should the route be `/studio-docs/`, `/dev-docs/`, or something else?
- Should this be implemented as a projection registry or as a new constrained `scope_type`?
- Should the publish action live beside existing public-scope publish actions or use a separate label and modal?
- Is unadvertised public visibility acceptable for the initial `studio` docs content?
- Should the plain HTML offline exporter be implemented first as a lower-risk step?
- Should the first implementation write only `var/docs-offline/studio/`, or also copy the generated bundle to `site/studio-docs/` by default?
