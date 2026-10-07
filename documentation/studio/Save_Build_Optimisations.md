---
draft: false
doc_id: d-20260911-232134-ec1ba8
title: Save/Build optimisations
added_date: "2026-09-11 23:21:34"
last_updated: "2026-10-07 10:02:41"
parent_id: d-20260428-000000-f5ff18
---
# Save/Build optimisations

Status: **steps 1–2 complete; steps 3–5 proposed**. The current-state review below was refreshed on 2026-10-07. Delivery order reflects identifiable unnecessary work; timing gains have not been measured. The next implementation slice is step 3, after its timing scope and prerequisite failure policy are agreed.

## Requirements

- Reduce ordinary-document watcher and Build work by removing unused computation, repeated source reads and unnecessary rendering.
- Preserve Source Save's completion boundary: one validated canonical source write, with unchanged saves remaining successful no-ops. Independent watcher generation and viewer refresh retain their own outcomes. [Runtime](Docs_Viewer_Runtime.md#source-editing-and-save) owns that contract.
- Keep exact document identity, canonical membership and hierarchy, selected-source validation, path confinement, and required generated-output checks at their owning boundaries.
- Keep full Build as complete reconciliation. Targeted work should use the selected documents and the metadata needed by their outputs; aggregate JSON files may remain complete files when their processing cost is proportionate.
- Preserve the separately owned Search, Recent, Links, media and publication workflows described by [Builder](Builder.md) and [Source Organisation](Source_Organisation.md).

## Current Implementation

Source Save does not await Build. The main remaining opportunities affect ordinary-document generation cost and the delay before generated content refreshes, rather than the Save response itself.

| Owner or output | Current work | Remaining opportunity |
| --- | --- | --- |
| Ordinary watcher snapshot | `parsed_doc_snapshot()` reparses the complete ordinary collection. Named-collection snapshots already merge changed-file records into their prior snapshot. | Extend changed-file processing to ordinary documents while retaining canonical membership and hierarchy. |
| Targeted-build prerequisites | Service/watcher preflight loads ordinary source and checks unchanged generated payloads; the builder loads the source again and repeats prerequisite checks. | Give prerequisite validation one owner and report missing targeted prerequisites explicitly. |
| Ordinary rendering and tree | The builder loads all ordinary Markdown, renders selected documents, and derives the complete tree. Link rewriting constructs identity lookups from the loaded records. | Read selected Markdown and merge navigation metadata using existing hierarchy and saved tree records; construct required lookups once per operation. |
| Document-count reporting | Counts come directly from loaded source records; the unused flat `index_payload`, rendered-file reads and plain-text extraction have been removed. | Step 1 complete. Legacy test consumers need separately scoped modernisation through the current workspace contract. |
| Watcher render selection | Changed files' before/after IDs select ordinary payloads; parent-title changes no longer add unchanged children. Tree projection and direct-neighbour relationship maintenance retain their own owners. | Step 2 complete. Unselected Related Links sections retain their existing document/full-Build snapshot refresh boundary. |
| `backlinks.json` | The ordinary builder reads every rendered payload and scans anchors to reconstruct same-collection incoming links. | Reuse suitable per-document relationship data or update backlink contributions incrementally after agreeing the report semantics. |

The relevant owners are the [ordinary pipeline](../../docs-viewer/build/docs_builder/pipeline.py), [source and metadata loader](../../docs-viewer/build/docs_builder/source.py), [watcher](../../docs-viewer/services/docs_live_rebuild_watcher.py), [write/rebuild service](../../docs-viewer/services/docs_write_rebuild.py), and [backlinks builder](../../docs-viewer/build/docs_builder/backlinks.py).

Named collections already have targeted builds: [CollectionDocsBuilder](../../docs-viewer/build/docs_builder/collection.py) reads selected sources, merges their metadata into the saved management manifest and preserves unselected by-ID payloads. Working writes `manage-manifest.json`; temporary publication builds write the public manifest. Collection host associations come from configuration, and exact document routes do not require a parent Markdown scan. Targeted deletion already checks exact generated IDs instead of listing all by-ID files.

Targeted, collection-only and watcher builds preserve saved Recent. Full Working Build and Publish own its refresh. Source Save and watcher work omit Search; complete docs-and-Search Build also aggregates prepared Links records into the saved workspace `links.json` and records completion. Registered media work depends on the actual invocation; watcher and targeted collection rebuilds skip media producers. The inspected pipeline does not produce the previously described semantic-token usage index, so usage-index maintenance is not included in this performance baseline.

## Deliverables And Process

Deliver independently complete reductions in ordinary Build work, followed by updated durable owner documentation and bounded verification evidence. Keep this document to current state, proposed order, decisions and completion gates. [Development Checklist](Development_Checklist.md) and [Development Workflow](Development_Workflow.md) govern implementation and closeout.

Each implementation step is a separate finishable slice. Apply steps 6 and 7 to each completed slice before starting the next; later steps remain proposed. Source Save continues to return after persistence, the watcher independently maintains projections, and explicit Build remains awaited through its required outcome.

Test creation or changes require a separately agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md). Delivery approval does not authorize changing tests, fixtures or temporary regression scripts. Record maintained coverage outside this plan and select only relevant existing checks after reviewing their actual coverage and cost.

## Proposed Delivery Steps

### 0 — Readiness And Timing Scope

- [x] Confirm steps 1–2's outcomes, broad owners, write boundaries and credible blast radius against current code. Repeat readiness for the next proposed slice.
- [ ] Before steps 3–5, agree a bounded timing baseline using existing logs and diagnostics first. Separate source persistence, watcher scheduling, builder execution and viewer refresh.
- [ ] Select representative unchanged Save, ordinary body edit, named-collection edit and explicit Build cases only where they answer the current performance question. Record the exact workspace/write boundary and expected cost before execution; use isolated storage for changes made solely to gather evidence.

Verification budget: read-only owner inspection and available diagnostics. Additional runs or instrumentation require a concrete question and a proportionate execution scope; runtime cost is currently unmeasured.

Gate: the slice is coherent and finishable, with no unresolved ownership decision. A missing timing baseline does not block removal of demonstrably unused computation in step 1.

Record: steps 1–2 readiness complete. Step 1 removed unused ordinary-builder reporting; step 2 confined watcher render selection and removed its unused child-order helpers. The current Related Links contract explicitly defers unselected sections to their own or a full Build, so no broader freshness change was needed. Both slices edit repository source/documentation only. Timing scope and later-slice readiness remain pending.

### 1 — Remove Unused Flat-Index Construction

- [x] Remove flat `index_payload` row construction and its whole-collection rendered-file reads and plain-text extraction.
- [x] Use the actual document count directly for summaries and diagnostics; retain required tree, by-ID, Recent and backlinks outputs.
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

- [ ] Extend the watcher's changed-file snapshot merge to ordinary documents, including creation and deletion under canonical hierarchy ownership.
- [ ] Put targeted prerequisite validation in one owner, using the operation's required inputs without a duplicate whole-source preflight.
- [ ] Preserve explicit full Build requests. Missing targeted prerequisites should report the need for a full Build instead of silently expanding one document edit into a complete rebuild.

Verification budget: compare source-file counts and phase timings within the agreed baseline; inspect selected-ID, deletion and missing-prerequisite paths. Use focused lint/syntax checks and an approved, reviewed existing service/generator selection where needed.

Gate: ordinary watcher/preflight processing no longer repeats a complete source parse, failures are actionable, and targeted requests preserve their scope. The tradeoff is explicit manual full-Build recovery when required generated state is unavailable.

Record: proposed; timing scope and failure-policy confirmation precede implementation.

### 4 — Read Only Selected Ordinary Markdown

- [ ] Use `index-order.json` as canonical membership and parentage authority; reuse saved tree metadata for unchanged navigation rows.
- [ ] Read and validate selected Markdown, merge its metadata and project required tree changes without opening every unchanged body.
- [ ] Build required document-identity/link lookups once per operation from the needed records.
- [ ] Define creation, deletion, movement and output-dependency handling; keep full Build as complete source reconciliation and report missing or invalid targeted metadata visibly.

Verification budget: bounded source/output comparison for the agreed ordinary-edit cases, including hierarchy and failure paths. Record selected-source counts and timing evidence; use isolated storage for generator writes and separately specify any new coverage.

Gate: ordinary targeted builds open only selected sources, preserve required output semantics and retain unchanged navigation records correctly. Complete aggregate JSON may remain where its measured cost is modest; avoid a second canonical metadata inventory.

Record: proposed; broader metadata/selection refactor after steps 1–3.

### 5 — Replace Full Backlinks Scanning

- [ ] Agree the Documents Linking Here report's same-collection rendered-link semantics before selecting its data owner.
- [ ] Assess reusing existing per-document Links records, accounting for their broader cross-collection, Catalogue-token and missing-destination behavior.
- [ ] If those records cannot preserve the required semantics, specify incremental backlink contributions for changed/deleted source documents.
- [ ] Replace the whole rendered-payload/anchor scan with the chosen bounded update, preserving title changes, relationship removals and complete reconciliation.

Verification budget: reviewed relationship/report coverage for the agreed semantics, isolated generator output comparison and bounded timing evidence. New or changed tests and a new contribution-storage format require their explicit specification.

Gate: the report retains its agreed meaning and selected updates no longer scan every rendered document. Stop before implementation if the choice requires a report behavior change that has not been agreed.

Record: proposed; potentially substantial benefit, with a larger ownership and semantics decision than the earlier steps.

### 6 — Code Review For The Delivered Slice

- [x] Review steps 1–2's final bounded diffs for ownership drift, unnecessary reads, duplicated state, compatibility residue, stale consumers and missing failure behavior. Repeat for later delivered slices.
- [x] Confirm steps 1–2 made no test changes; affected legacy consumers are recorded separately. Review future test changes against their separately approved specification.
- [x] Limit performance claims to the removed flat-index pass and child-render expansion; timing gains remain unmeasured. Rerun only checks affected by later review changes.

Gate: review findings are resolved and completion claims match the inspected and exercised surface.

Record: steps 1–2 review complete with no unresolved production findings. Reporting counts and required mutation boundaries remain intact; step 2 preserves exact changed identities and the existing Related Links snapshot policy. Removed sorting helpers have no remaining production callers. Legacy test limits are documented in Builder, and no alias was introduced. Repeat this review for the next slice.

### 7 — Closeout For The Delivered Slice

- [x] Update Builder for reporting, returned results, watcher render selection, Related Links refresh boundaries and legacy test limits.
- [x] Mark steps 1–2 complete and step 3 next; keep later work proposed and timing gains unmeasured.
- [x] Keep this feature document for the remaining proposed slices. Documentation is maintained directly in the repository and needs no Docs or Search rebuild.

Gate: the delivered outcome is complete and reviewable; subsequent work remains explicitly proposed.

Record: steps 1–2 delivered and closed. Builder is the durable owner; this plan remains useful for steps 3–5. Watcher runtime activation requires a restart; timing runs and separately specified test modernisation remain pending.
