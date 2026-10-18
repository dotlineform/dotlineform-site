---
draft: false
doc_id: d-20261018-191000-687cad
title: Document Image Detail
added_date: "2026-10-18 19:10:00"
last_updated: "2026-10-18"
summary: Opt-in image opening through the existing SVG Content Detail panel.
parent_id: d-20260424-000000-50b63f
---
# Document Image Detail

Use Source **Directives → Image detail** immediately before an image to add a small **Open image** icon button above it:

```md
<!-- dotlineform:image-detail -->

![Description]([[media:docs/collections/library/img/example.webp]])
```

The same directive works before a canonical `[[image:…]]` token, including its caption and summary. The displayed image stays in its document position until the button is activated. Its alt text supplies the detail title, with its HTML title or `Image N` used when alt text is empty. The button's tooltip and accessible label are **Open image**.

## Scope And Association

The directive selects the immediately following standalone image, allowing whitespace/blank lines between them. The reader accepts a direct image, a Markdown paragraph containing only one image, or the builder's Docs-owned image figure. A paragraph containing prose, multiple images, a linked image, a heading or other intervening content does not select a later image. Catalogue images retain their separate Media View owner. Unmatched directives remain invisible HTML comments and produce no control.

The shared image-detail adapter reads actual comment nodes in the already rendered document. Its exact comment contents are `dotlineform:image-detail`; examples rendered as code remain text, and comments inside literal code/preformatted, script/style, textarea or SVG containers are ignored. Source insertion preserves selected text after the directive and supplies block spacing. No new service request, source parser, image conversion, byte lookup or complete document rebuild is needed to interpret it.

SVG and raster images use the same optional directive and **Open image** button above the selected image. SVGs without the directive display as ordinary images without an expand control. Generated media markup does not select detail behavior; the browser uses only the authored directive.

## Viewer And Lifecycle

Public and Manage compose `docs-viewer-image-detail.js` into the existing Content Detail host. Review retains its read-only package composition without this interactive adapter. The adapter receives the exact current document/collection target and mount generation from the document controller, associates only the selected image occurrences and retains their current loaded file URLs. It moves the existing image element into the expanded image viewport; Back returns that element to its document wrapper. The shared host restores document position and invocation focus and exposes **Open in new tab** for the captured image URL. This introduces no document navigation entry or separate viewer panel.

The viewport uses the existing SVG detail sizing/scroll behavior. Raster detail displays the stored image's available resolution; it cannot recover pixels discarded by conversion. Choose **Preserve original resolution** during Add/Edit image when the source needs more detail. No zoom tools, alternative originals or additional image variants are implied.

SVG and raster image detail center Back, the title and Open in new tab as one group in the top row. Mirrored side columns keep the group centered between the outer edges, with Home on the left and Manage Actions followed by the theme control on the right; long titles wrap within the group on narrow screens. The separate management toolbar mount participates directly in the row grid, outside the centered image controls.

`docs-viewer.css` owns image wrappers, the above-image control and the common detail viewport. Docs-owned figures include the wrapper in their fill-width/natural-width, left/right and public narrow-screen layout rules so the control does not change the image/caption placement. The shared Content Detail icon styling also serves Table detail. Public runtime/styles use the explicit tracked site projection. Existing generated document payloads remain valid; normal Source Save or exact Rebuild includes a newly authored directive, and public source changes follow Publish. Runtime projection and deployment remain separate operations.

## Evidence And Limits

[Image Detail Directive](deliveries/Image_Detail_Directive.md) records implementation, static checks, projection and code-review evidence. New behavior tests and browser automation require separately approved test work. Normal-use confirmation covers insertion, the control's placement, ordinary/collection opening, Back, new-tab opening and optional SVG behavior.
