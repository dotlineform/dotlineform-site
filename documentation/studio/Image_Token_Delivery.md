---
draft: false
doc_id: d-20261004-123439-5c5dcd
title: Image Token Delivery
added_date: "2026-10-04 12:34:39"
last_updated: "2026-10-04 13:04:26"
summary: Make shared Add image insert an editable semantic image token, with builder-owned presentation and no migration of existing Markdown images or HTML figures.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Image Token Delivery

## Current And Next State

Proposed delivery under [Planned Features](Planned_Features.md). On 2026-10-04 the user approved documenting the semantic image-token direction and explicitly agreed that existing image markup can remain without migration. This authorizes the plan only. [Moments Images And Thumbnails Delivery](Moments_Images_And_Thumbnails_Delivery.md) was completed and accepted on 2026-10-04, satisfying the scheduling prerequisite. Next: complete read-only readiness and obtain approval for the bounded token implementation; no token implementation has started.

The current Add image operation inserts either a Markdown image containing a media reference or a literal HTML figure containing that reference. The proposed result stores image identity and authored presentation choices in one semantic token. The document builder owns the resulting HTML and classes, following the separation already used by Catalogue Image. Existing Markdown images and authored HTML remain supported document content.

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
[[image:docs/collections/moments/img/1-test-d-20261004-121258-0b8f84.jpg|alt=Collapsing&caption=Collapsing&placement=full&fill_width=true]]
```

This illustrates the identity/settings split; the exact grammar and field rules are not yet approved. A token must be self-contained and require no nested media token or stored HTML fragment.

### Shared Authoring And Thumbnail Boundary

- Use the existing shared Add image dialog and guarded Source adapter for ordinary documents and named collections with image-authoring capability. Reopen a supported occurrence with its current values, and replace only that captured occurrence after validation.
- Editing presentation on an existing token must reuse its media identity without requiring another file import. Selecting a new image continues through the existing awaited media operation and document-based naming owner.
- Keep Source insertion/editing in the dirty buffer and persist it through the existing single Save boundary. A modal does not save, rebuild, Publish or alter document dates independently.
- Retain **Create thumb** as an explicit, unchecked-by-default media operation. Do not store it in the body token or execute it during token rendering. The existing document `thumbnail` assignment, fixed thumbnail identity, replacement behavior and collection presentation retain their current owners.
- Do not add image selection history, automatic first-image thumbnail selection or a second image pipeline.

### Existing Content And Consumers

- Perform no source-markup migration, inventory-driven conversion or bulk replacement. Existing Markdown images and HTML figures continue through normal Markdown/HTML rendering with their current media references. They need no token alias or conversion to remain usable.
- Token editing applies to the new source form. Existing markup need not activate that editor; the author can replace an old image manually when useful.
- Integrate the new identity with Docs Media/reference collection, Preview capture and completed-snapshot distribution, static Export, document packages and read-only Review wherever those existing consumers handle body images. Keep source-oriented packages as source and rendered exports usable outside the viewer.
- Ensure Search's existing source-text extraction handles authored image text and does not index raw token syntax. This adds no automatic Search rebuild, membership or ranking change.
- Keep public reading static and read-only, using configured media roots. Add no public dependency on the management registry, local endpoints or Source editor.

## Deliverables

- [ ] One canonical image-token grammar and Python/browser parser/serializer integration through the existing semantic-token owners.
- [ ] Builder-owned image/figure rendering using the existing presentation and asset-resolution owners, with current Markdown/HTML behavior preserved.
- [ ] Shared Add image insertion and existing-token editing, preserving exact media identity, pending authored fields and guarded buffer replacement.
- [ ] Media/reference, publication, Export/package/Review and Search-text integration within their existing boundaries.
- [ ] Removal of obsolete Add image source-fragment production only where its callers are replaced; retain standard Markdown/HTML rendering without a custom legacy parser or compatibility alias.
- [ ] Shared/public runtime projection and focused validation for represented runtime files that change.
- [ ] A durable update to [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md), with a concise cross-reference from [Media And Asset Handling](Media_And_Asset_Handling.md) if its Add image source description changes.

## Process

1. Open an authorable document in Source and choose **Add image**. For a new occurrence, select a display-ready image and enter alt text and presentation choices.
2. Optionally select **Create thumb**, then await the existing media operation. Insert the serialized image token and any explicit thumbnail assignment into the dirty source buffer only after success.
3. To edit a new-format occurrence, activate it through the shared token-editing affordance. Hydrate the current fields, change presentation without importing another file, or explicitly select replacement media through the existing operation.
4. Save through the existing Source Save owner. The watcher renders the document with static image markup; Search remains under its separate rebuild owner.
5. Leave older Markdown images and HTML figures as they are, or replace individual images manually when desired. There is no required conversion step.
6. Use normal Build, Export, Review or separately authorized Publish through their existing owners. Token rendering itself performs no media writes.

## Delivery Steps

### IMT 0 Readiness

- [ ] Confirm broad semantic parsing, shared Source/modal, document rendering and media-consumer ownership against the completed thumbnail delivery.
- [ ] Settle the token identity grammar, field/default rules, uncaptioned presentation and intrinsic-dimension provenance, including supported vector behavior.
- [ ] Confirm that normal Markdown/HTML requires no migration or compatibility layer, and that the complete result fits existing storage and publication boundaries.
- [ ] State the bounded implementation and selected verification budget, then obtain implementation approval.

Verification budget: read-only owner/config inspection and source review. No prototype, media writes, source migration or executable tests are needed for this step.

Gate: do not start implementation until the preceding delivery is complete and the bounded change is approved. Stop to resolve any requirement for new media storage, render-time writes, token-driven thumbnail generation or a mandatory markup conversion.

Record: proposed plan created on 2026-10-04. Semantic-token direction and no-migration policy are agreed. Exact grammar, dimension handling, executable evidence and implementation approval remain open.

### IMT 1 Token Rendering And Shared Editing

- [ ] Implement canonical parsing/serialization and static rendering through existing focused owners.
- [ ] Change shared Add image to insert the token and hydrate supported existing occurrences for editing without unnecessary media writes.
- [ ] Preserve source-range/session guards, text escaping, exact media identity and the existing thumbnail operation boundary.
- [ ] Inspect active callers and remove obsolete producer paths within this bounded change.

Verification budget: explicit-path Python/JavaScript lint, source/diff review and proportionate existing builder diagnostics. Name the exact selected commands, expected writes and cost after owner inspection. User manual review covers modal interaction and visual presentation. Test authoring, changes and execution need a separate agreed selection/specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: new-format insertion and editing use one canonical source form, rendering produces the intended static presentation, and existing image markup remains supported without translation.

Record: not started.

### IMT 2 Consumer Integration And Projection

- [ ] Carry exact image references through media reads, publication capture/distribution and existing Export/package/Review paths.
- [ ] Integrate authored text with the existing Search extraction owner without changing rebuild scheduling.
- [ ] Reconcile generated document output through justified owning builds; use no source conversion or unrelated collection migration.
- [ ] Project represented runtime changes with `bin/site-code-update`, inspect the exact delta, then run `bin/site-code-update --check` and `bin/site-validate`.

Verification budget: focused lint, direct reference/generated-output diagnostics and required static projection/validation. Select any Working build and its credible blast radius before writing; no broad test suite, browser probe, Search rebuild or Publish is automatic.

Gate: each relevant consumer can discover or render the new image identity through its configured owner; public readers acquire no management dependency. Existing thumbnail references and older body images retain their current behavior.

Record: not started.

### IMT 3 Code Review

- [ ] Review the bounded production/config/generated diff for duplicated grammar, media-owner drift, unsafe authored text, hidden media writes, stale-range mutation, missed consumer references, dead producers and compatibility residue.
- [ ] Confirm that the no-migration boundary and independent thumbnail assignment remain intact.
- [ ] Resolve findings and repeat only evidence affected by corrections.

Verification budget: bounded source/diff review and accepted implementation evidence. Gate: findings are resolved or explicitly scoped before closeout.

Record: not started.

### IMT 4 Closeout

- [ ] Record user manual review of new insertion, existing-token editing, caption/layout choices and representative older Markdown/HTML images.
- [ ] Update the durable semantic-token owner with the accepted grammar, rendering and extension boundaries.
- [ ] Report exact selected evidence and remaining omissions, keeping tests, Publish, commit, push and deployment separately scoped.
- [ ] Present the delivery's retain-or-retire recommendation; do not delete it without approval.

Verification budget: bounded documentation/result review using accepted evidence. Gate: the complete token outcome works, the durable owner is current and existing markup needs no conversion.

Record: not started. Retain this proposed delivery for later readiness and implementation.

## Follow On

Bulk conversion of existing image markup, changes to Catalogue's derived text, thumbnail policy, primary rendition/srcset generation, general media-pipeline work and additional image-token families are outside this delivery. Any later test work requires its own agreed purpose, coverage, cost and acceptance, with a durable coverage record outside this delivery.
