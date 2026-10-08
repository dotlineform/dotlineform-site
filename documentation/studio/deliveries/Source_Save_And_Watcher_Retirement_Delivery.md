---
draft: false
doc_id: d-20261008-184804-e937b1
title: Source Save And Watcher Retirement Delivery
added_date: "2026-10-08 18:48:04"
last_updated: "2026-10-08 19:24:55"
summary: Await document generation and fresh display during Source Save, retire the filesystem watcher, and keep infrequent media rebuilds explicit.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Source Save And Watcher Retirement Delivery

Status: complete, parented to [Planned Features](../Planned_Features.md). Implementation and bounded static review are complete. On 2026-10-08 the user confirmed normal and collection document authoring, Draft and starred changes, and reported that Save feels much quicker. This is qualitative user acceptance, not a timing benchmark. Failure paths and real media regeneration remain unexercised.

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

Edit a document in Source and choose **Save**. The waiting cursor and busy controls remain until its exact generated result is displayed or a specific failure is reported. Successful Save is silent; failure messages remain visible. This removes watcher scheduling and polling delays from the Save path; build and payload-read time still belong to the awaited operation.

For a deliberate external Markdown edit, use **Edit doc → Rebuild** for that document. After an infrequent edit to a registered media build source, run the explicit media-capable action selected during readiness, then rebuild/reload any affected document as required by that action. Persistent `.mmd` to SVG production is distinct from inline Mermaid content rendered as part of a document. Ordinary media intake continues through its existing owner.

## Delivery Steps

### SW-0 Readiness

- [x] Confirm Source Save persistence, exact-target document/Links generation and fresh reader-load ownership across ordinary and named-collection documents.
- [x] Check the broad application-write and local-service lifecycle boundaries for reliance on the watcher, including creation, deletion, draft changes, imports, media operations and Regenerate.
- [x] Confirm configured persistent media producers and select the simplest explicit rebuild action, recording its scope, extra effects and occasional cost separately from normal Save.
- [x] Identify watcher-exclusive code, configuration, documentation and test references; apply the separate test-work policy to any affected test changes.

Gate: promote to planned only when watcher removal leaves application writes complete and the rare media workflow is concrete. If an operation has an unowned required result, or media support needs a broader new subsystem, resolve that boundary before implementation. Readiness is read-only and does not authorize test changes.

Record: complete. Source Save and Draft were the application-write gaps; both now reuse the exact document/Links rebuild owner. Creation, deletion, assignment, imports, media intake and Regenerate retain awaited output owners. Local Studio owned watcher startup/liveness. The user selected the existing **Rebuild docs and Search** action for rare persistent-media edits: it regenerates referenced Mermaid SVGs across configured owners with producer verification, plus all documents, Links, Recents and Search. Unreferenced `.mmd` files are not rendered; total cost is unmeasured and includes all document/Search work plus one render per referenced diagram. No broader media subsystem is needed. Watcher-only code/configuration is removed; [Testing](../Testing.md#source-save-and-watcher-retirement) records untouched stale tests/profiles.

### SW-1 Awaited Source Save

- [x] Invoke the existing exact-target rebuild owner after a successful canonical source write, with document/Links scope and media/Search excluded.
- [x] Carry saved-source and build outcomes through the service response; retain exact target validation and report partial completion accurately.
- [x] Await a forced fresh reader load before releasing Save busy state, preserving normal retained navigation behavior.

Verification budget: inspect the bounded service/editor diff and failure paths; run changed-source Python/JavaScript lint, relevant Python syntax checks and whitespace checks. These are read-only checks expected to take seconds. User manual review covers an ordinary and an authorable collection Save, updated display and busy completion after service restart and browser refresh. No automated tests or temporary regression scripts are included; any additional executable evidence requires a justified selection under [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md).

Gate: Save no longer needs watcher or polling timing to show its result; partial failures remain distinguishable. Do not widen Save into workspace rebuild, media generation, Search or publication.

Record: complete. Persistence and generation outcomes remain distinct, including an unchanged-source Save that still rebuilds. The editor marks persisted source clean on generation failure and awaits a fresh exact payload, Source exit, retained-mount rendering and current-entry capture on success. Busy release follows completion/failure. Changed-source Python/JavaScript lint, Python syntax, shell syntax and whitespace checks passed. The routine success message was removed at the user's request, with affected JavaScript lint and whitespace checks passing. The user accepted normal and collection document authoring; failure branches remain unexercised.

### SW-2 Retire Watcher And Confirm Explicit Media Workflow

- [x] Close any application-write generation gaps identified during readiness through their existing owners.
- [x] Remove watcher startup, monitoring, configuration and suppression code without changing unrelated write semantics or retaining compatibility paths.
- [x] Document and, only if agreed necessary, expose the selected explicit media producer invocation. Preserve configured source/generated media ownership and producer verification.
- [x] Update [Development Checklist](../Development_Checklist.md), [Docs Viewer Runtime](../Docs_Viewer_Runtime.md), [Source Editor Endpoints](../Source_Editor_Endpoints.md), [Source Editor Scripts](../Source_Editor_Scripts.md), [Source Organisation](../Source_Organisation.md) and [Media And Asset Handling](../Media_And_Asset_Handling.md) where the shipped contract changes.

Verification budget: scoped caller/configuration review, changed-source lint/syntax and shell syntax where relevant. User manual review confirms Local Studio startup and the selected explicit rebuild workflows with the watcher absent. Record the selected media action's real write scope and cost before running it; do not run a full media/Search Build merely to fill verification evidence. If a shared/public runtime owner changes, project it with `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`.

Gate: no required application result depends on the retired watcher, and the rare media rebuild has an explicit usable route without adding work to normal Save. Test/profile changes require their own approved specification; do not retain production compatibility code for stale tests.

Record: complete. Draft generation is awaited; watcher process/startup/liveness, service settings/schema, suppression storage calls and exclusive modules are retired without aliases. Existing write validation and mutation-specific recovery remain. Durable runtime, Source, build, identity, media and runner guidance is updated; [Source Organisation](../Source_Organisation.md#explicit-external-edit-and-media-rebuilds) owns explicit external editing and the user-selected media action. Browser polling is retained. Five shared runtime files were projected to `site/`; projection check and deploy-root validation passed. JSON parsing, changed-source lint/syntax and shell syntax passed. Local-service startup and real media production were not separately itemised in the user's acceptance; no full media/Search Build ran.

### SW-3 Code Review

- [x] Review exact target/capability validation, single-build ownership, busy completion, fresh reads and all partial-failure branches.
- [x] Review watcher/suppression removal, local-service lifecycle, media isolation, documentation and any required public projection for omissions or duplicated behavior.
- [x] Resolve findings and rerun only affected checks.

Gate: no material unresolved finding within this delivery; record manual acceptance and unexercised failure paths explicitly.

Record: code review complete. Reviewed exact target/capability validation, single-build scope, committed metadata on partial failure, clean-buffer handling, busy lifetime, fresh generated reads, retained route/history/position, source-path confinement, preserved import/delete recovery and suppression caller removal. Corrected rendered-mode unmount rejection handling so awaited Save reports display failure instead of remaining pending, and guarded malformed partial responses so they retain an error outcome. The edited service schema also dropped its obsolete `import_staging` requirement, matching the existing current defaults. Retired automatic external-edit timestamp capture is documented. No material source-review finding remains. User acceptance covers normal and collection document authoring, Draft and starred changes; static review does not establish live failure recovery.

### SW-4 Closeout

- [x] Record the complete delivered outcome, selected evidence and user manual acceptance.
- [x] Confirm durable owners describe the new Save and explicit external-edit/media workflow, and update Planned Features.
- [x] Reassess readiness of the optional polling delivery and recommend retaining or retiring this delivery document once its routing value is exhausted.

Gate: Source Save displays its completed result, application writes work without a filesystem watcher, and rare media regeneration remains explicit. Publish, deployment, commit and push remain separate actions.

Record: complete. On 2026-10-08 the user reported successful checks of normal and collection documents, changing Draft and starred state, and a noticeably quicker experience. Detailed route/history/reading-position cases, creation/import/deletion/Regenerate, explicit external-edit Rebuild, partial failures and real persistent-media regeneration were not separately confirmed. The media action's configured coverage and extra writes were reviewed and selected by the user; actual runtime cost remains unmeasured. Existing lint/syntax, scoped source review, public runtime projection and site validation evidence is retained without repeating it for status-only closeout. No automated tests, browser automation, media/Search Build, Publish, deployment, commit or push were performed by Codex. Browser polling retirement now has its accepted prerequisite, but action-to-view coverage still needs read-only readiness before implementation. Retain this delivery while it routes that optional follow-on and the evidence limits; recommend manual archival when that routing value is exhausted.

## Follow-on

[Browser Polling Retirement Delivery](Browser_Polling_Retirement_Delivery.md) is optional and follows this delivery. It removes the browser's recurring Working index/document reads only after relevant application actions explicitly refresh their affected views. This delivery remains complete with browser polling retained.
