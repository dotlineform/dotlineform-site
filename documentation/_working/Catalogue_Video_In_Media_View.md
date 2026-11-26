---
draft: false
doc_id: d-20261126-160014-0d93bf
title: Catalogue Video In Media View
added_date: "2026-11-26 16:00:14"
last_updated: "2026-11-26"
summary: Play the selected Catalogue film in Media View using the Work's existing poster and HLS package.
ui_status: planned
parent_id: d-20261118-235100-64ad2e
---
# Catalogue Video In Media View

Open a Catalogue film from a Work link, Gallery or Catalogue Discovery and play it in Media View using the same poster, HLS package and browser controls as its Catalogue page. In the *videos* document (`d-20261126-155004-f9856c`), selecting the existing poster for Work `05248` should open the film player in Media View. The player opens on the poster and the reader presses Play. [Media View](../reference/Catalogue_Media_View.md) · [Catalogue R2 Video Delivery](../deliveries/Catalogue_R2_Video_Delivery.md)

## Entry Points

Use the player’s fullscreen control for larger playback on the film’s own Catalogue page. From that page, a linked Gallery can lead to the film in Media View when the film belongs to that Gallery. Revisit a dedicated Catalogue Entry opener if readers need direct access from the film’s page to Media View’s browsing controls.

## Player Sizing

Use the saved poster dimensions to set the player’s maximum size and aspect ratio. Show a smaller player at that size when there is room, and scale larger players down proportionally to fit the media pane and available viewport height. Keep the frame stable when HLS switches quality. Work `05248` has a 1280 × 720 poster matching its largest rendition. If future posters differ from their films and exact video sizing matters, carry the prepared video dimensions with the Work. [Current Media View image sizing](../../docs-viewer/static/css/docs-viewer.css)

**Current encoding cap.** Prepare video produces HLS renditions up to 640 × 360 and 1280 × 720. A 1080p source currently plays at up to 720p. The same responsive sizing rule applies if a 1080p rendition is added later. [Encoder settings](../../bin/prepare-hls-pilot) · [1080p inventory assessment](Video_Inventory_And_Source_Organisation.md#1080p-playback-assessment)

## Delivery Steps

1. Carry the optional playlist reference through the existing Work presentation and resolve it through the configured video base. Manage uses the Working package, and site-preview and Public use R2. The browser already loads the exact Work on selection. Use that record and its prepared poster. [Work presentation](../../docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js)
2. Mount the shared HLS player in the selected film's Media View pane. Use the existing responsive figure and caption layout. Gallery and Discovery show thumbnails, and an image Work shows its usual image. The **cat.** link opens the Work's Catalogue page. **Open in new tab** opens the full-size image, which is the poster for a film. [Shared player](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-video.js)
3. Release the player when the selected Work changes, the reader returns to the grid, or Media View closes. Pause a playing inline film when Media View opens over its document. Keep the existing Previous, Next and Back behaviour, including return focus. [Media View lifecycle](../../docs-viewer/runtime/js/shared/docs-viewer-media-detail.js)

## Completion

- [ ] The poster in *videos* opens film `05248` in Media View. The film plays and seeks using the browser's controls. Check that the player fits at wide and narrow widths and keeps its aspect ratio when playback starts.
- [ ] Move between a film and an image Work in a Gallery or Discovery selection. Check that playback stops on a change of Work, return to the grid and Back. Check the normal image presentation, the **cat.** link, full-size image in a new tab and return to the opener.
- [ ] Check Manage and site-preview. Verify native playback on desktop Safari and iPhone and the `hls.js` path on an available Chromium browser. Project and validate the shared reader code for the public release. [Verification](../development/Verification.md#docs-viewer-site-code-projection)

## Follow-on If Ordinary Documents Need Inline Players

Keep the poster link for indexes such as *videos*. An inline player is useful when watching a film is part of reading the surrounding text. Revisit the following decisions if that need arises.

- **Authoring and layout.** Offer **Inline video** as an explicit presentation for a selected film Work alongside the existing poster and link choices. Decide which placements the player supports and whether an inline player also needs a separate Media View opener. [Catalogue reference authoring](../reference/Document_And_Catalogue_References.md)
- **Loading and playback.** Show the poster first and initialise the player on reader interaction, especially on pages with several films. Decide whether starting a second film pauses the first and how the reader leaves the page with playback active.
- **Publication.** The Work owns its HLS package and the referring document supplies the Work ID and presentation choice. Decide how authoring indicates that a selected film has yet to be prepared or published, and what the reader sees when playback is unavailable.
- **Export and Review.** A poster linked to the Catalogue page is a candidate for static export and Review. Decide whether any consumer needs a playable package offline before extending media packaging. [Export](../reference/Export.md) · [Document packages](../reference/Document_Packages.md)
