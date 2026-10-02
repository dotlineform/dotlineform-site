---
draft: false
doc_id: d-20261002-130225-c46d18
title: Document Edit Menu
added_date: "2026-10-02 13:02:25"
last_updated: "2026-10-02 13:24:24"
parent_id: d-20260428-000000-f5ff18
ui_status: done
summary: Consolidate displayed-document editing actions into the right-aligned Edit dropdown.
---
# Document Edit Menu

## Requirements

Replace the direct Edit action with a dropdown containing Source editor, Open in VS Code, Draft/Ready, Star, Copy link, Delete, Assign Subject and Open in Finder, in that order. Source editor uses `square-code.svg` and retains the existing Source workflow. VS Code, Draft/Ready and Star move from workspace Actions and keep their context-aware targets, handlers, changing labels, checkbox state and artwork. New remains in Actions. All items remain visible; existing eligibility makes unsupported operations disabled. The pen trigger retains its document-right-edge placement and the menu opens left. Source and expanded views hide it, including VS Code; Source-view access is part of the later toolbar design.

Collection detail actions keep their validated targets, existing workflows and live availability, with no duplicate detail toolbar buttons. Ordinary Copy/Delete use the existing handlers and deletion confirmation. Source editor toolbar changes remain a later outcome.

## Deliverables And Process

A local Edit menu owner renders the dropdown and dispatches ordinary actions. The existing context-actions owner supplies New's state/dispatch to Actions and VS Code, Draft/Ready and Star to Edit. State projection runs after Edit controls mount so returning from Source restores current labels and checkbox state. Keyboard navigation includes ordinary and checkbox items. The retained collection detail action host mounts inside the menu while rendered, and in the existing hidden collection-action mount during Source or expanded views. This preserves contribution lifecycle and asynchronous availability without another set of collection handlers. Delete and Subject modal focus returns to the Edit trigger.

[Toolbar Model](Toolbar_Model.md), [Runtime Module Ownership](Runtime_Module_Ownership.md) and [Toolbar Icon Mapping](Toolbar_Icon_Mapping.md) own shipped placement, ownership and artwork. The shared runtime's Manage-specific mounting change receives the normal tracked public projection; the menu module, stylesheet changes and Source editor artwork remain local.

## Delivery Steps

- [x] Readiness: approved by the user; one bounded dropdown consolidation using existing action owners. No service, deletion policy or Source editor toolbar redesign.
- [x] Implementation: menu, collection contribution presentation, modal focus, styles and durable documentation updated.
- [x] Verification: changed-source lint, SVG parsing, whitespace, shared-code projection/check and static-site validation passed. These address syntax, artwork and canonical/public artifact agreement; they do not prove UI fit or live mutations. No test work or browser automation was included. The checks wrote only the normal runtime projection and validation reports and took seconds.
- [x] Code review: reviewed exact dispatch targets, contribution ownership, Source/expanded retention, disabled fallbacks and public isolation after static evidence. No unresolved code findings or compatibility aliases were introduced.
- [x] Closeout: check outcomes and review findings recorded below; visual and interaction review remains with the user. No Publish, rebuild, commit or push ran.
- [x] Placement revision: VS Code, Draft/Ready and Star now render and dispatch in Edit; New remains in Actions. The obsolete Source-target branch was removed from this menu owner.
- [x] Placement-revision evidence and review: lint passed for the four changed local JavaScript modules and whitespace passed. Bounded review confirmed menu ownership, checkbox keyboard navigation and state projection after Source/expanded return, with no unresolved findings. These read-only static checks took seconds; no test or browser run was included. The already checked public projection is unchanged by this revision.

Verification evidence: `bin/lint-js` passed for the nine changed/new modules: `docs-viewer-management-edit-menu.js`, `docs-viewer-management-control-renderers.js`, `docs-viewer-management-hosted-views.js`, `docs-viewer-management-collection-default-contribution.js`, `docs-viewer-management-collection-working-subjects.js`, `docs-viewer-management-collection-delete-workflow.js`, `docs-viewer-management-index-controller.js`, `docs-viewer-management.js` and shared `docs-viewer-app-runtime.js`. `xmllint --nonet --noout docs-viewer/static/icons/square-code.svg` and `git diff --check` passed. `bin/site-code-update` changed only the projected shared app runtime; its exact delta was reviewed. `bin/site-code-update --check` reported all 99 projections current, and `bin/site-validate` passed.

Review resolutions: Source and expanded modes retain the existing contribution host in the hidden collection-action mount, preserving pending availability initialization. Edit refreshes ordinary disabled state when opened, and consumes the existing individual Delete state instead of resolving unrelated Index actions. Modal focus returns to the visible trigger. The public runtime retains its existing collection action placement; all new menu imports and artwork remain management-only. Relevant source lint was rerun after these refinements. Manual review should cover the menu's fit/order, disabled Catalogue and unsupported Subject/Finder entries, Source/expanded return and modal focus; live mutations were not exercised.

Placement-revision evidence: `bin/lint-js` passed for `docs-viewer-management-actions-renderer.js`, `docs-viewer-management-edit-menu.js`, `docs-viewer-management-context-actions.js` and `docs-viewer-management.js`; `git diff --check` passed. The three moved actions keep one existing state/dispatch owner. Edit's keyboard navigation includes `menuitemcheckbox` entries; state is projected after the menu mounts and refreshed when opened. Workspace dispatch retains New, with no duplicate moved entries. The captured Source-target branch is retired from this menu owner because Edit is hidden there. Manual review remains for the revised menu fit, Star/Draft labels and checkbox state, and Source/expanded return; no live mutations, rebuild, Publish, commit or push ran.

## Follow-on

Review the Source editor view's buttons as a separate design and implementation slice.
