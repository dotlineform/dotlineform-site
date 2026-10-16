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

## Mermaid Retirement

The Mermaid-specific Docs Viewer pipeline was retired on 2026-10-16. There is no `.mmd` image intake, registered Mermaid producer, Node/CLI package, vendored browser renderer, fenced-diagram conversion, theme-pair generation or editable-source opening endpoint. A fenced Mermaid block in a Docs Viewer document remains an ordinary code block.

Studio's maintained Markdown lives in repository `documentation/studio/`, outside Docs Viewer. Existing Mermaid fences there remain unchanged and can be interpreted by an external Markdown viewer. If a published document needs one of those diagrams, render it externally and import the SVG.

The existing Working metadata contained no Mermaid diagrams or companion relationships at retirement. Its 245 document records were converted directly to `collection` plus one `media` reference list without rebuilding documents or changing pending publication selections. Old local media, external tool installations and unreferenced files were not purged; cleanup remains manual.

[Publication Media](data_model/Publication_Media.md) explains the saved reference list. [Media And Asset Handling](Media_And_Asset_Handling.md) owns Save, exact removal and publication behavior. Historical Mermaid tests and smoke-profile entries remain unreviewed retirement residue; their removal or replacement requires separately agreed test work.
