---
draft: false
doc_id: d-20260623-000000-c99cef
title: Info Panel
added_date: "2026-06-23 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260424-000000-50b63f

---
# Info Panel

A reader opens Info with **Pin related links** beside a non-empty generated [Related Links](Related_Links.md) section. The panel shows a linked title, the optional builder-rendered summary and a detached copy of the list. The summary preserves line and paragraph breaks and supports restricted inline emphasis. Other Markdown and token syntax displays as literal text. [Summary generation](Builder.md#summary-block)

## Reader workflow

The linked title returns to the pinned document in the current viewer. Following a list link or navigating elsewhere leaves the capture open. Another document's pin replaces it, repeating the same pin leaves it open, and Close releases it. Entering Source or reloading clears the capture. Source editing uses the complete Markdown buffer and its own controls. Above 820px the panel sticks below the top controls, aligned with Index. Long lists scroll within the panel beneath the title and Close. [Source editor](Source_Editing.md) · [CSS ownership](CSS_Ownership.md)

Gallery rows keep their Media View controls. Activation uses the document displayed at that moment, so Media View's Back returns there. Closing Info after the Gallery opens leaves the active view usable. Public and Manage share pinning. Export and Docs Review show the static list. [Media View](Catalogue_Media_View.md)

## Data and exact targets

The pin captures the exact loaded document target and by-ID payload. A collection detail supplies its own collection and document ID. The report host never substitutes for the detail. The detached copy survives replacement of the main-pane mount. Pinning does no relationship, collection or readiness read. An unavailable document gets the ordinary unavailable response when followed. Modified clicks retain native link behaviour. [Related Links freshness](Related_Links.md#generated-data-and-freshness)

## Hosting and lifetime

The shared document coordinator mounts the pin. The Related Links module captures the list and supplies its hosted view. The Info controller owns replacement and Close, the host invalidates superseded loads, and the renderer owns the shell and linked title. Public projects those shared reader modules through the explicit site code inventory. [Document coordinator](../../docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js) · [Related Links runtime](../../docs-viewer/runtime/js/shared/docs-viewer-related-links.js) · [Info controller](../../docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js) · [Runtime](Docs_Viewer_Runtime.md)
