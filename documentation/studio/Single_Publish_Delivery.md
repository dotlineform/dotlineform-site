---
draft: false
doc_id: d-20260926-233236-bcd2e1
title: Docs Viewer Stage Simplification And Single Publish - Delivery
added_date: "2026-09-26 23:32:36"
last_updated: "2026-09-27 11:52:05"
summary: Keep Working and Preview inside one Publish pipeline, remove stage context from Docs Viewer readers and authoring, retain preview/ as inspectable output, and review through site-preview.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Docs Viewer Stage Simplification And Single Publish - Delivery

Status: complete. SP-0–SP-7 are closed with representative Manage acceptance, user-reported Publish success, completed-output/site-preview checks, bounded code review and durable documentation updates. Works editor, package operations, saved-state conversion, live failure recovery and independent R2 verification remain unexercised; no measured speedup is claimed. Retain this delivery for manual archival; no documents were deleted.

## Requirements

Publishing after editing one or two documents should be a simple, direct action. The current Prepare Preview, Docs Viewer Preview review, Publish change preview and confirmation sequence makes the operation feel disproportionate to the edit. Advance document counts and lists of file/folder changes are unnecessary for this workflow. The author wants to review the result through the site-preview server.

Retain the work and ownership boundaries established by preparation and publication. `preview/` remains a complete, physical set of publishable documents and supporting reader files, organised for Docs Viewer and available independently of the repository destination. Its layout is useful during development: the author can compare Working management output, such as `manage-manifest.json`, with prepared reader output, such as `manifest.json`, without locating the repository projection beneath `site/assets/`. Other consumers may use the prepared artifact; this delivery adds no new consumer or distribution framework.

Remove Preview as a Docs Viewer browsing surface and remove explicit stage context from the rest of Docs Viewer. One Publish button must prepare and validate the latest eligible content, complete `preview/`, and immediately distribute that same snapshot to the configured repository and public-media destinations. The operation has no intermediate user confirmation, change-review modal or requirement to open Preview. Automatic validation and sequencing remain necessary: distribution starts only after successful preparation, and the UI stays busy until the complete outcome is known.

### Stage Ownership

Working and Preview remain meaningful inside the publishing workflow and its configured storage boundary: `working/` → `preview/` → repository, with referenced assets distributed to their configured destinations. The Publish caller supplies no stage selection; the owning pipeline resolves its fixed source, prepared output and destination from configuration.

The rest of Docs Viewer has one local authoring and reading context. Manage mode at `/docs/` always uses the configured `working/` source/generated output and shared assets. Site-preview serves the repository's public site output and its configured public media, using the same reader composition as the deployed site. Neither reader chooses a publishing stage.

| Owner | Content and authority |
| --- | --- |
| Docs Viewer Manage at `/docs/` | The single configured Working workspace, shared local assets and local management capabilities. |
| Site-preview and the deployed site | Repository/public reader output and configured public media, without local management capabilities. |
| Publish pipeline | The configured `working/` → `preview/` → repository flow and referenced asset distribution. |

Documents, collections, reports, media, links, semantic targets, searches and UI state must not carry or choose a Working/Preview stage. Remove explicit stage parameters, stage-qualified URLs, stage-dependent target identities, reader-payload discriminators and browser state that exist to support that choice. Do not replace them with an optional stage parameter defaulted to Working or a compatibility branch that accepts the old context.

Exact document, collection, report-host and asset identities remain explicit. The local service resolves its one configured workspace; a public reader resolves its configured repository/public assets. Local management availability and public read-only behaviour remain separate capability and deployment concerns, without a `published` stage discriminator in ordinary reader contracts. Public URLs retain their existing public destinations.

Preparation and distribution may retain internal stage/role information in storage configuration, build context, completion manifests and provenance where it identifies `working/` or `preview/`. Keep that information at the publication boundary rather than threading it through general document/media/link APIs. The prepared artifact remains consumable independently of the repository without requiring each reader to understand publishing stages.

### Manage-Wide Change Boundary

Removing runtime stage context reaches across most of Manage mode. The implementation must account for the application shell and navigation; document loading and caching; collection/report readers; Source/metadata editing and management actions; media and Catalogue readers; links, backlinks and semantic targets; Search/Recents; API clients and service request validation; capabilities; and browser selection, bookmark and panel state wherever stage is currently part of their contract. This list names the affected owners, not a requirement to redesign their independent behaviour.

Treat caller, service, payload and state changes as a coordinated contract change. Removing the selector alone, or leaving `working` threaded through every function as a constant, does not complete this delivery. The owning local or public runtime supplies its configured readers and capabilities once; individual documents and controls do not resolve a stage. Readiness must account for this breadth and choose coherent implementation batches that preserve usable callers without transitional aliases. Exact file inventory and batch details belong to the implementation steps.

The agreed implementation is direct removal. Do not introduce an intermediate step that pins stage arguments to `working`, adds defaults, or supports both old and new runtime contracts. Batches organise the implementation and review of one coordinated cutover; they do not create a temporary compatibility mode or a later stage-removal delivery. Correct missed callers at their owner and let invalid uses fail visibly instead of restoring stage plumbing to conceal them. Working/Preview references required by the publication and storage boundary remain intentional.

### Preserved Boundaries

- Working source and generated output retain their authoring, management and build responsibilities. Publish must use fresh captured inputs; it cannot blindly distribute an older snapshot or stale Working document output.
- Preparation retains the existing explicit `draft` and `unpublishable` rules, hierarchy exclusions, exact collection-host ownership and collection customisations. Distribution consumes the complete prepared set without applying another eligibility filter.
- Catalogue JSON remains selected by its declared artifact inventory, independently of document membership. Save retains canonical record, local media preparation, dimensions and version ownership.
- Existing Working Search and Recents are captured and copied unchanged under their current lifecycle. This delivery does not rebuild them automatically or change their coverage/freshness policy.
- `preview/` retains its organised reader files, Catalogue JSON, completion manifest, provenance and exact shared asset references. Shared current media stays in the existing asset store; Preview does not gain media copies or historical versions.
- Public URL projection remains a distribution concern. Retire reader-facing stage fields, including the former `published` discriminator, while preserving document identity, public routes and read-only isolation. The repository remains a downstream consumer of Preview.
- Git commit, push and public deployment remain separate explicit actions. R2 transfers remain part of Publish, with the existing accepted possibility that replacement public media becomes visible before repository deployment.

### Performance And Failure Behaviour

Combining UI actions must also remove redundant processing. Carry captured inputs, the validated snapshot and destination comparison results through the same awaited operation. Remove work whose only purpose was to reconstruct and compare a plan across separate user confirmations. Compare media once for the operation where the same evidence remains valid, then transfer changed assets and verify those transfers; do not repeat full unchanged-asset comparisons merely because execution crossed an internal function boundary.

This is a synchronous single-user workflow: edits are unavailable until the operation completes. Source freshness means capturing current inputs at the start of each Publish. Carry those inputs, the completed snapshot and destination comparisons through the operation without concurrency checks, repeated input/snapshot scans or file-metadata freshness checks between internal calls. Preserve exact identity, valid inputs/destinations, missing-asset errors and verification of completed output/transfers. Fail visibly on errors. This delivery promises removal of identified duplication, not a particular duration or a new incremental-build architecture.

Preparation failure prevents distribution. Existing snapshot replacement and completion-receipt semantics remain. Repository and R2 distribution are not an atomic transaction; a failure must identify incomplete publication without reporting overall success. A successfully prepared snapshot remains available for inspection even when distribution fails. Recovery uses the existing owners and a fresh Publish attempt, without automatic rollback trees, background retries or a pending-publication ledger. Publish does not add automatic shared or remote asset deletion.

## Deliverables

- One Publish UI action with one awaited preparation/distribution operation and concise busy, completion and error feedback. No advance change-count report or file/folder confirmation list is required.
- A completed `preview/` artifact followed by distribution of that exact result, retaining preparation and distribution as distinct internal responsibilities.
- Removal of the separate Prepare Preview UI action and Docs Viewer Preview browsing/navigation. Preview storage and internal publication configuration remain.
- Stage-independent document, collection, report, media, link, semantic-target, reader-payload, request, cache and UI-state contracts across Manage mode. `/docs/` resolves Working through its owner; site-preview/public readers resolve repository/public output through theirs. Keep exact content identity and local/public capability boundaries; remove redundant stage arguments and selectors across active callers and producers.
- Removal of redundant plan reconstruction, snapshot reads and media comparisons that the combined operation no longer needs. No persistent cache, compatibility alias or second publication implementation is introduced.
- Focused evidence for the combined operation, manual site-preview review and bounded code review, followed by current durable workflow documentation. Tests and fixtures require a separately approved specification before modification.

The existing [Source Organisation](Source_Organisation.md), [Catalogue Deployment](Catalogue_Deployment.md) and [Catalogue Save And Publish Action Map](Catalogue_Save_And_Publish_Action_Map.md) identify current storage and operation owners. This delivery changes their split user workflow and the runtime stage-context model; they must describe shipped behaviour until implementation is complete.

## Process

1. Edit and save in Docs Viewer Manage at `/docs/`, backed by the configured `working/` workspace and shared assets. No stage is selected or supplied by the UI.
2. Click Publish. The server captures the eligible inputs and saved artifacts, prepares the complete Preview, validates it and records completion.
3. Within that same action, distribute the completed snapshot and referenced current assets to the configured repository and R2 destinations. Retain busy state throughout; no intermediate user gate appears.
4. Report the complete outcome. The author views or refreshes the site-preview server to inspect the actual public routes, repository files and public assets. `preview/` remains available for direct development inspection and other consumers.
5. Commit, push and deploy separately when ready.

## Delivery Steps

The gates below are development checkpoints, not gates inside the finished Publish workflow. Follow [Planned Features](Planned_Features.md) and the [Development Checklist](Development_Checklist.md). Keep each record to status, changed owners, selected evidence, deviations and gate outcome.

### SP-0 — Readiness

- [x] Confirm the agreed scope against the current preparation, snapshot, distribution, runtime identity, UI and storage owners. Preserve unrelated work already in progress.
- [x] Confirm how the combined operation carries a completed snapshot into distribution. Distinguish internal publication stage/role information from runtime context to remove across documents, media, links, reports, payloads and UI.
- [x] Account for active service and shared/public callers so removing stage context preserves exact content identity and public read-only isolation. Keep this a broad owner review, not an exhaustive implementation inventory.
- [x] Confirm the Manage-wide change boundary, including request, cache and saved-state ownership, and choose coherent producer/consumer batches with the UI cutover. Do not treat this as only a Publish-button change or use compatibility defaults to bridge unfinished callers.
- [x] Preserve the direct-removal decision in the implementation sequence: no interim constant-stage pass, dual contract or deferred cleanup phase.
- [x] Confirm the implementation sequence and credible failure boundaries. Identify genuine blockers without fixing exact schemas, producing code or expanding the delivery.

Verification budget: concise read-only owner inspection; no builds, publication runs or executable test work.

Gate: present the bounded readiness result and obtain implementation approval. Record: readiness complete and SP-1 approved on 2026-09-27. No implementation blocker identified by the bounded owner review. The worktree was clean before the readiness-record update.

The existing preparation, snapshot and distribution owners (`docs_prepare_preview.py`, `docs_preview_snapshot.py`, `docs_deploy_repo.py` and `docs_public_media_reconciliation.py`) provide the required seams. SP-1 composes capture/build, verified snapshot completion and distribution in one awaited service operation, carrying the completed artifact and its identity forward. SP-2 removes confirmation-related replanning and repeated media comparisons while retaining fresh input capture, snapshot byte verification, destination validity and changed-transfer verification. The initial owner review found distribution replanning on apply and repeated media preflight/comparison; SP-2 records their removal. This is source evidence, not a measured performance result.

Implementation sequence remains SP-1 then SP-2, followed by the coordinated SP-3/SP-4 runtime and UI cutover. Review batches cover workspace/service/payload producers with their provider/API consumers; feature targets and caches across documents, collections/reports, authoring, media/Catalogue, links/semantic targets and discovery; then route, capability, saved-state and control retirement. SP-3 and SP-4 must land as one usable contract, without a runnable intermediate constant-stage or dual-contract mode. Public route composition already separates management capability; preserve that separation while removing reader stage discriminators. Publication/storage configuration, captured build context and completion provenance keep their internal roles.

Saved-state inspection found distinct Working/Preview/public ownership plus older one-time Analysis/published conversions. Specify the exact state conversion or retirement in SP-3 before changing it; preserve exact document/collection identities and never silently merge Preview with Working or public state. Existing conversion code is part of that review, not justification for continuing stage aliases.

Failure boundaries remain explicit: capture/build failure prevents distribution; failure during snapshot replacement leaves no valid completion receipt; distribution failure retains the completed snapshot and reports incomplete publication because repository and R2 effects are not atomic. Readiness evidence was read-only source/configuration and caller inspection; only this delivery record changed during SP-0.

### SP-1 — Compose One Awaited Publish Operation

- [x] Introduce the single Publish entry point by composing the existing preparation and distribution owners. Resolve the fixed `working/` → `preview/` → repository pipeline internally, without a stage argument from the caller.
- [x] Prepare and complete `preview/`, then pass that exact completed result into distribution without another user-reviewed plan or another source build.
- [x] Preserve eligibility, output identity, artifact selection, freshness checks, failure reporting and synchronous completion. Retain the prepared artifact independently of the repository result.

Verification budget: changed-source lint/syntax and source review of sequencing and failure paths. Select any existing service checks only after inspecting their coverage and cost; specify test changes separately under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: review the coherent service change and its evidence before removing the old UI workflow. Record: implemented and continuation to SP-2 approved on 2026-09-27.

`docs_publish.py` now owns `POST /docs/publish` with an empty-object request and one synchronous preparation/distribution call. The management route registry and dispatcher expose it through the existing management-enabled and local-origin checks; dry-run and caller-supplied stage/confirmation fields are rejected. Preparation and snapshot completion return a `CompletedPreview` carrying verified bytes and the completion receipt. The distribution owner builds one plan from that object and applies it without another user confirmation or source build. Existing split endpoints use the same extracted owners until their SP-4 UI/route retirement; no runtime stage-default or alias was introduced.

The response distinguishes preparation failure from incomplete distribution, retains the completed Preview revision after preparation succeeds, and reports overall success only after distribution completes. Snapshot completion checks the written bytes/receipt. Existing eligibility, Catalogue inventory, unchanged Search/Recents copying, repository byte verification and media transfer ownership remain in place. Scoped source review found and corrected insufficient error detail so missing-asset and media/lineage failures retain actionable reasons. SP-2 removes the initial repeated snapshot validation. Full delivery code review remains SP-6.

Verification: explicit `bin/lint-python` and Miniconda `python3 -m py_compile` passed for `docs_publish.py`, `docs_prepare_preview.py`, `docs_preview_snapshot.py`, `docs_deploy_repo.py`, `docs_management_routes.py` and `docs_management_service.py`; `git diff --check` passed. These checks are local static evidence, with only ignored bytecode writes and no service/network/publication effects. No behavioral test was selected: the inspected Deploy Repo tests still use retired scope configuration and publication contracts. No tests/fixtures, browser/runtime projection, generated content, repository publication output or R2 state changed, and no live Publish, build, commit or push ran.

SP-2 owns removal of the initially retained replan, snapshot rereads and media preflight/apply comparisons. No timing improvement is claimed from this service-only step.

### SP-2 — Remove Duplicate Processing

- [x] Reuse captured input, validated snapshot and destination-comparison results within the combined operation; remove confirmation-related replanning and redundant rereads.
- [x] Use the media comparison result to perform required transfers and verify changed destinations, avoiding repeated full scans of unchanged assets.
- [x] Retain checks with a distinct integrity purpose and record any remaining expensive work. Do not weaken the publication rules or introduce persistent caches to obtain a faster result.

Verification budget: focused changed-source checks and a bounded call-path review showing which repeated work was removed. Runtime timing belongs to the agreed representative run in SP-5; no benchmark harness or synthetic regression script is authorised.

Gate: review removed duplication and preserved checks; identify remaining costs without expanding into incremental rebuilding. Record: implemented and continuation to coordinated SP-3/SP-4 approved on 2026-09-27.

Preparation captures inputs and the previous Preview once, selects eligibility once and builds once. It reuses loaded document text for unchanged source projection and passes captured previous-output bytes into snapshot replacement. Removed the post-build eligibility replan and within-operation source/configuration/saved-artifact freshness scans. Snapshot writing verifies final files once and the receipt separately; distribution consumes that completed object without rereading Preview. The Development Checklist now states the synchronous no-concurrent-edit contract explicitly.

Media planning returns its comparison report and exact transfer bindings. Distribution carries that plan into apply; apply performs no new listing, destination comparison or unchanged-asset read. Each remote family receives one listing pass during comparison. Only changed assets are read for transfer and verified afterward, reusing the remote adapter's existing post-write stat instead of issuing another HEAD. No metadata freshness checks, persistent cache, asset copies/history, cleanup or retry mechanism were introduced. Existing split confirmation endpoints still validate their reviewed revisions across separate requests until their SP-4 retirement; the combined Publish path does not use those endpoints.

Source review confirmed the combined call path and preserved input/path/identity validation, missing-asset failure before distribution, final Preview/receipt and repository byte verification, transferred-media verification, and incomplete-result reporting. Error aggregation uses failure status so an empty exception message cannot turn an error into success. Five changed Python owners are `docs_prepare_preview.py`, `docs_preview_snapshot.py`, `docs_public_media_reconciliation.py`, `docs_deploy_repo.py` and `docs_publish.py`.

Verification: explicit `bin/lint-python`, Miniconda `python3 -m py_compile` and `git diff --check` passed. Evidence is static only; no tests/fixtures, builds, live Publish, R2 operation, runtime projection, commit or push ran. Remaining costs are the complete captured build, initial source/previous-output reads, one full media comparison, changed-asset transfer reads and output verification. No measured timing improvement is claimed. Next: coordinated runtime-stage removal and UI cutover in SP-3/SP-4.

### SP-3 — Remove Runtime Stage Context

- [x] Remove stage arguments, discriminators and branching across the affected Manage owners, including document/collection/report readers, authoring actions, media/Catalogue, links, semantic targets, discovery and API/service boundaries. Keep publication-only roles within preparation/distribution and storage configuration.
- [x] Update affected payload producers and consumers together, including public reader contracts, stage-qualified URLs and target/state identities. Preserve exact document/collection/report-host/asset identity and public read-only isolation.
- [x] Make `/docs/` Manage readers and writes resolve the single Working workspace through their owner. Make site-preview/public readers use repository/public destinations and their own capabilities. Remove stage from request construction, validation and cache identities where it supplied that choice; preserve necessary document, collection and runtime ownership.
- [x] Remove the runtime stage contract directly across active producers, service/client contracts and state consumers. Do not introduce even an interim constant-stage pass, optional stage default, alias or fallback read. Fix missed callers without reinstating the retired contract.
- [x] Account for existing browser state explicitly without silently merging distinct document or collection identities. Any necessary state conversion must be specified at this step; it must not become a continuing compatibility layer.

Verification budget: focused source, syntax and lint checks plus the smallest justified existing service/payload evidence after inspecting its coverage. Test or fixture changes require their own approved specification. Required shared/public runtime projection checks apply when this step changes projected files.

Gate: review the coherent producer/consumer change and confirm that only the publication boundary retains stage roles. Record: implementation and source review complete with SP-4; representative manual acceptance remains in SP-5.

Saved-state decision: a one-time IndexedDB upgrade converts exact Working bookmark records to the Manage owner, preserving document IDs and user metadata and aborting on a key collision. A one-time panel conversion moves the exact Working panel preference to Manage and fails visibly on conflicting destination data. Public and Review state retain their separate owners. Retired Preview and older Analysis state remain stored but unused; they are not merged into Manage or consulted by runtime lookups. Remove the previous Analysis conversion paths. Selected documents continue to use explicit document/collection identity without a stage.

Implementation: the configured local owner now supplies document, collection, source, media, Catalogue, link and report readers without caller-selected stages. Managed targets retain exact document/collection identity. Browser configuration uses one workspace, capabilities use one workspace plus Publish, and local/public links retain their distinct destinations. Preview browsing handlers and the split preparation/distribution endpoints are retired; internal preparation, physical Preview output, distribution and storage provenance remain. Package metadata and Review producers/readers use their new contract directly; the user confirmed that no existing import/export packages require migration.

Generated-output reconciliation was necessary because the reader and builder contracts changed globally. Seven authored Working-qualified links in four configured source documents were updated without changing their document or report-host IDs. The obsolete generated Links records and semantic-token index were replaced once through their existing builders. The ordinary build and all five configured collections completed with zero warnings: 5,211 documents, 5,184 relationship records, and a completion manifest covering 10,415 generated files. Commands used `build_docs.py --stage working --write --skip-media-builds --skip-recent --skip-browser-config`, with `--collection` for Works, Concepts, Processing, Moments and Catalogue, followed by the owning Links aggregate and completion-manifest writers. Search and Recents were preserved; no media producer, Preview preparation or distribution ran. Browser configuration was regenerated through its owner, including the already configured public Works title, Context.

Evidence: changed Python and JavaScript lint, Python compilation, service/package/Review/Publish imports, and whitespace checks passed. The existing read-only `PYTHONPATH=. python3 docs-viewer/services/docs_broken_links.py --json` diagnostic completed with zero issues and zero unavailable generated sources after reviewing its local-file-only read boundary. No tests, fixtures or browser automation were changed or run. These checks do not establish manual UI, saved-state conversion, live Publish, R2 or failure-path acceptance.

### SP-4 — Simplify The Docs Viewer Workflow

- [x] Expose Publish and remove the separate Prepare Preview action, advance change-review dialog and confirmation list.
- [x] Remove Working/Preview selection, labels and stage-qualified navigation/state from the UI. Remove Preview browsing routes, capabilities and handlers after checking their callers; retain internal artifact production and consumers.
- [x] Keep the operation busy through preparation and distribution, with concise progress, completion and useful error messages. Use site-preview as the manual review surface.
- [x] Update the tracked shared/public runtime projection where required by the canonical-to-site inventory.

Verification budget: focused JavaScript/Python checks as applicable. For projected runtime changes, inspect `bin/site-code-update` output and run its check plus `bin/site-validate`. UI presentation and interaction are manual review; browser automation is not automatic.

Gate: present the complete UI/service change for manual review without starting an unapproved live Publish. Record: implementation complete and ready for manual review with SP-3. No live Publish ran during implementation; the subsequent user-triggered run is recorded in SP-5.

The Publish control makes one empty-body request to `/docs/publish`, remains busy until preparation and distribution finish, and displays completion or phase-specific failure feedback. The separate confirmation workflow and Working/Preview selector are removed. `bin/site-code-update` updated 28 existing projected modules; the public browser configuration was refreshed by its configuration writer. The tracked site delta was inspected. `bin/site-code-update --check` and `bin/site-validate` passed: 98 projected code files and 75 public Docs Viewer runtime modules. No public document publication, R2 transfer, commit or push ran. Restart Local Studio to load the changed Python service before manual review; use the stage-free `/docs/` route.

### SP-5 — Review The Complete Workflow

- [x] Record the user-triggered Publish and its reported completion. The user clicked the Publish icon during manual review and reported success; no small-edit baseline or elapsed time was recorded before that run.
- [x] Confirm the completed Preview artifact and representative repository/site-preview output. The completion receipt records 10,009 files and 18,526 shared asset identities. Selected Search, Recents, selections and Catalogue bytes match the repository projection; Context differs only by its expected `/docs/` to `/analysis/` viewer URL. Source review confirms the same `CompletedPreview` is passed directly into distribution. The user reports successful Publish and that site-preview serves the site.
- [x] Record representative Manage manual review. The user reports that reports, collections, Search, Recents, Media View, Info panel, action menus and Source Editor all appear to work after trying the visible controls. This is representative acceptance, not a claim that every operation or saved-state conversion was exercised. Runtime owner/identity review belongs to SP-6; public reader isolation remains part of the output/site-preview review above.
- [x] Record the timing evidence limit: no preparation/distribution elapsed time was captured for the user-triggered run. No measured speedup or proportional incremental performance is claimed; no repeat run is required solely to obtain timing.
- [x] Review preparation failure and partial-distribution behaviour from source: preparation failure returns before distribution, snapshot replacement removes the old receipt before mutation, and distribution failures retain completed Preview while reporting incomplete publication. Repository output and transfers are verified before success. Live failure/recovery execution was not selected; no fault injection or new test work was performed.

Verification budget: one agreed representative live run, manual site-preview/artifact inspection and proportionate review of the affected Manage boundaries. Agree the exact existing/manual selection and its effects before execution. Publish may write Preview, repository output and R2; document creation or code implementation alone does not authorise that run. No commit, push, public deployment or repeated benchmark runs.

Gate: obtain manual acceptance of the complete workflow and record the evidence limits. Record: passed at the representative scope above. Direct read-only HTTP requests returned 200 for site-preview's Analysis shell, public configuration and Context payload; each response matched its repository file. The public route declares public composition and disables management. Works editor, package operations, saved-state conversion, live failure recovery and independent R2 verification were not exercised. Site-preview serving is confirmed, without claiming exhaustive public visual/interaction coverage. No repeat Publish or timing run was required.

Manual finding: opening Context (`d-20260801-073826-8865a8`) failed with “Docs collection manifest customisation is invalid.” The stage-removal edit accidentally changed the customisation object's exact key count from two to one while still requiring both `data` and `id`. Restored the two-key check in `docs-collection-report.js` and projected it to `site/`. The separate stage-free collection target correctly requires one `collection` key and remains unchanged. Read-only inspection of the configured Works Manage manifest confirmed `{ "id": "working_works", "data": {} }` and 244 documents. No generated rebuild or repeat Publish is needed for this reader correction.

Finding verification: focused JavaScript lint, `bin/site-code-update --check`, `bin/site-validate` and `git diff --check` passed. `bin/site-code-update` changed only the existing collection report projection. The subsequent user report confirms that collections and reports appear to work, with no remaining Context failure reported. No new tests or browser automation ran; the agent did not initiate Publish, R2 transfers, commit, push or public deployment.

### SP-6 — Code Review

- [x] Review the bounded diff for duplicated work, stale split-workflow paths, ownership drift, compatibility residue and missing failure handling.
- [x] Confirm that Preview artifact production remains reusable independently of the repository, that the retired view has not been recreated, and that stage roles have not leaked back into ordinary reader or authoring contracts.
- [x] Check residual runtime stage parameters, cache/state keys and capability branches against the explicit owner boundary. Distinguish required publication provenance from redundant Manage context; do not equate a hidden selector with completed stage removal.
- [x] Confirm that no temporary constant/default/dual-contract implementation remains and that stage removal has not been deferred into follow-on work.
- [x] Resolve findings and rerun only checks affected by those changes.

Verification budget: scoped diff/source review and warranted reruns; no automatic broad suite or additional publication run.

Gate: record findings and resolution, with no unresolved issue inside the accepted delivery scope. Record: passed. Reviewed the publication coordinator/preparation/snapshot/distribution path, request and capability boundaries, runtime target validators, route/workspace composition, generated URL/relationship contracts and one-time saved-state conversion across commits `ee821592b`, `95a30eee0` and `3230150bf`. Residual browser stage references reject retired input; build/storage/publication provenance remains internal. The Context key-count finding is fixed, and the other changed key-count validators agree with their new targets. Working-to-Manage saved-state conversion is bounded and rejects collisions rather than serving an old runtime contract. No further production-code finding required a change. Durable docs still described split publication, stage targets and Preview browsing; SP-7 resolves those contradictions. Reused prior lint/projection/site evidence; no tests, fixtures, browser automation or publication were added or rerun.

### SP-7 — Closeout

- [x] Update the durable workflow, operation-order guidance, identity contracts and affected owner descriptions: Working/Preview belong to publication/storage, ordinary Docs Viewer has no explicit stage context, and Preview remains a physical output artifact.
- [x] Record the delivered outcome, selected evidence, manual acceptance and remaining performance or failure-coverage limits.
- [x] Recommend retaining this delivery as a completed review record until manual archival. Its durable destinations are updated; no deletion is requested or performed.

Verification budget: documentation source/link review and whitespace checks; reuse accepted implementation evidence unless a new change warrants more.

Durable destinations: [Source Organisation](Source_Organisation.md) owns the workflow and evidence limits; [Builder](Builder.md), [Configuration And Extension Points](Configuration_And_Extension_Points.md), [Generated Data Contracts](Generated_Data_Contracts.md), [Reports](Reports.md) and [Media And Asset Handling](Media_And_Asset_Handling.md) own their changed runtime/data boundaries. [Catalogue Deployment](Catalogue_Deployment.md) and [Catalogue Save And Publish Action Map](Catalogue_Save_And_Publish_Action_Map.md) now distinguish one Publish action's internal preparation/distribution phases. [Development Checklist](Development_Checklist.md) and repository `AGENTS.md` carry the current guardrails. No additional temporary Studio documents were created.

Gate: close only when one Publish action completes preparation and distribution, the Preview artifact remains useful and intact, ordinary Docs Viewer needs no stage context, and site-preview is the review surface. Record: closed with the evidence and limits above. Closeout changed documentation only; focused source/link review and `git diff --check` passed. No build, Search rebuild, repeat Publish, R2 audit, commit, push or public deployment was initiated by the agent during closeout.

## Follow-on

Incremental document preparation, dependency invalidation and persistent comparison caches are separate possible optimisations if remaining measured costs justify them. They are not prerequisites for this delivery. Other Preview consumers remain possible through the retained artifact boundary; adding them is separately scoped. Search/Recents policy, Catalogue Save recovery, private lookup retirement and deployment architecture retain their existing owners.
