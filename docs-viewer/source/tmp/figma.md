---
doc_id: figma
title: "figma"
added_date: 2026-05-26
last_updated: 2026-06-26
---

https://www.figma.com/pricing/

https://excalidraw.com


For this repo, the most useful format is usually:

1. **Annotated screenshot or sketch**
   - PNG/JPEG is fine.
   - Mark regions with labels like “filters”, “run list”, “details panel”.
   - Add notes for behavior/state, not just layout.

2. **Simple wireframe in Excalidraw, Figma, or a hand sketch**
   - Export as PNG.
   - Low fidelity is enough. Boxes and labels are better than polished mockups if the workflow is still changing.

3. **Short workflow notes**
   Include:
   - primary user goal
   - required actions
   - important empty/loading/error states
   - what should be visible without scrolling
   - what can be hidden behind details/modals

Best lightweight template:

```text
Screen: /admin/checks/
Goal: Run a report and review output quickly.

Must show:
- report + target filters
- run button
- recent runs
- selected report output

States:
- idle
- running
- failed
- no runs
- selected run loaded

Notes:
- controls should be compact
- output is more important than run history
- mobile is not important for this route
```

If you send an image plus those notes, I can translate it into implementation while keeping it consistent with the existing Admin/UI Catalogue guidance.