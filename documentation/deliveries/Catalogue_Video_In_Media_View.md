---
draft: false
doc_id: d-20261126-160014-0d93bf
title: Catalogue Video In Media View
added_date: "2026-11-26 16:00:14"
last_updated: "2026-11-26"
summary: Delivered playback of the selected Catalogue film in Media View using the Work's existing poster and HLS package.
ui_status: done
parent_id: d-20260419-000000-d2e47b
---
# Catalogue Video In Media View

Catalogue films play in Media View from a Work link, Gallery or Catalogue Discovery using the same poster, HLS package and browser controls as their Catalogue pages. In the *videos* document (`d-20261126-155004-f9856c`), selecting the existing poster for Work `05248` opens the film player in Media View. The player opens on the poster and the reader presses Play. [Media View](../reference/Catalogue_Media_View.md) · [Catalogue R2 Video Delivery](Catalogue_R2_Video_Delivery.md)

## Entry Points

Use the player’s fullscreen control for larger playback on the film’s own Catalogue page. From that page, a linked Gallery can lead to the film in Media View when the film belongs to that Gallery. Revisit a dedicated Catalogue Entry opener if readers need direct access from the film’s page to Media View’s browsing controls.

## Player Sizing

The saved poster dimensions set the player’s maximum size and aspect ratio. A smaller player displays at that size when there is room. Larger players scale down proportionally to fit the media pane and available viewport height. The frame stays stable when HLS switches quality. Work `05248` has a 1280 × 720 poster matching its largest rendition. If future posters differ from their films and exact video sizing matters, carry the prepared video dimensions with the Work. [Current Media View image sizing](../../docs-viewer/static/css/docs-viewer.css)

**Current encoding cap.** Prepare video produces HLS renditions up to 640 × 360 and 1280 × 720. A 1080p source currently plays at up to 720p. The same responsive sizing rule applies if a 1080p rendition is added later. [Encoder settings](../../bin/prepare-hls-pilot) · [1080p inventory assessment](../_working/Video_Inventory_And_Source_Organisation.md#1080p-playback-assessment)

## Delivered Workflow

The selected Work supplies the poster and playlist. Manage reads the Working package, and site-preview and Public read R2. Media View mounts the shared player in its responsive figure and caption layout. The **cat.** link opens the Work’s Catalogue page, and **Open in new tab** opens its full-size image or poster. [Work presentation](../../docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js) · [Shared player](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-video.js)

Media View releases the player when the reader changes Works, returns to the grid or closes the view. Opening Media View over a playing Catalogue Entry pauses the inline film. The existing Previous, Next and Back controls keep their navigation and return focus. [Media View lifecycle](../../docs-viewer/runtime/js/shared/docs-viewer-media-detail.js)

## Acceptance And Release

The author accepted the delivery on 26 November 2026 with Safari-only testing through iPhone. The delivery is in commit `470a8be919`, and the deployed Media View module matched the committed public projection byte for byte. [Deployed Media View module](https://www.dotlineform.com/docs-viewer/runtime/js/shared/docs-viewer-media-detail.js)

## Implementation Evidence

The existing selected Work read supplies the film reference and poster. Gallery and Discovery retain their thumbnail reads. The Work provider resolves the playlist using the configured video base, and presentation normalisation checks the browser URL at the same boundary that handles embedded Media View payloads. Media View reuses the shared player and releases it through the existing media cleanup on selection change and close.

The reader projection and site validation passed, as did lint for all six changed canonical JavaScript modules. A runtime data check used the existing payloads for `05248` and `04813` to confirm the film’s Working and R2 URLs, 1280 × 720 poster dimensions, full-size poster target and the print’s image presentation.

## Follow-on If Ordinary Documents Need Inline Players

Keep the poster link for indexes such as *videos*. An inline player is useful when watching a film is part of reading the surrounding text. Revisit the following decisions if that need arises.

- **Authoring and layout.** Offer **Inline video** as an explicit presentation for a selected film Work alongside the existing poster and link choices. Decide which placements the player supports and whether an inline player also needs a separate Media View opener. [Catalogue reference authoring](../reference/Document_And_Catalogue_References.md)
- **Loading and playback.** Show the poster first and initialise the player on reader interaction, especially on pages with several films. Decide whether starting a second film pauses the first and how the reader leaves the page with playback active.
- **Publication.** The Work owns its HLS package and the referring document supplies the Work ID and presentation choice. Decide how authoring indicates that a selected film has yet to be prepared or published, and what the reader sees when playback is unavailable.
- **Export and Review.** A poster linked to the Catalogue page is a candidate for static export and Review. Decide whether any consumer needs a playable package offline before extending media packaging. [Export](../reference/Export.md) · [Document packages](../reference/Document_Packages.md)
