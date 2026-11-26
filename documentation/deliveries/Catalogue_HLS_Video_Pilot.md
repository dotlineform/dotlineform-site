---
draft: false
doc_id: d-20261122-003943-ac9eb5
title: Catalogue HLS Video Pilot
added_date: "2026-11-22 00:39:43"
last_updated: "2026-11-26"
summary: Accepted the standalone balance machine 1 HLS pilot, selected R2 and retained the pilot assets for the first Catalogue film delivery.
ui_status: done
---
# Catalogue HLS Video Pilot

The standalone *balance machine 1* pilot was accepted on 26 November 2026. R2 is the selected host for Catalogue video, and this cut is the first film Work for the [Catalogue R2 Video Delivery](../_working/Catalogue_R2_Video_Delivery.md). Broader browser and bandwidth checks now follow live use. The standalone page, poster and R2 package remain available for comparison. [Live pilot](https://www.dotlineform.com/pilot/balance-machine-1/) · [Standalone pilot workflow](../_working/Standalone_Site_Pilots.md)

## Source And Player

The source is `projects/balance machine/balance machine 1.m4v` beneath `$DOTLINEFORM_PROJECTS_BASE_DIR`. The 2011 HandBrake export runs 4:09 at 1280 × 720 with H.264 video and an embedded stereo AAC soundtrack. FFmpeg decoded both tracks through to the end. The approved 1280 × 720 JPEG from 1:20.08 is saved as `balance machine 1 poster.jpg` alongside the film. The standalone page uses an identical poster and reserves a 16:9 player area before playback.

The thin right-edge line and diagonal corner marks are visible in the original M4V and both HLS renditions. The author recalls creating the film from a Flash animation and suspects a screen recording. The author accepted retaining the marks in the film.

The player uses the browser's standard controls and `playsinline`. It selects `hls.js` when supported, falls back to native HLS, and offers **Use native HLS** where available. Both modes use the same H.264/AAC fragmented MP4 package. The master playlist names the renditions, and each rendition has its own playlist, initialization file and segments. [Pilot player](../../site/pilot/balance-machine-1/index.html) · [hls.js 1.7.4](https://github.com/video-dev/hls.js/releases/tag/v1.7.4) · [Apple HLS authoring guidance](https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html)

## Local Preparation

Run [the pilot CLI](../../bin/prepare-hls-pilot) with the Projects root set in the shell. It reads one local video file with an embedded soundtrack and creates a new output directory. Use a new directory for another encode.

```bash
bin/prepare-hls-pilot \
  "$DOTLINEFORM_PROJECTS_BASE_DIR/projects/balance machine/balance machine 1.m4v" \
  var/catalogue-hls-pilot/balance-machine-1/hls
```

The encode took 1 minute 2 seconds and produced 92,386,736 bytes across 89 files. Both renditions use a 25 fps timeline, matching six-second keyframe intervals and stereo AAC at a 128 kbit/s target. Each rendition carries the soundtrack so FFmpeg's measured master-playlist bitrates include the full playback stream. The master also declares the output frame rate. Each media playlist has 42 segments covering 248.92 seconds, including a 2.92-second tail. Both renditions decoded to the end, and their segment boundaries matched.

| Rendition | H.264 video target | Measured average with audio | Peak segment with audio |
| --- | --- | --- | --- |
| 640 × 360 | 650 kbit/s | 717 kbit/s | 1,027 kbit/s |
| 1280 × 720 | 2,400 kbit/s | 2,253 kbit/s | 3,111 kbit/s |

## Upload And Playback Evidence

All 89 objects were uploaded to the pilot prefix on 26 November 2026, finishing around 12:13 GMT. The connection stopped after 64 objects and the remaining 25 completed in 13.4 seconds on resume. The master was uploaded last. For each pilot origin, the three gzip playlists, two initialization files and one segment per rendition had matching CORS origins and content types. The media byte-range requests returned HTTP 206. [Existing pilot CORS policy](../_working/Standalone_Site_Pilots.md#verify-deploy-and-retire) · [Apple HLS delivery requirements](https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html)

`bin/site-validate` passed. In local preview, the in-app browser played and resumed after a midpoint seek in both modes. Automatic playback moved from 360p to 720p on the unthrottled connection. Mac Safari started native playback and advanced to 15 seconds.

The live page and poster matched the deployed files. At the public URL, the in-app browser started `hls.js` playback at 360p, moved to 720p and resumed after a midpoint seek. Mac Safari 27.2 played the native stream, sought to 2:04, entered fullscreen and returned to inline at the same position. The author confirmed playback on iPhone Safari, a switch from 360p to 720p and fullscreen. [Public pilot](https://www.dotlineform.com/pilot/balance-machine-1/) · [Native HLS path](https://www.dotlineform.com/pilot/balance-machine-1/?playback=native) · [Deployment](https://github.com/dotlineform/dotlineform-site/actions/runs/45818377729)

Further observations in live use include explicit native HLS on iPhone, desktop Chrome and Firefox, audio sync and motion quality, and downshift and recovery under changing bandwidth. Record observations as devices and conditions are available. The pilot closeout rests on the checks recorded above.

## Video Inventory And Hosting Estimates

Use about 22 MB per film minute as an initial estimate for similar 720p sources encoded with these two renditions. The [Video Inventory And Source Organisation](../_working/Video_Inventory_And_Source_Organisation.md) delivery owns the local cuts and runtimes for planning a wider R2 rollout.

## Retained Assets

| Asset | Location |
| --- | --- |
| Standalone page and poster | `site/pilot/balance-machine-1/` |
| Local encode and poster copy | `var/catalogue-hls-pilot/balance-machine-1/` |
| R2 pilot package | `works/video/pilot/balance-machine-1/` on `media.dotlineform.com` |
| Source film, project note and approved poster | `projects/balance machine/` beneath `$DOTLINEFORM_PROJECTS_BASE_DIR` |
| Encode command | `bin/prepare-hls-pilot` |
