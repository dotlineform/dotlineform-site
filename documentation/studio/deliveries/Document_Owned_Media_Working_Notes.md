# Document Owned Media Working Notes

## Current State

Document-owned media and Source Save processing are implemented. Browser state owns pending Files, final-buffer membership and replacement choices. Python owns bounded uploads, selected raster conversion/SVG sanitization, confined persistence, exact document generation, owned-reference differences and queue handoff. Thumbnails remain independent flat `<doc_id>-thumb.webp` assignments.

Working `generated/documents/publication-media.json` contains root `ignored` and `documents`, with only `collection` and `media` per document. Generation extracts the source/field reference list once for both eligible publication and previous/current ownership. Queue persistence precedes selected Working deletion and the new baseline. Removals merge across later Saves/withdrawals and cancel only when completed ownership restores ready bytes. Whole-document media cleanup and old flat/orphan cleanup remain manual.

The retired diagram compiler, producers, source-opening routes, browser renderer, themed adapters, toolchain and vendor files are removed. Diagrams are externally authored SVG images. Generic SVG detail presentation remains. Workspace schema is `docs_workspace_v9`; no build-source registry or compatibility reader remains. The leftover local dependency directory and its specific ignore rule were subsequently deleted at the user's request. Documentation diagrams remain intact for external rendering.

## Completed Local Migration And Publish

The separately approved migration copied and byte-verified 342 body-media files (341 images and one HTML asset), 21,957,143 bytes, rewrote 245 canonical documents while retaining authored fields/dates/IDs, and completed exact generation in three calls: two ordinary, 206 Context and 37 Moments documents. Of these, 204 were Draft. All original files and 37 flat thumbnails remain. Builders rescanned zero source files, emitted zero warnings and changed no Links/index/manifests/Recent. Search and saved reports were untouched.

The separately approved single Publish completed in 36.821 seconds: 41 eligible document writes, 204 Draft withdrawal units and 85 selected media transfers. No media removal/shared/Catalogue unit was selected. It cleared those selections at `2026-10-16T15:22:39Z`. The tracked site received 41 by-ID changes; the Draft targets were already absent. Git/push/manual deployment remained separate.

Ignored evidence lives under `var/verification/2026-10-16-document-owned-media/`: `migration-plan.json`, `local-migration-result.json`, `publish-selection.json`, `publish-result.json` and `publish-inspection.json`. The operational migration script has already run and must not be rerun merely for evidence. Preserve later authoring work.

## Single-List Conversion And Current Pending Work

Converted all 245 saved media records directly, retaining 378 source references and the exclusion policy. One source reference is absent from rendered HTML; retaining the source list preserves ownership. No document rebuild, source/asset/queue write or Publish was needed for this metadata-only conversion.

At conversion inspection, `3 symbols (cards)` retained `cards-back.webp`, `cards-face.webp`, image 03 and image 04. Its Draft withdrawal selection retained exactly `bandage-back.webp`, image 01 and image 02 as removals. Do not clear or publish these later authoring selections incidentally. The saved Docs Media report contained zero build-source rows and needed no conversion or Refresh.

## Verification And Review

Implementation evidence: focused Python lint for 21 owners, JavaScript lint for 12 modules, Python compilation, service/configuration imports and ordinary/collection builder CLI-help diagnostics passed. Review removed duplicate rendered-media extraction, producer companion plumbing, unused write arguments, source-role abstractions, theme refresh maps and temporary inline resources. The normal write-free image-preparation provider hook and ordinary SVG detail view remain.

Public projection changed nine JavaScript/CSS files and removed the retired themed adapter. Projection check and site validation passed: 103 projected files, 71 runtime modules, 60 required files, seven directories and one route/seven route files. No public document JSON changed during single-list conversion. Existing 41 by-ID edits from the earlier Publish were retained. Static evidence does not establish browser interaction or partial-failure acceptance.

The user's follow-up approved deleting obsolete implementation, test, configuration and historical references while preserving documentation diagrams. Five dedicated Python test modules and one browser smoke were deleted; producer/source/watcher cases and fixture data were removed from mixed files. Generic fenced-code cases retain their behavior with a neutral language label. The browser profile now retains Manage boot, Review authority and public read-only isolation. [Testing](../Testing.md#diagram-pipeline-cleanup) records the bounded cleanup and current verification selection. Final cleanup evidence: Python lint and compilation passed for all 19 changed files; the two focused runner/Markdown checks passed in 0.04 seconds. The converter case was blocked at collection by its unchanged support module importing `docs_scope_config`, so its behavior remains unverified. The physical cleanup freed approximately 404 MB and removed 20 stale feature bytecode files. Final source/diff and defensive review preserved generic SVG/code coverage, current publication/removal evidence and all eight documentation diagrams. Remaining term references are only diagram fences and their notation guide. No production runtime/public artifact or configured workspace changed. DOM.8 is complete, with unrelated scope-era test migration excluded.

## Remaining Work

Restart the local service and reload before normal use. Manual Add/Edit/Save/discard, replacement, thumbnail independence, removal/cancellation and failure acceptance remain user-owned. Git commit/push, manual Pages deployment and deployed acceptance remain separate. Optional orphan cleanup is not a gate. Existing unrelated scope-era tests remain unreviewed; this cleanup does not migrate the full test suite or establish broad coverage.
