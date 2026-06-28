---
doc_id: site-request-docs-review-local-app
title: Docs Review Local App
added_date: 2026-06-28
last_updated: 2026-06-28
parent_id: change-requests
viewable: true
---
# Docs Review Local App

## Status

Proposed.

## Problem

Docs Import content review sessions need a way to display temporary Docs Viewer-compatible documents generated under `var/analytics/data-sharing/import-preview/...`.

Loading those temporary docs into the existing `/docs/` manage-mode app is too risky. The manage app assumes a configured Docs Viewer scope, canonical source Markdown, scope config, source-editor capability, normal generated payload locations, public route links, and management actions such as source open/edit, delete, settings, rebuild, publish, drag/drop, and hierarchy mutation.

Review-session documents are different:

- they are temporary local artifacts
- they are not configured scopes
- they are not canonical source documents
- their generated payloads live under `var/...`
- their source folders may be deleted manually
- most manage-mode actions are irrelevant or unsafe

Retrofitting review-session behavior into `/docs/` would require a compensating access/context layer over an already incomplete config and capability model. That would create another layer of `if review session then ...` unless the existing Docs Viewer runtime was first redesigned around complete host-context and capability projections.

The first implementation should avoid that coupling.

## Decision

Create a distinct local review app:

- route: `/docs-review/`
- frontend/repo area: `docs-viewer-review/`
- same local Docs Viewer server process
- separate frontend entrypoint and route-specific modules
- minimal read-only Docs Viewer experience for temporary review documents

The review app is not a new Docs Viewer scope system. It is a local app for viewing temporary folder-backed review documents.

Sessions are one feature this app can support later. They do not define the app. The app should first prove that an isolated Docs Viewer-like reader can load from a `var/...` review folder, build generated JSON from its source folder, and display a simple document tree plus selected document view.

## Relationship To Content Review Sessions

This request is a sibling preparatory slice for [Docs Import Content Review Sessions](/docs/?scope=studio&doc=site-request-docs-import-content-review-sessions).

The content-review sessions request owns the Data Sharing workflow:

- returned package parsing
- Markdown content-format requirement
- temporary source folder generation from staged returned files
- session manifests
- session list/delete/build workflow
- review-session lifecycle

This request owns the isolated local review app shell:

- `/docs-review/` route
- `docs-viewer-review/` frontend code
- minimal read-only tree/document renderer
- loading from a `var/...` review folder
- build button for the selected/default folder
- route-specific backend/static serving where needed

The first version of `/docs-review/` can use one fixed or default review folder. It does not need full session handling.

## Route And Repo Shape

The existing Docs Viewer local server can serve the app. A second server process is not required.

Routes:

- `/docs/`: existing full manage-mode Docs Viewer
- `/docs-review/`: isolated review app
- `/docs/review-sessions/...`: management-only review-folder API endpoints already owned by `docs_review_sessions.py`

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

The app may import shared read-only Docs Viewer modules from `site/docs-viewer/runtime/js/shared/` where that keeps behavior consistent and does not pull in manage-mode assumptions.

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

The generated payloads should be close enough to normal Docs Viewer generated payloads for the shared document renderer to display them.

The first app version can load `manual-smoke` by default. Later versions can list available folders and choose one.

## Build Capability

The first version should include a Build button for the selected/default review folder.

Build means:

- read `var/analytics/data-sharing/import-preview/<folder>/source/*.md`
- build `generated/index-tree.json`
- build `generated/by-id/<doc_id>.json`
- refresh the review app view after successful build

Build does not mean:

- update configured Docs Viewer scopes
- write canonical source
- publish public payloads
- rebuild normal `/docs/` generated outputs
- run Data Sharing returned-package conversion
- create or delete sessions

The backend build implementation should live behind the review-session/review-folder backend owner, not in the frontend app.

The current `docs_review_sessions.py` skeleton already has an explicit build placeholder. This request can replace that placeholder for the fixed/default folder use case, while still preserving the same module ownership.

## Minimal UI

The first `/docs-review/` app should include:

- visible local-review label
- current review folder id/path
- Build button
- Back to Docs Viewer link pointing to `/docs/`
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
- Data Sharing import/review controls
- session delete/list UI

This keeps the first app intentionally boring and safe.

## Backend Boundary

The app can use the same local Docs Viewer server.

Server additions should remain thin:

- serve `/docs-review/` shell HTML
- serve `docs-viewer-review/runtime/...`
- serve `docs-viewer-review/static/...`
- expose management-only review-folder API endpoints through existing local service origin/CORS rules

Business logic should stay in focused service modules:

- review-folder listing/build/read/delete stays in `docs_review_sessions.py` or a clearly named sibling if the app needs a lower-level build helper
- normal Docs Viewer server should only route and serve static files
- normal Docs Viewer management service should only delegate

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

- `GET /docs/review-sessions/index-tree?session_id=manual-smoke`
- `GET /docs/review-sessions/payload?session_id=manual-smoke&doc_id=review-root`
- `POST /docs/review-sessions/build` with `{ "session_id": "manual-smoke" }`

Although these endpoint names currently say `review-sessions`, the first app can treat `manual-smoke` as a review folder. The terminology can be refined later if needed, but the backend owner remains temp review folders under `var/...`.

The frontend should not use normal generated-data runtime until a clean payload-provider abstraction exists.

## Verification Target

The preparatory implementation is complete when:

- `/docs-review/` loads from the local server
- the page can load the `manual-smoke` review folder
- Build generates or regenerates the folder's `generated/` payloads
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

- list review folders under `var/analytics/data-sharing/import-preview`
- open selected folder
- delete selected folder
- show manifest metadata
- distinguish built and unbuilt folders
- integrate Data Sharing returned-package session creation
- support `review_session=<session_id>` URL state
- add side-by-side current/live versus temporary content comparison

These extensions should not change the core decision: `/docs-review/` is a separate local review app, not a mode inside `/docs/`.
