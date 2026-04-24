---
doc_id: search-change-log
title: "Search Change Log"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: search
sort_order: 1010
---

# Search Change Log

## [2026-04-24] Aligned Docs Viewer search result metadata across docs scopes

**Status:** implemented

**Area:** docs-domain search UI

**Summary:**
Updated the shared Docs Viewer result renderer so `/docs/` and `/library/` search results use the same title-plus-metadata pattern.

**Reason:**
Library search results were still showing `doc_id` as a visible second line, while Studio docs search presented the more useful `date • parent` metadata pattern. The two routes share the same Docs Viewer runtime, so the presentation contract should be consistent.

**Effect:**
Docs Viewer search results now omit the visible `doc_id` line and show muted metadata from `display_meta`, which is `date` or `date • parent` when available. The new recently-added view uses the same result shape.

**Affected files/docs:**
- `assets/js/docs-viewer.js`
- `_includes/docs_viewer_shell.html`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)

## [2026-04-22] Made `dev-studio` startup docs-search rebuilds opt-in

**Status:** implemented

**Area:** docs-domain search build flow

**Summary:**  
Updated `bin/dev-studio` so startup docs-search rebuilds now run only for scopes explicitly listed in `DOCS_STARTUP_REBUILD_SCOPES`.

**Reason:**  
The Docs Live Rebuild Watcher is now the normal same-scope live-sync path while the runner is active, so startup docs-search refreshes should be explicit rather than an implicit default for one scope.

**Effect:**  
`bin/dev-studio` now skips startup docs-search rebuilds unless `DOCS_STARTUP_REBUILD_SCOPES` includes `studio`, `library`, or both scopes. While the runner is active, watcher-driven same-scope docs-search rebuilds continue to keep `studio` and `library` search aligned with source edits.

**Affected files/docs:**  
- `bin/dev-studio`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## [2026-04-22] Removed the reserved `_archive` docs node from docs-viewer search results

**Status:** implemented

**Area:** docs-domain search payload

**Summary:**  
Updated the docs search builder so it no longer emits a docs-search entry for the reserved `_archive` node.

**Reason:**  
`_archive` remains a meaningful reserved `doc_id` in the viewer tree, but it now behaves as a structural section node rather than a loadable document. Leaving it in docs search would keep exposing a target that is not meant to resolve as standalone content.

**Effect:**  
Archived real docs remain searchable, but the Archive bucket itself no longer appears as a docs search result.

**Affected files/docs:**  
- `scripts/build_search.rb`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-23] Added `dev-studio` docs-root watching for same-scope docs-search rebuilds

**Status:** implemented

**Area:** docs-domain search build flow

**Summary:**  
Updated `bin/dev-studio` so it now performs a startup `studio` docs-search rebuild and starts a local watcher that rebuilds same-scope docs search when `_docs_src/*.md` or `_docs_library_src/*.md` change.

**Reason:**  
Once Task 6 made live docs-management actions rebuild same-scope docs search automatically, the remaining gap was the normal integrated dev runner. Editing docs source files directly while `dev-studio` was already running still relied on the operator to remember a manual docs-search rebuild.

**Effect:**  
While `bin/dev-studio` is running, `_docs_src/*.md` changes now rebuild `studio` docs plus `assets/data/search/studio/index.json`, and `_docs_library_src/*.md` changes rebuild `library` docs plus `assets/data/search/library/index.json`. Manual low-level commands remain available as fallback tooling.

**Affected files/docs:**  
- `bin/dev-studio`
- `scripts/docs/docs_live_rebuild_watcher.py`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)

## [2026-04-22] Aligned live docs-management writes with same-scope docs-search rebuilds

**Status:** implemented

**Area:** docs-domain search build flow

**Summary:**  
Updated the local docs-management flow so successful docs writes now rebuild same-scope docs search consistently, and deprecated the older Studio tag-server `/build-docs` path from the live docs workflow.

**Reason:**  
The docs viewer and docs search are separate generated artifacts, but live docs-management actions should not leave them out of sync or depend on the operator remembering a second rebuild step.

**Effect:**  
Docs create, move, archive, delete, metadata edit, and explicit docs rebuild actions now keep the current scope's docs-viewer payloads and docs-search artifact aligned through the docs-management service. Low-level manual commands remain split as `build_docs.rb` and `build_search.rb`.

**Affected files/docs:**  
- `scripts/docs/docs_management_server.py`
- `scripts/studio/tag_write_server.py`
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

## [2026-03-30] Removed dormant docs-domain branches from the dedicated `/search/` implementation

**Status:** implemented

**Area:** cleanup

**Summary:**  
Removed doc-specific labels, scoring branches, and disabled docs-domain scope entries from the dedicated `/search/` runtime and policy so the standalone search page now reflects its actual catalogue-only role.

**Reason:**  
After Studio and Library search both moved inline into the docs viewer, the dedicated search page no longer needed to carry dormant docs-domain behavior or future-scope fallback entries.

**Effect:**  
`/search/` now has a simpler catalogue-only runtime contract, the shared search policy only defines the live dedicated-page scope, and stale docs-domain branches no longer need to be reasoned about when changing the standalone search page.

**Affected files/docs:**  
- `assets/js/search/search-page.js`
- `assets/js/search/search-policy.js`
- `assets/data/search/policy.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

**Notes:**  
This does not remove the broader scope vocabulary from the architecture docs. It only removes dormant docs-domain behavior from the dedicated search-page implementation.

## [2026-03-30] Added inline Library docs search and extended the docs-scope search builder

**Status:** implemented

**Area:** UI

**Summary:**  
Added a library search artifact, wired `/library/` into the shared inline docs-viewer search flow, and extended the search-owned docs builder so both docs scopes now generate their own search indexes.

**Reason:**  
Once Studio docs search moved inline, leaving Library on a different pattern would have left the docs viewer/search architecture inconsistent across the two docs-domain scopes.

**Effect:**  
`/library/` now exposes the same inline search pattern as `/docs/`, `scripts/build_search.rb` supports both `studio` and `library`, and the dedicated `/search/` page remains catalogue-only.

**Affected files/docs:**  
- `library/index.md`
- `scripts/build_search.rb`
- `assets/data/search/library/index.json`
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)

**Notes:**  
This change is mainly architectural cleanup for consistency. With one Library doc, the immediate user-facing value is low, but it keeps the docs-domain search pattern aligned before Library grows.

## [2026-03-30] Moved Studio docs search inline into `/docs/` and returned `/search/` to catalogue-only

**Status:** implemented

**Area:** UI

**Summary:**  
Removed the `/docs/` link-out to `/search/?scope=studio`, added always-visible inline search inside the docs viewer, and disabled `studio` on the dedicated `/search/` page so catalogue search and docs-domain search now use different UI surfaces.

**Reason:**  
For Studio docs, inline search is a better fit than a separate page because the sidebar remains active and the search results can replace only the right content pane without losing context. The dedicated `/search/` page remains the right fit for the catalogue.

**Effect:**  
`/docs/` now owns Studio docs search directly, `assets/js/docs-viewer.js` lazily loads `assets/data/search/studio/index.json` when `q` is present, and `/search/` is once again the dedicated catalogue search surface.

**Affected files/docs:**  
- `_includes/docs_viewer_shell.html`
- `docs/index.md`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- `assets/data/search/policy.json`
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)

**Notes:**  
This change intentionally removes the transitional dual-UI state for Studio search. The dedicated `/search/` page now documents and serves the catalogue scope only.

## [2026-03-30] Enabled public `scope=studio` search and added the Studio docs search entry point

**Status:** implemented

**Area:** UI

**Summary:**  
Enabled the `studio` search scope in policy, added a search icon CTA to `/docs/`, and extended the shared search runtime so Studio docs records render and rank correctly in the public search shell.

**Reason:**  
The first Studio search artifact already existed, so the next step was to expose it through the same scope-led `/search/` route model already used by `catalogue`.

**Effect:**  
`/search/?scope=studio` now loads a live Studio docs search index, the docs page provides the scope-owned CTA, and the search page returns to `/docs/` via the scope-driven back link.

**Affected files/docs:**  
- `_includes/docs_viewer_shell.html`
- `docs/index.md`
- `assets/data/search/policy.json`
- `assets/js/search/search-page.js`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

**Notes:**  
This change enables Studio docs search only. It does not add `library` search or change the long-term search-pipeline ownership model.

## [2026-03-30] Added the first search-owned builder entrypoint and generated the Studio search artifact

**Status:** implemented

**Area:** build

**Summary:**  
Added a new search-owned Ruby builder entrypoint for non-catalogue scopes and used it to emit the first `studio` search artifact from published Studio docs outputs.

**Reason:**  
Studio search needed a concrete first implementation step that moves search ownership toward a dedicated pipeline without forcing a full refactor of either the catalogue generator or the docs builder first.

**Effect:**  
The repo now has `scripts/build_search.rb` as a search-owned build entrypoint, `assets/data/search/studio/index.json` can be generated from `assets/data/docs/scopes/studio/index.json`, and the Studio v1 record shape plus locked rollout decisions are now explicitly documented. Public `scope=studio` search remains disabled for now.

**Affected files/docs:**  
- `scripts/build_search.rb`
- `assets/data/search/studio/index.json`
- [Search Studio V1 Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This is a first search-owned build step, not the full standalone end-state pipeline yet.

## [2026-03-30] Documented the target search-pipeline ownership model and the proposed Studio v1 record shape

**Status:** implemented

**Area:** architecture

**Summary:**  
Added one doc describing the intended end-state where search owns its own pipeline and consumes canonical outputs from content systems, plus a second doc defining the proposed normalized record shape for `scope=studio` and how that first Studio rollout fits into the wider plan.

**Reason:**  
The next search scope will likely have a different upstream schema and different ranking needs from `catalogue`. The repo needed an explicit architectural guardrail so Studio search can ship pragmatically without making the generator or docs builder the conceptual owner of search.

**Effect:**  
Search now has a documented ownership boundary for the full subsystem and a concrete proposal for how Studio v1 should read canonical docs outputs through a search-owned adapter while still fitting the shared `/search/` shell.

**Affected files/docs:**  
- `_docs_src/search-pipeline-target-architecture.md`
- [Search Studio V1 Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Search](/docs/?scope=studio&doc=search)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- `_docs_src/search-config-architecture.md`
- `_docs_src/search-config-implementation-note.md`

**Notes:**  
This is a documentation decision only. It does not yet implement Studio search indexing or a standalone search build script.

## [2026-03-30] Added a scope-aware runtime policy layer for the public search shell

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated runtime search-policy artifact, pointed shared config at it, and refactored the public search page to validate `scope` against policy before loading any scope-owned index.

**Reason:**  
The public search route already uses explicit `scope`, but the runtime still hardcoded `catalogue` and several shell-level behavior values. That needed to be corrected before `scope=studio` is added so the shared `/search/` page becomes properly scope-native first.

**Effect:**  
`/search/?scope=catalogue` still works as before, but the shell now reads debounce, batching, scope labels, back-link routing, and scope enablement from `assets/data/search/policy.json`. `studio` and `library` now resolve to explicit unsupported-scope states instead of falling through to a broken fetch, and missing-scope behavior is now part of the same policy-led shell contract.

**Affected files/docs:**  
- `assets/data/search/policy.json`
- `assets/js/search/search-policy.js`
- `assets/js/search/search-page.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `_docs_src/search-config-implementation-note.md`
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

**Notes:**  
This phase does not add a Studio search index yet. Ranking logic and build-time entry generation remain in code.

## [2026-03-30] Added build-version cache busting to the public search runtime and data fetches

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a lightweight build-version query token to the public search module URL, the search page’s shared module imports, and the config/data fetch URLs used by the current `catalogue` scope.

**Reason:**  
The recent public-route and module-path changes exposed stale browser-cache failures during local review. Search needed a small cache-busting mechanism before further scope expansion.

**Effect:**  
`/search/?scope=catalogue` now reloads the renamed search runtime and its scope-owned JSON data more reliably after rebuilds, without introducing a separate asset fingerprint pipeline.

**Affected files/docs:**  
- `search/index.md`
- `assets/js/search/search-page.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/studio-data.js`
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)

**Notes:**  
This is a pragmatic build-version layer for the current static-site workflow. It does not change search ranking, scope rules, or index schema.

## [2026-03-30] Renamed the public search module and moved the catalogue search index into a scoped data path

**Status:** implemented

**Area:** architecture

**Summary:**  
Renamed the public search runtime module from the Studio-owned `assets/studio/js/studio-search.js` path to `assets/js/search/search-page.js`, and moved the current catalogue search artifact from `assets/data/search_index.json` to `assets/data/search/catalogue/index.json`.

**Reason:**  
The public search runtime is no longer a Studio page concern, and the search data contract needs to scale from one catalogue index to multiple scope-owned artifacts such as `catalogue`, `library`, and `studio`.

**Effect:**  
The search page now loads a top-level public search module, the current `catalogue` scope reads from a scope-owned JSON path, the config structure now supports search data paths by scope, and the generator default output path for the catalogue search artifact matches that new structure.

**Affected files/docs:**  
- `assets/js/search/search-page.js`
- `assets/studio/js/studio-data.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- `assets/data/search/catalogue/index.json`
- `scripts/generate_work_pages.py`
- `search/index.md`
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- `_docs_src/search-config-architecture.md`

**Notes:**  
This change introduces the scoped search-data convention now, before additional scopes are implemented. The current runtime still only accepts `scope=catalogue`.

## [2026-03-30] Replaced the public search heading with a scope-driven back link

**Status:** implemented

**Area:** UI

**Summary:**  
Replaced the static `search` heading on the public search page with a scope-resolved back link. The current `catalogue` scope now renders `← works` and returns to `/series/`.

**Reason:**  
The public search page should make it easy to return to the page that owns the active search scope, rather than showing a generic heading with no clear return path.

**Effect:**  
The search header now resolves its left-side link from scope context, the current `catalogue` scope returns to `/series/`, future scopes can map to their own owning pages, and the link is hidden when the page loads without valid scope context.

**Affected files/docs:**  
- `search/index.md`
- `assets/css/main.css`
- `assets/studio/js/studio-search.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

**Notes:**  
This is a header-navigation change only. It does not change search indexing, ranking, or scope validation rules.

## [2026-03-30] Moved catalogue search to the public `/search/` page and removed the Studio route

**Status:** implemented

**Area:** UI

**Summary:**  
Moved the current catalogue search page from `/studio/search/` to the public `/search/` route, removed the Studio page entirely, and added a catalogue search entry point to the `/series/` toolbar.

**Reason:**  
The agreed search contract now uses one public top-level search route with explicit scope context. Search needed to move out of Studio before later scope expansion so the public UI, route vocabulary, and entry-point model all align.

**Effect:**  
`/search/?scope=catalogue` is now the current public route, `/studio/search/` no longer exists, the `/series/` toolbar now includes a search CTA for the catalogue scope, and the public search page shows explicit scope context while continuing to use the same in-memory catalogue search runtime.

**Affected files/docs:**  
- `search/index.md`
- `studio/search/index.md`
- `series/index.md`
- `assets/css/main.css`
- `assets/studio/js/studio-search.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Search](/docs/?scope=studio&doc=search)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)

**Notes:**  
The runtime is still the same shared search module and still only supports the `catalogue` scope. This change is route and entry-point migration, not the later modular multi-domain refactor.

## [2026-03-30] Removed visible kind filters from the Studio search page and required scope context

**Status:** implemented

**Area:** UI

**Summary:**  
Updated the current Studio search page so it always searches across all indexed catalogue kinds, no longer exposes the `all` / `works` / `series` / `moments` filter buttons, and requires a valid `scope` URL parameter before the page becomes usable.

**Reason:**  
The search UI needs to align with the newer scope-led public-search direction before the route moves out of Studio. Exposing per-kind buttons no longer matches that direction, while a required URL scope makes the page behavior closer to the future public contract.

**Effect:**  
`/studio/search/?scope=catalogue` is now the valid Studio route, the visible filter row is gone, catalogue search remains internally mixed across works, series, and moments, and loading the page without a valid scope now shows a missing-context message instead of an ambiguous fallback search UI.

**Affected files/docs:**  
- `studio/search/index.md`
- `assets/studio/js/studio-search.js`
- `assets/studio/data/studio_config.json`
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)

**Notes:**  
This change intentionally does not remove the underlying internal support for per-kind filtering from the search runtime; it only removes that granularity from the current UI.

## [2026-03-30] Defined the public search route and scope-led UI contract

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated public-search contract doc that defines `/search/` as the shared public route, uses `scope` plus `q` as the URL contract, and establishes scope-owned page CTAs as the preferred public entry model.

**Reason:**  
Search is about to grow beyond the current Studio-first catalogue scope. The public route and UI model needed to be clarified before a larger modular refactor adds domain-specific search artifacts and policy/config.

**Effect:**  
The search docs now explicitly prefer a scope-led public model such as `/search/?scope=catalogue&q=...`, reserve future scope names such as `studio` and `library`, and avoid an ambiguous top-level public nav item called `search` as the default interaction pattern.

**Affected files/docs:**  
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search](/docs/?scope=studio&doc=search)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

**Notes:**  
This is a documentation-level contract decision. The public `/search/` route and the modular domain search architecture are not implemented yet.

## [2026-03-29] Added a concrete staged implementation note for search config extraction

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a focused implementation note that turns the search config architecture direction into a concrete phase sequence, beginning with runtime UI policy extraction and deferring ranking and field policy to later stages.

**Reason:**  
The architecture doc defined the boundary, but the next implementation step still needed a concrete shape in code terms so the config change can be reviewed and executed without ambiguity.

**Effect:**  
Search config work now has a documented first cut, a proposed `search_policy.json` shape, and a clearer roadmap for later phases such as ranking bands, field participation, and shared runtime/build policy.

**Affected files/docs:**  
- `_docs_src/search-config-architecture.md`
- `_docs_src/search-config-implementation-note.md`
- [Search](/docs/?scope=studio&doc=search)

**Notes:**  
This remains a documentation-level implementation plan; the config layer itself is not yet implemented.

## [2026-03-29] Normalized published search-doc references to docs-viewer links

**Status:** implemented

**Area:** architecture

**Summary:**  
Converted published-doc references across the search document set to use `/docs/?scope=studio&doc=...` links instead of raw filenames or legacy doc paths.

**Reason:**  
Search docs are now intended to be read through the docs viewer as a linked system. Raw filenames were inconsistent with that review flow and made navigation less direct.

**Effect:**  
Readers can now move between published search docs through stable viewer links, while non-doc file paths and unpublished docs remain explicit as plain repo references.

**Affected files/docs:**  
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
- `_docs_src/search-config-architecture.md`
- [Search Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)

**Notes:**  
This is a documentation-navigation change only; it does not alter search behaviour or schema.

## [2026-03-29] Reviewed and split the search document set into focused implementation docs

**Status:** implemented

**Area:** architecture

**Summary:**  
Replaced the earlier broad v1 planning-only search notes with a focused documentation set covering overview, schema, field policy, normalization, ranking, UI behaviour, build pipeline, validation, config architecture, and change-log maintenance.

**Reason:**  
The search system had moved beyond a single planning note. Review and future changes required smaller documents tied directly to the implemented v1 behaviour.

**Effect:**  
Search can now be reviewed one concern at a time, and future implementation changes have a clearer documentation surface to update alongside code.

**Affected files/docs:**  
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
- `_docs_src/search-config-architecture.md`
- [Search Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)

**Notes:**  
This documentation split is now part of the review surface for future search work and should be maintained alongside implementation changes.

## [2026-03-29] Defined the search config externalisation boundary and recommended staged adoption

**Status:** proposed

**Area:** architecture

**Summary:**  
Defined a structural direction for search policy externalisation: keep `studio_config.json` narrow, introduce a dedicated `search_policy.json`, and externalize runtime UI behaviour before ranking bands and field activation policy.

**Reason:**  
Search already has its own artifact, UI surface, and review docs. Config boundaries should be set before the next growth phase adds more fields, filters, and prose-related complexity.

**Effect:**  
Provides a clear basis for the next structural implementation step without prematurely externalizing all search logic.

**Affected files/docs:**  
- `_docs_src/search-config-architecture.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`

**Notes:**  
This is a documented direction, not yet an implemented config layer.

## [2026-03-29] Added batched result expansion to the Studio search UI

**Status:** implemented

**Area:** UI

**Summary:**  
Changed the Studio search page to render results in batches of `50` and reveal additional results with a `more` control instead of showing only a fixed hard cap.

**Reason:**  
The original result cap hid lower-ranked matches with no way to inspect more of the ranked set. Incremental expansion keeps the DOM lighter while preserving access to additional results.

**Effect:**  
Large result sets remain performant and readable, and the user can inspect more results without changing query or filter state.

**Affected files/docs:**  
- `assets/studio/js/studio-search.js`
- `studio/search/index.md`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

**Notes:**  
The initial implementation had a runtime bug from an obsolete constant; that was fixed immediately in the same development phase and the current behaviour is the corrected batched model.

## [2026-03-29] Implemented Studio-first search with a generated base search index

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Implemented v1 Studio search backed by a generated `assets/data/search_index.json` artifact and an in-memory client-side search runtime for works, series, and moments.

**Reason:**  
Search needed a simple but scalable in-house implementation that avoided external services and fit the existing static-site pipeline.

**Effect:**  
The site now has a working Studio-first search surface with deterministic ranking, build-time-generated search data, kind filtering, and a path toward later field and prose expansion.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `assets/data/search_index.json`
- `assets/studio/js/studio-search.js`
- `studio/search/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-data.js`
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)

**Notes:**  
This implementation keeps search as a dedicated artifact stage inside the existing generator rather than introducing a separate search builder.
