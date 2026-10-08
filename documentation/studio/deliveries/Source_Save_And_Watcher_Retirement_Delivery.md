---
draft: false
doc_id: d-20261008-184804-e937b1
title: Source Save And Watcher Retirement Delivery
added_date: "2026-10-08 18:48:04"
last_updated: "2026-10-08 18:48:04"
summary: Await document generation and fresh display during Source Save, retire the filesystem watcher, and keep infrequent media rebuilds explicit.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Source Save And Watcher Retirement Delivery

Status: proposed, parented to [Planned Features](../Planned_Features.md). The direction is agreed; implementation has not started. The current persistence-only Save and watcher rules remain in force until this delivery replaces them.

## Requirements

- Source Save completes as one awaited operation: validate and persist canonical source, rebuild the exact document and its Related links, fetch its fresh generated payload, display it, then release busy state. Returning to the rendered view must show the completed result without waiting for a watcher or browser polling interval.
- Reuse the existing document-only rebuild owner used by **Edit doc → Rebuild** for ordinary and authorable named-collection documents. Normal Save excludes Search, Publish and registered media production; it uses already prepared media.
- Retire the filesystem watcher rather than preserving it as an optional background mode. Normal authoring happens through application operations. Deliberate external Markdown edits require an explicit document Rebuild or an appropriately scoped full Build.
- Preserve required generation for other application writes when the watcher is absent. Each operation owns its required output before reporting completion; existing explicit Refresh, Regenerate, Search and Publish boundaries remain separate.
- Keep infrequent persistent build-source media regeneration behind an explicit manual action. Normal document Save must incur no media scans, hashes, producer readiness checks, change detection or rendering overhead.
- Keep browser polling in this delivery. Save must already load its own fresh result; removing polling is an optional, separately reviewable follow-on.

## Deliverables

- Source Save service integration with the existing exact-target document/Links builder, plus editor handling that awaits the fresh rendered display and retains the correct route, history and reading position.
- Clear outcomes for source-write, rebuild and reader-load failures. A failure before persistence preserves the unsaved draft. A rebuild failure after persistence reports that the source was saved but generation failed, and marks that persisted source as clean. A later load failure reports that saving and generation completed but display failed. Recovery uses the existing explicit Rebuild or reload; no automatic source rollback, retry queue or backup layer is added.
- Removal of the watcher process, startup/liveness handling, configuration knobs, suppression machinery and exclusive callers. No compatibility command, environment alias or replacement background monitor remains.
- A confirmed, documented manual media rebuild workflow using the smallest suitable existing capability. Prefer an existing media-capable Build or producer command over a new UI or endpoint. The current **Rebuild docs and Search** route invokes the full builder with media production enabled and Search included; readiness must establish its actual configured media coverage and whether its occasional broader cost is acceptable. If it is unsuitable, agree a minimal explicit invocation of the existing producer and its exact ownership boundary before implementation.
- Current durable Source Save, runtime, media and local-service documentation, including removal of instructions that rely on automatic external-edit detection.

## Process

Edit a document in Source and choose **Save**. The waiting cursor and busy controls remain until its exact generated result is displayed or a specific failure is reported. This removes watcher scheduling and polling delays from the Save path; build and payload-read time still belong to the awaited operation.

For a deliberate external Markdown edit, use **Edit doc → Rebuild** for that document. After an infrequent edit to a registered media build source, run the explicit media-capable action selected during readiness, then rebuild/reload any affected document as required by that action. Persistent `.mmd` to SVG production is distinct from inline Mermaid content rendered as part of a document. Ordinary media intake continues through its existing owner.

## Delivery Steps

### SW-0 Readiness

- [ ] Confirm Source Save persistence, exact-target document/Links generation and fresh reader-load ownership across ordinary and named-collection documents.
- [ ] Check the broad application-write and local-service lifecycle boundaries for reliance on the watcher, including creation, deletion, draft changes, imports, media operations and Regenerate.
- [ ] Confirm configured persistent media producers and select the simplest explicit rebuild action, recording its scope, extra effects and occasional cost separately from normal Save.
- [ ] Identify watcher-exclusive code, configuration, documentation and test references; apply the separate test-work policy to any affected test changes.

Gate: promote to planned only when watcher removal leaves application writes complete and the rare media workflow is concrete. If an operation has an unowned required result, or media support needs a broader new subsystem, resolve that boundary before implementation. Readiness is read-only and does not authorize test changes.

Record: pending. Initial source inspection identifies the exact document rebuild service as the reuse point, Local Studio as the watcher lifecycle owner, and watcher suppression calls in shared write/rebuild and draft services. The full Build is a candidate for rare media regeneration; its suitability is not yet agreed.

### SW-1 Awaited Source Save

- [ ] Invoke the existing exact-target rebuild owner after a successful canonical source write, with document/Links scope and media/Search excluded.
- [ ] Carry saved-source and build outcomes through the service response; retain exact target validation and report partial completion accurately.
- [ ] Await a forced fresh reader load before releasing Save busy state, preserving normal retained navigation behavior.

Verification budget: inspect the bounded service/editor diff and failure paths; run changed-source Python/JavaScript lint, relevant Python syntax checks and whitespace checks. These are read-only checks expected to take seconds. User manual review covers an ordinary and an authorable collection Save, updated display and busy completion after service restart and browser refresh. No automated tests or temporary regression scripts are included; any additional executable evidence requires a justified selection under [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md).

Gate: Save no longer needs watcher or polling timing to show its result; partial failures remain distinguishable. Do not widen Save into workspace rebuild, media generation, Search or publication.

Record: not started.

### SW-2 Retire Watcher And Confirm Explicit Media Workflow

- [ ] Close any application-write generation gaps identified during readiness through their existing owners.
- [ ] Remove watcher startup, monitoring, configuration and suppression code without changing unrelated write semantics or retaining compatibility paths.
- [ ] Document and, only if agreed necessary, expose the selected explicit media producer invocation. Preserve configured source/generated media ownership and producer verification.
- [ ] Update [Development Checklist](../Development_Checklist.md), [Docs Viewer Runtime](../Docs_Viewer_Runtime.md), [Source Editor Endpoints](../Source_Editor_Endpoints.md), [Source Editor Scripts](../Source_Editor_Scripts.md), [Source Organisation](../Source_Organisation.md) and [Media And Asset Handling](../Media_And_Asset_Handling.md) where the shipped contract changes.

Verification budget: scoped caller/configuration review, changed-source lint/syntax and shell syntax where relevant. User manual review confirms Local Studio startup and the selected explicit rebuild workflows with the watcher absent. Record the selected media action's real write scope and cost before running it; do not run a full media/Search Build merely to fill verification evidence. If a shared/public runtime owner changes, project it with `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`.

Gate: no required application result depends on the retired watcher, and the rare media rebuild has an explicit usable route without adding work to normal Save. Test/profile changes require their own approved specification; do not retain production compatibility code for stale tests.

Record: not started.

### SW-3 Code Review

- [ ] Review exact target/capability validation, single-build ownership, busy completion, fresh reads and all partial-failure branches.
- [ ] Review watcher/suppression removal, local-service lifecycle, media isolation, documentation and any required public projection for omissions or duplicated behavior.
- [ ] Resolve findings and rerun only affected checks.

Gate: no material unresolved finding within this delivery; record manual acceptance and unexercised failure paths explicitly.

Record: not started.

### SW-4 Closeout

- [ ] Record the complete delivered outcome, selected evidence and user manual acceptance.
- [ ] Confirm durable owners describe the new Save and explicit external-edit/media workflow, and update Planned Features.
- [ ] Reassess readiness of the optional polling delivery and recommend retaining or retiring this delivery document once its routing value is exhausted.

Gate: Source Save displays its completed result, application writes work without a filesystem watcher, and rare media regeneration remains explicit. Publish, deployment, commit and push remain separate actions.

Record: not started. This planning change runs no application build, media generation, Search or publication.

## Follow-on

[Browser Polling Retirement Delivery](Browser_Polling_Retirement_Delivery.md) is optional and follows this delivery. It removes the browser's recurring Working index/document reads only after relevant application actions explicitly refresh their affected views. This delivery remains complete with browser polling retained.
