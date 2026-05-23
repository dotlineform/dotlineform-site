---
doc_id: docs-viewer-management-current
title: Docs Viewer Management Current State
added_date: 2026-05-19
last_updated: 2026-05-23
parent_id: docs-viewer-management
sort_order: 54100
---
# Docs Viewer Management Current State

Status:

- Phase 1 implemented: flat Studio source layout and management contract
- Phase 2 implemented: localhost write service plus manage-mode create/archive/delete
- Phase 3 implemented: leaf-doc drag/drop move with front-matter-only tree updates
- Phase 4 implemented: current-doc metadata edit modal for `title`, `summary`, `ui_status`, `parent_id`, and `sort_order`
- Phase 5 implemented: right-click contextual creation for `New Sibling` and `New Child`
- Phase 6 implemented: hidden-doc review and bulk-backed `Show`
- Phase 7 implemented: drag/drop into any node
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
- source writes remain front-matter-only; files do not move on disk
- drag/drop moves assign a sparse `sort_order` to the moved doc only when there is room between neighboring siblings, and normalize the destination sibling set only when the numeric gap is exhausted or the target order is ambiguous
- sparse order spacing uses `1000` between normalized siblings
- the `Actions` menu exposes `Normalize order`, which opens a modal for current sibling group, selected-doc children, root sibling group, or whole-scope repair
- create-after-selected uses sparse `sort_order` increments without renumbering siblings
- create, reparent, archive, delete, and searchable metadata edits rebuild docs payloads plus same-scope docs search; same-parent drag/drop reorder rebuilds docs payloads without a search update
- docs-management writes `added_date` and `last_updated` values in `YYYY-MM-DD HH:MM` form for new or content-imported docs; metadata-only changes preserve existing `last_updated` values so the field reflects content freshness rather than tree/status/summary churn
- Library create/import defaults to `published: true`, `hidden: true`; Studio create/import defaults to `published: true`, `viewable: true`
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
- `Edit` is available for the current doc in the manage toolbar, and double-clicking the index opens the same metadata modal for the selected doc
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
- the metadata parent control is a Docs Viewer-owned searchable popup, not a native `datalist`; `Root` resolves to blank `parent_id`, parent choices display title-only labels, exact `doc_id` and title matches rank ahead of broad substring matches, and selected suggestions resolve back to their source `doc_id`
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
- `assets/docs-viewer/js/docs-viewer-management-interactions.js` owns manage-mode nav drag/drop event handling, double-click edit dispatch, transient drag/drop visual state, context-menu active-doc state, context-menu positioning, and context-menu action dispatch
- `assets/docs-viewer/js/docs-viewer-management-actions.js` owns create, metadata/status save, settings save, rebuild, archive/delete, viewability, move, source-open, and copy-link write/action orchestration
- `assets/docs-viewer/js/docs-viewer-management-capabilities.js` owns management capability helpers and the capability probe/retry state machine
- `assets/docs-viewer/js/docs-viewer-management-config.js` owns management UI-text/config application
- `assets/docs-viewer/js/docs-viewer-management-render.js` owns management-only markup helpers for status pills, metadata parent/status controls, and settings warnings
- `assets/docs-viewer/js/docs-viewer.js` keeps the reader/search/history controller plus a small management bridge for shared state and lazy controller loading
- `assets/docs-viewer/js/docs-viewer-document-controller.js` owns document pane visibility, payload rendering, loading/error states, and report mount handoff

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
  - archive and delete

Potential later areas, if promoted:

- dragging docs with child docs
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
