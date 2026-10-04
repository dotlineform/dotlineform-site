---
draft: false
doc_id: d-20261004-123439-5c5dcd
title: Image Token Delivery
added_date: "2026-10-04 12:34:39"
last_updated: "2026-10-04 15:02:10"
summary: Make shared Add image insert an editable semantic image token, with builder-owned presentation and no migration of existing Markdown images or HTML figures.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Image Token Delivery

## Current And Next State

Completed under [Planned Features](Planned_Features.md) and accepted for closeout by the user on 2026-10-04. IMT 0–4 and the approved source-filename revision are complete: canonical parsing/serialization, static rendering, shared insertion/editing, consumer integration, selected diagnostics and bounded code review are delivered. Search excludes the new token entirely; the broader policy across existing image forms remains a follow-on. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md#docs-owned-images) owns the shipped source/rendering contract and [Media And Asset Handling](Media_And_Asset_Handling.md#import-materialization) owns source naming and replacement. Retain this completed delivery for manual archive. Individual manual scenarios were not separately confirmed; the recorded evidence limits remain. Tests, Search rebuild, Publish, commit, push and deployment have not run.

Shared Add image now stores image identity and authored presentation choices in one semantic token. The document builder owns the resulting HTML and classes, following the separation already used by Catalogue Image. Existing Markdown images and authored HTML remain supported document content without conversion.

The user approved a source-filename revision on 2026-10-04 after accepting shared-asset and normalization-collision consequences. New Add image operations use the normalized original source basename, with same-name reuse or confirmed replacement and no title/ID prefix or allocated suffix. Implementation, focused lint and bounded code review are complete, and the user subsequently accepted the delivery and authorized closure. Existing media and thumbnail identities are unchanged.

## Requirements

Deliver one complete outcome: shared **Add image** inserts a semantic image token that the shared Source editor can reopen and edit, and all existing document build and media consumers handle that token through their current owners.

### Source And Presentation

- Store the exact configured logical media identity, required authored alt text, optional authored caption and summary, placement and fill-width choice in the token. Preserve the selected media owner; do not infer an image from the document title, Subject or thumbnail.
- Keep caption and summary as literal authored text. Catalogue Image retains its separate Work-derived alt, caption and metadata choices; an ordinary image token gains no Catalogue lookup or Work binding.
- Use deterministic serialization, canonical text encoding, allowlisted fields and consistent Python/browser parsing. Preserve source ranges and the existing inactive code/comment boundaries. Escape authored text in generated markup and retain path/owner validation.
- Produce static image/figure markup during document Build through a focused renderer. Reuse the existing figure presentation and asset URL resolution. CSS classes and HTML structure belong to rendering, not authored source.
- Keep the current captioned and uncaptioned presentation choices, including full, left and right placement and natural/fill width where applicable. Settle the exact field defaults and intrinsic-dimension provenance at readiness without introducing primary-image resizing or browser media generation.
- Keep source directly editable. Define unsupported or malformed token handling consistently with the existing semantic-token owner; do not silently choose another asset or insert default presentation values over an existing occurrence.

An illustrative source form is:

```text
[[image:docs/collections/moments/img/collapsing.jpg|alt=Collapsing&caption=Collapsing&placement=full&fill_width=true]]
```

The accepted grammar separates logical identity from authored settings. A token is self-contained and requires no nested media token or stored HTML fragment.

### Shared Authoring And Thumbnail Boundary

- Use the existing shared Add image dialog and guarded Source adapter for ordinary documents and named collections with image-authoring capability. Reopen a supported occurrence with its current values, and replace only that captured occurrence after validation.
- Editing presentation on an existing token must reuse its media identity without requiring another file import. Selecting a new image continues through the existing awaited media operation and source-filename naming owner.
- Normalize each selected original source basename to a lowercase websafe stem and lowercase supported extension. Do not add a document title, `doc_id` or collision suffix. Reuse matching stored bytes; changed bytes at the same identity require the existing Replace confirmation. Replacing an asset affects every reference in its configured owner, and different source names can normalize to that same identity. Keep existing stored names and fixed document-thumbnail identities without migration.
- Keep Source insertion/editing in the dirty buffer and persist it through the existing single Save boundary. A modal does not save, rebuild, Publish or alter document dates independently.
- Retain **Create thumb** as an explicit, unchecked-by-default media operation. Do not store it in the body token or execute it during token rendering. The existing document `thumbnail` assignment, fixed thumbnail identity, replacement behavior and collection presentation retain their current owners.
- Do not add image selection history, automatic first-image thumbnail selection or a second image pipeline.

### Existing Content And Consumers

- Perform no source-markup migration, inventory-driven conversion or bulk replacement. Existing Markdown images and HTML figures continue through normal Markdown/HTML rendering with their current media references. They need no token alias or conversion to remain usable.
- Token editing applies to the new source form. Existing markup need not activate that editor; the author can replace an old image manually when useful.
- Integrate the new identity with Docs Media/reference collection, Preview capture and completed-snapshot distribution, static Export, document packages and read-only Review wherever those existing consumers handle body images. Keep source-oriented packages as source and rendered exports usable outside the viewer.
- Exclude each active, valid new image token entirely from Search's source-text extraction, including alt, caption, image summary, media identity and structural syntax. Review Search policy for existing image forms separately. This adds no Search field, automatic Search rebuild, membership or ranking change.
- Keep public reading static and read-only, using configured media roots. Add no public dependency on the management registry, local endpoints or Source editor.

### Search Boundary

The user clarified on 2026-10-04 that image alt, caption and summary should not be searchable. The delivered builder change is limited to excluding the new semantic image token entirely. The saved Search index has not been rebuilt. [Docs Search Index](Docs_Search_Index.md#source-boundary) owns the current behavior; the broader review of existing image forms is a separate follow-on.

The existing `searchable_markdown` method in `docs-viewer/build/build_search.py` projects semantic occurrences before the shared Markdown search extractor runs. It now replaces each active, valid image occurrence with whitespace rather than text from its fields. Whitespace preserves separation between surrounding words. The token contributes no searchable alt, caption, image summary, filename, path, field names or layout values. This requires no asset lookup or image-byte analysis. Inline/fenced examples keep their existing code-text treatment rather than becoming active image occurrences; unsupported/malformed forms keep the existing literal-source treatment.

Existing Markdown image alt and visible HTML figure text currently contribute searchable text. Their extraction and Catalogue token extraction remain unchanged in this delivery, so old and new image forms will have different Search treatment until the separately scoped review resolves that policy. Exclusion is confined to the new token occurrence; the same words in ordinary document prose or front-matter summary remain searchable.

The saved index schema, configured Search fields, selected documents/collections, query behavior and ranking stay unchanged. Saving or building a document still does not rebuild Search. Exclusion takes effect in the saved index only on the next explicitly requested complete Working Search rebuild; Publish continues copying the existing index. Implementation approval does not authorize that rebuild or Publish. Verification of actual postings requires a separately agreed Search build/diagnostic selection; the current lint and source-review budget does not establish generated-index correctness.

## Deliverables

- [x] One canonical image-token grammar and Python/browser parser/serializer integration through the existing semantic-token owners.
- [x] Builder-owned image/figure rendering using the existing presentation and asset-resolution owners, with current Markdown/HTML behavior preserved.
- [x] Shared Add image insertion and existing-token editing, preserving exact media identity, pending authored fields and guarded buffer replacement.
- [x] Source-filename image identity with same-name reuse or confirmed replacement, replacing title/ID naming and numbered allocation without media migration.
- [x] Media/reference, publication and Export/package/Review integration, plus exclusion of the new image token from Search within its existing extraction boundary.
- [x] Removal of obsolete Add image source-fragment production only where its callers are replaced; retain standard Markdown/HTML rendering without a custom legacy parser or compatibility alias.
- [x] Confirm represented shared/public runtime projection is current; no represented runtime files changed.
- [x] Update [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md), the Add image description in [Media And Asset Handling](Media_And_Asset_Handling.md) and the changed source-extraction boundary in [Docs Search Index](Docs_Search_Index.md).

## Process

1. Open an authorable document in Source and choose **Add image**. For a new occurrence, select a display-ready image and enter alt text and presentation choices.
2. Optionally select **Create thumb**, then await the existing media operation. Insert the serialized image token and any explicit thumbnail assignment into the dirty source buffer only after success.
3. To edit a new-format occurrence, activate it through the shared token-editing affordance. Hydrate the current fields, change presentation without importing another file, or explicitly select replacement media through the existing operation.
4. Save through the existing Source Save owner. The watcher renders the document with static image markup; Search remains under its separate rebuild owner.
5. Leave older Markdown images and HTML figures as they are, or replace individual images manually when desired. There is no required conversion step.
6. Use normal Build, Export, Review or separately authorized Publish through their existing owners. Token rendering itself performs no media writes.

## Delivery Steps

### IMT 0 Readiness

- [x] Confirm broad semantic parsing, shared Source/modal, document rendering and media-consumer ownership against the completed thumbnail delivery.
- [x] Approve the proposed token identity grammar, field/default rules, uncaptioned presentation and intrinsic-dimension provenance, including supported vector behavior.
- [x] Confirm that normal Markdown/HTML requires no migration or compatibility layer, and that the complete result fits existing storage and publication boundaries.
- [x] State the bounded implementation and selected verification budget, then obtain implementation approval.

Verification budget: read-only owner/config inspection and source review. No prototype, media writes, source migration or executable tests are needed for this step.

Gate: do not start implementation until the preceding delivery is complete and the bounded change is approved. Stop to resolve any requirement for new media storage, render-time writes, token-driven thumbnail generation or a mandatory markup conversion.

Record: readiness completed and revised implementation approved on 2026-10-04. Semantic parsing/content rendering, the shared Source adapter/modal and existing media/consumer owners cover the complete result. The accepted Search scope omits active, valid new image tokens entirely and leaves existing image forms for separate review. Intrinsic sizing remains browser-owned from raster/SVG bytes. No new media storage, migration, compatibility layer or render-time writes are required.

#### Accepted Rules And Bounded Implementation

Use `[[image:<logical-media-path>|alt=<encoded-text>&caption=<encoded-text>&summary=<encoded-text>&placement=full&fill_width=true]]`. The identity is the exact configured ordinary or collection `img`/`svg` logical path, with confined relative asset identity and canonical encoding for reserved characters. It stores neither a nested media token nor a local/public URL. Sanitized SVG and the existing persistent Mermaid SVG output use the same image form; editable Mermaid source retains its current media owner.

Field order is `alt`, optional `caption`, optional `summary`, `placement`, `fill_width`. Required alt is literal single-line text; caption is optional literal single-line text; summary is optional literal multiline text. Reuse the semantic owner's canonical UTF-8 percent encoding and text normalization, omit empty optional fields, reject duplicate or unknown fields, and require explicit placement (`full`, `left`, `right`) and boolean fill width. Malformed or unsupported forms remain literal source and do not activate editing; a supported token with an invalid configured asset owner fails rendering rather than selecting another asset. Preserve inactive code/comment boundaries and captured source ranges.

For new insertion, retain the current suggested alt/caption, caption enabled, full-column placement, fill width enabled and empty summary defaults. Layout choices remain available when caption is disabled; caption and summary are independently optional. Hydrate existing occurrences from their exact stored values without applying insertion defaults. Render through the existing figure classes, omitting `figcaption` when both authored text fields are empty. Escape authored text and use the owning asset resolver. Natural raster dimensions come from the display bytes and SVG sizing comes from the sanitized SVG's intrinsic dimensions/viewBox in the browser; the new token has no authored dimension fields or Build-time dimension scan. Existing Markdown/media dimension attributes remain supported unchanged.

Implement the complete parser/serializer, static renderer, shared insertion and reopening/editing, source/reference discovery, package/Review integration and Search exclusion for the new token. Presentation-only editing reuses the current identity and performs no media operation. Explicit replacement selection uses the existing awaited Add image operation. Create thumb remains unchecked by default, belongs only to an explicitly selected raster-media operation, and is absent from the token. Remove replaced Add image fragment producers after caller inspection; normal Markdown/HTML support remains with its current renderer. Update the durable semantic architecture and the changed Add image description in the media owner.

Selected implementation evidence: `bin/lint-python <changed-production-paths>`, `bin/lint-js <changed-runtime-paths>` and `git diff --check`, followed by bounded source/diff review. These address syntax, maintained lint rules, whitespace, owner integration and escaping/range/write boundaries without new test code. If represented shared/public runtime files change, run `bin/site-code-update`, inspect its tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`; projection writes only its configured repository destinations. Expected lint/projection/validation cost is seconds to a few minutes, with actual tool/runtime cost not yet measured. No test execution, browser automation, Working Build, media write, Search rebuild, Publish, commit, push or deployment is selected at readiness. Select any necessary existing builder diagnostic and its output boundary during implementation before running it; manual modal and visual review remain IMT 4 gates.

### IMT 1 Token Rendering And Shared Editing

- [x] Implement canonical parsing/serialization and static rendering through existing focused owners.
- [x] Change shared Add image to insert the token and hydrate supported existing occurrences for editing without unnecessary media writes.
- [x] Preserve source-range/session guards, text escaping, exact media identity and the existing thumbnail operation boundary.
- [x] Inspect active callers and remove obsolete producer paths within this bounded change.

Verification budget: explicit-path Python/JavaScript lint, source/diff review and proportionate existing builder diagnostics. Name the exact selected commands, expected writes and cost after owner inspection. User manual review covers modal interaction and visual presentation. Test authoring, changes and execution need a separate agreed selection/specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: new-format insertion and editing use one canonical source form, rendering produces the intended static presentation, and existing image markup remains supported without translation.

Record: implemented on 2026-10-04. New image grammar uses shared canonical encoding and active-source boundaries, with builder-owned static figures and current-owner URL resolution. Add image reopens supported occurrences, preserves pending fields through replacement/folder selection and uses guarded dirty-buffer replacement; presentation-only editing performs no media operation. Replaced Markdown/HTML image producers were removed, with normal Markdown/HTML rendering retained. Explicit-path Python/JavaScript lint passed; modal interaction and new-token rendered presentation remain user manual gates.

### IMT 1a Source Filename Identity Revision

- [x] Normalize the original source basename and extension for Add image without title/ID naming or numbered allocation; remove the obsolete allocator rather than retaining an alias.
- [x] Retain exact target/source validation, unchanged-byte reuse, changed-byte Replace confirmation, SVG review and independently selected thumbnail creation.
- [x] Complete explicit-path Python lint and whitespace checks, then bounded code review of naming, preview/apply destination agreement, media reuse/replacement and thumbnail separation.

Verification budget: `bin/lint-python docs-viewer/services/docs_staged_media_service.py docs-viewer/services/docs_document_images.py`, `git diff --check` and bounded source/diff review. These check the changed Python owners, whitespace and existing collision/write integration without executing media writes. Expected cost is seconds, with no new tests, browser checks, Build, Search rebuild, Publish or Git action. Existing browser confirmation and public runtime files are unchanged; prior projection evidence remains applicable.

Record: the naming revision was approved and implemented on 2026-10-04. Naming now uses only the source stem and extension; Mermaid independently skips stored source/SVG writes whose bytes already match. The prior title/ID allocator has been removed with no remaining callers or alias. Explicit-path lint passed for both changed Python owners and `git diff --check` passed. Bounded code review confirmed exact target/source validation, normalized preview/apply destination agreement, unchanged-byte reuse, retained Replace confirmation and separate thumbnail identity/write behavior; no unresolved production finding remains. Existing media references and `<doc_id>-thumb.webp` remain intact. No media operation or new executable behavior check ran, so same-name reimport interaction remains a manual review gate. Browser/public runtime files are unchanged by this revision, and the earlier projection evidence is retained.

### IMT 2 Consumer Integration And Projection

- [x] Carry exact image references through media reads, publication capture/distribution and existing Export/package/Review paths.
- [x] Exclude valid active new image tokens and all their fields from Search, retaining existing image-form extraction, fields, membership, ranking and rebuild scheduling as specified above.
- [x] Inspect whether generated output needs reconciliation; no canonical Working source changed and no generated write was selected.
- [x] Confirm represented runtime files remain unchanged with `bin/site-code-update --check`; no projection write or consequent `bin/site-validate` run is required.

Verification budget: focused lint, direct reference/generated-output diagnostics and required static projection/validation. Select any Working build and its credible blast radius before writing; no broad test suite, browser probe, Search rebuild or Publish is automatic.

Gate: each relevant media consumer can discover or render the new image identity through its configured owner, and Search excludes active, valid new image tokens. Public readers acquire no management dependency. Existing thumbnail references and older body images retain their current behavior.

Record: consumer integration completed on 2026-10-04. Docs Media uses the shared semantic parser on body source and excludes image-token syntax from its older path scans. Review resolves decoded identities against its existing asset inventory; source packages retain source and rendered package transforms, Preview and static Export reuse their existing rendering/URL collectors. Search excludes the new family. Service import diagnostics passed. The read-only targeted command `build_docs.py --stage working --collection moments --only-doc-ids d-20261004-121258-0b8f84 --skip-media-builds --diagnostics` scanned/rendered one existing source, reported zero warnings and zero proposed payload/manifest changes; it does not verify new-token output. `bin/site-code-update --check` reported 102 unchanged files and no projection delta. No Working/media write, Search rebuild, Publish or transfer ran; consumer execution with new tokens remains unverified beyond source review.

### IMT 3 Code Review

- [x] Review the bounded production/config/generated diff for duplicated grammar, media-owner drift, unsafe authored text, hidden media writes, stale-range mutation, missed consumer references, dead producers and compatibility residue.
- [x] Confirm that the no-migration boundary and independent thumbnail assignment remain intact.
- [x] Resolve findings and repeat only evidence affected by corrections.

Verification budget: bounded source/diff review and accepted implementation evidence. Gate: findings are resolved or explicitly scoped before closeout.

Record: bounded code review completed on 2026-10-04. Resolved duplicated Python percent encoding, renamed the shared semantic-fragment restoration owner without aliases, kept Catalogue audit lookup confined to its family, confined new source references to body occurrences through the shared parser, and preserved current-owner or inventoried Review resolution. Explicit-path lint covered 11 Python and five JavaScript production files; module import diagnostics, the targeted older-image builder diagnostic and `git diff --check` passed. No compatibility layer was introduced. The retained `test_docs_staged_media_fragments.py` still targets removed source-fragment producers; it was not changed or run and requires separate test work. Browser/modal behavior, new-token generated output, actual Search postings and lifecycle/media transfers have no executable acceptance evidence from this delivery.

### IMT 4 Closeout

- [x] Record user acceptance and explicit closeout authorization, distinguishing that acceptance from individually confirmed manual scenarios.
- [x] Update the durable semantic-token owner with the accepted grammar, rendering and extension boundaries.
- [x] Report exact selected evidence and remaining omissions, keeping tests, Publish, commit, push and deployment separately scoped.
- [x] Present the delivery's retain-or-retire recommendation; do not delete it without approval.

Verification budget: bounded documentation/result review using accepted evidence. Gate: the delivered token outcome is accepted, the durable owners are current and existing markup needs no conversion. New code review is not applicable to this status-only closeout; reuse the completed implementation reviews and checks.

Record: the user accepted the delivered result and explicitly authorized closure on 2026-10-04 after the source-filename revision. No individual results were supplied for insertion, same-name reuse/replacement, token editing, caption/layout choices, optional thumbnails or older markup, so closeout records acceptance without claiming those checks passed. No browser automation was run. The durable semantic, media and Search owners describe the delivered behavior. Bounded documentation review confirms the completed state and retain-for-manual-archive recommendation; implementation evidence is reused without repeated lint, rebuilds or media operations. Tests, Search rebuild, Publish, commit, push and deployment remain separately scoped.

## Follow On

Review Search's image-content policy across semantic image tokens, existing Markdown images, HTML figures and Catalogue images. Use the user's preference to exclude image alt, caption and summary as the proposed policy; establish how the extractor identifies image-owned text while retaining ordinary prose and document front-matter summary. Resolve the temporary difference between existing markup and new tokens through Search's owning extraction boundary, without requiring source-markup conversion. Any resulting code changes, verification selection and complete Search rebuild need their own bounded scope and approval.

Bulk conversion of existing image markup, changes to Catalogue's derived text, thumbnail policy, primary rendition/srcset generation, general media-pipeline work and additional image-token families are outside this delivery. Any later test work requires its own agreed purpose, coverage, cost and acceptance, with a durable coverage record outside this delivery.
