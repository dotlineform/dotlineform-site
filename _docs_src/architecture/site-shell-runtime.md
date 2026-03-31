---
doc_id: site-shell-runtime
title: Site Shell Runtime
last_updated: 2026-03-30
parent_id: architecture
sort_order: 20
---

# Site Shell Runtime

This document records site-level layout/runtime decisions for the shared shell around page content.

Current scope:

- `_layouts/default.html`
- `_includes/nav_item.html`
- `assets/js/site-nav.js`
- `assets/js/theme-toggle.js`

## Default Layout Responsibilities

`_layouts/default.html` owns the shared site shell:

- document `<head>`
- site header and primary navigation
- page content wrapper
- site footer

It should stay lightweight and avoid repeating larger behavior blocks inline unless there is a strong rendering reason.

## Theme Bootstrap

The tiny theme bootstrap remains inline in the `<head>` of `_layouts/default.html`.

Reason:

- it reads `localStorage.theme`
- it sets `data-theme` on `<html>` before first paint
- this reduces the chance of a visible flash of the wrong theme

This is intentionally different from the rest of the shell JS and should not be moved into an external asset unless the loading behavior is re-evaluated.

## Shared Shell Scripts

The non-critical default-layout runtime lives in shared asset files:

- `assets/js/site-nav.js`
  - handles the compact `nav-more` menu open/close behavior
- `assets/js/theme-toggle.js`
  - handles the footer theme toggle control

Reason:

- keeps `_layouts/default.html` smaller
- keeps site-shell behavior easier to edit and review
- avoids repeating larger inline script blocks in generated HTML

This split is for maintainability and code organization. It is not primarily a Jekyll build-time optimization.

## Shared Asset Versioning

The shared default-layout CSS and shell JS currently append a lightweight build-version query token derived from `site.time`.

Current versioned shell assets:

- `assets/css/main.css`
- `assets/js/site-nav.js`
- `assets/js/theme-toggle.js`

Reason:

- reduces stale-cache breakage after local JS or CSS changes
- keeps cache-busting simple without introducing a separate fingerprinting pipeline
- aligns the public shell with the search page’s build-version asset loading

This is intentionally a minimal static-site mechanism, not a content-hash asset pipeline.

## Navigation Rendering

Primary nav items in `_layouts/default.html` are rendered through `_includes/nav_item.html`.

The include centralizes the repeated three-state pattern:

- current page: render a `<span aria-current="page">`
- active section: render an active `<a aria-current="page">`
- inactive item: render a normal `<a>`

Reason:

- removes repeated Liquid branches from the default layout
- keeps current/active/default behavior consistent across top-level nav contexts
- makes future nav changes lower-risk because the rendering contract lives in one include

Current browsing-nav rule:

- the public top-level browsing nav exposes only `works`
- moment detail routes under `/moments/<moment_id>/` are treated as part of the `works` browsing section for active-nav state
- there is no separate top-level `moments` nav item or `/moments/` landing-page UI

## Maintenance Rule

When changing site-shell behavior:

1. Keep the head theme bootstrap inline unless there is a specific reason to revisit first-paint behavior.
2. Prefer shared JS assets for larger interactive shell behavior.
3. Prefer shared includes when the same nav/state rendering pattern appears multiple times in the layout.
