---
doc_id: site-request-docs-viewer-local-public-projection
title: Docs Viewer Static HTML Export
added_date: 2026-06-28
last_updated: 2026-06-29
parent_id: change-requests
---
# Docs Viewer Static HTML Export

Status: implemented 2026-06-29.

Implemented owner surfaces:

- exporter service: `docs-viewer/services/docs_static_html_export.py`
- management apply endpoint: `POST /docs/export/static-html/apply`
- management delete endpoint: `POST /docs/export/static-html/delete`
- Docs Viewer Actions menu item: `Export` for repo-backed local scopes with static export capability

Implement a static HTML export workflow.

The export reads existing generated Docs Viewer payloads and writes pre-rendered HTML pages:

- one root `index.html`
- one shared `styles.css`
- one HTML file per doc

The export includes every generated doc for the selected repo-backed local scope. It does not filter to `viewable: true`.

## Output Destination

The exporter should be available to all repo-backed local Docs Viewer scopes.

This export does not apply to external local scopes whose source and generated JSON are saved outside the repo, such as `local_external` scopes under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/`. Those scopes need a separate portability/export decision because their data ownership and filesystem boundary are different.

Destination: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-export/<scope>/`

Example:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/docs-export/studio/`
  index.html
  styles.css
  docs/
    dev-home.html
    scripts-cloud-environments.html
    site-request-docs-viewer-static-html-export.html
```

- Destination folders are directly derived from the scope name and are wiped as the first step of every apply run before the current export is written.
- Do not add stale-file tracking, delete manifests, fallback reconciliation, or partial sync semantics.
- Media copying may be a later enhancement but current docs do not need it.

## Scope Lifecycle Dependencies

New Scope does not need export-specific bookkeeping. If a new scope is repo-backed local, the Export action can recognise it from the normal scope config and use the deterministic destination path.

Delete Scope does not need export cleanup. The user is responsible for deleting any stale export destinations.


## Inputs

Use existing generated Docs Viewer payloads as input:

e.g for studio scope:

```text
docs-viewer/generated/docs/studio/index-tree.json
docs-viewer/generated/docs/studio/by-id/<doc_id>.json
```

Each `by-id` payload already contains rendered HTML in `content_html`.

The exporter should not parse Markdown or re-render Markdown. It should consume generated payloads and template them into standalone HTML pages.

## Template Shape

Each document page can be rendered from a small template:

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
    {{ content_html }}
  </main>
</body>
</html>
```

Metadata such as `<title>` must be HTML-escaped. `content_html` can be inserted as generated HTML from the existing Docs Viewer builder and already includes the source document heading.

The root `index.html` should render a simple nested tree from `index-tree.json`, with links to `docs/<doc_id>.html`.

The shared stylesheet is referenced as a local file from a document page:

```html
<link rel="stylesheet" href="../styles.css">
```

This works from direct `file://` browser access.

## Export UI

Expose the workflow from the existing Docs Viewer Actions button as:

```text
Export
```

There is currently no other Docs Viewer export action, so the short label is enough. The modal should make the output destination clear.

modal:

- source scope, e.g. `studio`
- document count and default document if specified
- destination folder: e.g. `/docs-export/studio/`
- cancel, export buttons
- The modal should not own the action. it is closed when the response is sent (export or cancel).
- Mouse cursor is in waiting state whilst the export is running.

The action should be available when the active `/docs/` scope is repo-backed local. Export action is disabled for any other type of scope.


## Backend Service

Add one focused exporter service:

```text
docs-viewer/services/docs_static_html_export.py
```

Candidate request shape:

```json
{
  "scope": "studio",
  "action": "export"
}
```

Responsibilities:

- validate scope and generated payload paths
- reject public, local-external, and other non-repo-backed scopes unless explicitly supported later
- read `index-tree.json`
- read referenced `by-id/*.json` payloads
- render root index-tree page
- render one document page per doc
- write shared CSS file
- rewrite internal Docs Viewer links to local `.html` links
- wipe destination folder before writing current output

## Implementation Tasks

This should be a straightforward implementation: one focused exporter service, one small management API surface, and one Docs Viewer Actions modal.

### 1. Service core

- Add `docs-viewer/services/docs_static_html_export.py`.
- Add pure functions for:
  - resolving repo-backed local scope input paths
  - loading `index-tree.json`
  - collecting doc ids from the tree
  - loading `by-id/<doc_id>.json`
  - validating doc ids are safe HTML filenames
  - rendering root `index.html`
  - rendering per-doc HTML pages
  - rendering `styles.css`
  - rewriting internal Docs Viewer links
  - computing a replace plan for destination folder
  - wiping and writing destination folder
- Keep the service independent from Docs Viewer frontend code.
- Use generated payloads as input; do not parse or render source Markdown.
- Reject public, local-external/non-repo-backed scopes.

### 2. Link rewriting

- Rewrite `/docs/?scope=<scope>&doc=<doc_id>` links to local HTML links.
- From the root index page, link to `docs/<doc_id>.html`.
- From a document page, link to `<doc_id>.html`.
- Leave external links unchanged.
- Do not validate links.

### 3. Preview/apply API

- Add management-only endpoints under existing Docs management routes:
  - apply export plan
  - delete export outputs
- Request shape should include:

```json
{
  "scope": "studio",
  "action": "export"
}
```

### 4. Docs Viewer UI

- Add one Actions menu item: `Export`.
- Show it only for repo-backed local scopes.
- Add an export modal with:
  - source scope name
  - document count/default document
  - destination path
  - export button
- Keep this separate from existing public-scope `Publish` actions.

### 5. Tests

- Add Python unit tests for:
  - tree doc-id collection
  - doc payload loading
  - per-doc page rendering
  - index page rendering
  - internal link rewriting
  - output path validation
  - rejection of public/local-external scopes
- Add route/API tests for apply response.
- Add a small JS syntax check for new frontend modules.
- No browser smoke is required.
