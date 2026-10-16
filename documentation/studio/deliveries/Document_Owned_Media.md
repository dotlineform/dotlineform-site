---
draft: false
doc_id: d-20261016-113806-43f3db
title: Document Owned Media
added_date: "2026-10-16 11:38:06"
last_updated: "2026-10-16"
summary: Complete and user-accepted on 2026-10-16 after Draft media additions/removals, content reuse, Draft deletion and publication; in-memory media comparison and one canonical exclusion-policy input.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Document Owned Media

This completed delivery is parented to [Planned Features](../Planned_Features.md). It extends [Incremental Document Publish](Incremental_Document_Publish.md) and the [Working/Preview media boundary](Document_Media_Working_And_Preview.md) with one result: each authored document owns its media, and Source Save completes its selected Working media writes/removals and publication handoff before returning the fresh document.

## Completion And Acceptance

Status: complete and user-accepted on 2026-10-16. DOM.0–DOM.10 are complete. The user accepted the normal-use result and requested closeout after publishing media removals from a Draft, adding media to that Draft, copying its content/media references into a publishable document and deleting the Draft document.

Source Save owns pending-media processing, source persistence, exact generation and fresh display. Save and replacement Import compare loaded before/after references in memory; no media baseline file or by-ID media list remains. Index generation reads current `unpublishable.json` once per operation without storing a policy copy. The diagram pipeline and obsolete repository references are retired; documentation diagrams remain.

The approved migration completed 245 source rewrites/exact generated documents and 342 verified body-media copies while retaining originals and 37 flat thumbnails. The separate migration Publish completed 41 eligible document writes, 204 Draft withdrawals and 85 media transfers. The user's subsequent workflow supplies representative real Save/removal/publication acceptance beyond that migration.

The reported live-image failure was traced to deploying the earlier committed document while the latest published `site/` JSON remained uncommitted. Exact checks found the new image objects in R2 matching Working bytes, six old referenced objects absent after their removals, and a representative new public image returning HTTP 200. A cache-bypassing live document request matched the old committed payload. The user recognised the missed commit and then accepted the workflow; no new application defect or delivery gate remained. Publish, commit/push and manual deployment retain their separate ownership.

Acceptance is based on that reported workflow and the recorded implementation/static/read-only evidence. Same-name isolation, discard/before-first-Save removal, repeated occurrences, same-identity replacement, thumbnail independence, replacement Import and injected failure variants were not individually demonstrated. These are disclosed evidence limits for continued normal use, not open delivery gates. Whole-document media cleanup, old flat files and partial-write orphans remain manual and optional.

Durable ownership is in [Media And Asset Handling](../Media_And_Asset_Handling.md#saved-ownership-and-exact-removals), [Builder](../Builder.md#publish-preparation), [Source Editor Endpoints](../Source_Editor_Endpoints.md) and [Publication Media](../data_model/Publication_Media.md). This completed delivery and its [Working Notes](Document_Owned_Media_Working_Notes.md) are retained for evidence lookup pending manual archive; neither is an active handoff.

## Requirements

### Document Ownership And Paths

- Keep the existing configured workspace/collection and media-type roots. Store authored body media under `<doc_id>/<readable-filename>` within its type. The document ID is an explicit path segment, not a filename prefix; no additional literal `by-id/` segment is needed. Thumbnails retain their fixed flat identity under `thumbs/` as specified below.
- Example Working paths, relative to the configured Docs workspace root, are `working/assets/media/workspace/img/<doc_id>/photo.webp` and `working/assets/media/collections/concepts/img/<doc_id>/photo.webp`. Preview and configured public destinations retain the same type-relative identity, `<doc_id>/photo.webp`. Source image paths correspondingly become `docs/img/<doc_id>/photo.webp` or `docs/collections/concepts/img/<doc_id>/photo.webp` inside their normal tokens.
- Cover authored document images, SVGs, attachments, HTML media and their owned companions. Keep the single thumbnail per document flat as `thumbs/<doc_id>-thumb.webp`, preserving its independent front-matter assignment and exact document ownership; no document folder is required for this fixed identity. adapt their paths only where required by the ownership contract.
- Preserve existing conversion, sanitizer rules and presentation policies while simplifying their author interaction. Different documents can use the same readable filename independently. Within one document, carry an explicit Edit replacement choice through Save without a second Replace dialog. An unexpected conflict from a new addition or competing pending files is reported for the author to resolve; do not silently overwrite, allocate filenames or introduce cross-document deduplication.
- Native intake and import/materialisation derive destinations from the exact resolved document target. Import/export, return import, generation, local reads, reports and publication carry the complete relative identity instead of flattening it to a basename. Reuse prepared bytes and resolved owners through those operations.
- Each document owns its media independently. Reuse in another document creates a copy in that document's namespace through its authoring/import operation. Handwritten references into another document's namespace remain an authoring concern; ordinary Save, generation and Publish do not scan other documents to establish sharing or protect such references from deletion.
- Catalogue Work images/downloads, Catalogue media tokens, external media URLs, the native app and the Processing project's storage/build lifecycle remain outside this change. Apply the document-media contract to whatever named collections the Docs workspace explicitly configures, without changing their separate project owners.

### Media Writes On Save

- Add Image/Add file retains the selected browser `File` and the required insertion/thumbnail choices in the mounted Source session. Token insertion and presentation-only edits make no permanent media writes. Do not add persistent server staging, upload sessions or a media queue independent of the document draft.
- The browser owns the draft, pending-file membership, authoring feedback and replacement choices. Preserve pending files through ordinary editing/Undo; select the pending files still used by the final buffer and thumbnail assignment when Save runs. Pending replacement bytes or a thumbnail choice make the session dirty even when its text is unchanged.
- Python owns required upload parsing/limits, canonical destination construction, media decoding/conversion/sanitization, confined writes, source persistence, exact generation and publication handoff. Establish candidate validity once using the saved inputs and selected pending media; a new file must not have to exist permanently before that candidate can be accepted.
- Save prepares selected files once and carries explicit replacement intent from the editor. Keep filename/existing-byte checks limited to the selected document identities and reuse unchanged bytes where useful. Sanitize selected SVG at its processing owner automatically; report sanitizer changes through the existing Save result without a blocking review/confirmation dialog. Invalid SVG or a processing failure stops Save normally. Do not add a sanitizer override, second upload/processing pass for confirmation or a new review workflow.
- A write-free insertion preparation call is acceptable only for a concrete required identity/authoring result; it must not silently store media or create a second validation owner. Carry known choices and completed preparation forward rather than repeating processing without an operational reason.
- One awaited Save completes the selected media writes, canonical source persistence, exact document/Links generation, queue effects and fresh display. It does not run Search, Publish, complete media inventories or unrelated registered media production. Media processing is limited to the supplied pending files and their explicitly requested outputs.
- If a file or combined pending-media request exceeds the size limit, report the exceeded limit before media processing/persistence and retain the draft and pending Files. The author resolves the input. Add no automatic splitting, subset saves, batch coordinator, partial uploads or extra authoring workflow; keep request-size enforcement at the existing upload boundary.
- Discard releases the unsaved source and pending files without permanent writes. Adding an image and removing its token before the first Save therefore stores no image, unless an independent retained thumbnail choice still requires that file.
- Preserve useful pending files when Save fails. Report the failed target/phase and completed effects accurately, including a source that was already saved. Partial media writes can leave orphans for manual cleanup; do not add rollback, automatic backup, retry markers or a stronger recovery guarantee.

### Removed Media And Publication

- Compare the already loaded saved body/fields and prepared candidate in memory, carrying current references and exact owned differences through the authoring operation. Do not persist a media baseline, add a by-ID media field, reread saved source for the comparison or use the explicitly refreshed Docs Media report as Save's authority.
- Keep ownership independent of public eligibility and rendered presentation. Use the same source-derived media reference list for ownership and eligible publication.
- Treat references as a set: removing one of several occurrences of the same owned file does not delete it. A thumbnail remains while its front-matter assignment remains, independently of body-image tokens. Do not infer dependencies through filename guesses or directory scans.
- Automatic removal applies to the exact document-owned body-media namespace and the document's explicit fixed thumbnail identity. Clearing the saved thumbnail assignment can select that exact flat thumbnail for removal through the same previous/current ownership handoff. Other old flat files remain outside that automatic lifecycle; migrating a flat body-media reference into a document folder queues the new bytes and document without deleting its flat original.
- After saved source and exact generation no longer use an owned file, persist its exact Preview/public removal in the existing queue before removing selected Working bytes. Report completed effects on failure and leave remaining Working orphan cleanup manual; do not introduce another ledger or transaction/recovery framework.
- Extend the existing document-owned publication handoff to carry exact media removals as well as current media. Repeated Saves preserve removals until completed, merge further removals and cancel a pending removal when a later successful Save restores that exact identity with ready bytes. Replacing an image at the same identity selects a write, not a subsequent deletion of its replacement.
- A removal retains its collection, document, type and relative identity even when no corresponding Working bytes or eligible current-document write remain. Publish consumes supplied removals without source reads, eligibility calculations, sharing checks, inventories, remote listings or orphan inference. Clear a successful publication unit only after its selected writes and removals have completed in Preview and the configured destinations; later GitHub Pages deployment is independent.
- Draft/exclusion changes retain canonical Working media. Whole-document deletion cleanup remains manual in this delivery; do not silently broaden token/assignment removal into automatic deletion of every file in a document folder.

### Migration And Manual Orphans

- Migrate body media from saved canonical document references, not from filenames that appear to contain an owner. Copy each referenced body-media file into its referencing document's namespace and rewrite that document's maintained references. A file referenced by several documents becomes one independent copy per document. Preserve ready bytes without routine image re-encoding,. Thumbnails retain their existing flat identities and bytes; this cutover does not move them.
- Include Draft and otherwise unpublished documents because this is canonical Working ownership. Use the established generation/eligibility handoff to select public effects only where appropriate. Reconcile affected generated references and per-document media metadata through the owning builders; do not leave a second reference baseline.
- Leave existing collection-level files where they are. This includes current orphans and the original files from which migrated copies were made. Neither group blocks migration, and neither needs an invented document owner, orphan directory, quarantine or automatic cleanup operation.
- After reference migration, retained originals become additional manual cleanup candidates. Keep old Preview/public files until the public references that need them have switched. Manual cleanup of Working, Preview and public storage remains explicit; deleting an old orphan locally does not implicitly select its remote deletion.
- Docs Media continues listing remaining flat files through its existing explicit recursive Refresh. Display the readable basename and known owning document separately from reference status. Flat leftovers have no assigned document owner. A file in a document folder can also be orphaned when it is no longer referenced; folder ownership alone does not make it referenced.
- Optional cleanup before migration reduces clutter but requires no new cleanup feature or migration prerequisite. A blank reference cell alone is not an instruction to delete a file.
- New body-media writes and migrated maintained references use the document layout; thumbnails retain the fixed flat layout. Retained old body-media bytes are cleanup residue, not a fallback reader, dual-write destination, compatibility alias or second supported ownership model. Keep report inventory of those bytes without adding legacy-path resolution branches.

### Publish And Manual Deployment

Publish transfers configured R2 media immediately and writes document JSON into the tracked `site/` artifact; Git commit/push and manually triggered GitHub Pages deployment happen separately. The user reconfirmed on 2026-10-16 that the resulting interval is an accepted consequence of choosing when to deploy instead of deploying on every commit. This follows the existing [Failure And Timing](../Catalogue_Deployment.md#failure-and-timing) boundary.

Apply document-owned media removals to Preview and configured public destinations during Publish. A still-deployed document can temporarily reference removed media until the user runs the next deployment; this is accepted and does not require a new readiness gate, deferred deletion action, deployment detection, scheduled cleanup, publication ledger or progress/resume state. Migration still retains old flat media as optional manual cleanup residue under the requirements above. This agreement establishes the intended implementation behavior; implementation and real migration/Publish actions retain their separate approval boundaries.

## Deliverables

| Owner/artifact | Target result |
| --- | --- |
| Document media paths and configured destinations | Body-media type roots with document-ID subfolders; thumbnails retain one flat document-ID filename. Exact relative identities survive every consumer. |
| Mounted Source session | Pending native files/choices, draft-aware dirty state and Save/discard membership; insertion has no permanent storage effect. |
| Source Save/media preparation | One narrow awaited operation owns supplied media processing, source persistence, exact generation and completed handoff. |
| In-memory media handoff and Docs publication queue | Loaded before/after reference differences and durable exact pending removals, without a media baseline file, by-ID media list, cross-document sharing decision or extra ledger. |
| Preview and selected publication | Selected current media and explicit removals completed during Publish, with existing confinement and transfer-completion boundaries; manual Pages deployment remains independent. |
| Existing-document migration | Referenced body-media copies and rewritten canonical/generated references, preserving old flat files for optional manual cleanup and leaving fixed flat thumbnails in place. |
| Docs Media | Readable filenames, document ownership and actual reference/orphan status from the existing explicit report refresh; flat residue remains visible. |
| Durable documentation | Update [Media And Asset Handling](../Media_And_Asset_Handling.md) as media authority, with narrow Source endpoint, publication/generated-contract and Development Checklist changes where their contracts change. |

## Process

1. The author optionally reviews existing orphans and cleans selected files manually. Leaving them in place has no effect on delivery readiness.
2. In Source, Add/Edit media retains pending files and updates the draft. Saved document/media bytes remain unchanged until Save.
3. Save selects the pending files used by that draft/thumbnail assignment, prepares them once using the carried author choices, then persists media/source and generates the exact document. Unexpected filename conflicts or invalid inputs are authoring errors; automatic sanitizer changes can produce a nonblocking note. The owner carries previous/current references into its selected Working removals and publication handoff.
4. The fresh document appears after Save completion. Unreferenced pending files are released; failures retain useful draft inputs and report completed effects. Search is unchanged.
5. Publish consumes the completed selected document/media writes and exact removals, including immediate configured R2 effects. The author continues to own commit/push and manual deployment, accepting the intervening public-media/site differences.
6. Explicit Docs Media Refresh supplies manual orphan review when wanted. It is not part of Save or Publish, and migration leftovers can remain indefinitely.

## DOM.0 Readiness Findings

### Workflow Changes

| Action | Current behavior | Proposed behavior |
| --- | --- | --- |
| Add Image/Add file | Uploads, prepares and permanently writes media, then inserts its reference. | Retains the browser File and inserts the document-owned reference. Only the identity preparation genuinely needed for insertion may call the server; no permanent write or media conversion is required at insertion. |
| Edit image presentation | Rewrites the captured token locally. | Stays a local draft edit. Selecting replacement bytes makes the draft dirty even if the resulting token text is identical. |
| Save | Sends source JSON, persists source and awaits exact document/Links generation plus fresh display. | Carries source, needed pending files/thumbnail choice and explicit replacement intent through one bounded operation. It prepares/sanitizes selected media once, reports unexpected conflicts, writes media/source, generates the exact result and persists current/removal effects before fresh display. No additional Replace or sanitizer review dialog. |
| Return/discard or browser exit | Discard handling observes source-text changes. | Includes pending media/thumbnail changes in that same draft decision and releases unsaved Files on discard. A reload still loses an unsaved draft; no persistent draft/upload recovery is introduced. |
| Create thumb | Writes the document's fixed thumbnail immediately and sets its assignment in the buffer. | Defers the write to Save. Preserve the existing single-thumbnail behavior: the latest explicit Create thumb selection wins; removing the body token does not clear the independent assignment. If only the thumbnail remains wanted, Save needs the File for thumbnail generation but need not write an unreferenced body image. |
| Remove an owned reference and Save | Leaves its stored bytes in place. | Removes the selected Working media after successful persistence/generation and queues exact Preview/public removal. Remaining occurrences or thumbnail assignments retain their own files. Restoring just the token after a completed deletion does not restore its bytes; add the file again. |
| Exact Rebuild or replacement Import | Completes saved document generation through the common handoff; Import writes its selected media as part of Import Apply. | Rebuild derives current publication references without a historical comparison. Replacement Import compares its loaded target and candidate in memory and completes exact removals after generation. Import Apply remains its own awaited commit operation, without a second Source Save step or persisted baseline. |
| Draft/exclusion, whole-document Delete | Eligibility updates publication; Delete removes source/generated documents while retaining media. | Keep those lifecycle boundaries. Eligibility never destroys canonical media; whole-document media cleanup remains manual within this delivery. Previously queued reference removals survive a later eligibility change or document deletion. |
| Publish and deployment | Publish applies selected repository/R2 effects; Pages deployment is manually triggered later. | Adds exact media removals to the existing selected units, including immediate R2 deletions. Retains the accepted deployment interval without coordination or deferred cleanup. |
| Migration and Docs Media | Flat media inventory is refreshed explicitly; cleanup is manual. | Copies referenced body media into each document namespace, rewrites maintained references and leaves flat originals and fixed thumbnails untouched. Refresh continues to report leftovers; neither migration nor opening the report automatically cleans them. |

### Implementation Findings And Scope

- The browser owns the captured source buffer, native File selection and token serialization; Python owns conversion/sanitization, persistence, exact generation and transfers. Pending-file selection and thumbnail choice stay in the browser; the server carries loaded saved source and the prepared candidate through one in-memory media comparison and completes their exact filesystem effects.
- Artifact paths, image-token references, inventory traversal and selected publication already accept nested relative identities. Native intake, import/materialisation and package/return-import boundaries must stop conflating a basename with the full body-media identity; thumbnails continue deriving their exact flat document-ID filename. This is coordinated ownership work, not a need for alternate roots or compatibility aliases. Migration preserves existing basenames; imported filenames do not need an additional naming cleanup.
- Source Save currently accepts source JSON only; native media intake accepts exactly one file with a 64 MiB file limit, 1 MiB metadata limit and approximately 66 MiB envelope. Multi-file Save needs a bounded request change at that actual upload boundary. No server staging sessions, parallel upload workflow or general JSON-limit increase is required by the proposed approach.
- `publication-media.json` is retired by DOM.9. Save and replacement Import compare loaded before/after source in memory. Generation derives current publication references without a historical ledger. DOM.10 removes the policy snapshot: index generation reads current `working/source/unpublishable.json` once per operation, applies it to complete metadata and compares membership with saved public indexes.
- A thumbnail is an independent assignment. Imported SVG and HTML use ordinary ready-media identities; no companion crawler or producer-source lifetime is introduced.
- Save failure can leave completed media writes, as the agreed manual-recovery model permits. Retain useful pending Files and report completed effects; do not add transactional rollback or a new retry protocol. Required target/owner, upload/format, path/symlink, sanitization and selected-transfer safeguards remain at their existing authoritative boundaries. Cross-document sharing audits, routine report refreshes, repeated conversion and whole-media scans have no purpose in this flow. The distinct post-implementation defensive review remains DOM.4.

### Workflow Decisions

| Choice | Recommendation | Effect |
| --- | --- | --- |
| Intentional replacement and unexpected filename conflicts | Selecting replacement bytes through Edit and then Save supplies replacement intent; no second Replace confirmation. Check only the selected document identity. | New/competing additions with conflicting bytes at the same identity report a clear filename conflict and retain the draft/Files for authoring to resolve. Reuse matching stored bytes where useful; do not add a review workflow, automatic renaming or shared-media scan. |
| SVG sanitization | Apply the existing sanitizer automatically once at its processing owner and carry the resulting bytes/diagnostics forward. | Report actual changes as a nonblocking note in the existing Save result. Malformed or unprocessable input remains an ordinary Save error. Remove mandatory sanitizer confirmation and its resubmission path; no override or separate review UI. |
| Combined pending-media limit for one Save | Retain the existing request scale: at most 64 MiB of selected pending file bytes combined, with source/metadata and multipart overhead bounded separately within the existing approximately 66 MiB envelope. | Individual files remain subject to the existing 64 MiB limit. Only new/replacement Files are submitted; already saved media is not re-uploaded. The user agreed on 2026-10-16 that an exceeded limit is reported for authoring to resolve. Keep the draft/pending Files and perform no automatic split, partial save/upload, batching or retry. |

This refined light-touch proposal was authorised by the user's request to start delivery on 2026-10-16. The size-limit handling is settled without adding batch machinery. Thumbnail independence, manual orphan cleanup, manual whole-document media cleanup and immediate Publish effects are carried forward as specified above. Product implementation does not authorise new test work or live-data work.

## Delivery Steps

All steps below are complete. Their records describe evidence at each implementation step; the final DOM.6 acceptance supersedes earlier pending-manual notes. Unexercised variants are disclosed under Completion And Acceptance. Optional orphan cleanup remains outside the delivery gates.

### [x] DOM.0 — Readiness And Implementation Approval

- [x] Confirm the outcome against the current broad intake/import, Source, generation, report and publication owners; reuse the shared generated-document boundary already delivered.
- [x] Identify selected media/thumbnail/source-companion lifetimes, the bounded Save upload boundary and required pending-removal semantics without freezing a complete schema or file inventory at readiness. Record the workflow changes and two choices above.
- [x] Review the actual replacement/sanitizer path and refine it following the user's light-touch request: carry Edit replacement intent into Save, report unexpected conflicts for authoring and sanitize SVG automatically with nonblocking diagnostics. No second Replace/sanitizer review dialog or confirmation resubmission is proposed.
- [x] Retain bounded file/aggregate uploads and report an exceeded limit for authoring to resolve, keeping the draft/pending Files. The user explicitly rejected automatic splitting or additional batch machinery on 2026-10-16.
- [x] Retain immediate Publish-time media writes/removals and separately triggered GitHub Pages deployment. The user reconfirmed the interval as an acceptable tradeoff on 2026-10-16; no deployment coordination or deferred deletion action is required.
- [x] Confirm old flat files can remain indefinitely and that pre-migration orphan cleanup is optional. Stop for missing referenced inputs or unresolved producer ownership, not for the existence of orphans.
- [x] Implementation authorised by the user's 2026-10-16 request to start delivery. Live migration/Publish still needs explicit authorisation at DOM.5. Test work remains separately specified under [Test Contract Discipline](../Test_Contract_Discipline.md).

Verification budget: concise read-only owner review, no prototype, generated writes, source/media migration or tests. Gate: complete. Record: readiness review completed on 2026-10-16 through scoped source/configuration reads covering the mounted Source/native intake, Save/exact Rebuild, Import Apply, thumbnail, generation metadata/queue, Docs Media and selected publisher boundaries. No architectural blocker was found. Size-limit feedback is agreed as an authoring concern without batch machinery. The refined replacement/sanitizer proposal removes confirmation resubmission and repeated preparation while retaining sanitizer rules. The user subsequently authorised starting implementation; live data and test-work approvals remain separate.

### [x] DOM.1 — Document-Owned Paths

- [x] Introduce document-ID subfolders under the existing body-media types and relevant editable producer roots; carry the resolved target and relative identity through intake/import, producers, local reads, export/return import and publication. Retain the single flat `thumbs/<doc_id>-thumb.webp` per document.
- [x] Preserve readable basenames and within-document replacement choices. Remove affected basename-flattening assumptions rather than adding aliases or duplicated ownership parsing.
- [x] Adapt Docs Media to present filename/ownership/reference status using its loaded datasets and keep flat residue visible through existing explicit Refresh.

Verification budget: focused changed-source lint/syntax and bounded path/call-chain review, expected short local static work without real asset writes or network. Gate: implemented and statically reviewed; live body-media cutover waits for DOM.5. Record: focused Python lint/compilation and JavaScript lint passed. The flat-thumbnail refinement restored the producer, readers and projected modules to their original flat paths; there is no net public runtime projection delta. Focused lint/compilation, projection check, site validation and whitespace passed after that refinement. No test, browser, real media processing, report Refresh, Build, migration or Publish ran. The scoped Redundancy And Defensive Behavior Review removed basename defaults at the media-file boundary, HTML destination fallback, repeated configuration loading and redundant HTML destination preflights. It retained exact target/configuration, upload/format, path/symlink, sanitizer, selected collision and byte-verification safeguards. Thumbnail review confirmed that source extraction and publication reuse the fixed-identity helper without scans, aliases or data moves. DOM.4 still owns final review of the complete Save/removal lifecycle.

### [x] DOM.2 — Media Writes On Source Save

- [x] Retain pending files/choices in the mounted browser session, including unchanged-text replacement dirty state and final-buffer/thumbnail selection. Token insertion writes no permanent files.
- [x] Carry selected pending inputs and explicit replacement intent through the narrow Save operation; complete required validation/preparation, automatic sanitization, writes, exact generation, queue handoff and fresh display under one busy lifetime. Report unexpected conflicts through ordinary authoring errors rather than a review/resubmission workflow.
- [x] Preserve useful inputs and accurate completed-effect errors on failure; discard and removed-before-first-Save inputs create no permanent media.

Verification budget: focused changed-source lint/syntax and source/service ordering review, expected short local static work. Gate: implemented and statically reviewed; manual Add/Edit/Save/discard, replacement and thumbnail observations remain user-owned. Record: Python lint/compilation passed for ten changed owners and JavaScript lint for six changed modules, including the new pending-file owner; affected review refinements received only their focused repeats. The workspace-provider public projection was updated and its exact diff reviewed; projection check, site validation and whitespace passed. No tests, browser, real Save/processing, source/media mutation, Build, report Refresh, migration or Publish ran. Restart/reload and interaction/failure acceptance remain unexercised.

DOM.2 code review: traced plain/unchanged Save, active final-buffer selection, pending replacement and independent thumbnail choices, removed-before-Save/discard, bounded multipart parsing, selected processing/collision/writes, saved-source versus generation failure, queue handoff and fresh display. Removed immediate intake writes and confirmation resubmission, duplicate raster validation/SVG sanitization, opaque-file/SVG temporary byte copies, cross-document media requeue scans, downstream envelope rechecks and the empty-upload fallback. The actual upload boundary owns sizes/field agreement; Save owns one candidate validation and request-output representation; processing retains format/sanitizer checks; target/adapter boundaries retain configured authority, confinement and selected comparison/verification. The review also kept committed metadata out of pre-source-write failures, reused the producer's sanitizer diagnostics and preserved loaded Subject context when replacement/thumbnail bytes change without changing the buffer. No persistent media staging/queue, batch split, rollback, compatibility alias, sharing audit or stronger recovery model was added. DOM.4 still owns final review after removal effects exist.

### [x] DOM.3 — Exact Removed-Media Effects

- [x] Carry previous/current per-document media references through successful Save/generation and identify only removed owned references and explicitly related outputs/sources.
- [x] Complete selected Working deletions and durable publication handoff without losing removal identities on partial failure. Preserve/merge/cancel pending removals across later completed Saves.
- [x] Apply exact Preview/public removals during Publish and retain successful-unit completion semantics; keep deployment waiting, other-document and directory/remote scans out of the path.

Verification budget: focused lint/syntax and bounded reference-set, queue-merge and selected-transfer source review; no live deletions or Publish as an incidental check. Gate: implemented and statically reviewed; runtime/failure acceptance remains open. Record: focused lint and compilation passed for 15 Python owners, affected review changes received focused repeats, generation/Save/publication imports and whitespace passed. No tests, browser, real Save/processing/removal, Build, Refresh, migration or Publish ran. Authored ownership is established by generation; absent fields do not authorise inference from old rendered payloads. The DOM.5 cutover completes that baseline for existing documents.

### [x] DOM.4 — Code And Defensive Behavior Review

- [x] Perform a distinct review of the final changed owners and reused helpers under [Development Checklist — Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).
- [x] Challenge repeated conversion, source parsing, collision comparisons, readiness probes, report refreshes, corpus scans, shared-media protection, compatibility paths, fallback roots and retry/rollback machinery. Confirm browser-owned membership decisions stay in the browser.
- [x] Record justified retained upload/format, exact target/configuration, path/symlink, sanitizer and selected write/transfer safeguards with their authoritative owner and operational purpose. Resolve findings and repeat only affected evidence.
- [x] Review migration ordering and confirm the accepted independent Publish/manual-deployment boundary has no added coordination machinery. Keep test changes outside the production approval unless separately agreed.

Verification budget: bounded source/diff review plus checks justified by concrete review changes; no automatic suite, Build or live publication. Gate: code findings resolved; remaining data/public effects are concrete and reviewable. Record: reviewed plain/empty/unchanged Save, selected preparation, repeated references, thumbnail independence, same-identity replacement, Draft/exclusion/fence changes, later Saves, withdrawal/deletion, queue/unlink/metadata failure ordering and selected Publish completion. Removed redundant downstream producer-identity normalisation/duplicate auditing. Kept upload/format/sanitizer, exact target/configuration, confined paths/unlink and selected byte/transfer verification at their owners; an exact ready-file check exists only to cancel a pending removal. No compatibility aliases, inferred companions, sharing/corpus audits, new ledger, rollback, deployment detection or cleanup service were added. Durable Media, Source endpoint, generated/publication contracts and checklist are updated. Static evidence establishes no runtime/manual acceptance.

### [x] DOM.5 — Existing Referenced-Media Migration And Cutover

- [x] Present the concrete local migration scope and obtain explicit approval before changing canonical sources and real Working media. Reuse the selected mapping as execution input; Preview/public publication retains its separate authority and no persistent migration framework is required.
- [x] Read each affected saved document once through the owning source boundary, map its exact referenced body media and producer companions, then copy ready bytes into its document namespace. Duplicate shared inputs per referencing document and preserve document IDs, authored fields and presentation. Keep fixed flat thumbnails in place.
- [x] Rewrite maintained references and complete the owning exact document generation/media-metadata/queue handoff. Use a wider document reconciliation only if the changed renderer/config contract requires it; keep Search and unrelated registered media production out of the cutover.
- [x] Preserve unrelated queued effects and keep all old flat files, including originals and existing orphans, in place. Do not infer owners for leftovers, clear queues wholesale or delete old public keys during migration.
- [x] Complete the explicitly approved Publish of migrated document/media selections through Preview to configured repository/R2 destinations, retaining old flat media and clearing only completed units.
- [x] Record the user's representative normal-use/publication acceptance and the inspected local/R2/live surfaces at DOM.6; retain commit/push/deployment as user-owned actions and old-media cleanup as optional maintenance.

Verification budget: proportional diagnostics for the explicitly approved migration/Publish, with no baseline inventory or idempotence rebuild. Gate: complete; migration/publication and representative normal use are accepted. Record: 342 files were copied/verified, 245 canonical/generated documents were updated with IDs/fields/dates retained, and the separate Publish completed 245 document units and 85 media transfers. Old flat files and thumbnails remained in place. Focused validation and source/defensive review passed; no incidental Search, report Refresh, cleanup, Git or deployment action ran. DOM.9 later retired the temporary media baseline. Working Notes retains the detailed operation evidence.

### [x] DOM.6 — Manual Acceptance And Closeout

- [x] Record the user's accepted sequence: remove media from a Draft, add media to it, copy its content/references into a publishable document, delete the Draft, and Publish. Keep observed behavior separate from unexercised variants.
- [x] Record local site-preview, exact R2 checks and the diagnosed committed-document/deployment mismatch; accept the representative normal-use result without claiming a complete migrated-corpus or failure audit.
- [x] Maintain durable media/Source/publication contracts, including in-memory comparison, the single canonical exclusion-policy read, immediate Publish-time media removal and manual orphan cleanup.
- [x] Mark the delivery complete in Planned Features and retain it and Working Notes as closed evidence pending manual archive; delete no documentation.

Verification budget: user normal-use observations and bounded documentation/source-diff review. Gate: complete; the user explicitly accepted the working result and requested closeout on 2026-10-16. The Completion And Acceptance section records the observed sequence and remaining evidence limits. Code review is not applicable to this documentation-only closeout; the earlier distinct implementation and Redundancy And Defensive Behavior Reviews remain the source evidence. No tests, Build, Search/Recent, media/queue writes, Publish, Git or deployment ran for closeout.

### [x] DOM.7 — One Media Reference List

- [x] Remove the retired diagram compiler, producers, source-opening endpoints, browser rendering/theme pairs and toolchain; preserve ordinary SVG import/sanitization/detail viewing.
- [x] Use each document's single source/field-derived `media` map for owned-reference differences and eligible publication, with no separate rendered list or producer-companion metadata.
- [x] Convert the existing 245 saved records directly, retaining all 378 references, exclusion policy and pending publication selections. The baseline has zero diagrams/relationships; no document/media regeneration or physical asset cleanup is needed.
- [x] Update maintained file/media/diagram/configuration/toolchain documentation while preserving repository documentation diagrams.
- [x] Complete focused lint/import/projection validation and the distinct source/diff and Redundancy And Defensive Behavior Review; record actual evidence and limits in Working Notes.

Verification budget: focused lint/syntax/import diagnostics, selected metadata inspection, public-code projection and site validation. Gate: implementation, 245-record/378-reference conversion and distinct review complete. Static evidence passed; no Build, Search, Publish, Git or deployment ran for this slice. Retained upload/format/sanitizer/confinement/transfer safeguards keep their existing owners, with no alias, reconciliation, purge or stronger recovery. Manual interaction remains unverified.

### [x] DOM.8 — Repository Reference Cleanup

- [x] Delete the leftover feature dependency directory and its specific ignore rule.
- [x] Remove dedicated retired renderer/source/projection tests and browser smoke, their profile entry, and obsolete fixture/assertion fragments in mixed files. Keep ordinary SVG behavior and generic fenced-code preservation coverage.
- [x] Remove obsolete implementation references and historical mentions, delete the superseded coverage note and preserve documentation diagrams byte for byte. Update external diagram-authoring guidance and the three retained browser boundaries.
- [x] Complete focused syntax/lint, selected pure runner/Markdown checks and distinct source/diff review. Record exact evidence and limits without running a broad scope-era suite or browser profile.

Verification budget: existing focused pure checks in [Testing](../Testing.md#diagram-pipeline-cleanup), syntax/whitespace and reference/diff inspection. No runtime/media generation, configured workspace writes, Publish, Git or deployment. Gate: complete within the approved cleanup scope. Removed the 404 MB leftover dependency directory, 20 stale bytecode files, five dedicated Python test modules, one browser smoke, 18 retired selectors/helpers and obsolete mixed fixture/assertion fragments. Lint and compilation passed for all 19 changed Python files; the runner-membership and shared Markdown selectors passed (two checks, 0.04 seconds). The converter selector could not collect because its old support module imports `docs_scope_config`; that fixture migration remains outside this scope. Distinct source/diff and Redundancy And Defensive Behavior Review confirmed deletion-only feature work, preserved generic code/SVG behavior and no new production checks, fallback, alias, audit or recovery machinery. Documentation pruning retained current metadata/removal evidence and restored surviving acceptance details; all eight documentation diagrams remain unchanged. A final reference search finds only those diagrams and their notation guide. No runtime/public artifact, configured workspace, media, queue, Build, Search, Publish, browser, Git or deployment operation changed.

### [x] DOM.9 — In-Memory Media Comparison

- [x] Compare loaded saved source and prepared candidate in memory during Source Save and replacement Import; carry exact owned removals through generation without a persisted baseline or new by-ID media field.
- [x] Keep Rebuild/CLI generation to current reference extraction and eligible queue selection; retain pending-removal merging/cancellation, independent thumbnails and manual whole-document/orphan cleanup.
- [x] Retire the configured `publication-media.json` directly and preserve pending queue bytes. The initial private-index policy snapshot is superseded by DOM.10.
- [x] Update maintained media/file/build contracts and complete focused static diagnostics and a distinct Redundancy And Defensive Behavior Review.

Verification budget: focused Python lint/compilation, service/builder import and CLI diagnostics, exact local metadata cutover and bounded source/diff review. No new or modified tests, live Save/Import, document/media generation, Search/Recent refresh, Publish or deployment. Gate: implementation and local metadata retirement complete; normal-use interaction/failure acceptance remains in DOM.6. Working Notes records selected evidence and review findings.

### [x] DOM.10 — Single Exclusion Policy Input

- [x] Remove the policy copy from `index-tree.json`, saved policy comparison/flags and old membership-reuse shortcuts tied to that snapshot.
- [x] Read canonical `working/source/unpublishable.json` once per index-generation operation, carry it through ordinary/collection and dependent generation, and compare resulting membership with saved public indexes.
- [x] Retain ordinary subtree/Draft and collection-host exclusions, fixed Catalogue eligibility and queue-only Publish. Exact operations apply policy edits at the next index generation; Search/Recent retain their explicit refresh owners.
- [x] Remove the field from the configured private index without generation, policy/queue changes or publication; update maintained contracts and complete focused static/read-only diagnostics and distinct defensive review.

Verification budget: lint/compilation for six changed Python owners, service/builder imports, a read-only projection using existing real metadata and exact private-index cleanup. No test authoring or test run, live Save, document/media generation, Search/Recent refresh, Publish or deployment. Gate: code and local cleanup complete; normal-use interaction/failure acceptance remains in DOM.6. Working Notes records selected evidence and review findings.

## Follow-on

Manual deletion/reconciliation of existing flat leftovers and partial-write orphans remains author maintenance. An automated orphan purge, cross-document media library, whole-document media deletion, deployment-aware cleanup service or new test collection requires its own explicit scope; none is implied by this delivery.
