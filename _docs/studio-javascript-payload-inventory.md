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
| Mixed responsibility | single role | minor overlap | several roles | route owns most workflow layers |
| State coupling | explicit inputs | limited state reads | broad state reads | broad reads and writes across concerns |
| Change frequency | stable | occasional | recurring | frequent or active feature area |
| Performance exposure | lazy/rare | route-local | common route | eager/high-cost/common |
| Structural leverage | little | local cleanup | clear boundary | establishes/reinforces pattern across routes |
| Testability gain | none | minor | focused verification possible | logic becomes independently testable |
| Line pressure | <600 | 600-800 | 800-1,000 | >1,000 |

Priority should be based on **impact**, not ease:

`priority = mixed responsibility + state coupling + change frequency + performance exposure + structural leverage + testability gain + line pressure`

## Application

> Prefer extraction slices that remove a complete responsibility from a mixed controller and leave a clearer ownership boundary behind. Do not prioritise slices because they are narrow, mechanical, or easy. Prioritise slices that reduce future change risk, clarify state ownership, improve route-load behavior, or establish a repeatable module pattern for sibling routes.

For `tag-registry.js`, for example, list/control rendering is meaningful not because it is easy, but because it matches the just-established `tag-aliases-render.js` boundary and would make the two sibling routes structurally consistent.

## Current Summary

Measured on 2026-05-20, after the Data Sharing Review apply-orchestration extraction.

- Browser JavaScript files under `assets/`: 129
- Total browser JavaScript lines under `assets/`: 41,066
- Priority score threshold used for the current table: 16 or higher

## Current Priorities

The full ranked priority table now lives in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).
That child document lists all 129 browser JavaScript files with rank, file, score, and focus.

The detailed sections below cover the top five highest-scoring current improvement priorities after manual review.
When files have the same score, use the ranked child table order for the detail set and watch list.

Each section should summarise:
- why this is a priority area to optimise.
- what direction improvements should go in, and areas that should be left alone, with reasons.

## Top Priority Details

### `assets/docs-viewer/js/docs-viewer.js`

- Priority score: 18
- Classification: mixed shared viewer runtime controller
- Raw: 40.4 KiB

**Why This Is Priority Work**

- This is a shared site runtime, not a single local tool route, so performance exposure and architectural consistency matter even when the remaining controller responsibilities are partly legitimate composition work.

**Direction**

- Separate generated-payload loading and loadable-doc visibility state for when new scope or payload behavior grows.
- Keep management dynamic-loading behind the existing lazy boundary; improve that boundary only if management boot, capability loading, or report loading changes materially.
- Avoid reopening router or document-rendering work just for line count; those responsibilities already have focused modules.
- A further split is only useful if it reduces shared-runtime coupling or route-load cost.
- Do not turn the entry file into a thin pass-through layer if it makes the viewer boot sequence harder to inspect.

### `assets/studio/js/tag-registry.js`

- Priority score: 17
- Classification: mixed route controller
- Raw: 36.0 KiB

**Why This Is Priority Work**

- Existing domain/save/service split is useful but incomplete.
- The route still owns tag lookup, validation decisions, match filtering rules, import parsing/submission, service calls, patch fallback decisions, route busy/ready state, and list/control rendering.
- The strongest leverage is architectural consistency: Tag Aliases now has route-local render and import-mode modules, so Tag Registry can follow the same boundary and make future tag tooling easier to compare and maintain.

**Direction**

- Extract list/control rendering into `assets/studio/js/tag-registry-render.js`, following the Tag Aliases render boundary.
- Extract import-mode availability probing if it can share or mirror the Tag Aliases import-mode boundary without hiding route-specific copy or write behavior.
- Consider service orchestration only after rendering is out of the controller, because the remaining state surface will be easier to define.
- Do not open another modal-extraction slice unless new modal responsibilities are introduced.
- Validation should move only when it clarifies the domain/service boundary.

### `assets/studio/js/tag-aliases.js`

- Priority score: 17
- Classification: route controller with extracted modal, render, and import-mode boundaries
- Raw: 31.8 KiB

**Why This Is Priority Work**

- Modal behavior, list/control rendering, and import-mode availability now have route-local owners.
- The remaining controller still coordinates alias import parsing/submission, service calls, save behavior, route busy/ready state, and cross-module state handoff.
- This route remains architecturally useful because it is the clearest sibling reference for Tag Registry boundaries.

**Direction**

- Revisit import parsing/submission only when alias import behavior changes materially.
- Keep render and modal behavior out of the route shell.
- Use the current Tag Aliases split as the comparison point for Tag Registry and future tag tooling.
- Do not merge extracted render, modal, or import-mode behavior back into the controller.

### `assets/docs-viewer/js/docs-html-import.js`

- Priority score: 17
- Classification: mixed management workflow controller
- Raw: 35.0 KiB

**Why This Is Priority Work**

- The file combines route-state emulation, UI text loading, scope selection, file selection, import preview, confirmation, write calls, result rendering, activity context, and management-service fallback handling.
- It is lazy and management-only, so transfer-size risk is not the main reason to work on it.
- The maintenance risk is high because Docs Import behavior spans HTML/Markdown conversion, media handling, create/overwrite semantics, and local write-service contracts.

**Direction**

- Extract import result rendering into a focused render module that owns media plans, warnings, replacement docs, and final status markup.
- Extract preview/write orchestration into a workflow module that owns service calls, replacement decisions, and write-mode transitions.
- Keep scope selection and route readiness separate from import conversion details.

### `assets/studio/js/tag-studio.js`

- Priority score: 17
- Classification: route shell with extracted modal, render, suggestion, state, save, and offline modules
- Raw: 28.4 KiB

**Why This Is Priority Work**

- Recent extractions created useful owners for modal rendering, tag rendering, suggestion behavior, state helpers, save orchestration, and offline support.
- The remaining controller still coordinates a broad editing workflow, route readiness, and cross-module handoff.
- This route is a common tag-editing surface, so new save/probe/offline behavior can easily drift back into the shell if boundaries are not maintained.

**Direction**

- Keep new save, probe, offline, suggestion, and render behavior in the existing focused modules.
- Extract if a future change adds a complete responsibility that does not already have an owner.
- Prefer tightening module contracts over creating another tiny helper split.
- Do not add new route-local patterns when an existing Tag Studio module already owns the behavior.

## Watch Areas

These files are the next five priorities after the top five detail set for the current pass.

- `assets/studio/js/data-sharing-prepare.js`: mirrors the Data Sharing Review architecture problem below the top-five set. Visit when prepare/review workflow adapter work resumes.
- `assets/studio/js/tag-registry-modals.js`: large route-local modal module. Keep it modal-focused; split if modal workflows themselves gain separate complete responsibilities.
- `assets/docs-viewer/js/docs-viewer-management.js`: Visit if management workflow growth reintroduces mixed ownership.
- `assets/studio/js/series-tags.js`: Visit when analytics scoring, RAG display, or series tag reporting changes.
- `assets/studio/js/data-sharing-review.js`: Keep returned-package loading, route readiness, and workflow-domain adapter policy small; visit if review workflow behavior grows.

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
    rows.append((len(data), len(gzip.compress(data, compresslevel=9)), str(path)))

print('files', len(rows))
for raw, gz, path in sorted(rows, reverse=True)[:30]:
    print(f'{path}\t{raw / 1024:.1f} KiB\t{gz / 1024:.1f} KiB')
PY
```

2. Run a scoring pass using the scoring model above.
Use `git log --since=90 days --name-only` to estimate change frequency, then review the top-scoring files manually for actual responsibility boundaries and route exposure.

3. Confirm route exposure before changing priority rank.
Search checked-in route shells and includes, but avoid generated docs payload noise:

```bash
rg -n "file-name\\.js" _layouts _includes docs studio search catalogue assets/js assets/docs-viewer assets/studio
```

4. Update this document in three parts:
- refresh the current summary totals
- refresh the priority table in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- keep detailed sections for the top five highest-scoring current priorities after manual review
- keep Watch Areas to the next five priorities after the top five

5. When selecting detailed priorities, prefer files where the next slice removes a complete responsibility or clarifies a reusable boundary.
Do not promote a file only because the next slice looks easy.

## Related References

- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
