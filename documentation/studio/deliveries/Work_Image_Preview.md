---
draft: false
doc_id: d-20261020-211017-0539ef
title: Work Image Preview
added_date: "2026-10-20 21:10:17"
last_updated: "2026-10-20"
parent_id: d-20260428-000000-f5ff18
---
# Work Image Preview

## Current And Next State

Complete; user accepted the implementation and requested closeout on 2026-10-20. Temporary previews and editable physical-dimension defaults precede Save; loaded Works show a calculated size without processing their source again. [Catalogue Work Editor](../Catalogue_Work_Editor.md#image-preview-and-dimensions) owns shipped behavior and evidence limits; [Planned Features](../Planned_Features.md) parents this delivery. Retained pending manual archive.

## Requirements And Deliverables

- Inspect only a confirmed single-file selection in New/existing Work editing. Picker highlights and metadata edits do not trigger processing. Folder-batch per-image defaults/previews are a separate delivery.
- Produce one still **WebP**, maximum **512 px longest edge**, **quality 75**, **compression level 1**, preserving aspect ratio without cropping/upscaling. Show original pixel dimensions with orientation consistent with the preview and Save. Large-source decoding remains necessary.
- Fill initially blank `width_cm` / `height_cm` using **300 dpi**, rounded to **one decimal place**: `round(original_pixels × 2.54 ÷ 300, 1)`, independently of embedded DPI or preview size. Example: 3000 × 2400 px → 25.4 × 20.3 cm.
- Display the calculated size directly beneath the source pixel dimensions in the image panel for every loaded Work with pixel dimensions, using the same axis order: `25.4 × 20.3 cm at 300 dpi`. Calculate it when an existing Work loads from its saved `width_px` / `height_px`, and recalculate from the selected source dimensions when a new preview completes. Existing Works need no new file selection or Save to show this caption.
- The caption is a runtime display calculation: loading a saved Work needs no additional image read, conversion or request, and does not autofill physical-dimension fields. Manual/saved physical dimensions do not change the caption. Add no derived centimetre field to `works.json` or generated metadata; the existing editable `width_cm` / `height_cm` fields retain their normal Save behavior.
- Preserve nonblank saved dimensions and manual draft edits, including clearing. Track automatic defaults in browser state; subsequent file selection replaces only those defaults. Both fields remain editable with existing Save validation.
- Keep metadata editable during inspection and disable Save until the current request finishes. Errors identify the selected-file failure and clear busy state; existing Save rules remain authoritative.
- Release preview bytes/object URL on replacement, discard/cancel, Work change, editor exit or completed Save; ignore late superseded results. Save prepares its normal persistent renditions from the original.

## Implementation And Ownership

The browser owns selection/request lifetime, preview Blob/object URL, dimension defaults/manual precedence, the runtime size caption and disposal. Share one conversion helper between defaults and caption. Render the caption from pixel dimensions already loaded with each Work, or from the selected source dimensions when preview preparation completes. Integrate the existing [file picker](../../../studio/app/frontend/js/catalogue-project-media-picker.js), form/draft state and [preview renderer](../../../studio/app/frontend/js/catalogue-work-sections.js); successful Save adopts its existing response.

Python returns original dimensions and preview bytes through one read-only `POST /studio/api/catalogue/project-media/preview` request. The [inspection service](../../../studio/services/catalogue/catalogue_work_image_preview.py) reuses configured-source resolution, path/symlink confinement, local-origin authority and the narrow [pixel reader](../../../studio/services/catalogue/catalogue_build_media.py). Configuration/source resolution happens once, without loading Works, building a rendition task or inspecting output files. The response is binary WebP with `X-Source-Width-Px` / `X-Source-Height-Px` headers and `Cache-Control: no-store`. Preview and Save share orientation-aware source measurement; EXIF orientations 5–8 transpose the axes.

Conversion reads the source path into a memory pipe and captures only the small encoded output, using bilinear scaling. Server buffers are released after responding and browser references/object URL on disposal. A converter already running may finish after browser cancellation; its abandoned response is discarded. Decoder memory may still reflect the large original. No application temporary/staging files, server cache or preparation token are created. [Save](../../../studio/services/catalogue/catalogue_output_media.py) retains canonical/media/version writes and queue effects.

## Process

Load existing Work → show saved source pixels and calculated centimetres. Select file → preview/source pixels, calculated centimetres and eligible defaults → adjust metadata/dimensions → Save once. Discard uses the existing draft owner.

## Delivery Steps

### WIP-0 — Readiness

- [x] Implementation approved on 2026-10-20. Confirmed the existing picker formats, shared orientation measurement, draft/discard/Save lifetimes and single-file boundary.

Gate: agree the narrow response and ownership split. Raise changes to Save, batch behavior or persistent preparation before implementation; keep readiness read-only.

### WIP-1 — Implementation And Focused Evidence

- [x] Implement inspection, preview/defaults, runtime centimetre caption, pending/error behavior and draft/Save disposal.
- [x] Select and run proportionate evidence with a recorded budget.

Budget: changed-path lint, syntax/import/whitespace checks and one selected real-image inspection; choose the image and estimate decode/memory cost before running. Manual review covers New/existing Works, overrides, replacement/discard, orientation, caption rounding/axis order and independence from authored dimensions, failure and one-Save behavior. New/changed tests or browser automation require separate approval under [Testing](../Testing.md); no corpus scan or benchmark is required.

Evidence: JavaScript lint passed for all 11 changed owners; Python lint and compilation passed for all four changed owners. One isolated Studio HTTP request read Work `00008`'s 1600 × 2263 JPEG (estimated seconds/tens of MB decoder memory) and returned HTTP 200, the exact source-dimension headers and a 362 × 512 WebP of 9,170 bytes with no-store caching. The isolated server was stopped. Whitespace review passed. Tests, browser interaction, large/rotated/other-format specimens and live Save remain unexercised; no canonical/generated/public data, Build, Search, Refresh or Publish changed.

### WIP-2 — Code Review

- [x] Complete distinct source/diff review and the mandatory Redundancy And Defensive Behavior Review in [Development Checklist](../Development_Checklist.md).

Gate: trace normal, replacement, manual/empty-dimension, failure and disposal paths through reused helpers. Challenge duplicate reads/decodes, hidden staging/loading, audits, caches, fallbacks and recovery. Retain selected-file authority, confinement, decoding/response and async lifetime checks; record findings and repeat affected evidence only.

Review: traced selection, saved loading, automatic/manual/cleared dimensions, replacement, discard, failed inspection and completed/incomplete Save. Removed a duplicate file-existence read and client checks that repeated producer-owned pixel/rendition validation. Corrected the unavailable-preview caption and reset default provenance when a canonical Save returns saved values but retains incomplete media intent. Retained request representation, configured-source/path/symlink confinement, real decoder success, HTTP error handling and header parsing at their boundaries; browser request identity prevents late results from changing another draft. Client disconnect handling discards completed conversion output without recovery. No Works scan, persistent preparation, cache, token, compatibility alias or Save-time preview reuse was added. Only affected static checks were repeated after review fixes.

### WIP-3 — Closeout

- [x] Transfer shipped behavior and evidence limits to Catalogue Work Editor; update durable guardrails and Planned Features.
- [x] Record user acceptance and closeout on 2026-10-20. Restart/reload instructions were supplied with implementation; individual manual scenarios were not itemised in the acceptance.

Closed using the recorded implementation evidence and user acceptance; no verification was repeated for this status-only closeout. Further scenario confirmation continues through ordinary use. Recommend manual archive of this delivery; its durable destination is Catalogue Work Editor. Search, Refresh, Publish and Git actions remain separate.
