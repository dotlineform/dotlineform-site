---
draft: false
doc_id: d-20260928-203519-3b7793
title: Catalogue Image Token Metadata - Delivery
added_date: "2026-09-28 20:35:19"
last_updated: "2026-09-28 21:00:35"
summary: Proposed Work-derived alt text, optional title caption and metadata for Catalogue images across targeted, full and captured Preview builds, with action-level and Search follow-ons.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Image Token Metadata - Delivery

Proposed under [Planned Features](Planned_Features.md). This delivery makes one `catalogue:image:work` occurrence capable of selecting current generated Work title and the defined display metadata whenever that document is built. Targeted Working builds, full Working rebuilds and Publish's full Preview build use the same token renderer. The source stores the exact Work identity, selection choices, image presentation settings and optional authored summary; it stores no Work metadata, image alt text or caption. The resulting page still contains static rendered text. The existing browser image and Media View resolution remain separate and current-data driven.

## Requirements

- Keep the explicit five-digit `work_id` in every image token. Do not infer a Work from a document Subject, title, filename, collection or selected row. A Work image token needs no corresponding Catalogue document.
- Add explicit token choices for **Use Work title for caption** and **Include Work metadata**. These are source instructions for the document builder, not literal values such as `caption=title` or `summary=metadata`. An unselected choice omits that visible content; there is no authored caption or metadata field.
- In the new bound image form, derive `alt` from the current `work.title` on every document Build, whether or not the visible caption uses that title. Do not store a literal alt value or expose an editable alt field. Keep `summary` as the only optional authored text that Build never overwrites.
- Resolve selected values through one document-builder token path. Working builds read the exact configured generated `works/index/<work_id>.json` record; Publish's temporary Preview build receives the Catalogue JSON already captured for that Publish before rendering. Validate the record's Work identity and required title; fail the document build visibly if selected data is unavailable or invalid, without falling back to canonical Studio data or saved text. Omit absent optional metadata lines using the current Work-record formatting rules.
- Read generated Work data only for bound occurrences, including those that bind alt alone, and reuse a selected Work record within one build operation. A Catalogue Refresh makes generated JSON current; a Work Save alone does not rebuild documents or implicitly run Refresh Catalogue.
- Existing image tokens currently contain literal Work metadata, captions and alt text. Readiness must inventory those occurrences and agree a bounded one-time conversion to the bound form without ongoing per-Work manual edits. Identify any genuinely authored prose that is distinct from the metadata and title before conversion; do not preserve Work-derived literals as a static fallback or claim old tokens have become fresh until converted. Do not add a compatibility alias, or change Media View text links, Gallery tokens, Subject associations, document relationships or image URL resolution.

### Current Metadata Set

When **Include Work metadata** is selected, Build renders these lines in this order, separately from the authored `summary`:

| Line | Generated Work field and formatting |
| --- | --- |
| Year | `year_display`, when nonempty. |
| Medium | `medium_caption`, when nonempty. |
| Dimensions | Positive numeric `height_cm × width_cm × optional depth_cm` followed by ` cm`; omit the line without both height and width, and omit `.0` from whole numbers. |
| Catalogue number | `cat. <work_id>` using the token's exact five-digit identity. |

The bound form always uses `work.title` for image alt text. The separate Work-title checkbox controls whether that title also appears as the visible caption. “All metadata” means exactly the four lines above for this delivery. Adding another Work field later changes this defined set deliberately; it does not turn the token into a generic JSON-field renderer. The figure must support metadata or an authored summary with no visible caption. Keep the visible title in its existing bold style, render metadata in the same text style as summary content, and leave the same existing gap between metadata and any authored summary as there is currently between title caption and summary. Render selected metadata before the authored summary and escape both as text.

## Deliverables

- Canonical image-token parsing and serialization in Python Build and Source JavaScript for Work-title alt binding and explicit caption/metadata choices, with deterministic field order and validation. Store no literal Work-derived text. Preserve exact source ranges and unsupported-token handling; settle the existing literal-token transition at readiness.
- One shared document-rendering path that resolves selected fields before producing the existing image figure and semantic-token occurrence output in targeted Working, full Working and full Preview builds. Make captured Catalogue JSON available to the temporary Preview builder before it runs. Keep source unchanged and retain static HTML in generated by-ID payloads.
- **Add Catalogue Image** modal checkboxes for the two choices. Remove the manual alt, caption and metadata inputs; the optional authored summary remains editable and is labelled as static text. Keep Work selection, Use document subject, figure placement, fill width, current-media validation and guarded insertion, including when no visible caption is selected.
- Semantic token Info editing for the same choices and authored fields, preserving pending session values and the single Source Save boundary. Present the current Work title as the derived alt and optional caption without writing its literal value into source.
- A one-time conversion plan and, after its readiness decision, the bounded source transition needed for existing literal image tokens. Preserve exact Work identities, genuinely authored summaries and image presentation settings while replacing stored Work-derived alt, caption and metadata with selections. Avoid ongoing manual edits after Work data changes.
- A bounded durable update to [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) after the behavior is accepted. Full Rebuild and Publish acquire token support through their existing document-builder calls; this delivery does not change their controls, Search/Recents ownership or Catalogue Regenerate.

## Process

An author selects an exact Work in **Add Catalogue Image**, chooses whether the visible caption follows the Work title and whether the defined metadata lines appear, then optionally writes a static summary and sets the existing image presentation. The inserted token stores those choices but no Work-derived text. Source Save writes the token but does not fetch new Work metadata or rebuild Search. A targeted Working build updates that document's rendered figure; **Rebuild docs and Search** updates bound tokens in every rebuilt Working document; Publish rebuilds eligible documents in temporary storage from its captured Catalogue JSON. Each path derives alt from the current Work title and retains the authored summary. The visible caption may be absent even when metadata or summary is present. Work changes appear in a rendered document only after Catalogue Refresh and the relevant document Build. Opening the page performs no new caption or metadata request.

Existing literal tokens require the agreed one-time transition before they gain title-bound alt text; a later title change must not require editing a converted token. The browser continues to resolve the actual image and Media View presentation through the token's exact Work identity.

## Delivery Steps

### CIT-0 — Readiness

- [ ] Confirm Work-title alt binding without a literal alt field, the two visible caption/metadata checkbox choices, the static summary, the fixed metadata lines and captionless figure rendering against the current modal, Info view and builder.
- [ ] Inventory existing literal image tokens, distinguishing Work-derived text from genuinely authored summary prose; agree the one-time conversion and any exclusions before source changes.
- [ ] Confirm the new token grammar stores identity, selections, presentation settings and optional summary without literal Work-derived text or compatibility aliases, and that the shared renderer receives exact Working or captured Preview Work data.
- [ ] Confirm the review example and credible parser, captured-input, generated-output and UI risks. Do not change action controls or tests at this gate.

Gate: present the bounded grammar and authoring behavior for approval before implementation. Record: proposed on 2026-09-28; no implementation or executable verification has begun.

### CIT-1 — Token And Document Build

- [ ] Add Work-title alt binding and the explicit caption/metadata choices to canonical Python and JavaScript parsing/serialization.
- [ ] Resolve bound alt and selected fields through the shared builder for targeted and full Working builds; retain the bold title, summary-style metadata and existing inter-block gap before any authored summary, while retaining source identity and usage ranges.
- [ ] Supply Publish's already-captured Catalogue JSON to that same builder in the temporary Preview workspace before its full build. Do not reread live Working JSON during Preview rendering or add a second token resolver.
- [ ] Carry out the agreed bounded one-time source conversion without retargeting Works or replacing genuinely authored summaries and presentation settings. Make new tokens safe for the existing Search parser without indexing raw token syntax; dynamic Search content remains a follow-on.
- [ ] Record a proportional verification budget after owner inspection. Use focused existing parser/build evidence and changed-file lint only where justified; new or changed tests need their own agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: inspect a selected Working document's source, current alt and generated figure after a Work-title change, confirm the agreed literal-token conversion and confirm the captured Preview path uses the same renderer and captured JSON. Select proportionate evidence without running a live Publish or full collection regeneration solely for this gate. Record: not started.

### CIT-2 — Source Authoring And Manual Review

- [ ] Add the two choices to **Add Catalogue Image** and Semantic token Info, including clear static-summary wording, removal of manual Work-derived text inputs and captionless figure validation.
- [ ] Preserve exact Work selection, session-owned drafts, guarded insertion/replacement and one Save operation.
- [ ] Present insertion, editing, derived alt text, caption/metadata combinations and static summary for user manual review, including the bold title, summary-style metadata and gap before authored summary. UI feel and layout remain manual evidence unless a separate durable browser boundary is approved.

Gate: stop for user confirmation of the modal and rendered Working document. Record: not started.

### CIT-3 — Code Review

- [ ] Review the bounded grammar, provider reads, generated HTML, usage output, modal/Info behavior, failure path and one-time literal-token transition for duplicated ownership or hidden fallbacks.
- [ ] Resolve findings, run only affected focused checks, and update the durable token owner with accepted behavior.

Gate: present the reviewed result and remaining limits. Record: not started.

### CIT-4 — Closeout

- [ ] Confirm the complete token outcome across targeted Working, full Working and captured Preview builds, selected evidence, manual review and durable documentation transfer.
- [ ] State the action-level and data-owner follow-ons below without representing them as completed or silently expanding this delivery.

Gate: explicit user closeout. Record: open; no executable build, Publish, Catalogue Regenerate, Search rebuild, Git commit/push or public deployment belongs to this document-only planning action.

## Follow-on

| Owner or action | Follow-on decision or action-level review |
| --- | --- |
| **Catalogue Regenerate** | Make its Work-record generator emit the bound form, with Work-title alt and caption plus the full current metadata set selected for new and regenerated Catalogue documents. Keep front-matter document title updates under Regenerate. The existing **Only create new docs** checkbox and all-existing-doc replacement behavior remain unchanged until a separate Regenerate decision; a changed-only mode is not part of this token delivery. |
| **Rebuild docs and Search** | The existing action invokes the shared full Working builder, so it refreshes all bound tokens as part of this token delivery. Decide separately whether complete-build timing or the combined Search action needs a workflow change; Search is not a condition for refreshing rendered figures. |
| **Publish and Preview** | The existing action invokes the shared full builder on captured eligible source. This token delivery supplies its captured Catalogue JSON to that builder, so Preview renders bound tokens from the same bytes distributed with the snapshot. Decide separately whether the action needs any later workflow or performance change. Keep its current readiness exclusions, static output and saved Search/Recents copy behavior; Publish does not run Catalogue Refresh. |
| **Search** | Current Site Search indexes a token's saved title text, not resolved Work metadata, and excludes Catalogue collection documents; it includes eligible ordinary and Works documents. Decide separately whether selected Work titles should enter Search for included documents and whether any metadata lines belong there. Search remains Working-owned and Preview copies its saved bytes. If refreshed bound-title search is wanted before Publish, consider a Search-only operation when Working document projections are current, rather than requiring a full **Rebuild docs and Search** immediately before Publish's full document build. |

Any follow-on behavior changes require their own bounded requirements and approval. The token delivery does not change collection membership, Catalogue report metadata, document front-matter titles, Search coverage, Recents, Publish eligibility or public deployment.
