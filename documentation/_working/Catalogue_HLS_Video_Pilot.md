---
draft: false
doc_id: d-20261122-003943-ac9eb5
title: Catalogue HLS Video Pilot
added_date: "2026-11-22 00:39:43"
last_updated: "2026-11-22"
summary: Pilot adaptive video playback for one Catalogue Work using FFmpeg, Cloudflare R2 and the browser's video controls.
ui_status: proposed
parent_id: d-20261118-235100-64ad2e
---
# Catalogue HLS Video Pilot

Test whether visitors can watch a film inline in a Catalogue document with good picture quality and reliable playback across devices. Start with a manual pilot for one film on the existing R2 media host, `media.dotlineform.com`. Use the pilot measurements and the video inventory to choose a production workflow. [Existing media configuration](../../site-tools/config/site-tools.json) · [Catalogue workflow](../guide/Maintain_The_Catalogue.md)

## Inline Playback And Media View

Create a temporary Catalogue document preview page reachable from the pilot browsers and iPhone. Give the player the R2 master playlist URL and the separate Catalogue poster image URL. The reader presses Play in the Work media area and watches the film inline using the browser's standard controls.

A possible follow-through is a dedicated **Open in Media View** button beside the playback controls. It would open a larger presentation in the main pane, following the navigation used for still Work images. Both views would use the same HLS playlist. Carry the current playback position when opening Media View and returning via **Back to document**, with one active player at a time. [Catalogue Media View](../reference/Catalogue_Media_View.md) · [Return behaviour](../reference/Reader_Discovery_And_Return.md#exact-document-navigation-and-return)

## How Playback Works

- FFmpeg takes one master and produces several quality versions split into short, aligned segments. The Work page needs one URL, the master playlist (`.m3u8`). It lists a playlist for each quality, and each of those playlists lists its segments. R2 serves the playlists and segments as files. [Apple HLS authoring guidance](https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html)
- **Auto** is the player's choice of quality as playback progresses. The player can start at a lower quality, request higher-quality segments when the connection can sustain them, and drop back down when the buffer runs low. Use the browser's video controls and automatic quality for the pilot.
- Use an HTML video element with `playsinline` for the inline player. Safari on Mac and iPhone can handle HLS natively. Desktop Safari can also use `hls.js`. Start with the library's documented capability check, using `hls.js` where supported and native HLS as the fallback. Exercise both paths during the pilot. [hls.js setup and compatibility](https://github.com/video-dev/hls.js#embedding-hlsjs) · [WebKit inline video behaviour](https://webkit.org/blog/6784/)
- Allow the page origin to fetch the HLS playlists and segments from R2. Check cross-origin `GET` responses from the actual pilot origin, and include `https://www.dotlineform.com` when serving the public Work page. Use the same package for both playback paths. [hls.js CORS requirements](https://github.com/video-dev/hls.js#cors) · [R2 CORS configuration](https://developers.cloudflare.com/r2/buckets/cors/)

## Video Formats In Plain English

- **Codecs** determine how the picture and sound are compressed. H.264 is a video codec and AAC is an audio codec. A 360p copy and a 720p copy can both use H.264. Creating the smaller picture requires a new video encode.
- **Containers** are the file wrappers that hold the picture, soundtrack and any other tracks. `.mov` is QuickTime, `.mp4` and `.m4v` are common extensions for MP4 video, and `.mkv` is Matroska. Different wrappers can hold the same codecs. For example, `balance machine 1.m4v` holds H.264 video and AAC audio. The separate `.aif` is an AIFF audio file.
- **HLS** is a way to deliver video in short pieces. For the pilot, FFmpeg will package the H.264 and AAC tracks as **fragmented MP4**. The `.m4s` files carry the pieces of the film, and the `.m3u8` files are text playlists that tell the player which pieces it can fetch. The player starts with one master playlist URL. DASH is another way to deliver adaptive video and uses an `.mpd` file for its manifest. [Apple HLS authoring guidance](https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html) · [HLS and DASH examples](https://developers.cloudflare.com/stream/viewing-videos/using-own-player/)

## Manual Pilot And Acceptance

- [x] Select **balance machine 1** as the pilot film. The source is `projects/balance machine/balance machine 1.m4v` beneath `$DOTLINEFORM_PROJECTS_BASE_DIR`. The 2011 HandBrake export runs 4:09 at 1280 × 720 with H.264 video and an embedded stereo AAC soundtrack. FFmpeg decoded both tracks through to the end without errors.
- [ ] Write a small local CLI that takes a source video and an output directory and runs FFmpeg to create an HLS package. Run it for the pilot film with two or three quality levels, using H.264 video up to 720p and AAC audio from the embedded soundtrack. Record the chosen resolutions and bitrates, encoding time and total size of the playlists and segments.
- [ ] Confirm the pilot R2 destination and the preview page's origin. Upload the package to R2 manually, record the upload time and point the preview page at the master playlist. Catalogue Work `04813` describes the same-title print.
- [ ] Open the same preview in Mac Safari, iPhone Safari, desktop Chrome and Firefox. Record which playback path each uses and explicitly exercise native HLS on the iPhone if the default selects `hls.js`. Check startup, seeking, audio sync after seeks, inline playback on the iPhone, fullscreen and how well the film retains its detail during motion.
- [ ] Throttle a desktop connection during playback. Inspect segment requests to confirm a quality change and assess whether playback recovers as bandwidth falls and rises. Check that the soundtrack stays in sync through quality changes, and record any stalls or visible quality issues alongside the network conditions.

## Video Inventory And Hosting Estimates

The separate [Video Inventory And Source Organisation](Video_Inventory_And_Source_Organisation.md) delivery owns the local source review and Vimeo and YouTube reconciliation. Use its confirmed source sizes, distinct cut runtimes and unresolved source count for the hosting estimates. The manual pilot can proceed with the verified *balance machine 1* file.

- [ ] Total the local source sizes and estimate R2 storage for the HLS delivery packages. A combined video and audio bitrate of 4 Mbit/s across all stored renditions would use about **30 MB per film minute**, or **125 MB for the 4:09 pilot film** and **3 GB for 100 minutes**, before packaging overhead. Use the measured pilot package size for similar sources and estimate higher-resolution packages separately. Include existing R2 usage when comparing with the Standard allowance of 10 GB-month and the rate of **US$0.015 per additional GB-month**. R2 counts read and write requests separately and charges no bandwidth fee. [R2 pricing](https://developers.cloudflare.com/r2/pricing/)
- [ ] Use total film duration and expected viewing to estimate Cloudflare Stream costs. Stream starts at **US$5/month** for up to 1,000 stored minutes, plus **US$1 per 1,000 minutes delivered**. If five visitors each watch ten minutes in a month, 50 minutes of delivery costs about **US$0.05**. That is about **US$5.05 for the month** if the library fits in the first storage block. Stream also counts segments fetched for buffering. [Stream pricing](https://developers.cloudflare.com/stream/pricing/)

## Decision After The Manual Pilot

Complete the manual pilot and review playback, preparation effort, the inventory and the hosting estimates before choosing a production workflow. Studio integration follows that decision.

- **R2.** If playback and recurring preparation are acceptable, productionise the FFmpeg CLI and integrate video preparation, **Refresh Catalogue**, **Regenerate** and **Publish** for selected Works.
- **Cloudflare Stream.** If playback is unreliable or the R2 workflow takes too much effort, use Stream for encoding, storage and delivery with its own embedded player. The Catalogue Work would carry a Stream reference. [Cloudflare Stream overview](https://developers.cloudflare.com/stream/) · [Stream Player](https://developers.cloudflare.com/stream/viewing-videos/using-the-stream-player/)
- **Player controls.** Use the pilot to assess the browser's standard controls. If a consistent quality menu or closer Media View integration is needed, compare the engineering effort of integrating an existing public player library with building custom controls on one. Include keyboard access, fullscreen and mobile behaviour in the comparison.

## Film And Still Work Records

Use `works.json` for both films and still Works. A Series can contain the film and its related stills, each with its own Work ID and metadata. Record **Duration** on the film Work and leave it blank for still Works. [Catalogue identities and relationships](../reference/Catalogue_Source_Model.md#relationships-and-identity) · [Work fields](../reference/Catalogue_Source_Model.md#metadata-and-ordering)

Add an optional video source reference to the Work record. A film Work's selected Catalogue image supplies its poster and Gallery thumbnail. Publish the Catalogue image separately from the HLS package so the poster can be changed through Studio's normal image workflow without re-encoding the video. [Studio image workflow](../reference/Catalogue_Save_And_Refresh.md#work-media-authoring)

If the poster image is also a Work in its own right, such as a print, it can have its own record in the same Series. An existing film Work represented by a still and a Vimeo link keeps its Work ID, Catalogue document and Gallery memberships when hosted playback is added.

## Proposed Studio Integration For R2

If the pilot supports R2, Studio's browser editor would capture the selected master for the Work. The local Python service would run FFmpeg for a new or replacement video and stage the complete package. Prefer preparing it on **Save**, as Studio does for image renditions. Use the measured encode time to decide whether to defer preparation to **Refresh Catalogue**. Metadata edits reuse the prepared video. [Studio media pipeline](../reference/Catalogue_Media_Pipeline_Config.md#save-and-refresh)

**Refresh Catalogue** would hand the finished package into Working. **Regenerate** would add an optional playlist reference to the generated Catalogue document data and queue the selected package. Keep the existing Catalogue source tokens. The identity-only Catalogue Entry token identifies the Work, and the reader uses the playlist reference from that Work's data for inline playback. For this delivery, use the normal queued Regenerate on the Work IDs receiving hosted video. [Catalogue Entry token](../reference/Document_And_Catalogue_References.md#build-and-runtime-resolution) · [Regenerate scope](../reference/Catalogue_Save_And_Refresh.md#regenerate-timing)

**Publish** would transfer the selected HLS package to R2 and publish the updated Work document data. The shared player code follows the usual public site projection and deployment workflow. [Catalogue publication](../guide/Maintain_The_Catalogue.md) · [Public runtime projection](../development/Verification.md#docs-viewer-site-code-projection)
