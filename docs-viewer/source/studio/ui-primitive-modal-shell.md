---
doc_id: ui-primitive-modal-shell
title: Modal Shell Primitive
added_date: 2026-05-15
last_updated: 2026-05-15
parent_id: ui-catalogue
sort_order: 5875
---
# Modal Shell Primitive

This doc is the durable implementation contract for shared modal shells across Studio and Docs Viewer management surfaces.

Demo reference:

- [Modal shell primitive demo](/studio/ui-catalogue/demos/primitives/modal-shell/)

## Scope

The modal shell primitive covers the container, lifecycle, and action-row contract for modal UI.
It does not own the domain action that caused the modal to open.

Use this primitive for:

- confirmation dialogs
- notice and result dialogs
- short input or choice dialogs
- route-owned workflow modals
- import, preview, and review modals
- portable Docs Viewer management modals that need their own implementation namespace

Do not use this primitive for:

- inline suggestion or autocomplete popups
- non-modal dropdowns
- page panels that should remain visible during normal editing
- native browser dialogs such as `window.prompt()`, `window.confirm()`, or `window.alert()`

## Contract

The shared modal shell contract includes:

- a root overlay with explicit open/hidden state
- a backdrop that can cancel or close the modal when the workflow allows it
- a dialog with `role="dialog"`, `aria-modal="true"`, and `aria-labelledby`
- a header with title and optional metadata
- a body slot for arbitrary route-owned content
- a status or validation slot near the body/action boundary
- an action row with consistent primary, secondary, cancel, close, and destructive command placement
- action-row buttons that use the shared command-button default width
- Escape, backdrop, cancel, close, and submit behavior
- focus entry, focus containment, and focus return to the opener
- responsive sizing through shell variants rather than page-specific modal chrome

The shell owns modal structure and interaction affordances.
The opener or route command owns service payload assembly, writes, rebuilds, delete operations, reloads, navigation, and durable status messages.

## Canonical Implementation Direction

The Studio canonical source should build from:

- `assets/studio/js/studio-modal.js`
- `renderStudioModalFrame()`
- `renderStudioModalActions()`
- route-owned or shared modal hosts created through `createStudioModalHost()`

Those helpers should be refined to match this full shell contract rather than treated as complete as-is.
The shared Studio helper now provides:

- explicit header support in the shared frame helper
- a standard status or validation slot
- focus return and focus containment
- Enter-submit behavior for short input modals
- `compact`, `default`, `wide`, and `document` size variants

The existing `openConfirmModal()`, `openConfirmDetailModal()`, `openNoticeModal()`, `openTextInputModal()`, and `openChoiceModal()` helpers are convenience APIs on top of this shell.
They are not separate modal patterns.

Docs Viewer management may keep `docsViewer__*` classes, its own static shell markup, and portable JavaScript helpers when portability requires it.
That implementation separation is acceptable only when it preserves this same shell anatomy, focus behavior, action ownership, and audit contract.

## Migration Defaults

Use these defaults before starting page-level modal migration:

- action order is secondary, cancel, or close first and primary confirmation last/rightmost
- action buttons use the shared `tagStudio__button--defaultWidth` minimum width
- destructive actions do not get a separate default visual treatment unless a page audit proves the workflow needs one
- destructive meaning should be carried by title, body copy, affected-record detail, and confirmation flow
- shell size variants are `compact`, `default`, `wide`, and `document`
- `compact` is `38rem` and is for simple notices, short confirmations, and short input or choice modals
- `default` is `52rem` and is the normal multi-field modal width
- `wide` is for dense workflow modals with list, import, or preview content
- `document` is for document-like or import-body content that should follow readable measure
- Studio helper equivalence is available through confirm, detail-confirm, notice, text-input, and choice helpers
- Docs Viewer may keep portable `docsViewer__*` implementation details, but must match this contract visually and behaviorally
- page migrations should use this primitive contract plus the page-level tracker in [Modal Composition Pattern Request](/docs/?scope=studio&doc=ui-request-modal-composition-pattern)

## Anatomy

Preferred anatomy:

1. overlay root
2. backdrop
3. dialog
4. header
5. title and optional meta
6. body
7. status or validation message
8. action row

The body may contain fields, lists, previews, file inputs, nested local popups, or route-specific workflow controls.
Those controls should use the same primitive contracts as equivalent controls on the page.

## Action Ownership

Modal helpers may own:

- local required-field checks
- local choice completeness checks
- close/cancel result construction
- returned values or selected options
- transient status inside the modal

Modal helpers should not own:

- create, update, delete, publish, import, rebuild, or write actions
- service endpoint selection
- service payload assembly beyond local returned values
- route reloads or navigation
- long-lived page status outside the modal

## Possible Patterns

These are application patterns that should use the modal shell primitive.
They are listed here to keep the primitive tied to actual page work, not to create separate shell contracts.

| Pattern | Use when | Current examples |
| --- | --- | --- |
| Confirmation modal | A command needs explicit review before continuing. | Catalogue editor publish/delete confirmations, tag delete confirmations, Docs Viewer delete confirmations. |
| Notice or result modal | A completed command needs readable details but no extra decision. | Activity details, Data Sharing Prepare result, Data Sharing Review result. |
| Short input modal | A command needs one or two values before the opener can continue. | Docs Viewer new document title. |
| Choice modal | A command needs a small structured selection. | Docs Viewer viewability parent/descendant choices. |
| Reopenable result modal | A result remains valid and should reopen without rerunning the command. | Data Sharing Review result modal. |
| Route-owned workflow modal | A route owns staged state, complex controls, validation, and writes. | Tag Registry, Tag Aliases, Series Tags, Catalogue Work embedded-entry modals. |
| Import or review modal | A file/input workflow needs preview, conflict handling, and apply controls. | Series Tags import, Docs Viewer import, Docs HTML import filename conflict. |
| Portable static shell modal | A portable surface cannot depend directly on Studio JS/CSS but must preserve the same contract. | Docs Viewer metadata, import, and settings modals. |

## Implementation Notes

Current live implementation sources:

- `assets/studio/js/studio-modal.js`
- `assets/studio/css/studio.css`
- `docs-viewer/runtime/js/docs-viewer-management-modals.js`
- `docs-viewer/static/css/docs-viewer-management.css`
- `_includes/docs_viewer_shell.html`

Current demo implementation lives in:

- `studio/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `studio/ui-catalogue/assets/js/ui-catalogue-demo.js`
- `studio/ui-catalogue/demos/primitives/modal-shell/index.md`

The UI Catalogue demo uses `uiCatalogueDemo*` classes and demo-owned JavaScript.
Treat the demo as the modal shell contract reference, then map the structure into the live Studio namespace or the portable Docs Viewer namespace during page migration.

## Audit Notes

UI audits for modal-owning pages should check:

- at least one browser-opened modal state for each modal pattern used on the page
- desktop and mobile fit
- Escape, backdrop, close/cancel action, and submit behavior
- focus entry and return
- validation and status-message placement
- action ownership, especially that writes and reloads remain route-owned
- parity between Studio and portable Docs Viewer modal implementations where applicable

The modal migration is tracked in [Modal Composition Pattern Request](/docs/?scope=studio&doc=ui-request-modal-composition-pattern).
