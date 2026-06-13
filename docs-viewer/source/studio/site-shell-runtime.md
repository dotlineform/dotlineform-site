---
doc_id: site-shell-runtime
title: Site Shell Runtime
added_date: 2026-03-31
last_updated: 2026-06-13
parent_id: architecture
---
# Site Shell Runtime

This document records the current shared shell around page content and the boundary between public pages, Studio pages, and docs-viewer routes.

Current scope:

- tracked public route HTML under `site/`
- `docs-viewer/templates/public-route/index.html`
- `site/assets/js/theme-toggle.js`
- `site/assets/js/site-nav.js`
- `site/assets/js/public-catalogue-runtime.js`
- `site/library/index.html`
- `site/analysis/index.html`

## Public Static Shell Responsibilities

Tracked public route HTML under `site/` owns the shared public site shell:

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

The tiny theme bootstrap remains inline in public route `<head>` markup.

- it reads `localStorage.theme`
- it sets `data-theme` on `<html>` before first paint
- this reduces the chance of a visible flash of the wrong theme

This is intentionally different from the rest of the shell JS and should not be moved into an external asset unless the loading behavior is re-evaluated.

## Shared Shell Scripts

The active public shell runtime lives in shared asset files:

- `site/assets/js/theme-toggle.js`
  - handles the footer theme toggle control
- `site/assets/js/public-catalogue-runtime.js`
  - provides shared public catalogue fetch, generated-data URL, normalization, and thumbnail helpers for work, work-detail, and series routes

Reason:

- keeps `_layouts/default.html` smaller
- keeps site-shell behavior easier to edit and review

Notes:

- the current public header does not render a `nav-more` control
- `site/assets/js/site-nav.js` is loaded by current public route shells for shared navigation behavior

`site/assets/js/public-catalogue-runtime.js` is route-loaded by the public catalogue layouts rather than by `_layouts/default.html`.
The default shell remains responsible for page chrome; public catalogue routes opt into the helper where their inline bootstraps need generated-data fetches and URL/media helpers.

## Shared Asset Versioning

The shared public CSS and JS append a lightweight static query token.

Current versioned shell assets:

- `site/assets/css/main.css`
- `site/assets/js/theme-toggle.js`
- `site/assets/js/site-nav.js`
- `site/assets/js/public-catalogue-runtime.js` when loaded by public catalogue layouts

Reason:

- reduces stale-cache breakage after local JS or CSS changes
- keeps cache-busting simple without introducing a separate fingerprinting pipeline
- keeps the public shell independent of a deploy-time build process

This is intentionally a minimal static-site mechanism, not a content-hash asset pipeline.

## Public Nav

Primary nav items are static markup in tracked public route shells.
Shared navigation behavior lives in `site/assets/js/site-nav.js`.

Current default-layout public nav:

- `works` -> `/series/`
- `analysis` -> `/analysis/`
- `library` -> `/library/`

Current public active-state rules:

- `/series/`, `/series/?series=<series_id>`, `/moments/`, and `/moments/?moment=<moment_id>` are treated as part of the `works` section
- there is no separate top-level `moments` nav item

## Docs Viewer Shell Boundary

Docs routes are scope-owned shells that wrap one shared viewer runtime.

Current route shells:

- `/docs/`
  - Studio docs
  - loads `docs-viewer/generated/docs/studio/index-tree.json`
  - enables inline Studio docs search with `docs-viewer/generated/search/studio/index.json`
- `/analysis/`
  - analysis docs
  - loads `site/assets/data/docs/scopes/analysis/index-tree.json`
  - enables inline analysis docs search with `site/assets/data/search/analysis/index.json`
- `/library/`
  - library docs
  - loads `site/assets/data/docs/scopes/library/index-tree.json`
  - enables inline library docs search with `site/assets/data/search/library/index.json`

Current shared docs-viewer layer:

- `docs-viewer/templates/public-route/index.html` for new public route shell creation
- `site/docs-viewer/runtime/js/public/docs-viewer-public.js`
- `docs-viewer/runtime/js/management/docs-viewer-manage.js`

The fork/no-fork rule for that shared viewer is documented in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).
