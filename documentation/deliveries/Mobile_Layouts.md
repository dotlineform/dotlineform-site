---
draft: false
doc_id: d-20261117-202611-bbe5a8
title: Mobile Layouts
added_date: "2026-11-17 20:26:11"
last_updated: "2026-11-20"
summary: Accepted public reader layouts for iPad and iPhone, including Index, pinned links, figures, Media View and Moments verse.
ui_status: done
parent_id: d-20260419-000000-d2e47b
---
# Mobile Layouts

Closed on 20 November 2026 after physical-device acceptance. The delivery addressed the public reader on the 11-inch iPad Air and iPhone 15 Pro. Desktop Safari on a 16-inch MacBook Pro supplied responsive viewport comparisons. [Earlier mobile exploration](Public_Mobile_Experience.md)

## Delivered layout

- On iPad landscape, the document uses the space right of Index up to its standard reading width, and pinned links sit below Index in the same sticky column. When Info is open, Index can use half the available sidebar height so both panels can be reached. In iPad portrait, Info follows Index above the document. [Info Panel](../reference/Info_Panel.md)
- The single-column reader starts with the Index search row visible. Search, Recent and the chevron reveal the list. Selecting a document or collection collapses it. The collection button sits above the displayed document. [Reader discovery and return](../reference/Reader_Discovery_And_Return.md#retained-index-views)
- Document figures retain their authored side-by-side proportions at pane widths of 36rem or more. Narrower panes stack image and caption. Media View uses its own inner panel width for the split between an image or Gallery grid and its metadata. Gallery thumbnails wrap at their existing size. [Reader CSS](../reference/CSS_Ownership.md#layout-and-prose) · [Media View](../reference/Catalogue_Media_View.md#gallery-presentations)
- In short landscape viewports, public document paragraphs and the Work catalogue-number line use 100% text-size adjustment. In narrow portrait, axis-aligned Moments verse keeps each authored row at the 47% split, with wrapping inside each side. A title and date with the alignment class each occupy a separate block. [Reader CSS](../reference/CSS_Ownership.md#layout-and-prose)

## How CSS and JavaScript work together

**CSS decides where the Index can collapse.** The compact layout applies up to 820px wide, or up to 960px wide when the viewport height is below 35rem. CSS uses the chevron’s `aria-expanded` value to hide or show the list area. The search row stays visible and the list keeps its scroll box. Outside the compact layout, CSS shows the list in full and hides the chevron. [Reader stylesheet](../../docs-viewer/static/css/docs-viewer.css)

**JavaScript decides when to change the state.** The chevron, Search, Recent and a shared search URL can open the list. A successful same-tab document or collection selection collapses it. Back restores the saved state with the preceding document, and rotation preserves the disclosure state for the next time the compact layout is shown. The mounted Index retains its query and browsing position. [Index renderer](../../docs-viewer/runtime/js/shared/docs-viewer-index-panel-renderer.js) · [Navigation workflow](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js)

**The collection toolbar moves as one piece.** JavaScript uses the same viewport condition to put the toolbar above the document when the collection button is available. The header hosts the toolbar in the wider layout. Both positions use the same control and collection action. [Reader runtime](../../docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js)

## Acceptance and evidence

| Surface | Observed result |
| --- | --- |
| iPad Air | Safari’s 820 × 1180 portrait preset showed “3 symbols” with the collapsed Index, pinned links below it, the collection control above the title, and the half-width image beside its caption. The user confirmed that the layout looked right on the physical iPad Air. The 1180 × 820 landscape preset supplied the initial width comparison. |
| iPhone 15 Pro | Safari’s 402 × 874 and 874 × 402 presets were used for portrait and landscape comparisons, and phone rotation was accepted in Safari. On the physical iPhone, the “3 symbols” Gallery title and links sat beside six thumbnails per row and landscape document paragraphs returned to the expected size. Work portrait was also accepted. |
| Moments | Safari’s portrait preset showed longer phrases wrapping in their own columns in “all the little cracks” (`d-20260215-000000-f5f727`). The user confirmed the portrait correction on the physical device after the date moved below the heading. |

The physical iPhone showed the layout used below the former 760px Media View breakpoint. Safari’s default safe-area insets help explain the narrower landscape viewport. The screenshot suggested about 734px of usable width. The split now responds to the panel itself. [WebKit safe areas](https://webkit.org/blog/7929/designing-websites-for-iphone-x/) · [Safari Responsive Design Mode](https://developer.apple.com/documentation/safari-developer-tools/responsive-design-mode)

Focused JavaScript lint passed for the disclosure changes. Public code projection, `bin/site-code-update --check`, `bin/site-validate` and whitespace checks passed during implementation. The local preview served the updated shell, canonical-style projection, changed browser modules and existing representative document payloads. The final reader changes are recorded in `7e52d257e9`.

## Further review

Acceptance was based on the representative cases above. Dedicated checks for the Work catalogue-number line in landscape, reader zoom, keyboard navigation, Back restoration and long lists remain separate review topics. Broader mobile Catalogue List and rolling Gallery questions can be revisited alongside the earlier reader journeys. Transfer size and loading remain a separate investigation. [Public Mobile Experience](Public_Mobile_Experience.md) · [Site Optimisation](../_working/Site_Optimisation.md)
