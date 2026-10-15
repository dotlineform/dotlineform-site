---
draft: false
doc_id: d-20260907-201225-db6e8a
title: Analysis Media In R2
added_date: "2026-09-07 20:12:25"
last_updated: "2026-10-15 16:55:29"
summary: Restore legacy Moments media to Working and make R2 mirror the accepted Analysis media structure.
ui_status: paused
parent_id: d-20260902-102745-8379ea
---
# Analysis Media In R2

This delivery records the September migration. Current storage and publication paths are maintained in [Media And Asset Handling](Media_And_Asset_Handling.md#r2-namespace-and-historical-cleanup); the October maintenance migration superseded its R2 layout without changing its original restoration evidence.

## Requirements

All public Analysis media lives in R2. Mirror paths inside Analysis `published/` beneath R2 `docs/analysis/`: parent `media/<type>/...` and child `sub-scopes/<collection>/media/<type>/...`. Working and Generated remain local. R2 contents do not establish document publication status.

Restore all legacy Moments images to `analysis/working/source/sub-scopes/moments/media/img/`, verify their bytes and replace the documents' external URLs with local collection tokens. Moments has not been published and must not be added to the accepted snapshot or the new R2 projection.

## Deliverables

- Collection-aware R2 media configuration and deployment from accepted Published media only.
- Restored local Moments images, updated references and Generated output.
- Migrated accepted Analysis media, updated tracked public media references and removal of obsolete local public media files.
- Legacy R2 cleanup only after byte preservation and reference checks; Catalogue and unrelated R2 prefixes remain independently owned.

## Process

Source → Build/Generated → Publish/Published → R2 deployment. This migration changes media placement and accepted public URLs. It does not enable the deferred Analysis promotion controls, publish newer documents, commit, push or trigger GitHub Pages. No background services are started by Codex.

## Delivery Steps

- [x] ARM-0 — Confirm current Published authority, local ownership, R2 inventory and old URL references.
- [x] ARM-1 — Restore and verify Moments media locally; update its references and Generated output.
- [x] ARM-2 — Implement collection-aware R2 projection and verify the changed deployment contract.
- [x] ARM-3 — Apply the reviewed media migration, verify remote/local parity and remove obsolete tracked media. Legacy R2 deletion has the explicit release dependency below.
- [x] ARM-4 — Review the final changes and resolve findings.
- [ ] ARM-5 — User acceptance, durable transfer and closeout.

| Contract or risk | Lowest adequate evidence | Permanent test change |
| --- | --- | --- |
| A child uses parent media or a repository public destination | Configuration, URL projection and reconciliation service tests | Extend owning tests |
| R2 differs from accepted media or cleanup crosses an owner boundary | Fake-R2 reconciliation tests and exact migration manifests | Extend owning tests; retain one-off inventory |
| Moments media is lost or published prematurely | Remote/local byte hashes, exact source edits and Generated membership | One-off evidence |
| Existing public references break | Tracked reference audit, matching new objects and site validation | One-off evidence |

## Baseline Inventory

Analysis Published contains 12 media files: two parent files and ten Works files. R2 has one legacy Analysis PDF plus folder marker objects. Legacy Moments contains 111 WebP files (three size variants for 37 images) and three folder markers; 36 image URLs are currently referenced by its 56 documents. Restore all 111 image files to preserve the extra variants and unreferenced image.

## Follow-on

Ready for user review. Analysis promotion controls and Git/public deployment remain separate. Retain local unused Moments variants until the user chooses any later editorial cleanup. Restart the user's `local-all` when ready to load the changed configuration and Python services; Codex has not started background processes.

## Live-Site Release Dependency

Rechecked on 15 October 2026: the live site still exposes `/moments/` and the old scope configuration from the successful 13 July deployment. Its artifact contains 36 exact legacy Moments image references, and sampled live configuration/document bytes match that deployed commit. Preserve all 111 legacy Moments images until replacement public deployment and live-reference verification release them. All 111 have matching local bytes. This temporary hold adds no alternate writer or runtime fallback.

The follow-up audit established that the legacy Analysis PDF is not referenced by the checked deployed artifact or current local/public payloads and has identical bytes at `docs/media/collections/works/files/d-20260801-212422-df11f3-attachment-01.pdf`. Its old key is removable, as are the folder markers, which are unnecessary for serving descendant objects. The September 118-object hold is therefore superseded by the current 111-image hold. Exact current keys, replacements and evidence are recorded in `var/verification/2026-10-15-docs-r2-migration/`. The follow-up copied the 137 current media objects into `docs/media/` and updated configuration; neither migration deleted remote objects.

## Result And Evidence

- Restored 111 Moments WebP files (19,317,698 bytes) with remote/local byte verification. Replaced the 36 external image references with collection tokens; all 56 Generated documents and their 36 referenced image files verify. Moments remains absent from Published.
- Uploaded the 12 accepted Analysis media files to their exact new R2 paths. Authenticated reads and all 12 public URLs match Published bytes; PNG, JPEG, WebP, PDF and HTML content types verify. The new R2 trees contain exactly these 12 files.
- Changed only media URLs in three tracked public document payloads and removed their 11 obsolete local media copies. Refreshed canonical/site public browser configuration from its owner, including the four R2 media prefixes and the already-configured Analysis icon. The accepted 288-file Analysis snapshot remains unchanged.
- Focused configuration, collection building, storage, lifecycle, deployment and reconciliation tests: 114 passed. The final reconciliation-only rerun passed all five tests after the review adjustment. Python lint, `git diff --check`, `bin/site-code-update --check` and `bin/site-validate` pass. No browser interaction test or Search rebuild was required.
- Bounded review checked Published ownership, exact child destinations, same-name separation, missing-file handling, upload-failure cleanup, retired-path compatibility and the media-only repository delta. Corrected the per-type reference count to remain a reference count when unreferenced accepted files are included. Final source review also caught and removed a nested token introduced by the Moments URL conversion: the existing media wrapper and dimensions are preserved while only its target changes. All 36 exact rendered image URLs, widths and heights now verify against Source, and the watcher rebuilt the corrected payloads. No unresolved findings remain in this slice.

One-off inventories, previews, source/remote byte proofs, public URL checks and command logs are under `var/analysis-r2-migration/`. Durable ownership and serving rules are transferred to [Source Organisation](Source_Organisation.md) and [Media And Asset Handling](Media_And_Asset_Handling.md).
