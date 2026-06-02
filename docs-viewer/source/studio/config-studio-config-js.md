---
doc_id: config-studio-config-js
title: Config Loader JS
added_date: 2026-04-01
last_updated: 2026-05-30
parent_id: studio
viewable: true
---
# Studio Config Loader JS

Config module:

- `studio/app/frontend/js/studio-config.js`

## Scope

`studio-config.js` is the shared browser-side loader and accessor layer for the Studio runtime config and Studio scoped UI-text bundles.
The runtime config URL is supplied by `meta[name="dlf-studio-config-url"]`; local Studio currently publishes `/studio/runtime-config.json`.
Analytics/Data Sharing pages use `analytics-app/app/frontend/js/analytics-config.js` with `analytics-app/app/frontend/config/analytics-config.json` instead of this Studio config surface.

It is configuration code rather than a route controller. Its job is to fetch the runtime config once, resolve site-relative paths, load route-owned text bundles on demand, and expose stable helpers to the rest of the Studio browser runtime.

## What calls it

Current direct importers are active Studio frontend modules under `studio/app/frontend/js/`, including `studio-app.js`, route modules, shared data loaders, and navigation helpers.

## When it runs

- when a Studio page imports the module during page boot
- when `loadStudioConfig()` is first called on that page
- when a route calls `loadStudioConfigWithText(...)` or `loadScopedStudioText(...)`
- when accessor helpers such as `getStudioRoute(...)` or `getStudioUiTextPath(...)` are used after config load

## Current responsibilities

Current responsibilities include:

- fetching the configured runtime config JSON
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

The Studio config loader does not publish a fallback copy of the full Studio runtime config or route registry.

## Current boundaries

What stays here:

- small accessor fallbacks and path-resolution logic shared by multiple browser modules
- reusable config accessors
- scoped UI-text loading, route-level caching, and fallback warnings
- shared config-backed Studio route accessors

What does not stay here:

- Analytics tag metric and RAG scoring
  that lives in the Analytics app, not in Studio
- dedicated `/catalogue/search/` policy parsing
  that lives in `assets/js/search/search-policy.js`
- local write transport
  that lives in `assets/studio/js/studio-transport.js`
- page-specific DOM/event logic
  that stays in the page controllers
