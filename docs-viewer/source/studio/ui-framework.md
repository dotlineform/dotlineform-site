---
doc_id: ui-framework
title: UI Framework
added_date: 2026-04-24
last_updated: 2026-05-22
parent_id: ui
---
# UI Framework

This document defines the current site-wide UI framework.

References:

- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [UI Audits](/docs/?scope=studio&doc=ui-audits)

## Design Steps

For any UI task:

1. Identify the UI type before editing.
2. Check whether the page should use an existing shared primitive or composition.
3. Check whether visible runtime copy should come from `studio_config.json`.
4. Check whether the issue is local or systemic.
5. Only then move into the detailed framework or page docs.

### Identify The UI Type

Decide which contract the change belongs to:

- command button
- link or route-entry action
- pill or chip
- panel or panel-link
- input or search field
- local command feedback/status
- list shell or capped list
- modal shell or modal action row
- page-specific composition

If the answer is unclear, stop and classify it first. Several recent inconsistencies came from mixing buttons, links, and route-local compositions.

### Shared Primitive Check

Before adding or changing UI:

- check the isolated demo pages under `/ui-catalogue/demos/`
- map the demo structure into the shared layer or an owning route namespace before inventing unrelated markup or CSS
- if the live page fails after mapping a catalogue pattern, use UI Audit to decide whether the issue is in the live route, the shared production primitive, or the demo pattern
- if a pattern is repeated but not yet formalized, decide whether it is:
  - a shared primitive
  - a shared composition
  - or a truly route-specific layout
- use this is a prompt to call out the need to define a new shared primitive or composition pattern

### UI Copy Check

For Studio pages, visible runtime copy should normally come from `assets/studio/data/studio_config.json`.

Check these points:

- if the runtime calls `getStudioText(config, "<scope>.<key>")`, the matching `ui_text.<scope>` block must exist
- do not let JS fallback strings become the real source of truth
- route paths belong in config routes
- visible button labels, headings, placeholders, status text, and other runtime copy belong in `ui_text`
- build-time-only design selections for static pages belong in Jekyll data, not Studio runtime config

Relevant references:

- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio Config And Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)

### Fast Rules

Use these default checks on every Studio UI task:

- buttons are commands, not navigation
- route-entry actions should usually be links, not buttons
- shared command buttons should use the shared size/width contract unless reviewed otherwise
- command feedback should stay adjacent to the related control area
- capped-list search should appear only when the list is actually truncated
- if a row already has a clear link to the target record, do not duplicate that same navigation as a button
- do not use a panel as a generic wrapper just to get a border around unrelated controls
- if a static Studio route gains async data, service checks, or route commands, replace the static ready initializer with a route-specific ready/busy contract before treating it as smoke-test ready

### Close-Out Checklist

Before finishing Studio UI work:

- update `studio_config.json` if visible runtime copy changed
- update shared docs if the contract changed
- verify desktop and mobile behavior
- run `$HOME/miniconda3/bin/python3 studio/checks/audit_studio_ready_state.py --strict` after changing Studio route shells or route-ready scripts

The goal is consistency without introducing a heavy component system. Pages should expose their major layout containers in template markup, keep JS focused on dynamic UI, and reuse stable hooks and shared primitives instead of borrowing unrelated page-specific class names.

## Site UI Contract Boundary

Use three separate UI contracts across the site:

- `class=""`
  presentation only
- stable `id=""`, `data-role=""`, or feature-scoped `data-*`
  JS lookup only
- `data-role=""`
  use when a reusable semantic JS hook is needed
- `data-state=""` and `aria-*`
  runtime state only

Rules:

- JS behavior must not query styling classes when a stable hook can be exposed.
- Prefer explicit `data-role`, stable `id`, or feature-scoped `data-*` hooks over presentational selectors.
- JS must not toggle presentation classes such as `.is-active`, `.is-error`, or page-specific BEM classes.
- Page templates should own major layout containers and section boundaries.
- JS should generate only the inner dynamic fragments that actually change at runtime.

For Studio-generated markup, use `assets/studio/js/studio-ui.js` to keep `data-role` selectors and generated style class names visible in one place.

## Site Interaction Defaults

### Progressive enhancement

Site interactions should default to progressive enhancement:

- preserve baseline links, buttons, keyboard behavior, and visible controls
- add JS behavior on top of existing navigation and control flows rather than replacing them
- keep behavior scoped to the relevant content region rather than binding globally unless the page architecture genuinely requires it

### Header navigation overflow

When a section-specific header has more top-level links than fit on narrow screens:

- keep the primary/root destination visible as a normal link
- move secondary destinations behind the shared `nav-more` menu at mobile widths
- use the existing `data-nav-more` disclosure behavior so Escape, outside-click close, active-state styling, and ordinary links stay consistent
- keep the desktop link row unchanged unless the desktop layout also overflows

### Prev/next and paginated navigation

For any image viewer, detail viewer, or paginated grid:

- reuse the existing previous/next controls or the same underlying URL/state-generation logic already used by the UI
- do not invent a parallel navigation model in JS
- preserve existing first/last behavior exactly, including wrapping if the current controls already wrap
- if no valid previous/next action exists, do nothing in that direction

### Swipe navigation default

Horizontal swipe is the default progressive enhancement for:

- image viewers with existing previous/next navigation
- paginated thumbnail grids with existing previous/next pagination controls

Required implementation rules:

- use Pointer Events as the primary input model unless a page has a clear incompatible constraint
- activate swipe only from the main media or grid region, not from the whole document by default
- use stable DOM hooks such as `data-role`, stable `id`, or feature-scoped `data-*`, not presentational class names
- resolve navigation from the existing prev/next anchors or buttons at gesture time
- preserve click/tap navigation, keyboard navigation, visible controls, and ordinary vertical scroll
- use conservative gesture thresholds and ignore taps, small drags, slow drags, vertical scrolls, and diagonal movement
- ignore multi-touch interactions
- cancel tracking on `pointercancel`
- apply `touch-action: pan-y` only on the specific swipe zone, not globally

Benefits:

- keeps navigation behavior consistent across input modes
- avoids duplicated URL/state logic
- reduces accidental regressions when navigation behavior changes

Risks to watch:

- accidental click activation after a successful swipe
- over-broad swipe zones that interfere with vertical scrolling or interactive children
- JS that reads visual class names instead of stable behavior hooks

## Docs Viewer UI Standards

These standards apply to the shared docs-viewer UI used by:

- `/docs/`
- `/library/`
- `/analysis/`

Detailed runtime behavior still belongs in the docs-viewer and search sections. This document only records the current UI standards.

### Viewer anatomy

The current shared viewer uses:

- a left index rail for the docs tree
- a right main pane for search, metadata, and content
- a sticky sidebar on larger screens
- desktop index-panel controls for direct expanded mode and one-step restore/collapse
- a stacked single-column layout on smaller screens

The docs tree remains visible while the right pane switches between:

- doc-view mode
- inline docs-search results mode

This should stay a quiet document-reader layout rather than becoming an app-style workspace shell.

On larger screens, the index panel may collapse to a narrow visible strip or expand to occupy the viewer content area. A direct expand control should be visible only in normal state. A separate one-step control restores collapsed to normal, collapses normal to collapsed, and restores expanded to normal. The mobile stacked layout should remain unchanged because the document pane is already full width there.

### Search placement

When docs search is enabled for a scope:

- the search input lives in the main pane header
- the recently-added command lives immediately before the search input
- results replace the normal content pane
- search is inline, not a floating overlay or dropdown
- the docs tree remains the stable left-side navigation surface

This keeps docs search visually tied to the current docs scope rather than the global site header.

The recently-added command is part of the shared Docs Viewer shell. It should remain available on both `/docs/` and `/library/` when inline docs search is available, and it should render the same simple result-list shape as docs search.

### Metadata and content framing

In doc-view mode, the main pane should show:

- search field first when available
- status line below the search field
- ancestor path, last-updated metadata, and optional summary metadata above document content
- one readable content column rather than full-width text
- linked or token-resolved Markdown images constrained to the content column width, with image-only paragraphs rendered as block media

The ancestor path must not repeat the current doc title, because the rendered document H1 is the title. Root-level docs should hide the path line and let the updated date occupy the top metadata line.

When a doc has summary metadata, show it below the updated date as secondary text rather than folding it into the authored body.

In search mode, the main pane should show:

- status line
- one inline results list
- one inline `more` control when needed

In recently-added mode, the main pane should show:

- status line
- one inline capped results list
- no separate `more` control

### Tree and result styling

The current shared treatment is:

- tree links render as quiet pill-like rows, not file-manager rows
- tree text uses the small text token so the index reads as secondary navigation and long titles fit better
- result links render as simple stacked list items
- result metadata stays secondary and muted
- docs-viewer search and recently-added results show title plus `date` or `date • parent`; they do not show `doc_id` as a separate visible line
- docs-viewer search uses `last_updated` for its date metadata, while recently-added uses `added_date`
- active state should be obvious without turning the viewer into a tabbed interface
- scope-level structural visibility should come from generated docs index options rather than hard-coded scope checks in the viewer
- in manage mode, the toolbar note should appear only for actionable states such as checking, unavailable server, active search, or operation results; the available local-server state should stay quiet
- in manage mode, non-viewable docs remain visible by default and the checked-by-default `show viewable` checkbox controls whether viewable docs stay in the tree for context
- non-viewable tree rows use a `✏️` title prefix plus the draft color from `studio_config.json`; they should not rely on bold text as the primary distinction
- in manage mode, drag/drop tree moves should treat every doc node as a potential parent, and the root list as a root-level target
- drop indicators should distinguish the target parent row from the root-level drop target
- drag/drop tree moves update only `parent_id`; index order remains generated title order within each parent
