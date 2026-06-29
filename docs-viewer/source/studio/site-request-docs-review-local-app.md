---
doc_id: site-request-docs-review-local-app
title: Docs Review Local App
added_date: 2026-06-28
last_updated: 2026-06-29
parent_id: change-requests
viewable: true
---
# Docs Review Local App

## Status

Proposed.

## Problem

Returned document-content review needs a safe way to display temporary Docs Viewer-compatible documents under `var/analytics/data-sharing/import-preview/...`.

The normal `/docs/` app is the wrong host for those temporary documents. It assumes configured Docs Viewer scopes, canonical source Markdown, normal generated payload locations, public route links, and management actions such as source open/edit, delete, settings, rebuild, publish, drag/drop, and hierarchy mutation.

Review folders are different:

- they are temporary local artifacts
- they are not configured scopes
- they are not canonical source documents
- their generated payloads live under `var/...`
- their source folders may be deleted manually
- most manage-mode actions are irrelevant or unsafe

The first implementation should avoid coupling this workflow to normal `/docs/`.

## Decision

Create a distinct local review app:

- route: `/docs-review/`
- frontend/repo area: `docs-viewer-review/`
- same local Docs Viewer server process
- separate frontend entrypoint and route-specific modules
- minimal read-only Docs Viewer experience for temporary review folders

The review app is not a new Docs Viewer scope system. It is a local app that lists review folders under `var/analytics/data-sharing/import-preview/...`, builds generated Docs JSON from the selected folder's source Markdown, and displays the resulting tree and document payloads.

The normal `/docs/` UI should remain completely unaware of this capability.

## Ownership Boundary

Data Sharing owns returned-package parsing and temporary source Markdown creation.

For this workflow, Data Sharing review should only create or refresh a folder like:

```text
var/analytics/data-sharing/import-preview/<folder-id>/
  manifest.json
  source/
    <doc-id>.md
```

Data Sharing does not own folder listing, generated Docs JSON, document rendering, folder opening, or review app navigation.

Docs Review owns:

- listing subfolders under `var/analytics/data-sharing/import-preview/...`
- showing selected folder metadata when `manifest.json` exists
- building `generated/` from the selected folder's `source/*.md`
- reading `generated/index-tree.json`
- reading `generated/by-id/<doc_id>.json`
- rendering the tree and selected document in `/docs-review/`

## Route And Repo Shape

The existing Docs Viewer local server can serve the app. A second server process is not required.

Routes:

- `/docs/`: existing full manage-mode Docs Viewer
- `/docs-review/`: isolated review app
- `/docs-review/folders...`: local review-folder API endpoints

Proposed repo area:

```text
docs-viewer-review/
  shell/
    docs-review.html
  runtime/
    js/
      docs-review-app.js
      docs-review-client.js
      docs-review-renderer.js
      docs-review-state.js
  static/
    css/
      docs-review.css
```

The exact module names can change during implementation, but the ownership boundary should not: review-app frontend code belongs under `docs-viewer-review/`, not inside the existing `/docs/` manage runtime.

The app may import shared read-only Docs Viewer modules where that keeps behavior consistent and does not pull in manage-mode assumptions.

Allowed shared dependencies include:

- basic document rendering helpers
- tree payload normalization
- tree rendering primitives
- main document view rendering primitives
- asset URL helpers
- small shared CSS tokens/base styles

Do not import:

- `docs-viewer/runtime/js/management/docs-viewer-management.js`
- management toolbar/action modules
- source editor modules
- import modal modules
- publish/settings/rebuild normal-scope modules
- normal scope lifecycle modules
- normal `/docs/` route workflow when it assumes configured scopes

## Initial Folder Contract

Use a simple local fixture folder under:

```text
var/analytics/data-sharing/import-preview/manual-smoke/
```

Initial shape:

```text
var/analytics/data-sharing/import-preview/manual-smoke/
  manifest.json
  source/
    review-root.md
    review-child.md
  generated/
    index-tree.json
    by-id/
      review-root.json
      review-child.json
```

The review app does not need normal Docs Viewer discovery payloads:

- no search UI
- no recently-added UI

The source Markdown files should be Docs Viewer-compatible, but they are not canonical source docs.

Example source front matter:

```markdown
---
doc_id: review-root
title: Review Root
parent_id: ""
viewable: true
---
# Review Root

Temporary review body.
```

The first app version can load `manual-smoke` by default. Later versions can list available folders and choose one.

## Build Capability

The first version should include a Build button for the selected/default review folder.

Build means:

- read `var/analytics/data-sharing/import-preview/<folder-id>/source/*.md`
- build `generated/index-tree.json`
- build `generated/by-id/<doc_id>.json`
- refresh the review app view after successful build

The implementation should reuse the existing Docs Viewer payload builder as a library, not through the CLI or normal scope rebuild orchestration. A review-owned backend adapter can create a synthetic review config and call `DocsDataBuilder` directly:

```python
builder = DocsDataBuilder(
    repo_root=repo_root,
    config=review_config,
    source_dir=folder_path / "source",
    output_dir=folder_path / "generated",
    viewer_base_url="/docs-review/",
)
result = builder.run(write=True)
```

This keeps Markdown parsing, front matter handling, tree generation, HTML rendering, link rewriting, and by-id payload shape aligned with normal Docs Viewer generation without treating the review folder as a configured scope.

Build does not mean:

- update configured Docs Viewer scopes
- write canonical source
- publish public payloads
- rebuild normal `/docs/` generated outputs
- call `docs_write_rebuild.rebuild_scope_outputs`
- call the `build_docs.py` CLI
- add CLI support for review-folder builds
- call `build_search.py`
- require a search index
- require a recently-added payload
- run Data Sharing returned-package conversion
- create or delete source folders

The direct `DocsDataBuilder` call may still write unused normal-builder artifacts such as `generated/recently-added.json` or `generated/references/...`. Those are acceptable implementation byproducts. The review app should ignore them.

## Minimal UI

The first `/docs-review/` app should include:

- visible local-review label
- current review folder id/path
- Build button
- Back to Docs Viewer link pointing to `/docs/`
- folder list
- tree/index panel
- main document view
- simple loading/error status

The app should not include:

- scope selector
- manage toolbar
- source editor
- source open action
- canonical document delete
- metadata edit modal
- hierarchy drag/drop
- publish/settings/rebuild normal-scope actions
- public links
- search
- recently added
- Data Sharing import/review controls
- folder delete UI in the first slice

This keeps the first app intentionally boring and safe.

## Backend Boundary

The app can use the same local Docs Viewer server.

Server additions should remain thin:

- serve `/docs-review/` shell HTML
- serve `docs-viewer-review/runtime/...`
- serve `docs-viewer-review/static/...`
- expose review-folder API endpoints through the same local service origin/CORS rules

Business logic should stay in focused service modules:

- review-folder listing/build/read behavior belongs in `docs_review_folders.py` or a clearly named sibling
- normal Docs Viewer server should only route and serve static files
- normal Docs Viewer management service should only delegate where routing reuse is unavoidable

`docs_viewer_service.py` should not become the owner of review app behavior.

## Frontend Boundary

The `/docs-review/` frontend should be a separate app entrypoint.

It should own:

- app boot
- selected/default review folder
- calling review-folder endpoints
- rendering tree/document view
- Build button lifecycle
- Back to Docs Viewer navigation

It should not depend on normal manage-mode state:

- no `viewerScope`
- no configured scope context
- no normal management action controller
- no source config
- no source write capability
- no publish capability

If shared Docs Viewer renderer modules require too much configured-scope context, add a small adapter in `docs-viewer-review/` rather than modifying the shared module with review-specific conditionals.

## Payload Loading

The `/docs-review/` app should load review-folder payloads directly.

Initial endpoints can be:

- `GET /docs-review/folders`
- `GET /docs-review/folders/index-tree?folder_id=manual-smoke`
- `GET /docs-review/folders/payload?folder_id=manual-smoke&doc_id=review-root`
- `POST /docs-review/folders/build` with `{ "folder_id": "manual-smoke" }`

The frontend should not use normal generated-data runtime until a clean payload-provider abstraction exists.

## Implementation Tasks

### 1. Remove Normal Docs Viewer Review UI

- Remove tentative `/docs/` management review UI modules, toolbar buttons, modal wiring, controller imports, and related CSS.
- Remove or rewrite tests that assert normal `/docs/` management UI knows about review folders.
- Keep normal `/docs/` UI completely unaware of the review app capability.
- Do not add review mode, review URL state, review-folder document rendering, review buttons, or review-folder modals to the normal `/docs/` app.
- Remove or rename legacy backend paths/modules that expose review-folder behavior under normal `/docs/` route names.
- Update stale content-review docs that still describe opening review folders inside `/docs/`.

### 2. Add Manual Smoke Fixture

- Add or generate `var/analytics/data-sharing/import-preview/manual-smoke/manifest.json`.
- Add `source/review-root.md` and `source/review-child.md` with stable `doc_id`, `title`, `parent_id`, and `viewable` front matter.
- Keep the fixture local/temp-oriented; do not add it to Docs Viewer scope config.
- If fixture files are intentionally tracked, keep them tiny and deterministic. If they are generated by tests, document the fixture builder instead.

### 3. Implement Review-Folder Build

- Add a real build operation for a selected review folder.
- Validate the folder id before any filesystem access and reject paths outside `var/analytics/data-sharing/import-preview`.
- Require a `source/` directory with at least one Markdown document before build.
- Create a synthetic Docs builder config with:
  - source root set to the selected folder's `source/`
  - output root set to the selected folder's `generated/`
  - viewer base URL set to `/docs-review/`
  - no publish/search output dependency required by the app
- Call `DocsDataBuilder` directly as a library rather than invoking `build_docs.py`, `docs_write_rebuild`, or configured-scope rebuild orchestration.
- Return a structured build report with generated root, index-tree path, by-id count, warnings, and `summary_text`.

### 4. Serve The Local App Shell

- Add a `/docs-review/` route to the existing local Docs Viewer server.
- Serve `docs-viewer-review/shell/docs-review.html` for the route.
- Serve `docs-viewer-review/runtime/...` and `docs-viewer-review/static/...` as static local assets.
- Keep route dispatch thin; app behavior remains in frontend modules and review-folder service code.
- Add route tests proving `/docs-review/` serves the shell and `/docs/` behavior is unchanged.

### 5. Build Review Frontend Modules

- Create the `docs-viewer-review/` frontend area with client, state, renderer, and app-entry modules.
- Default to `manual-smoke` as the selected review folder.
- On boot, call the review-folder list endpoint, then load `manual-smoke` index tree when built.
- Render a local-review label, folder id/path, Build button, Back to Docs Viewer link, folder list, tree panel, document panel, and status/error text.
- Build action posts `{ "folder_id": "manual-smoke" }`, then reloads the index tree and selected/default document.
- Tree selection loads document payloads from `/docs-review/folders/payload`.
- Render `content_html` from the generated payload without source-edit, manage-action, publish, search, or normal-scope controls.

### 6. Keep Links And Assets Review-Local

- Treat generated review document links as local review links where practical.
- Internal links to documents in the same generated review tree should navigate within `/docs-review/`.
- Links to normal `/docs/` documents may remain normal links unless a future side-by-side comparison feature needs interception.
- Asset URLs should be loaded only from paths that the existing local server can safely serve.
- Missing linked docs or assets should show as ordinary document rendering issues, not as source-management failures.

### 7. Add Focused Verification

- Add Python tests for:
  - path-safe review-folder resolution
  - build endpoint writing `generated/index-tree.json`
  - build endpoint writing `generated/by-id/<doc_id>.json`
  - index-tree and payload read endpoints after build
  - missing, unbuilt, invalid-id, and deleted-folder error behavior
- Add route tests for `/docs-review/` shell/static serving.
- Add JS syntax checks for new review frontend modules.
- Add a small browser smoke only after the shell exists:
  - load `/docs-review/`
  - click Build
  - verify folder rows render
  - verify tree rows render
  - select `review-child`
  - verify document content renders
  - verify no manage toolbar/source actions are present

## Verification Target

The preparatory implementation is complete when:

- `/docs-review/` loads from the local server
- the page can list and select the `manual-smoke` review folder
- Build generates or regenerates the selected folder's `generated/` payloads
- the tree displays at least `review-root` and `review-child`
- selecting a tree item renders its document payload
- no normal manage-mode toolbar/action controls are present
- deleting or modifying canonical source is impossible from this app

Automated verification should focus on service and route contracts first:

- build endpoint writes expected generated files under `var/...`
- read endpoints return expected index/payload objects
- route shell is served by the local Docs Viewer server
- public `/docs/` runtime does not import `docs-viewer-review/`

Browser verification can be a small smoke only after the route shell exists.

## Future Extensions

After this isolated app shell works, it can grow toward the full content-review workflow:

- open selected folder from a returned-package review result
- show manifest metadata
- distinguish built and unbuilt folders
- add side-by-side current/live versus temporary content comparison

These extensions should not change the core decision: `/docs-review/` is a separate local review app, not a mode inside `/docs/`.
