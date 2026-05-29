---
doc_id: panel-sizes
title: panel sizes
added_date: 2026-05-20
last_updated: "2026-05-20 19:37"
parent_id: ""
---
# panel sizes

Current Docs Viewer desktop layout is defined in `docs-viewer/static/css/docs-viewer.css`.

Assuming default `1rem = 16px` and desktop container max width:

| State | Total Docs Viewer content width | Index panel | Gap | Doc panel grid column |
| --- | ---: | ---: | ---: | ---: |
| Index expanded | `980px` | `260px` | `22px` | `698px` |
| Index collapsed | `980px` | `2.8rem` = `44.8px` | `22px` | `913.2px` |

Relevant CSS:

```css
.container { max-width: var(--container); } /* --container: 980px */

.docsViewer {
  grid-template-columns: minmax(220px, 260px) minmax(0, 1fr);
  column-gap: var(--docs-viewer-space-5); /* resolves to 22px */
}

.docsViewer[data-sidebar-state="collapsed"] {
  grid-template-columns: 2.8rem minmax(0, 1fr);
}
```

A couple of important distinctions:

- The **doc panel grid column** is `698px` expanded / `913.2px` collapsed.
- The actual rendered prose content is also capped by `--docs-viewer-measure`: `72ch` normally, and `min(96ch, 100%)` when collapsed. So the doc column can be wider than the readable text line.

On `rem`: I would not use `rem` as the main way to specify panel-width requirements. Use:
- `px` for fixed layout panels and breakpoints, like “index panel should be 280px”.
- `ch` for readable prose measure, like “doc content should cap around 72ch”.
- `rem` for controls, padding, icon rails, and things that should scale with text size.

For this requirement, I’d express it as: “within the 980px Docs Viewer content area, expanded index is 260px plus 22px gap, collapsed index rail is 2.8rem plus 22px gap; doc column takes the remaining width.”
