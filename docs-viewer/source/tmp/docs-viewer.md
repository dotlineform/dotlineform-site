---
doc_id: docs-viewer
title: "docs viewer"
added_date: 2026-05-30
last_updated: 2026-06-26
ui_status: draft
parent_id: ""
---

## doc viewer toolbars

- `docsViewer__controls`
  - mount point only, plus status/bookmark row
- `docsViewer__topBar`
  - `docsViewer__viewerToolbar` with `role="toolbar"` and `aria-label="Viewer controls"`
    - scope selector
    - recently added
    - search input
    - panel controls group: folder toggle + info toggle
  - management toolbar mount
    - `docsViewer__manageActions` with `role="toolbar"` and `aria-label="Management actions"`
      - Actions
      - Show
      - show non-viewable
    - theme toggle sits in the management row beside that toolbar

So search and recents are not floating controls. Structurally they are inside the viewer toolbar. The visual top row is a top bar containing two toolbar groups: viewer controls on the left, management controls on the right.

---

## panel widths

[docs-viewer.css](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/static/css/docs-viewer.css:23):

```css
--docs-viewer-index-width: 16.25rem; /* current: 260px / 16.25rem; try 14rem-20rem */
--docs-viewer-doc-width: var(--docs-viewer-content-measure, var(--content-measure, 72ch)); /* current: 72ch; try 60ch-88ch */
--docs-viewer-info-width: 17.5rem; /* current: 280px / 17.5rem; try 14rem-22rem */
--docs-viewer-panel-width-min: 13.75rem; /* current: 220px / 13.75rem */
```

The grid rails and sidebar now derive from those tokens, so you can experiment by changing only the three main panel values: `index-width`, `doc-width`, and `info-width`.

---

> we didn't discuss the framework question for docs viewer

Correct. We only framed the framework checkpoint for **Studio**.

For **Docs Viewer**, I would treat it as a separate decision with a higher bar. Docs Viewer already has more established app architecture work around app session, state domains, controllers, hosted views, public/manage mode, and service adapters. Introducing a framework there would risk disturbing a boundary that has recently been tightened.

My recommendation:

- Do **not** fold Docs Viewer framework evaluation into the Studio app-shell request.
- Add a separate Docs Viewer framework checkpoint only after current Docs Viewer architecture cleanup is stable.
- Use different evidence than Studio:
  - repeated controller/view lifecycle boilerplate
  - growing hosted-view composition complexity
  - public/manage mode branching becoming hard to verify
  - state-domain updates becoming too manual
  - modal/action workflow duplication
  - browser smoke burden increasing because behavior is too hand-wired
- Keep public read-only Docs Viewer weight as a hard constraint.

For now: Studio can collect framework evidence during its shell migration. Docs Viewer should stay vanilla unless its own architecture docs or future task tracker shows repeated framework-like machinery.