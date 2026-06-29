---
doc_id: site-request-docs-import-content-review-sessions
title: Docs Import Content Review Sessions
added_date: 2026-06-28
last_updated: 2026-06-29
parent_id: change-requests
viewable: true
---
# Docs Import Content Review Sessions

## Status

Proposed.

## Problem

Returned `document-content` packages can contain expanded or rewritten text for many Docs Viewer documents. The current live source model cannot safely treat those returned rows as replacement docs by creating new revision doc ids such as `example-r2`.

Changing `doc_id` breaks existing parent-child relationships, links, references, and any other stable identity assumptions. If a parent document moved to a new revision id, its children and inbound links would also need coordinated changes. That turns a content review workflow into a source graph migration.

The returned content also needs enough structure for review. Plain text remains useful for summary-generation workflows, but it is not a good basis for full content rewrite/review sessions because the missing structure can make returned full content ambiguous.

Markdown export for `document-content` is therefore a prerequisite. That prerequisite is tracked separately in [Docs Document Content Markdown Export](/docs/?scope=studio&doc=site-request-docs-document-content-markdown-export).

## Decision

Implement returned content review as temporary review sessions, not as live scope writes or permanent revision docs.

A review session is a complete staged returned file. It is not a selected-row subset. If `content.jsonl` is staged, one generated review session represents the whole valid contents of `content.jsonl`.

The session should be disposable:

- generated under `var/analytics/data-sharing/import-preview/...`
- safe to delete casually
- safe to regenerate from the staged file
- excluded from live Docs Viewer scope config
- excluded from public generated payloads
- excluded from canonical source lifecycle rules

The workflow is content review, not document import:

1. A user stages a returned `document-content` file.
2. Data Sharing creates or regenerates temporary review source Markdown for the complete file.
3. Docs Viewer creates a session from the selected review source folder.
4. Docs Viewer builds the session JSON, index, and generated payloads.
5. Docs Viewer opens the session in an explicit import-review mode.
6. The user reviews generated temporary docs.
7. The user manually copies useful text into canonical source Markdown.
8. The user deletes or regenerates the review session as needed.

No live source docs are created, overwritten, or deleted by this action.

## Content Format

Content-review sessions consume package-level content format metadata; they do not own Markdown export.

The Markdown export prerequisite should provide:

- `content_format: "markdown"` at package level
- `source_markdown` on each returned record
- no mixed formats within one package

Full content-review sessions require `content_format: "markdown"`.

If a staged `document-content` file declares `content_format: "plain_text"`, the UI should either block content-review session creation or label it as lower-fidelity text review rather than document-content review.

See [Docs Document Content Markdown Export](/docs/?scope=studio&doc=site-request-docs-document-content-markdown-export) for the export/package shape and implementation tasks.

## Temporary Review Sessions

Review sessions should not be first-class Docs Viewer scopes.

They should be management-only review data sources with Docs Viewer-compatible generated payloads. A session manifest should describe:

- `session_id`
- `data_domain`
- `source_scope`
- `profile_id`
- `source_export_id`
- `staged_filename`
- `content_format`
- `created_at`
- record count
- skipped/error records
- generated payload root
- delete-safe status

The session id can be derived from staged-file identity and export metadata, but regeneration should be explicit. If a session already exists for the staged file, the UI should make replacement clear rather than mutating data silently underneath an open review.

Invalid records should be reported in the manifest or session report. They should not be silently omitted.

## Temporary Source Contract

Data Sharing owns conversion from the returned staged file into temporary review source Markdown.

The source folder should live under the session output, for example:

`var/analytics/data-sharing/import-preview/<session_id>/source/`

Each valid returned row should produce one Markdown file in that folder. The file is Docs Viewer-compatible source, but it is not canonical source.

The file shape is:

- system-generated front matter
- mapped front matter copied from the staged row
- body copied verbatim from the staged row content field

The body must be a straight copy from the staged JSON field. Do not normalize, convert, wrap, enrich, linkify, or otherwise process the returned content. If the selected content field is `content`, the body is exactly that `content` value.

For full content-review sessions, the selected content field should be the Markdown content field produced by the `document-content` Markdown export prerequisite. The session builder copies the staged field verbatim; conversion belongs to prepare/export, not session creation.

Front matter should be mapping-driven rather than hard-coded. Generated/system fields are owned by the session builder. Mapped fields come from the staged row when present.

System fields include:

- `doc_id`
- `title` fallback when the row title is missing
- `added_date`
- `last_updated`
- review/session metadata fields

Mapped front matter fields can include:

- `title`
- `parent_id`
- `summary`
- `viewable`
- future exported front matter fields that are explicitly allowed by the profile/session mapping

Do not copy arbitrary staged row keys into front matter. Relationship/context fields such as `children`, `ancestors`, `parent_title`, `current_summary`, and operational metadata should remain review metadata, not source front matter, unless a future profile explicitly makes them canonical front matter fields.

The content mapping should be declared by the profile or session builder, for example:

```json
{
  "content_field": "source_markdown",
  "content_format": "markdown",
  "front_matter_fields": ["title", "parent_id", "summary", "viewable"]
}
```

Docs Viewer owns turning a selected temporary source folder into a review session. It builds the generated JSON and index from that source folder, serves the generated payloads through management-only session endpoints, and displays the resulting docs in review mode.

## Backend Boundary

Review session files live under `var/analytics/data-sharing/import-preview/...`.

They must not be added to:

- `docs-viewer/config/scopes/docs_scopes.json`
- public scope lists
- regular generated scope outputs
- canonical source roots

Session folders are temporary artifacts. The folder tree under `var/analytics/data-sharing/import-preview/...` is the source of truth for what sessions exist. There should be no config registration, durable session registry, or source-control lifecycle for these sessions.

Manual deletion is valid. If a user deletes a session folder outside the UI, the system should not complain. The next list operation should simply omit that session, and an already-open stale session can report that the session no longer exists.

Backend support should be management-only. Possible endpoints:

- list content review sessions
- create or regenerate a session for a staged file
- read session manifest
- serve session `index-tree.json`
- serve session `by-id/<doc_id>.json`
- delete a session

The session builder can reuse Docs Viewer source/generation concepts where practical, but the output remains temporary review output rather than a configured scope.

## Frontend Boundary

The normal scope selector should not list review sessions.

Review sessions should be opened from the data-sharing/import workflow. The viewer should make the mode visible with a label such as:

`Import review - library - document-content - markdown`

Review mode should be read-only:

- no source write action
- no source delete action
- no public links
- no assumption that links, references, or the full tree are complete
- no implication that the temporary docs are canonical source docs

The route should be distinct from normal scope navigation, for example:

`/docs/?review_session=<session_id>&doc=<doc_id>`

Avoid URLs that imply the review session is a normal scope, such as `scope=library-review`.

Initial Docs Viewer UI shape:

- add a manage-toolbar sessions icon toggle button
- clicking the sessions toggle opens a modal listing current session folders under `var/analytics/data-sharing/import-preview/...`
- each listed session should indicate whether it has already been built
- selecting a built session loads its generated docs in Docs Viewer review mode
- selecting an unbuilt session enables a Build action
- a Delete action deletes the complete session folder
- clicking the sessions toggle again exits review-session mode and returns to the selected normal scope

The modal should treat sessions as folders/artifacts, not as scope records. Build and delete actions operate on the session folder, and loading a session should not mutate the active configured scope.

Delete in Docs Viewer is acceptable because it is temp-artifact cleanup, not a canonical source mutation. The delete action should be guarded by path validation under the import-preview root and should delete the complete selected session folder. It must not touch canonical source Markdown, configured scopes, public generated payloads, or any folder outside the session root.

## Gating

Because a staged returned file can contain many documents, session creation should be explicit. However, a session should include the complete staged file rather than selected rows.

The first implementation should:

- require a user action to create or regenerate the session
- show the staged filename, source export id, source scope, content format, record count, and warnings before opening
- require `content_format: "markdown"` for full content-review sessions
- block or report rows with missing `doc_id`, missing `title`, or missing content
- warn when content was truncated during prepare
- keep all canonical source writes out of this workflow

Filtering, searching, and reviewing smaller groups should happen inside the review UI, not by creating partial sessions.

## Future Extension

Markdown return content is tracked as a prerequisite in [Docs Document Content Markdown Export](/docs/?scope=studio&doc=site-request-docs-document-content-markdown-export) and should be implemented before this session workflow.

If Markdown return content later proves reliable enough for source replacement, that should be a separate apply action with stronger review and diff tooling. It should not reuse the plain-text content review action as an implicit live-source overwrite.

Potential future capabilities:

- side-by-side live/current versus returned content comparison
- content-format-aware diffing
- controlled apply of Markdown source updates
- session cleanup tooling

## Implementation Architecture

The implementation should prefer a narrow, disposable review session over a broad live-scope integration. Review sessions must be added as their own management-only feature, not as branches inside normal scope config, normal generated data reads, or canonical source management.

### Backend Modules

Add a dedicated backend owner:

- `docs-viewer/services/docs_review_sessions.py`

This module should own all review-session filesystem and payload behavior:

- resolve the import-preview root: `var/analytics/data-sharing/import-preview`
- list immediate child session folders
- read a session manifest when present
- report built/unbuilt status for each folder
- validate that a requested `session_id` resolves under the import-preview root
- build or rebuild a session from its source folder
- read session `index-tree.json`
- read session `by-id/<doc_id>.json`
- delete one complete session folder
- produce structured JSON responses for list/build/read/delete operations

It should not:

- read or mutate `docs-viewer/config/scopes/docs_scopes.json`
- add review sessions to scope config
- write canonical source Markdown
- publish public payloads
- treat missing manually deleted folders as corruption
- import browser/UI concerns

Path safety should be explicit. A valid session id should be a folder name, not an arbitrary path. Reject empty ids, path separators, `..`, absolute paths, symlinks that escape the import-preview root, and delete/build/read targets outside the root.

### Backend Routes

Keep route additions thin.

Add path constants in `docs-viewer/services/docs_management_routes.py`, for example:

- `REVIEW_SESSIONS_PATH = "/docs/review-sessions"`
- `REVIEW_SESSION_BUILD_PATH = "/docs/review-sessions/build"`
- `REVIEW_SESSION_DELETE_PATH = "/docs/review-sessions/delete"`
- `REVIEW_SESSION_INDEX_TREE_PATH = "/docs/review-sessions/index-tree"`
- `REVIEW_SESSION_PAYLOAD_PATH = "/docs/review-sessions/payload"`

Add those paths to the appropriate `GET_PATHS` and `POST_PATHS`.

`docs-viewer/services/docs_management_service.py` should only dispatch to `docs_review_sessions.py`. It should not grow session business logic. The server layer in `docs-viewer/services/docs_viewer_service.py` should not need special session handling beyond its existing route dispatch and management/generation gates.

The route split should be:

- `GET /docs/review-sessions`: list session folders and built status
- `POST /docs/review-sessions/build`: build or rebuild one selected session folder
- `POST /docs/review-sessions/delete`: delete one selected session folder
- `GET /docs/review-sessions/index-tree?session_id=...`: return built session tree
- `GET /docs/review-sessions/payload?session_id=...&doc_id=...`: return one built session document payload

Build and delete should require management mode. Session generated reads should also stay management-only; they are local review artifacts, not public generated data.

### Session Build Contract

The session builder should consume a session folder that already contains temporary source Markdown, for example:

```text
var/analytics/data-sharing/import-preview/<session_id>/
  manifest.json
  source/
    example.md
    child.md
  generated/
    index-tree.json
    by-id/
      example.json
      child.json
```

Data Sharing owns creating the `source/` files from the staged returned package. Docs Viewer owns building `generated/` from that selected temporary source folder.

The build path should reuse Docs Viewer source/generation concepts where practical, but it must not require the folder to be registered as a configured scope. If existing builders are too tightly tied to `DocsScopeConfig`, add a small review-session build adapter rather than broadening normal scope config.

The generated payload shape should match the normal Docs Viewer payloads closely enough that the document renderer can display them. Any additional review-only metadata should be in the session manifest or a clearly namespaced payload field, not mixed into canonical source assumptions.

### Frontend Modules

Add dedicated frontend modules rather than expanding existing management files:

- `docs-viewer/runtime/js/management/docs-viewer-review-sessions-client.js`
- `docs-viewer/runtime/js/management/docs-viewer-review-sessions-modal.js`
- `docs-viewer/runtime/js/management/docs-viewer-review-sessions-controller.js`

Responsibilities:

- `docs-viewer-review-sessions-client.js`
  - calls the review-session management endpoints
  - contains request/response normalization for list/build/delete/read
  - does not know about modal DOM

- `docs-viewer-review-sessions-modal.js`
  - renders the sessions modal UI
  - lists session folders
  - shows built/unbuilt status
  - exposes Build, Delete, Open, Cancel interactions
  - does not know how to load a document payload into the viewer

- `docs-viewer-review-sessions-controller.js`
  - wires the sessions toolbar button, modal, client, and viewer callbacks
  - owns review-session mode state
  - asks the viewer runtime to load the selected built session
  - exits review-session mode back to the previous configured scope

Existing files should only receive narrow integration points:

- `docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js`
  - add the sessions icon/toggle button markup

- `docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js`
  - either add only a neutral mount point for session modal content, or delegate modal markup to the new modal module
  - do not add a large hard-coded sessions modal block here

- `docs-viewer/runtime/js/management/docs-viewer-management.js`
  - initialize the sessions controller
  - pass callbacks for loading/exiting review-session mode
  - do not put session listing/build/delete logic here

If the existing management shell makes adding a new modal require large markup inside `docs-viewer-management-shell-renderer.js`, split a generic management modal mount first. Review sessions should not make that renderer substantially heavier.

### Runtime State

Review sessions need their own runtime state. Do not overload normal scope state.

Use a distinct state shape such as:

```js
{
  mode: "review_session",
  sessionId: "ds_20260628T120000Z-document-content",
  previousScope: "library",
  previousDocId: "library",
  contentFormat: "markdown"
}
```

Normal scope state should continue to mean configured Docs Viewer scope state:

- `viewerScope`
- scope selector value
- configured `indexTreeUrl`
- configured `searchIndexUrl`
- configured `recentlyAddedUrl`
- public route base
- source management capabilities

Review-session mode should not:

- add the session to the scope selector
- set `viewerScope` to the session id
- use fake scope ids such as `library-review`
- mutate route config
- mutate docs scope config
- imply the temporary docs are canonical

The route can use:

```text
/docs/?review_session=<session_id>&doc=<doc_id>
```

The normal scope URL should remain available when exiting review mode. Toggling the sessions button while a session is active should exit review-session mode and restore the selected configured scope.

### Payload Loading

Normal generated-data loading currently reads configured scope payloads. Session payload loading should use a separate payload source.

Preferred implementation:

- introduce a small payload-provider abstraction in the viewer runtime
- normal provider reads normal generated scope payloads
- review-session provider reads `/docs/review-sessions/index-tree` and `/docs/review-sessions/payload`

This keeps review-session logic out of `docs-viewer-generated-data-runtime.js` and avoids conditionals throughout document loading.

If a payload-provider abstraction is too large for the first slice, keep the session loading branch in the sessions controller and pass loaded tree/payloads to the viewer through a narrow callback. Do not spread `if (reviewSession)` checks through the document controller, router, search controller, sidebar, and generated-data runtime.

Search and recently-added can be omitted initially. The first version only needs:

- session index tree
- session document payload by id
- sidebar tree display
- selected document rendering

### UI Behavior

The sessions toolbar button is a manage-mode control. It should not appear on public routes.

Expected behavior:

- click Sessions while in normal scope mode: open the sessions modal
- select a built session and Open: load that session in review mode
- select an unbuilt session: enable Build
- click Build: build/rebuild that session folder and refresh list state
- click Delete: confirm, delete complete session folder, refresh list state
- click Sessions while in review-session mode: exit review mode and return to the selected normal scope
- if the current session was manually deleted: show a clear stale-session message and offer to return to normal scope

Review mode should visually communicate that it is temporary:

- show a label such as `Import review - library - document-content - markdown`
- suppress source write/delete actions
- suppress public links
- suppress source config settings
- keep ordinary read/navigation controls available where they still make sense

### Completed Enabling Work

The following enabling work has been completed so implementation has clear owners and does not start by expanding existing large files.

Backend review-session service skeleton:

- `docs_review_sessions.py` owns path-safe review-session temp-folder behavior.
- It lists session folders under `var/analytics/data-sharing/import-preview`.
- It reads built session `index-tree.json`.
- It reads built session `by-id/<doc_id>.json` payloads.
- It deletes complete session folders as temp-artifact cleanup.
- It rejects unsafe session ids, path traversal, absolute paths, and symlink session folders.
- Its build endpoint is wired as an explicit `build_status: "not_implemented"` placeholder so later build behavior has an owner but no fake implementation.
- Focused tests cover list, read, delete, route registration, management-only GET gating, unsafe ids, and symlink rejection.

Thin backend route wiring:

- `docs_management_routes.py` owns review-session route constants.
- `docs_management_read_service.py` delegates review-session GET routes to `docs_review_sessions.py`.
- `docs_management_service.py` delegates review-session build/delete POST routes to `docs_review_sessions.py`.
- `docs_viewer_service.py` gates review-session GET routes as management-only while keeping business logic out of the server layer.

Frontend review-session module skeleton:

- `docs-viewer-review-sessions-client.js` owns endpoint paths and request helpers.
- `docs-viewer-review-sessions-modal.js` owns modal rendering, session list display, built/unbuilt action state, and Open/Build/Delete/Cancel interactions.
- `docs-viewer-review-sessions-controller.js` owns client/modal orchestration and exposes `open`, `close`, `refresh`, `buildSession`, and `deleteSession`.
- These modules are not yet wired into the live management runtime, so unfinished review-session UI is not visible.
- Static tests assert that the client/modal/controller modules exist and that review-session behavior has not been folded into `docs-viewer-management.js`.

Management shell modal mount:

- `docs-viewer-management-shell-renderer.js` now exposes a neutral `docsViewerManagementModalMount`.
- New management modals can render from their own modules into that mount.
- This prevents review sessions from adding another large hard-coded modal block to the shell renderer.
- A fuller modal registry can still be added if sessions need shared modal lifecycle behavior.

Payload-provider assessment:

- Normal document loading currently flows through configured generated-data reads.
- Review-session loading should still use a separate payload source.
- The smallest future implementation path is to add a payload-provider abstraction at the viewer runtime/document-loading boundary.
- The normal provider should read configured scope payloads.
- The review-session provider should read `/docs/review-sessions/index-tree` and `/docs/review-sessions/payload`.
- This avoids spreading `if (reviewSession)` checks through generated-data runtime, document controller, router, sidebar, and search modules.
- Search and recently-added remain out of scope for the first session implementation.

Ownership documentation:

- `docs-viewer/source/studio/development-checklist.md` records `docs_review_sessions.py` as the review-session temp-folder owner.
- The checklist records that review sessions are folder artifacts, not Docs Viewer scopes.
- The checklist records that frontend review-session behavior should live in dedicated management modules, not normal generated-data runtime, normal scope selector code, public route runtime, or `docs_viewer_service.py`.

HTML-to-Markdown enabling refactor:

- `docs-viewer/services/docs_html_markdown.py` now owns reusable HTML/SVG parsing, sanitization helpers, and `html_to_markdown(...)`.
- `docs_import_html_parser.py` is now import-preview-specific and builds HTML summaries from the shared converter.
- `docs_import_preview.py` and `docs_import_media.py` use the shared conversion boundary where they need HTML-derived Markdown.
- Data Sharing Markdown export should call `docs_html_markdown.html_to_markdown(...)` rather than duplicating HTML-to-Markdown logic or depending on import-preview summaries; that implementation is owned by [Docs Document Content Markdown Export](/docs/?scope=studio&doc=site-request-docs-document-content-markdown-export).
