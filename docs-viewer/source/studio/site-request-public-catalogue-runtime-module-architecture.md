---
doc_id: site-request-public-catalogue-runtime-module-architecture
title: Public Catalogue Runtime Module Architecture Request
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: in-progress
parent_id: change-requests
---
# Public Catalogue Runtime Module Architecture Request

## Summary

Design and migrate to a new public catalogue runtime module structure for the static site.

This request is a module-level refactor, not a cleanup pass over the current extracted route scripts and not a greenfield rewrite.
The current scripts contain older inline route behavior that accumulated over time while newer modules were added around it.
They should be treated as behavior references and source material, not as the target module architecture.

The target modules should be new, documented, and built around explicit ownership, but the working legacy behavior should be ported and adapted rather than redesigned line by line.
Routes should then switch over to the new entrypoints once the equivalent behavior exists.

## Goal

Create a stable public catalogue runtime structure before deciding detailed functionality changes or optimization work.

The first design question is:

- what is the ideal module structure for public catalogue routes, and how should the site migrate to it?

Once that target is stable, follow-up work can decide:

- which detailed route behavior should stay, change, or be simplified;
- which UI differences are intentional or should be normalized;
- which payload and runtime costs are worth optimizing;
- whether public catalogue search needs a separate data/runtime redesign.

## Design Direction

Build new target modules rather than refactoring the old extracted files in place.
This is a module-boundary refactor from a flat list of public scripts, some of which used to contain inline JavaScript.
File-level and function-level cleanup can continue after the module structure is correct.

The migration should:

- define the target module map first;
- create new modules with documented responsibilities;
- carefully inspect the relevant legacy code before defining component contracts;
- port or adapt existing working logic where it already satisfies the required behavior;
- prefer concise shared modules where there is real shared behavior;
- switch routes to the new entrypoints when ready;
- delete obsolete legacy route scripts once no route loads them.

This avoids preserving accidental boundaries from older inline code.
Each new module must have a clear owner and reason to exist.

## Refactor Boundary

This request is a code-structure refactor, not a public-route redesign.
The implementation should replace old route-local function calls with new module and component calls behind the same behavior.
The problem being solved is modularisation, ownership, and consistency, not unmet UI requirements.

These contracts must remain stable unless a separate recorded decision explicitly changes them:

- public navigation design;
- URL and query patterns;
- route state semantics;
- thumbnail-grid page persistence;
- back-link behavior;
- browser history behavior;
- localStorage keys and stored preference behavior;
- user-visible UI behavior;
- public link targets;
- generated data schemas.

Small UI normalization is allowed only when it supports code structure without changing navigation design or user-visible behavior.
Do not invent new UI behavior to make a module easier to write.

## Incremental Migration Invariant

Each completed implementation slice must leave the public site functional and deployable.

The migration may temporarily contain a mixed runtime:

- some routes may still use legacy extracted scripts;
- some routes may use new module entrypoints;
- shared foundations may exist before every route uses them;
- old scripts may remain checked in until no route loads them.

Mixed legacy and new runtime ownership is allowed only at clean route, component, or foundation boundaries.
Do not leave a route half-switched.
Do not update a route shell to new modules before the required modules exist and have passed the relevant checks.
Delete legacy extracted scripts only after no public route loads them.

At each stopping point, `bin/site-validate` and the relevant targeted smoke checks should pass.

## Engineering Ground Rules

New public catalogue runtime code should use ES modules.
The old classic-script and global-object pattern belongs to the legacy extracted route scripts, not the target architecture.

Code rules:

- route files are entrypoints only and should bootstrap one route or one route mode;
- imports should be explicit and static unless dynamic `import()` has a clear route or performance reason;
- shared modules must have narrow named responsibilities;
- do not create a broad `utils.js`-style module;
- do not introduce new globals;
- old extracted scripts are behavior references only, not files to gradually reshape.

Performance is a first-order requirement for this migration.
The site is small, so public catalogue routes should be extremely fast.
Do not treat the absence of quantified measurement, or the current small scale of the site, as a reason to accept avoidable runtime cost.

Performance rules:

- routes should load only the JavaScript needed for the current route or route mode;
- avoid "download then early return" as a normal routing strategy;
- avoid duplicate JSON fetches on one route;
- prefer small route entrypoints and focused shared modules;
- use lazy loading when it prevents meaningful unused work;
- consider parse and execute cost, not just transfer size;
- do not make public search payload or runtime performance worse while leaving search redesign to a separate request.

Ownership rules:

- `routes/` owns route bootstrapping and route state wiring;
- `shared/` owns primitives such as fetch, URL state, parsing, normalization, and media helpers;
- `components/` owns reusable DOM rendering where reuse is real;
- `navigation/` owns keyboard, swipe, and previous/next behavior;
- `search/` owns public catalogue search runtime modules, but not the broader search payload redesign.

## Data Constraints

The existing public catalogue data JSON structures should remain stable unless there is an obvious gap that blocks the module architecture.

In particular:

- catalogue data JSON files are probably acceptable as they are, apart from search;
- public search JSON is a known separate problem and should be addressed in detail separately;
- this request should not redesign generated catalogue payload schemas as part of the module migration;
- changing shared catalogue data structures risks forcing a Studio refactor, which is outside this request.

The runtime migration may change how route code reads existing payloads.
It should not change payload ownership or schema contracts without a separate recorded decision.

## UI Constraints

The current public catalogue UI is acceptable as the baseline.

This request is not a visual redesign.
However, if small page-to-page UI differences prevent a concise shared module from existing, the UI should adjust rather than forcing duplicated runtime code.

Allowed UI changes are small normalization changes that support clearer module ownership.
Material layout, route, or interaction changes need a separate decision.

## Target Module Map

The target module map starts from this ownership model:

| Area | Purpose |
| --- | --- |
| `site/assets/js/catalogue/routes/` | Route entrypoints only. Each file bootstraps one public route or route mode. |
| `site/assets/js/catalogue/shared/` | Narrow shared primitives such as URL state, JSON fetch, text normalization, media helpers, and dataset parsing. |
| `site/assets/js/catalogue/components/` | Reusable DOM components for coherent public catalogue UI concepts such as cards, thumbnail grids, pagination, loading states, error states, or empty states. |
| `site/assets/js/catalogue/navigation/` | Focused interaction modules such as keyboard navigation, swipe navigation, and previous/next catalogue navigation. |
| `site/assets/js/catalogue/search/` | Public catalogue search runtime modules. Search payload redesign remains separate. |

Route entrypoints should be thin.
Shared modules should stay narrow.
No broad utility dump should replace the current route-script tangle.

The folder map is the target structure.
Implementation should adjust file-level module boundaries inside this structure when needed.
Change the folder map only if implementation shows that a whole ownership area is missing or wrongly named.

## File-Level Placement Criteria

Use these criteria when deciding where a new module belongs.

### `routes/`

A file belongs in `routes/` when it is the browser entrypoint for one public route or route mode.

Route files may:

- read route DOM anchors and page-level data attributes;
- parse route query state;
- compose shared, component, navigation, and search modules;
- make route-specific decisions about what to load.

Route files should not:

- contain reusable rendering logic;
- contain generic fetch, parsing, media, or normalization helpers;
- expose functions imported by non-route modules;
- become the place where shared behavior is hidden because it was awkward to name.

If a route file grows large, first decide whether the code is genuinely route-specific.
If it is not route-specific, move it to the narrowest suitable non-route module.

### `shared/`

A file belongs in `shared/` when it is a narrow primitive used by more than one route or module type.

Good shared modules include:

- JSON fetch and error handling;
- URL/query state helpers;
- DOM dataset parsing;
- text normalization;
- media path and image-size helpers.

Shared files should not:

- know about a specific route shell;
- render substantial UI;
- import from `routes/`;
- grow route flags such as `isRecent`, `isSeries`, or `isMomentMode`;
- become a generic utility bucket.

If a shared module needs many route-specific options, either split it or keep the behavior route-owned.

### `components/`

A file belongs in `components/` when it renders a coherent public catalogue UI concept.
Reuse is not restricted to the current public runtime import graph.
The criterion is whether the UI concept is repeatable and should have one designed implementation, not whether more than one route already imports it.

This component design approach should be repeatable later in Studio and Analytics code.
A component can be valid from the outset even when the first migration slice uses it once.
That avoids creating route-local forks that later require a harder refactor when the same UI concept appears again.

Valid component concepts include:

- work cards;
- series cards;
- pagination;
- empty states;
- loading states;
- error states;
- image or thumbnail grids;
- route controls where the control concept is reusable.

Component files may:

- receive normalized data and render DOM fragments;
- own small UI-specific formatting needed by that component;
- expose focused render functions used by route entrypoints.
- define a stable DOM contract for a repeated UI concept even before a second route imports it.

Component files should not:

- fetch data;
- parse route query state;
- read page-level route configuration directly;
- contain keyboard, swipe, or history navigation behavior;
- accept many options to compensate for unrelated page designs.

Create a component when:

- the UI concept has a clear name;
- the DOM structure is expected to recur across routes, apps, or later migration slices;
- defining it once prevents future route-local forks;
- the component can receive data and small presentation options cleanly;
- the component does not need route-specific flags to explain what it is rendering.

If two pages need nearly identical renderers but differ in small markup details, prefer a small UI normalization over a highly configurable component.
Do not keep a coherent UI concept route-local just because it is currently used once.

### `navigation/`

A file belongs in `navigation/` when it owns user navigation behavior independent of route rendering.

Navigation modules include:

- keyboard navigation;
- swipe navigation;
- previous/next catalogue navigation;
- focus movement or interaction wiring that is reusable across route modes.

Navigation files should not:

- fetch catalogue payloads;
- render route content;
- decide which route mode is active;
- depend on a specific route entrypoint.

If navigation cannot be separated without route-specific data loading or rendering, keep the thin wiring in the route file and extract only the reusable interaction primitive.

### `search/`

A file belongs in `search/` when it is specific to public catalogue search behavior.

Search modules may:

- load and apply public search policy;
- normalize and score search index records;
- render search results;
- manage search-specific performance instrumentation.

Search files should not:

- redesign the search JSON payload schema as part of this request;
- become the place for general catalogue list rendering unless search and non-search routes genuinely share the same component;
- force non-search routes to load search runtime code.

Search may need its own internal substructure later.
That is a file-level or subfolder decision inside `search/`, not a reason to reopen the top-level folder map.

## Function And Module Boundary Criteria

Use responsibility, reuse, dependency direction, and route cost to decide whether a function belongs in an existing module or should become a new module.

Add a function to an existing module when:

- it serves the same responsibility already named by that module;
- it uses the same inputs and abstractions as the existing functions;
- adding it does not require route-specific flags or optional behavior branches;
- the module remains easy to describe in one sentence;
- importing the module will not make routes load unrelated code.

Create a new module when:

- the function introduces a second responsibility;
- it would make the existing module name vague or misleading;
- it needs different dependencies from the rest of the module;
- it is reused by a different ownership area;
- it would cause a route to import code it does not need;
- testing or reviewing it separately would make the code clearer;
- the existing module would need configuration flags to keep behavior straight.

A practical test: if the module's purpose sentence needs "and", split it or rename it.

For this project, prefer small focused modules over fewer broad files.
Do not create microscopic files with no meaningful responsibility, but do not keep unrelated functions together just to reduce file count.

## Behavior Porting Rules

Preserve route contracts and interaction semantics.
Normalize incidental presentation or DOM differences when they mainly exist because old inline route code evolved separately.

Port these behaviors exactly unless a separate decision records a change:

- URL and query contracts such as `/works/?work=...`, `/work-details/?detail=...`, `/series/?mode=moments`, selected series state, and pagination state;
- browser back and forward behavior for route state;
- existing localStorage keys and stored preferences, especially series view, sort, and page state;
- fallback states for missing work, detail, moment, empty list, and failed fetch cases;
- keyboard, swipe, and previous/next navigation semantics;
- public link targets for work cards, series links, moment links, and detail links.

These differences may be normalized when doing so supports a concise shared module:

- markup differences between work cards on `/recent/`, `/series/`, and `/works/`;
- small empty-state wording or wrapper differences;
- thumbnail and image attribute parsing differences;
- repeated sort, filter, or view-control wiring;
- inconsistent CSS class or data-attribute names that exist because route scripts evolved separately;
- loading and error DOM conventions;
- tiny layout or label differences that are not meaningful user-facing distinctions.

Do not normalize a behavior just because it is inconvenient to port.
Normalize only when the difference is incidental and the resulting shared module is simpler, faster, or easier to maintain.

## Component Normalization Rule

When routes currently implement the same UI concept with different DOM, CSS hooks, or JavaScript code, the migration should create one component and normalize those differences into a stable component contract.

Routes may pass:

- route-specific data;
- small presentation parameters;
- link behavior;
- paging or sizing configuration;
- current or selected item state.

Routes should not keep separate implementations of the same UI concept just because the current legacy code differs.
Different route data does not justify a different component by itself.

For thumbnail grids:

- use one thumbnail grid component;
- allow parameters for rows, columns, page size, paging behavior, item link behavior, caption mode, and selected or current item state;
- preserve the existing thumbnail-grid page persistence behavior;
- let routes decide which records belong in the grid;
- let the component own grid DOM, paging controls, image/caption rendering hooks, and empty, loading, or error display where applicable.

For images and captions:

- use shared media parsing and size helpers;
- use one image component and one caption component;
- let routes pass caption data and link behavior;
- let components own DOM markup and image attributes.

For metadata:

- use a metadata panel component family;
- let routes pass fields, labels, values, links, and grouping;
- let the component own DOM layout, repeated field markup, and missing-value behavior.

The refactor should replace route-local UI implementations with component calls behind the same user-visible behavior.

## Component And Runtime Foundation Examples

The first implementation slices should think at component and runtime-foundation level, not route level.
Routes are integration targets after the foundations exist.

The first foundation slice is the thumbnail grid/list component.
It is intentionally chosen as the architecture stress test.
If this component cannot be refactored from the existing code while preserving behavior inside the new framework and module structure, the migration concept needs to be revisited before easier components hide the problem.

A sensible foundation order is:

1. Thumbnail grid/list.
2. Navigation.
3. Image and image caption.
4. Metadata panel.

### Navigation

Navigation is a runtime foundation because back links, persistent history behavior, keyboard movement, swipe behavior, and previous/next movement appear across catalogue routes.

Navigation modules should provide focused primitives that routes can compose.
They should not fetch catalogue payloads or render route content.

Candidate navigation modules include:

- back-link and return-target handling;
- persistent history state;
- previous/next item navigation;
- keyboard navigation;
- swipe navigation.

### Image And Image Caption

Image display is a component foundation because public catalogue routes repeatedly render media with captions, dimensions, responsive sizing, and links.

Image modules should separate:

- media path and size parsing in `shared/`;
- DOM rendering for images and captions in `components/`.

Candidate modules include:

- image sizing helpers;
- responsive image attribute helpers;
- image component;
- image caption component;
- linked image component where the link behavior is a clean option.

### Metadata Panel

Metadata panels are component foundations because work pages and work-detail pages both display structured descriptive data.

The component should define the DOM contract for labels, values, grouped fields, missing values, and linkable values.
Routes should provide normalized data; the component should not fetch work payloads or parse route query state.

Candidate modules include:

- metadata panel;
- metadata row;
- metadata link list;
- compact metadata summary where a distinct compact concept is needed.

### Thumbnail Grid/List

Thumbnail grid/list is one component family, not separate grid and list components.
Grid and list are modes of the same catalogue presentation concept.

Thumbnail grid/list is the first foundation slice because it appears in work details, works in series, series index, and related catalogue lists.
It touches images, captions, pagination, page persistence, item links, current or selected item state, and layout modes.
That makes it the best early test of whether the target architecture can handle a complex existing UI concept without becoming flag-heavy or route-local again.

The component should own repeated layout and item rendering structure.
Routes should decide which records belong in the grid and provide normalized item data.

Candidate modules include:

- thumbnail grid/list;
- thumbnail grid/list item;
- grid/list mode handling;
- grid/list empty state;
- grid/list pagination or incremental loading controls where needed.

Additional likely component families include work cards, series cards, moment cards, pagination, empty states, loading states, error states, and reusable route controls.
These should be created when the concept is clear, even if the first route migration uses the component once.

## First Integration Route Selection

Choose the first integration route after the thumbnail grid/list foundation exists.
Do not preselect a route before the component contract is visible.

Prefer the route that gives the clearest proof of the component contract with the least unrelated migration work.
`/work-details/` may be a good candidate because it is likely one of the simpler routes.
A route closer to `/series/` may be better if it exercises grid/list behavior more directly.

The first integration route is a proof point for the foundation slice, not a route-first migration strategy.

## Route Coverage

The migration must cover the public catalogue routes:

- `/series/`
- `/series/?mode=moments`
- `/recent/`
- `/works/`
- `/works/?work=...`
- `/work-details/?detail=...`
- `/moments/?moment=...`
- `/catalogue/search/`

Docs Viewer public scopes such as `/library/` and `/analysis/` are not part of this catalogue runtime architecture.
They already have their own public runtime ownership model.

## Search Refactor Scope

Catalogue search is part of this module-architecture refactor, but only within the structural scope of the refactor.

In scope:

- place current search route code into the target route, component, shared, and search ownership structure;
- treat the search UI as componentized public catalogue UI where the concepts are reusable;
- make search runtime calls consistent with the new module structure;
- remove unnecessary search-related JavaScript calls or loads when they are structural waste;
- preserve current search behavior while replacing route-local or poorly owned code.

Out of scope:

- optimizing the search JSON payload;
- reducing or reshaping the search index data;
- changing search policy;
- changing ranking, matching, or result semantics;
- deciding which fields belong in search JSON.

Search payload and policy work remains a separate request.
This request should not inspect or redesign what data is in the search JSON unless an obvious structural blocker prevents the current behavior from being preserved.

## Non-Goals

- Do not introduce a public-site build, copy, bundling, or transpilation step.
- Do not redesign catalogue JSON payload schemas.
- Do not refactor Studio generated-data ownership as part of this request.
- Do not make public search JSON optimization part of the first module migration.
- Do not preserve old script filenames, globals, or boundaries for compatibility.
- Do not add compatibility aliases for old module paths.
- Do not redesign the public catalogue UI.

## Migration Strategy

The implementation should proceed in controlled slices:

1. Define and document the target module map.
2. Create the new module folders and minimal shared primitives.
3. Build the first low-level component/runtime foundation slice.
4. Use a low-risk route as the first integration target once the relevant foundations exist.
5. Build additional foundations before routes need them, rather than forking route-local code.
6. Port route entrypoints onto the established foundations.
7. Normalize small UI differences only where they remove duplicated route logic.
8. Keep generated catalogue data structures stable.
9. Move catalogue search runtime into the new structure within the structural-only search scope.
10. Remove old extracted route scripts after the public routes no longer load them.

Each route migration should verify behavior against the current route before deleting the legacy script it replaces.

## Temporary Workflow Change

During this refactor, the public-site GitHub Actions workflow should not run automatically on pushes to `main`.
The migration is expected to involve many local commits and local verification runs.
Automatic `main` push runs would add noise while the deploy root is being refactored.

The workflow should keep:

- `workflow_dispatch`, so the public-site validation/upload/deploy path can be run manually when needed;
- `pull_request`, so review branches can still get workflow feedback when relevant.

This is an intentional temporary change for the catalogue runtime migration.
After the refactor is complete, restore the `main` push trigger for `site/**`, `site-tools/**`, `bin/site-validate`, and `.github/workflows/public-site.yml`.

## Child Docs

- [Public Catalogue Runtime Module Architecture Slices](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-slices)

## Decisions Needed

No open design decisions remain.
Implementation should proceed with the thumbnail grid/list foundation first, then integrate routes incrementally while keeping search structural-only.

## Verification Expectations

- Use JavaScript syntax checks for changed modules.
- Use manual browser testing for touched routes and component states.
- Do not run automated browser smoke tests by default.
- Do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.
- Keep validation notes focused on checks actually performed and materially relevant to the slice.
