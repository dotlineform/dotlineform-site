---
draft: false
doc_id: d-20261117-202611-bbe5a8
title: Mobile Layouts
added_date: "2026-11-17 20:26:11"
last_updated: "2026-11-20"
summary: Review the public site's layouts, navigation and touch interaction on small screens.
ui_status: proposed
parent_id: d-20261118-235100-64ad2e
---
# Mobile Layouts

Review the public site as a whole on small screens. The first change addresses iPad reading width and pinned links. Further changes follow observations from browsing collections, searching, opening documents and media, and returning to the previous view. [Public Mobile Experience](../deliveries/Public_Mobile_Experience.md)

## Test Devices

- Desktop uses a 16-inch MacBook Pro.
- Tablet uses an 11-inch iPad Air.
- Phone uses an iPhone 15 Pro.

Use desktop Safari for screenshots. Use screenshots from the physical iPad or iPhone when its layout differs substantially from Safari’s simulation.

## iPad Document Width And Pinned Links

In desktop Safari’s 1180 × 820 iPad landscape viewport, Context’s “3 symbols” document was narrower than on desktop. The layout reserved matching space on either side of the document even with Info closed, leaving the right side empty.

The updated public layout is ready in local preview. It uses two columns above 820px and below 94rem, and puts Info after Index in the single column above 760px through 820px. Both rules require at least 35rem of viewport height. The two-column layout reuses the measured toolbar offset and existing scrollable lists. It limits Index to half the available sidebar height when Info is open so the pinned links stay within reach.

The projected stylesheet passed `bin/site-code-update --check` and `bin/site-validate`. The running preview served the updated shell and stylesheet. The user accepted the layout on the physical iPad Air. The detailed checks below cover additional navigation and overflow cases.

- [ ] In iPad landscape at 1180 × 820, check that “3 symbols” uses the space to the right of Index up to the desktop reading width. Open and close Info and check that the document stays in place at the same width. Scroll with both panels open and check that long Index and Info lists remain usable.
- [ ] Check keyboard navigation with Info open in the MacBook, iPad and iPhone layouts.

### iPad portrait Index and images

At 820 × 1180, the Index starts as a search row and the collection button sits directly above the document. The same disclosure state survives rotation. Landscape shows Index beside the document, and returning to portrait restores the saved open or closed state.

The opening figure in “3 symbols” fills the left column of an image-and-caption pair. A CSS container query now measures the document pane. At 36rem or wider it uses the authored image size and caption position. Below 36rem it stacks the pair, using the same pane width threshold as wrapped figures. Both image decisions use the mounted document markup. [Reader stylesheet](../../docs-viewer/static/css/docs-viewer.css)

The compact layout reuses the existing Index state and toolbar. The stylesheet scopes figure measurement to documents with authored figure layouts. Focused JavaScript lint, projection and site validation passed, and the local preview served the updated files.

- [x] Desktop Safari at 820 × 1180 shows “3 symbols” with the Index collapsed, pinned links directly below it, the collection button above the document, and the half-width image beside its caption. The user accepted this portrait arrangement.
- [x] The user reported that the deployed layout is fine on the physical iPad Air.
- [ ] Rotate the iPad with Index open and then closed to check that the portrait state is restored.
- [ ] Compare iPhone portrait and iPad landscape. Check that the caption stacks below the image on the narrow phone pane and that authored image proportions are visible in the wider pane.

## Index Disclosure In The Single-Column Reader

In Safari’s 402 × 874 phone preset, the expanded Library Index took up much of the first screen and separated the collection button from its document. The phone layout starts with the search row visible and places the collection button directly above the document in both Index states.

### How CSS and JavaScript work together

**CSS decides where the Index can collapse.** The compact layout applies up to 820px wide, or up to 960px wide when the viewport height is below 35rem. In those viewports CSS shows the chevron and reads its `aria-expanded` attribute. When the value is `false`, CSS reduces the list area to zero height and hides it. The search row stays visible, and the list keeps its own scroll box. Outside the compact layout, CSS hides the chevron and displays the list at full height. Resizing and rotation preserve the open or closed state for the next time the compact layout is shown. [Reader stylesheet](../../docs-viewer/static/css/docs-viewer.css)

**JavaScript decides when to change the state.** A normal page starts collapsed. Tapping the chevron flips `aria-expanded`, and Search, Recent or a URL with a search query opens the list. Selecting a document or collection closes the list after the destination opens. Browser Back restores the previous disclosure state with the document. The public Index is flat today. If Book branches are added, their own expand buttons can reveal children without closing the phone panel. [Index renderer](../../docs-viewer/runtime/js/shared/docs-viewer-index-panel-renderer.js) · [Navigation workflow](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js)

**The collection toolbar moves as one piece.** JavaScript uses the same viewport condition to put the existing toolbar inside the document pane when the collection button is available. Its position follows the document while the Index expands and collapses. Outside the compact layout the toolbar lives in the header. Both positions use the same control and collection action. The change uses the mounted reader and its existing data. [Reader runtime](../../docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js)

### Safari acceptance

Focused JavaScript lint, the public projection check and site validation passed. The local preview served the updated shell, stylesheet and all five changed JavaScript modules. The implementation reuses the mounted Index and the existing navigation snapshots to carry disclosure state through Back.

- [ ] At 402 × 874, open “Biological and physical memories” directly. Check that the search row and chevron are visible and that the collection button stays immediately above the document when Index opens or closes.
- [ ] Open a document from the Index, Search and Recent. Check that the list closes after navigation, reopens with its previous selection and position, and returns when using Back from a result. Check that a shared search link opens expanded and that keyboard focus follows the selected document.
- [ ] Compare the Index with wider iPad and desktop layouts.

### Phone landscape

The original landscape screenshot of “3 symbols” showed the wide layout reserving room on both sides of the document. At 874 × 402, that left about 154px for the document. The phone layout now puts the collapsible Index above the document and lets the document use the available width up to its desktop reading measure. Rotation keeps the same Index and disclosure state.

The landscape change extends the existing viewport condition and reuses the same Index and toolbar. Its document-width and scrolling rules apply to the ordinary reader. Focused JavaScript lint, the projection check and site validation passed, and the local preview served the updated stylesheet and reader runtime.

- [x] Phone rotation accepted in Safari.
- [ ] Choose a document in phone landscape at 874 × 402 and check that the Index collapses after navigation.
- [x] Media View Work detail accepted in both phone orientations in desktop Safari. The landscape screenshot of “sea - detail 4” shows the image, details and navigation controls clearly.

### Physical iPhone landscape findings

In the deployed test, the iPhone 15 Pro in landscape placed the “3 symbols” Media View gallery title and related document link below the thumbnails. Desktop Safari’s 874 × 402 preset showed them alongside. The deployed shell uses Safari’s default safe-area insets. The phone screenshot is consistent with an inset viewport below the former 760px Gallery breakpoint. The exact CSS viewport width awaits measurement. [WebKit safe areas](https://webkit.org/blog/7929/designing-websites-for-iphone-x/) · [Safari Responsive Design Mode](https://developer.apple.com/documentation/safari-developer-tools/responsive-design-mode)

The public Gallery layout uses a CSS container query. At an inner panel width of 36rem, a narrower metadata column fits beside at least five standard thumbnails at the default font size. The existing thumbnail grid wraps in the available width and keeps its page membership. Gallery presentations include Discovery grids. [Gallery presentations](../reference/Catalogue_Media_View.md#gallery-presentations)

The projection check and site validation passed. Local preview served the updated shell and stylesheet. The physical iPhone screenshot confirms six thumbnails per row with the Gallery title and related document link beside them.

The first Work detail test on the physical iPhone stacked the metadata below the image in landscape because Work detail still used the 760px viewport breakpoint. The same Work looked right in portrait. Work detail now uses the same 36rem panel-width query as Gallery, with metadata alongside the image when the panel has room. The stylesheet supplies the shared columns for Work, Gallery and Discovery. The Media View runtime owns data and navigation. [Reader stylesheet](../../docs-viewer/static/css/docs-viewer.css)

On the phone, document body text grew when rotated to landscape, while headings and captions stayed the same size. The `cat.` line in Work detail also grew. This pattern points to Safari’s automatic text sizing. Local preview sets `text-size-adjust` and `-webkit-text-size-adjust` to 100% on public document paragraphs outside figure captions and on the catalogue-number line in short landscape viewports. [Safari text sizing](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/AdjustingtheTextSize/AdjustingtheTextSize.html)

The Work and text patch passed the projection check and site validation. Local preview served the updated stylesheet.

- [x] Gallery layout accepted on the physical iPhone in landscape.
- [x] Work detail layout accepted on the physical iPhone in portrait.
- [ ] Check Work metadata placement and the `cat.` line at normal page zoom on the phone in landscape. Rotate to portrait and back, compare document paragraph sizing, and check reader-controlled zoom. Open a Work and return to the Gallery to verify the return path.

## Catalogue And Media View

- Catalogue currently falls back to List when the pane cannot fit the rolling Gallery. It keeps the chosen mode and columns for when there is room again. Review the width at which List, search and dice serve the reader better, and compare that fallback with showing fewer Gallery columns. Base the decision on the available pane width.
- Media View can wrap thumbnails into fewer columns on narrow screens. Check whether vertical scrolling leaves the controls easy to reach, and whether opening a Work and returning restores a useful position.
- Review List and Gallery controls, search, Work and Media View navigation, and touch interaction as part of the wider site review. [Catalogue browsing](../reference/Reader_Discovery_And_Return.md#catalogue-collection-browsing) · [Gallery presentations](../reference/Catalogue_Media_View.md#gallery-presentations)

## First Readiness Review

- [ ] Walk representative public pages on a phone and tablet. Include orientation changes, long documents, the Index, search, image detail, and browser Back. Record where layout or controls make a task difficult.
- [ ] Check deep Index branches, zoom, theme changes, diagrams and links. Check touch targets and safe areas where controls sit near an edge. Keep these public-reader checks separate from desktop Manage and Review.
- [ ] Record the viewport widths used for manual acceptance and choose the next layout change from the observed reader journeys.

Review transfer size and loading separately, using the same reader journeys where that helps. [Site Optimisation](Site_Optimisation.md)
