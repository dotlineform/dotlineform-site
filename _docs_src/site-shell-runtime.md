---
doc_id: site-shell-runtime
title: "Site Shell Runtime"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: architecture
sort_order: 20
---

# Site Shell Runtime

This document records the current shared shell around page content and the boundary between public pages, Studio pages, and docs-viewer routes.

Current scope:

- `_layouts/default.html`
- `_includes/nav_item.html`
- `assets/js/theme-toggle.js`
- `docs/index.md`
- `library/index.md`
- `_includes/docs_viewer_shell.html`

## Default Layout Responsibilities

`_layouts/default.html` owns the shared site shell:

- document `<head>`
- site header and primary navigation
- page content wrapper
- site footer

It is the shared shell for:

- public catalogue pages
- public search
- library docs
- any non-Studio page using the default layout

Studio application pages use `_layouts/studio.html` instead.

## Theme Bootstrap

The tiny theme bootstrap remains inline in the `<head>` of `_layouts/default.html`.

Reason:

- it reads `localStorage.theme`
- it sets `data-theme` on `<html>` before first paint
- this reduces the chance of a visible flash of the wrong theme

This is intentionally different from the rest of the shell JS and should not be moved into an external asset unless the loading behavior is re-evaluated.

## Shared Shell Scripts

The active default-layout runtime lives in shared asset files:

- `assets/js/theme-toggle.js`
  - handles the footer theme toggle control

Reason:

- keeps `_layouts/default.html` smaller
- keeps site-shell behavior easier to edit and review

Notes:

- the current public header does not render a `nav-more` control
- `assets/js/site-nav.js` still exists in the repo, but the current default shell does not depend on it for active navigation behavior

## Shared Asset Versioning

The shared default-layout CSS and JS append a lightweight build-version query token derived from `site.time`.

Current versioned shell assets:

- `assets/css/main.css`
- `assets/js/theme-toggle.js`
- `assets/js/site-nav.js`

Reason:

- reduces stale-cache breakage after local JS or CSS changes
- keeps cache-busting simple without introducing a separate fingerprinting pipeline
- aligns the public shell with the search page’s build-version asset loading

This is intentionally a minimal static-site mechanism, not a content-hash asset pipeline.

## Public And Studio Nav Split

Primary nav items in `_layouts/default.html` are rendered through `_includes/nav_item.html`.

The include centralizes the repeated three-state pattern:

- current page: render a `<span aria-current="page">`
- active section: render an active `<a aria-current="page">`
- inactive item: render a normal `<a>`

Reason:

- removes repeated Liquid branches from the default layout
- keeps current/active/default behavior consistent across top-level nav contexts
- makes future nav changes lower-risk because the rendering contract lives in one include

Current default-layout public nav:

- `works` -> `/series/`
- `library` -> `/library/`

Current public active-state rules:

- `/series/`, `/series/<series_id>/`, and `/moments/<moment_id>/` are treated as part of the `works` section
- `/library/` is treated as the library section
- there is no separate top-level `moments` nav item

Current Studio-context nav inside `_layouts/default.html`:

- `studio` -> `/studio/`
- `series tags` -> `/studio/series-tags/`
- `docs` -> `/docs/?scope=studio&doc=studio`

The default layout switches to that Studio nav when the current page is in Studio docs context.

## Docs Viewer Shell Boundary

Docs routes are scope-owned shells that wrap one shared viewer runtime.

Current route shells:

- `/docs/`
  - Studio docs
  - loads `assets/data/docs/scopes/studio/index.json`
  - enables inline Studio docs search with `assets/data/search/studio/index.json`
- `/library/`
  - library docs
  - loads `assets/data/docs/scopes/library/index.json`
  - enables inline library docs search with `assets/data/search/library/index.json`

Current shared docs-viewer layer:

- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`

The fork/no-fork rule for that shared viewer is documented in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).

## Maintenance Rule

When changing site-shell behavior:

1. Keep the head theme bootstrap inline unless there is a specific reason to revisit first-paint behavior.
2. Keep `_layouts/default.html` responsible for shell structure and section-level nav state, not page-specific application logic.
3. Prefer shared includes when the same nav or viewer-shell pattern appears multiple times.
4. Treat docs route differences as scope-shell composition unless the viewer model itself has changed.
