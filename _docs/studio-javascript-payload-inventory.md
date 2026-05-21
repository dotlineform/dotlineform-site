---
doc_id: studio-javascript-payload-inventory
title: JavaScript Inventory Priorities
added_date: 2026-05-14
last_updated: 2026-05-21
ui_status: urgent
parent_id: studio
sort_order: 7000
hidden: false
---
# JavaScript Inventory: Policy and Priorities

This document describes the policy for updating the site-wide browser JavaScript inventory for key runtime files, and the key priorities. Re-prioritise this inventory after material browser JavaScript refactors.

## Criteria for prioritisation

This document prioritises improvements to script modules based on four interdependent risk categories. A high score means the current file shape exposes high risk and important work is needed. A low score means the current file shape and purpose are acceptable. A middle score means the file is workable but has clear improvement opportunities.

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

**Architectural Risk**
Architectural risk is whether the current shape will keep pulling future changes into the wrong place.

Useful indicators:
- Current shape does not reinforce a durable boundary already used elsewhere.
- Future related work is likely to land in the route shell because no focused owner is obvious.
- A sibling route has a clearer pattern that this file does not yet match.
- Extracted responsibilities are easy to reintroduce inline because contracts are loose.
- The module must understand broad cross-route or cross-workflow concepts to make local changes.
- The next useful slice is a complete responsibility, but that responsibility still has no owner.
- Reviewers must reason about unrelated concerns together to understand a change.

## Scoring model

Each file is scored from 1 to 3 for each risk category. The maximum risk score is 12.

| Risk | Score 1: low risk | Score 2: medium risk | Score 3: high risk |
| --- | --- | --- | --- |
| Maintenance Risk | focused role, explicit inputs, stable behavior, small enough to review | some mixed concerns, recurring touches, or broad reads that are still locally understandable | many mixed concerns, broad reads/writes, frequent edits, fallback paths, or hard-to-test behavior |
| Structural Risk | module shape matches its role and established route-family boundaries | partial split exists, but ownership is incomplete or contracts remain broad | route/controller owns workflow layers that belong in domain, service, render, modal, or workflow modules |
| Performance Risk | lazy, rare, small, or no meaningful boot/input cost | route-local exposure, moderate size, or occasional repeated rendering/filtering cost | eager/common exposure, large initial payload, heavy boot work, repeated full renders, or expensive input-time operations |
| Architectural Risk | clear owner exists for future changes and the file reinforces durable patterns | some future changes may drift into this file because ownership is only partly clear | current shape is likely to attract unrelated future work, diverge from sibling patterns, or make unrelated concerns reviewed together |

Risk bands:

- 4-5: low priority; currently ok.
- 6-8: medium priority; some improvements needed.
- 9-12: high priority; important work needed.

Priority should be based on **current risk**, not ease or theoretical leverage:

`risk score = maintenance risk + structural risk + performance risk + architectural risk`

## Application

> Prefer extraction slices that remove a complete responsibility from a mixed controller and leave a clearer ownership boundary behind. Do not prioritise slices because they are narrow, mechanical, or easy. Prioritise slices that reduce future change risk, clarify state ownership, improve route-load behavior, or establish a repeatable module pattern for sibling routes.

For `tag-registry.js`, for example, list/control rendering is meaningful not because it is easy, but because it matches the just-established `tag-aliases-render.js` boundary and would make the two sibling routes structurally consistent.

## Current Summary

Measured on 2026-05-21, after the Series Tags offline-session extraction slice.

- Browser JavaScript files under `assets/`: 133
- Total browser JavaScript lines under `assets/`: 41,383
- Current detail set floor: 8. The Series Tags detail remains below as recently mitigated context because this slice changed its score.

## Current Priorities

The full ranked priority table now lives in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).
That child document lists all 133 browser JavaScript files with rank, file, risk score, and focus.
[Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) keeps the Docs Viewer-specific subset and follow-up tasks separate from the all-script mitigation pass.

The detailed sections below cover selected highest-risk current improvement priorities after manual review, plus recently mitigated context where a completed slice changed the score.
When files have the same score, use the ranked child table order for the detail set and watch list.

Each section should summarise:
- why this is a priority area to optimise.
- what direction improvements should go in, and areas that should be left alone, with reasons.
- which actionable tasks would reduce the risk score, and the anticipated score improvement from each task.

## Top Priority Details

### `assets/docs-viewer/js/docs-html-import.js`

- Risk score: 8
- Classification: mixed management workflow controller
- Raw: 35.0 KiB

**Why This Is Priority Work**

- The file still owns route-state emulation, UI text loading, scope selection, staged file selection, management-service availability, and workflow handoff.
- It is lazy and management-only, so transfer-size risk is not the main reason to work on it.
- The maintenance risk remains meaningful because Docs Import behavior spans HTML/Markdown conversion, media handling, create/overwrite semantics, and local write-service contracts.

**Direction**

- Keep import result rendering in `assets/docs-viewer/js/docs-html-import-render.js`, which owns media plans, warnings, replacement docs, and final status markup.
- Keep preview/write orchestration in `assets/docs-viewer/js/docs-html-import-workflow.js`, which owns service calls, replacement decisions, and write-mode transitions.
- Keep scope selection and route readiness separate from import conversion details.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | done | Moved import result rendering into `assets/docs-viewer/js/docs-html-import-render.js` for media plans, warnings, replacement docs, and final status markup. |
| 2 | done | Extracted preview/write orchestration into `assets/docs-viewer/js/docs-html-import-workflow.js`, which owns service calls, replacement decisions, and write-mode transitions. |
| 3 | done | Kept scope selection and route readiness in the controller while passing explicit workflow inputs for scope, route path, management base URL, UI text config, and prompt-meta selection. |
| 4 | done | Added focused module-smoke checks for preview overwrite confirmation, replacement doc id selection, write failure partial-result fallback, and result rendering. |

### `assets/docs-viewer/js/docs-viewer.js`

- Risk score: 9
- Classification: mixed shared viewer runtime controller
- Raw: 40.4 KiB

**Why This Is Priority Work**

- This is a shared site runtime, not a single local tool route, so performance exposure and architectural consistency matter even when the remaining controller responsibilities are partly legitimate composition work.
- Router and document-rendering already have focused modules, so this is high risk because of shared route exposure rather than because every remaining responsibility is misplaced.

**Direction**

- Separate generated-payload loading and loadable-doc visibility state for when new scope or payload behavior grows.
- Keep management dynamic-loading behind the existing lazy boundary; improve that boundary only if management boot, capability loading, or report loading changes materially.
- Router or document-rendering already have focused modules.
- A further split is only useful if it reduces shared-runtime coupling or route-load cost.
- Do not turn the entry file into a thin pass-through layer if it makes the viewer boot sequence harder to inspect.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract generated-payload loading and loadable-doc visibility state into a focused module when scope or payload behavior next changes. Anticipated improvement: -1 to -2 from maintenance and structural risk. |
| 2 | proposed | Audit the management lazy boundary and move any newly eager management setup back behind dynamic loading. Anticipated improvement: -1 to -2 from performance risk, depending on whether route-load exposure changes. |
| 3 | proposed | Add focused verification around payload loading, scope switching, and document visibility state after extraction. Anticipated improvement: -1 from maintenance risk by making the behavior reviewable outside full viewer boot. |

### `assets/studio/js/series-tags.js`

- Risk score: 7
- Score breakdown: maintenance 2, structural 2, performance 2, architectural 1.
- Classification: mitigated route orchestration shell
- Raw: 18.6 KiB

**Why This Was Rescored**

- The route no longer owns analytics scoring interpretation, RAG/report markup, filter rendering, chip display, visible-row projection, or report sorting.
- Scoring now lives in `assets/studio/js/analysis-tag-scoring.js`, and report/table rendering now lives in `assets/studio/js/series-tags-render.js` behind an explicit report input.
- Offline-session storage, export, clear, import-cleanup, and editor offline staging now live in `assets/studio/js/tag-assignments-offline-session.js`.
- The normal Series Tags route path no longer reads local storage, overlays staged offline rows, or wires session/import modal behavior until the user opens the session or import flow.
- The Series Tag Editor local-save failure path now switches to offline mode but requires an explicit follow-up Save before staging offline changes.
- Remaining risk comes from legitimate route orchestration plus still-inline import preview/apply service workflow.
- The route is still eager and route-local, with several async data and service states, so future import changes should avoid rebuilding analytics, render, modal, or offline-session behavior in the route shell.

**Direction**

- Keep scoring calculation and RAG interpretation in `assets/studio/js/analysis-tag-scoring.js`.
- Keep report/table rendering, row projection, tag chip display, and sort comparison in `assets/studio/js/series-tags-render.js`.
- Keep offline-session storage/write/export behavior in `assets/studio/js/tag-assignments-offline-session.js`.
- Keep session/import modal rendering and focus lifecycle in `assets/studio/js/series-tags-modals.js`, loaded by the route only when the user activates a modal flow.
- Keep route-shell work limited to boot, config/data loading, event wiring, route ready/busy state, dynamic module activation, modal coordination, and applying successful import changes back to local state.
- If import preview/apply behavior grows materially, extract a focused workflow/service owner with explicit inputs for import payload, resolutions, activity context, and assignment reloads.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | done | Extracted scoring calculation and interpretation into `assets/studio/js/analysis-tag-scoring.js`, including RAG label and sort-rank interpretation for the Series Tags route. |
| 2 | done | Moved Series Tags report/table rendering into `assets/studio/js/series-tags-render.js`, including RAG indicator markup, filters, chip display, visible-row projection, and sort comparison. |
| 3 | done | Passed an explicit Series Tags report input from the route shell into `assets/studio/js/series-tags-render.js` instead of handing over broad route state. |
| 4 | done | Added focused smoke checks for score interpretation and Series Tags report rendering/RAG display output. |
| 5 | done | Extracted offline-session handling for Series Tags and Series Tag Editor into `assets/studio/js/tag-assignments-offline-session.js`, with Series Tags loading session storage/modals only after the user opens the session or import flow and Series Tag Editor save-failure fallback requiring an explicit follow-up Save before staging offline changes. Tag Registry and Tag Aliases remain out of scope because they do not currently use offline sessions. |
| 6 | proposed | If import preview/apply workflow changes materially, extract it into a focused workflow/service module. Anticipated improvement: -1 from maintenance or structural risk. |

### `assets/studio/js/data-sharing-prepare.js`

- Risk score: 8
- Score breakdown: maintenance 2, structural 2, performance 2, architectural 2.
- Classification: medium-risk route orchestration shell
- Raw: 18.0 KiB

**Why This Remains In The Detail Set**

- The route now has focused workflow, render, service, and modal owners, so package-state projection, list/result rendering, request validation, and success/failure result shaping no longer sit directly in the route shell.
- Focused module smoke coverage now checks prepare request projection, result rendering, and write failure shaping without requiring full route boot.
- Remaining route risk comes from legitimate orchestration responsibilities: route boot, adapter registry loading, generated docs-index loading, scope URL changes, event wiring, service availability, and ready/busy state.
- The route still coordinates several async data and service states, so future prepare changes should keep behavior inside the focused owners rather than rebuilding mixed workflow logic here.

**Direction**

- Keep capability/profile interpretation and prepare request shaping in `assets/studio/js/data-sharing-prepare-workflow.js`.
- Keep config/list/format/result rendering in `assets/studio/js/data-sharing-prepare-render.js`.
- Keep request validation, package write calls, and result shaping in `assets/studio/js/data-sharing-prepare-service.js`.
- Keep route-shell work limited to boot, config/data loading, scope routing, event wiring, modal coordination, and route ready/busy projection.
- If generated docs-index loading or visible-doc tree projection changes materially, consider extracting that as a focused data-loading/projection helper with explicit inputs.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | done | Extracted package workflow adapter behavior into `assets/studio/js/data-sharing-prepare-workflow.js`, which owns prepare capability/profile interpretation, config and format projection, selection requirements, and prepare request shaping. |
| 2 | done | Moved prepare list/control rendering, selection checkbox sync, and result modal body rendering into `assets/studio/js/data-sharing-prepare-render.js` with explicit route-state inputs. |
| 3 | done | Defined `assets/studio/js/data-sharing-prepare-service.js` as the preparation service boundary for request validation, package write calls, and success/failure result shaping. |
| 4 | done | Added focused module checks for package-state projection, preparation result rendering, and fallback write behavior. |
| 5 | proposed | If generated docs-index loading or visible-doc tree projection changes materially, extract it as a focused helper with explicit route inputs. Anticipated improvement: -1 from maintenance or architectural risk. |

### `assets/studio/js/tag-registry.js`

- Risk score: 8
- Score breakdown: maintenance 2, structural 2, performance 2, architectural 2.
- Classification: medium-risk route orchestration shell
- Raw: 30.2 KiB

**Why This Remains In The Detail Set**

- The route now has focused domain, save, service, render, import-mode, modal, and workflow owners, so the original high-risk sibling-boundary gap has been mitigated.
- Remaining route risk comes from legitimate orchestration responsibilities: route boot, data hydration, event wiring, modal state transitions, validation handoff, mutation result application, and ready/busy state.
- The file is still route-local and moderately sized, so future tag-registry changes should continue to avoid pulling render, service, fallback, or domain behavior back into the route shell.

**Direction**

- Keep list/control rendering in `assets/studio/js/tag-registry-render.js`.
- Keep import-mode availability probing in `assets/studio/js/tag-registry-import-mode.js`.
- Keep service orchestration and patch fallback decisions in `assets/studio/js/tag-registry-workflow.js`.
- Keep route-shell work limited to boot, data loading, event wiring, route state, modal coordination, and applying successful mutation results to local state.
- Move validation or mutation-state projection only if future changes make either one a complete responsibility with explicit inputs.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | done | Moved list and control rendering into `assets/studio/js/tag-registry-render.js`, matching the Tag Aliases render boundary. |
| 2 | done | Extracted import-mode probing into `assets/studio/js/tag-registry-import-mode.js`, mirroring the Tag Aliases import-mode boundary. |
| 3 | done | Defined `assets/studio/js/tag-registry-workflow.js` as the service-orchestration boundary for save/import fallback decisions. |
| 4 | done | Added focused verification for render output, import-mode availability, and fallback save behavior, without requiring full route boot. |
| 5 | proposed | If validation or mutation-state projection changes materially, extract it as a focused domain/workflow adapter with explicit inputs. Anticipated improvement: -1 from maintenance or architectural risk. |

## Watch Areas

These files are notable watch areas after the current mitigation pass.

- `assets/studio/js/series-tags.js`: now rescored to 7 after offline-session extraction. Revisit only if import preview/apply behavior grows materially or route boot starts taking on modal/offline responsibilities again.
- `assets/studio/js/tag-aliases.js`: now a medium-risk reference state with useful render, modal, and import-mode owners. Revisit only when alias import parsing/submission changes materially.
- `assets/studio/js/tag-studio.js`: medium risk because several good owners already exist. Offline staging now requires explicit activation through Save after fallback, so revisit only if route orchestration, editor state projection, or save-mode behavior grows materially.
- `assets/studio/js/data-sharing-review.js`: medium risk after apply-orchestration extraction. Keep returned-package loading, route readiness, and workflow-domain adapter policy small.
- `assets/studio/js/tag-registry-modals.js`: large route-local modal module. Keep it modal-focused; split if modal workflows themselves gain separate complete responsibilities.

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
Use `git log --since=90 days --name-only` to inform maintenance risk, then review the highest-risk files manually for actual responsibility boundaries and route exposure.

3. Confirm route exposure before changing risk rank.
Search checked-in route shells and includes, but avoid generated docs payload noise:

```bash
rg -n "file-name\\.js" _layouts _includes docs studio search catalogue assets/js assets/docs-viewer assets/studio
```

4. Update this document in three parts:
- refresh the current summary totals
- refresh the priority table in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- keep detailed sections for the top five highest-risk current priorities after manual review
- keep Watch Areas to the next five priorities after the top five

5. When selecting detailed priorities, prefer files where the next slice removes a complete responsibility or clarifies a reusable boundary.
Do not promote a file only because the next slice looks easy.

## Related References

- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
