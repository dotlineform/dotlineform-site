---
doc_id: config-studio-config-js
title: Studio Config Loader JS
added_date: 2026-04-01
last_updated: 2026-05-30
parent_id: config
viewable: true
---
# Studio Config Loader JS

Config module:

- `assets/studio/js/studio-config.js`

## Scope

`studio-config.js` is the shared browser-side loader and accessor layer for `assets/studio/data/studio_config.json` and Studio scoped UI-text bundles.
Analytics/Data Sharing pages use `analytics-app/app/frontend/js/analytics-config.js` with `analytics-app/app/frontend/config/analytics-config.json` instead of this Studio config surface.

It is configuration code rather than a route controller. Its job is to fetch the bootstrap config once, merge defaults, resolve site-relative paths, load route-owned text bundles on demand, and expose stable helpers to the rest of the Studio browser runtime.

## What calls it

Current direct importers include:

- `assets/studio/js/studio-works.js`
- `assets/studio/js/activity.js`

Its exported helpers are also used indirectly through:

- `assets/studio/js/studio-data.js`

## When it runs

- when a Studio page imports the module during page boot
- when `loadStudioConfig()` is first called on that page
- when a route calls `loadStudioConfigWithText(...)` or `loadScopedStudioText(...)`
- when accessor helpers such as `getStudioRoute(...)` or `getStudioUiTextPath(...)` are used after config load

## Current responsibilities

Current responsibilities include:

- fetching `studio_config.json`
- merging file values with built-in defaults
- fetching scoped UI-text bundles with route-level caching
- resolving root-relative paths against the current site base path
- exposing accessors for:
  - Studio data paths
  - shared site data paths
  - generated docs-scope data paths
  - search scope index paths
  - search policy path
  - scoped UI-text bundle paths
  - Studio route paths
  - Studio UI text from loaded scoped bundles
- exposing Studio-owned config-backed accessors used by current Studio routes

Analysis tag metric and RAG scoring now lives in `analytics-app/app/frontend/js/analysis-tag-scoring.js`.
The Analytics config loader reads analysis policy for that runtime; the Studio config loader no longer owns or exposes Analytics scoring behavior.

## Current boundaries

What stays here:

- defaulting and path-resolution logic shared by multiple browser modules
- reusable config accessors
- scoped UI-text loading, route-level caching, and fallback warnings
- shared config-backed Studio route accessors

What does not stay here:

- Analytics tag metric and RAG scoring
  that lives in `analytics-app/app/frontend/js/analysis-tag-scoring.js`
- dedicated `/catalogue/search/` policy parsing
  that lives in `assets/js/search/search-policy.js`
- local write transport
  that lives in `assets/studio/js/studio-transport.js`
- page-specific DOM/event logic
  that stays in the page controllers
