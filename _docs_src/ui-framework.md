---
doc_id: ui-framework
title: "UI Framework"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: design
sort_order: 10
---

# UI Framework

This document defines the current site-wide UI framework.

It covers:

- site-wide interaction defaults and JS hook rules
- shared UI standards for the docs viewer
- shared UI standards for the dedicated public search page

It does not define Studio-specific shared primitives or modal patterns. Those now live in [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework).

The goal is consistency without introducing a heavy component system. Pages should expose their major layout containers in template markup, keep JS focused on dynamic UI, and reuse stable hooks and shared primitives instead of borrowing unrelated page-specific class names.

Related references:

- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [CSS Primitives](/docs/?scope=studio&doc=css-primitives)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

## Scope

This framework covers:

- site-wide behavior contracts for progressive enhancement, navigation interactions, and DOM hooks
- docs-viewer UI standards for `/docs/` and `/library/`
- public search UI standards for `/search/`

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

Detailed runtime behavior still belongs in the docs-viewer and search sections. This document only records the current UI standards.

### Viewer anatomy

The current shared viewer uses:

- a left index rail for the docs tree
- a right main pane for search, metadata, and content
- a sticky sidebar on larger screens
- a desktop sidebar collapse control for widening the document pane
- a stacked single-column layout on smaller screens

The docs tree remains visible while the right pane switches between:

- doc-view mode
- inline docs-search results mode

This should stay a quiet document-reader layout rather than becoming an app-style workspace shell.

On larger screens, the index rail may collapse to a narrow visible strip. The collapse control must remain visible in both states, and the collapsed document pane may use a wider capped reading measure. It should not become fully fluid prose. The mobile stacked layout should remain unchanged because the document pane is already full width there.

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
- breadcrumb/path and last-updated metadata above document content
- one readable content column rather than full-width text

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
- result links render as simple stacked list items
- result metadata stays secondary and muted
- docs-viewer search and recently-added results show title plus `date` or `date • parent`; they do not show `doc_id` as a separate visible line
- docs-viewer search uses `last_updated` for its date metadata, while recently-added uses `added_date`
- active state should be obvious without turning the viewer into a tabbed interface

## Public Search UI Standards

These standards apply to the dedicated public search page:

- `/search/`

Detailed search behavior, scope policy, and ranking are documented elsewhere. This section only records the current UI shape.

### Page anatomy

The current page should keep this structure:

- back link to the owning scope surface
- explicit visible scope label
- one primary search input
- one inline status line
- one inline result list
- one inline `more` control when results are incrementally expanded

This remains a dedicated page, not a header-level overlay.

### Scope visibility

The active search scope must stay visible in page chrome, not only in the URL.

Current UI signals:

- back-link label
- scope label beside the header area
- scope-owned placeholder and ARIA copy

### Result list shape

Results should remain:

- a single mixed ranked list
- inline on the page
- visibly typed by small kind labels
- light on controls and chrome

The page should not introduce:

- result grouping panels
- floating suggestion menus
- separate filter drawers
- secondary result panes

### Search input consistency

The dedicated public search page and the docs viewer should keep their search inputs visually aligned where possible:

- same overall pill-like shape
- same focus treatment
- same plain inline placement above results

Minor scope-specific differences are acceptable, but divergence should be intentional.

## Relationship To Other Documents

Use this document for:

- current site-wide UI standards
- current docs-viewer UI standards
- current public search page UI standards

Use other docs for:

- Studio shared primitives and modal patterns
  - [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- docs-viewer runtime fork rules
  - [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- public search route, scope vocabulary, and functional behavior
  - [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
  - [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
