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

Create a temporary Catalogue-style preview page under `site/pilot/balance-machine-1/` using the standalone pilot workflow. Give the player the R2 master playlist URL and the separate poster image URL. The reader presses Play in the Work media area and watches the film inline using the browser's standard controls. [Standalone Site Pilots](Standalone_Site_Pilots.md)

The film's own Catalogue document would use the inline player after Studio integration. An **Add Media View link** in another document shows the poster as a responsive still when the author selects the image presentation. With **This Work** as the target, clicking the still opens that Work in Media View. The existing Studio Work Editor image preview shows the selected frame. A separate **Play** action could be added in Studio later to preview the selected source video or a prepared local package. [Media View link authoring](../reference/Catalogue_Media_View.md#authoring) · [Studio image preview](../reference/Catalogue_Work_Editor.md#image-preview-and-dimensions)

A possible follow-through is a dedicated **Open in Media View** button beside the playback controls. It would open a larger presentation in the main pane, following the navigation used for still Work images. Both views would use the same HLS playlist. Carry the current playback position when opening Media View and returning via **Back to document**, with one active player at a time. [Catalogue Media View](../reference/Catalogue_Media_View.md) · [Return behaviour](../reference/Reader_Discovery_And_Return.md#exact-document-navigation-and-return)

## How Playback Works

- FFmpeg takes one master and produces several quality versions split into short, aligned segments. The player starts with one URL for the stream, the master playlist (`.m3u8`). It lists a playlist for each quality, and each of those playlists lists its segments. R2 serves the playlists and segments as files. [Apple HLS authoring guidance](https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html)
- **Auto** is the player's choice of quality as playback progresses. The player can start at a lower quality, request higher-quality segments when the connection can sustain them, and drop back down when the buffer runs low. Use the browser's video controls and automatic quality for the pilot.
- Use an HTML video element with `playsinline` for the inline player. Safari on Mac and iPhone can handle HLS natively. Desktop Safari can also use `hls.js`. Start with the library's documented capability check, using `hls.js` where supported and native HLS as the fallback. Exercise both paths during the pilot. [hls.js setup and compatibility](https://github.com/video-dev/hls.js#embedding-hlsjs) · [WebKit inline video behaviour](https://webkit.org/blog/6784/)
- Allow the page origin to fetch the HLS playlists and segments from R2. Check cross-origin `GET` responses from the actual pilot origin, and include `https://www.dotlineform.com` when serving the public Work page. Use the same package for both playback paths. [hls.js CORS requirements](https://github.com/video-dev/hls.js#cors) · [R2 CORS configuration](https://developers.cloudflare.com/r2/buckets/cors/)

### Native HLS Player Example

The proposed `video_source` field in `works.json` identifies the local file Studio encodes. Once the HLS package is ready, Regenerate carries its master playlist reference into the generated Catalogue document. The renderer checks for that prepared reference. If it is present, the film's Catalogue entry uses a `<video>` element with the playlist as its source and an existing image rendition as its poster. Otherwise, the entry shows the normal Work image. The example uses short URLs for the two assets. [Catalogue entry renderer](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-rendering.js)

```html
<video controls playsinline poster="poster.webp">
  <source src="master.m3u8" type="application/vnd.apple.mpegurl">
</video>
```

With native HLS support, the browser reads the playlist directly. The `controls` attribute provides the browser's built-in play, pause, seek and fullscreen controls, and `playsinline` lets playback stay in the document on an iPhone. When `hls.js` handles the stream, it attaches to the same video element and uses the same browser controls. [HTML video element](https://html.spec.whatwg.org/multipage/media.html#the-video-element) · [hls.js setup](https://github.com/video-dev/hls.js#embedding-hlsjs)

## Video Formats In Plain English

- **Codecs** determine how the picture and sound are compressed. H.264 is a video codec and AAC is an audio codec. A 360p copy and a 720p copy can both use H.264. Creating the smaller picture requires a new video encode.
- **Containers** are the file wrappers that hold the picture, soundtrack and any other tracks. `.mov` is QuickTime, `.mp4` and `.m4v` are common extensions for MP4 video, and `.mkv` is Matroska. Different wrappers can hold the same codecs. For example, `balance machine 1.m4v` holds H.264 video and AAC audio. The separate `.aif` is an AIFF audio file.
- **HLS** is a way to deliver video in short pieces. For the pilot, FFmpeg will package the H.264 and AAC tracks as **fragmented MP4**. The `.m4s` files carry the pieces of the film, and the `.m3u8` files are text playlists that tell the player which pieces it can fetch. The player starts with one master playlist URL. DASH is another way to deliver adaptive video and uses an `.mpd` file for its manifest. [Apple HLS authoring guidance](https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html) · [HLS and DASH examples](https://developers.cloudflare.com/stream/viewing-videos/using-own-player/)

## Manual Pilot And Acceptance

- [x] Select **balance machine 1** as the pilot film. The source is `projects/balance machine/balance machine 1.m4v` beneath `$DOTLINEFORM_PROJECTS_BASE_DIR`. The 2011 HandBrake export runs 4:09 at 1280 × 720 with H.264 video and an embedded stereo AAC soundtrack. FFmpeg decoded both tracks through to the end without errors.
- [ ] Select a frame from the film and save it at the video's native dimensions as a high-quality JPG or PNG in the source project. Use that still as the preview page's poster and reserve the 16:9 player area before playback.
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

Keep Studio's **Choose image** action and the existing `project_filename` and folder fields for the poster. Add **Choose video** to set the proposed optional `video_source` field to the film's file path relative to the Work's project folder. The selected Catalogue image supplies the poster and Gallery thumbnail. Publish those through the normal image workflow, separately from the HLS package, so the poster can be changed without re-encoding the video. [Studio image workflow](../reference/Catalogue_Save_And_Refresh.md#work-media-authoring)

Studio's primary WebP conversion caps the rendition width at the source image's width. A 1280 × 720 frame produces renditions 800, 1200 and 1280 px wide for the configured 800, 1200 and 1600 px targets. The largest file retains the `1600` target in its filename, and the reader uses its actual 1280 px width in `srcset`. The native video player takes one of the prepared stills as its poster. [Image conversion](../../studio/services/catalogue/catalogue_build_media.py) · [Catalogue rendition widths](../../docs-viewer/services/docs_catalogue_projection.py)

If the poster image is also a Work in its own right, such as a print, it can have its own record in the same Series. An existing film Work represented by a still and a Vimeo link keeps its Work ID, Catalogue document and Gallery memberships when hosted playback is added.

## Video Files And Work Metadata

This table covers films intended for inline playback on dotlineform using HLS. Vimeo and YouTube links and cut matching are part of the inventory delivery. [Video inventory and reconciliation](Video_Inventory_And_Source_Organisation.md#reconcile-local-files-and-published-cuts)

The Projects locations below are examples. The pilot CLI writes the HLS package to a chosen output folder for manual upload. The production staging location, R2 key layout and playlist reference format are decisions for Studio integration after the pilot. [Work media roots](../reference/Catalogue_Media_Pipeline_Config.md#work-media-sources) · [Current Catalogue storage](../reference/Catalogue_Save_And_Refresh.md#storage-and-selection)

| File or asset | Role | Where it can be saved | How the Work records it |
| --- | --- | --- | --- |
| Project note `_<project folder name>.md` | Describes the source files and records the selected cut, provenance and any preparation still needed. | In the project root. | The note records the Work ID once the cut is registered. [Project-note table](Video_Inventory_And_Source_Organisation.md#table-in-the-project-note) |
| Source footage, edits and alternate exports | Supplies material and candidate copies of a cut. | Within the project, for example `source video/` for footage and `video/` for finished exports. | Record candidate paths in the project note. The Work identifies the selected export. |
| Selected video master or export (`.mov`, `.m4v`, `.mp4`) | Input to FFmpeg for the cut associated with this Work. Embedded audio comes from the same file. The pilot uses `balance machine 1.m4v`. | In the project root or a subfolder such as `video/`. | **Choose video** sets the proposed `video_source` field in `works.json` to the file path relative to the Work's project folder. Resolve that folder using existing `project_folder` and the configured media source, selected by `media_source_id` when supplied. |
| Separate soundtrack (`.aif`, `.wav` or similar) | Holds a separate soundtrack or mix if the project has one. The pilot uses the audio in the selected video. | In the project root or a subfolder such as `soundtrack/`. | Record its path and relationship to the cut in the project note. An optional `soundtrack_source` field would be useful if Studio later needs to combine a separately selected soundtrack with the video. |
| Original poster image (`.jpg`, `.png` or other supported image) | Supplies the still displayed before playback and the source for the Gallery thumbnail. | The Work's project folder or image subfolder. | **Choose image** uses the existing image source fields `project_folder`, optional `project_subfolder` and `project_filename`, with `media_source_id` when needed. The measured `width_px` and `height_px` describe this image. |
| Prepared poster renditions (`.webp`) | Supply responsive stills for document links and a single poster rendition for the video player. | Published separately from HLS, through the existing image staging and `assets/works/primary/` in Working and Preview, then R2 under `works/img/`. | The image pipeline derives the renditions from the existing Work ID and selected image. `media_version` tracks the prepared image bytes. |
| Gallery thumbnail (`.webp`) | Small image for browsing and selection in the Catalogue. | `assets/works/thumbs/` in Working and Preview, then the public site under `site/assets/data/catalogue/works/thumbs/`. | The existing image pipeline generates the thumbnail from the Work's selected image and names it for the Work ID. |
| HLS master playlist (`.m3u8`) | Required for each hosted HLS video. Lists the playlists for the available qualities. | In the prepared HLS package, then at its public R2 location. | The generated Catalogue data for the hosted video must carry a reference to this file, either a URL or a path resolved against the media host. |
| HLS quality playlists (`.m3u8`) | Each lists the files needed to play one quality version. | In the same package, with locations relative to the master playlist. | The master playlist carries these references. |
| HLS initialization and media segments (`.mp4`, `.m4s`) | The initialization file describes how to read the track. The media segments carry short pieces of the picture and sound. | In the same package, with locations relative to the quality playlists. | The quality playlists carry these references. Publish transfers the files as part of the selected package for the Work. |
| Generated Catalogue document (`<work-id>.json`) | Supplies the Work's poster and playback data to the reader. | Generated Working by-ID data, then Preview and the public `site/assets/data/docs/catalogue/by-id/` output. | The existing Work ID identifies the document. Regenerate carries the prepared master playlist reference alongside the image data in `catalogue.work`. [Generated Catalogue data](../reference/Generated_Data_Contracts.md#catalogue-reference-and-presentation) |

Use the existing `medium` and `duration` fields to describe the film. Keep the selected video's pixel dimensions and file provenance in the project note. If the player needs video dimensions before it loads the playlist, carry the measured dimensions in the generated playback data. The pilot preview uses the master playlist URL and the poster URL directly.

## Balance Machine Pilot And Production Paths

Paths starting with `projects/` or `dotlineform-site/catalogue/media-staging/` are relative to `$DOTLINEFORM_PROJECTS_BASE_DIR`. `working/` and `preview/` are relative to `$DOTLINEFORM_DOCS_BASE_DIR`. `var/` and `site/` are relative to the repository.

### Manual Pilot

| File or stage | Path | Status |
| --- | --- | --- |
| Project note | `projects/balance machine/_balance machine.md` | Existing inventory and reconciliation notes. |
| Selected video | `projects/balance machine/balance machine 1.m4v` | Verified source. FFmpeg will use its embedded soundtrack. |
| Separate soundtrack | `projects/balance machine/balance machine 1.aif` | Existing candidate. Its match to the embedded soundtrack is unconfirmed. |
| Poster source, JPEG example | `projects/balance machine/balance machine 1 poster.jpg` | Proposed file for the chosen frame at 1280 × 720. |
| Pilot poster | `site/pilot/balance-machine-1/poster.jpg` | Preview copy of the chosen frame for local and deployed checks. |
| Pilot preview page | `site/pilot/balance-machine-1/index.html` | Proposed temporary page served by `bin/site-preview` and GitHub Pages at the direct `/pilot/balance-machine-1/` route. |
| Local HLS master playlist | `var/catalogue-hls-pilot/balance-machine-1/hls/master.m3u8` | Proposed CLI output. The playlists and segments go together in `hls/` for manual upload. |
| Pilot master playlist on R2 | `https://media.dotlineform.com/works/video/pilot/balance-machine-1/master.m3u8` | Proposed public address for the preview player. The named folder gives the package an address before the film has a Work ID. |

### Production With Studio And R2

These are target paths if R2 is chosen after the manual pilot. `<film-work-id>` stands for the film's eventual Catalogue ID. Work `04813` describes the print. The source subfolders shown here assume the inventory review adopts that layout.

| File or stage | Target path |
| --- | --- |
| Project note | `projects/balance machine/_balance machine.md` |
| Selected video | `projects/balance machine/video/balance machine 1.m4v` |
| Separate soundtrack, if organised under `soundtrack/` | `projects/balance machine/soundtrack/balance machine 1.aif` |
| Selected poster source, JPEG example | `projects/balance machine/balance machine 1 poster.jpg` |
| HLS master playlist in Studio staging | `dotlineform-site/catalogue/media-staging/works/video/<film-work-id>/master.m3u8` |
| HLS master playlist in Working | `working/assets/works/media/video/<film-work-id>/master.m3u8` |
| HLS master playlist in Preview | `preview/assets/works/media/video/<film-work-id>/master.m3u8` |
| Published HLS master playlist on R2 | `https://media.dotlineform.com/works/video/<film-work-id>/master.m3u8` |
| Published poster rendition on R2, for example at 800 px | `https://media.dotlineform.com/works/img/<film-work-id>-primary-800.webp` |
| Published Gallery thumbnail | `site/assets/data/catalogue/works/thumbs/<film-work-id>-thumb-96.webp` |
| Published Catalogue document data | `site/assets/data/docs/catalogue/by-id/<film-work-id>.json` |

Both packages keep the same relative structure through upload. For example, `master.m3u8` could point to `720p/index.m3u8`, which references `init.mp4` and `segment-0000.m4s` beside it in `720p/`. FFmpeg's output determines the exact quality playlist and segment filenames.

## Proposed Studio Integration For R2

If the pilot supports R2, Studio's browser editor would capture the selected master for the Work. The local Python service would run FFmpeg for a new or replacement video and stage the complete package. Prefer preparing it on **Save**, as Studio does for image renditions. Use the measured encode time to decide whether to defer preparation to **Refresh Catalogue**. Metadata edits reuse the prepared video. [Studio media pipeline](../reference/Catalogue_Media_Pipeline_Config.md#save-and-refresh)

**Refresh Catalogue** would hand the finished package into Working. For each Work receiving hosted video, **Regenerate** would carry the required master playlist reference into the generated Catalogue document data and queue the package. Keep the existing Catalogue source tokens. The identity-only Catalogue Entry token identifies the Work, and the reader uses the playlist reference from that Work's data for inline playback. Use the normal queued Regenerate for those Work IDs. [Catalogue Entry token](../reference/Document_And_Catalogue_References.md#build-and-runtime-resolution) · [Regenerate scope](../reference/Catalogue_Save_And_Refresh.md#regenerate-timing)

**Publish** would transfer the selected HLS package to R2 and publish the updated Work document data. The shared player code follows the usual public site projection and deployment workflow. [Catalogue publication](../guide/Maintain_The_Catalogue.md) · [Public runtime projection](../development/Verification.md#docs-viewer-site-code-projection)
