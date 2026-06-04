---
doc_id: site-shell-runtime
title: Site Shell Runtime
added_date: 2026-03-31
last_updated: 2026-05-29
parent_id: architecture
---
# Site Shell Runtime

This document records the current shared shell around page content and the boundary between public pages, Studio pages, and docs-viewer routes.

Current scope:

- `_layouts/default.html`
- `_includes/nav_item.html`
- `assets/js/theme-toggle.js`
- `assets/js/public-catalogue-runtime.js`
- `library/index.md`
- `analysis/index.md`
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
- analysis docs
- any non-Studio page using the default layout

## Theme Bootstrap

The tiny theme bootstrap remains inline in the `<head>` of `_layouts/default.html`.

- it reads `localStorage.theme`
- it sets `data-theme` on `<html>` before first paint
- this reduces the chance of a visible flash of the wrong theme

This is intentionally different from the rest of the shell JS and should not be moved into an external asset unless the loading behavior is re-evaluated.

## Shared Shell Scripts

The active default-layout runtime lives in shared asset files:

- `assets/js/theme-toggle.js`
  - handles the footer theme toggle control
- `assets/js/public-catalogue-runtime.js`
  - provides shared public catalogue fetch, generated-data URL, normalization, and thumbnail helpers for work, work-detail, and series routes

Reason:

- keeps `_layouts/default.html` smaller
- keeps site-shell behavior easier to edit and review

Notes:

- the current public header does not render a `nav-more` control
- `assets/js/site-nav.js` still exists in the repo, but the current default shell does not depend on it for active navigation behavior

`assets/js/public-catalogue-runtime.js` is route-loaded by the public catalogue layouts rather than by `_layouts/default.html`.
The default shell remains responsible for page chrome; public catalogue routes opt into the helper where their inline bootstraps need generated-data fetches and URL/media helpers.

## Shared Asset Versioning

The shared default-layout CSS and JS append a lightweight build-version query token derived from `site.time`.

Current versioned shell assets:

- `assets/css/main.css`
- `assets/js/theme-toggle.js`
- `assets/js/site-nav.js`
- `assets/js/public-catalogue-runtime.js` when loaded by public catalogue layouts

Reason:

- reduces stale-cache breakage after local JS or CSS changes
- keeps cache-busting simple without introducing a separate fingerprinting pipeline
- aligns the public shell with the search page’s build-version asset loading

This is intentionally a minimal static-site mechanism, not a content-hash asset pipeline.

## Public Nav

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
- `analysis` -> `/analysis/`
- `library` -> `/library/`

Current public active-state rules:

- `/series/`, `/series/<series_id>/`, and `/moments/<moment_id>/` are treated as part of the `works` section
- there is no separate top-level `moments` nav item

## Docs Viewer Shell Boundary

Docs routes are scope-owned shells that wrap one shared viewer runtime.

Current route shells:

- `/docs/`
  - Studio docs
  - loads `docs-viewer/generated/docs/studio/index.json`
  - enables inline Studio docs search with `docs-viewer/generated/search/studio/index.json`
- `/analysis/`
  - analysis docs
  - loads `assets/data/docs/scopes/analysis/index.json`
  - enables inline analysis docs search with `assets/data/search/analysis/index.json`
- `/library/`
  - library docs
  - loads `assets/data/docs/scopes/library/index.json`
  - enables inline library docs search with `assets/data/search/library/index.json`

Current shared docs-viewer layer:

- `_includes/docs_viewer_shell.html`
- `docs-viewer/runtime/js/docs-viewer-public.js`
- `docs-viewer/runtime/js/docs-viewer-manage.js`

The fork/no-fork rule for that shared viewer is documented in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).
