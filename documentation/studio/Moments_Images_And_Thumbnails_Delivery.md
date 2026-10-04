---
draft: false
doc_id: d-20261003-222607-d910e8
title: Moments Images And Thumbnails Delivery
added_date: "2026-10-03 22:26:07"
last_updated: "2026-10-04 13:04:26"
summary: Enhance shared Add image with document-based naming and optional thumbnails in a registered thumbs media family, and migrate existing Moments images and references.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Moments Images And Thumbnails Delivery

## Current And Next State

Completed under [Planned Features](Planned_Features.md) and accepted for closeout by the user on 2026-10-04. Shared image naming and optional thumbnails, media/source migration, Working reconciliation, public runtime/configuration projection and bounded code review are complete. The user ran Publish and reviewed site-preview, confirming public loading and opening Moments after the configuration correction, then accepted the public list-navigation correction and authorized closure. [Media And Asset Handling](Media_And_Asset_Handling.md) owns the shipped behavior, and [Development Checklist](Development_Checklist.md) records the public-config projection guardrail. Retain this completed delivery for manual archive. [Image Token Delivery](Image_Token_Delivery.md) remains a separate proposed follow-on; its implementation has not started. Further Publish, test work, commit, push and deployment remain separately authorized actions.

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

The approved collision-safe main-image convention is recorded below. Thumbnail generation and row presentation match Works/Catalogue as specified below. An 800px input is an authoring expectation, not permission to silently resize an unsuitable input. Existing input/path handling remains; it does not introduce a separate thumbnail-replacement validation workflow.

### Source Metadata And Collection Rows

The canonical document source must record its thumbnail assignment. Collection generation projects a small `has_thumbnail` flag from that assignment; it does not infer intent by listing files. The list derives the thumbnail filename from `doc_id` and that collection's configured `thumbs` media base, without reading every document or requesting thumbnails for rows whose flag is false. Identical filenames under different collection owners remain separate assets.

Source metadata is optional boolean `thumbnail`, with `true` assigning the fixed document thumbnail and `false` or omission clearing its presentation. It records thumbnail presence, not a competing selection history or a rule that can prevent the next image from overwriting the thumbnail. Source editing and the existing committed-record/list update path carry the assignment. A generated flag alone is not authoring authority. Explicitly changing thumbnail metadata updates the next manifest and the retained caller through its existing owner.

The list matches Catalogue's existing thumbnail presentation: a reserved 64×64px image box, `object-fit: contain`, 6px rounded corners, vertically centred beside the title with the existing `--docs-viewer-space-3` gap. Use lazy loading, asynchronous decoding, decorative empty alt text and the existing shared image/title navigation control. Generalize the current Catalogue row styling for assigned document thumbnails rather than creating a separate Moments presentation. When any document in the full collection manifest has an assigned thumbnail, rows without one reserve an empty decorative 64×64px slot with no image request, aligning title offsets and minimum row heights across filtering and paging. Collections without assigned thumbnails retain compact text rows. An unavailable image preserves its slot and does not prevent navigation. Thumbnail presence does not change a collection's ordering, document identity, dates, readiness, Search membership or navigation behavior.

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

### Approved Naming Convention

| Choice | Proposed default | Reason or remaining decision |
| --- | --- | --- |
| Main-image filename | `<title-slug>-<doc_id>.<extension>`; numbered suffixes for additional images if needed | Approved on 2026-10-04. Retains a readable title and prevents different documents with duplicate title slugs from sharing a write target. |

## Deliverables

- [x] Generic document-based naming and **Create thumb** in the shared Add image workflow.
- [x] A Docs Viewer-owned raster thumbnail service using the current Works 96px crop/encoding recipe and validated media write contract.
- [x] Registered ordinary/collection `thumbs` media families with configured local/public paths and relevant lifecycle/reference support.
- [x] Canonical thumbnail assignments, projected presence metadata and shared Working/public collection-row rendering with Catalogue's existing 64px thumbnail presentation, including Concepts and Moments.
- [x] Preparation and publication reference support for thumbnails outside document body HTML.
- [x] Migrated existing display-image names, source references and thumbnails, with affected Working output reconciled.
- [x] Shared/public runtime projection and focused validation where those files change.
- [x] Shipped behavior documented in [Media And Asset Handling](Media_And_Asset_Handling.md), including generic naming, the `thumbs` role, source assignment and publication ownership.

## Process

1. Prepare a display-ready image outside Add image and place it in the workflow's supported input location.
2. Open an authorable document in Source, choose **Add image**, select the file and enter its alt text/presentation options.
3. Check **Create thumb** when this image should represent the document in a supported list. The thumbnail uses its fixed identity in the separate `thumbs` location and replaces any existing thumbnail without another prompt or validation workflow.
4. Await the media operation. On success, insert the image reference and thumbnail assignment into the editable source; report a failure at the point reached without claiming uncompleted effects or automatically undoing completed writes.
5. Save the source through the existing Save operation. Its confirmed metadata updates the retained list; the watcher owns generated-document refresh. Media writes have already completed and remain even if the source edit is discarded.
6. Use normal Publish when separately authorized to prepare and distribute the eligible documents and their referenced media. Review public presentation through site-preview before the separately authorized public release.

## Delivery Steps

### MIT 0 Readiness

- [x] Confirm broad source, shared insertion, collection-list, media registration and publication owners against the current product, including ordinary documents and Concepts.
- [x] Confirm the proposed main-image naming convention.
- [x] Carry the settled Works generation recipe, Catalogue row presentation, first-image migration, unconditional thumbnail replacement and manual orphan-retention rules into the implementation scope.
- [x] State the bounded code/migration change set and obtain implementation approval.

Verification budget: read-only owner/config inspection and source review. No prototype, migration writes, media inventory project or executable tests are needed merely to approve readiness.

Gate: stop if destination identity or source metadata cannot be represented through the existing owners, or if the work requires broader Studio/media architecture changes. Do not reopen the settled thumbnail-selection, replacement or orphan-retention policies.

Record: readiness completed on 2026-10-04 through read-only source/config review. Shared staged-media insertion, strict source Save and committed metadata, collection manifests/rows, workspace media registration and Preview reference capture can represent the outcome within existing owners. Concepts uses the same report as Moments. The user approved code, migration and naming; no wider Studio architecture or compatibility layer is required. Migration inventory remains an implementation step.

### MIT 1 Naming And Thumbnail Authoring

- [x] Implement the bounded Docs Viewer FFmpeg thumbnail operation with the specified Works parameters and generic document naming within existing Add image owners.
- [x] Register the `thumbs` managed media family and resolve ordinary/collection destinations through the existing configuration owner.
- [x] Carry the exact document/title context, proposed destination names and opt-in selection through validated requests.
- [x] Carry thumbnail presence through Source editing, replace existing thumbnail bytes unconditionally, and retain completed media writes on source cancellation.
- [x] Keep primary bytes unchanged and produce no srcset variants or Studio pipeline dependency.

Verification budget: targeted Python/JavaScript lint and direct image/file diagnostics for a justified existing input. These establish source validity and actual derivative dimensions/format, not broad workflow coverage. Record the exact targets, writes and cost before execution. User manual review covers dialog behavior; new test code requires its own approved specification.

Gate: the media result and source assignment agree, and failure reporting does not imply rollback or successful insertion after an incomplete operation.

Record: implemented on 2026-10-04. Exact current source and target validation own title/ID naming; the shared modal requests the optional derivative, and insertion sets canonical assignment in the dirty buffer. Targeted lint passed for 11 changed/new Python and 6 JavaScript source files. Actual migration exercised the naming/storage/FFmpeg owners for 36 existing raster inputs; direct diagnostics confirmed unchanged primary bytes and 96×96 WebP derivatives. Generic ordinary/Concepts insertion and cancellation/replacement interaction remain manual review.

### MIT 2 Collection And Publication Integration

- [x] Project thumbnail presence from canonical assignment and render assigned thumbnails through the shared collection-list owner using Catalogue's existing 64px presentation, including Concepts and Moments.
- [x] Include the registered `thumbs` family and assigned thumbnails in relevant inventory/reference reads, eligible document media capture and completed-snapshot distribution; inspect package/export role handling where affected.
- [x] Reuse committed-record reconciliation and existing cache/refresh behavior for changed assignments and replaced thumbnail bytes.
- [x] Project changed shared/public code with `bin/site-code-update`, inspect its tracked delta, then run its check and `bin/site-validate`.

Verification budget: focused lint, generated metadata/reference diagnostics and required static projection/validation. Inspect any exact existing test selection and its durable coverage before proposing a run; no suite or browser test is automatic. Working/public visual fit remains user manual review. Public transfer behavior is unverified until separately authorized publication.

Gate: ordinary and named-collection thumbnails resolve through their exact registered owners; list-only thumbnails are captured as media, excluded documents contribute no public thumbnails, and rows without thumbnails issue no speculative image requests. Missing images leave document navigation usable. Catalogue retains its own generated-media behavior.

Record: implemented on 2026-10-04. Working and public manifest projection, Preview reference capture, prepared-public distribution references and Docs Media references each identify the 36 assigned Moments thumbnails. These were read-only diagnostics over real generated payloads and configured owners, not a Publish or transfer. Package/static Export role handling is configuration-driven; body-only static exports gain no thumbnail presentation, and content packages retain their existing metadata boundary. Four represented shared JS/CSS files were projected and their exact delta reviewed; projection check and site validation passed. Implementation diagnostics did not Publish; the later user-run Publish and public boot correction are recorded at closeout. Working/public visual fit remains manual review.

### MIT 3 Existing Image And Source Migration

- [x] Resolve current Moment identities, image tokens in source order and `img`/`thumbs` destination names; use the first image for each thumbnail without a selection or existing-thumbnail validation pass.
- [x] Apply the approved migration through the same naming/generation owner, preserving primary bytes and authored content/metadata.
- [x] Update every affected active source reference and thumbnail assignment, then reconcile affected Working output through its owning build path.
- [x] Leave old identities, orphaned images, historical variants and public/held assets untouched; use reports for later manual reconciliation.

Verification budget: direct source/reference and file diagnostics, byte comparison for renamed primaries, generated thumbnail dimensions/format, and inspection of affected builder output. A targeted or complete Moments build may write replaceable Working output as justified above. Record actual selection, cost and effects before the migration; no new regression scripts or Search rebuild.

Gate: migrated display references use the new names, each document's first image supplies its thumbnail, dates/body layout remain intact, and original media files remain untouched. The reader uses no alias or fallback to old names.

Record: completed on 2026-10-04. Of 57 Moments, 36 each referenced one WebP (3,074,012 display bytes in total); 21 had no image. The shared naming/materialisation/thumbnail owners wrote 36 new display identities and 36 derivatives, then direct source patches changed only media identities and thumbnail assignment. Receipt-based diagnostics found no unexpected source delta, changed title/date or primary byte mismatch; old display files remain byte-identical. No watcher was running, so the justified complete Moments doc-only reconciliation rendered 57 documents, wrote 36 by-ID payloads and the management manifest, removed none and reported no warnings. Search, Preview and public document/media output were not rebuilt or published.

### MIT 4 Code Review

- [x] Review the final bounded code/config/source/generated delta for identity collisions, ownership drift, Studio coupling, duplicated dialogs, speculative thumbnail requests, missed publication references and compatibility residue.
- [x] Review migration results against source-order first-image selection and the no-deletion boundary; remove any added thumbnail-selection, replacement-confirmation or orphan-cleanup machinery.
- [x] Resolve findings and repeat only evidence affected by corrections.

Verification budget: source/diff review and already selected evidence; additional runs need a concrete remaining risk. Gate: review findings are resolved or explicitly scoped before closeout.

Record: bounded code/source/projection review completed on 2026-10-04 after selected evidence. Mermaid's proposed SVG destination is validated against its derived source identity; media apply reuses its validated insertion contract. The migration uses the existing prepared-media owner to meet basename validation. Canonical assignment and body-free public references stay explicit, Catalogue keeps its existing media policy, no compatibility aliases or deletion/rollback hooks were added, and missing artwork leaves navigation intact. Read-only reference diagnostics used the actual Preview/public configuration for distribution coverage. No unresolved code finding remains; browser interactions and public transfers remain evidence gaps.

### MIT 5 Closeout

- [x] Record user closeout acceptance and the scope of manual review, including remaining individual scenarios without recorded confirmation.
- [x] Update the durable media owner with the shipped convention and actual replacement/cancellation behavior.
- [x] Report exact focused evidence, media/source/generated changes and publication status, with orphaned files left for manual report-based reconciliation.
- [x] Present a retain-or-retire recommendation for this delivery document; do not delete it without approval.

Verification budget: bounded documentation/result review; no repeated builds or tests solely for closure. Gate: the complete Working outcome is delivered, its public projection/reference contract is ready, and publication status is stated separately.

Record: implementation and migration evidence are recorded above and the durable media owner is updated. User manual review on 2026-10-04 identified unequal title offsets and row heights for Moments without thumbnails; the shared row renderer now reserves an empty slot whenever the full collection contains assigned thumbnails. `bin/lint-js docs-viewer/runtime/js/shared/docs-collection-browsing.js docs-viewer/runtime/js/shared/docs-collection-report.js` passed. The two public projections were updated and their tracked delta reviewed; `bin/site-code-update --check`, `bin/site-validate` and scoped whitespace checks passed. Bounded review confirmed that empty slots reuse the existing 64px styling, remain decorative, create no image request and use the full manifest before filtering/paging.

The user's subsequent Publish exposed a pre-existing public configuration gap from the exact-document navigation change: canonical public config includes `document_url_template`, while the served `site/` copy omitted it. Publish owns document/media distribution and did not refresh this runtime configuration; the code projection inventory also omitted that file. The projection policy and inventory now allowlist only `docs-viewer-public-config.json`, keeping private defaults excluded. `bin/lint-python site-tools/site_code_update.py` passed; code projection changed only that public config, and its exact tracked delta was reviewed. Projection check and site validation passed with 102 projected files, and scoped whitespace checks passed. Direct HTTP reads from site-preview confirmed the exact template in served config and HTTP 200 for the default by-ID document. The user subsequently confirmed that the page loaded and Moments opened. The Development Checklist now records public browser config as part of the runtime projection guardrail.

Public list-item navigation then exposed a retained-list capture/restore assumption that a collection contribution always exists. Both optional callbacks now resolve through the existing null-safe function guard, preserving their receiver when present; public collections with no contribution use null caller-specific state. `bin/lint-js docs-viewer/runtime/js/shared/docs-collection-report.js` passed. Code projection changed only that shared module; its tracked delta was reviewed, and projection check, site validation and scoped whitespace checks passed. Direct HTTP reads confirm the guarded module is served and a representative Moments by-ID document returns HTTP 200. Bounded review covered capture and restoration with absent callbacks and preserved receiver behavior.

Closeout: the user accepted the delivery and authorized closure on 2026-10-04 after reviewing Working rows and the published site-preview, reporting the alignment/public-loading/navigation findings and accepting their fixes. Individual ordinary/Concepts insertion, cancellation, thumbnail replacement and Back scenarios were not separately confirmed, and remote transfer bytes were not independently audited. This acceptance closes the delivery without claiming those individual checks. Durable media documentation and the public-config guardrail are current. The status/documentation closeout uses bounded source review and the recorded implementation evidence; no new code review, rebuild or repeated executable verification is warranted. No tests or browser probes were authored, changed or run. The user performed Publish; Codex performed no further Publish, remote deletion, deployment, commit or push.

Closeout recommendation: retain this completed delivery for manual archive, with shipped media behavior in [Media And Asset Handling](Media_And_Asset_Handling.md) and the runtime projection guardrail in [Development Checklist](Development_Checklist.md). Retain [Image Token Delivery](Image_Token_Delivery.md) as the proposed next change. No planning documents or stored media are deleted by closeout.

## Follow On

The separately proposed [Image Token Delivery](Image_Token_Delivery.md) will make future Add image insertions store identity and presentation choices in a semantic token with builder-owned markup. Existing Markdown images and HTML figures will remain supported with no source-markup migration. This completed delivery satisfies its scheduling prerequisite; readiness and implementation approval for that refactor remain separate.

Thumbnail presentation in ordinary Index, Search, Recent or unrelated reports, srcset generation, automatic title-change media renaming, a general media pipeline, migration of other collections' existing images and historical variant/remote cleanup are outside this delivery. Generic Add image and shared collection-row support are within this delivery. Test authoring or changes follow [Test Contract Discipline](Test_Contract_Discipline.md) and [Testing](Testing.md), with coverage maintained outside this delivery.
