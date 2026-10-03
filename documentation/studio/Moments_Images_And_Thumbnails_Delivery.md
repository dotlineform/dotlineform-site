---
draft: false
doc_id: d-20261003-222607-d910e8
title: Moments Images And Thumbnails Delivery
added_date: "2026-10-03 22:26:07"
last_updated: "2026-10-03 22:58:55"
summary: Enhance shared Add image with document-based naming and optional thumbnails in a registered thumbs media family, and migrate existing Moments images and references.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Moments Images And Thumbnails Delivery

## Current And Next State

Proposed delivery under [Planned Features](Planned_Features.md). The user requested this document and the migration scope; implementation, migration writes and publication have not been authorized. Next: confirm the remaining main-image naming choice at readiness, then obtain approval for the bounded code and migration change set. Works thumbnail generation parameters, Catalogue row presentation, thumbnail replacement, migration selection and orphan retention are settled requirements below, not readiness decisions.

The delivery now covers a generic enhancement to **Add image**, usable by Concepts, Moments and other documents with image-authoring capability. Use readable image filenames derived from the document title, optional **Create thumb**, and thumbnail filenames derived from the immutable `doc_id`. Store thumbnails in their own configured `thumbs` media family beside `img`. The imported image is already prepared for display, normally around 800px; Docs Viewer does not create primary size variants or a srcset. The previously requested migration of existing Moments images and references remains included.

Thumbnail processing belongs in Docs Viewer. Match the current Works thumbnail recipe and Catalogue row presentation through a contained Docs Viewer operation, without importing Studio's image pipeline or job orchestration. Reuse Docs Viewer's existing media storage and publication boundaries; matching output parameters and existing transport dependencies do not imply sharing thumbnail-generation code with Studio.

## Requirements

Deliver one complete outcome: shared Add image supports document-based image naming and explicitly selected thumbnails under each document's own media owner; collection rows display those thumbnails in Working and the prepared public projection, and existing Moments images/references adopt the same conventions.

### Shared Authoring And List Scope

Apply the authoring enhancement to ordinary documents and named-collection documents wherever the existing Add image capability is available. Collection identity selects storage and route context; it does not select a separate thumbnail-generation workflow. Concepts and Moments use the same implementation and naming rules.

The shared collection report renders assigned thumbnails for its document rows, including Concepts and Moments, without a collection-name whitelist. Catalogue retains its existing generated Work thumbnails and separate media ownership; this delivery does not rename Catalogue media, alter its regeneration workflow or add image editing to generated Catalogue documents. Ordinary Index, Search, Recent and unrelated reports gain no thumbnail presentation through this delivery.

### Add Image And Naming

- Extend the existing **Add image** workflow through its shared dialog and insertion machinery. Use the exact ordinary/collection document context rather than copied collection-specific dialogs.
- Name the stored display image from the document's title using a websafe slug and its original supported extension. Preserve its bytes, dimensions and format; the caller prepares it for display before adding it. Existing authored references remain valid until explicitly migrated; there is no blanket rename of other collections' stored media.
- Keep **Create thumb** as an opt-in checkbox, unchecked by default. When checked, generate one 96×96px WebP from the selected raster image using the Works recipe below and associate it with that document. No automatic first-image selection applies to new authoring.
- Use `<doc_id>-thumb.webp` for the thumbnail. A title change never changes this identity. When thumbnail generation is requested for a newly added image, write that image's thumbnail over any existing thumbnail at the same identity. Add no existing-thumbnail validation, choice, collision preview or replacement confirmation. With the checkbox unchecked, image insertion leaves the existing thumbnail alone.
- Main-image references remain explicit. Their title-derived name is chosen when the image is added and is not recomputed on every title edit. A later document title change does not trigger automatic media renaming.
- Validate the exact collection/document identity and destination filename at the service boundary. A browser naming helper cannot own filesystem renaming or raster generation.

The collision-safe main-image convention is the remaining proposed choice below. Thumbnail generation and row presentation match Works/Catalogue as specified below. An 800px input is an authoring expectation, not permission to silently resize an unsuitable input. Existing input/path handling remains; it does not introduce a separate thumbnail-replacement validation workflow.

### Source Metadata And Collection Rows

The canonical document source must record its thumbnail assignment. Collection generation projects a small `has_thumbnail` flag from that assignment; it does not infer intent by listing files. The list derives the thumbnail filename from `doc_id` and that collection's configured `thumbs` media base, without reading every document or requesting thumbnails for rows whose flag is false. Identical filenames under different collection owners remain separate assets.

Keep source thumbnail metadata small, with exact fields settled during implementation. It records thumbnail presence/reference, not a competing selection history or a rule that can prevent the next image from overwriting the thumbnail. Integrate it with Source editing and the existing committed-record/list update path. A generated flag alone is not authoring authority. Explicitly changing thumbnail metadata updates the next manifest and the retained caller through its existing owner.

The list matches Catalogue's existing thumbnail presentation: a reserved 64×64px image box, `object-fit: contain`, 6px rounded corners, vertically centred beside the title with the existing `--docs-viewer-space-3` gap. Use lazy loading, asynchronous decoding, decorative empty alt text and the existing shared image/title navigation control. Generalize the current Catalogue row styling for assigned document thumbnails rather than creating a separate Moments presentation. Documents without thumbnails remain usable text rows. An unavailable image does not prevent navigation. Thumbnail presence does not change a collection's ordering, document identity, dates, readiness, Search membership or navigation behavior.

### Generation And Publication Ownership

Keep raster generation in a small Docs Viewer service invoking FFmpeg for the same bounded thumbnail operation currently used by Works. Preserve the selected display image and generate only the requested thumbnail. Do not import Studio's srcset generator, Catalogue media policy or pipeline loader, or introduce a general media-job framework for this feature. Docs Viewer owns its thumbnail-only settings and operation; the current Works settings below define the required delivery baseline.

The configured Works recipe was inspected on 2026-10-03 in [pipeline configuration](../../_data/pipeline.json) and [thumbnail generation](../../studio/services/media/make_srcset_images.py). Use those current configured values, not the pipeline loader's fallback defaults:

| Parameter | Required value |
| --- | --- |
| Output size | One 96×96px thumbnail |
| Geometry | Scale proportionally until the square is covered, using Lanczos, then take a centred 96×96px crop; match the existing scaling behavior for small inputs |
| Format and encoder | WebP, `libwebp` |
| Encoder preset | `photo` |
| Thumbnail quality | 62 |
| Compression level | 6 |
| Metadata | Strip source metadata with `-map_metadata -1` |

The main display image remains unchanged and no primary variants or srcset are generated. Thumbnail filenames remain `<doc_id>-thumb.webp` in the document owner's `thumbs` family.

The current Catalogue presentation is owned by the [shared collection browser](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) and [report stylesheet](../../docs-viewer/static/css/docs-viewer-reports.css). Match its 64px row presentation for Moments and Concepts while preserving their own list behavior.

### Separate Thumbnail Media Family

Register `thumbs` as a managed derivative-media family beside `img`, owned by the same ordinary or collection document namespace. Store display-ready inputs under `img` and generated thumbnail bytes under `thumbs`:

| Document owner | Display image folder | Thumbnail folder |
| --- | --- | --- |
| Ordinary workspace | `$DOTLINEFORM_DOCS_BASE_DIR/assets/media/workspace/img/` | `$DOTLINEFORM_DOCS_BASE_DIR/assets/media/workspace/thumbs/` |
| Named collection | `$DOTLINEFORM_DOCS_BASE_DIR/assets/media/collections/<collection>/img/` | `$DOTLINEFORM_DOCS_BASE_DIR/assets/media/collections/<collection>/thumbs/` |

For example, Moments uses `assets/media/collections/moments/thumbs/<doc_id>-thumb.webp` and Concepts uses `assets/media/collections/concepts/thumbs/<doc_id>-thumb.webp`, relative to the configured Docs root. Preserve the agreed thumbnail filename convention; the folder changes the media role, not the document identity.

The current supported media-type set contains only `img`, `svg`, `files` and `html`; workspace configuration rejects an unregistered `thumbs` type. This delivery therefore includes registration and the relevant read/write, inventory, reference, snapshot and public-projection support. Check the owning package/export boundaries where they consume these roles; a directory or browser URL convention alone is insufficient.

Resolve all paths and local/public URLs through workspace configuration, including each owner's public `thumbs` projection. Reuse the existing workspace and collection media layout; do not create another media root, ready-media copies under Working source/generated, a separate Preview source tree, or a hardcoded public host. The `thumbs` role does not become a source-image chooser or a new editable build-source format.

Treat thumbnails as document-owned referenced media even though a collection list displays them and they are absent from the document body. Preparation must capture each eligible document's assigned thumbnail from its exact `thumbs` owner, and distribution must use that completed snapshot's recorded assets. The current public-media reference collector inspects by-ID body HTML, so adding a list flag alone would miss these assets; extend the owning reference/capture boundary explicitly, including the new media role. Do not insert hidden body images or discover files from derived public URLs as a workaround.

Generation completes within the awaited Add image operation and replaces the fixed thumbnail file immediately. This follows the existing media-write model: media is written before insertion into the dirty source buffer. Source Save retains its existing canonical-source persistence boundary, with watcher generation independent of Save. Cancelling the source edit does not undo a thumbnail overwrite or remove the newly stored image. Do not add deferred replacement, staging, rollback or cleanup machinery.

### Orphan Retention And Manual Reconciliation

Removing an image token, deleting its document or abandoning an edit leaves stored display images and thumbnails untouched. Removing a body-image token does not itself clear existing thumbnail metadata. Orphaned files remain in their registered media folders, and Docs Media/report inspection remains the manual reconciliation process. No token-removal hook, document-delete hook, automatic orphan scan, garbage collection or Publish cleanup is part of this delivery.

### Existing Moments Migration

Migrate the currently referenced display images and corresponding canonical Moment sources under their configured owner. Keep document IDs, titles, dates, readiness, text, poetry layout, captions, alt text and image dimension attributes. A mechanical reference/metadata migration preserves `added_date` and `last_updated`.

Moments is the existing-image migration scope. The user confirmed on 2026-10-03 that Concepts currently has no images, so Concepts needs no image migration or thumbnail backfill. Generic authoring and list support still apply to future Concepts images. Other collections' existing images are not part of this migration.

For each existing Moment, the first image token in document source order wins as its thumbnail source. Apply the same rule to documents with several images; do not choose a better image, validate against an existing thumbnail choice or request a selection decision. Documents without images remain without a thumbnail. Preserve display-image bytes rather than resizing them during migration.

Materialize the migrated display images under their new `img` identities with the existing images' exact bytes, update their document references, and generate each Moment's thumbnail under `thumbs` from its first image. Leave old image files in place even when the new references make them orphaned. Use the same naming and generation owner as new Add image operations, without compatibility aliases, duplicate writers or permanent alternate lookup rules. Retained orphan bytes are not used as runtime fallback targets.

The migration removes no local or remote media. Previously prepared 1200/1600px variants, unrelated unused images and old filenames remain available for manual report-based reconciliation. Existing Preview/public/export references and release holds remain supported by those retained bytes. Publish and deployment are separate authorized actions; no media deletion is needed to complete this delivery.

Regenerate affected Working document and manifest output through the watcher or the supported targeted collection build when the watcher is unavailable. A complete Moments reconciliation is justified if the manifest/reference contract changes globally or targeted prerequisites are missing. Search remains separately requested. Do not hand-edit generated JSON, Preview or `site/` document payloads.

### Proposed Naming Choice For Readiness

| Choice | Proposed default | Reason or remaining decision |
| --- | --- | --- |
| Main-image filename | `<title-slug>-<doc_id>.<extension>`; numbered suffixes for additional images if needed | Retains a readable title and prevents different documents with duplicate title slugs from sharing a write target. The title-plus-ID convention is a proposal beyond the agreed title-derived naming. |

## Deliverables

- [ ] Generic document-based naming and **Create thumb** in the shared Add image workflow.
- [ ] A Docs Viewer-owned raster thumbnail service using the current Works 96px crop/encoding recipe and validated media write contract.
- [ ] Registered ordinary/collection `thumbs` media families with configured local/public paths and relevant lifecycle/reference support.
- [ ] Canonical thumbnail assignments, projected presence metadata and shared Working/public collection-row rendering with Catalogue's existing 64px thumbnail presentation, including Concepts and Moments.
- [ ] Preparation and publication reference support for thumbnails outside document body HTML.
- [ ] Migrated existing display-image names, source references and thumbnails, with affected Working output reconciled.
- [ ] Shared/public runtime projection and focused validation where those files change.
- [ ] Shipped behavior documented in [Media And Asset Handling](Media_And_Asset_Handling.md), including generic naming, the `thumbs` role, source assignment and publication ownership.

## Process

1. Prepare a display-ready image outside Add image and place it in the workflow's supported input location.
2. Open an authorable document in Source, choose **Add image**, select the file and enter its alt text/presentation options.
3. Check **Create thumb** when this image should represent the document in a supported list. The thumbnail uses its fixed identity in the separate `thumbs` location and replaces any existing thumbnail without another prompt or validation workflow.
4. Await the media operation. On success, insert the image reference and thumbnail assignment into the editable source; report a failure at the point reached without claiming uncompleted effects or automatically undoing completed writes.
5. Save the source through the existing Save operation. Its confirmed metadata updates the retained list; the watcher owns generated-document refresh. Media writes have already completed and remain even if the source edit is discarded.
6. Use normal Publish when separately authorized to prepare and distribute the eligible documents and their referenced media. Review public presentation through site-preview before the separately authorized public release.

## Delivery Steps

### MIT 0 Readiness

- [ ] Confirm broad source, shared insertion, collection-list, media registration and publication owners against the current product, including ordinary documents and Concepts.
- [ ] Confirm the proposed main-image naming convention.
- [ ] Carry the settled Works generation recipe, Catalogue row presentation, first-image migration, unconditional thumbnail replacement and manual orphan-retention rules into the implementation scope.
- [ ] State the bounded code/migration change set and obtain implementation approval.

Verification budget: read-only owner/config inspection and source review. No prototype, migration writes, media inventory project or executable tests are needed merely to approve readiness.

Gate: stop if destination identity or source metadata cannot be represented through the existing owners, or if the work requires broader Studio/media architecture changes. Do not reopen the settled thumbnail-selection, replacement or orphan-retention policies.

Record: pending. Planning inspection identified the shared staged-media service and collection report/manifest builder, the current four-type media registration, and the body-only public-media reference collector. Concepts uses the same `docs_collection` report as Moments. No implementation readiness or migration inventory is claimed.

### MIT 1 Naming And Thumbnail Authoring

- [ ] Implement the bounded Docs Viewer FFmpeg thumbnail operation with the specified Works parameters and generic document naming within existing Add image owners.
- [ ] Register the `thumbs` managed media family and resolve ordinary/collection destinations through the existing configuration owner.
- [ ] Carry the exact document/title context, proposed destination names and opt-in selection through validated requests.
- [ ] Carry thumbnail presence through Source editing, replace existing thumbnail bytes unconditionally, and retain completed media writes on source cancellation.
- [ ] Keep primary bytes unchanged and produce no srcset variants or Studio pipeline dependency.

Verification budget: targeted Python/JavaScript lint and direct image/file diagnostics for a justified existing input. These establish source validity and actual derivative dimensions/format, not broad workflow coverage. Record the exact targets, writes and cost before execution. User manual review covers dialog behavior; new test code requires its own approved specification.

Gate: the media result and source assignment agree, and failure reporting does not imply rollback or successful insertion after an incomplete operation.

Record: pending; no code or media changed.

### MIT 2 Collection And Publication Integration

- [ ] Project thumbnail presence from canonical assignment and render assigned thumbnails through the shared collection-list owner using Catalogue's existing 64px presentation, including Concepts and Moments.
- [ ] Include the registered `thumbs` family and assigned thumbnails in relevant inventory/reference reads, eligible document media capture and completed-snapshot distribution; inspect package/export role handling where affected.
- [ ] Reuse committed-record reconciliation and existing cache/refresh behavior for changed assignments and replaced thumbnail bytes.
- [ ] Project changed shared/public code with `bin/site-code-update`, inspect its tracked delta, then run its check and `bin/site-validate`.

Verification budget: focused lint, generated metadata/reference diagnostics and required static projection/validation. Inspect any exact existing test selection and its durable coverage before proposing a run; no suite or browser test is automatic. Working/public visual fit remains user manual review. Public transfer behavior is unverified until separately authorized publication.

Gate: ordinary and named-collection thumbnails resolve through their exact registered owners; list-only thumbnails are captured as media, excluded documents contribute no public thumbnails, and rows without thumbnails issue no speculative image requests. Missing images leave document navigation usable. Catalogue retains its own generated-media behavior.

Record: pending; no manifest, runtime projection or publication changed.

### MIT 3 Existing Image And Source Migration

- [ ] Resolve current Moment identities, image tokens in source order and `img`/`thumbs` destination names; use the first image for each thumbnail without a selection or existing-thumbnail validation pass.
- [ ] Apply the approved migration through the same naming/generation owner, preserving primary bytes and authored content/metadata.
- [ ] Update every affected active source reference and thumbnail assignment, then reconcile affected Working output through its owning build path.
- [ ] Leave old identities, orphaned images, historical variants and public/held assets untouched; use reports for later manual reconciliation.

Verification budget: direct source/reference and file diagnostics, byte comparison for renamed primaries, generated thumbnail dimensions/format, and inspection of affected builder output. A targeted or complete Moments build may write replaceable Working output as justified above. Record actual selection, cost and effects before the migration; no new regression scripts or Search rebuild.

Gate: migrated display references use the new names, each document's first image supplies its thumbnail, dates/body layout remain intact, and original media files remain untouched. The reader uses no alias or fallback to old names.

Record: pending; existing images, source documents and generated payloads are unchanged.

### MIT 4 Code Review

- [ ] Review the final bounded code/config/source/generated delta for identity collisions, ownership drift, Studio coupling, duplicated dialogs, speculative thumbnail requests, missed publication references and compatibility residue.
- [ ] Review migration results against source-order first-image selection and the no-deletion boundary; remove any added thumbnail-selection, replacement-confirmation or orphan-cleanup machinery.
- [ ] Resolve findings and repeat only evidence affected by corrections.

Verification budget: source/diff review and already selected evidence; additional runs need a concrete remaining risk. Gate: review findings are resolved or explicitly scoped before closeout.

Record: pending; code review is not applicable to this planning-only document creation.

### MIT 5 Closeout

- [ ] Record user manual review of shared image insertion, thumbnail choice/replacement, Concepts/Moments collection rows and migrated Moments.
- [ ] Update the durable media owner with the shipped convention and actual replacement/cancellation behavior.
- [ ] Report exact focused evidence, media/source/generated changes and publication status, with orphaned files left for manual report-based reconciliation.
- [ ] Present a retain-or-retire recommendation for this delivery document; do not delete it without approval.

Verification budget: bounded documentation/result review; no repeated builds or tests solely for closure. Gate: the complete Working outcome is delivered, its public projection/reference contract is ready, and publication status is stated separately.

Record: pending. Publish, remote deletion, deployment, commit and push remain separate explicit actions.

## Follow On

Thumbnail presentation in ordinary Index, Search, Recent or unrelated reports, srcset generation, automatic title-change media renaming, a general media pipeline, migration of other collections' existing images and historical variant/remote cleanup are outside this delivery. Generic Add image and shared collection-row support are within this delivery. Test authoring or changes follow [Test Contract Discipline](Test_Contract_Discipline.md) and [Testing](Testing.md), with coverage maintained outside this delivery.
