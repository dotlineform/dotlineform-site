---
draft: false
doc_id: d-20261001-145038-ad04ac
title: Source Editor And Token Modals - Delivery
added_date: "2026-10-01 14:50:38"
last_updated: "2026-10-01 18:27:54"
summary: Edit complete Markdown including front matter and reopen token modals with existing values, removing Source's metadata/token panel while retaining one validated document Save.
ui_status: done
parent_id: d-20260902-102745-8379ea
---
# Source Editor And Token Modals - Delivery

## Requirements

Deliver one outcome: eligible local documents are edited as complete Markdown in one Source buffer, including front matter, while supported Catalogue tokens are created or edited through their corresponding modals. Source no longer needs a metadata/token side panel or **i** control. One document Save validates and persists the complete source; modal confirmation changes only the unsaved buffer.

Complete, accepted and closed on 2026-10-01. Complete-source editing, modal occurrence editing and panel retirement are implemented; focused static evidence, shared-runtime projection and bounded code review are complete. The user accepted the delivered outcome and explicitly approved closeout; separately itemized interaction cases and live persistence/Import/Review remain evidence limits. [Unified Analysis And Catalogue Presentation](Analysis_And_Catalogue_Presentation.md) is the feature parent. [Info Panel Related Links And Pinning - Delivery](Info_Panel_Links_And_Pinning_Delivery.md) is accepted and closed, satisfying the suggested sequence. [Source Editor Scripts](Source_Editor_Scripts.md) is the updated primary durable owner, with the implemented API in [Source Editor Endpoints](Source_Editor_Endpoints.md) and token interaction in [Semantic Tokens Source Editor UI](Semantic_Tokens_Source_Editor_UI.md). This delivery is ready for manual archive; Publish, deployment and Git actions remain separate.

### Complete Markdown Buffer

- Show the complete loaded Markdown document, with its front-matter delimiters, authored fields and body in the same editable buffer. Title and Summary are edited directly there; remove their separate form and split metadata draft.
- Retain one session for dirty/busy state, Save and Return to doc. Opening in VS Code remains an independent action. Exposing front matter reduces the number of editing surfaces; Save validation supplies the guard against invalid edits.
- Keep the mounted document target fixed independently of editable source. Changing or removing `doc_id`, or declaring a conflicting collection identity, fails visibly and retains the full unsaved buffer. Save cannot rename a document, change its collection or resolve a different file from edited metadata.
- Other authored front-matter fields may be edited when valid under the owning ordinary/collection schema. Reuse the maintained front-matter grammar, required-field rules and collection specialisation rather than introducing another parser or schema.
- Save validates the complete candidate before one atomic source write. Preserve unaffected authored content and metadata formatting through the existing normalization and timestamp policies. Malformed front matter, missing required fields or a write failure leaves the full draft available for correction.
- Canonical Index position and hierarchy retain their existing owner; editing source is not an index-placement operation. Catalogue data, Works authoring-subject rules and publication eligibility retain their own authorities.
- Keep existing source-root confinement and authoring eligibility. Showing front matter does not make generated or otherwise read-only collection documents editable.

### Existing-token Modal Editing

- Reuse the existing token creation modals for editing supported occurrences: Work/Gallery Media View links and Work Catalogue images. Add no new token grammar, target families or Gallery image form.
- An explicit corresponding Source action with the caret inside a supported occurrence or its exact range selected opens that token's modal in edit mode. Selecting or moving the caret alone does not open a modal. With no matching occurrence, the action retains its normal creation behaviour.
- Preselect the stored target and populate every authored presentation value from the current buffer. Media links retain their current link text. Images retain caption and metadata choices, optional static summary, placement and fill-width. Derived Work title/alt presentation continues to come from Catalogue data; loading it must not overwrite the stored choices with insertion defaults.
- The same target picker and field rules apply to creation and editing. An edit may select another supported Catalogue target through that picker; the mounted document identity remains fixed. Unavailable targets and failed media reads remain visible without silently selecting another target or losing the existing source.
- Label editing confirmation **Apply**. Validate the modal values and current media through the existing token owners, serialize the result and replace only the captured occurrence in the unsaved buffer. Creation retains its existing insertion action.
- **Cancel** leaves the buffer unchanged. Failed validation keeps the modal's entered values for correction. After Apply, the token text itself is the session's authoritative value; do not maintain a separate pending token-field draft that is serialized later by Save.
- Capture exact occurrence boundaries, current buffer revision and the mounted adapter before focus moves. Reject a stale range, changed buffer or replaced editor before mutation. These are in-session guards; do not introduce disk revision checks or external-edit merging.
- Full-document offsets must account for editable front matter. Token recognition applies to the Markdown body using the existing code/comment/literal exclusions. Token-looking front-matter values must not become editable body occurrences. Unsupported or malformed token-like source retains the existing literal behaviour.

### Save And Panel Retirement

The source service owns full-document parsing, immutable-target validation and persistence. Replace the current separate loaded-front-matter, Title/Summary and body request assembly with one complete-source workflow through the existing service. Determine the exact transport shape during approved implementation; remove the superseded contract without compatibility aliases. Save continues to finish at source persistence. The watcher independently generates document and Links projections; Source does not await generation, suppress refresh, rebuild Search or publish.

Remove Source's metadata and semantic-token hosted views, **i** action, automatic panel opening/context switching and the obsolete pending token-field plumbing once the complete buffer and modal workflow replace them. Retain the shared shell and reader-owned panel integration used by the pinning delivery. Entering Source closes any captured reader panel; returning to rendered content leaves it closed until a related-links pin is used.

This delivery is local Manage authoring work. Public readers gain no source, token modal, registry lookup, management-service or write capability. Any shared runtime changes still follow the canonical `docs-viewer/` to tracked `site/docs-viewer/` inventory; management-only modules remain excluded.

## Deliverables

- [x] One complete Markdown Source buffer, including front matter, with one dirty/discard/Save lifecycle.
- [x] Full-source read/save integration with required-field validation, fixed document/collection identity and preserved failed drafts.
- [x] Creation/edit modal reuse with current-token initialization, Apply/Cancel and guarded exact-occurrence replacement.
- [x] Removal of the separate Source metadata/token panel, **i** control and obsolete drafts/hosted-view wiring without aliases.
- [x] Preserved reader pinning, local/public boundaries, source normalization/timestamps and independent watcher generation.
- [x] Proportionate selected evidence, user acceptance, distinct code review and durable documentation transfer; separately itemized interaction cases remain an evidence limit.

## Process

1. Choose Edit document for an eligible ordinary or collection document. Source displays the complete Markdown, including front matter, without opening a side panel.
2. Edit Title, Summary, other valid metadata or body text directly. The session remains unsaved until Save.
3. Place the caret inside an existing supported token or select its exact occurrence, then use the corresponding token action. Its modal opens with that target and its current values selected.
4. Change fields or choose another supported target, then Apply. Only that occurrence changes in the dirty buffer. Cancel leaves it unchanged.
5. Save the document. Valid source is persisted once and returns to the rendered route; the watcher refreshes generated content independently. Invalid front matter or immutable identity produces a clear error and retains the full draft.
6. Return to doc without saving to use the existing single discard decision. Cancellation retains the session. In rendered mode, open the related-links panel only through a non-empty section's pin.

## Delivery Steps

### SEM-0 — Readiness

- [x] Confirm full-source read/save ownership, schema/identity rules, timestamp handling and the exact ordinary/collection authoring boundary.
- [x] Confirm current modal initialization, explicit occurrence selection and full-buffer token ranges against the existing parser/editor owners.
- [x] Confirm source-panel retirement and reader capture transitions can be completed without changing public capabilities or unrelated authoring workflows.
- [x] Confirm the delivery sequence and primary durable owner. Stop for a required identity migration, index-placement redesign, new front-matter language or broader editor framework.

Gate: complete; the user approved implementation on 2026-10-01. Record: read-only comparison confirmed the source service, mounted adapter, existing Catalogue modal/parser and reader capture as the owning boundaries. Reader pinning is closed; no migration, Index redesign, new language or editor framework was required. The worktree was clean. Stale Source endpoint documentation and scope/revision-bearing tests were identified; production documentation is reconciled and test work remains separate.

### SEM-1 — Complete Source Session And Save

- [x] Mount one complete-source buffer and replace the separate metadata form/draft and split request assembly.
- [x] Parse and validate the complete source at Save, enforce the fixed target and preserve the draft on failure.
- [x] Preserve normal source normalization, timestamp ownership, atomic persistence and source-write completion timing.
- [x] Keep body contributions and current document-subject projection tied to the exact active buffer/target without a duplicate editable state.

Gate: complete and accepted. Record: read/save use one `source_text` contract with no split-field aliases. The source model owns strict splitting; the service validates fixed identity, required Title/readiness, report rules and collection Subject fields before the existing atomic write. A write-free context request projects the captured unsaved Subject without rereading document sources. Header newline conventions, authored formatting, body normalization and existing timestamp policy are retained. Save still ends at persistence, independently of watcher generation.

Verification budget: explicit-path Python/JavaScript lint and Python syntax address malformed source and module errors; direct module imports address the moved splitter's service integration; bounded diff review addresses identity, failed-draft retention and normalization. These are local diagnostics with no service startup, network requests or document writes and took seconds. Existing Source service tests were inspected and retain retired scope/revision contracts, so no tests were changed or run. Evidence limits are recorded in [Source Editor Scripts](Source_Editor_Scripts.md); test changes require separate agreement under [Testing](Testing.md). Python lint/syntax passed for the eleven changed service/parser modules, JavaScript lint passed for the seventeen changed/new modules, and management/viewer module imports succeeded.

### SEM-2 — Modal Occurrence Editing And Panel Removal

- [x] Add edit-mode initialization for every supported stored token value and retain current creation behaviour.
- [x] Bind the corresponding explicit action to a recognized occurrence, implement Apply/Cancel and guard its full-buffer range before replacement.
- [x] Remove Source metadata/token hosted views, **i**, selection-driven panel updates and obsolete pending token drafts after their replacements are available.
- [x] Preserve one session Save/discard lifecycle and the independent reader-pinning owner; remove obsolete production call sites and configuration without aliases.
- [x] Inspect any affected existing tests as unreviewed contracts; separately scope changes instead of silently rewriting them to match the new implementation.

Gate: complete and accepted. Record: explicit actions recognize only corresponding body occurrences, initialize stored Work/Gallery links or Work image fields, preserve authored values during media reads and serialize Apply directly into the unsaved buffer. Recognition excludes front matter and literal Markdown contexts. Captured text/range, revision and mounted adapter protect exact repeated occurrences and stale mutations. Source hosted views, **i**, metadata/token drafts, automatic panel routing and obsolete registrations/CSS are removed. The reader controller now carries only detached capture, pin replacement and Close. Explicit-path lint and bounded source/call-site review passed; no tests or browser checks were run.

### SEM-3 — Integration And User Review

- [x] Confirm ordinary and configured collection targets, validation failures, dirty discard and existing buffer contributions still use the mounted Source target.
- [x] Record user acceptance of the delivered Source/modal workflow; separately itemized review of front matter, Title/Summary edits, repeated-token occurrences, preselection, Apply/Cancel and failed Save recovery remains an evidence limit.
- [x] Confirm Source entry/exit and rendered pin opening without exposing management capabilities publicly.
- [x] For inventory-listed shared runtime changes, run `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`. Do not project management-only modules.

Gate: complete; user acceptance recorded on 2026-10-01. Record: source review confirms mounted ordinary/collection targets remain independent of editable metadata, failed Save retains the draft, contributions use the current complete buffer, and Source entry releases reader capture without an authoring reopening path. `bin/site-code-update` projected exactly seven changed shared runtime files; the tracked delta was inspected. `bin/site-code-update --check` and `bin/site-validate` passed. Management modules and token registry remain outside the public inventory. The user accepted the delivered outcome and approved closeout after clarification of the shared runtime changes. Live Save/failed-write recovery, Import/Review flows and editor/modal interaction were not exercised by Codex; no separate item-by-item manual results were supplied. No browser tests, Docs/Search rebuild, Publish, deployment, commit or push occurred.

### SEM-4 — Code Review

- [x] Review the final bounded diff for source/target ownership, parser duplication, normalization loss, range errors, modal-default overwrite, failed-draft loss and stale mutation paths.
- [x] Confirm removal of duplicate metadata/token drafts, old request assembly, dead hosted views and compatibility residue.
- [x] Confirm public code/config carries no management capability and reader capture does not become authoring context.
- [x] Resolve findings and repeat only affected evidence; report separately scoped test gaps and other omissions.

Gate: bounded code review complete. Findings resolved: guard parser registry access during synchronous occurrence recognition; treat valid token fields atomically so authored backticks/comment markers do not create Markdown exclusion contexts; compare response identity using explicit target fields; invalidate adapters and late source/context responses after replacement; preserve original header newlines after textarea normalization; resolve unsaved Subject context without scanning source documents; redirect existing Import/Review splitter consumers to the source-model owner. Production reference scans found no obsolete panel/draft calls or aliases. Affected lint/syntax passed after corrections, and management/viewer module imports succeeded. Public capture carries no authoring/service context, and public adapters acquire no Source API. Separately itemized interaction cases and live persistence/Import/Review evidence remain the explicit limits.

### SEM-5 — Closeout

- [x] Confirm user acceptance of complete Markdown editing, current-token modal editing and removal of Source's panel and **i** control, with explicit closeout approval.
- [x] Transfer implemented ownership into Source Editor Scripts, update Source Editor Endpoints for the actual API contract, and reconcile Semantic Tokens Source Editor UI and Info Panel for the retired authoring views.
- [x] Update the feature parent's delivery state and recommend this completed delivery for manual archive.
- [x] Distinguish verified implementation from separately requested Publish, deployment, commit and push.

Gate: complete; the user explicitly approved closeout on 2026-10-01. Durable ownership is transferred and the feature parent's state records the accepted delivery. Recommend this completed delivery for the next manual documentation archive. Closeout reused the recorded implementation evidence and reviewed only the status/documentation edits; no rebuild, lint or test run was required. No separate working-note or verification sibling was created. Publish, deployment, commit and push remain separate user actions and were not performed.

## Follow-on

New token families, general Markdown-link editing modals, syntax highlighting, richer text editing, disk-conflict handling and canonical Index placement remain separate work. This delivery simplifies the current Source and Catalogue-token workflows without adding those capabilities.
