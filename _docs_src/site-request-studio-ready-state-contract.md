---
doc_id: site-request-studio-ready-state-contract
title: Studio Ready State Contract Request
added_date: 2026-05-01
last_updated: 2026-05-03
ui_status: in-progress
parent_id: change-requests
sort_order: 37
---
# Studio Ready State Contract Request

Status:

- partially implemented

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
- `data-studio-mode="single|bulk|new|import|list|registry|preview|results|confirm|summary|session|edit|idle|empty"`
- `data-studio-service="available|unavailable"`

The shared attributes should live on the main route root, such as `#catalogueWorkRoot`, not on a nested panel.

## Current Implementation

Adopted routes:

- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-series/`
- `/studio/catalogue-moment/`
- `/studio/build-activity/`
- `/studio/bulk-add-work/`
- `/studio/catalogue-activity/`
- `/studio/catalogue-status/`
- `/studio/catalogue-field-registry/`
- `/studio/docs-broken-links/`
- `/studio/docs-import/`
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

The page also exposes:

- `data-studio-route="catalogue-work|catalogue-work-detail|catalogue-series|catalogue-moment|build-activity|bulk-add-work|catalogue-activity|catalogue-status|catalogue-field-registry|docs-broken-links|docs-import|project-state|series-tag-editor|series-tags|studio-works|tag-aliases|tag-groups|tag-registry"`
- `data-studio-mode="empty|single|bulk|new|import|list|registry|idle|preview|results|confirm|result|summary|session|edit"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

Primary async and service-backed Studio routes have adopted the helper. Remaining rollout is limited to lower-priority dashboard, landing, and reference Studio pages where useful.

## Rollout Checklist

Primary async or service-backed Studio routes:

- [x] `/studio/build-activity/` root `#buildActivityRoot`
- [x] `/studio/bulk-add-work/` root `#bulkAddWorkRoot`
- [x] `/studio/catalogue-activity/` root `#catalogueActivityRoot`
- [x] `/studio/catalogue-field-registry/` root `#fieldRegistryReviewRoot`
- [x] `/studio/catalogue-moment/` root `#catalogueMomentRoot`
- [x] `/studio/catalogue-series/` root `#catalogueSeriesRoot`
- [x] `/studio/catalogue-status/` root `#catalogueStatusRoot`
- [x] `/studio/catalogue-work-detail/` root `#catalogueWorkDetailRoot`
- [x] `/studio/catalogue-work/` root `#catalogueWorkRoot`
- [x] `/studio/docs-broken-links/` root `#docsBrokenLinksRoot`
- [x] `/studio/docs-import/` root `#docsHtmlImportRoot`
- [x] `/studio/project-state/` root `#projectStateRoot`
- [x] `/studio/series-tag-editor/` root `#seriesTagEditorRoot`
- [x] `/studio/series-tags/` root from `data-role="series-tags"`
- [x] `/studio/studio-works/` root `#worksStudioRoot`
- [x] `/studio/tag-aliases/` root from `data-role="tag-aliases"`
- [x] `/studio/tag-groups/` root from `data-role="tag-groups"`
- [x] `/studio/tag-registry/` root from `data-role="tag-registry"`

Lower-priority dashboard, landing, and reference routes:

- [ ] `/studio/`
- [ ] `/studio/analytics/`
- [ ] `/studio/catalogue/`
- [ ] `/studio/library/`
- [ ] `/studio/search/`
- [ ] `/studio/ui-catalogue/`
- [ ] `/studio/ui-catalogue/button/`
- [ ] `/studio/ui-catalogue/input/`
- [ ] `/studio/ui-catalogue/list/`
- [ ] `/studio/ui-catalogue/panel/`

These lower-priority routes may need a dedicated route root before they can expose the same attributes consistently. They should still adopt the contract if a page loads async metrics, local service state, or interactive reference content that smoke tests need to wait on.

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
5. Extend the contract across operational catalogue and docs-maintenance routes. Current pass completed Build Activity, Bulk Add Work, Catalogue Activity, Catalogue Drafts, Catalogue Field Registry, Docs Broken Links, Docs Import, and Project State.
6. Extend the contract across tag tools and Studio Works. Current pass completed Series Tag Editor, Series Tags, Studio Works, Tag Aliases, Tag Groups, and Tag Registry.
7. Extend to lower-priority dashboard, landing, and reference Studio pages where useful.

## Verification

For each adopted route:

- load the route with local services available and confirm `data-studio-ready="true"` after initial render
- load the route with a required local service unavailable and confirm the page still reaches a stable ready or unavailable state
- run one command and confirm `data-studio-busy` is true during the command and false afterward
- update one smoke test to wait on the shared ready contract instead of status text

## Benefits

- fewer false failures in Codex-run browser smoke tests
- simpler cross-route smoke-test helpers
- clearer separation between visible user feedback and machine-readable page state
- a stable foundation for future Studio automation

## Risks

- inconsistent adoption could make some tests trust the contract while others still need route-specific waits
- setting ready too early would create a false sense of stability
- broad rollout could touch many Studio controllers, so the first implementation should be intentionally narrow
