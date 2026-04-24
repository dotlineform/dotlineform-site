---
doc_id: config-studio-config-js
title: "Studio Config Loader JS"
added_date: 2026-04-01
last_updated: 2026-04-01
parent_id: config
sort_order: 40
---

# Studio Config Loader JS

Config module:

- `assets/studio/js/studio-config.js`

## Scope

`studio-config.js` is the shared browser-side loader and accessor layer for `assets/studio/data/studio_config.json`.

It is configuration code rather than a route controller. Its job is to fetch the config once, merge defaults, resolve site-relative paths, and expose stable helpers to the rest of the browser runtime.

## What calls it

Current direct importers include:

- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-studio-index.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/studio-works.js`
- `assets/studio/js/build-activity.js`
- `assets/js/search/search-page.js`

Its exported helpers are also used indirectly through:

- `assets/studio/js/studio-data.js`

## When it runs

- when a Studio page or the dedicated `/search/` page imports the module during page boot
- when `loadStudioConfig()` is first called on that page
- when accessor helpers such as `getStudioRoute(...)` or `getSearchPolicyPath(...)` are used after config load

## Current responsibilities

Current responsibilities include:

- fetching `studio_config.json`
- merging file values with built-in defaults
- resolving root-relative paths against the current site base path
- exposing accessors for:
  - Studio data paths
  - shared site data paths
  - search scope index paths
  - search policy path
  - Studio route paths
  - Studio UI text
- computing current Studio tag metrics and RAG state from config-backed rules

## Current boundaries

What stays here:

- defaulting and path-resolution logic shared by multiple browser modules
- reusable config accessors
- shared config-backed Studio analysis helpers

What does not stay here:

- dedicated `/search/` policy parsing
  that lives in `assets/js/search/search-policy.js`
- local write transport
  that lives in `assets/studio/js/studio-transport.js`
- page-specific DOM/event logic
  that stays in the page controllers
