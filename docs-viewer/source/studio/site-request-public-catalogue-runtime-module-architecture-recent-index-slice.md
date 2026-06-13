---
doc_id: site-request-public-catalogue-runtime-module-architecture-recent-index-slice
title: Public Catalogue Runtime Recent Index Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Recent Index Route Slice

Status:

- completed

## Purpose

Track the focused `/recent/` route slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Works Index Route Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-works-index-slice).

The `/recent/` shell is now the clearest remaining public-runtime consumer. This slice should migrate `site/assets/js/recent-index.js` into a focused ES module route, remove `/recent/` from `site/assets/js/public-catalogue-runtime.js`, and retire the public runtime if no deploy-root callers remain.

## Steer

- Treat current `site/assets/js/recent-index.js` behavior as the behavior reference.
- Preserve current DOM IDs and CSS classes:
  - `recentIndexRoot`;
  - `recentIndexList`;
  - `recentIndexEmpty`;
  - `.recentIndexItem`;
  - `.recentIndexItem__date`;
  - `.recentIndexItem__img`;
  - `.recentIndexItem__meta`;
  - `.recentIndexItem__title`;
  - `.recentIndexItem__caption`.
- Preserve list data sources:
  - `/assets/data/recent_index.json`;
  - `/assets/data/series_index.json`, optional fallback to an empty object on fetch failure.
- Preserve entry behavior:
  - newest-first sorting by `published_date`, then `recorded_at_utc`, then numeric-aware title;
  - cap rendered entries at 50;
  - render work entries as `/works/?from=recent&work=...`;
  - render series entries as `/series/?series=...&from=recent`;
  - render single-work series entries as `/works/?from=recent&work=...`;
  - keep date formatting as `D mon YYYY`;
  - keep thumbnail and placeholder behavior.
- Remove `public-catalogue-runtime.js` from `site/recent/index.html` after the migrated recent route no longer depends on it.
- Delete `site/assets/js/recent-index.js` after the shell stops loading it.
- Audit remaining deploy-root callers before deleting `site/assets/js/public-catalogue-runtime.js`.
- Do not change generated data schemas, CSS, search runtime, or catalogue route behavior outside `/recent/` and shared URL construction.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for `/recent/`;
- verify `/recent/` no longer loads `public-catalogue-runtime.js` or legacy `recent-index.js`;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 12: Recent Index Route Module

Purpose: migrate `recent-index.js` into a focused ES module route and remove the final public-runtime shell consumer.

Scope:

- inspect current behavior in:
  - `site/assets/js/recent-index.js`;
  - `site/recent/index.html`;
  - `site/assets/js/public-catalogue-runtime.js`;
  - shared helpers under `site/assets/js/catalogue/shared/`;
  - current recent-list CSS in `main.css` only as needed for DOM contract awareness;
- create a focused route module:
  - `site/assets/js/catalogue/routes/recent-index.js`;
- reuse existing shared helpers where they already match behavior:
  - `trimBaseurl`;
  - `catalogueIndexUrl`;
  - `workUrl`;
  - `seriesIndexUrl`;
  - `fetchJson`;
  - text and numeric normalization helpers;
  - thumbnail URL helper;
- add a shared `recentIndexUrl` helper beside the other catalogue data URL helpers;
- port recent-index-specific date formatting, entry sorting, and render helpers locally;
- update `site/recent/index.html` to load the module route and remove the legacy classic script;
- remove `public-catalogue-runtime.js` from `site/recent/index.html` after no remaining `/recent/` script needs it;
- delete `site/assets/js/recent-index.js` after the shell stops loading it;
- audit remaining deploy-root callers and delete `site/assets/js/public-catalogue-runtime.js` if none remain;
- register the new route module in `site-tools/config/site-tools.json`.

Out of scope:

- changing recent index generated data schemas;
- changing visible list markup, visible text, or CSS classes;
- changing recent-index sorting semantics or the 50-entry cap;
- changing selected-work, works-index, series-index, moments, work-detail, or search runtime behavior;
- automated smoke-test maintenance.

## Candidate Module Ownership

- `routes/recent-index.js` owns `/recent/` list boot, data loading, entry sorting, date formatting, entry link projection, and item rendering.
- `shared/catalogue-urls.js` owns recent, series, catalogue, and work URL construction.
- `shared/fetch-json.js` owns JSON fetch response validation.
- `shared/text.js` owns generic text and numeric normalization.
- `shared/thumbnails.js` owns thumbnail URL construction.
- `public-catalogue-runtime.js` should have no deploy-root callers after this slice and may be retired after audit.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 12.1 | completed | Inspect `recent-index.js`, `/recent/` shell script order, public-runtime helper usage, shared helper equivalents, and recent-list CSS contracts. | Confirmed the legacy script owned recent list rendering and only used public-runtime URL/base helpers. |
| 12.2 | completed | Define the recent-index route module contract. | Kept route-specific date/sort/render helpers local; no global compatibility alias. |
| 12.3 | completed | Implement `catalogue/routes/recent-index.js` and shared `recentIndexUrl`. | Ported behavior with shared URL, fetch, text, size, and thumbnail helpers. |
| 12.4 | completed | Update `/recent/` shell script tags. | `/recent/` now loads only the recent-index route module for catalogue behavior. |
| 12.5 | completed | Retire legacy `recent-index.js`, audit public-runtime callers, and update validation config. | Deleted `site/assets/js/recent-index.js` and `site/assets/js/public-catalogue-runtime.js`; no deploy-root callers remain. |
| 12.6 | completed | Verify `/recent/` state and record evidence. | See Completed Verification. |

## Completed Verification

- `node --check site/assets/js/catalogue/routes/recent-index.js`
- `node --check site/assets/js/catalogue/shared/catalogue-urls.js`
- `$HOME/miniconda3/bin/python3 -m json.tool site-tools/config/site-tools.json`
- `bin/site-validate`
- `rg -n "public-catalogue-runtime.js|recent-index.js|__dlfPublicCatalogueRuntime" site site-tools/config/site-tools.json -S`
  - returned only the new `catalogue/routes/recent-index.js` route references in `site/recent/index.html` and `site-tools/config/site-tools.json`;
  - no deploy-root caller references to `site/assets/js/public-catalogue-runtime.js`;
  - no `window.__dlfPublicCatalogueRuntime` references under `site/`.
- Browser check at `http://127.0.0.1:8175/recent/`:
  - route rendered 12 entries;
  - `#recentIndexRoot` was visible and `#recentIndexEmpty` was hidden;
  - first entry rendered `1 apr 2026`, title `simultaneous equations`, caption `2 works`, image `/assets/works/img/01941-thumb-96.webp`, and href `/series/?series=143&from=recent`;
  - single-work series entries rendered work links, for example `forest (2024)` linked to `/works/?from=recent&work=01175`;
  - script list included `recent-index.js`, `site-nav.js`, and `theme-toggle.js`, but not `public-catalogue-runtime.js` or legacy `assets/js/recent-index.js`;
  - `window.__dlfPublicCatalogueRuntime` was absent;
  - browser console error check returned no errors.

## Slice 12 Assessment

- Completed. Recent index behavior now lives in `site/assets/js/catalogue/routes/recent-index.js`.
- `site/assets/js/recent-index.js` is retired and `/recent/` no longer loads `site/assets/js/public-catalogue-runtime.js`.
- `site/assets/js/public-catalogue-runtime.js` is retired after the deploy-root caller audit found no remaining active callers.
- The new module keeps recent-specific date, sort, and render behavior local while reusing shared URL, fetch, text, size, and thumbnail helpers.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | met | Moved the existing route behavior into a focused ES module and reused established shared helpers. |
| Current `recent-index.js` behavior inspected before module contract design | met | Legacy data loading, sorting, date formatting, link projection, thumbnails, placeholders, and shell loading were inspected before implementation. |
| Recent index behavior ported without changing visible list contracts | met | Browser check confirmed rendered entries, title/caption/date/image content, root visibility, and empty-state hiding. |
| Recent entry links remain stable | met | Browser check confirmed series links use `/series/?series=...&from=recent` and work links use `/works/?from=recent&work=...`. |
| Single-work series link behavior remains stable | met | Browser check confirmed `forest (2024)` linked to `/works/?from=recent&work=01175`. |
| Date formatting and sort semantics remain stable | met | Browser check confirmed newest-first first entry and `D mon YYYY` date text such as `1 apr 2026`. |
| Existing recent-list IDs/classes remain stable | met | The route continues to use `recentIndexRoot`, `recentIndexList`, `recentIndexEmpty`, and the existing `recentIndexItem*` classes. |
| `recent-index.js` retired only after route shell stops loading it | met | Removed the shell script tag, added the module route, then deleted `site/assets/js/recent-index.js`. |
| `/recent/` no longer loads `public-catalogue-runtime.js` after migration | met | Browser check confirmed the `/recent/` script list excludes `public-catalogue-runtime.js`. |
| `public-catalogue-runtime.js` removed only after caller audit | met | Deploy-root audit found no active caller references before deleting `site/assets/js/public-catalogue-runtime.js`. |
| Completed slice leaves site functional and deployable | met | Syntax checks and `bin/site-validate` passed. |
| Route module boundary follows target folder structure | met | Added `site/assets/js/catalogue/routes/recent-index.js`. |
| No global compatibility alias introduced | met | The route imports modules directly and does not write a window-level compatibility object. |
| No broad utility bucket introduced | met | Recent-specific date, sort, and render helpers stayed local to the route. |
| Performance rules respected | met | `/recent/` no longer downloads `public-catalogue-runtime.js`; no new data fetches were introduced. |
| Search, if touched, stays structural-only | not touched | Search runtime was not changed. |
| Validation stayed within agreed policy | met | Used syntax checks, site validation, reference audit, and manual browser checks; no automated browser smoke tests. |

## Follow-On

After Slice 12, audit any stale documentation that still describes `public-catalogue-runtime.js` as an active deploy-root runtime before deciding whether to close the parent architecture request.
