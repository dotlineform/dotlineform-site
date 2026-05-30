---
doc_id: docs-viewer
title: "docs viewer"
added_date: 2026-05-30
last_updated: 2026-05-30
ui_status: draft
parent_id: ""
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