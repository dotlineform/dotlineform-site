---
doc_id: ui-pattern-action-menu
title: Action Menu Pattern
added_date: 2026-05-29
last_updated: 2026-05-29
parent_id: ui-catalogue
---
# Action Menu Pattern

This composition pattern covers a button-triggered menu of commands where each item invokes a route-owned action.
It is intended for repeated command groups that should share visual treatment, accessibility behavior, and lifecycle rules without sharing route-specific business logic.

Demo reference:

- [Action menu pattern demo](http://127.0.0.1:8768/admin/ui-catalogue/demos/patterns/action-menu/)

Initial live migration target:

- Docs Viewer management `Actions` menu on `/docs/?mode=manage`

## Scope

Use this pattern when:

- a compact toolbar or header needs several related commands
- the commands are actions, not navigation links
- trusted route code can define commands as structured action records
- the command list needs disabled or hidden projection from route state
- menu open/close behavior should be consistent across Studio surfaces

Do not use this pattern for:

- ordinary navigation groups
- a single primary action
- choosing one persistent value from a list
- long record lists or search results
- destructive confirmation content that belongs in a modal

Use [Select Menu Pattern](/docs/?scope=studio&doc=ui-pattern-select-menu) for value selection.

## Anatomy

The pattern has four parts:

- trigger button
- positioned menu surface
- one button per action record
- route-owned action dispatcher

The trigger should expose menu state with `aria-haspopup="menu"` and `aria-expanded`.
The menu should use `role="menu"` and command buttons should use `role="menuitem"` unless a live route has a stronger semantic reason to use ordinary button grouping.

The visual treatment should be compact and stable:

- trigger width should not jump when the menu opens
- menu width should be at least the trigger width and wide enough for the longest expected command
- menu items should use consistent row height, padding, focus state, disabled state, and text alignment
- the menu should close before or immediately after an action begins

## Action Record Contract

Live routes should define action records close to the route/controller state that owns them.
The shared pattern should not know route-specific services, document state, backend endpoints, or modal flows.
Action records are design-time code, not user-editable config.
The route may read stable UI text from the route's normal copy/config source, but user-editable config must not create, remove, reorder, rename, or retarget action commands.

Recommended record shape:

```js
{
  id: "rebuild-docs",
  emoji: "🔁",
  label: "Rebuild docs",
  title: "Rebuild generated docs for the active scope",
  hidden: false,
  disabled: state.busy,
  run: handlers.rebuildDocs
}
```

Required fields:

- `id`: stable command id used for DOM data attributes, dispatch, and tests
- `label`: visible command label
- `run`: callback invoked by the route when the command is selected

Optional fields:

- `title`: tooltip or disabled reason
- `emoji`: short emoji marker shown in a reserved leading slot
- `hidden`: omit or hide the action from the menu
- `disabled`: render the action but prevent dispatch
- `danger`: visual variant for destructive commands when the route has already handled confirmation rules
- `controlId`: stable DOM id when a route has existing tests or activity logging tied to ids
- `activityActionId`: optional activity-log id distinct from the UI id

Routes may derive records from local config, backend capability data, or route state.
The menu pattern should receive already-normalized records and callbacks.
Those sources may decide availability or disabled state, but the executable command set stays code-owned.

If any item in a menu uses `emoji`, every item row should reserve the same leading emoji slot.
Items without `emoji` should render an empty placeholder rather than shifting the label left.
This keeps scan alignment stable and allows selective visual hints for action type, risk, or destination without turning emoji into required UI copy.

## Lifecycle Contract

The menu controller owns:

- render or projection of menu item markup
- trigger `aria-expanded` state
- open, close, and toggle behavior
- outside-click close behavior
- Escape-key close behavior
- closing on scroll or resize when the menu position could become stale
- disabled-item dispatch prevention
- restoring a closed state when the trigger becomes disabled

The route owns:

- action record construction
- label source and production UI text lookup from trusted route-owned copy
- hidden and disabled projection from route state
- command callbacks
- busy state and status messages
- validation, confirmation, modals, service calls, and writes
- route readiness and activity logging

The pattern should not retain stale action records after route state changes.
Routes should re-project the actions whenever capability, selection, busy state, or loaded data changes.

## Accessibility And Keyboard Behavior

Minimum behavior:

- trigger toggles the menu with click and normal button keyboard activation
- Escape closes the menu and returns focus to the trigger
- outside click closes the menu
- disabled items cannot dispatch
- hidden items are not reachable by keyboard

Preferred behavior for production implementations:

- Down Arrow from the trigger opens the menu and focuses the first enabled item
- Up Arrow from the trigger opens the menu and focuses the last enabled item
- Arrow keys move between enabled menu items
- Home and End move to first and last enabled menu items
- Tab leaves the menu through normal document focus order and closes it

If a first implementation does not include full roving focus, it must still keep native button focus visible and avoid trapping focus.

## Implementation Notes

Current demo implementation should live in:

- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/assets/js/ui-catalogue-demo.js` or a scoped demo module under `admin-app/ui-catalogue/assets/js/`
- `admin-app/ui-catalogue/source/demos/patterns/action-menu/index.md`

The UI Catalogue demo must use `uiCatalogueDemo*` classes and demo-owned JavaScript.
Treat the demo as the pattern reference, then map the structure into the owning live namespace.
The reusable contract is the composition pattern: item record shape, markup structure, class roles, visual behavior, and interaction expectations.
It is not a requirement that every Studio route use the same JavaScript app model as Docs Viewer.

Live implementations should use route-owned classes:

- Docs Viewer should use `docsViewer*`
- Studio routes should use their existing route or family namespace
- UI Catalogue demos should use `uiCatalogueDemo*`

Live implementations should adapt the pattern into their owning runtime.
Docs Viewer can use a lazy app-shell renderer and management controller bindings.
Studio routes can use route-owned modules or local route JavaScript until Studio has a broader app model.

Do not import production Docs Viewer or Studio CSS into the demo page to prove the pattern.
Do not make the demo call real write services.

## Docs Viewer Implementation Notes

The Docs Viewer management `Actions` menu uses this pattern in `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`.
Menu rows are design-time records owned by the renderer, with stable ids, labels, optional emoji, and visibility defaults.
The management controller still owns capability projection and command binding.

Implementation boundaries:

- keep management-only loading behind the Docs Viewer lazy management boundary
- keep Docs Viewer classes and current visual styling
- define management actions as design-time records in the focused management action renderer
- keep actual write workflows in `docs-viewer-management-actions.js`
- keep backend calls behind `docs-viewer-management-client.js`
- preserve existing stable ids where current smoke tests or activity contexts need them
- do not make the Docs Viewer `Actions` menu user-configurable

The action-menu renderer must not become a Docs Viewer service adapter.
It owns menu markup only; state projection and command dispatch remain with the management controller and action workflow modules.

## Benefits

- keeps command-menu behavior consistent across Studio and Docs Viewer
- reduces fixed-id and per-button wiring in route controllers
- gives routes a clear place to project capability and busy state
- makes future action additions smaller and easier to test
- separates visual/menu interaction from command workflow ownership

## Risks

- an overly broad helper could hide route-specific write authority
- storing callbacks inside long-lived records can become stale after route state changes
- keyboard behavior can regress if the helper relies only on click handling
- generic labels can bypass trusted route-owned UI text sources
- user-editable action configuration can create false expectations or security risk
- destructive actions can look too casual if confirmation remains unclear

Keep the pattern narrow: a consistent command menu shell with explicit route-supplied records and callbacks.
