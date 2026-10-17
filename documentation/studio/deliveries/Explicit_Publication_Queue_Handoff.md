---
draft: false
doc_id: d-20261017-195107-8e0b46
title: Explicit Publication Queue Handoff
added_date: "2026-10-17 19:51:07"
last_updated: "2026-10-17"
summary: Ready for implementation approval; explicit Save, Import and Build orchestration, one shared Docs publication queue owner, and Save media selection from known completed effects.
parent_id: d-20260428-000000-f5ff18
---
# Explicit Publication Queue Handoff

Parent: [Planned Features](../Planned_Features.md). Current behavior is maintained in [Builder](../Builder.md#publish-preparation), [Source Editor Endpoints](../Source_Editor_Endpoints.md) and [Media And Asset Handling](../Media_And_Asset_Handling.md#saved-ownership-and-exact-removals). This delivery describes the proposed replacement boundary; those durable documents remain current until implementation.

Status: planned; readiness review complete on 2026-10-17, ready for implementation approval. Only documentation and read-only investigation are authorized so far. No runtime, source, generated output or publication queue has been changed by this review.

## Requirements

Source Save currently persists selected media and source, then invokes exact document generation. The ordinary and collection builders invoke publication preparation themselves. That preparation resolves publication membership, expands exact dependencies/restorations, selects complete current media references, saves publication queues and completes owned Working-media removals. Save awaits this chain, but its consequential publication work is hidden inside the builder call. The previous incremental-publication delivery deliberately used this boundary; it does not implement Save-owned media selection from known additions/replacements.

The result of this refactor is one explicit workflow: Save, Import and Build orchestrate their required input preparation, persistence, generation and publication handoff. The builder executes supplied build work and returns completed output facts. One shared Docs publication queue owner merges and persists completed selections. A text-only Save with unchanged media references and no media writes contributes no new media writes to the queue.

There is no separate persistent pending-media store, media staging workflow or media publication ledger. The editor's existing unsaved selected Files remain mounted browser state. Save persists selected finished media into Working. Thereafter, media writes/removals awaiting Publish are simply selections inside the existing document entries in `docs-publish-pending.json`. A later Save must preserve still-required media writes already selected there. Use that wording rather than introducing a separate “pending media” concept.

### Responsibility Boundary

| Owner | Responsibility after the refactor |
| --- | --- |
| Mounted Source editor | Own the draft, final-buffer membership of selected native Files, replacement intent, thumbnail choice and authoring feedback. Supply the existing Save request and await completion/fresh display. No new browser request or media state is required. |
| Save workflow service | Carry its resolved target, parsed saved/candidate source, reference differences and prepared media results through persistence, explicit generation orchestration and explicit queue handoff. Report the actual completed phases. |
| Import workflow | Retain its existing conversion, authored choices and source/media persistence owners. Carry prepared records, reference differences and completed media effects into explicit generation and the same queue handoff. |
| Build workflow orchestration | Own the requested scope, required source loading, eligibility/dependency preparation, explicit build calls, public metadata/Selected/discovery follow-through and queue handoff. Application exact generation and command-line/maintenance Build reuse these responsibilities without reparsing supplied records. |
| Shared publication preparation | Resolve publication eligibility and completed public effects from supplied operation inputs and required saved metadata. Reuse the canonical exclusion policy once per operation. Supply explicit render/output selections to orchestration; do not invoke builders recursively or persist queues behind rendering calls. |
| Builder executor and output writers | Render supplied records and construct/write specified outputs from supplied metadata, configuration and relationships. Return completed output facts and changed/unchanged results. No publication queue access, publication policy selection or workflow expansion. |
| Shared Docs publication queue owner | Own document/shared selection merging, preservation/cancellation of exact media effects, queue loading/persistence and the existing completion header. Workflow owners invoke it explicitly with completed effects. Publish uses the same queue persistence authority when clearing completed selections. |
| Publish | Continue consuming only supplied completed selections, applying selected document/media/shared writes and removals to Preview/configured destinations, and clearing successful units. Existing transfer comparison and verification stay with their transfer owners. |

One shared queue owner does not mean putting Save, Import, rendering and publication policy inside one large queue service. Workflow services own sequencing; preparation owns publication decisions; the queue owner owns coalescing and persistence. Load the Docs queue once through that owner for an operation and carry it forward with resolved configuration, saved metadata and completed results. Keep consequential reads and writes visible to the workflow owner, including explicit persistence at existing completed-unit boundaries. Exact interfaces emerge during implementation; no new framework or generic job system is required.

### What Save Will Do

1. Consume the browser's final source, selected Files, replacement intent and thumbnail choice. Resolve the exact configured target once.
2. Prepare and validate the candidate at the current authoring boundary. Reuse its parsed source, fields, metadata, report classification and resolved configuration throughout the operation.
3. Prepare only the supplied selected media outputs. Retain their identities and new/replaced/unchanged byte results, including separately requested thumbnails. Compare saved/candidate media reference sets in memory using the already loaded bodies/fields.
4. Persist prepared changed media and changed source through their current confined writers. Carry completed media identities forward rather than rediscovering them from stored files.
5. Invoke shared generation orchestration explicitly with the prepared document and known authoring effects. That orchestration prepares required relationships, eligibility, exact dependent/restored targets and metadata, and calls the builder for the supplied work. It may have successive bounded build calls when one completed result supplies the next selection; the sequence stays visible in orchestration.
6. After required local outputs complete, explicitly invoke the shared queue owner with document/shared effects and the media selections described below. Preserve existing publication effects instead of replacing them with an empty media map during a later text-only Save.
7. After that handoff has durably recorded exact public removal selections, unlink the corresponding owned Working media. Report a queue or unlink failure at its actual phase, preserving completed effects under the current failure contract.
8. Return the committed record and accurate persistence/generation/handoff results. The browser completes its existing awaited fresh display.

Save performs no Preview/public existence lookup or media-byte comparison, remote request, directory inventory, unrelated media production, Search/Recent refresh or Publish. Checks at actual upload, authoring, configured path, selected write and transfer boundaries remain with their existing owners.

### What The Builder Will Do

The builder's role is to build the requested artifacts from explicit prepared inputs. For application Save/Import it consumes supplied parsed records; explicit Build's input preparation owns the source loading/parsing it actually requires. The executor receives the selected records/deletions, metadata/order, resolved configuration, relationship presentation data and output instructions needed for that invocation. It renders Markdown/tokens, constructs deterministic document/index/manifest payloads, writes the specified generated files/removals, and reports completed outputs and ordinary changed/unchanged byte results. Saved unchanged metadata can still be merged where that is an explicit input to a targeted build.

“Just building” does not eliminate rendering rules, token interpretation, formatting or unchanged-output write avoidance. Those are build mechanics. It removes decisions about why a document should be built or published and which additional workflow should run. The executor will not load or mutate a publication queue, choose publication media, calculate publication eligibility, discover further dependency/restoration builds, trigger discovery refreshes, delete canonical source media or expand a selected request into a full build.

CLI commands such as `build_docs.py --write` remain complete user-facing Build operations, including their required publication handoff. Their command/workflow coordinator invokes the executor and then the shared queue owner explicitly. Making the executor narrower must not leave command-line builds silently unqueued or require the author to run another command.

### Media Selection On Save

| Completed Save effect | Publication contribution |
| --- | --- |
| Heading, prose or presentation change; reference identities unchanged; no media bytes written | Select the document and any actually affected shared/dependent output. Add no media writes. |
| Newly referenced media identity, including an existing Working file pasted into the source or a new thumbnail assignment | Select that identity when the document is eligible. Its prior public availability is not inferred or checked. |
| Referenced file or thumbnail actually added/replaced by this Save | Select the completed written identity. Same-identity replacement must work even when source text is unchanged. |
| Selected replacement/thumbnail produces bytes identical to existing Working bytes | Add no write for that unchanged output unless the identity is newly referenced or is already selected in the publication queue. |
| Later Save before Publish | Preserve already-selected media writes that remain required by the current eligible document, and merge this Save's completed effects. Do not lose an earlier addition/replacement because the later Save changed only text. |
| Last saved reference to an owned body file or the fixed assigned thumbnail is removed | Carry the exact owned removal into the queue, drop a superseded write for that identity, then complete Working removal in the established order. Other documents' namespaces and flat residue retain their current manual-cleanup boundary. |
| A later Save restores an identity selected for removal | Cancel only that exact removal when completed current ownership has ready Working bytes; retain/select the required write. Carry readiness already established by the owning operation, retaining any genuinely required exact ready-input check at this restoration boundary. |
| Draft/excluded document edited | Persist its Working source/media as now, without selecting public media writes. Preserve required withdrawal/removal effects. When it becomes eligible, explicitly select all its current referenced media. |

Reference comparison also covers body media, file/HTML media and thumbnail assignment; it is not limited to native image additions. Identity differences and actual completed byte writes are distinct inputs. Eligibility transitions and newly created eligible documents require complete current media because a previous eligible publication cannot be assumed. A dependency-only re-render has no authored media change and adds no media writes unless it also makes the document newly eligible.

The existing queue can represent selected subsets of media without another persistent baseline or a new queue family. Already-queued complete reference lists remain valid supplied selections and must be preserved; do not rewrite the current queue merely to remove previously selected unchanged media. Exact representation and merge changes are implementation work, with no compatibility aliases or automatic rebaseline.

### Import, Build And Other Existing Callers

Import must explicitly hand off its completed document/media/removal effects after required generation, using the same queue owner. Its conversion and selected media writers remain authoritative; the builder must not infer their results. Carry known inputs and effects from current Import apply paths, including replacement imports, flat collections and native Import doc. Creation/eligibility restoration explicitly selects complete current media. This delivery requires unchanged-media suppression on Save; it does not impose a new Import or maintenance-media optimization.

Explicit exact Rebuild/CLI Build lacks an editor's completed media-write knowledge and must retain its current deliberate media selection behavior through orchestration. Complete Working maintenance retains its existing changes-only output selection and exact referenced-media comparison against local Preview at the explicit maintenance boundary. That comparison must not migrate into Save or the executor. External source/media changes continue to use the existing explicit Build owners.

Removing the builder's hidden handoff affects New, Draft, Delete, reparenting and Catalogue document-generation callers as well. Adapt their invocation boundaries sufficiently to preserve their current completed effects and Catalogue ownership, using the shared queue owner. Retain navigation-only Sort/same-parent Position behavior. Preserve document-only Catalogue dependency renders without adding Work/media selections or including Catalogue in bulk Working Build. This is required call-path integration, not a redesign of those authoring workflows or Catalogue's separate queue.

Search/Recent remain explicitly owned discovery operations. Their completed shared-file contributions must use the common Docs queue writer at an explicit workflow boundary, without changing coverage, format, algorithms or refresh timing. In particular, no Save/Import follow-through starts discovery work. Existing completion boundaries can persist completed selections during a multi-part maintenance operation; one queue owner does not introduce an atomic end-only commit, rollback or progress ledger.

## Deliverables

- Explicit Save, Import and Build orchestration with the executor/publication responsibilities above, preserving awaited completion and current phase-specific errors.
- One shared Docs publication queue merge/persistence owner, with known completed media-write/reference differences carried into Save's selection and existing queued selections preserved.
- Narrow builder inputs/results and explicit integration for affected application, CLI, dependency and Catalogue callers; remove superseded hidden queue writes, recursive handoffs and obsolete publication state/flags from the executor instead of retaining alternate modes.
- Current failure ordering, draft/exclusion/restoration behavior, exact media removals, public metadata and separate discovery/Catalogue ownership preserved.
- Durable ownership transferred primarily to [Builder](../Builder.md), with targeted Source endpoint, media lifecycle and [Development Checklist](../Development_Checklist.md) corrections where their current contracts change. Existing current-state wording is not rewritten as if this proposal has shipped.

## Process

The author continues to use Save, Import, exact Rebuild, complete Build and Publish as now. A heading-only Save produces a document selection without newly adding its unchanged SVG. A Save that writes an image selects that image; another Save before Publish preserves that selection while it remains referenced. Publish completes the supplied units. No new author controls, manual handoff command or media state is introduced.

## Delivery Steps

### QH.0 — Readiness

- [x] Confirm the current boundary against Source Save/media writes, ordinary/collection builders, publication preparation/queue, Import apply, explicit/complete Build and Catalogue/discovery contributors.
- [x] Agree the broad proposed owners, Save/builder responsibilities, media-selection rules and caller-integration boundary without freezing final interfaces or writing implementation code.
- [x] Identify existing queue preservation, eligibility/dependencies and media-removal ordering as the credible regression risks; retain current sources/generated output and queued work.

Readiness result: ready for implementation approval. Current Save supplies full current references and exact removals to generation, while its actual prepared media-write results are not used for publication selection. Ordinary/collection builder completion invokes the queue handoff and dependent renders. Some Import paths additionally apply source-media removals after their build wrapper, so moving only the Save queue call would leave two incomplete ownership paths. Complete Build already has a workflow coordinator and carries a shared preparation/queue, providing an existing seam for explicit orchestration. Search's builder also saves its shared selection internally; its invocation boundary needs the same narrow extraction without changing discovery behavior.

The current queue shape supports selected media lists and exact removals, so no migration, new baseline or storage change is expected. Existing queued writes/removals must survive the refactor; empty queues are not a prerequisite. Current generated `site/` changes belong to the user's publication and are outside this documentation/review work.

Some reused Import wrappers contain snapshot freshness checks and rollback paths. They must not become implicit requirements of the new shared handoff. Implementation review must distinguish genuinely required Import apply boundaries from redundant internal preflights/recovery and remove unnecessary behavior on the touched path under the agreed single-user model. A broader Import recovery redesign is a stop-and-raise condition rather than hidden scope.

Verification budget for readiness: focused source/document reads and a scoped documentation/whitespace review, taking minutes with no service startup, source/media/queue writes, generation, network transfer or test execution. Source/document review and repository whitespace checks passed; production code review is not applicable to this documentation-only step. No implementation feasibility experiment is required for this gate. Remaining interface details belong to implementation.

Stop conditions: raise a need for another ledger, new queue schema migration, compatibility mode, corpus/remote audit, new authoring UX, changed publication eligibility or broad Catalogue/Import/discovery redesign before proceeding. Existing historical test setup may be incompatible with current workspace contracts; that is a verification limitation, not authority to repair fixtures or broaden this delivery.

### QH.1 — Make Generation And Queue Ownership Explicit

- [ ] Move operation scope, eligibility, dependencies/restorations and completion sequencing into explicit shared workflow preparation/orchestration; keep executor inputs/results narrow.
- [ ] Route Save, Import, application/CLI Build and the required existing callers through explicit queue completion using one merge/persistence owner. Preserve existing Catalogue and discovery contribution boundaries.
- [ ] Remove hidden executor queue access and source-media cleanup, nested publication-driven render calls and obsolete arguments/branches. Do not add a flag that leaves the old hidden handoff available.

Verification budget: focused changed-path Python lint/compilation and bounded call-path review for all affected entrypoints, required inputs, output completion, queue invocation and failure ordering. Expected cost is minutes with local caches only and no live workspace writes or network. Inspect any relevant existing test selection and its coverage before proposing a run; new/changed tests, fixtures or harnesses require separate approval. No broad suite or live Build/Publish is automatically authorized by this plan. Gate: every retained entrypoint visibly owns its completed queue handoff and a direct executor call cannot modify the queue.

### QH.2 — Select Save Media From Known Effects

- [ ] Carry actual selected media-write results and loaded before/after references into the shared publication preparation/queue handoff.
- [ ] Implement the Save selection cases above, preserving still-required queued writes/removals across later Saves and retaining complete selection for newly eligible documents.
- [ ] Preserve durable public-removal selection before owned Working unlink and accurate completed-phase/error reporting; introduce no Preview/remote reads on Save.

Verification budget: changed-path lint/compilation plus focused source review against heading-only Save, same-identity replacement, unchanged prepared bytes, newly referenced stored media, repeated Saves, thumbnails, removals/restoration and draft-to-eligible handoff. These are contract cases for review/manual acceptance, not approval to author temporary regression scripts or tests. Separate test work can be specified against the durable [Testing](../Testing.md) policy if justified. User normal-use acceptance should confirm the queue after a heading-only Save and an image replacement followed by a text Save; live media/source/queue writes or Publish require their own concrete authorized action. Gate: Save contributes only required media effects and preserves previously selected effects without publication-state discovery.

### QH.3 — Code Review

- [ ] Review the complete bounded change and affected callers against the mandatory [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).
- [ ] Challenge repeated configuration/policy/queue/source reads, hidden work in reused helpers, snapshot/rollback remnants, normalization, scans, fallbacks, compatibility flags and duplicated publication decisions. Record removed behavior and justified retained safeguards with their owners and operational purpose.
- [ ] Confirm the builder cannot choose publication work or write the queue, workflows invoke the same queue authority explicitly, and Publish remains a consumer of supplied completed effects.

Verification budget: a distinct focused source/diff review after implementation and selected evidence; repeat only checks affected by review changes. Gate: no unresolved ownership or lost-selection finding; static evidence and unexercised live scenarios are stated separately.

### QH.4 — Closeout

- [ ] Update durable current-state ownership and link any separately approved test coverage record from this delivery.
- [ ] Record actual manual normal-use observations and remaining omissions without treating lint/source review as behavioral proof.
- [ ] Retain this delivery for acceptance/evidence lookup or recommend its retirement after transfer to durable owners; do not delete it without approval. Commit, push, Publish and deployment remain separate actions.

Verification budget: bounded documentation/status review using completed evidence; no repeat generation or test run solely for closeout. Gate: agreed operation/queue behavior is implemented, reviewed and accepted, with durable ownership current.

## Follow-On

Further Import/maintenance media selection optimization, broader Import recovery cleanup, historical test migration, media orphan cleanup, Catalogue lifecycle changes and publication/deployment redesign remain separate work. This refactor adds no asynchronous workflow, concurrent-user support, freshness tracking, automatic repair or stronger recovery guarantee.
