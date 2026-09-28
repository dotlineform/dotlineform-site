---
draft: false
doc_id: d-20260928-203519-3b7793
title: Catalogue Image Token Metadata - Delivery
added_date: "2026-09-28 20:35:19"
last_updated: "2026-09-28 22:28:02"
summary: Work-derived alt text, optional title caption and metadata for Catalogue images across targeted, full and captured Preview builds, with action-level and Search follow-ons.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Image Token Metadata - Delivery

Completed under [Planned Features](Planned_Features.md). This delivery makes one `catalogue:image:work` occurrence capable of selecting current generated Work title and the defined display metadata whenever that document is built. Targeted Working builds, full Working rebuilds and Publish's full Preview build use the same token renderer. The source stores the exact Work identity, selection choices, image presentation settings and optional authored summary; it stores no Work metadata, image alt text or caption. The resulting page still contains static rendered text. The existing browser image and Media View resolution remain separate and current-data driven.

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
- A one-time source transition for existing literal image tokens. The agreed conversion selects Work-title caption and full metadata for every existing occurrence, removes stored literal fields and preserves exact Work identities and image presentation settings. Existing Works and demonstration-token summaries may be overwritten as agreed. Avoid ongoing manual edits after Work data changes.
- Update Catalogue Regenerate's Work-record token producer to emit the same bound form, so later regeneration cannot restore literal tokens. Do not change its controls, front-matter behavior or replacement policy.
- A bounded durable update to [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) after the behavior is accepted. Full Rebuild and Publish acquire token support through their existing document-builder calls; this delivery does not change their controls or Search/Recents ownership.

## Process

An author selects an exact Work in **Add Catalogue Image**, chooses whether the visible caption follows the Work title and whether the defined metadata lines appear, then optionally writes a static summary and sets the existing image presentation. The inserted token stores those choices but no Work-derived text. Source Save writes the token but does not fetch new Work metadata or rebuild Search. A targeted Working build updates that document's rendered figure; **Rebuild docs and Search** updates bound tokens in every rebuilt Working document; Publish rebuilds eligible documents in temporary storage from its captured Catalogue JSON. Each path derives alt from the current Work title and retains the authored summary. The visible caption may be absent even when metadata or summary is present. Work changes appear in a rendered document only after Catalogue Refresh and the relevant document Build. Opening the page performs no new caption or metadata request.

Existing literal tokens received the agreed one-time transition to title-bound alt text; a later title change does not require editing a converted token. The browser continues to resolve the actual image and Media View presentation through the token's exact Work identity.

## Delivery Steps

### CIT-0 — Readiness

- [x] Confirm Work-title alt binding without a literal alt field, the two visible caption/metadata checkbox choices, the static summary, the fixed metadata lines and captionless figure rendering against the current modal, Info view and builder.
- [x] Inventory existing literal image tokens, distinguish Work-derived text from genuinely authored summary prose and agree the one-time conversion before source changes.
- [x] Confirm the new token grammar stores identity, selections, presentation settings and optional summary without literal Work-derived text or compatibility aliases, and that the shared renderer receives exact Working or captured Preview Work data.
- [x] Confirm the review example and credible parser, captured-input, generated-output and UI risks. Do not change action controls or tests at this gate.

Gate: present the bounded grammar and authoring behavior for approval before implementation. Record: approved on 2026-09-28. The agreed transition covers 4,638 active tokens across 4,634 Working source documents, plus three inert examples; it selects title caption and full metadata throughout while preserving Work IDs and presentation settings. Catalogue Regenerate's token producer joins CIT-1. Work `04620` provides a current-title review example. No action controls or tests changed at readiness.

### CIT-1 — Token And Document Build

- [x] Add Work-title alt binding and the explicit caption/metadata choices to canonical Python and JavaScript parsing/serialization.
- [x] Resolve bound alt and selected fields through the shared builder for targeted and full Working builds; retain the bold title, summary-style metadata and existing inter-block gap before any authored summary, while retaining source identity and usage ranges.
- [x] Supply Publish's already-captured Catalogue JSON to that same builder in the temporary Preview workspace before its full build. Do not reread live Working JSON during Preview rendering or add a second token resolver.
- [x] Carry out the agreed bounded one-time source conversion and update Catalogue Regenerate's token producer without retargeting Works or changing image presentation settings. Make new tokens safe for the existing Search parser without indexing raw token syntax; dynamic Search content remains a follow-on.
- [x] Record a proportional verification budget after owner inspection. Use focused existing parser/build evidence and changed-file lint only where justified; new or changed tests need their own agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: inspect a selected Working document's source, current alt and generated figure after a Work-title change, confirm the agreed literal-token conversion and confirm the captured Preview path uses the same renderer and captured JSON. Select proportionate evidence without running a live Publish or full collection regeneration solely for this gate. Record: ready for review. Work `04620` source stores choices while its watcher-built alt and caption use the current generated title; all 4,638 active source occurrences parse as bound tokens. Captured Preview wiring uses the same renderer and copied captured JSON by code inspection, without executing a full isolated Preview build. Focused Working dry runs, changed-file lint, site projection and validation, and `git diff --check` passed. Existing literal-token tests were not run or changed; test work needs a separate agreed specification. Source authoring controls remain CIT-2.

### CIT-2 — Source Authoring And Manual Review

- [x] Add the two choices to **Add Catalogue Image** and Semantic token Info, including clear static-summary wording, removal of manual Work-derived text inputs and captionless figure validation.
- [x] Preserve exact Work selection, session-owned drafts, guarded insertion/replacement and one Save operation.
- [x] Present insertion, editing, derived alt text, caption/metadata combinations and static summary for user manual review, including the bold title, summary-style metadata and gap before authored summary. UI feel and layout remain manual evidence unless a separate durable browser boundary is approved.

Gate: stop for user confirmation of the modal and rendered Working document. Record: user reported “tests passed” on 2026-09-28 after the metadata line-break correction; the exact manual cases were not itemized. **Add Catalogue Image** and token Info use Work-derived alt/title display, explicit title-caption and metadata choices, optional static summary, placement and fill width. Media View link editing and ordinary media controls retain their separate fields. The user's rendered `04620` screenshot had shown metadata collapsed onto one visual line; the renderer now emits explicit HTML line breaks. Working was regenerated for all 4,616 Catalogue documents, all 244 Works documents and the one ordinary image-token example, writing 4,615, 17 and one changed payloads respectively after the initial `04620` targeted rebuild. The resulting Catalogue, Works and ordinary payloads contain explicit line breaks. Changed-file Python and JavaScript lint and `git diff --check` passed; Codex did not perform browser interaction, permanent tests or live Publish.

### CIT-3 — Code Review

- [x] Review the bounded grammar, provider reads, generated HTML, usage output, modal/Info behavior, failure path and one-time literal-token transition for duplicated ownership or hidden fallbacks.
- [x] Resolve findings, run only affected focused checks, and update the durable token owner with accepted behavior.

Gate: present the reviewed result and remaining limits. Record: ready for review. The shared builder reads only exact generated Work records needed by image occurrences, caches each within a build, derives static escaped title and metadata text, and fails when required identity/title is invalid. Preview build code uses the already-captured Catalogue bytes. Python and JavaScript require the same bound fields; the source transition leaves no literal `alt=` image tokens in Working. Review removed a silent Info fallback when the token registry or target read fails and removed default-on fallback choices when hydrating valid image tokens. The current token, Source UI, Media View and collection architecture owners were updated; the completed Regenerate delivery identifies its literal-token examples as historical. Focused JavaScript lint and `git diff --check` passed after these changes. Existing legacy grammar tests were not changed or run; captured Preview has been inspected in code but not executed in isolation or through live Publish.

### CIT-4 — Closeout

- [x] Confirm the complete token outcome across targeted Working, full Working and captured Preview builds, selected evidence, manual review and durable documentation transfer.
- [x] State the action-level and data-owner follow-ons below without representing them as completed or silently expanding this delivery.

Gate: explicit user closeout. Record: complete on 2026-09-28 after the user reported passing tests and accepted the result in `site-preview`. Targeted Working and complete Catalogue/Works Working builds produced bound figures with explicit metadata line breaks. The current completed Preview manifest records `2026-09-28T21:24:02Z`; its `04620` by-ID payload and the tracked site payload contain the same bound title and metadata HTML, with the expected Preview/site `viewer_url` difference. Final `bin/site-code-update --check`, `bin/site-validate` and `git diff --check` passed. Codex did not invoke Publish, Catalogue Regenerate, Search rebuild, Git commit/push or public deployment. At closeout, 4,635 tracked `site/` paths are modified, including generated payloads; their Git disposition remains separate. The user-reported tests were not itemized, and no test files were changed by this delivery.

## Follow-on

| Owner or action | Follow-on decision or action-level review |
| --- | --- |
| **Catalogue Regenerate** | CIT-1 changes only the Work-record token producer to emit the bound form. Front-matter document title updates remain under Regenerate. The existing **Only create new docs** checkbox and all-existing-doc replacement behavior remain unchanged until a separate Regenerate decision; a changed-only mode is not part of this token delivery. |
| **Rebuild docs and Search** | The existing action invokes the shared full Working builder, so it refreshes all bound tokens as part of this token delivery. Decide separately whether complete-build timing or the combined Search action needs a workflow change; Search is not a condition for refreshing rendered figures. |
| **Publish and Preview** | The existing action invokes the shared full builder on captured eligible source. This token delivery supplies its captured Catalogue JSON to that builder, so Preview renders bound tokens from the same bytes distributed with the snapshot. Decide separately whether the action needs any later workflow or performance change. Keep its current readiness exclusions, static output and saved Search/Recents copy behavior; Publish does not run Catalogue Refresh. |
| **Search** | Bound image tokens have no saved title text, so the existing Search parser omits their syntax rather than resolving Work content. Search excludes Catalogue collection documents and includes eligible ordinary and Works documents. Decide separately whether selected Work titles should enter Search for included documents and whether any metadata lines belong there. Search remains Working-owned and Preview copies its saved bytes. If refreshed bound-title search is wanted before Publish, consider a Search-only operation when Working document projections are current, rather than requiring a full **Rebuild docs and Search** immediately before Publish's full document build. |

Any follow-on behavior changes require their own bounded requirements and approval. The token delivery does not change collection membership, Catalogue report metadata, document front-matter titles, Search coverage, Recents, Publish eligibility or public deployment.
