---
doc_id: docs-viewer-toolbar-model-tasks
title: Docs Viewer Toolbar Model Tasks
added_date: 2026-05-31
last_updated: 2026-05-31
parent_id: docs-viewer-toolbar-model
viewable: true
---
# Docs Viewer Toolbar Model Tasks

This is the tracker for implementing [Docs Viewer Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model).

## Status

### just done

- Documented the target Docs Viewer toolbar model: top bar, viewer toolbar, manage toolbar, document toolbar, and context panel toolbar.
- Implemented the top-bar and viewer-toolbar renderer split.
- Moved the index-view toggle and info/context panel toggle into the viewer toolbar.
- Retargeted panel-layout and info-panel controller refs so behavior ownership remains unchanged.
- Updated focused app-shell smoke coverage for the new toolbar surfaces.

### steer for next task

- Start with the top-bar and viewer-toolbar extraction because that is where the index-view and context/info panel controls should converge.
- Keep behavior stable: this work should move rendered controls and refs before changing panel semantics.
- Avoid a broad `infoPanel` to `contextPanel` rename in the first implementation slice.
- Preserve public read-only behavior: viewer toolbar controls may appear on public routes, but manage toolbar controls must remain route/access gated.

### baseline verification set

Use focused verification proportional to each slice:

- CSS-only or renderer-only source review for narrow markup/layout changes.
- Focused browser-module smoke where refs, event binding, dynamic imports, or route startup order changes.
- Docs Viewer smoke profile when moving controls between renderers or changing route/access-gated UI: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`.
- Public read-only scope checks for `/library/` and `/analysis/` when a control moves into a toolbar that also renders in public mode.
- Manage-mode checks for `/docs/?mode=manage` when management toolbar mounts, action menu refs, index-view toggle refs, theme toggle, or viewability controls move.

Codex sandbox note: browser and localhost checks need elevated permissions.

### general steer

- Keep the top bar as layout only; it should render toolbar mounts and not own control behavior.
- Keep the viewer toolbar read/layout/navigation oriented.
- Keep the manage toolbar management/write/admin oriented.
- Keep document toolbar controls scoped to the selected document.
- Keep context panel toolbar inside the context/info panel.
- Do not add compatibility aliases unless a single-slice migration cannot safely update all current refs.
- Update [Docs Viewer Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model), [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts), and [Docs Viewer View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract) when implementation changes their current-state descriptions.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Introduce a top-bar renderer that owns layout mounts for viewer and manage toolbar surfaces. Preserve existing header-control rendering and management action mounting behavior while establishing the named top-bar structure. |
| 2 | done | Introduce a viewer-toolbar renderer for scope selector, recently-added control, search input, index-view toggle, and context/info panel toggle. Move index-view toggle ownership out of management-actions markup and move info/context toggle rendering out of the document meta action cluster. |
| 3 | planned | Keep management write/admin controls in a manage-toolbar renderer. Rename or replace the current `docs-viewer-management-actions-renderer.js` surface only if the same slice updates all imports, refs, CSS selectors, and docs. |
| 4 | done | Create or clarify document-toolbar ownership for bookmark and document status controls. Keep document-specific controls in the document shell boundary, but do not return layout/context controls to that surface. |
| 5 | planned | Preserve context panel toolbar ownership inside `docs-viewer-info-panel-renderer.js` while updating docs to describe it as the context panel toolbar. Defer implementation renames from `infoPanel` to `contextPanel` unless a later slice has a clear benefit. |
| 6 | done | Update CSS so top-bar wrapping operates on toolbar groups first, then individual controls within each toolbar. Verify narrow layouts do not interleave viewer and manage controls incoherently. |
| 7 | done | Retarget runtime refs and controller handoffs to the new toolbar owner surfaces. Preserve panel-layout ownership of index state, info-panel controller ownership of open/close and active-view projection, and management controller ownership of management actions. |
| 8 | done | Update current-state docs and inventory notes after the implementation lands. Record moved renderer ownership, changed refs, verification results, and any deferred rename work. |

## Completion Criteria

- The rendered top bar has distinct viewer-toolbar and manage-toolbar surfaces.
- The index-view toggle and context/info panel toggle are viewer-toolbar controls.
- Manage/write/admin controls stay manage-toolbar controls and remain route/access gated.
- Bookmark and document status controls remain document-specific.
- The context panel toolbar remains inside the context/info panel.
- CSS can wrap toolbar groups without interleaving unrelated controls.
- Runtime controller ownership is unchanged except for receiving refs from clearer toolbar owners.
