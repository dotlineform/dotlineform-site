---
draft: false
doc_id: d-20261006-122135-8c74a1
title: Docs Static Image Conversion Delivery
added_date: "2026-10-06 12:21:35"
last_updated: "2026-10-06 12:35:24"
summary: Docs-owned native raster conversion to an 800px-long-edge WebP with optional original-upload thumbnails and explicit animation rejection.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Docs Static Image Conversion Delivery

## Current And Next State

Status: complete and accepted on 2026-10-06. After implementation, the user confirmed a successful Add image operation that saved an 800px image. Native raster conversion, naming, documentation, focused static checks and code review are complete. This manual confirmation covers the reported addition and sizing; input format/orientation, upscaling, replacement/collision, thumbnails, animation rejection and failure scenarios were not itemised, so no exhaustive runtime coverage is claimed. This standalone delivery is parented to [Planned Features](../Planned_Features.md). [Media And Asset Handling](../Media_And_Asset_Handling.md) owns the lasting intake contract. Retain this delivery for recent-work lookup until manual archive.

## Requirements

- Add image and selected-file Edit image replacement store one WebP with an exactly 800px long edge, scaling up or down proportionally without cropping.
- Docs Viewer owns the converter and its settings independently of Studio. Start with Works primary encoding: FFmpeg `libwebp`, Lanczos scaling, `photo`, quality 82, compression level 6 and stripped metadata.
- Accept JPEG, PNG, static WebP and single-frame GIF; reject animated inputs before permanent writes. Animation support is deferred until needed.
- Store `<normalized-source-stem>.webp` and compare converted bytes for reuse or confirmed shared-asset replacement. Different raster extensions with the same normalized stem address the same managed identity.
- Preserve the selected file. Optional 96px square thumbnails use the original upload through their existing Docs owner. SVG, Mermaid, Add file, package Import, existing media and presentation-only image edits retain their current workflows.

## Deliverables And Process

One Docs-owned converter is invoked by the existing native media preparation path before collision comparison and storage. The stored identity flows through the existing canonical token, exact document/collection owner and awaited insertion response. Required media writes complete before insertion; Source Save, watcher generation and Publish remain separate. Update the durable media contract, author guide and dependency boundary.

## Delivery Steps

### DSI 0 Readiness

- [x] Confirm one shared native server intake covers insertion and selected-file replacement.
- [x] Confirm existing pinned Pillow can validate static input and existing FFmpeg supplies the Works encoding recipe.
- [x] Bound the change to native raster preparation, filename identity and its documentation; no compatibility alias or public runtime change is required.

Record: ready and implementation authorized. Conversion must happen before collision decisions or permanent media writes. Same-stem collisions, unsupported animation, decoder/converter errors and untouched original-upload thumbnails are the main review risks.

### DSI 1 Implementation And Evidence

- [x] Add independent Docs static raster validation and 800px WebP preparation.
- [x] Route native raster naming/preparation through the converter while preserving other media paths and thumbnail input.
- [x] Update the durable contract, author guide and dependency description.
- [x] Run changed-Python lint/syntax, service-import diagnostics and whitespace checks.

Verification budget: focused lint/syntax and direct import diagnostics for changed production modules plus bounded source/diff review; expected seconds for commands and minutes for review, with no permanent media writes or network effects. No tests, temporary regression scripts, browser automation or existing-image migration are authorized. Static evidence does not demonstrate actual conversion dimensions, image quality, upload/replacement behavior or animation failure handling; those remain manual review gates.

Gate: resolve static failures and documentation mismatches within this slice. Do not expand into package conversion, Studio media, public output or test work.

Record: `docs_source_image_conversion.py` owns static-format/frame-count validation and FFmpeg display conversion; native media preparation uses it before comparing converted bytes. Changed-Python lint and `py_compile` passed for the converter and media service. Direct imports of conversion, media, management and HTTP services passed with configured environment loaded. Whitespace checks cover tracked changes and both new files. The durable media contract, author workflow and dependency boundary are current. No browser/public runtime file changed, so no site code projection or public validation is needed. Codex ran no tests, real conversion/media writes, document/Search builds, Publish, deployment, commit or push. The user's subsequent real Add image check is recorded in closeout.

### DSI 2 Code Review

- [x] Review independent ownership, converted-byte collision semantics, animation rejection before writes, unchanged original/thumbnail inputs and vector/file boundaries.
- [x] Resolve material findings and rerun only affected checks.

Gate: no unresolved material finding in the bounded final diff. Record actual evidence limits.

Record: bounded source/diff review complete. Native additions and selected-file replacements share the converter; already-WebP uploads also convert. Frame-count validation precedes storage, vectors/downloads retain their paths, and optional thumbnails still receive the original temporary upload. No Studio converter/config import, compatibility alias, second storage writer or existing-media migration was added. Review removed an unnecessary full Pillow pixel decode; Pillow inspects format/frame count and FFmpeg owns pixel decoding. Changed-source lint/syntax and whitespace checks passed after that adjustment. Actual decoder/FFmpeg output, byte reuse/replacement, thumbnail failure handling and visual quality remain manual evidence gaps.

### DSI 3 Closeout

- [x] Reconcile implementation and durable documentation, report exact evidence and manual review limits.
- [x] Update this delivery and its Planned Features link with current state.
- [x] Record the user's successful 800px Add image check and acceptance; retain this delivery for manual archive without document deletion.

Gate: implementation and code review complete. User review of real additions/replacements and resulting images remains separate from delivered code. No Docs/Search build, Publish, deployment, commit or push is required.

Record: closed after the user's successful Add image/800px confirmation on 2026-10-06. The manual result supplements the accepted implementation/static evidence for that operation; replacement, thumbnail, animation and failure scenarios were not individually confirmed. Lasting behavior is in Media And Asset Handling, with author instructions in Docs Images And Assets and dependency ownership in Dependencies. Closeout changed documentation only and reused implementation evidence; no further executable check or Docs/Search rebuild was needed. Retain this delivery and its Planned Features link for recent-work lookup until manual archive; no documents were deleted. Publish, deployment, commit and push remain separate.

## Follow-on

Animated-image support and any new or retargeted conversion/intake tests require their own requirements and authorization. Existing media is not migrated by this delivery.
