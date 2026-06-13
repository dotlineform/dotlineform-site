---
doc_id: site-request-public-catalogue-runtime-module-architecture-slices
title: Public Catalogue Runtime Module Architecture Slices
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Module Architecture Slices

Status:

- planned

## Purpose

Track the implementation slices for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture).

This is not a comprehensive inventory of every public route.
The work should proceed from the agreed module structure and the first foundation refactor: thumbnail grid/list.
The work is not a greenfield rewrite.
The existing route code is the authoritative behavior reference for this refactor.

## Steer

- Set up the defined folder structure before moving behavior.
- Start with the thumbnail grid/list foundation.
- Carefully inspect existing legacy route code before defining the component contract.
- Port and adapt working logic into new ES module boundaries instead of redesigning behavior line by line.
- Change code only where needed for modularity, ownership, consistency, or the agreed component contract.
- Do not batch a full public-site route migration.
- Do not create a giant inventory before implementing the first foundation.
- Keep each completed slice functional and deployable.
- Each task must leave a short next-session steer if it is not complete.

## Validation Policy

Use lightweight validation for implementation slices:

- run JavaScript syntax checks for changed modules;
- perform manual browser testing for touched routes and component states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation that was actually performed and materially relevant.
Do not maintain an exhaustive list of every possible validation command.

## Slice Assessment Requirement

Each implementation slice must end with a written assessment in this document.
The assessment should be specific enough that no separate state inventory is needed later.
The parent request is a design guide, not just a request for work.
Its sections are acceptance criteria for each slice.

For each completed slice, record:

- what legacy behavior was inspected;
- what behavior was preserved;
- what was normalized into the component contract;
- what the new component or module owns;
- what the route still owns;
- what was intentionally not changed;
- what specific improvement opportunities remain;
- whether any remaining issue blocks the architecture or is later cleanup;
- whether the component or module is good enough to continue the migration.

Each assessment must also include a parent-design acceptance checklist with concrete `yes` evidence against the key design principles.
Do not merely say that the parent request was followed.
Record evidence for each criterion.
The design principles are requirements, not suggestions.
If a criterion cannot be answered `yes`, the slice is not complete and the assessment must record the blocking correction needed before continuing.

Required acceptance checks:

- module-level refactor, not greenfield rewrite;
- legacy behavior was carefully inspected before contract design;
- working behavior was ported or adapted rather than redesigned line by line;
- public navigation, URL/query, route state, persistence, history, localStorage, link targets, and data schemas remain stable;
- completed slice leaves the site functional and deployable;
- ES module boundaries follow the target folder structure;
- no broad `utils.js`-style module was introduced;
- performance rules were respected, including no unnecessary loads or duplicate fetches introduced;
- component normalization uses a stable component contract rather than route-local forks;
- thumbnail grid/list remains one component family with grid/list modes;
- search work, if touched, stays structural-only;
- validation stayed within syntax checks and manual browser testing unless a separate decision changed that.

Avoid vague risk language without a condition and action.
Do not write notes such as "this may become a maintenance problem and should be watched."

Use concrete follow-up triggers instead.
Example:

- `thumbnail-grid-list.js` currently owns pagination button rendering and page-state persistence. If the next route needs server-sized pages or infinite loading, split page-state persistence into `shared/page-state.js` before integrating that route.

## Slice 1: Thumbnail Grid/List Foundation

Purpose: create the first low-level component foundation and prove that the new structure can absorb a complex existing UI concept without changing public behavior.

Scope:

- create `site/assets/js/catalogue/routes/`;
- create `site/assets/js/catalogue/shared/`;
- create `site/assets/js/catalogue/components/`;
- create `site/assets/js/catalogue/navigation/`;
- create `site/assets/js/catalogue/search/`;
- carefully inspect the existing thumbnail grid/list behavior in the relevant legacy route scripts;
- define the thumbnail grid/list component contract;
- implement the first component modules under `components/` by porting or adapting existing working logic where it fits the contract;
- add only shared helpers required by the thumbnail grid/list component;
- do not switch every route;
- choose the first integration route only after the component contract is visible.

Out of scope:

- search payload optimization;
- generated catalogue data schema changes;
- public navigation redesign;
- broad route migration;
- automated smoke-test maintenance.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 1.1 | planned | Create the `site/assets/js/catalogue/` folder structure with empty or minimal module files only where needed. | Record any naming concern before adding behavior. |
| 1.2 | planned | Carefully inspect legacy thumbnail grid/list behavior in the relevant scripts that currently implement grid/list variants. | Capture behavior needed for the component contract without expanding into a broad public-site inventory. |
| 1.3 | planned | Define the thumbnail grid/list component contract, including grid/list modes, paging, page persistence, item links, captions, and current/selected item state. | Stop for review if the contract needs route-specific flags. |
| 1.4 | planned | Implement the first thumbnail grid/list component modules and required shared helpers by porting or adapting existing working logic. | Keep modules focused; avoid route integration until the component is coherent. |
| 1.5 | planned | Select and integrate one first route after the component contract is visible. | Choose the route that proves the component with the least unrelated migration work. |

## Completed Verification

- Not started.

## Slice 1 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Legacy behavior inspected before contract design | yes required |  |
| Working behavior ported/adapted rather than redesigned line by line | yes required |  |
| Public route/navigation/data contracts remain stable | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| ES module boundaries follow target folder structure | yes required |  |
| No broad `utils.js`-style module introduced | yes required |  |
| Performance rules respected | yes required |  |
| Component normalization uses stable component contract | yes required |  |
| Thumbnail grid/list remains one component family with grid/list modes | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 1, decide whether the next foundation should be navigation, image and image caption, or metadata panel based on what the grid/list work exposes.
