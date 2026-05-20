---
doc_id: studio-javascript-payload-inventory
title: JavaScript Inventory Priorities
added_date: 2026-05-14
last_updated: 2026-05-20
ui_status: urgent
parent_id: studio
sort_order: 7000
hidden: false
---
# JavaScript Inventory: Policy and Priorities

This document describes the policy for updating the site-wide browser JavaScript inventory for key runtime files, and the key priorities. Re-prioritise this inventory after material browser JavaScript refactors.

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
- UI primitive drift: route invents markup/event patterns instead of using established site or route-family primitives.
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

Measured on 2026-05-20, after the site-wide JavaScript prioritisation pass.

- Browser JavaScript files under `assets/`: 127
- Total browser JavaScript lines under `assets/`: 40,987
- Files over the 1,000-line review threshold: 3
- Files in the 900-1,000 line watch band: 7
- Priority score threshold used for the current table: 16 or higher

## Current Priorities

The full ranked priority table now lives in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).
That child document lists all 127 browser JavaScript files with rank, file, score, and focus.

The detailed sections below cover the top five current improvement priorities after manual review.
High-scoring recently improved files stay in the child table, but are not automatically top-detail priorities unless the next slice would still remove a complete responsibility or clarify a reusable boundary.

## Top Priority Details

### `assets/studio/js/data-sharing-review.js`

- Priority score: 18
- Lines: 1,109
- Raw: 41.6 KiB
- Gzip: 8.9 KiB
- Classification: mixed route controller
- Line pressure: 2

**Why This Is Priority Work**

- This route owns returned-package loading, staged package listing, preview rendering, selected-row state, action-menu state, preflight calls, apply calls, result shaping, activity context, and route busy/ready state.
- Result modal and apply-confirmation modal behavior now lives in `assets/studio/js/data-sharing-review-modals.js`, but the main controller still mixes workflow policy, rendered review state, and mutation orchestration.
- The route is not only large; it controls write-facing review/apply behavior where state ownership mistakes can create confusing or unsafe local workflow outcomes.

**Meaningful Improvement Slices**

- Extract preview table rendering and selection-state projection into a route-local render module.
- Extract apply-action orchestration into a controller/service-adapter module that owns preflight, apply, result payload shaping, and status transitions.
- Keep workflow-domain adapter decisions explicit so library and tags package support do not grow as conditional branches inside the route shell.

**Deferral Criteria**

- Do not prioritise a cosmetic split that only moves helper functions.
- A useful slice should remove one complete responsibility from the route and leave a smaller public surface between rendered state, selected package state, and service mutation.

### `assets/studio/js/tag-registry.js`

- Priority score: 17
- Lines: 1,128
- Raw: 36.0 KiB
- Gzip: 7.8 KiB
- Classification: mixed route controller
- Line pressure: 2

**Why This Is Priority Work**

- Existing domain/save/service split is useful but incomplete.
- Registry modal rendering, field population, delete impact display, import result display, popup option rendering, and modal event/lifecycle wiring now live in `assets/studio/js/tag-registry-modals.js`.
- The route still owns tag lookup, validation decisions, match filtering rules, import parsing/submission, service calls, patch fallback decisions, route busy/ready state, and list/control rendering.
- The strongest leverage is architectural consistency: Tag Aliases now has route-local render and import-mode modules, so Tag Registry can follow the same boundary and make future tag tooling easier to compare and maintain.

**Meaningful Improvement Slices**

- Extract list/control rendering into `assets/studio/js/tag-registry-render.js`, following the Tag Aliases render boundary.
- Extract import-mode availability probing if it can share or mirror the Tag Aliases import-mode boundary without hiding route-specific copy or write behavior.
- Consider service orchestration only after rendering is out of the controller, because the remaining state surface will be easier to define.

**Deferral Criteria**

- Do not open another modal-extraction slice unless new modal responsibilities are introduced.
- Do not extract tiny validation helpers only to reduce line count; validation should move only when it clarifies the domain/service boundary.

### `assets/docs-viewer/js/docs-viewer.js`

- Priority score: 18
- Lines: 1,205
- Raw: 40.4 KiB
- Gzip: 8.7 KiB
- Classification: mixed shared viewer runtime controller
- Line pressure: 3

**Why This Is Priority Work**

- Bookmark state, storage, rendering, and events now live in `assets/docs-viewer/js/docs-viewer-bookmarks.js`.
- Config/scope boot and viewer UI text merging now live in `assets/docs-viewer/js/docs-viewer-config-controller.js`.
- Sidebar/nav/meta rendering and trail display now live in `assets/docs-viewer/js/docs-viewer-sidebar.js`.
- Search loading, recent/search result rendering, result batching, and debounced search input binding now live in `assets/docs-viewer/js/docs-viewer-search-controller.js`.
- Document pane visibility, loading/missing/error states, final payload rendering, report context creation, and report mounting handoff now live in `assets/docs-viewer/js/docs-viewer-document-controller.js`.
- Result-row and bookmark-row markup helpers live in `assets/docs-viewer/js/docs-viewer-render.js`.
- URL building, anchor route parsing, history writes, requested-doc resolution, canonical route correction, popstate route orchestration, and payload-load orchestration now live in `assets/docs-viewer/js/docs-viewer-router.js`.
- Status-pill markup and events stay behind the lazy management-controller boundary.
- This is a shared site runtime, not a single local tool route, so performance exposure and architectural consistency matter even when the remaining controller responsibilities are partly legitimate composition work.

**Meaningful Improvement Slices**

- Separate generated-payload loading and loadable-doc visibility state if new scope or payload behavior grows.
- Keep management dynamic-loading behind the existing lazy boundary; improve that boundary only if management boot, capability loading, or report loading changes materially.
- Avoid reopening router or document-rendering work just for line count; those responsibilities already have focused modules.

**Deferral Criteria**

- A further split is only useful if it reduces shared-runtime coupling or route-load cost.
- Do not turn the entry file into a thin pass-through layer if it makes the viewer boot sequence harder to inspect.

### `assets/docs-viewer/js/docs-html-import.js`

- Priority score: 17
- Lines: 990
- Raw: 35.0 KiB
- Gzip: 7.7 KiB
- Classification: mixed management workflow controller
- Line pressure: 1

**Why This Is Priority Work**

- The file is below the 1,000-line threshold but combines route-state emulation, UI text loading, scope selection, file selection, import preview, confirmation, write calls, result rendering, activity context, and management-service fallback handling.
- It is lazy and management-only, so transfer-size risk is not the main reason to work on it.
- The maintenance risk is high because Docs Import behavior spans HTML/Markdown conversion, media handling, create/overwrite semantics, and local write-service contracts.

**Meaningful Improvement Slices**

- Extract import result rendering into a focused render module that owns media plans, warnings, replacement docs, and final status markup.
- Extract preview/write orchestration into a workflow module that owns service calls, replacement decisions, and write-mode transitions.
- Keep scope selection and route readiness separate from import conversion details.

**Deferral Criteria**

- Do not split only because the file is near the line threshold.
- Prioritise this when Docs Import media handling, replacement behavior, or source-format support is changing; that is when the boundary improvement has the highest leverage.

### `assets/studio/js/data-sharing-prepare.js`

- Priority score: 17
- Lines: 836
- Raw: 32.5 KiB
- Gzip: 6.7 KiB
- Classification: mixed route controller
- Line pressure: 0

**Why This Is Priority Work**

- This file does not need attention because of line count; it needs attention because it mirrors the Data Sharing Review problem below the review threshold.
- The route owns workflow-domain selection, generated docs index loading, export config loading, package preparation options, selection model state, service probing, submit orchestration, status rendering, result modal handoff, and route readiness.
- The architectural leverage is high because prepare/review should share a clear workflow-adapter boundary instead of growing as two parallel route controllers with similar conditional logic.

**Meaningful Improvement Slices**

- Extract package-list and selection rendering into a route-local render module.
- Extract preparation submit orchestration into a workflow module that owns service capability checks, request shaping, result normalization, and status transitions.
- Align the route boundary with any Data Sharing Review extraction so future library/tags workflows land in shared adapters rather than route-specific branches.

**Deferral Criteria**

- Do not defer just because the file is below 900 lines if data-sharing workflow changes are active.
- Do defer if the next available slice does not clarify the prepare/review shared architecture.

## Watch Areas

These files scored high but are not in the top five detail set for the current pass.

- `assets/studio/js/tag-aliases.js`: recently moved below threshold with modal, render, and import-mode extraction. Keep watching import parsing/submission and service orchestration, but do not immediately reopen it unless new alias workflow work is planned.
- `assets/studio/js/tag-studio.js`: recently split across modal, render, suggestion, state, save, and offline modules. Keep new save/probe/offline work out of the route shell.
- `assets/studio/js/tag-registry-modals.js`: large route-local modal module. Keep it modal-focused; split only if modal workflows themselves gain separate complete responsibilities.
- `assets/docs-viewer/js/docs-viewer-management.js`: recent management action, capability/config, interaction, and modal extractions lowered line pressure. Reopen only if management workflow growth reintroduces mixed ownership.
- `assets/studio/js/series-tags.js`: sub-threshold but stateful analytics route. Revisit when analytics scoring, RAG display, or series tag reporting changes.

## Rerun Notes

Use these notes for future Codex sessions that need to refresh this inventory.

1. Run the metric inventory from the repo root.

```bash
python3 - <<'PY'
from pathlib import Path
import gzip

rows = []
for path in Path('assets').rglob('*.js'):
    data = path.read_bytes()
    lines = data.count(b'\n') + (0 if data.endswith(b'\n') or not data else 1)
    rows.append((lines, len(data), len(gzip.compress(data, compresslevel=9)), str(path)))

print('files', len(rows))
print('total_lines', sum(item[0] for item in rows))
print('over_1000', sum(1 for item in rows if item[0] > 1000))
print('watch_900_1000', sum(1 for item in rows if 900 <= item[0] <= 1000))
for lines, raw, gz, path in sorted(rows, reverse=True)[:30]:
    print(f'{path}\t{lines}\t{raw / 1024:.1f} KiB\t{gz / 1024:.1f} KiB')
PY
```

2. Run a scoring pass using the scoring model above.
Use line pressure only as a recorded metric and tie-breaker.
Use `git log --since=90 days --name-only` to estimate change frequency, then review the top-scoring files manually for actual responsibility boundaries and route exposure.

3. Confirm route exposure before changing priority rank.
Search checked-in route shells and includes, but avoid generated docs payload noise:

```bash
rg -n "file-name\\.js" _layouts _includes docs studio search catalogue assets/js assets/docs-viewer assets/studio
```

4. Update this document in three parts:
- refresh the current summary totals
- refresh the priority table for files with score 16 or higher, or adjust the threshold if the table becomes too broad
- keep detailed sections for the top five current priorities after manual review

5. When selecting detailed priorities, prefer files where the next slice removes a complete responsibility or clarifies a reusable boundary.
Do not promote a file only because the next slice looks easy.

## Related References

- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
