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

Measured on 2026-05-20, after the Data Sharing Review apply-orchestration extraction.

- Browser JavaScript files under `assets/`: 129
- Total browser JavaScript lines under `assets/`: 41,066
- High-priority risk score threshold used for the current detail set: 9 or higher

## Current Priorities

The full ranked priority table now lives in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).
That child document lists all 129 browser JavaScript files with rank, file, risk score, and focus.
[Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) keeps the Docs Viewer-specific subset and follow-up tasks separate from the all-script mitigation pass.

The detailed sections below cover the top five highest-risk current improvement priorities after manual review.
When files have the same score, use the ranked child table order for the detail set and watch list.

Each section should summarise:
- why this is a priority area to optimise.
- what direction improvements should go in, and areas that should be left alone, with reasons.
- which actionable tasks would reduce the risk score, and the anticipated score improvement from each task.

## Top Priority Details

### `assets/studio/js/tag-registry.js`

- Risk score: 11
- Classification: mixed route controller
- Raw: 36.0 KiB

**Why This Is Priority Work**

- Existing domain/save/service/render/import-mode/workflow split is useful but incomplete.
- The route still owns tag lookup, validation decisions, match filtering rules, user-facing mutation result handling, and route busy/ready state.
- The strongest risk is architectural drift: Tag Aliases now has route-local render and import-mode modules, so Tag Registry is the sibling route most likely to accumulate future tag tooling in the wrong place if it does not follow the same boundary.

**Direction**

- Keep list/control rendering in `assets/studio/js/tag-registry-render.js`, following the Tag Aliases render boundary.
- Keep import-mode availability probing in `assets/studio/js/tag-registry-import-mode.js`, following the Tag Aliases import-mode boundary.
- Keep service orchestration and patch fallback decisions in `assets/studio/js/tag-registry-workflow.js`.
- Do not open another modal-extraction slice unless new modal responsibilities are introduced.
- Validation should move only when it clarifies the domain/service boundary.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | done | Moved list and control rendering into `assets/studio/js/tag-registry-render.js`, matching the Tag Aliases render boundary. |
| 2 | done | Extracted import-mode probing into `assets/studio/js/tag-registry-import-mode.js`, mirroring the Tag Aliases import-mode boundary. |
| 3 | done | Defined `assets/studio/js/tag-registry-workflow.js` as the service-orchestration boundary for save/import fallback decisions. |
| 4 | proposed | Add focused verification for render output, import-mode availability, and fallback save behavior as each slice lands. Anticipated improvement: -1 from maintenance risk where logic no longer requires full route boot. |

### `assets/studio/js/data-sharing-prepare.js`

- Risk score: 11
- Classification: mixed workflow route controller
- Raw: 35.1 KiB

**Why This Is Priority Work**

- This route still mirrors the Data Sharing Review architecture problem: route readiness, package preparation, validation, workflow-state projection, preview rendering, service calls, and result handling are tightly coordinated in one place.
- Data-sharing behavior changes tend to affect cross-file contracts, so broad route ownership makes future package workflow changes harder to review safely.
- The existing review-side extraction gives a comparison point, but prepare still exposes high maintenance and structural risk.

**Direction**

- Mirror the Review route by extracting workflow-domain adapter behavior where package state crosses route and service boundaries.
- Move preview/result rendering into a focused render module if it currently requires the route to understand full package detail shape.
- Keep route readiness and top-level event wiring in the route shell.
- Do not split small validators unless the split gives package workflow state a clearer owner.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract package workflow adapter behavior into a focused module that owns route-to-domain state projection. Anticipated improvement: -1 to -2 from structural and architectural risk. |
| 2 | proposed | Move preview/result rendering into a render module with explicit inputs. Anticipated improvement: -1 from maintenance risk, or -2 if route state reads shrink materially. |
| 3 | proposed | Define a preparation service/workflow boundary for write calls, fallback states, and package result shaping. Anticipated improvement: -1 to -2 from maintenance and structural risk. |
| 4 | proposed | Add focused checks for package-state projection, preparation result rendering, and fallback write behavior. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-html-import.js`

- Risk score: 10
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

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Move import result rendering into a focused render module for media plans, warnings, replacement docs, and final status markup. Anticipated improvement: -1 to -2 from maintenance and structural risk. |
| 2 | proposed | Extract preview/write orchestration into a workflow module that owns service calls, replacement decisions, and write-mode transitions. Anticipated improvement: -1 to -2 from maintenance and structural risk. |
| 3 | proposed | Keep scope selection and route readiness in the controller while passing explicit inputs to conversion and workflow modules. Anticipated improvement: -1 from architectural risk. |
| 4 | proposed | Add focused checks for preview, replacement, write-mode fallback, and result rendering. Anticipated improvement: -1 from maintenance risk. |

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

- Risk score: 9
- Classification: mixed analytics/tag reporting route
- Raw: 29.0 KiB

**Why This Is Priority Work**

- The route combines analytics scoring, RAG display, tag reporting, route readiness, and rendering coordination.
- It is not the worst current controller, but the scoring/reporting concepts are cohesive enough to deserve clearer owners before more analytics behavior accumulates.
- The main risk is maintainability and future ownership drift, not initial transfer size.

**Direction**

- Extract analytics scoring or RAG display only as complete responsibilities with explicit inputs.
- Keep route readiness and high-level event wiring in the route shell.
- Prefer a focused reporting/rendering boundary over small helper splits.
- Leave stable display code alone unless the next analytics change would otherwise expand the route shell.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract scoring calculation and interpretation into a focused analytics module if scoring behavior changes. Anticipated improvement: -1 to -2 from maintenance and architectural risk. |
| 2 | proposed | Move RAG/report rendering into a focused render module if display behavior grows. Anticipated improvement: -1 from maintenance or structural risk. |
| 3 | proposed | Pass explicit scoring/report inputs from the route shell rather than broad route state. Anticipated improvement: -1 from maintenance risk. |
| 4 | proposed | Add focused checks for score interpretation and RAG display output when those modules are extracted. Anticipated improvement: -1 from maintenance risk. |

## Watch Areas

These files are the next five priorities after the top five detail set for the current pass.

- `assets/studio/js/tag-aliases.js`: now a medium-risk reference state with useful render, modal, and import-mode owners. Revisit only when alias import parsing/submission changes materially.
- `assets/studio/js/tag-studio.js`: medium risk because several good owners already exist. Keep new save, probe, offline, suggestion, and render behavior in those modules.
- `assets/studio/js/data-sharing-review.js`: medium risk after apply-orchestration extraction. Keep returned-package loading, route readiness, and workflow-domain adapter policy small.
- `assets/studio/js/tag-registry-modals.js`: large route-local modal module. Keep it modal-focused; split if modal workflows themselves gain separate complete responsibilities.
- `assets/docs-viewer/js/docs-viewer-management.js`: Visit if management workflow growth reintroduces mixed ownership.

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
