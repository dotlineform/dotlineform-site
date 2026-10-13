---
draft: false
doc_id: d-20261012-112453-211357
title: Incremental Document Publish
added_date: "2026-10-12 11:24:53"
last_updated: "2026-10-13 19:25:13"
summary: Proposed queue-only Publish for ordinary and non-Catalogue collection documents, with completed public artifacts and eligibility, dependency, media and shared-output effects supplied upstream.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Incremental Document Publish

This is the ordinary and non-Catalogue collection document follow-on to [Incremental Updates](Incremental_updates.md), parented to [Planned Features](../Planned_Features.md). It extends the principle that Publish acts only on supplied publication selections. The existing Catalogue queues retain their ownership; the final unconditional ordinary-document/shared preparation pass is replaced by explicitly queued work.

## Current And Next State

Status: proposed on 2026-10-12. The user requested this delivery write-up; implementation is not approved. No code, configuration, tests, external documents or generated payloads have been changed for this proposal.

Prerequisite set on 2026-10-12: use [User Facing Rules](../data/User_Facing_Rules.md) as the target definition, review the relevant targets and complete required cleanup through functional delivery groups before this delivery proceeds. Each cleanup delivery records the actual implementation comparison, changes and evidence; the target index does not carry that inventory or require a separate delivery per entry. Documented design conventions and authoring preferences do not automatically require server enforcement. [Studio User Facing Rules](../data/Studio_User_Facing_Rules.md) retains the Studio review and implementation record. The active Docs Viewer review removes redundant calls, checks and downstream validation before extending incremental Catalogue publication to the whole corpus. Reconcile this proposal's assumptions with the accepted targets and completed cleanup before implementation.

Current Publish completes queued Catalogue Works, then captures ordinary and collection sources, resolves publication eligibility, rebuilds ordinary and other collection documents in temporary storage and distributes a complete prepared snapshot. Catalogue Gallery/shared selections are already explicit, but the enclosing pass still processes ordinary documents and discovery data even when those selections are empty.

Prerequisite cleanup on 2026-10-13: the user approved M.25/M.28/M.29 review groups 1–4, implemented through the existing Publish owners. They remove repeated queue/content audits, reuse Catalogue setup/media inputs and limit browser follow-through to reported Recent persistence. [User Facing Rules](../data/User_Facing_Rules.md) records implementation and evidence. Groups 5–7 remain gaps for this delivery: the unconditional full source/eligibility/build/snapshot pass, complete repository/referenced-media reconciliation including remote listings, and selected shared/document/media completion with retry from retained Preview bytes. Shared document media currently retains a common live asset root. This cleanup does not approve this delivery's implementation or satisfy its queue-only/no-op/retry gates.

Complete proposed result: Save/build owners prepare exact public artifacts and record their completed writes/removals; Publish applies only those queued effects to Preview and configured repository/R2 destinations. Unselected files retain their bytes. When all publication queues are empty, Publish performs no publication work.

## Requirements

- **Publish is strictly queue-only. It performs no corpus reconciliation or data validation.** It trusts the completed artifacts and effects supplied by upstream owners.
- Publish does not load document sources, recalculate eligibility, expand dependencies, render Markdown, prepare public payloads, generate media, rebuild discovery data, check links or audit document/collection/Catalogue content.
- Publish does not enumerate source/output directories or remote media to rediscover changes, infer deletion from absence, compare complete corpora, hash complete snapshots or establish whole-corpus consistency.
- Every published document, media item and shared output has an explicit queued write/removal. There is no unconditional final preparation or distribution pass and no missing-queue fallback to reconciliation.
- Preserve the single awaited empty-body `POST /docs/publish` action, configured storage/destinations and synchronous operation ordering. Working owns generation; Preview retains the last applied publication artifacts; distribution consumes those Preview bytes.
- Ordinary documents use their immutable document identity. Non-Catalogue collection documents additionally carry the exact configured collection identity. Catalogue Work/Gallery/Series selections retain their existing queue owner and are not duplicated in a generic document queue.
- Complete upstream handoffs and queue persistence before reporting generation complete. Failed queue persistence must report generated-but-incomplete publication handoff rather than silently lose the selection.
- Keep full generation, validation, baseline population and repair in explicitly requested upstream maintenance operations. Such an operation may generate and queue a complete corpus; Publish still consumes only its supplied queue.

Queue decoding, configured destination/path confinement, missing required transfer inputs and filesystem/network failures remain execution boundaries. An unreadable or unprocessable queue stops the operation. These boundaries do not authorize content/schema validation, membership agreement checks, readiness checks or an audit of queued or unqueued data inside Publish. Transfer completion evidence is limited to the selected writes/removals.

## Eligibility And Dependencies

Eligibility and dependency resolution belong to authoring/generation owners before publication selections are merged. Publish neither filters the queue nor adds work to it. Entry creation means the necessary preparation has completed; there is no Publish-time readiness check against an earlier queue or current source.

The current eligibility baseline is explicit boolean `draft` for ordinary and non-Catalogue collection documents, descendant exclusions for ordinary unpublishable/draft roots, and exclusion of a configured collection when its ordinary host is excluded. Catalogue documents have fixed intrinsic eligibility without a draft field. Collection publication and Search inclusion are separate decisions. Confirm the rules still required after the prerequisite review rather than preserving every existing branch by default; the effect selections below must then follow the accepted rules. Root-level collection hosts are a documented layout convention, not a new validation requirement.

| Upstream change | Required completed publication selection |
| --- | --- |
| Create or edit an eligible document | Its prepared public document and any affected public metadata/output. |
| Delete a document or make it ineligible | Exact document removals and affected public index/manifest, Recent and Selected output. The removal identity survives source/generated deletion. |
| Exclude a parent subtree | Exact removals for the affected descendants as well as the parent, with the corresponding shared-output changes. |
| Restore a subtree's eligibility | Prepared writes for every newly eligible document and the corresponding shared-output changes. |
| Move a document between parents | Effects for any inherited eligibility change, index placement and affected rendered dependencies. |
| Exclude or restore a collection host | Exact collection document and public manifest removals/writes, plus any other publication artifacts owned by that collection whose eligibility depends on the host. The owning domain supplies these effects through its queue. |
| Change a title, relationship or other rendering input | Prepared writes for affected dependent documents, including rendered Related Links, when their public presentation changes. |
| Change publication policy or configuration outside an application write | An explicit owning generation/maintenance operation resolves the affected identities and queues their effects. Publish does not discover the external edit. |

Use saved hierarchy, collection and relationship metadata to select affected identities where available. Upstream owners must retain sufficient private metadata for scoped eligibility and dependency calculations; public document metadata must not acquire private draft/readiness fields. Do not introduce a full-source dependency scan merely to compensate for a missing upstream handoff.

An explicitly requested complete maintenance build can establish or repair those metadata prerequisites. Missing required saved metadata during an incremental operation stops that operation with an explicit repair requirement; Publish does not supply the repair.

Dependency completion is part of the originating operation's generation handoff. Updating a relationship record alone is insufficient when another document embeds the changed presentation. Its completed public payload must also be queued. This applies across ordinary and collection boundaries without transferring Catalogue generation ownership to Docs Publish.

## Deliverables

### Docs Publication Queue And Handoff

Proposed file: `working/docs-publish-pending.json`, relative to the configured Docs workspace root. The exact schema and artifact locations are implementation decisions within this boundary, not frozen by this proposal.

| Selection family | Supplied identity and effect |
| --- | --- |
| Current documents | Exact document/collection target and completed public artifact awaiting replacement. |
| Removed documents | Exact document/collection target awaiting removal, including eligibility withdrawal as well as source deletion. |
| Media | Exact configured media owner/type/relative filename and write/removal selection. |
| Shared outputs | Explicit allowed output identity, such as the ordinary public index, a named collection manifest, Recent, Selected, Search or public configuration. |

Queue entries supply identities and actions, not absolute paths, destination providers or new publication authority. The queue owner coalesces repeated completed contributions to the latest intended state. Later removal replaces a pending document write; recreation replaces its pending removal. Independent media and shared selections remain pending until their own completion.

Source Save, Create, Import, Move, Delete, exact Rebuild and CLI generation use one common generation-to-publication handoff. The generation result supplies its completed target writes/removals and affected shared artifacts; services do not each rediscover that selection. An explicitly requested Rebuild can queue replacement even when generated bytes are unchanged, so it can repair missing publication output without a Publish-time comparison.

Initialize Publish progress only for new publication units. Upstream contributors preserve initialized progress; Publish owns its transitions. Finish an interrupted Publish before resuming authoring or generation, following the existing Catalogue workflow.

### Prepared Public Artifacts

Generation prepares the final public form, including configured collection field projection, public URLs, local folder-link treatment and Mermaid presentation. Reuse the current public projection/rendering owners rather than copying their rules into a new queue or publisher.

Where local and public document forms differ, retain the public form as replaceable generated output within Working. This is not a new storage stage, persistent Preview source tree or independent source authority. Publish transfers these finished bytes without parsing or transforming document content.

### Explicit Shared Output

Upstream generation maintains the public ordinary index and affected collection manifests from known changes and saved metadata, then queues their finished files. Assembly of a selected aggregate may serialize its complete metadata inventory upstream; it does not cause Publish to read or rebuild the document corpus. Unselected aggregates remain untouched.

Move Recent preparation out of Publish. The proposed default is to update its saved candidate metadata during document follow-through, apply its existing eligibility, exclusions and limit, and queue the finished Recent file. Removing a current top entry must allow the next saved eligible candidate to enter without reopening all document bodies. External Recent-policy edits take effect through an explicit owning build, rather than through Publish.

Star/Unstar, metadata refresh and eligibility/deletion effects prepare and queue the public Selected payload upstream while retaining excluded selections in the Working source list. Starring continues to preserve document modification dates.

Search retains its explicit Working rebuild owner and complete-index format. A completed explicit Search rebuild queues its exact bytes. Ordinary document changes neither rebuild Search nor queue it automatically; Publish leaves an unqueued Search index untouched and performs no freshness or membership checks.

Public configuration changes require an explicit owning preparation operation to queue the corresponding bytes and any required removals. Removing a collection or changing output layout must provide exact removal identities before its former configuration authority is lost.

### Exact Document-Media Effects

Import, media intake/production and generation owners supply the required transfers, including assets newly needed by a document. Same-name byte replacement explicitly contributes a media write. Referencing a Work or Gallery does not implicitly queue that Catalogue's media; its existing owner supplies any required Catalogue effects.

Preserve ordinary Source Save's exclusion of registered media scanning, detection and production. Reuse the references known during rendering and the completed media owner's selections; an infrequent persistent media-source edit still uses the explicit media/docs build workflow before Publish.

Removing a document reference does not automatically remove shared media. A media removal requires the exact explicit selection from its owner. Publish performs no reference/ownership scan, orphan cleanup or remote listing. Shared media selection coalesces by exact configured identity so several documents can require one transfer.

### Selected Preview And Distribution

Replace the complete-snapshot preparation/distribution dependency with selected application through the existing publication owners. Preserve Catalogue per-Work selection and progress, while adapting the shared Catalogue consumer to execute only its queued Gallery/system-file effects. Remove content-validation and whole-snapshot requirements from the normal Publish call path, including those that would otherwise be reached through a reused helper.

Publication completion records successful selected work. It must not certify all untouched Preview/destination files, require a complete snapshot inventory or rescan/hash them to produce a receipt. Retire obsolete complete-corpus checks from the normal path without compatibility aliases, shadow copies or a second publication ledger.

## Process

```text
Authoring/build operation
  -> complete local/public generation and upstream eligibility/dependency effects
  -> merge exact completed publication selections
Publish
  -> apply queued document/media units to Preview and distribute them
  -> apply queued shared output after its required item work
  -> remove only successfully distributed selections
```

For each publication unit, apply its supplied Preview writes/removals when `preview_done` is false, then persist true after that work completes. Distribution reads the retained Preview artifacts and deletion selection. Only successful distribution removes the unit. Queued shared output uses the same completion boundary; an item queue becoming empty must not erase unfinished shared selections or trigger a new shared build.

Unselected files remain in place. Missing owned deletion targets count as successful removal. All queues empty means no copies, uploads, deletions, generation, corpus validation or timestamp-only output changes.

On failure, stop and report the exact target and Preview/distribution phase. Retain failed/unprocessed selections and accurate progress; earlier completed effects remain. A later explicit Publish retries the retained selection, using Preview bytes after Preview completion rather than newer Working data. No automatic retry, rollback, backup tree, transactional swap or concurrency/freshness scan is introduced. Repository/R2 effects remain non-atomic, and temporary differences between item and shared output remain possible during an incomplete operation.

External Markdown and policy edits require explicit owning generation before Publish. An omitted queue contribution remains unpublished until its owner queues it. Initial population or a global renderer/configuration change uses an explicit maintenance build to generate and queue the required set; normal Publish has no bootstrap or drift-repair mode.

## Delivery Steps

### [ ] IDP.0 — Readiness And Implementation Approval

- [ ] Review the relevant User Facing Rules targets and complete required functional cleanup deliveries, then reconcile the eligibility/dependency assumptions with the accepted targets.
- [ ] Confirm the complete queue-only boundary against the current generation, eligibility, dependency, media and publication owners, including shared Catalogue publication.
- [ ] Confirm saved metadata prerequisites, the upstream Recent decision and a deliberate cutover/baseline approach that does not silently reconcile during Publish.
- [ ] Obtain explicit implementation approval before code/configuration work. Agree any proposed test work separately under [Test Contract Discipline](../Test_Contract_Discipline.md).

Verification budget: concise read-only owner review; no fixtures, prototype, generated writes, executable tests or live Publish. Stop if required upstream effects or cutover ownership remain unresolved.

Gate: the prerequisite review/required cleanup is complete and one coherent implementation boundary and its genuine stop conditions are approved. Record: proposed; documentation only is authorized; rules review and cleanup precede this delivery.

### [ ] IDP.1 — Public Preparation And Queue Handoff

- [ ] Implement the Docs queue owner and common completed-generation handoff for application and CLI paths, including deletion and explicit unchanged-byte Rebuild.
- [ ] Prepare final public artifacts upstream through the current projection owners and report incomplete queue persistence.
- [ ] Establish the approved queue/generated baseline without invoking Publish reconciliation or adding old-format aliases.

Verification budget: focused changed-source lint/syntax and bounded source/output inspection selected after owner inspection. Test work and real workspace writes require their agreed scope; do not add temporary regression scripts without approval.

Gate: completed public artifacts and exact selections are supplied by every in-scope generation path. Record: not started.

### [ ] IDP.2 — Eligibility, Dependencies, Media And Shared Output

- [ ] Complete the distinct eligibility/dependency contract, including subtree and collection-host withdrawal/restoration and affected rendered neighbours.
- [ ] Prepare and queue public index/manifest, Recent, Selected and configuration effects upstream; connect explicit Search completion without changing ordinary edit/Search ownership.
- [ ] Supply exact media effects while preserving normal Save's exclusion of media detection/production and shared-media deletion ownership.

Verification budget: bounded owner review and selected generated artifacts for the agreed scenarios. Record the exact existing diagnostics/checks, purpose, cost and writes before any non-trivial execution. Manual UI review stays with the user unless requested.

Gate: upstream operations supply the complete effects without requiring Publish to filter, infer dependencies or generate output. Record: not started.

### [ ] IDP.3 — Queue-Only Publish

- [ ] Apply queued document/media/shared Preview and distribution units with retained progress and exact removals.
- [ ] Remove unconditional shared preparation, full snapshots, corpus comparisons, remote listings and data validation from the normal call path, including reused Catalogue/shared helpers.
- [ ] Make empty queues a no-op and preserve selected partial-failure/manual-retry behavior without a new ledger or recovery layer.

Verification budget: focused lint/syntax and bounded call-path review for forbidden scans/builds/validation. Any existing executable selection must have understood coverage and an accepted cost/effect budget. Live Publish and real destination/media deletion remain explicit actions.

Gate: Publish consumes only the supplied queues, reads only selected artifacts and performs no corpus reconciliation or data validation. Record: not started.

### [ ] IDP.4 — Code Review And Selected Evidence

- [ ] Review the final bounded diff for complete handoffs, selection loss, hidden full passes, validation in reused helpers, public/private projection leaks, dependency omissions and retained-progress correctness.
- [ ] Resolve findings and rerun only evidence affected by changes. Record exact evidence and material omissions without treating a check count as whole-workflow confidence.

Verification budget: distinct bounded review and only the already justified evidence affected by findings; no automatic suites, benchmarks or browser tests.

Gate: findings are resolved and evidence supports the exact proposed contract. Record: not started.

### [ ] IDP.5 — Acceptance, Durable Transfer And Closeout

- [ ] Obtain user acceptance of ordinary and representative collection publication, eligibility/dependency effects, exact media/shared selection and empty-queue behavior, with unexercised variants stated.
- [ ] Transfer shipped ownership and lifecycle rules to the appropriate durable publication/generation documentation and update [Development Checklist](../Development_Checklist.md) guardrails where the implemented boundary changes them.
- [ ] Update this delivery, Planned Features and the predecessor's follow-on state. Present a retain/archive recommendation; document deletion requires approval.

Verification budget: reconcile acceptance with recorded evidence and inspect documentation/navigation changes; do not repeat generation or Publish solely for closeout. Git commit/push and public deployment remain separate explicit actions.

Gate: the complete outcome is accepted, durable owners are current and remaining evidence limits are visible. Record: not started.

## Follow-on

Orphan-media cleanup, new publication eligibility rules, automatic Search freshness, background publication and atomic multi-destination deployment are outside this delivery. Complete upstream maintenance remains an explicit operation and must not return as a normal Publish fallback.

[[links|related links]]
