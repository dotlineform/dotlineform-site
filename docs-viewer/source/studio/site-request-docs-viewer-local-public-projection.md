---
doc_id: site-request-docs-viewer-local-public-projection
title: Docs Viewer Static HTML Export
added_date: 2026-06-28
last_updated: 2026-06-28
parent_id: change-requests
viewable: true
---
# Docs Viewer Static HTML Export

## Status

Proposed.

The earlier local-to-public Docs Viewer scope projection idea is cancelled. The static HTML export is enough for the current need.

## Problem

Repo-backed local Docs Viewer scopes are readable only through the local `/docs/` management app. Current repo-backed local scopes include `studio` and `tmp`. Off the local machine, the practical options are poor:

- run the local apps in Codespaces
- browse raw Markdown files in GitHub
- rely on memory or local-only access

Those options are slower than opening a simple rendered HTML page, especially from another machine or on unreliable connectivity.

The need is not remote management and not a full Docs Viewer experience. The need is quick read-only access to rendered docs.

## Decision

Implement a static HTML export workflow.

The export reads existing generated Docs Viewer payloads and writes pre-rendered HTML pages:

- one root `index.html`
- one shared `styles.css`
- one HTML file per doc

The export includes every generated doc for the selected repo-backed local scope. It does not filter to `viewable: true`.

No Docs Viewer runtime is required.

No local server is required.

No JSON fetches are required.

No public Docs Viewer scope, route config, search index projection, or local-to-public payload projection is required.

## Cancelled Approach

Do not implement the heavier local-to-public Docs Viewer projection for this request.

Cancelled pieces:

- `docs-studio` as a public Docs Viewer payload scope
- copying/projecting `docs-viewer/generated/docs/studio/` into `site/assets/data/docs/scopes/docs-studio/`
- projecting `docs-viewer/generated/search/studio/index.json`
- creating public Docs Viewer route config for `/docs-studio/`
- creating a public Docs Viewer runtime route shell for this workflow
- rewriting generated Docs Viewer JSON payload URLs for public runtime use
- adding a projection registry for local-to-public scope mirrors

Those can be reconsidered later only if the plain HTML export proves insufficient.

## Output Destinations

The exporter should be available to all repo-backed local Docs Viewer scopes. `studio` is the first practical target and the examples below use it, but the implementation should not hard-code `studio`.

This does not apply to external local scopes whose source and generated JSON are saved outside the repo, such as `local_external` scopes under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/`. Those scopes need a separate portability/export decision because their data ownership and filesystem boundary are different.

The exporter should support both private/offline and public static destinations.

Private/offline output:

```text
var/docs-offline/studio/
  index.html
  styles.css
  docs/
    dev-home.html
    scripts-cloud-environments.html
    site-request-docs-viewer-static-html-export.html
```

Public static output:

```text
site/docs-studio/
  index.html
  styles.css
  docs/
    dev-home.html
    scripts-cloud-environments.html
    site-request-docs-viewer-static-html-export.html
```

The public output would be available from:

```text
https://dotlineform.com/docs-studio/
```

Anything under `site/` is public once deployed. The private `var/` output should remain available so future non-public docs can use the same exporter without being deployed.

Export always writes both destinations in the same workflow:

- `var/docs-offline/<scope>/`
- `site/docs-<scope>/`

There are no destination checkboxes in the first implementation. Keeping both outputs together avoids per-scope preferences and UI state.

Destination folders are exclusively owned by this exporter. They are directly derived from the scope name and are wiped as the first step of every apply run before the current export is written. Do not add stale-file tracking, delete manifests, fallback reconciliation, or partial sync semantics.

## Scope Lifecycle

New Scope does not need export-specific bookkeeping. If a new scope is repo-backed local, the Export action can recognise it from the normal scope config and use the deterministic destination paths.

Delete Scope does need export cleanup. When deleting a repo-backed local scope, the delete workflow should remove any deterministic exporter-owned outputs for that scope, such as:

```text
var/docs-offline/<scope>/
site/docs-<scope>/
```

This cleanup should use the same path validation as the exporter. It should not look for manifests or scan arbitrary folders.

## Inputs

Use existing generated Docs Viewer payloads as input:

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

This works from direct `file://` browser access because it does not rely on JavaScript `fetch()` loading local JSON.

## Export UI

Expose the workflow from the existing Docs Viewer Actions button as:

```text
Export
```

There is currently no other Docs Viewer export action, so the short label is enough. The modal should make the output format and destinations clear.

Suggested modal controls:

- source scope summary, such as `studio`
- document count and default document
- fixed destination summary:
  - private offline folder: `var/docs-offline/studio/`
  - public site folder: `site/docs-studio/`
- preview button showing destination folders that will be replaced and files that will be written
- export/apply button that writes both destinations
- delete button that deletes both destinations
- explicit public visibility warning because `site/docs-<scope>/` is always written

The action should be available when the active `/docs/` scope is repo-backed local. Current repo-backed local scopes are `studio` and `tmp`.

The service should accept the active local scope explicitly.

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
- render root index page
- render one document page per doc
- write shared CSS
- rewrite internal Docs Viewer links to local `.html` links
- produce a preview diff before writing
- wipe both destination folders before writing current output
- delete both destination folders when requested

The service should generate the private bundle first, validate it, then replace the public `site/docs-<scope>/` destination with the same generated files. This keeps rendering and link rewriting in one path.

## Implementation Tasks

This should be a fairly straightforward implementation: one focused exporter service, one small management API surface, and one Docs Viewer Actions modal.

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
  - rendering or copying `styles.css`
  - rewriting internal Docs Viewer links
  - computing a replace plan for both destination folders
  - wiping and writing both destination folders
  - deleting both destination folders
- Keep the service independent from Docs Viewer frontend code.
- Use generated payloads as input; do not parse or render source Markdown.
- Reject public, local-external, and non-repo-backed scopes.

### 2. Export paths and defaults

- Define deterministic destination paths:
  - offline: `var/docs-offline/<scope>/`
  - site: `site/docs-<scope>/`
- Allow `studio` to use `site/docs-studio/` naturally through the same pattern.
- Validate all output paths stay inside the intended repo roots.
- Treat destination folders as exporter-owned generated output.
- Wipe both destination folders before writing the new export.
- Do not keep a manifest or track stale files.
- Add Delete Scope cleanup for these deterministic exporter-owned outputs.
- Do not add New Scope bookkeeping; repo-backed local scopes are recognised from scope config.

### 3. Link rewriting

- Rewrite `/docs/?scope=<scope>&doc=<doc_id>` links to local HTML links.
- From the root index page, link to `docs/<doc_id>.html`.
- From a document page, link to `<doc_id>.html`.
- Preserve fragments where possible.
- Leave external links unchanged.
- Emit warnings for links to unknown doc ids.

### 4. Preview/apply API

- Add management-only endpoints, likely under existing Docs management routes:
  - preview export plan
  - apply export plan
  - delete export outputs
- Request shape should include:

```json
{
  "scope": "studio",
  "action": "export"
}
```

- Preview response should include:
  - scope
  - doc count
  - destination paths
  - destination folders that will be replaced
  - files that will be written after replacement
  - warnings
  - public visibility warning
- Apply response should include:
  - written file count
  - replaced destination folders
  - destination links/paths
  - warnings
- Delete response should include:
  - deleted destination folders
  - paths that were already absent

### 5. Docs Viewer UI

- Add one Actions menu item: `Export`.
- Show it only for repo-backed local scopes.
- Add an export modal with:
  - source scope summary
  - document count/default document
  - fixed offline and site destination paths
  - preview button
  - export/apply button
  - delete button
  - public visibility warning
  - result links/paths after apply
- Keep this separate from existing public-scope `Publish` actions.

### 6. Tests

- Add Python unit tests for:
  - tree doc-id collection
  - doc payload loading
  - metadata escaping
  - per-doc page rendering
  - index page rendering
  - internal link rewriting
  - destination-folder replacement plan
  - output path validation
  - rejection of public/local-external scopes
- Add route/API tests for preview and apply responses.
- Add a small JS syntax check for new frontend modules.
- Browser smoke is optional; use it only to verify the modal/API boundary if the implementation touches route boot or Actions wiring in a risky way.

### 7. Manual verification

- Export `studio` to `var/docs-offline/studio/`.
- Open `var/docs-offline/studio/index.html` directly from the filesystem.
- Confirm links and CSS work without a server.
- Export `studio` to `site/docs-studio/`.
- Run `bin/site-preview` and open `/docs-studio/`.
- Confirm no Docs Viewer runtime, route config, JSON fetch, or local service is required.

## Link Rewriting

Required rewrite behavior:

- `/docs/?scope=studio&doc=<doc_id>` -> `docs/<doc_id>.html` from the index page
- `/docs/?scope=studio&doc=<doc_id>` -> `<doc_id>.html` from a document page
- links to unknown docs can remain unchanged or be flagged in an export warning

The first implementation should preserve doc ids as filenames where safe. If a doc id is not a safe filename, the exporter should fail rather than invent an ambiguous mapping.

## Optional Output

Optional outputs:

- public copy under `site/docs-studio/`
- copied local media/assets if the rendered docs reference files that are not already browser-reachable
- previous/next links based on tree order
- generated timestamp and source scope summary

Media copying can be a later enhancement if current docs do not need it.

Zip output is intentionally not part of the first implementation. If a zip archive is needed, the user can create it manually from the generated `var/docs-offline/<scope>/` folder.

## Verification

Automated checks should cover:

- generated input payload loading
- tree-to-index rendering
- by-id page rendering
- metadata escaping
- `content_html` insertion
- internal docs link rewriting
- destination-folder replacement
- destination path validation
- public-output warning when `site/` is selected
- deletion of both deterministic destination folders

Manual checks:

- open `var/docs-offline/studio/index.html` directly from the filesystem
- confirm the generated index links open document pages
- confirm local CSS loads
- confirm internal doc links resolve to sibling `.html` files
- confirm no JavaScript/runtime/server dependency is required
- open `/docs-studio/` on the public site or local static preview
- confirm public-copy links stay under `/docs-studio/`
- use the modal Delete button and confirm both destination folders are removed

## Open Questions

- Should media copying be included in a later enhancement, or is the current linked-asset behavior enough?
