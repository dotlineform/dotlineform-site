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

Proposed; implementation awaits approval. Show a temporary image preview and editable physical-dimension defaults before Save, so selection, corrections and persistence take one Save. [Catalogue Work Editor](../Catalogue_Work_Editor.md) will own shipped behavior; [Planned Features](../Planned_Features.md) parents this delivery.

## Requirements And Deliverables

- Inspect only a confirmed single-file selection in New/existing Work editing. Picker highlights and metadata edits do not trigger processing. Folder-batch per-image defaults/previews are a separate delivery.
- Produce one still **WebP**, maximum **512 px longest edge**, **quality 75**, **compression level 1**, preserving aspect ratio without cropping/upscaling. Show original pixel dimensions with orientation consistent with the preview and Save. Large-source decoding remains necessary.
- Fill initially blank `width_cm` / `height_cm` using **300 dpi**: `round(original_pixels × 2.54 ÷ 300, 2)`, independently of embedded DPI or preview size. Example: 3000 × 2400 px → 25.4 × 20.32 cm.
- Preserve nonblank saved dimensions and manual draft edits, including clearing. Track automatic defaults in browser state; subsequent file selection replaces only those defaults. Both fields remain editable with existing Save validation.
- Keep metadata editable during inspection and disable Save until the current request finishes. Errors identify the selected-file failure and clear busy state; existing Save rules remain authoritative.
- Release preview bytes/object URL on replacement, discard/cancel, Work change, editor exit or completed Save; ignore late superseded results. Save prepares its normal persistent renditions from the original.

## Implementation And Ownership

The browser owns selection/request lifetime, preview Blob/object URL, dimension defaults/manual precedence and disposal. Integrate the existing [file picker](../../../studio/app/frontend/js/catalogue-project-media-picker.js), form/draft state and [preview renderer](../../../studio/app/frontend/js/catalogue-work-sections.js); successful Save adopts its existing response.

Python returns original dimensions and preview bytes through one read-only local request. Reuse configured-source resolution, path/symlink confinement, local-origin authority and narrow [dimension/conversion primitives](../../../studio/services/catalogue/catalogue_build_media.py). Resolve configuration/source once, without loading Works, building a full rendition task or inspecting output files. Prefer binary WebP with dimension metadata to base64 JSON.

Convert from the source path to a memory pipe; capture only the small encoded output. Release server buffers after responding and browser references/object URL on disposal. Decoder memory may still reflect the large original. Create no application temporary/staging files, server cache or preparation token. [Save](../../../studio/services/catalogue/catalogue_output_media.py) retains canonical/media/version writes and queue effects.

## Process

Select file → preview/source pixels and eligible defaults → adjust metadata/dimensions → Save once. Discard uses the existing draft owner.

## Delivery Steps

### WIP-0 — Readiness

- [ ] Confirm formats/orientation, draft/discard/Save lifetimes and the single-file boundary; approve implementation.

Gate: agree the narrow response and ownership split. Raise changes to Save, batch behavior or persistent preparation before implementation; keep readiness read-only.

### WIP-1 — Implementation And Focused Evidence

- [ ] Implement inspection, preview/defaults, pending/error behavior and draft/Save disposal.
- [ ] Select and run proportionate evidence with a recorded budget.

Budget: changed-path lint, syntax/import/whitespace checks and one selected real-image inspection; choose the image and estimate decode/memory cost before running. Manual review covers New/existing Works, overrides, replacement/discard, orientation, failure and one-Save behavior. New/changed tests or browser automation require separate approval under [Testing](../Testing.md); no corpus scan or benchmark is required.

### WIP-2 — Code Review

- [ ] Complete distinct source/diff review and the mandatory Redundancy And Defensive Behavior Review in [Development Checklist](../Development_Checklist.md).

Gate: trace normal, replacement, manual/empty-dimension, failure and disposal paths through reused helpers. Challenge duplicate reads/decodes, hidden staging/loading, audits, caches, fallbacks and recovery. Retain selected-file authority, confinement, decoding/response and async lifetime checks; record findings and repeat affected evidence only.

### WIP-3 — Closeout

- [ ] Transfer shipped behavior and evidence limits to Catalogue Work Editor; update durable guardrails and Planned Features.
- [ ] Record manual acceptance and any service restart/reload requirement.

Gate: reconcile evidence/limits and recommend retaining or retiring this delivery. Search, Refresh, Publish and Git actions remain separate.
