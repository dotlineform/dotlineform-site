---
draft: false
doc_id: d-20261014-155524-f8752f
title: Document Media Working And Preview
added_date: "2026-10-14 15:55:24"
last_updated: "2026-10-14 15:55:24"
summary: Prerequisite split of ready document media into Working and Preview, using a user-owned Publish and manual-copy baseline before the code cutover.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Document Media Working And Preview

This is a prerequisite to [Incremental Document Publish](Incremental_Document_Publish.md), parented to [Planned Features](../Planned_Features.md). It gives document media the same Working/Preview ownership already used by Work media, so incremental Publish can start from an established media baseline.

## Current And Next State

Scope and manual cutover sequence agreed on 2026-10-14. The user will complete the existing Publish and manually copy the media before code changes begin. This document is proposed; the user baseline, code cutover and acceptance remain pending. Creating this document does not perform Publish, copy media or authorize an immediate code change.

Current ready document media lives in one shared `assets/media/` tree beneath the configured Docs workspace root. Local media reads, intake/build output and publication use that live tree; Preview has no independent document-media copy. Work media already uses `working/assets/works/` and `preview/assets/works/`.

Complete result: ready document media lives under `working/assets/media/` and `preview/assets/media/`. Authoring, intake, generation and local readers use Working. Publish applies its prepared media selection to Preview, then deployment reads Preview media. Snapshot replacement preserves the Preview media tree. The former shared document-media root is retired after the cutover.

The user estimates about 43 MB and considers the media replaceable. This delivery uses a light manual baseline and focused source/path review. It requires no migration utility, byte-for-byte baseline comparison, hash inventory, remote audit, backup scheme or complex recovery procedure.

## Requirements

- Cover ready document media for the ordinary workspace and configured collections: `img`, `thumbs`, `svg`, `files` and `html`, including owned companion assets. Preserve the existing `workspace/` and `collections/<id>/` namespaces, filenames and type layout.
- Keep editable media/build inputs with their existing Working source owners. This delivery changes ready-media ownership, not the source authority or producer policy.
- Keep document tokens, `docs-media:` identities, local served URLs and public repository/R2 namespaces unchanged. Storage roles do not become browser stages or URL discriminators.
- Resolve ready media through the configured workspace/stage owner. Local readers, media intake, generation, inventory and package/export input reads use Working; publication transfer uses Preview. Keep resolved inputs explicit through the owning operations.
- Publish reads prepared Working media, copies its selected bytes into Preview and deploys from Preview. Media output created by the existing temporary publication preparation uses its explicit publication output owner; it must not reintroduce shared live storage or write back into Working media.
- Preserve Preview media across document snapshot replacement without adding a second media scan or complete-tree hash/inventory. Reuse the current Publish operation's known media selection for the Working-to-Preview handoff.
- Cut over the active code/configuration in one change. The former `assets/media/` location is not a fallback, compatibility alias or second write destination.
- Retain existing confinement, missing-input and selected transfer checks at their current boundaries. Add no baseline-validation framework, freshness checks, automatic repair, rollback or backup retention requirement.
- Keep the existing complete document preparation/Publish workflow for this prerequisite. Queue-only selection, generic media deletions, retained queue progress, upstream public-document preparation and removal of full reconciliation belong to Incremental Document Publish.

## Deliverables

- User-confirmed published baseline and two manually populated document-media trees.
- Workspace configuration and path resolution that give Working and Preview their own ready document media.
- Updated local/media/build/package owners and the existing Publish media handoff, with deployment bound to Preview and snapshot replacement preserving its media.
- Durable storage/media documentation describing the shipped boundary, plus prerequisite completion recorded in Incremental Document Publish.

Frontend readers and authoring controls retain their existing logical identities and interaction. Python configuration/services/builders own the required physical reads, writes and publication copying. There is no new browser stage, media-selection UI or lifecycle service.

## Process

All paths below are relative to the configured Docs workspace root.

1. The user runs the existing Publish and waits for successful completion before establishing the manual media baseline.
2. The user manually copies `assets/media/` to both `working/assets/media/` and `preview/assets/media/`, preserving the `workspace/` and `collections/` contents beneath each `media/` directory. The existing Work-media trees stay alongside these copies.
3. The user confirms the Publish and both copies completed. Keep media unchanged between that baseline and the code cutover; this is a short user sequencing rule, not a new lock or preflight system. The old shared folder remains available because the current code still uses it until cutover.
4. After the baseline confirmation and implementation approval, update code/configuration to use Working for local/input media, Preview for published media, and the existing Publish operation for the handoff.
5. The user checks ordinary and collection media through normal local use. Subsequent Publish uses the new ownership. Retire the old shared folder after the code cutover is accepted; there is no ongoing backup requirement.

User confirmation is sufficient for the baseline. If a copy is wrong, correct that copy; do not add migration receipts, reconciliation manifests or automated recovery.

## Delivery Steps

### [ ] DMP.0 — Readiness

- [ ] Confirm the existing media/path, temporary publication and snapshot owners support this bounded storage cutover.
- [ ] Retain the agreed user Publish → manual copies → code sequence and the light verification budget.
- [ ] Confirm the prerequisite leaves queue-only publication and new deletion/progress behavior with Incremental Document Publish.

Verification budget: concise read-only owner review; no prototype, generated writes, tests or live Publish by Codex.

Gate: one coherent storage/copy boundary and manual baseline sequence are understood. Record: scope and sequence agreed; baseline and implementation pending.

### [ ] DMP.1 — User Publish And Manual Baseline

- [ ] User completes the existing Publish successfully.
- [ ] User copies the ready media folder into Working and Preview at the paths above.
- [ ] Record the user's confirmation, then agree the concise code change set before editing code/configuration.

Verification budget: user confirmation only. No Codex copy operation, full tree comparison, hashes or remote verification. The user owns the real publication/network effects and the approximately 43 MB manual copies.

Gate: the baseline Publish and both copies are user-confirmed, and the code cutover is approved. Record: awaiting user Publish/copy confirmation; no code changes started.

### [ ] DMP.2 — Storage And Publish Cutover

- [ ] Update configured media roots and explicit stage resolution through the existing storage owner.
- [ ] Switch local readers, intake/build output and other Working input consumers to Working media without changing their logical URLs/identities.
- [ ] Copy the existing prepared publication media selection from Working into Preview, route publication-produced media to the explicit publication owner and deploy from Preview.
- [ ] Preserve Preview media during snapshot replacement and remove old shared-root resolution without aliases or fallback paths.

Verification budget: focused changed-source lint/syntax and configuration/call-path review to catch incorrect stage bindings or old-root reads/writes. Select exact commands after inspecting the changed owners; expected cost is a short local static check, with no media writes or network effects. User manual local reads provide the presentation evidence. No new/changed tests, temporary regression scripts, broad profiles, whole-corpus builds or automated Publish are authorized.

Gate: storage owners and deployment inputs follow the new boundary, with the manual baseline retained. Record: not started.

### [ ] DMP.3 — Code Review

- [ ] Apply the mandatory [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) to the changed path/copy owners and reused helpers.
- [ ] Review normal publication, snapshot replacement and unchanged media for accidental Working writes, shared-root access, duplicate copying/scans and misplaced generation.
- [ ] Record findings and justified retained execution checks; rerun only evidence affected by fixes.

Verification budget: bounded source/diff review and already selected evidence affected by review changes; no extra audit or test infrastructure.

Gate: findings are resolved within this prerequisite's storage boundary. Record: not started.

### [ ] DMP.4 — Acceptance And Closeout

- [ ] Obtain user acceptance of ordinary/collection local media reads and the new publication ownership; record any later normal-use Publish observation separately from static review.
- [ ] Update [Source Organisation](../Source_Organisation.md), [Media And Asset Handling](../Media_And_Asset_Handling.md) and the owning configuration/publication documentation where their current contract changes.
- [ ] User retires the former shared `assets/media/` folder after acceptance; record completion without treating its retention as a runtime fallback.
- [ ] Mark this prerequisite complete, update its Planned Features entry and let Incremental Document Publish inherit the established media baseline.

Verification budget: reconcile user confirmation and focused implementation evidence, then review the documentation changes. No repeated Publish/build/copy solely for closeout. Commit, push and public deployment remain separate actions.

Gate: the cutover is accepted, durable owners are current and Incremental Document Publish has a clean Working/Preview media baseline. Record: not started.

## Follow-on

[Incremental Document Publish](Incremental_Document_Publish.md) supplies current/deleted media queue selections, completed upstream public artifacts, empty-queue no-op behavior and retained progress/manual retry. This prerequisite establishes physical media ownership without implementing those later contracts.

[[links|related links]]
