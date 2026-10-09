---
draft: false
doc_id: d-20261005-192051-a4df70
title: Empty Gallery Cleanup Delivery
added_date: "2026-10-05 20:20:51"
last_updated: "2026-10-05 20:38:13"
summary: Offer explicit deletion when saved Work membership removals empty a Gallery.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Empty Gallery Cleanup Delivery

## Current And Next State

Status: implementation complete; focused static checks and bounded code review passed. The user confirmed that adding and saving a Gallery named `test`, then removing it and saving, opened the cleanup prompt. At the user's request, both Gallery delete prompts now omit Series-association wording. The single and bulk Work Save owners return newly empty Gallery IDs from their loaded membership maps; the editor awaits sequential **Delete**/**Keep Gallery** confirmations through the existing Gallery delete owner. The durable Save workflow is updated. Next: reload the editor to review the revised copy; bulk, multiple-prompt, **Keep Gallery**, **Delete** and failure behavior remain manually unconfirmed. User acceptance is pending; retain this delivery until manual archive after acceptance. No runtime deletion, tests, browser automation, Catalogue Refresh, Docs/Search build, Publish, commit or push was performed by Codex.

This standalone delivery is parented to [Planned Features](../Planned_Features.md). [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) owns the shipped authoring workflow.

## Requirements And Deliverables

- Single and bulk Work Save report only Galleries whose accepted membership removals leave no members anywhere in the Catalogue. Pre-existing empty Galleries and Galleries with remaining unselected members are excluded.
- Offer cleanup only after the Work Save and its required local/editor completion succeed. A cancelled draft or failed/incomplete Save does not offer deletion.
- Open the existing Gallery delete confirmation directly, with its title and exact ID. Omit Series-association wording from both Gallery delete prompts. Offer **Delete** and **Keep Gallery**; process several newly empty Galleries sequentially.
- Deletion remains its own explicit canonical operation, using the existing exact Gallery revision and expected-member checks. Preserve the successfully saved Work changes on cancellation or cleanup failure. Reconcile deleted definitions and references into current editor state and invalidate Catalogue Refresh through its existing owner.
- Keep the check within the loaded membership maps; do not add a persisted count/index, new endpoint or automatic Gallery deletion.
- The separate Docs Viewer Galleries report is future work and is not implemented by this delivery.

## Process

Remove a Gallery from one Work or a bulk selection, then Save. If those saved removals leave the Gallery empty, the editor asks whether to delete it. **Keep Gallery** closes that prompt and retains the definition. **Delete** runs the existing Gallery delete operation and removes its Series associations. Each remaining newly empty Gallery receives its own prompt after the previous one completes.

## Delivery Steps

- [x] **EGC-0 — Readiness:** confirmed server-owned membership authority and existing Gallery deletion/modals. User authorization covers this bounded UI/server change; existing canonical data edits and the earlier status-message change remain separate. No scheduling dependency blocks implementation.
- [x] **EGC-1 — Implementation:** added the shared membership check, Save response fields, sequential cleanup prompts and durable authoring documentation. Required Work Save/local/editor completion precedes prompting; the existing Gallery revision/member validation and deletion-state reconciliation remain the write owner. No canonical Gallery or membership data were changed during implementation.
- [x] **EGC-2 — Focused verification:** `bin/lint-python` and explicit Python `-m py_compile` passed for `catalogue_galleries.py`, `catalogue_work_service.py` and `catalogue_bulk_service.py`; `bin/lint-js` passed for `catalogue-work-actions.js`, `catalogue-work-editor.js`, `catalogue-work-definitions.js`, `catalogue-work-definition-modal.js` and `catalogue-work-gallery-modal.js`. Scoped `git diff --check` and the new-document whitespace diagnostic emitted no errors. The focused sanitization scan found only existing token-interpolation variable names. These inexpensive local checks address source/module mistakes and write only ordinary lint/cache output; runtime coverage remains source review plus user manual use.
- [x] **EGC-3 — Code review:** checked before/after candidate derivation, remaining unselected members, single/bulk completion ordering, explicit deletion, cancellation/error propagation, state reconciliation and local-only ownership. No blocking finding remains. Narrowed the new deletion-success wording and message clearing to the cleanup flow so ordinary Series/Gallery definition actions retain their existing status behavior; reran its JavaScript lint and whitespace check. The new response field is required by the frontend; restarting Local Studio and reloading its browser assets adopts both sides together, without a compatibility alias.
- [x] **EGC-4 — Implementation closeout:** durable Save documentation reconciled and evidence limits recorded. The user confirmed the single-Work cleanup prompt with `test`; the requested Series-association copy removal passed focused JavaScript lint, whitespace checks and source review. Manual review remains pending for the revised copy, bulk prompts, multiple newly empty Galleries, **Keep Gallery**, **Delete** and failure behavior. Retain this delivery for manual archive after acceptance; no separate concept, architecture or verification document was created.

Gate: stop cleanup on incomplete Save or a failed cleanup operation; report the confirmed Work Save separately from later failure. Manual UI review belongs to the user. No tests or fixtures are created, changed or run; test work remains separately scoped under [Test Contract Discipline](../Test_Contract_Discipline.md).
