---
draft: false
doc_id: d-20261018-191000-687cad
title: Document Image Detail
added_date: "2026-10-18 19:10:00"
last_updated: "2026-11-18"
summary: Opt-in opening for standalone raster and SVG document images through Content Detail.
parent_id: d-20260424-000000-50b63f
---
# Document Image Detail

Use Source **Directives → Image detail** immediately before a standalone Markdown image or Docs-owned image token. **Add image → Image detail** inserts the same comment before a new raster or SVG image. In **Edit image**, the checkbox shows whether the standalone image has that directive. **Apply** adds or removes the comment and updates the image token in the source buffer. **Save** persists the edit.

```md
<!-- dotlineform:image-detail -->

![Description]([[media:docs/img/<doc_id>/example.webp]])
```

## Scope And Association

The reader associates the comment with the immediately following standalone image, including the builder's Docs-owned image figure. Blank lines are allowed. Prose, multiple images, a link wrapper or another block interrupt the association. Literal code and comments in preformatted/script/style/textarea/SVG elements do not activate it. An unmatched directive remains invisible. Catalogue images use their own Media View opening control. [Catalogue Media View](Catalogue_Media_View.md)

## Viewer And Lifecycle

Click or tap the inline image or use **Open image** to move the loaded image into the shared Content Detail viewport. Its alt text supplies the title, falling back to the HTML title or `Image N`. Back restores the image and scroll position and returns keyboard focus to **Open image**. **Open in new tab** uses the loaded image URL. Manage and Public share this adapter, while Docs Review keeps its read-only package view.

Raster detail can display only the stored resolution. Choose **Preserve original resolution** at Add/Edit when the image needs that detail. Save or rebuild to regenerate an authored directive, then Publish for Public. Runtime/CSS changes follow the public code projection. The shared stylesheet keeps the button within the figure's ordinary width and alignment rules and centres the detail controls in the header. [Media intake](Media_And_Asset_Handling.md#add-a-new-image-or-download) · [Image detail adapter](../../docs-viewer/runtime/js/shared/docs-viewer-image-detail.js)
