---
draft: false
doc_id: d-20260719-123719-fb7565
title: Document Diagrams
added_date: "2026-07-19 12:37:19"
last_updated: "2026-10-16"
summary: Create diagrams externally and import finished SVG images through the ordinary document-media workflow.
parent_id: d-20260424-000000-50b63f

---
# Document Diagrams

Docs Viewer treats a diagram as an ordinary SVG image. Create or edit it in an external tool, export the finished SVG and select it with Source **Add Image**. Source Save sanitizes the SVG, writes it beneath the document's configured `svg/<doc_id>/` folder and completes exact generation. Publish later transfers the selected ready bytes through the normal document/media queue.

## Authoring And Replacement

Keep the editable diagram source with the external tool or project that owns it. Docs Viewer stores and publishes the imported SVG; it does not manage a companion source file. Use the image's alt text, optional caption and summary to describe it. Reopen its image token in Source to change presentation or select replacement SVG bytes, then Save.

An SVG has one authored appearance. Set its colours and background in the external tool so it works with the intended reader presentation. Docs Viewer does not create automatic light/dark variants.

## Reader Detail View

Imported SVG images retain the shared **Open diagram** detail view and **Open in new tab** action. The detail view uses the stored SVG's stable media URL and returns the same image presentation to the document when closed. Raster image, file and interactive HTML workflows retain their existing owners.

## Repository Documentation

Maintained Studio Markdown lives in repository `documentation/studio/`, outside Docs Viewer. Existing fenced diagrams can be interpreted by an external Markdown viewer. Render a diagram externally and import its finished SVG when it is needed in a published document.

[Publication Media](data_model/Publication_Media.md) explains the single saved reference list. [Media And Asset Handling](Media_And_Asset_Handling.md) owns Save, exact removal and publication behavior.
