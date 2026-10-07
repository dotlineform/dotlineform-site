---
draft: false
doc_id: d-20260911-232134-ec1ba8
title: Save/Build optimisations
added_date: "2026-09-11 23:21:34"
last_updated: "2026-10-07 11:57:54"
parent_id: d-20260428-000000-f5ff18
---
# Save/Build optimisations

Status: **complete**. Steps 1–5 are delivered and reviewed. On 2026-10-07 the user retired Documents Linking Here and backlinks in favour of [Related Links](Related_Links.md), closing step 5 by removing the unused report and its whole rendered-payload scan. Bounded ordinary dry-runs confirm selected source reads; their small timings are not a general performance benchmark.

## Requirements

- Reduce ordinary-document watcher and Build work by removing unused computation, repeated source reads and unnecessary rendering.
- Preserve Source Save's completion boundary: one validated canonical source write, with unchanged saves remaining successful no-ops. Independent watcher generation and viewer refresh retain their own outcomes. [Runtime](Docs_Viewer_Runtime.md#source-editing-and-save) owns that contract.
- Keep exact document identity, canonical membership and hierarchy, selected-source validation, path confinement, and required generated-output checks at their owning boundaries.
- Keep full Build as complete reconciliation. Targeted work should use the selected documents and the metadata needed by their outputs; aggregate JSON files may remain complete files when their processing cost is proportionate.
- Preserve the separately owned Search, Recent, Links, media and publication workflows described by [Builder](Builder.md) and [Source Organisation](Source_Organisation.md).

## Current Implementation

Source Save does not await Build. These reductions affect ordinary-document generation cost and the delay before generated content refreshes, rather than the Save response itself.

| Owner or output | Current work | Remaining opportunity |
| --- | --- | --- |
| Ordinary watcher snapshot | Startup seeds the collection; subsequent ordinary and named-collection snapshots merge changed-file records. Ordinary source loading retains canonical hierarchy ownership. | Step 3 complete. |
| Targeted-build prerequisites | The ordinary builder checks canonical membership, required saved tree metadata and unselected payloads. Service/watcher preflight and automatic prerequisite fallback have been removed. | Step 3 complete. Missing prerequisites require an explicit full Build. |
| Ordinary rendering and tree | Targeted builds read selected Markdown and merge unchanged saved navigation records under current canonical hierarchy. Rendering, parent membership and tree reuse one identity lookup. | Step 4 complete. Full Build still validates and reconciles all canonical sources. |
| Document-count reporting | Counts distinguish canonical documents, source files read and rendered payloads; the unused flat `index_payload`, rendered-file reads and plain-text extraction have been removed. | Step 1 complete. Legacy test consumers need separately scoped modernisation through the current workspace contract. |
| Watcher render selection | Changed files' before/after IDs select ordinary payloads; parent-title changes no longer add unchanged children. Tree projection and direct-neighbour relationship maintenance retain their own owners. | Step 2 complete. Unselected Related Links sections retain their existing document/full-Build snapshot refresh boundary. |
| Documents Linking Here and `backlinks.json` | Retired, including generation, whole rendered-payload scanning, write planning, diagnostics, report loading, browser configuration and the local API. Related Links remains the relationship presentation. | Step 5 complete. No replacement reverse-link payload or compatibility alias. |

The relevant owners are the [ordinary pipeline](../../docs-viewer/build/docs_builder/pipeline.py), [source and metadata loader](../../docs-viewer/build/docs_builder/source.py), [watcher](../../docs-viewer/services/docs_live_rebuild_watcher.py), [write/rebuild service](../../docs-viewer/services/docs_write_rebuild.py), and [Related Links](Related_Links.md).

Named collections already have targeted builds: [CollectionDocsBuilder](../../docs-viewer/build/docs_builder/collection.py) reads selected sources, merges their metadata into the saved management manifest and preserves unselected by-ID payloads. Working writes `manage-manifest.json`; temporary publication builds write the public manifest. Collection host associations come from configuration, and exact document routes do not require a parent Markdown scan. Targeted deletion already checks exact generated IDs instead of listing all by-ID files.

Targeted, collection-only and watcher builds preserve saved Recent. Full Working Build and Publish own its refresh. Source Save and watcher work omit Search; complete docs-and-Search Build also aggregates prepared Links records into the saved workspace `links.json` and records completion. Registered media work depends on the actual invocation; watcher and targeted collection rebuilds skip media producers. The inspected pipeline does not produce the previously described semantic-token usage index, so usage-index maintenance is not included in this performance baseline.

## Deliverables And Process

Deliver independently complete reductions in ordinary Build work, followed by updated durable owner documentation and bounded verification evidence. Keep this document to current state, decisions and completion gates. [Development Checklist](Development_Checklist.md) and [Development Workflow](Development_Workflow.md) govern implementation and closeout.

Each implementation step is a separate finishable slice, reviewed and closed through steps 6 and 7. Source Save continues to return after persistence, the watcher independently maintains projections, and explicit Build remains awaited through its required outcome.

Test creation or changes require a separately agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md). Delivery approval does not authorize changing tests, fixtures or temporary regression scripts. Record maintained coverage outside this plan and select only relevant existing checks after reviewing their actual coverage and cost.

## Delivery Steps

### 0 — Readiness And Timing Scope

- [x] Confirm steps 1–5's outcomes, broad owners, write boundaries and credible blast radius against current code.
- [x] Bound step 3's evidence to source-call inspection and available diagnostics. Existing historical builder logs report builder totals, without separate watcher/preflight timings; they cannot establish a current elapsed-time comparison. No source edits, generated writes or benchmark runs were needed solely for evidence.
- [x] Bound step 4's comparison to the existing CLI's read-only targeted ordinary dry-run against the same configured Working document, with media and Recent disabled. One full ordinary dry-run with media disabled checks the changed complete-build/Recent path. Repeat only the targeted command after review changes to saved-tree input reuse. Existing diagnostics showed a small ordinary corpus; all four commands completed in under a second each, without source or generated writes.
- [x] Scope step 5 to the user's retirement decision: remove the report and its production consumers, preserve Related Links, and remove the obsolete replaceable Working payload. Use source inspection, existing static checks and one read-only targeted CLI diagnostic; no source mutation, Preview change or Publish is included.

Verification budget: read-only owner inspection, focused static checks, step 4's three selected existing CLI diagnostics plus its targeted review recheck, and one targeted read-only diagnostic for step 5. Additional runs or instrumentation require a concrete question and a proportionate execution scope; broader runtime cost remains unmeasured.

Gate: the slice is coherent and finishable, with no unresolved ownership decision. Source-call evidence can establish a removed pass; elapsed-time claims require a representative runtime comparison.

Record: steps 1–5 readiness complete. Saved tree rows contain the required unchanged navigation fields; current hierarchy remains canonical and no persistent metadata inventory is added. Missing targeted metadata retains explicit full-Build recovery. Changed shared rendering interfaces require collection and package call-site updates; optional targeted media must reuse captured selected source text. Step 5 also deletes the obsolete Working `generated/documents/backlinks.json`; all diagnostic commands are read-only and Preview remains untouched.

### 1 — Remove Unused Flat-Index Construction

- [x] Remove flat `index_payload` row construction and its whole-collection rendered-file reads and plain-text extraction.
- [x] Use the actual document count directly for summaries and diagnostics; retain required tree, by-ID and Recent outputs. The backlinks output retained at this slice is retired in step 5.
- [x] Identify affected legacy test consumers and record their separately scoped modernisation need in [Builder](Builder.md#commands). The production path retains no compatibility return value; test work requires its own agreed specification.

Verification budget: focused source/call-site review, changed Python lint/syntax and whitespace checks. Select existing output/count evidence only if its reviewed coverage addresses a remaining risk.

Gate: production reporting remains correct and the removed flat-index pass has no remaining production consumer. Review and close this slice through steps 6 and 7.

Record: complete. The ordinary pipeline, source mixin and write-plan reporting now omit the flat index and its unused helpers. Focused Python lint, `py_compile` and `git diff --check` passed for the changed boundary. Source/diff review confirmed equivalent document counts and unchanged required write planning; generated builds, timings and legacy tests were not run.

### 2 — Remove Unnecessary Render Expansion

- [x] Review parent-title changes against current by-ID metadata and navigation outputs; remove direct-child expansion, its snapshot parent/sort fields and its unused sorting helpers.
- [x] Define render dependencies through the existing Related Links snapshot contract: selected documents render refreshed records, while unselected sections refresh on their own document build or a full Build.
- [x] Keep relationship-maintenance targets distinct from render targets and confine targeted payload rendering to changed files' before/after identities.

Verification budget: source inspection of selection and consuming outputs, focused lint/syntax/whitespace checks, and the smallest reviewed existing dependency evidence. UI presentation remains manual.

Gate: title and relationship changes retain required refresh behavior without automatic rendering of unrelated children. The existing Related Links freshness boundary is retained; any broader refresh policy remains separately scoped.

Record: complete. The watcher and source-model helper boundary no longer computes child ordering or expands title edits to children. Focused Python lint, `py_compile` and `git diff --check` passed for both changed Python files. Source/diff review covered creation, deletion, identity replacement, existing fallback decisions, tree projection and independent Links maintenance. Tests, generated builds and timing measurements were not run; an already running watcher must restart to load the changed module.

### 3 — Remove Repeated Ordinary Source Reads

- [x] Extend the watcher's changed-file snapshot merge to ordinary documents, including creation and deletion under canonical hierarchy ownership.
- [x] Put targeted prerequisite validation in one owner, using the operation's required inputs without a duplicate whole-source preflight.
- [x] Preserve explicit full Build requests. Missing targeted prerequisites report the need for a full Build instead of silently expanding one document edit into a complete rebuild; empty targeted selections fail explicitly.

Verification budget: inspect source-call counts, selected-ID, deletion and missing-prerequisite paths; run focused lint/syntax/whitespace checks. Available historical diagnostics do not separate the removed phases, so runtime comparisons and behavior tests were not selected for this slice.

Gate: ordinary watcher/preflight processing no longer repeats a complete source parse, failures are actionable, and targeted requests preserve their scope. The tradeoff is explicit manual full-Build recovery when required generated state is unavailable.

Record: complete. Normal ordinary snapshot processing reads changed surviving sources, and builder-owned prerequisites replace duplicate whole-source preflight. Step 4 now also confines builder source loading to selected inputs. Startup snapshot loading, canonical hierarchy validation, explicit full requests, watcher bulk/unavailable-snapshot policies and separately owned Links reads remain. Focused Python lint, `py_compile` and `git diff --check` passed for step 3's three changed Python files. Its source/diff review covered creation/deletion merge, suppression adoption, selector forwarding, empty selections and missing/invalid prerequisite failures. No tests or live execution were selected for that slice; affected obsolete test consumers are recorded in Builder without aliases.

### 4 — Read Only Selected Ordinary Markdown

- [x] Use `index-order.json` as canonical membership and parentage authority; reuse saved tree metadata for unchanged navigation rows.
- [x] Read and validate selected Markdown, merge its metadata and project required tree changes without opening every unchanged body. Optional targeted media receives the already captured source text.
- [x] Build required document-identity/link lookups once per operation from the needed records; update collection and package rendering callers without aliases.
- [x] Define creation, deletion, movement and output-dependency handling; keep full Build as complete source reconciliation and report missing or invalid targeted metadata visibly.

Verification budget: compare source counts and proposed output through the selected read-only targeted CLI runs and one review recheck; one complete ordinary dry-run covers shared lookup and Recent integration. Review hierarchy and failure paths in source, with focused Python lint/syntax/whitespace checks. No new behavior tests, source mutations, generator writes or browser work are included.

Gate: ordinary targeted document loading opens selected render/Links sources, preserves output semantics and retains unchanged navigation records under current hierarchy. Separately owned Links neighbour reads remain; step 5 retires the remaining backlinks rendered-payload scan. Complete aggregate JSON stays in place; no second canonical metadata inventory is introduced.

Record: complete. The same existing ordinary document's dry-run scanned 33 source files before and 1 after, proposed no payload/tree/backlinks changes and preserved Recent; the final targeted review recheck retained those counts and outputs. Diagnostic builder time was 0.024s before and 0.012s after; this single small comparison establishes the removed reads, not a representative speedup. The full ordinary dry-run loaded/rendered 33 documents with no payload/tree/backlinks changes and proposed one normal Recent refresh, without applying it. Python lint and syntax passed for all 12 changed Python files; whitespace checks passed. Source/diff review covered canonical ordering, creation/deletion/movement, selected-source identity and path confinement, missing/invalid saved metadata, independent Links selectors, media source reuse and all production lookup callers. Mutation/failure behavior, collection/package execution and registered media production remain unexercised; test changes and runs remain separately scoped.

### 5 — Retire Documents Linking Here And Backlinks

- [x] Retire Documents Linking Here and backlinks in favour of the existing Related Links directive, as explicitly requested by the user.
- [x] Remove the backlinks producer, whole rendered-payload/anchor scan, write planning, result field and diagnostics.
- [x] Remove the report registry entry, executable module/loader, local API/read helper, browser setting and obsolete preparation validation; retain no alias.
- [x] Delete the obsolete Working generated payload and replace the development checklist and Docs Data report footers with `[[links|related links]]`. Inspection found no active retired report blocks in canonical Working sources.
- [x] Retain persisted Links maintenance and Related Links rendering with their existing snapshot refresh boundaries; introduce no replacement reverse-link index.

Verification budget: source/call-site and scoped diff review, changed Python/JavaScript lint, Python syntax, configuration JSON parsing, whitespace, public projection/site validation and one existing targeted read-only CLI diagnostic with media and Recent disabled. Tests, live service/browser checks and Publish are outside this slice.

Gate: production has no backlinks report, payload, scan, setting or route consumer; Related Links remains the maintained relationship presentation. Old authored report blocks fail normal unknown-report validation and must be converted to the directive.

Record: complete. Production source inspection found no remaining backlinks references. The targeted builder completed with the obsolete file absent, reading 1 source for 33 canonical documents and rendering 1 payload, with no proposed payload/tree/Recent changes or warnings. Diagnostic time was 0.003s for this single small run; the performance claim is removal of the scan, not a representative speedup. Python and JavaScript lint, Python syntax, JSON parsing, `git diff --check`, `bin/site-code-update --check` and `bin/site-validate` passed. Public projection changed only the shared browser config controller. Obsolete dedicated report tests and mixed output/route assertions remain unchanged and unrun; [Reports](Reports.md#current-reports) records their separately scoped cleanup. No live Save/watcher/API/browser or Publish behavior was exercised.

### 6 — Code Review For The Delivered Slice

- [x] Review steps 1–5's final bounded diffs for ownership drift, unnecessary reads, duplicated state, compatibility residue, stale consumers and missing failure behavior.
- [x] Confirm steps 1–5 made no test changes; affected legacy consumers are recorded separately. Review future test changes against their separately approved specification.
- [x] Limit performance claims to removed work and bounded diagnostic counts/timings. Rerun only checks affected by later review changes.

Gate: review findings are resolved and completion claims match the inspected and exercised surface.

Record: steps 1–5 review complete with no unresolved production findings. Current hierarchy, exact selected identities and the existing Related Links snapshot policy remain authoritative. Saved metadata is validated by its consuming builder, source text is carried to optional media, and shared lookup callers are updated. Retirement leaves shared authored-link audit helpers in place for their remaining owners and does not edit Preview. Legacy test limits are documented in Builder and Reports, and no alias was introduced.

### 7 — Closeout For The Delivered Slice

- [x] Update Builder for reporting, returned results, watcher render selection and incremental snapshots, selected-source builder metadata/lookup ownership, targeted prerequisite failures, Related Links refresh boundaries and legacy test limits. Update Reports, Related Links and related runtime/configuration owners for retirement.
- [x] Mark steps 1–5 complete; retain measured evidence limits. No further implementation is proposed within this delivery.
- [x] Retain this completed delivery record with durable contracts in its owner documents. Documentation is maintained directly in the repository and needs no Docs or Search rebuild.

Gate: the delivered outcome is complete and reviewable; evidence limits and any separately scoped follow-up are explicit.

Record: steps 1–5 delivered and closed. Builder, Reports and Related Links are the durable owners. Restart an already running Docs service/watcher and reload the viewer to activate changed service/runtime modules; builder subprocesses load current modules on their next invocation. Separately specified test cleanup remains pending. No Publish, commit or push was performed.
