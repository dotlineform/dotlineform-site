---
draft: false
doc_id: d-20261001-145038-ad04ac
title: Source Editor And Token Modals - Delivery
added_date: "2026-10-01 14:50:38"
last_updated: "2026-10-01 14:50:38"
summary: Edit complete Markdown including front matter and reopen token modals with existing values, removing Source's metadata/token panel while retaining one validated document Save.
ui_status: proposed
parent_id: d-20260902-102745-8379ea
---
# Source Editor And Token Modals - Delivery

## Requirements

Deliver one outcome: eligible local documents are edited as complete Markdown in one Source buffer, including front matter, while supported Catalogue tokens are created or edited through their corresponding modals. Source no longer needs a metadata/token side panel or **i** control. One document Save validates and persists the complete source; modal confirmation changes only the unsaved buffer.

The requirements were agreed on 2026-10-01. This is a proposed delivery; readiness and implementation have not started. [Unified Analysis And Catalogue Presentation](Analysis_And_Catalogue_Presentation.md) is the feature parent. Suggested order is [Info Panel Related Links And Pinning - Delivery](Info_Panel_Links_And_Pinning_Delivery.md) first, this Source simplification second. Reader pinning does not depend on this delivery. [Source Editor Scripts](Source_Editor_Scripts.md) is the primary durable destination, with API ownership in [Source Editor Endpoints](Source_Editor_Endpoints.md) and token interaction in [Semantic Tokens Source Editor UI](Semantic_Tokens_Source_Editor_UI.md).

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

- [ ] One complete Markdown Source buffer, including front matter, with one dirty/discard/Save lifecycle.
- [ ] Full-source read/save integration with required-field validation, fixed document/collection identity and preserved failed drafts.
- [ ] Creation/edit modal reuse with current-token initialization, Apply/Cancel and guarded exact-occurrence replacement.
- [ ] Removal of the separate Source metadata/token panel, **i** control and obsolete drafts/hosted-view wiring without aliases.
- [ ] Preserved reader pinning, local/public boundaries, source normalization/timestamps and independent watcher generation.
- [ ] Proportionate selected evidence, user editor/modal review, distinct code review and durable documentation transfer.

## Process

1. Choose Edit document for an eligible ordinary or collection document. Source displays the complete Markdown, including front matter, without opening a side panel.
2. Edit Title, Summary, other valid metadata or body text directly. The session remains unsaved until Save.
3. Place the caret inside an existing supported token or select its exact occurrence, then use the corresponding token action. Its modal opens with that target and its current values selected.
4. Change fields or choose another supported target, then Apply. Only that occurrence changes in the dirty buffer. Cancel leaves it unchanged.
5. Save the document. Valid source is persisted once and returns to the rendered route; the watcher refreshes generated content independently. Invalid front matter or immutable identity produces a clear error and retains the full draft.
6. Return to doc without saving to use the existing single discard decision. Cancellation retains the session. In rendered mode, open the related-links panel only through a non-empty section's pin.

## Delivery Steps

### SEM-0 — Readiness

- [ ] Confirm full-source read/save ownership, schema/identity rules, timestamp handling and the exact ordinary/collection authoring boundary.
- [ ] Confirm current modal initialization, explicit occurrence selection and full-buffer token ranges against the existing parser/editor owners.
- [ ] Confirm source-panel retirement and reader capture transitions can be completed without changing public capabilities or unrelated authoring workflows.
- [ ] Confirm the delivery sequence and primary durable owner. Stop for a required identity migration, index-placement redesign, new front-matter language or broader editor framework.

Gate: present concise read-only readiness for implementation approval; remain proposed until safe to implement. Verification: broad specification/owner comparison, without a prototype, test authoring or generated writes. Record: requirements agreed on 2026-10-01; readiness not started.

### SEM-1 — Complete Source Session And Save

- [ ] Mount one complete-source buffer and replace the separate metadata form/draft and split request assembly.
- [ ] Parse and validate the complete source at Save, enforce the fixed target and preserve the draft on failure.
- [ ] Preserve normal source normalization, timestamp ownership, atomic persistence and source-write completion timing.
- [ ] Keep body contributions and current document-subject projection tied to the exact active buffer/target without a duplicate editable state.

Gate: complete-source editing and Save are available for local review. Verification: inspect the smallest relevant existing parser/service selection and its durable coverage before selecting execution; document the risk, side effects and cost. Use focused syntax/lint and source review where sufficient. Test changes require a separately approved specification under [Testing](Testing.md) and [Test Contract Discipline](Test_Contract_Discipline.md). Record: not started.

### SEM-2 — Modal Occurrence Editing And Panel Removal

- [ ] Add edit-mode initialization for every supported stored token value and retain current creation behaviour.
- [ ] Bind the corresponding explicit action to a recognized occurrence, implement Apply/Cancel and guard its full-buffer range before replacement.
- [ ] Remove Source metadata/token hosted views, **i**, selection-driven panel updates and obsolete pending token drafts after their replacements are available.
- [ ] Preserve one session Save/discard lifecycle and the independent reader-pinning owner; remove obsolete production call sites and configuration without aliases.
- [ ] Inspect any affected existing tests as unreviewed contracts; separately scope changes instead of silently rewriting them to match the new implementation.

Gate: Source works entirely through its full buffer and modals, with no authoring panel dependency. Verification: select any justified existing parser/range/provider evidence within the agreed budget; editor selection, modal values, cancellation and feel remain user manual review. Record: not started.

### SEM-3 — Integration And User Review

- [ ] Confirm ordinary and configured collection targets, validation failures, dirty discard and existing buffer contributions still use the mounted Source target.
- [ ] Record user review of complete front matter, Title/Summary edits, exact repeated-token occurrences, existing-value preselection, Apply/Cancel and failed Save recovery.
- [ ] Confirm Source entry/exit and rendered pin opening without exposing management capabilities publicly.
- [ ] For inventory-listed shared runtime changes, run `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`. Do not project management-only modules.

Gate: user acceptance of the complete Source/modal workflow. Verification: explicit-path lint, required shared-runtime projection checks and the agreed manual review; no automatic broad suite, browser choreography, Search build or Publish. Record: not started.

### SEM-4 — Code Review

- [ ] Review the final bounded diff for source/target ownership, parser duplication, normalization loss, range errors, modal-default overwrite, failed-draft loss and stale mutation paths.
- [ ] Confirm removal of duplicate metadata/token drafts, old request assembly, dead hosted views and compatibility residue.
- [ ] Confirm public code/config carries no management capability and reader capture does not become authoring context.
- [ ] Resolve findings and repeat only affected evidence; report separately scoped test gaps and other omissions.

Gate: present review findings, resolutions and remaining limitations. Verification: bounded code/diff review with selected affected checks. Record: not started.

### SEM-5 — Closeout

- [ ] Confirm complete Markdown editing, current-token modal editing and removal of Source's panel and **i** control.
- [ ] Transfer shipped ownership into Source Editor Scripts, update Source Editor Endpoints for the actual API contract, and reconcile Semantic Tokens Source Editor UI and Info Panel for the retired authoring views.
- [ ] Update the feature parent's delivery state and recommend this delivery for manual archive after durable transfer.
- [ ] Distinguish verified implementation from separately requested Publish, deployment, commit and push.

Gate: explicit user closeout. Verification: reuse accepted implementation evidence; documentation-only closeout needs bounded source review, without automatic rebuilds or tests. Record: not started.

## Follow-on

New token families, general Markdown-link editing modals, syntax highlighting, richer text editing, disk-conflict handling and canonical Index placement remain separate work. This delivery simplifies the current Source and Catalogue-token workflows without adding those capabilities.
