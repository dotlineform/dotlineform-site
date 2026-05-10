---
doc_id: site-request-js-config-structural-review-module-versioning
title: Studio Module Asset Versioning Slice
added_date: 2026-05-10
last_updated: "2026-05-10 13:55"
ui_status: implemented
parent_id: site-request-js-config-structural-review
sort_order: 10
hidden: false
---
# Studio Module Asset Versioning Slice

Status:

- implemented

## Purpose

This child doc tracks the first implementation slice from the [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The goal is to make Studio ES module entry scripts use the same cache-busting contract as the rest of the site runtime.
This is the first priority because it is deterministic, low-risk, and likely to reduce confusing background effects during Studio work after code, config, or generated data changes.

## Problem

The default layout defines an `asset_version` from `site.time`, writes it to the `dlf-asset-version` meta tag, and appends it to shared classic scripts such as `assets/js/site-nav.js` and `assets/js/theme-toggle.js`.
Several Studio modules also read that meta value for dynamic imports.

However, Studio route entry scripts are currently included as unversioned module script tags, for example:

```liquid
<script type="module" src="{{ '/assets/studio/js/catalogue-work-editor.js' | relative_url }}"></script>
```

That means the page shell can be current while a browser reuses a stale route entry module or stale static module graph.
The effect is easy to experience as inconsistent Studio behavior but hard to diagnose as a specific bug.

## Target Ownership

The versioning contract should be owned by the route/template layer, not by individual route controllers.

Owner:

- `_includes/studio_module_script.html`

Route controllers under `assets/studio/js/` should not own their own entry-script cache busting.
They can continue to read the `dlf-asset-version` meta tag for dynamic imports where needed.

## Implementation Notes

This slice added `_includes/studio_module_script.html` and replaced every direct Studio route entry script tag under `studio/**/index.md` with that include.
The include accepts a project-local `src` value, resolves it through `relative_url`, and appends a `site.time`-derived `?v=` query that matches the default layout's asset-version contract.
The Studio ready-state audit now recognizes both direct module script tags and the shared include when checking static and dashboard route shells.

The inventory found Studio route entry scripts only in `studio/**/index.md`.
No public route, Docs Viewer shell, `_layouts/`, or other `_includes/` template was found directly loading `assets/studio/js/*.js` as a module entry script.

Static ES imports remain normal browser module specifiers.
The version query is applied to each route entry module; deeper static imports are not rewritten in this slice because no route behavior change is intended and route controllers already use the asset-version meta value for dynamic imports where that contract exists.

Browser smoke testing confirmed `/studio/` and `/studio/catalogue-status/` both request their entry modules with `?v=...` and reach `data-studio-ready="true"`.
The same smoke test confirmed static imports such as `studio-route-state.js` remain unversioned, so follow-up dynamic-import wrapping should be considered only if stale imported dependencies remain a practical problem after entry-module versioning.

## Implementation Tasks

1. Inventory all Studio module entry script tags.
   - Search `studio/`, `_layouts/`, and `_includes/` for `type="module"` references to `assets/studio/js/`.
   - Confirm whether any public route or Docs Viewer shell also loads Studio modules directly.

2. Add a shared include or template helper for Studio module scripts.
   - Input should be the project-local asset path, such as `/assets/studio/js/catalogue-work-editor.js`.
   - Output should append `?v={{ asset_version }}` or an equivalent `site.time`-derived value.
   - Keep the helper machine-agnostic and Jekyll-native.

3. Replace route-local Studio module script tags with the shared helper.
   - Keep each route loading the same entry module it loads today.
   - Do not change module import paths or route behavior in this slice.

4. Check static import behavior in a browser smoke test.
   - Open one static Studio route that uses `studio-static-route.js`.
   - Open one async/data-backed Studio route such as Catalogue Status, Studio Works, or Catalogue Work.
   - Verify the entry module request includes the asset-version query.
   - Verify route ready/busy state still reaches the expected loaded state.

5. Decide whether static module imports need additional handling.
   - If the browser loads the entry script with `?v=...` but static imports remain unversioned in the network graph, document that residual risk.
   - Only add more complex dynamic-import wrapping if the smoke test shows a real stale-import problem that cannot be solved by entry-module versioning alone.

6. Update docs if the route/template contract changes.
   - Update the relevant Studio runtime or UI docs if a new include becomes the standard way to load Studio route modules.
   - A site change-log entry is appropriate if the implementation changes the Studio route-loading contract across many pages.

## Acceptance Checks

- every Studio route entry script under `studio/**/index.md` that loads `assets/studio/js/*.js` uses the shared versioned include or equivalent shared pattern
- no route entry module path changes except adding the asset-version query
- representative static Studio route loads and reaches ready state
- representative async Studio route loads and reaches ready state
- network or DOM inspection confirms the entry module URL includes the version query
- `./scripts/build_docs.rb --scope studio --write` is run if docs are changed
- `./scripts/build_search.rb --scope studio --write` is run if Studio docs search output changes

## Benefits

- reduces stale Studio JavaScript after local builds or deploys
- makes Studio route script loading consistent with the default layout's classic scripts
- keeps cache-busting out of route controller code
- creates a small, safe first slice before larger Docs Viewer, catalogue editor, or config ownership work

## Risks

- adding a shared include touches many route files, so the diff can be broad even though behavior is narrow
- if static ES module imports remain unversioned, this slice may only partially solve stale module graphs
- changing script tags across many Studio pages requires at least one static and one async browser smoke test

## Out Of Scope

- no bundler, transpiler, or framework introduction
- no route-controller refactor
- no `studio_config.json` split
- no endpoint, payload, or generated-data schema changes
- no broad Studio UI changes beyond script-loading mechanics
