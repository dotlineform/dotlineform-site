---
doc_id: studio-plan
title: "Implementation Plan"
added_date: 2026-03-28
last_updated: 2026-03-28
parent_id: _archive
sort_order: 90
published: false
---

**Phase 1 Task List**

This is the concrete implementation plan for the first pass.

**Phase 1: Shared data and transport extraction**
Goal: remove duplicated fetch/parse/endpoint logic without changing UI behavior.

Tasks:
1. Add a shared Studio data module.
Target: `assets/studio/js/studio-data.js`
Output:
- shared `fetchJson`
- shared loaders for registry, aliases, assignments, groups
- shared lookup builders and normalization helpers that are already duplicated

2. Add a shared Studio transport module.
Target: `assets/studio/js/studio-transport.js`
Output:
- local endpoint constants in one place
- shared health probe
- shared `postJson`

3. Repoint small modules first.
Targets:
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/tag-studio-index.js`
- `assets/studio/js/series-tags.js`
Output:
- these modules import shared helpers instead of owning their own fetch/parse copies

4. Repoint large modules second.
Targets:
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/tag-studio.js`
Output:
- transport and data loading moved out
- no render or UX changes yet

Benefits:
- immediate reduction in duplication
- lower risk for later controller splits
- consistent parsing behavior across Studio pages

Key risks:
- shared normalizers may not match every current edge case
- one helper bug can affect multiple pages

Verification:
- load `tag groups`, `series tags`, `tag registry`, `tag aliases`, `series tag editor`
- confirm data loads and error states still render
- confirm local save mode detection still flips correctly

**Phase 2: Move inline page controllers out of markdown**
Goal: separate page/template structure from behavior.

Tasks:
1. Create `assets/studio/js/series-tag-editor-page.js`
2. Move logic from `studio/series-tag-editor/index.md` into the module
3. Pass Liquid/runtime values through `data-*` or inline JSON, not embedded logic
4. Create `assets/studio/js/studio-works.js`
5. Move logic from `studio/studio-works/index.md` into the module

Benefits:
- cleaner content files
- easier review and testing
- clearer split between structure and behavior

Key risks:
- Liquid values currently injected into JS may break if moved incorrectly
- query param behavior must remain exact

Verification:
- `?series=` loading still works
- works index sorting/filtering still works
- selected-work media sync still works

**Phase 3: Split tag editor by responsibility**
Goal: isolate business logic and save logic from DOM control code.

Tasks:
1. Extract pure editor/domain logic from `assets/studio/js/tag-studio.js`
Output:
- tag resolution
- assignment normalization
- diff calculation
- work-state transforms

2. Extract save logic
Output:
- health probe
- post save
- patch snippet generation

3. Leave one controller module for:
- init
- render orchestration
- event wiring

Benefits:
- highest-value modularity win
- save/diff rules become testable
- future editor changes get safer

Key risks:
- selected-work state is fragile
- save semantics are high regression risk

Verification:
- adding/removing tags
- selecting multiple works
- inherited vs override chip behavior
- patch fallback
- local save success/failure paths

**Phase 4: Split tag registry**
Goal: separate registry UI from registry mutation logic.

Tasks:
1. Extract registry service layer from `assets/studio/js/tag-registry.js`
2. Extract validators and patch builders
3. Keep page/controller responsible only for render/wire/state transitions

Benefits:
- modal flows become understandable
- import/edit/delete/demote paths are easier to maintain
- same structure as editor split

Key risks:
- preview/mutation/result messaging is intertwined
- easy to break patch fallback wording or refresh timing

Verification:
- import add/merge/replace parsing
- edit tag description
- create tag
- delete preview and delete confirm
- demote flow in post and patch modes

**Phase 5: Split tag aliases**
Goal: mirror the registry architecture for consistency.

Tasks:
1. Extract alias service layer from `assets/studio/js/tag-aliases.js`
2. Extract alias validators and patch builders
3. Keep page/controller focused on UI state and rendering

Benefits:
- consistent architecture across Studio tools
- alias rules become easier to reason about
- lower future maintenance cost

Key risks:
- current UX mixes modal, prompt, and confirm flows
- alias promote/demote behavior may rely on current sequencing

Verification:
- import aliases
- create/edit alias
- promote alias
- demote canonical tag from aliases page
- patch-mode fallback outputs

**Phase 6: Styling cleanup**
Goal: finish structure/style separation.

Tasks:
1. Move layout CSS from `_layouts/studio.html` into `assets/studio/css/studio.css`
2. Replace residual inline style attributes where safe

Benefits:
- cleaner templates
- easier visual maintenance
- fewer hidden dependencies

Key risks:
- small layout regressions

Verification:
- desktop and mobile spot check for all Studio pages

**Recommended first implementation batch**
Start with:
1. `studio-data.js`
2. `studio-transport.js`
3. rewiring `tag-groups.js`, `tag-studio-index.js`, and `series-tags.js`
