---
doc_id: ui-pattern-select-menu
title: Select Menu Pattern
added_date: 2026-05-29
last_updated: 2026-05-29
parent_id: ui-catalogue
---
# Select Menu Pattern

This composition pattern covers compact value-selection controls that share visual treatment with toolbar controls while preserving selection semantics.
It is a sibling of [Action Menu Pattern](/docs/?scope=studio&doc=ui-pattern-action-menu), not a command-menu variant.

Demo reference:

- [Select menu pattern demo](/studio/ui-catalogue/demos/patterns/select-menu/)

Initial live migration target:

- Docs Viewer management toolbar scope dropdown on `/docs/?mode=manage`

## Scope

Use this pattern when:

- a compact toolbar, header, or control row needs a value picker
- the user is choosing one current value from a known option set
- the selected value should remain visible after the menu closes
- option state comes from route config, loaded data, or capability data
- visual treatment should align with nearby toolbar buttons

The pattern supports user-config-backed option records by default.
This is appropriate for controls such as the Docs Viewer scope dropdown, where config describes selectable values rather than executable behavior.
That support is not a requirement for every live use of the pattern: each route still decides whether its option source may be user-editable, checked-in config, generated data, or code-owned state.

Do not use this pattern for:

- command actions
- multi-select controls
- typeahead search results
- long record pickers
- navigation links that do not represent a selected value

Use [Action Menu Pattern](/docs/?scope=studio&doc=ui-pattern-action-menu) for command dispatch.

## Native Select First

Prefer a native `<select>` when it can satisfy the interaction requirement.
Native selects provide reliable keyboard, pointer, screen-reader, and mobile behavior with less custom code.
When a native select appears beside custom toolbar controls, align it with the same control-height, border, font, and horizontal padding tokens where practical.
Native select rendering can still vary by browser and platform; do not replace native behavior only to achieve pixel-perfect height matching.

Use a custom select-menu only when a native select cannot meet a real requirement, such as:

- richer option rows
- grouped options with route-specific presentation
- disabled reasons that need clear inline display
- a shared menu surface that must visually align with nearby action menus

When using a native select, the pattern still applies to structure, sizing, labeling, option sourcing, and route-owned change handling.

## Anatomy

The native-select version has four parts:

- optional visible or visually-hidden label
- select control
- option records
- route-owned change handler

The custom-menu version has five parts:

- trigger button showing the current value
- positioned listbox/menu surface
- one option row per option record
- selected-state projection
- route-owned change handler

The selected value should be stable in width and legible in compact toolbars.
If option labels vary significantly, set a sensible control width rather than letting the toolbar jump between values.
Custom select menus that show `meta` should use route-scoped sizing tokens to avoid pushing secondary text too far from the label.
A useful default is a fixed menu width plus a label column that has a minimum width but does not consume all remaining space.

Example:

```css
.routeSelectMenu {
  --select-menu-width: 19rem;
  --select-menu-label-min: 7rem;
}
```

Then map those tokens into the live namespace so the row grid can keep emoji, label, and meta aligned without making a full-width gutter between label and meta.

## Option Record Contract

Live routes should define option records close to the route/controller state that owns the current value.
Option records may come from user-editable config when the route explicitly treats those values as safe selectable data.

Recommended record shape:

```js
{
  value: "studio",
  emoji: "🛠️",
  label: "Studio",
  title: "Studio documentation",
  selected: state.scope === "studio",
  disabled: false
}
```

Required fields:

- `value`: stable value sent to the route change handler
- `label`: visible option label

Optional fields:

- `emoji`: short emoji marker shown in a reserved leading slot
- `title`: tooltip or disabled reason
- `selected`: current selected projection when the helper does not receive a separate value
- `disabled`: render the option but prevent selection
- `hidden`: omit or hide the option
- `controlId`: stable DOM id when a route has existing tests or activity logging tied to ids
- `meta`: short secondary text for custom option rows only

Routes may derive options from route config, generated data, or backend capability data.
The pattern should receive already-normalized options and a current value.

If any option uses `emoji`, every option row should reserve the same leading emoji slot.
Options without `emoji` should render an empty placeholder rather than shifting the label left.
For scope pickers, emoji can provide a compact visual indication of scope type, such as public, local, management-only, or generated-data-backed scopes.
The selected-value display may include the selected option emoji when space allows, but the text label remains the accessible source of meaning.

## Lifecycle Contract

The select-menu controller owns:

- render or projection of options
- current-value display
- disabled and hidden option projection
- open, close, and toggle behavior for custom menus
- Escape and outside-click close behavior for custom menus
- disabled-option selection prevention
- emitting a single change event or callback when the selected value changes

The route owns:

- option record construction
- label source and production UI text lookup
- current value
- deciding whether value changes update URL, local state, loaded data, or all three
- loading or reloading data after selection
- route readiness, busy state, status messages, and validation

The pattern should not decide navigation or persistence.
It should only surface a selected value and call the route when that value changes.

## Accessibility And Keyboard Behavior

Native select implementation:

- associate the select with a visible or visually-hidden label
- keep focus states visible
- disable unavailable options with native `disabled`
- do not replace native keyboard behavior with JavaScript

Custom implementation minimum:

- trigger exposes popup state with `aria-expanded`
- option list exposes selected value with `aria-selected` or equivalent button state
- Escape closes and returns focus to the trigger
- outside click closes the popup
- disabled options cannot dispatch
- hidden options are not reachable by keyboard

Preferred custom implementation:

- Down Arrow and Up Arrow open the list and move through enabled options
- Home and End move to first and last enabled options
- Enter or Space selects the focused option
- Tab leaves the control and closes the popup

Use a custom implementation only when this keyboard behavior can be maintained.

## Implementation Notes

Current demo implementation should live in:

- `studio/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `studio/ui-catalogue/assets/js/ui-catalogue-demo.js` or a scoped demo module under `studio/ui-catalogue/assets/js/`
- `studio/ui-catalogue/demos/patterns/select-menu/index.md`

The UI Catalogue demo must use `uiCatalogueDemo*` classes and demo-owned JavaScript.
Treat the demo as the pattern reference, then map the structure into the owning live namespace.

Live implementations should use route-owned classes:

- Docs Viewer should use `docsViewer*`
- Studio routes should use their existing route or family namespace
- UI Catalogue demos should use `uiCatalogueDemo*`

Do not import production Docs Viewer or Studio CSS into the demo page to prove the pattern.
Do not make the demo load real route data.

## Docs Viewer Migration Notes

The Docs Viewer scope picker is currently rendered as a native select in the header controls renderer and populated by the config controller.
The migration target is a visually consistent toolbar select with no unnecessary semantic downgrade.

For the first Docs Viewer pass:

- prefer keeping the native select unless a custom menu requirement is explicit
- move repeated select projection into a focused helper only if it reduces controller wiring
- keep scope options owned by Docs Viewer config and route context
- keep scope changes owned by the Docs Viewer config/route workflow
- preserve public/manage route capability rules
- keep the control available only where the route allows scope query selection

The select-menu helper should not know about Docs Viewer scopes.
It should receive option records, current value, labels, and an `onChange` callback.

## Benefits

- keeps value-pickers visually aligned with command controls
- preserves a clear distinction between commands and selected values
- reduces route-local select styling drift
- gives routes a small normalized option contract
- keeps native form semantics available where they are sufficient

## Risks

- replacing native selects too early can reduce keyboard and mobile reliability
- a generic helper can hide route-specific URL or loading behavior
- long labels can destabilize compact toolbar layouts
- option records can become stale if route config changes after initial render
- custom select behavior can duplicate browser behavior poorly

Keep the pattern conservative: native select first, custom menu only for a documented need.
