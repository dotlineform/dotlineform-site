---
draft: false
doc_id: d-20260528-224754-964108
title: Panel Hosts and Control Surfaces
added_date: "2026-05-28 22:47:54"
last_updated: "2026-11-18"
summary: Current panel lifecycle, five control surfaces and exact caller-owned targets.
parent_id: d-20260424-000000-50b63f

---
# Panel Hosts And Control Surfaces

Docs Viewer has three regions, Index, Main and Info, and five registered control surfaces. The shell owns mounts; the registry owns definitions and eligibility; hosts own rendering/delegation; focused browser controllers own live state and exact operation targets. A visible control does not authorize a server write.

## Control Placement

| Surface or local host | Current responsibility |
| --- | --- |
| `index-lists` | Search input, Portfolio selection and Recent in the Index header |
| `index-view` | Controls for the active Index view, currently Manage's Recent-exclusions shortcut |
| `main-view` | Displayed-document actions, Source mode and Content Detail return controls |
| `app-management` | Manage's workspace Actions menu |
| `app-viewer` | App-level contributions such as Review's composite package controls |
| Panel chrome | Info close/status; layout-owned presentation |
| Mounted report/component | Collection search, sort, Select/Actions, row actions and modal controls |

Home and theme are composed directly by the [top-bar renderer](../../docs-viewer/runtime/js/shared/docs-viewer-top-bar-renderer.js). They are not registry definitions. The top bar supplies mounts and wrapping; its visual position does not give it ownership of a workflow. A collection's controls remain report-owned when composed into the top row. [Reader Discovery](Reader_Discovery_And_Return.md) owns what Search/Recent read and restore.

Choose placement from the user's object of attention. Use document controls for the displayed document, report controls for the mounted collection, workspace Actions for workspace work, and a context menu for an explicitly invoked row. Frequency and discoverability can justify a direct control, but its behaviour and target still have one owner. Treat action, control, placement and target as separate concepts.

## Definitions, State And Dispatch

[The registry](../../docs-viewer/runtime/js/shared/docs-viewer-view-registry.js) accepts code-owned views, modes and controls. A control declares a stable id/renderer, app or view ownership, surface, optional action id, eligible app kinds/features/capabilities and, for view controls, owning view/modes. Route policy may hide known ids; it cannot inject modules, renderers or artwork. Definition order is presentation order: shared app definitions, entrypoint contributions, then shared view definitions.

[The surface host](../../docs-viewer/runtime/js/shared/docs-viewer-control-surface-host.js) projects eligible controls into the existing mount, reuses renderer output, applies identity, labels and accessible live state, hides empty mounts and delegates click/change/input. Focused owners publish renderer-facing state keyed by control id: hidden, disabled, busy, pressed, expanded, label, counts and applicable menu availability. Domain records, editor buffers and checked IDs stay with their controllers. The runtime combines genuinely shared projections such as management busy state and Source readiness.

Manage contributes [definitions](../../docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js), renderers and [action definitions](../../docs-viewer/runtime/js/management/docs-viewer-action-definitions.js) only through its entrypoint. Review contributes its [package group](../../docs-viewer/runtime/js/review/docs-viewer-review-controller.js) through its own entrypoint. Shared/public controls remain safe to import without either local workflow.

## Exact Targets

The displayed-document owner supplies an exact ordinary or `{collection, doc_id}` target. A collection-list display supplies its ordinary report host; validated detail supplies its member. Loading or invalid detail does not fall back to the host. Edit supplies Source, Rebuild, VS Code, readiness, Star, Thumb and Copy link according to current action policy. Collection contributions retain their own handlers and may be placed in this host without changing their target.

Source owns an immutable session target and the unsaved buffer. Its return, Save, Directives and Add date controls belong to `main-view`; directives capture the adapter and selection before moving focus. [Source Editing](Source_Editing.md) owns validation, persistence, rebuild and fresh display.

Collection Actions uses immutable checked IDs from that mounted report for Export/package, and its explicit collection for import/new. The ordinary Index has no checkbox-selection owner. Its row context menu supplies the invoked ordinary document independently of whichever document is displayed. Structural/delete commands retain their subtree semantics. [Source Organisation](Source_Organisation.md) and [Collections and Books](Collections_And_Books.md) own those workflows.

## Panels And Lifecycle

The [panel layout](../../docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js) projects active Index/Main/Info presentation. Index tree, Search and Recent are retained Index views. Their data acquisition and query state remain with the discovery owner. Saved Index sizing, collapse/expand controls, Graph and the former Index action toolbar are retired.

Main hosts rendered documents, Source mode and Content Detail. [The coordinator](../../docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js) keeps view/mode and control projections aligned. Content Detail temporarily selects `expanded-main`, hiding Index/Info presentation while retaining their state. Return restores the owning document context; navigation releases that target. This layout operation performs no acquisition.

Info now hosts a pinned Related Links capture. It is opened by Pin related links, retains that capture during later document navigation and clears it on Source/reload. The former metadata/semantic-token-picker Info views are retired. [Info Panel](Info_Panel.md) owns its capture and close lifecycle.

Hosted stateful modules can implement `load → mount → update → unmount → dispose`; Main views/modes can also use `beforeLeave`. Supply the projected context needed by that module. Stateless render/projection helpers need no hosted lifecycle. Receiving a client handle or mount does not grant canonical write authority.

## Changing A Control

Trace one change through the focused browser owner, definition/eligibility, existing mount, renderer, state projection and dispatch. If it performs an operation, carry the resolved target into that operation's existing workflow; required server work remains with persistence/generation/transfer owners. Keep composite controls, including Review packages and Source Directives, together while their internal items share that lifecycle.

Then locate its [styles](CSS_Ownership.md), [artwork](Toolbar_Icons.md) and actual entrypoint. A shared/public change must follow [explicit public projection](Public_Docs_Route_Shell.md#maintenance). Readiness is a separate [route state](Route_Ready_State.md), and public/private import boundaries remain with [Runtime Ownership](Runtime_Module_Ownership.md).
