---
draft: false
doc_id: d-20261002-135221-f16b64
title: Source Editor Toolbar
added_date: "2026-10-02 13:52:21"
last_updated: "2026-10-10 16:57:25"
parent_id: d-20260428-000000-f5ff18
ui_status: done
summary: Align Source controls at the document's left edge and consolidate insertion actions and VS Code in Directives.
---
# Source Editor Toolbar

## Requirements

Place Return to doc, Save Markdown source and Directives on one row beginning at the document's left edge. Move all other Source toolbar actions into Directives: Add image, Add Catalogue image, Add file, Add Media View link and Insert doc link. Assign Subject also lives in Directives and updates the unsaved front matter; Open Subject folder follows it and opens the buffer's valid Folder subject in Finder, remaining disabled for Work or None. [Assign Subject In Source Editor](deliveries/Assign_Subject_In_Source_Editor.md) records their 2026-10-10 move from Edit and ordinary Source ownership. Open in VS Code uses the mounted editor's immutable document target. The existing Table detail, Insert related links, Insert icon and Summary actions remain together below a separator in the same flat menu. Keep existing icons and workflows; unavailable items remain disabled.

Return, Save, insertion and modal semantics remain with their existing owners. Opening the menu must preserve the selected source range; a menu item must never insert into a replaced editor or use edited front matter to choose a different Source file. This delivery does not combine modals, add token types or change persistence/publication policies.

## Deliverables And Process

Source registers three main-view controls in the required order. Local management CSS aligns the group to the shared document boundary and opens Directives to the right. The focused menu captures the adapter and selection before moving focus, closes before dispatch and invokes existing modal/workflow owners. Image/file insertion uses the Source adapter's staged-media operation with captured range/revision. VS Code reuses the existing source-opening workflow with immediate busy projection. Standalone insertion definitions/renderers, the two exclusive Catalogue toolbar wrappers and image/file event dispatch are retired without aliases.

[Source Editor Scripts](Source_Editor_Scripts.md) owns current Source and menu behavior. [Toolbar Model](Toolbar_Model.md), [Toolbar Icon Mapping](Toolbar_Icon_Mapping.md), [Runtime Module Ownership](Runtime_Module_Ownership.md) and [Panel Hosts and Control Surfaces](Panel_Hosts_And_Control_Surfaces.md) own lasting placement, artwork and composition. All executable changes are management-only; the public code projection and manifest are unchanged.

## Delivery Steps

- [x] Readiness: user approved the specified menu and row layout; inspected the existing controls, dispatcher, Source adapter, modal captures and media insertion owner. No separately approved test work is included.
- [x] Implementation: three-control row, flat menu, captured selections, VS Code, retired standalone paths and durable documentation completed.
- [x] Static evidence: lint passed for the nine changed local JavaScript modules, whitespace passed and runtime/test reference inspection found no retired imports, standalone handlers, image/file events or uncaptured replacement calls. These read-only checks addressed syntax, dead imports and incomplete retirement and took seconds; they do not prove visual fit or real mutation workflows. No tests, temporary regression scripts or browser automation were included.
- [x] Code review: reviewed the bounded final diff after static evidence for target/capture ownership, Source readiness and busy state, menu lifecycle, row/menu placement and obsolete paths. Findings were resolved within this delivery; no unresolved code findings or compatibility aliases remain.
- [x] Closeout: accepted static evidence and review results recorded below. Visual, keyboard, token-editing and live Save/media/VS Code behavior remain manual review. No Docs/Search rebuild, Publish, commit or push ran.

Evidence: `bin/lint-js` passed for `docs-viewer-manage.js`, `docs-viewer-management-hosted-views.js`, `docs-viewer-management-control-renderers.js`, `docs-viewer-management.js`, `docs-viewer-management-actions.js`, `source-editor/source-editor.js`, `source-editor/source-editor-media.js`, `source-editor/directive-actions.js` and `source-editor/document-link-contribution.js`. `git diff --check` passed. Reference inspection covered the retired definitions, renderer/handler exports, wrapper imports, image/file event names and `replaceSelection` call across `docs-viewer/runtime` and `tests`; none remain. Tests were inspected only for references and were not changed or run. No public runtime/projection files changed, so no site projection or validation run was needed for this local-only slice.

Review resolutions: the menu retains the captured adapter independently of the currently active editor, and every insertion uses the established range/revision and mounted-editor guards. Staged-media insertion now takes the captured range through its existing workflow instead of reading the current selection at completion. VS Code uses the adapter's immutable target and immediately projects the existing workflow's busy state. Source keeps one loaded/busy projection for the composite Directives control. Source-mode definition order establishes Return, Save and Directives; local CSS positions the group and opens its menu into the document. The existing directive group is flat below a separator. Former standalone wrappers and dispatch paths are removed rather than retained as hidden controls.
