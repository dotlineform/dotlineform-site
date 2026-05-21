---
doc_id: "_tmp"
title: tmp
added_date: 2026-05-20
last_updated: "2026-05-20 19:37"
parent_id: ""
sort_order: 40000
viewable: false
---
# tmp

## javascript risk mitigation

we are working on _docs/javascript-inventory-implementation-plan.md
please proceed with batch 1

---

<https://developers.openai.com/codex/migrate?utm_campaign=ML_MIX_GWT_AW_codexnewsletter_OF_EX_MAY_18&utm_content=utm_content&utm_medium=email&utm_source=sendgrid&utm_term=utm_term>

<https://developers.openai.com/codex/skills>

---

here is a potential upcoming requirement for docs viewer. it is still rough. what is the blast radius for this request as it stands, and does it have any relationship with any of the risk mitigation work identified?

request:
docs viewer: the index panel currently expands/collapses.
- we need it to have a third state where it expands to fit the full content area. It can therefore be in states collapsed, normal, expanded.
- the current expand/collapse button is used to expand/collapse, moving through the states collapsed, normal, expanded.
- when expanded, the currently selected document is hidden.
This new behaviour is a precursor to introducing alternative index structures (e.g. graph) which will only be displayed in 'expanded mode'.

---

Blast radius is **medium**, mostly because this changes layout state semantics rather than just CSS.

Current sidebar state is binary in [docs-viewer.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/docs-viewer/js/docs-viewer.js:587): `state.sidebarCollapsed` plus `data-sidebar-state="collapsed|expanded"`. The first design issue is that today’s `"expanded"` really means “normal”. A third state would need a small state-machine cleanup.

Likely touched files:

- [docs-viewer.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/docs-viewer/js/docs-viewer.js:587): replace boolean `sidebarCollapsed` with something like `sidebarState: "collapsed" | "normal" | "expanded"`, update localStorage, toggle order, labels, resize behavior.
- [docs-viewer.css](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/docs-viewer/css/docs-viewer.css:23): add grid rules for full-width index mode and hide the main/document column in expanded mode.
- [_includes/docs_viewer_shell.html](/Users/dlf/Developer/dotlineform/dotlineform-site/_includes/docs_viewer_shell.html:145): possibly update button label/icon assumptions, maybe no structural change.
- [docs-viewer-document-controller.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/docs-viewer/js/docs-viewer-document-controller.js:160): only if “expanded mode hides selected document” is handled as pane state rather than pure CSS.
- [docs-viewer-management-interactions.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/docs-viewer/js/docs-viewer-management-interactions.js) and management CSS: needs smoke testing because drag/drop/context menu operate in the index.

Relationship to risk mitigation: yes, directly.

- It lands on [docs-viewer.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/docs-viewer/js/docs-viewer.js:587), which the new inventory marks as high risk because shared runtime state can attract unrelated behavior.
- It touches the “status ownership” lesson indirectly: this should become an **index layout/view-state owner**, not another broad set of ad hoc conditionals in the entry controller.
- It relates to [docs-viewer-javascript-inventory.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/docs-viewer-javascript-inventory.md:91): “alternative index structures” are exactly the kind of future feature that argues for a focused boundary before the entry controller grows again.
- It also brushes [docs-viewer-runtime-boundary.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/docs-viewer-runtime-boundary.md:116): a graph index is okay as an alternate index view if the viewer remains the same route/content model, but a fundamentally different navigation model would be a runtime-boundary concern.

Implementation recommendation: don’t just extend `sidebarCollapsed`. Add a small `docs-viewer-index-layout` or similar helper if this is genuinely a precursor to graph/index modes. For a one-off tri-state, it is easy to do inline; for “expanded mode hosts alternate index structures”, inline would increase the exact risk we just documented.

Open requirement points before implementation:
- In expanded mode, does clicking a document select it but keep content hidden, or return to normal mode?
- Does expanded mode apply on mobile, where collapse is currently disabled?
- Should search/recent results also be hidden in expanded mode, or only document content?
- Should the tri-state be persisted per scope, and how should existing stored `"expanded"` values migrate to `"normal"`?

---

most of these open questions are fine (e.g. mobile = no) but the big question is around the index/document relationship. I don't think the current 'click on index, show document' is relevant here, because a graph index is about surfacing document relationships. we have only just added a simple semantic token into the source markdown documents, this is going to be an area of focus. it might be that if you open a doc from the graph, it opens in a new window, or displays summary information in a pop-up or info panel. the whole direction is that the index becomes more than a helper, it is an interactive surface. so this will need be supported by distinct modules, especially since a graph index will likely need external libraries as well.

Yes. With that direction, I would treat the requested tri-state less as “sidebar gets wider” and more as the first step toward an **index workspace mode**.

That changes the architecture call:

- **Do not** bury this in `docs-viewer.js` as more sidebar conditionals.
- Create a distinct owner for index mode/layout state, probably something like `docs-viewer-index-controller.js` or `docs-viewer-index-workspace.js`.
- Keep the current tree index as one index surface.
- Let expanded mode become a host area for alternate index surfaces later: tree now, graph later.
- Keep document opening behavior separate from graph interactions. A graph node click should not inherit the current nav-link behavior by default.

The graph requirement has a clear relationship to the risk work: it is exactly the kind of feature that could push `docs-viewer.js` and `docs-viewer-sidebar.js` from “acceptable orchestration/rendering” into mixed interactive-surface controllers. The new inventory should probably get updated when this requirement firms up, because it introduces a new risk theme: **index surface ownership**.

I would model the next slice like this:

- `docs-viewer-index-state.js` or similar: owns `collapsed | normal | expanded`, persistence, toggle transitions, labels.
- `docs-viewer-index-controller.js`: owns index workspace behavior and decides which index surface is active.
- Existing `docs-viewer-sidebar.js`: remains the tree renderer, not the owner of future graph behavior.
- Future `docs-viewer-graph-index.js`: graph-specific rendering/interactions, lazy-loaded only in expanded mode if external libraries are needed.

For the immediate tri-state requirement, the implementation can still be modest: introduce the state boundary, make expanded mode hide the document/search pane, and keep rendering the existing tree index full-width. That gives you the structural affordance without committing to graph behavior yet.

The main requirement to settle before implementation is this: in expanded mode, should tree item clicks continue navigating documents, or should expanded mode suppress document navigation and treat the tree as an index surface only? Given your direction, I’d lean toward keeping current tree clicks as-is for now, but making graph behavior independent when it arrives.

---

yes, the tree-index bahviour doesn't change, it just makes viewing a many-levels tree easier because of the expanded width. but the expanded mode also gives us a generic surface in which to put other things later.

That’s a good boundary.

So the requirement becomes:

- Add a tri-state index layout: `collapsed`, `normal`, `expanded`.
- Existing tree index behavior stays unchanged in all states.
- `expanded` gives the index full content width and hides the document/search pane.
- The implementation should create an index workspace/layout boundary now, so future graph/semantic views can plug into expanded mode without growing `docs-viewer.js`.
- No mobile behavior change; keep the current desktop-only collapse/expand control.
- Existing persisted `expanded` should migrate to `normal`, because today’s stored value means “not collapsed”, not new expanded workspace mode.

I’d implement the first slice with:
- a small focused module for index layout state and labels
- CSS for `data-index-layout="collapsed|normal|expanded"` or equivalent
- `docs-viewer.js` wiring only
- no graph code yet
- a browser smoke check for the three states, tree click behavior, and document pane hiding/restoring

This is now a cleaner medium-small feature rather than a risky layout hack.

---

I suppose that the key point to get right now is that the expanded mode isn't just a bigger tree index. it is that there is a generic panel which can be collapsed, normal or expanded, and it is currently populated with a tree index which fills the space available to it. it is not the index itself changing or expanding.

Exactly. That distinction is the architecture.

I’d name and model it as an **index panel** or **index workspace**, not “expanded tree index”.

Current content:
- panel content = tree index
- tree index behavior = unchanged
- tree index layout = fills whatever panel size it is given

Panel state:
- `collapsed`: panel is icon-width, tree hidden
- `normal`: panel is sidebar-width, tree visible
- `expanded`: panel occupies the main content area, document/search pane hidden, tree visible with more width

Future content:
- panel content could be tree, graph, semantic references, relationship map, etc.
- expanded mode is the natural host for richer interactive index surfaces
- graph interactions do not need to inherit tree document navigation behavior

That means the implementation should avoid names like `sidebarExpanded` or `expandTree`. Better names would be:

- `indexPanelState`
- `docs-viewer-index-panel.js`
- `data-index-panel-state`
- `toggleIndexPanelState()`
- labels like `Collapse index panel`, `Restore index panel`, `Expand index panel`

The existing `docs-viewer-sidebar.js` can stay as a tree renderer inside the panel. The new state owner should be about the panel, not the tree.

---

great. I will create a new change request for this, which we can refine in a later session. it will take us up to the point where we have a UI space ready for a graph index, but the actual index will be a separate project. as part of this change request, we will determine which generic tasks in docs-viewer-javascript-inventory.md need to be done first. we'll keep the two separate but it sounds like some prioritised tasks are now pre-requisites for the change request. please add a top-line summary of this to docs-viewer-javascript-inventory.md.