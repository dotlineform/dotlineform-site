---
doc_id: site-request-studio-ready-state-contract
title: Studio Ready State Contract Request
added_date: 2026-05-01
last_updated: "2026-05-03 22:38"
ui_status: done
parent_id: change-requests
sort_order: 37
---
# Studio Ready State Contract Request

Status:

- implemented

## Summary

Define a shared readiness contract for Studio pages so browser smoke tests and future automation can wait for stable route state without relying on route-specific status text.

## Reason

Current Studio pages are async-rendered and service-backed. A page may be visible before the active record, lookup payloads, media previews, or list sections have finished rendering.

Codex-run smoke tests can work around this with page-specific waits, but that makes tests more brittle than they need to be. A shared contract would give test code and future Studio scripts a stable signal for "the page is ready for interaction."

## Goals

- expose a route-level ready signal after required data loads and the final initial render completes
- expose a busy signal while route-level save, preview, publish, delete, import, or rebuild actions are in progress
- keep the contract small enough that each Studio page can adopt it incrementally
- let smoke tests wait on stable page state instead of route-specific status text
- preserve existing visible status messages for users

## Non-Goals

- replacing user-facing status text
- defining formal end-to-end QA coverage
- adding a full client-side test framework
- blocking page-specific readiness details where a route has special needs

## Proposed Contract

Each Studio page root should expose shared state attributes:

- `data-studio-ready="false"` while initial route data is loading
- `data-studio-ready="true"` after the route has loaded the data required for normal interaction and completed its initial render
- `data-studio-busy="true"` while a route-level command is running
- omit or set `data-studio-busy="false"` when no route-level command is running

Pages may also expose route-specific detail attributes when useful:

- `data-studio-record-loaded="true"`
- `data-studio-mode="single|bulk|new|import|list|registry|preview|results|confirm|summary|session|edit|dashboard|landing|reference|idle|empty"`
- `data-studio-service="available|unavailable"`

The shared attributes should live on the main route root, such as `#catalogueWorkRoot`, not on a nested panel.

## Current Implementation

Adopted routes:

- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-series/`
- `/studio/catalogue-moment/`
- `/studio/activity/`
- `/studio/bulk-add-work/`
- `/studio/activity/`
- `/studio/catalogue-status/`
- `/studio/catalogue-field-registry/`
- `/studio/docs-broken-links/`
- `/studio/docs-import/`
- `/studio/import/`
- `/studio/audits/`
- `/studio/project-state/`
- `/studio/series-tag-editor/`
- `/studio/series-tags/`
- `/studio/studio-works/`
- `/studio/tag-aliases/`
- `/studio/tag-groups/`
- `/studio/tag-registry/`

Current shared helper:

- `assets/studio/js/studio-route-state.js`

The adopted catalogue editors and service-backed Studio tools now expose shared route attributes on their route roots. Initial route loading keeps `data-studio-ready="false"`, each route switches to `data-studio-ready="true"` after the initial route mode, requested record/import selection, or empty/unavailable state has completed, and command-state updates keep `data-studio-busy` synchronized with save, create, preview, import, audit, report, refresh, publish, unpublish, rebuild, and delete flows.

Static/reference route helper:

- `assets/studio/js/studio-static-route.js`

Enforcement helper:

- `scripts/audit_studio_ready_state.py`

The page also exposes:

- `data-studio-route="catalogue-work|catalogue-work-detail|catalogue-series|catalogue-moment|activity|bulk-add-work|activity|catalogue-status|catalogue-field-registry|docs-broken-links|docs-import|data-import|studio-audits|project-state|series-tag-editor|series-tags|studio-works|tag-aliases|tag-groups|tag-registry|studio-home|studio-catalogue|studio-library|studio-analytics|studio-search|studio-ui-catalogue|studio-ui-catalogue-button|studio-ui-catalogue-input|studio-ui-catalogue-list|studio-ui-catalogue-panel"`
- `data-studio-mode="empty|single|bulk|new|import|list|registry|idle|preview|results|confirm|result|summary|session|edit|dashboard|landing|reference"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

Primary async, service-backed, dashboard, landing, and reference Studio routes have adopted the contract. Dashboard routes mark busy while lightweight metric hydration runs. Landing and UI catalogue routes expose static/reference ready state so future development has an obvious route-root contract to extend.

## Rollout Checklist

Primary async or service-backed Studio routes:

- [x] `/studio/activity/` root `#buildActivityRoot`
- [x] `/studio/bulk-add-work/` root `#bulkAddWorkRoot`
- [x] `/studio/activity/` root `#catalogueActivityRoot`
- [x] `/studio/catalogue-field-registry/` root `#fieldRegistryReviewRoot`
- [x] `/studio/catalogue-moment/` root `#catalogueMomentRoot`
- [x] `/studio/catalogue-series/` root `#catalogueSeriesRoot`
- [x] `/studio/catalogue-status/` root `#catalogueStatusRoot`
- [x] `/studio/catalogue-work-detail/` root `#catalogueWorkDetailRoot`
- [x] `/studio/catalogue-work/` root `#catalogueWorkRoot`
- [x] `/studio/docs-broken-links/` root `#docsBrokenLinksRoot`
- [x] `/studio/docs-import/` root `#docsHtmlImportRoot`
- [x] `/studio/export/` root `#dataExportRoot`
- [x] `/studio/import/` root `#dataImportRoot`
- [x] `/studio/audits/` root `#studioAuditsRoot`
- [x] `/studio/project-state/` root `#projectStateRoot`
- [x] `/studio/series-tag-editor/` root `#seriesTagEditorRoot`
- [x] `/studio/series-tags/` root from `data-role="series-tags"`
- [x] `/studio/studio-works/` root `#worksStudioRoot`
- [x] `/studio/tag-aliases/` root from `data-role="tag-aliases"`
- [x] `/studio/tag-groups/` root from `data-role="tag-groups"`
- [x] `/studio/tag-registry/` root from `data-role="tag-registry"`

Lower-priority dashboard, landing, and reference routes:

- [x] `/studio/` root `#studioHomeRoot`
- [x] `/studio/analytics/` root `#studioAnalyticsDashboardRoot`
- [x] `/studio/catalogue/` root `#studioCatalogueDashboardRoot`
- [x] `/studio/library/` root `#studioLibraryDashboardRoot`
- [x] `/studio/search/` root `#studioSearchDashboardRoot`
- [x] `/studio/ui-catalogue/` root `#studioUiCatalogueRoot`
- [x] `/studio/ui-catalogue/button/` root `#studioUiCatalogueButtonRoot`
- [x] `/studio/ui-catalogue/input/` root `#studioUiCatalogueInputRoot`
- [x] `/studio/ui-catalogue/list/` root `#studioUiCatalogueListRoot`
- [x] `/studio/ui-catalogue/panel/` root `#studioUiCataloguePanelRoot`

These lower-priority routes expose a deliberately small contract. Dashboard pages use the shared dashboard metric loader to mark ready after metric hydration settles. Static landing and reference pages use a generic static-route initializer that immediately marks the route ready after DOM load.

Future async features should extend the contract at the route level. Static-route readiness is only valid while the page is a static or reference shell; if the route adds async data, service checks, route commands, or additional route scripts, replace the static initializer with a route-specific ready/busy implementation and run the ready-state audit in strict mode.

## Event Option

In addition to attributes, each page may dispatch a shared event after readiness changes:

```js
root.dispatchEvent(new CustomEvent("studio:ready", {
  bubbles: true,
  detail: {
    ready: true,
    mode: state.mode || "",
    route: "catalogue-work"
  }
}));
```

The event is helpful for future runtime tools, but smoke tests should primarily depend on attributes because attributes are easy to inspect after the event has already fired.

## Test Harness Impact

After adoption, smoke tests should prefer:

```python
page.wait_for_selector("#catalogueWorkRoot[data-studio-ready='true']")
page.wait_for_function(
    "selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'",
    arg="#catalogueWorkRoot",
)
```

Route-specific status-text waits should become fallback checks rather than the normal readiness contract.

## Rollout Plan

1. Define small shared helpers for setting `data-studio-ready` and `data-studio-busy`.
2. Adopt the attributes on one catalogue editor route first.
3. Update the smoke-test harness guidance in [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing).
4. Roll the contract across the remaining catalogue editors. Completed for work-detail, series, and moment.
5. Extend the contract across operational catalogue and docs-maintenance routes. Current pass completed Studio Activity, Bulk Add Work, Studio Activity, Catalogue Drafts, Catalogue Field Registry, Docs Broken Links, Docs Import, and Project State.
6. Extend the contract across tag tools and Studio Works. Current pass completed Series Tag Editor, Series Tags, Studio Works, Tag Aliases, Tag Groups, and Tag Registry.
7. Extend to lower-priority dashboard, landing, and reference Studio pages. Current pass completed the Studio home, domain dashboards, and UI catalogue reference pages with static or lightweight dashboard ready state.

## Verification

For each adopted route:

- load the route with local services available and confirm `data-studio-ready="true"` after initial render
- load the route with a required local service unavailable and confirm the page still reaches a stable ready or unavailable state
- run one command and confirm `data-studio-busy` is true during the command and false afterward
- update one smoke test to wait on the shared ready contract instead of status text
- run `./scripts/audit_studio_ready_state.py --strict` after changing Studio route shells or route-ready scripts

## Benefits

- fewer false failures in Codex-run browser smoke tests
- simpler cross-route smoke-test helpers
- clearer separation between visible user feedback and machine-readable page state
- a stable foundation for future Studio automation

## Risks

- inconsistent adoption could make some tests trust the contract while others still need route-specific waits
- setting ready too early would create a false sense of stability
- broad rollout could touch many Studio controllers, so the first implementation should be intentionally narrow
