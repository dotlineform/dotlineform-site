---
draft: false
doc_id: d-20260513-214100-0a7f44
title: UI Status
added_date: "2026-05-13 21:41:00"
last_updated: "2026-08-04 12:02:52"
parent_id: d-20260424-000000-50b63f

---
# Doc UI Status

Ordinary document front matter can carry a free-text `ui_status` value for editorial context. The shared viewer currently displays a status icon for `planned` and `report`. Other saved values can still describe delivery status in repository documentation.

Document readiness uses the separate boolean `draft`. Named-collection documents omit `ui_status`. A status word such as `draft` or `done` does not select publication. [Source contract](Builder.md#source-contract)

The canonical [viewer code config](../../docs-viewer/runtime/js/shared/docs-viewer-code-config.js) owns the icon mapping. Project any change to its public copy through the [site-code workflow](Run_Checks.md#docs-viewer-site-code-projection).
