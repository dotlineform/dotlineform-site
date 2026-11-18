---
draft: false
doc_id: d-20261118-180200-809cfb
title: Document Media And Thumbnails Review
added_date: "2026-11-18 18:02:00"
last_updated: "2026-11-18"
summary: Migration and acceptance evidence for document media ownership, reuse, cleanup and thumbnails.
ui_status: done
parent_id: d-20261118-151521-a0f9c3
---
# Document media and thumbnails review

## What shipped

- **R2 namespace.** On 15 October 2026, 137 current objects moved to `docs/media/` with byte-size and ETag verification. The follow-up checked all 85 Docs media references from the deployed snapshot, then deleted 317 authorized legacy objects. The 111 former Moments variants remained in Working. The original record names deployed commit `1c4432723bc39d16db972ff51018dc8a7d5aa5e2` and inventories in `var/verification/2026-10-15-docs-r2-migration/`. Catalogue Work media was outside the migration.
- **Document-ID ownership.** On 16 October, 342 referenced body-media files were copied and 245 sources rewritten, including drafts, preserving bytes and authored metadata. Old flat copies remained for manual review. The separately approved cutover Publish applied 41 document writes, 204 draft withdrawal selections and 85 selected media transfers. The user later accepted a real workflow covering Draft additions/removals, copying references into a publishable document, deleting the Draft and publishing the result.
- **Adoption and whole-document cleanup.** On 18 October, bounded implementation review covered copy/rewrites, same/different destination bytes, missing Working input, nested and unused files, the fixed thumbnail, ordinary descendants and queue-before-unlink ordering. The original record reports lint, compilation and import checks. It leaves live failure variants and the full Delete matrix unexercised.
- **Independent thumbnails.** The October reset removed 40 authored thumbnails and 39 obsolete source declarations and queued the corresponding public removals. Thumb uses a separate document-owned file. [Thumbnail delivery and reset](Subject_Retirement.md#existing-thumbnail-reset) · [Earlier Moments migration](Moments_Images_And_Thumbnails_Delivery.md)

The full dated implementation evidence is retained in Git at `c76f6608ef:documentation/studio/Media_And_Asset_Handling.md`. Earlier intake and report work has its own evidence. [Image token delivery](Image_Token_Delivery.md) · [Docs Media report refactor](Docs_Media_Report_Refactor.md)

## Remaining follow-up

Old flat media and partial-write orphans are manual review. The current R2 report lists findings and leaves decisions and deletion to the operator. The scope-era staged-media tests need a separately scoped retirement or replacement review. [Current lifecycle](../reference/Media_And_Asset_Handling.md) · [Code and file follow-ups](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)

## Later Thumbnail Acceptance

On 14 November the user accepted **Edit → Thumb → From this document**, replacing a thumbnail from a rendered raster, SVG or Catalogue image. Review reused the active document mount and existing thumbnail publication selection, with decoding/pixel bounds at replacement. Focused lint, compilation, whitespace, public projection and site validation passed. Individual image families, deletion and failure cases were not separately reported. The older Planned Features entry's broad pending acceptance for 18 October adoption/Delete work is superseded by the later real-workflow acceptance above; it does not establish the unexercised failure variants.
