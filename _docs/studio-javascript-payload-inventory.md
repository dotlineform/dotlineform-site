---
doc_id: studio-javascript-payload-inventory
title: JavaScript Payload Inventory
added_date: 2026-05-14
last_updated: 2026-05-20
ui_status: urgent
parent_id: studio
sort_order: 7000
hidden: false
---
# JavaScript Inventory

This document records the current browser JavaScript inventory for key runtime files. Re-prioritise this inventory after material Studio or Docs Viewer JavaScript refactors.

## Criteria for prioritisation

This document prioritises improvements to script modules based on four interdependent indicators.

**Maintenance Risk**
Maintenance risk is the cost and danger of changing behavior later.

Useful indicators:
- Mixed responsibilities: rendering, validation, service calls, state mutation, modal lifecycle, and data normalization in one module.
- High edit frequency or repeated recent touches.
- Bug-prone ownership: the same concept is updated in several places.
- Hidden contracts: functions depend on broad `state` shape instead of explicit inputs.
- Hard-to-test behavior: meaningful logic only runs through DOM events or route boot.
- Large local helper clusters that are only implicitly related.
- Many fallback paths: post/patch/offline/manual modes interleaved with UI code.

**Structural Risk**
Structural risk is whether the module shape matches the architecture we want.

Useful indicators:
- Boundary mismatch: route controller owns work that belongs in domain/save/service/render/modal modules.
- Dependency direction problems: lower-level helpers import route-level concepts, or modules form circular/near-circular knowledge.
- State ownership ambiguity: several modules mutate the same state fields without a clear owner.
- UI primitive drift: route invents markup/event patterns instead of using established Studio primitives.
- Copy-pasted patterns that should become shared or route-local focused modules.
- Entry controller doing implementation work instead of orchestration.

**Performance Risk**
Performance risk should be about actual route cost, not just file size.

Useful indicators:
- Eagerly loaded on common/high-traffic routes.
- Large gzip/raw size on initial route load.
- Heavy boot-time work before route-ready.
- Repeated full-list renders where incremental rendering would matter.
- Expensive filtering/sorting on every input event.
- Large generated data reads or joins on the client.
- Missed lazy boundary: modal/import/management code loaded before needed.

**Architectural Leverage**
This is the important prioritisation piece. A slice is meaningful when it improves future change velocity, not when it is merely small.

Useful indicators:
- Creates or reinforces a durable boundary already used elsewhere.
- Removes a whole responsibility from a mixed controller.
- Makes future related work land in the right module by default.
- Reduces the amount of state a module must understand.
- Makes behavior independently reviewable or testable.
- Aligns sibling routes, like Tag Aliases and Tag Registry.
- Prevents extracted responsibilities from being reintroduced inline.

## Scoring model

| Indicator | Score 0 | Score 1 | Score 2 | Score 3 |
| --- | --- | --- | --- | --- |
| Line pressure | <900 | 900-1,000 | 1,000-1,200 | >1,200 |
| Mixed responsibility | single role | minor overlap | several roles | route owns most workflow layers |
| State coupling | explicit inputs | limited state reads | broad state reads | broad reads and writes across concerns |
| Change frequency | stable | occasional | recurring | frequent or active feature area |
| Performance exposure | lazy/rare | route-local | common route | eager/high-cost/common |
| Structural leverage | little | local cleanup | clear boundary | establishes/reinforces pattern across routes |
| Testability gain | none | minor | focused verification possible | logic becomes independently testable |

Priority should be based on **impact**, not ease:

`priority = mixed responsibility + state coupling + change frequency + performance exposure + structural leverage + testability gain`

Line pressure is a review trigger and tie-breaker, not the main score.

## Application

> Prefer extraction slices that remove a complete responsibility from a mixed controller and leave a clearer ownership boundary behind. Do not prioritise slices because they are narrow, mechanical, or easy. Prioritise slices that reduce future change risk, clarify state ownership, improve route-load behavior, or establish a repeatable module pattern for sibling routes.

For `tag-registry.js`, for example, list/control rendering is meaningful not because it is easy, but because it matches the just-established `tag-aliases-render.js` boundary and would make the two sibling routes structurally consistent. That is a stronger argument than line count alone.

## Current Summary

Measured on 2026-05-20, after the Tag Aliases list/control and import-mode extraction pass.

- Browser JavaScript files under `assets/`: 127
- Total browser JavaScript lines under `assets/`: 40,987

## Current Priorities

### `assets/studio/js/tag-registry.js`

- Lines: 1,128
- Raw: 36.0 KiB
- Gzip: 7.8 KiB
- Classification: mixed route controller
- Maintenance risk: high
- Transfer-size risk: low

**Status**

- Existing domain/save/service split is useful but incomplete.
- Registry modal rendering, field population, delete impact display, import result display, popup option rendering, and modal event/lifecycle wiring now live in `assets/studio/js/tag-registry-modals.js`.
- The route still owns tag lookup, validation decisions, match filtering rules, import parsing/submission, service calls, patch fallback decisions, route busy/ready state, and list/control rendering.

**Next steps**

Next cleanup should target list/control rendering, import parsing/submission, or service orchestration. Modal extraction is complete.

### `assets/docs-viewer/js/docs-viewer.js`

- Lines: 1,205
- Raw: 40.4 KiB
- Gzip: 8.7 KiB
- Classification: mixed shared viewer runtime controller
- Maintenance risk: medium
- Transfer-size risk: medium

**Status**

- Bookmark state, storage, rendering, and events now live in `assets/docs-viewer/js/docs-viewer-bookmarks.js`.
- Config/scope boot and viewer UI text merging now live in `assets/docs-viewer/js/docs-viewer-config-controller.js`.
- Sidebar/nav/meta rendering and trail display now live in `assets/docs-viewer/js/docs-viewer-sidebar.js`.
- Search loading, recent/search result rendering, result batching, and debounced search input binding now live in `assets/docs-viewer/js/docs-viewer-search-controller.js`.
- Document pane visibility, loading/missing/error states, final payload rendering, report context creation, and report mounting handoff now live in `assets/docs-viewer/js/docs-viewer-document-controller.js`.
- Result-row and bookmark-row markup helpers live in `assets/docs-viewer/js/docs-viewer-render.js`.
- URL building, anchor route parsing, history writes, requested-doc resolution, canonical route correction, popstate route orchestration, and payload-load orchestration now live in `assets/docs-viewer/js/docs-viewer-router.js`.
- Status-pill markup and events stay behind the lazy management-controller boundary.

**Next steps**

- The remaining entry controller responsibilities are shared state setup, route callback binding, generated-payload fetch dependencies, visibility/loadable-doc state, search/bookmark/sidebar controller wiring, and management dynamic-loading.
- Maintenance risk is lower after the document-controller extraction, but the file remains under review because it is still the shared runtime composition point.

### `assets/studio/js/data-sharing-review.js`

- Lines: 1,109
- Raw: 41.6 KiB
- Gzip: 8.9 KiB
- Classification: mixed route controller
- Maintenance risk: medium
- Transfer-size risk: low

**Status**

- Result modal and apply-confirmation modal behavior now lives in `assets/studio/js/data-sharing-review-modals.js`.
- The route still owns returned package loading, staged package listing, preview row rendering, selection state, preflight/apply service calls, apply result payload shaping, activity context, status updates, and route busy state.

**Next steps**

- Next cleanup should target preview table rendering or apply-action orchestration.

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
