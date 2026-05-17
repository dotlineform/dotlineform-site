---
doc_id: docs-viewer-management
title: Docs Viewer Management
added_date: 2026-04-22
last_updated: 2026-05-17
ui_status: done
parent_id: archive
sort_order: 54000
---
# Docs Viewer Management

Status:

- Phase 1 implemented: flat Studio source layout and management contract
- Phase 2 implemented: localhost write service plus manage-mode create/archive/delete
- Phase 3 implemented: leaf-doc drag/drop move with front-matter-only tree updates
- Phase 4 implemented: current-doc metadata edit modal for `title`, `summary`, `ui_status`, `parent_id`, and `sort_order`
- Phase 5 implemented: right-click contextual creation for `New Sibling` and `New Child`
- Phase 6 implemented: hidden-doc review and bulk-backed `Show`
- Phase 7 implemented: drag/drop into any node plus one-step client-side move Undo
- Phase 8 implemented: management mode is scoped to `/docs/`, and `/docs/` can manage `studio`, `library`, or `analysis` by changing the active docs scope
- Phase 9 implemented: Docs Import runs inside the Docs Viewer management modal from the shared importer module
- Phase 10 implemented: management UI orchestration lives in `assets/docs-viewer/js/docs-viewer-management.js`, loaded only for management-enabled viewer shells
- Phase 11 implemented: public builds render `/docs/` through the read-only shell; `bin/dev-studio` opts into the management shell with `docs_viewer_management_enabled: true`
- current follow-on work is optional rather than required for the local management surface

## Implementation Status

Implemented now:

- `_docs` flattened for Studio docs management
- dedicated localhost docs-management server added at `scripts/docs/docs_management_server.py`
- manage mode enabled only for `/docs/` behind `?mode=manage`
- the `/docs/` management shell is enabled only when the Jekyll config sets `docs_viewer_management_enabled: true`
- public builds leave `docs_viewer_management_enabled` false, so `?mode=manage` does not render management CSS, controls, modal markup, or localhost server configuration
- `/docs/` can change the active management scope with `?scope=studio`, `?scope=library`, or `?scope=analysis`
- public `/library/` and `/analysis/` viewer routes remain read-only and do not render management controls, configure the local docs-management server, or load management-only CSS
- public read-only viewer routes use the shared reader controller without loading the management controller module
- create, archive, delete-preview, and delete-apply implemented
- drag/drop move implemented for leaf docs only
- dropping on the upper half of any doc row moves the dragged doc inside that doc as its last child
- dropping on the lower half of a doc row moves the dragged doc after that doc and shows a visible insert line
- all nodes can gain children through drag/drop; there is no source or generated `folder` schema field
- the index toolbar exposes a one-step Undo action for the most recent successful move in the current viewer session
- source writes remain front-matter-only; files do not move on disk
- drag/drop moves assign a sparse `sort_order` to the moved doc only when there is room between neighboring siblings, and normalize the destination sibling set only when the numeric gap is exhausted or the target order is ambiguous
- sparse order spacing uses `1000` between normalized siblings
- the `Actions` menu exposes `Normalize order`, which opens a modal for current sibling group, selected-doc children, root sibling group, or whole-scope repair
- create-after-selected uses sparse `sort_order` increments without renumbering siblings
- create, reparent, archive, delete, and searchable metadata edits rebuild docs payloads plus same-scope docs search; same-parent drag/drop reorder rebuilds docs payloads without a search update
- docs-management writes `added_date` and `last_updated` values in `YYYY-MM-DD HH:MM` form for new or content-imported docs; metadata-only changes preserve existing `last_updated` values so the field reflects content freshness rather than tree/status/summary churn
- Library create/import defaults to `published: true`, `hidden: true`; Studio create/import defaults to `published: true`, `hidden: false`
- generated docs data keeps a compatibility `viewable` field computed as `!hidden`
- manage mode uses a checked-by-default `show hidden` checkbox so hidden docs remain visible for review
- selected hidden docs can be shown through the manage toolbar
- `Show` includes required hidden ancestors after confirmation and can optionally include descendants
- hidden/show changes are sent through a bulk endpoint so one action writes the affected source files and runs one docs/search rebuild
- docs-management backups are operation-scoped rather than full-scope snapshots
- `Copy Link` is available from a manage-mode right-click menu on doc rows and copies a Markdown link such as `[Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)`
- manage mode preserves itself at runtime when canonical internal `/docs/?scope=<scope>&doc=<doc_id>` links are clicked from `/docs/?mode=manage`; source Markdown links do not need to include `mode=manage`
- `Open Source` is available from a manage-mode right-click menu on doc rows
- right-click `Open Source` currently exposes:
  - `Open`
  - `Open In VS Code`
- right-click create actions now expose:
  - `New Sibling`
  - `New Child`
- `Edit` is available for the current doc in the manage toolbar
- `Rebuild docs`, `Normalize order`, `Import`, `New`, `Edit`, `Archive`, and `Delete` are grouped under the top-row `Actions` menu
- `Settings` is grouped under the top-row `Actions` menu and opens the active-scope settings modal
- the settings modal currently exposes scoped `show_updated_date` only, writes through the local source-config settings endpoint, and rebuilds the affected docs payloads after a changed save
- `Actions`, `Show`, and `show hidden` sit in the search/control row so hidden-doc review controls stay quick to reach
- the shared viewer status row appears above favourites and is reused for management progress, blocked/unavailable states, validation failures, write errors, and normal viewer/search status; routine success messages are cleared after the viewer reloads
- metadata edit opens in a modal and currently supports:
  - `title`
  - `summary`
  - `ui_status`
  - `hidden`
  - `parent_id`
  - `sort_order`
- blank `summary` removes the front matter field
- blank `ui_status` removes the front matter field
- the metadata status control is a listbox sized to show all available options without scrolling and labels the active choice as selected
- `ui_status` is descriptive UI metadata and does not change viewer visibility
- `draft` is a configured `ui_status` option rather than a special modal-only status
- `hidden` is edited independently through a metadata checkbox
- the metadata parent control is a Docs Viewer-owned searchable popup, not a native `datalist`; `Root` resolves to blank `parent_id`, parent choices display title-only labels, and selected suggestions resolve back to their source `doc_id`
- configured `ui_status` values are available from a compact tag-menu button beside the bookmark control
- the tag menu is hidden outside available manage mode
- in available manage mode, status menu choices write immediately through the metadata endpoint without changing `hidden`, and reload the docs payload
- title edits do not mutate `doc_id` or filename
- metadata edits validate parentage and reject self-parent or descendant-parent cycles
- when the metadata modal changes `parent_id` to a non-root parent and the user leaves `sort_order` unchanged, the doc appends as the last sibling under the new parent
- when the metadata modal changes `parent_id` to root, the visible `sort_order` field is respected rather than converted to append
- metadata edits rebuild docs payloads plus same-scope docs search, except `ui_status`-only edits skip search because status emoji are viewer-only metadata
- Docs Import is reachable from the `/docs/` management toolbar as an import modal seeded with the active scope
- `assets/docs-viewer/js/docs-html-import.js` exports the importer initializer used by the Docs Viewer modal
- Docs Import reads its scope list, target source roots, and media token path prefixes from the Docs Viewer scope config
- `assets/docs-viewer/js/docs-viewer-management.js` owns manage-mode toolbar rendering, status-pill events, metadata/import modal coordination, metadata payload collection, settings reads, busy/message/reload callbacks, and navigation
- `assets/docs-viewer/js/docs-viewer-management-interactions.js` owns manage-mode nav drag/drop event handling, transient drag/drop visual state, context-menu active-doc state, context-menu positioning, and context-menu action dispatch
- `assets/docs-viewer/js/docs-viewer-management-actions.js` owns create, metadata/status save, settings save, rebuild, archive/delete, viewability, move/undo, source-open, and copy-link write/action orchestration
- `assets/docs-viewer/js/docs-viewer-management-capabilities.js` owns management capability helpers and the capability probe/retry state machine
- `assets/docs-viewer/js/docs-viewer-management-config.js` owns management UI-text/config application
- `assets/docs-viewer/js/docs-viewer-management-render.js` owns management-only markup helpers for status pills, metadata parent/status controls, and settings warnings
- `assets/docs-viewer/js/docs-viewer.js` keeps the reader/search/history controller plus a small management bridge for shared state and lazy controller loading

Not implemented yet:

- dragging any doc with child docs
- incremental docs-search updates

## Suggested Follow-On Features

Current state:

- no further follow-on feature is currently committed
- the local management surface now covers the originally confirmed workflow:
  - `Open`
  - `Open In VS Code`
  - metadata edit for the current doc
  - `New Sibling`
  - `New Child`
  - hidden-doc review
  - `Show` with required-ancestor and optional-descendant handling
  - drag/drop move for leaf docs
  - one-step move Undo
  - archive and delete

Potential later areas, if promoted:

- dragging docs with child docs
- deeper undo/history beyond the most recent move
- true incremental docs-search updates for visibility-only changes
- a stronger modal/shareable shell for docs-viewer management actions if the surface grows
- more explicit structured impact previews for archive/delete if native confirm flows become a limiting factor

Recommended boundary:

- use the viewer to manage structure and metadata
- use a real editor to write document body content
- keep docs management desktop/local only rather than designing a mobile management surface

Declined for now:

- recent-ops or restore view backed by backup bundles
- additional drag/drop hints or manage-mode helper copy
- guided `archive` setup flow
- richer move/archive/delete preview UI
- `Reveal In Finder`
- inline markdown body editing
- rich text editing
- turning `/docs/` into a CMS
- automatic cross-doc link rewriting

Confirmed priority order:

1. no further confirmed follow-on item is currently queued

## Summary

This document scopes a possible management mode for the shared Docs Viewer.

The feature would allow a local user to manage docs directly from a viewer instance rather than editing source files by hand first.

This is not only a UI change. It potentially affects:

- the shared Docs Viewer UI
- the `_docs` source tree
- docs metadata conventions
- the docs builder assumptions
- the local write-service boundary

## Goal

Implement a local-only management mode for the Docs Viewer that can expose document-management actions from within the viewer.

Candidate actions:

- drag and drop of index items to change `sort_order` and `parent_id`
- `new`
- `archive`
- `delete`

Required guardrails:

- enforce unique filenames
- enforce unique `doc_id` values
- define whether titles must also be unique
- expose management commands only when an explicit query param enables management mode

Phase 1 should end with a stable operational contract for:

- how source docs are stored on disk
- how the shared viewer enters management mode
- which localhost write surface is allowed to mutate docs
- what `new`, `archive`, and `delete` mean
- which conditions block write operations

## Why This Needs A Real Spec

This request is bigger than a normal UI enhancement because it mixes:

- viewer interaction design
- source-of-truth file writes
- metadata validation
- file-system mutation rules
- archive/delete semantics

The toolbar itself is straightforward. The hard part is defining what these actions mean on disk and in the generated docs tree.

## Scope

Included:

- a management toolbar in the shared Docs Viewer shell
- a URL query switch that enables management mode
- local-server-only write behavior
- source metadata updates needed for supported management actions
- validation for filename and `doc_id` uniqueness
- tree operations that affect `parent_id` and `sort_order`

Excluded:

- remote multi-user editing
- GitHub Pages hosted write behavior
- server-side auth and permissions
- collaborative conflict resolution
- inline markdown body editing
- publish workflow beyond local doc metadata mutations

## Primary Surfaces

- `/docs/`
- `/docs/?scope=library`
- `/docs/?scope=analysis`
- shared Docs Viewer shell and runtime
- local docs-management service, if introduced

## Assumptions

- management mode is for local admin/developer use only
- the feature is unavailable on the static hosted site
- the feature does not need to be exposed in mobile environments
- the current shared Docs Viewer model should remain shared unless management mode forces a deeper fork
- source docs remain file-backed under `_docs`
- `library` and `analysis` remain part of the same shared runtime, but public `/library/` and `/analysis/` are read-only shells

## Core Questions To Answer

These historical questions are kept as decision prompts and provenance.
Current Phase 1 answers are captured in the contract above and in the decision log below.

### Source Of Truth

- What is the canonical source of a managed doc: the markdown file path, front matter, or both together?
- Should management mutate only front matter and tree placement metadata, or also move files on disk?

### File Creation

- When creating a new doc, how is the filename chosen?
- Is filename generation automatic from the title, from the `doc_id`, or user-specified?
- Which directory does a new doc go into by default?

### Tree Changes

- If a doc is reparented in the viewer, does only `parent_id` change, or should the file also move into a different folder?
- If `sort_order` changes by drag/drop, should the system renumber sibling items automatically or preserve sparse numbering?

### Archive

- What does `archive` mean?
- Move the file into `_docs/archive/`?
- Set `published: false`?
- Change `parent_id` to `archive`?
- Some combination of the above?

### Delete

- Is delete a real file deletion or a soft-delete workflow?
- If soft-delete, where does the doc go?
- If hard-delete, what protections are required?

### Uniqueness Rules

- Filenames should be unique: yes or no?
- `doc_id` values should be unique: yes or no?
- Titles should be unique: yes or no?

### Management Mode

- What is the query string key that enables management mode?
- Should management mode be visible only when the local write server is available?
- Should the mode fail closed when the server is unavailable?

## Recommended Initial Narrowing

This document started with a narrower first pass:

- show management toolbar behind a query param
- support `new`
- support `archive`
- support `delete`
- support metadata validation
- defer drag/drop reorder/reparent until command semantics are proven

That narrower sequence has now been completed and extended with a leaf-doc drag/drop move flow.

## Phase 1 Contract

Phase 1 is now defined as a planning-and-boundary phase, not a viewer-UI implementation phase.

The required output of Phase 1 is an implementation-ready contract for:

- flat source storage
- management-mode gating
- localhost write authority
- create/archive/delete semantics
- validation and backup rules

### Flat Source Storage

The Studio docs source root is now flat before viewer management writes source docs.

Target shape:

- Studio docs: `_docs/*.md`
- Library docs: `_docs_library/*.md`

Implications:

- source folders under `_docs/` stop carrying storage meaning
- visible docs hierarchy remains metadata-driven through `doc_id`, `parent_id`, and `sort_order`
- special viewer groupings such as Archive continue to exist as docs in the tree, not as filesystem folders
- `doc_id` remains stable even if title changes later

Implemented flattening work:

- moved Studio markdown docs from nested folders into the `_docs/` root
- preserving existing `doc_id` values
- preserving tree position through front matter, not file placement
- rewriting any relative markdown links that currently depend on nested source paths
- rebuilding docs output and checking for broken internal links after the move

Important builder note:

- the docs builder currently resolves relative `.md` links from each file's `source_path`, so flattening is not just a file move; it also changes how relative markdown links are interpreted

### Management Mode Gating

Management mode uses this query contract:

- `?mode=manage`

Management controls are shown only when both conditions are true:

- the current URL includes `mode=manage`
- the local docs-management server reports support for the current scope

If `mode=manage` is present but the local server is unavailable, the viewer must:

- stay read-only
- show a clear `server unavailable` message in the viewer-level control area
- avoid rendering controls that imply writes will succeed

Mobile note:

- docs management is not intended as a mobile-admin surface
- mobile environments are not expected to have the required local server
- right-click-driven management actions do not need mobile equivalents

### Local Write Boundary

First implementation should use a dedicated docs-management localhost service rather than extending the existing tag or catalogue services.

Recommended script and ownership:

- script: `scripts/docs/docs_management_server.py`
- purpose: local-only management writes for shared Docs Viewer source docs

Recommended endpoint surface:

- `GET /health`
- `GET /capabilities`
- `POST /docs/create`
- `POST /docs/archive`
- `POST /docs/delete-preview`
- `POST /docs/delete-apply`

Recommended capabilities shape:

```json
{
  "ok": true,
  "capabilities": {
    "docs_management": true,
    "scopes": ["studio", "library"]
  }
}
```

Write allowlist:

- Studio scope may write only `_docs/*.md`
- Library scope may write only `_docs_library/*.md`
- backups may write only under `var/docs/backups/`
- operational logs may write only under `var/docs/logs/`

Security and operational rules:

- bind to loopback only
- allow loopback origins only
- reject writes outside the allowlisted roots
- create a timestamped backup bundle before every non-dry-run write batch
- log one structured summary record per successful apply request

### Validation Rules

Validation rules for all write commands:

- filename stem must be unique within the scope root
- `doc_id` must be unique within the scope root
- title does not need to be unique
- `sort_order`, when present, must be an integer
- `parent_id`, when present, must resolve to an existing doc in the same scope
- docs with children cannot be deleted until their children are moved or deleted
- `archive` is an ordinary doc id; the Archive command uses it as the conventional destination parent

Title-change rule:

- editing a title later does not mutate `doc_id` or filename

### `new` Command

Recommended request shape:

```json
{
  "scope": "studio",
  "title": "New Doc",
  "parent_id": "",
  "sort_order": null
}
```

Behavior:

- default title is `New Doc`
- default `doc_id` is a slug-friendly version of title
- default filename stem matches `doc_id`
- if the generated stem already exists, append `-2`, `-3`, and so on until both filename and `doc_id` are unique
- default target root is `_docs/` for Studio or `_docs_library/` for Library
- default `parent_id` is blank unless the user creates from a specific parent context
- default position is last sibling under the chosen parent
- initial markdown body may be a minimal heading based on title

Recommended sort-order rule for append operations:

- prefer sparse ordering
- append new docs at the end of the sibling list using the next available integer slot
- when inserting after a visible doc, prefer a simple integer increment for the new doc only
- do not renumber sibling docs automatically in v1

### `archive` Command

Recommended request shape:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Behavior:

- `parent_id` becomes `archive`
- `sort_order` becomes the last sibling order under `archive`
- file does not move on disk
- `published` stays unchanged
- archiving a doc that is already under `archive` is a no-op success
- archiving `archive` itself is a no-op because the command cannot move the Archive parent into itself

### `delete-preview` And `delete-apply`

Recommended preview request shape:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Preview must report:

- whether the target exists
- child docs whose `parent_id` points at the target
- inbound markdown links from other docs when they can be detected
- file path that would be deleted
- whether apply would be blocked or allowed with warnings

Delete blockers:

- target doc does not exist
- one or more child docs still depend on the target as `parent_id`

Warnings but not blockers:

- inbound markdown links from other docs that will become broken

`delete-apply` behavior:

- requires explicit confirmation payload or matching preview token
- reruns validation before file deletion
- deletes the markdown file for the target doc
- writes backups before delete
- returns deleted path, warnings, and a summary record

## Write Model

Phase 1 decision:

- use a dedicated docs-management local server first

The current repo already keeps new localhost write surfaces separate while domain contracts settle.
That same approach is appropriate here because docs management introduces a different write target and a different validation model from Studio catalogue or tag writes.

Required write-model properties:

- local-only write endpoints
- explicit scope-to-root allowlist
- backup before every write batch
- deterministic front matter rewrite behavior
- apply endpoints that can be mirrored with dry-run validation

## Command Semantics

Initial command semantics were defined for `new`, `archive`, and `delete`.
The implemented management surface now also includes metadata edit, leaf-doc drag/drop move, draft viewability, and one-step move Undo.

### `new`

- minimum required field from UI: `scope`
- server may accept omitted title and create `New Doc`
- default parent is the flat scope root
- default parent is blank unless created from a parent context
- default `sort_order` appends as the last sibling
- default title and `doc_id` use the normalized `New Doc` stem rule

### `archive`

- file does not move
- `published` does not change automatically
- tree position changes through `parent_id = archive`
- archived Studio docs remain discoverable in the normal docs tree under the Archive doc
- archived Library docs remain generated; public visibility depends on each doc's own `hidden` value
- `archive` is an ordinary doc id and can be hidden from public views with `hidden: true`

### `delete`

- delete is a hard file delete
- preview is required before apply
- child-doc dependencies block delete
- inbound markdown references are previewed as warnings

### `move` / drag and drop

- only leaf docs are draggable
- dropping on the upper half of a row changes `parent_id` to that target doc and appends as the target's last child
- dropping on the lower half of a row keeps the target's parent, shows an insert line after the target row, and places the moved doc after the target
- any node can become a parent through drag/drop; there is no `folder` source field
- when there is room between neighboring `sort_order` values, only the moved doc is rewritten
- the destination sibling set is normalized to sparse unique orders, currently `1000`, `2000`, `3000`, and so on, only when the numeric gap is exhausted or target ordering is ambiguous
- one successful move is stored client-side for Undo in the current viewer session, including all docs whose placement changed

## Data And Builder Implications

Phase 1 answers:

- the docs builder does not need nested source folders for tree meaning, but it currently uses `source_path` for relative markdown-link resolution
- flattening `_docs` is a prerequisite for Studio management mode
- `_docs_library` is already flat and does not need the same migration
- special names such as `archive` remain meaningful as `doc_id` values, not as required source folders
- the `archive` `doc_id` remains a conventional Archive command target, but it is not protected or non-loadable by name

Implementation consequence:

- write-enabled viewer management can now rely on a flat Studio source root
- any future layout change still requires relative-link review because nested-path assumptions can affect markdown source links
- viewer visibility comes from generated doc fields such as `hidden`, not from hard-coded source-folder names

## Related Work

Possible related tasks:

- flatten the `_docs` folder
- add a dedicated docs-management local server
- later evaluate whether docs-management should join the broader localhost-server consolidation work

The broader localhost-server consolidation question is still a separate planning track.
Flattening is no longer optional work here: it is a prerequisite for Studio docs management.

## Non-Goals

- turning the Docs Viewer into a full CMS
- multi-user or remote editing
- browser editing on the hosted public site
- solving cross-doc reference migration automatically
- introducing server-backed user accounts

## Phased Implementation Plan

### Phase 1

- flatten `_docs` for Studio
- rewrite or verify source-relative markdown links affected by flattening
- define management-mode query param
- define write boundary and local-only availability
- define semantics for `new`, `archive`, and `delete`
- define uniqueness and validation rules
- keep title edits independent from `doc_id` and filename
- define the conventional Archive command target id, `archive`
- define the localhost API contract for create/archive/delete

### Phase 2

- add management toolbar UI
- add create/archive/delete command flow
- implement the local service and backups for every write batch
- add delete preview with inbound reference reporting

Status:

- implemented

### Phase 3

- evaluate drag/drop reorder and reparent
- evaluate whether folder moves should exist at all
- implement `POST /docs/move` for front-matter-only tree moves
- add manage-mode drag/drop for leaf docs in the shared docs index

Status:

- implemented as a leaf-doc-only move flow
- docs with children remain non-draggable by design

### Phase 7

- let any node receive children through drag/drop without adding a source schema field
- add a one-step client-side Undo action for the most recent successful move
- keep Undo in the index toolbar because it reverses tree state, not document content

Status:

- implemented

## Decision Log

What is the canonical source of a managed doc: the markdown file path, front matter, or both together?  
A: front matter

Should management mutate only front matter and tree placement metadata, or also move files on disk?  
A: only front matter. this is one reason for flattening _docs: having folders which can easily drift from the hierarchy displayed in the viewer will be more confusing than just having a flat list of files in _docs

When creating a new doc, how is the filename chosen?  
A: 'new doc'. 'new doc 2' if 'new doc' already exists, etc

Is filename generation automatic from the title, from the doc_id, or user-specified?  
A: doc_id is slug friendly version of title. doc_id is used as file name stem

Which directory does a new doc go into by default?  
A: _docs/

If a doc is reparented in the viewer, does only parent_id change, or should the file also move into a different folder?  
A: file doesn't move on disk (flat structure).

If sort_order changes by drag/drop, should the system renumber sibling items automatically or preserve sparse numbering?  
A: drag/drop preserves sparse numbering when possible by assigning only the moved doc a value between neighboring siblings. If the numeric gap is exhausted or the target order is ambiguous, the destination sibling set is normalized to `1000`, `2000`, `3000`, and so on. Undo restores every touched doc's prior placement in one client-side history step.

What does archive mean?  
A: parent_id becomes doc_id: archive. so it moves to the Archive folder in Doc Viewer, as the last sibling. file remains unmoved in _docs. published remains true, so that it is still visible unless `hidden: true` is set.

Is delete a real file deletion or a soft-delete workflow?  
A: real file deletion. warning prompt.

Filenames should be unique: yes or no?  
A: yes (flat structure)

doc_id values should be unique: yes or no?  
A: yes

Titles should be unique: yes or no?  
A: no. agree with your comment, it's not necessary. it's a valid thing to do if docs have different parents, but this doesn't need to be enforced by the system. It's up to the user to decide.

What is the query string key that enables management mode?  
A: ?...&mode=manage

Should management mode be visible only when the local write server is available?  
A: yes this is better than my initial idea of having visibility determined by scope.

Should the mode fail closed when the server is unavailable?  
A: yes if user manually calls url with query string and server is not available, then 'server unavailable' message is displayed.

Is a dedicated docs-management local server needed, or should this extend an existing local Studio/tag server?  
A: If we follow current approach of creating a dedicated server for each new major requirement, then yes a dedicated server is needed. We already have a future task documented to consider merging dedicated servers into one. A decision is needed about when that point is reached. I will defer to your advice.

What exact commands does the browser send?  
A: whatever you think is best

What validation happens before write?  
A: unqiue filename and doc_id. unless there are security related reasons to additionally validate content or file name.

What rollback/backup behavior is required before file mutations?  
A: no rollback. backup before every write batch.

whether references should be checked first before delete?  
A: yes, preview references first. broken links can still be user-resolved, but delete should surface what will break before confirmation.

whether drag/drop can change both parent_id and sort_order?  
A: yes. if a leaf doc is dropped on the upper/main part of any doc row, it becomes the last child of that target doc. if it is dropped on the lower edge of a row, it is placed after that target doc.

whether folder moves happen automatically?  
A: there is no source-level folder flag. any node can become a parent through drag/drop, but docs that already have children still cannot be dragged in the current implementation.

does the docs builder assume source folder placement has semantic meaning beyond the doc tree?  
A: not in a flat structure.

does flattening _docs become a prerequisite, or is it a separate cleanup project?  
A: it becomes a pre-requisite.

are there any sections that depend on special folder names such as archive, _draft, or _dev?  
A: yes, but only in terms of doc_id. I have already mentioned archive, that needs to exist for the Archive command. if system finds that it doesn't exist, it fails with error. In terms of file structure, archive, _draft etc will disappear in flat structure.

Should `archive` be treated as a protected system doc?  
A: no. `archive` is required only as the conventional Archive command target. It should be editable like a normal doc, and public/search visibility should be controlled with `hidden: true`.

If a title changes later, should that mutate `doc_id` and filename?  
A: no. title changes do not mutate `doc_id` or filename.
