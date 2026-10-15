---
draft: false
doc_id: d-20261012-112453-211357
title: Incremental Document Publish
added_date: "2026-10-12 11:24:53"
last_updated: "2026-10-15"
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

Prerequisite cleanup on 2026-10-13: the user approved M.25/M.28/M.29 review groups 1–4, implemented through the existing Publish owners. They remove repeated queue/content audits, reuse Catalogue setup/media inputs and limit browser follow-through to reported Recent persistence. [User Facing Rules](../data/User_Facing_Rules.md) records implementation and evidence. Groups 5–7 remain gaps for this delivery: the unconditional full source/eligibility/build/snapshot pass, complete repository/referenced-media reconciliation including remote listings, and selected shared/document/media completion. The 2026-10-15 failure decision below replaces the earlier retained-progress/retry proposal. Document-media storage has subsequently been cut over by the prerequisite below. This cleanup does not approve this delivery's implementation or satisfy its queue-only/no-op/completion gates.

Prerequisite complete on 2026-10-15: [Document Media Working And Preview](Document_Media_Working_And_Preview.md). The user confirmed the baseline Publish and both manual media copies, accepted ordinary/collection media checks after the code cutover and retired the former shared folder. Working owns local/input document media, temporary publication output is isolated, and prepared media is copied into Preview for distribution. Static checks/path diagnostics and source review passed; no post-cutover Publish observation was supplied. This delivery inherits that established media baseline and retains ownership of exact queue effects, selected completion and queue-only operation; its implementation remains unapproved.

Complete proposed result: Save/build owners prepare exact public artifacts and record their completed writes/removals; Publish applies only those queued effects to Preview and configured repository/R2 destinations. Unselected files retain their bytes. When all publication queues are empty, Publish performs no publication work.

Cutover baseline agreed on 2026-10-15: before delivery starts, the user will complete a Full Working Build followed by Publish through the existing workflows and ensure all existing queues are empty. The user will make no further document updates during delivery. Initialise the new Docs queue empty against that published baseline; no pending-removal migration or full eligible-set republish is required. Any new prepared public Working artifacts and saved metadata are populated upstream as implementation setup, without automatically queuing the already-published baseline. The user's baseline Full Build, Publish and empty-queue confirmation remain pending.

Failure contract agreed on 2026-10-15: Publish stops at the first error and reports the cause, target/phase and any already completed effects. Diagnosis and correction are manual; running Publish again is appropriate only after that review determines it will work. Queue membership records unfinished selections, not resumable Preview/distribution progress. Remove the proposed progress flags and existing Catalogue resume branching within this delivery; add no retry guarantee, recovery procedure or authoring lock.

Readiness cleanup on 2026-10-15: the user requested removal of unused Catalogue document-media ownership while preserving separate Work media. Workspace schema v7 now declares document-media ownership per collection; Catalogue remains registered for documents but has no document-media configuration, local namespace, producers/report scans or public media bindings. Work-media paths and deployment inputs are retained. Focused static checks, read-only path/import diagnostics and source review passed; [Media And Asset Handling](../Media_And_Asset_Handling.md#docs-media-inventory-report) records the ownership review and evidence limits. This cleanup does not approve or implement the proposed publication queue.

## Review Handoff — 2026-10-13

The [User Facing Rules](../data/User_Facing_Rules.md) prerequisite review has completed its agreed code cleanup. M.01–M.04 are agreed with no code changes; all six Settings/Export/package groups for M.05/M.06/M.22 are implemented with manual checks pending. Earlier source/generation, discovery, Catalogue Regenerate and Publish cleanup records remain in that document. This handoff preserves the existing Incremental Document Publish gaps and does not approve implementation or close IDP.0.

Key findings to carry into the Publish delivery:

- The browser owns editorial availability and choices resolvable from loaded state. Exact invoked/displayed targets and ordinary/collection identity remain separate. The 2026-10-15 default-document cleanup retires Settings and its writes. One design-time default applies to local/public readers; browser configuration stays owned by the config projector and site-code-update inventory, outside this publication queue.
- Export capability discovery checks configured locations without document-payload audits; subtree/workspace actions use loaded IDs and add no capability refresh. Export consumes its server response directly, retaining its separate overwrite confirmation, one Apply comparison and one output file-set/byte verification. Those guards belong to user-owned Export; they do not justify another Publish planning, confirmation or destination-reconciliation pass.
- Package options now makes one metadata-only request for captured subtree/checked targets. Application Prepare trusts final UI IDs/formats, reads selected sources once and uses saved relationship metadata plus a lazy content renderer; tree output needs no manifest or renderer. CLI selection and returned-package validation retain their independent owners. Reuse these ownership principles when preparing public artifacts upstream, without moving package/source validation or body rendering into Publish.
- Source/generation and Catalogue owners already carry resolved inputs and completed effects through their operations. Docs Viewer trusts Refresh-owned generated Catalogue data through completed handoffs; Catalogue queues preserve existing media selections and initialized progress. Publish cleanup removed repeated queue/content/identity/manifest/Mermaid audits and reused selected media inputs. Required parsing, exact configured artifact authority, path/symlink confinement and selected transfer/output verification remain execution concerns.
- Busy/status flow reports actual completion and partial effects. Publish refreshes Recent only after its response reports completed Working persistence and adds no detached capability refresh. Preserve that completion-driven follow-through when Recent moves upstream; do not retain a redundant Publish-time Recent write solely to support the current marker.

Ownership and structure are contributing concerns to address within this delivery. The reviews suggest that starting from existing server helpers, reusing full generation contexts and hiding dependencies in shared state can bring unnecessary preparation/audits into simple operations. Small files alone do not resolve that coupling. [Development Checklist](../Development_Checklist.md#workflow-ownership-and-structure) now owns the cross-app principles; apply them here without a blanket language migration or unrelated module-splitting delivery:

- Choose the decision owner from the required data and agreed local operating model. The frontend owns loaded-state choices and awaited user-visible completion; Python owns required upstream artifact preparation and selected filesystem/media transfers. Existing server code must not pull browser-owned choices or upstream generation into Publish.
- Separate public preparation and queue handoff from selected Preview application and destination transfer. Give each responsibility narrow inputs/outputs and explicit side effects. Reuse existing projection/rendering owners with supplied selected inputs; avoid a general builder/context loader whose defaults recapture the corpus or repeat authoring validation.
- Keep one visible Publish workflow owner for supplied selections, Preview writes/removals, destination transfers, completed selection removal and stop-on-error reporting. Carry the resolved workspace, parsed queues and completed artifact/effect identities forward. Empty queues must return before expensive setup, and required selected work must be visible at the call site.
- Refactor the relevant responsibility seams while implementing IDP.1–IDP.3 when that removes an implicit dependency or unnecessary pass. Do not treat file-size reduction as completion evidence or expand this delivery into repository-wide restructuring. Required maintenance/full-generation owners remain separate and explicit.
- IDP.4 must trace reused Catalogue/shared/build/transfer helpers beyond the changed lines, including constructors, mixins and missing-input branches, for hidden reads, rendering, scans or audits. Record the removed work, clarified ownership and justified retained execution checks. Normal-use failures or surprising processing costs should guide bounded follow-up fixes; this adds no automatic tracing, benchmark or test infrastructure.

The remaining gaps map to the existing delivery steps:

| Review entries | Remaining Publish work | Delivery owner |
| --- | --- | --- |
| M.18/M.19 | Ordinary and non-Catalogue generation, including exact Rebuild, lacks a completed public-artifact/effects queue handoff. External source/policy edits can still enter publication through Publish's current source capture. Prepare and queue writes/removals upstream across application and CLI paths; deliberate external edits require explicit owning generation. | IDP.1 |
| M.26 | Publish still calculates eligibility from current sources. Upstream owners must supply exact subtree/host withdrawal/restoration, move and affected rendered-dependency effects using sufficient saved private metadata. Missing prerequisites require explicit upstream repair, without a corpus-scan fallback in Publish. | IDP.2 |
| M.27 | Recent and eligible Selected are still prepared during Publish; Search is copied every time without a queued transfer. Full Working Build prepares and queues Recent; move eligible Selected effects upstream and queue explicit Search rebuild bytes, plus finished public index/manifests. Unqueued shared output remains untouched; ordinary edits do not automatically refresh Recent or Search. | IDP.2 |
| M.25 | Empty Catalogue selections still enter full source/eligibility/build/shared-snapshot preparation; ordinary/other collection queues do not exist. Remove the unconditional pass and consume completed selections only. All publication queues empty must produce no generation, transfer, deletion, scan or timestamp-only change. | IDP.1/IDP.3 |
| M.28 | Shared distribution still depends on a complete snapshot, repository-tree comparison and referenced-media reconciliation, including remote family listings. Apply exact document/shared writes and removals plus referenced document-media writes through existing destination owners, verifying only selected transfers and retaining unselected bytes. Document-media deletion remains manual. | IDP.2/IDP.3 |
| M.29 | Catalogue currently retains per-Work Preview progress and resume branching. The agreed target is stop-and-report on the first error, with manual diagnosis/correction and no simple-retry guarantee. Remove the progress/resume machinery while retaining completed effects and removal of successfully distributed selections. | IDP.3 |

Before implementation, IDP.0 must reconcile the accepted rules with the saved eligibility/dependency metadata, Full Build-owned Recent generation, exact media effects and agreed pre-delivery Full Build/Publish baseline. Interrupted publication is a manual diagnosis/correction process, not a prescribed retry sequence or a reason to add authoring locks. These decisions must not introduce resume/progress machinery, automatic retry, rollback, polling, a second ledger, compatibility aliases or a normal Publish reconciliation fallback.

Evidence remains focused lint, syntax/import diagnostics and distinct source/diff review recorded in User Facing Rules. Live/manual acceptance is pending; no tests or live Settings/Export/Prepare/Build/Refresh/Regenerate/Publish were run for the cleanup. Existing retired-contract tests require separately agreed review/migration, and this note adds no test scope. This handoff edit is documentation only, so code review is not applicable; bounded documentation review and whitespace checking apply. Keep the delivery proposed and all implementation/acceptance gates open until their own approval and evidence are recorded.

## Requirements

- **Publish is strictly queue-only. It performs no corpus reconciliation or data validation.** It trusts the completed artifacts and effects supplied by upstream owners.
- Publish does not load document sources, recalculate eligibility, expand dependencies, render Markdown, prepare public payloads, generate media, rebuild discovery data, check links or audit document/collection/Catalogue content.
- Publish does not enumerate source/output directories or remote media to rediscover changes, infer deletion from absence, compare complete corpora, hash complete snapshots or establish whole-corpus consistency.
- Every published document/shared output has an explicit queued write/removal; Docs-owned document media has queued writes only. Document-media deletion remains manual, and a possible cleanup workflow belongs outside Publish. There is no unconditional final preparation or distribution pass and no missing-queue fallback to reconciliation.
- Preserve the single awaited empty-body `POST /docs/publish` action, configured storage/destinations and synchronous operation ordering. Working owns generation; Preview retains the last applied publication artifacts; distribution consumes those Preview bytes.
- Publish treats prepared Working document/media artifacts as read-only. It updates publication queue metadata in Working for completed selection removal and completion timestamps, without intermediate Preview/distribution progress flags. Published-artifact writes and deletions target Preview and configured deployment destinations. Document-media stage ownership and its initial baseline come from the prerequisite delivery.
- Ordinary documents use their immutable document identity. Non-Catalogue collection documents additionally carry the exact configured collection identity. Catalogue Work/Gallery/Series selections retain their existing queue owner and are not duplicated in a generic document queue.
- Complete upstream handoffs and queue persistence before reporting generation complete. Failed queue persistence must report generated-but-incomplete publication handoff rather than silently lose the selection.
- Keep full generation, validation and repair in explicitly requested upstream maintenance operations. Such an operation may generate and queue a complete corpus; Publish still consumes only its supplied queue. Initial cutover uses the agreed pre-delivery Full Build/Publish baseline and an empty Docs queue.

Queue decoding, configured destination/path confinement, missing required transfer inputs and filesystem/network failures remain execution boundaries. An unreadable or unprocessable queue stops the operation. These boundaries do not authorize content/schema validation, membership agreement checks, readiness checks or an audit of queued or unqueued data inside Publish. Transfer completion evidence is limited to the selected writes/removals.

## Eligibility And Dependencies

Eligibility and dependency resolution belong to authoring/generation owners before publication selections are merged. Publish neither filters the queue nor adds work to it. Entry creation means the necessary preparation has completed; there is no Publish-time readiness check against an earlier queue or current source.

The current eligibility baseline is explicit boolean `draft` for ordinary and non-Catalogue collection documents, descendant exclusions for ordinary unpublishable/draft roots, and exclusion of a configured collection when its ordinary host is excluded. Catalogue documents have fixed intrinsic eligibility without a draft field. Collection publication and Search inclusion are separate decisions. Confirm the rules still required after the prerequisite review rather than preserving every existing branch by default; the effect selections below must then follow the accepted rules. Root-level collection hosts are a documented layout convention, not a new validation requirement.

Collection-host scope agreed on 2026-10-15: Catalogue is a document collection and follows the existing host-eligibility rule. Its document and manifest effects are sufficient; host exclusion does not withdraw Catalogue JSON or Work media or delete canonical Work records. No additional Catalogue validation or workflow adjustment is required. The UI no longer offers Draft or Delete for collections, so changing a collection host's eligibility or removing the collection would be a design-time change handled by its owning development delivery.

| Upstream change | Required completed publication selection |
| --- | --- |
| Create or edit an eligible document | Its prepared public document and any affected public metadata/output. |
| Delete a document or make it ineligible | Exact document removals and affected public index/manifest and Selected output. Recent refreshes on Full Working Build. The removal identity survives source/generated deletion. |
| Exclude a parent subtree | Exact removals for the affected descendants as well as the parent, with the corresponding shared-output changes. |
| Restore a subtree's eligibility | Prepared writes for every newly eligible document and the corresponding shared-output changes. |
| Move a document between parents | Effects for any inherited eligibility change, index placement and affected rendered dependencies. |
| Exclude or restore a collection host | Exact collection document and public manifest removals/writes under the existing document-collection eligibility rule, including Catalogue. |
| Change a title, relationship or other rendering input | Prepared writes for affected dependent documents, including rendered Related Links, when their public presentation changes. |
| Change publication policy or configuration outside an application write | An explicit owning generation/maintenance operation resolves the affected identities and queues their effects. Publish does not discover the external edit. |

Use saved hierarchy, collection and relationship metadata to select affected identities where available. Upstream owners must retain sufficient private metadata for scoped eligibility and dependency calculations; public document metadata must not acquire private draft/readiness fields. Do not introduce a full-source dependency scan merely to compensate for a missing upstream handoff.

An explicitly requested complete maintenance build can establish or repair those metadata prerequisites. Missing required saved metadata during an incremental operation stops that operation with an explicit repair requirement; Publish does not supply the repair.

Dependency completion is part of the originating operation's generation handoff. Updating a relationship record alone is insufficient when another document embeds the changed presentation. Its completed public payload must also be queued. This applies across ordinary and collection boundaries without transferring Catalogue generation ownership to Docs Publish.

## Deliverables

### Docs Publication Queue And Handoff

Agreed file: `working/docs-publish-pending.json`, relative to the configured Docs workspace root. It stays alongside `working/catalogue-updates-pending.json` and `working/catalogue-publish-pending.json` so queue state remains together. This file is private workflow metadata, not an artifact copied into Preview or deployed. Upstream owners merge completed selections; Publish removes successfully distributed selections and records completion. Prepared Working artifacts remain read-only during Publish. The queue structure, field names and shared-output labels below are agreed; artifact paths resolve through their configured owners.

| Selection family | Pending writes | Pending deletions | Supplied publication identity |
| --- | --- | --- | --- |
| Documents including referenced media | `current_documents` | `deleted_documents` | Exact document ID, optional configured collection owner and nested `media` type/relative filename lists for current documents. |
| Shared outputs | `current_shared_outputs` | `deleted_shared_outputs` | Exact owner/output name, such as the ordinary public index, collection manifest, Recent, Selected or Search. |

**Current** means selected completed bytes awaiting Preview application and/or deployment; these maps are pending selections, not complete inventories. **Deleted** means the selected artifact must be deleted from `preview/` and its configured deployment destinations. It describes the publication effect, including eligibility withdrawal. A deleted selection retains the target identity needed to complete those deletions and requires no corresponding Working input bytes.

Queue entries supply identities, with current/deleted map membership selecting the document/shared-output effect. Each current document carries its own referenced media in a nested `media` object; there is no separate media queue family. Entries supply no absolute paths, destination providers or new publication authority. Repeated completed saves replace that document's entry with its latest prepared payload identity and eligible saved media references, without deduplicating media across documents. For documents/shared output, a later deletion moves the identity into the corresponding deleted map and a later completed write moves it into the current map; an identity occurs in only one of its family's current/deleted maps. Document media has no deletion map. Each document, including its referenced media, is one publication unit; shared selections retain their own completion units.

Source Save, Create, Import, Move, Delete, exact Rebuild and CLI generation use one common generation-to-publication handoff. The generation result supplies its completed target writes/removals and affected shared artifacts; services do not each rediscover that selection. An explicitly requested Rebuild can queue replacement even when generated bytes are unchanged, so it can repair missing publication output without a Publish-time comparison.

Queue entries carry no intermediate progress state. A failure leaves completed effects where they occurred and stops the operation; manual diagnosis determines the corrections and whether another Publish is appropriate. Successful unit removals already persisted remain complete; failed or unprocessed selections are not cleared on error.

#### Example Pending Record Shape

The following `working/docs-publish-pending.json` example shows the agreed queue structure with illustrative document IDs and filenames, following the JSON example and field-ownership format in [Incremental Updates](Incremental_updates.md#pending-record-shape-1). All selection families use objects keyed by their identities. The example uses the configured `concepts` collection, omits `collection` for the ordinary document and uses `workspace` for workspace-wide shared outputs. Each current document lists its own media. Artifact locations and repository/R2 destinations come from their configured owners, not from this file.

```json
{
  "header": {
    "schema": "docs_publish_pending_v1",
    "last_published_at_utc": null
  },
  "current_documents": {
    "d-20261014-090000-001a2b": {
      "media": {
        "img": ["guide-overview.png"]
      }
    },
    "d-20261014-091000-003c4d": {
      "collection": "concepts",
      "media": {
        "svg": ["concept-map.svg"]
      }
    }
  },
  "deleted_documents": {
    "d-20261012-100000-005e6f": {},
    "d-20261012-101000-007a8b": {
      "collection": "moments"
    }
  },
  "current_shared_outputs": {
    "workspace": {
      "ordinary_index": {},
      "search": {}
    },
    "concepts": {
      "collection_manifest": {}
    }
  },
  "deleted_shared_outputs": {
    "moments": {
      "collection_manifest": {}
    }
  }
}
```

This example selects writes for an ordinary document and a Concepts document, each with its own referenced media, plus shared outputs. The deleted maps select removal of an ordinary document, a Moments document and public manifest from Preview and deployment destinations. Document media has no queued deletion. A current document without media can omit `media`; an ordinary document without media therefore has an empty record. Empty document/shared-output records still select work through their enclosing keys. No entry contains progress flags. The Search selection represents a completed explicit Search rebuild; the document changes do not imply it. Recent and Selected use the workspace shared-output shape when their owners explicitly contribute them.

Document IDs are immutable and unique across the whole corpus. `current_documents` and `deleted_documents` are keyed by document ID, following the Catalogue queue pattern; the ID is not repeated inside each value. Document `collection` is routing metadata for its configured owner, not part of the queue key; ordinary documents omit it, while named collection documents supply it.

Each current document's optional `media` object maps media types directly to owner/type-relative filename lists. The document's existing optional `collection` resolves both its payload owner and media namespace; routing metadata is not repeated for media. Several document records may contain the same physical media identity; Publish processes them independently, with no cross-document deduplication pass, shared transfer registry or suppression of repeated checks. Complete one document and all its referenced media before removing that document's queue entry and moving to the next document. No per-file progress is persisted. Deleted document records carry no media because document-media deletion remains manual.

Both shared-output maps remain keyed by owner, then output name, using `workspace` or the exact configured non-Catalogue collection ID. Each document entry including its media, and each shared-output entry, is one publication unit. Repeated document/shared contributions update their existing identity; repeated eligible document preparation replaces the document's nested media references along with its entry. An empty selection-family object selects no work, while an empty document/shared-output record at a supplied identity selects that unit. All publication queues empty retain the no-op behavior specified above. Publish owns the required document-before-shared sequencing rather than deriving it from JSON member order.

#### Field And Selection Ownership

| Field or selection | Meaning | What updates it | What reads it |
| --- | --- | --- | --- |
| `header.schema` | Identifies the agreed queue representation; it does not assert corpus validity or publication readiness. | Queue initialization establishes it; contributors and Publish preserve it. | The queue owner and Publish decode the agreed representation. |
| `header.last_published_at_utc` | Nullable UTC time of the last completed nonempty Docs publication queue, covering its document units including media and its shared-output units. | Initialization sets null. Publish records completion in the same queue write that removes the final successfully distributed unit. Upstream contributors, partial failures and initially empty Publishes preserve the previous value. | Queue inspection reports completed Docs queue publication independently of Catalogue publication. |
| `current_documents` membership | A completed public document artifact and its nested media references await selected Preview/deployment completion as one unit. Membership selects a write without a separate action flag. | Completed generation adds/coalesces entries; completed deletion replaces a write. Publish removes the entry only after the document and all its supplied media complete successfully. | Publish processes the supplied documents one by one, including each document's media. |
| `deleted_documents` membership | Exact owned document files await deletion from Preview and deployment destinations, including publication eligibility withdrawal. | The upstream owner contributes the exact deletion selection; a completed write replaces it; Publish removes each successfully distributed entry. | Publish deletes the selected output using the retained identity, without requiring Working input bytes or inferring deletion from absence. |
| Document-map key | Immutable document ID, unique across the whole corpus, used directly as the key in `current_documents` or `deleted_documents`. | The originating generation/deletion owner supplies it and coalesces completed effects under that key. | Publish resolves the exact document artifact and deletion targets through the supplied owner. |
| Document `collection` | Routing metadata naming the exact configured non-Catalogue collection owner for both the document and its media; omitted for ordinary documents and not part of the queue key. | The collection's generation/deletion owner supplies it. | Publish resolves the configured document/media owner without rediscovering membership. |
| Current document `media` | Optional media-type keys containing owner/type-relative filename lists. The same file may occur under several documents. | Eligible preparation supplies all referenced ready media in the document entry. Known media-byte changes requeue an eligible referring document with its existing prepared payload and complete saved media references. | Publish checks/transfers these files as part of that document's unit, without reference/eligibility rechecks or cross-document deduplication. |
| Media filename list item | Exact filename relative to that document owner's selected media type. | The upstream operation carries references known during preparation. | Publish resolves read-only input bytes and their exact Preview/deployment write targets. |
| Shared-output owner key | `workspace` or the exact configured non-Catalogue collection owning the shared output. | The owning upstream operation supplies it; shared-output deletions retain exact identities before configuration authority is lost. | Publish resolves the configured shared-output owner. |
| `current_shared_outputs` membership | Explicit finished shared bytes await Preview writes and deployment; an empty document queue does not clear these selections or trigger a shared build. | Index/manifest, Recent, Selected and Search owners contribute finished writes; Publish removes each successfully distributed entry. | Publish transfers shared selections after their required item work. |
| `deleted_shared_outputs` membership | Exact shared artifacts await deletion from Preview and deployment destinations. | The owning upstream operation contributes exact deletion identities; Publish removes each successfully distributed entry. | Publish deletes the supplied owned shared outputs after their required item work. |
| Shared output key | Allowed logical output name beneath its owner key. | The corresponding upstream output owner supplies it and coalesces effects at that key. | Publish resolves the allowed artifact through configuration; the label grants no new file authority. |

#### Schema Values

| `header.schema` value | Meaning |
| --- | --- |
| `docs_publish_pending_v1` | Agreed first representation of this Docs publication queue. This label does not imply that the queue has been implemented. |

#### Publication Timestamp Values

| `header.last_published_at_utc` value | Meaning |
| --- | --- |
| `null` | No completed nonempty Docs publication queue has been recorded yet. |
| UTC timestamp string | Time when the final selected unit completed distribution and this Docs queue became empty. |

This timestamp records Docs queue completion independently of Catalogue publication and makes no claim about whole-corpus freshness. An initially empty Docs queue leaves it unchanged, preserving the no-op behavior.

#### Collection Values

The following current values apply to document `collection`, which also owns its nested media, and collection-owned shared-output owner keys. They come from `stages.working.collections` in [Docs Workspace Configuration](../../../docs-viewer/config/workspace/docs-workspace.json). Ordinary documents omit `collection`; workspace-wide shared output uses `workspace`. Future collection values require explicit configuration/registration through their owning delivery. Deleted document/shared selections retain their exact former identities through completion.

| Collection value | Configured collection |
| --- | --- |
| `works` | Context documents; distinct from Catalogue Work records and Work media. |
| `concepts` | Concepts documents. |
| `moments` | Moments documents. |

`catalogue` is also configured, but its document, Work/Gallery/Series, media and shared selections retain their existing Catalogue queue ownership and are not duplicated in this Docs queue.

#### Owner Values

This table applies to owner keys directly beneath `current_shared_outputs` and `deleted_shared_outputs`. Document media uses the containing document's optional `collection` instead.

| Owner key | Meaning |
| --- | --- |
| `workspace` | Workspace-wide shared outputs. |
| `works` | Shared outputs owned by the Context collection. |
| `concepts` | Shared outputs owned by the Concepts collection. |
| `moments` | Shared outputs owned by the Moments collection. |

#### Media Type Values

These ready-media types follow the workspace's configured media families and [Media And Asset Handling](../Media_And_Asset_Handling.md#workspace-configuration-and-storage). Editable `mermaid`/`build-source` inputs are upstream preparation inputs; their completed public SVG output is queued under `svg`.

| Type key beneath a current document's `media` | Meaning |
| --- | --- |
| `img` | Ready raster images. |
| `thumbs` | Document thumbnail derivatives. |
| `svg` | Ready SVG assets, including completed Mermaid diagram output. |
| `files` | Downloadable files. |
| `html` | Ready HTML media and its owned companion assets. |

#### Shared Output Values

These are the agreed logical output names for this delivery. Their configured owners resolve the finished artifacts and exact destinations; they are not filesystem paths or destination-provider selectors.

| Output key | Owner | Meaning |
| --- | --- | --- |
| `ordinary_index` | `workspace` | Finished public ordinary-document navigation index. |
| `recent` | `workspace` | Finished eligible Recent output prepared by Full Working Build. |
| `selected` | `workspace` | Finished eligible public Selected output. |
| `search` | `workspace` | Exact bytes from an explicitly completed Search rebuild. |
| `collection_manifest` | `works`, `concepts`, `moments` | Finished public manifest for that exact non-Catalogue collection. |

Document IDs and media filenames are exact supplied identities rather than enumerated options. These tables describe the agreed queue handoff; they do not add Publish-time authoring validation, content audits or configuration-discovery scans.

### Prepared Public Artifacts

Generation prepares the final public form, including configured collection field projection, public URLs, local folder-link treatment and Mermaid presentation. Reuse the current public projection/rendering owners rather than copying their rules into a new queue or publisher.

Where local and public document forms differ, retain the public form as replaceable generated output within Working. This is not a new storage stage, persistent Preview source tree or independent source authority. Publish transfers these finished bytes without parsing or transforming document content.

### Explicit Shared Output

Upstream generation maintains the public ordinary index and affected collection manifests from known changes and saved metadata, then queues their finished files. Assembly of a selected aggregate may serialize its complete metadata inventory upstream; it does not cause Publish to read or rebuild the document corpus. Unselected aggregates remain untouched.

Recent ownership agreed on 2026-10-15: Full Working Build generates Recent using its existing coverage, eligibility, exclusions and limit, then queues the finished file. Ordinary document operations, including Save, exact Rebuild, Delete and eligibility changes, preserve saved Recent until the next Full Working Build. Publish transfers only queued Recent bytes and performs no Recent generation or freshness checks. This requires no incremental Recent candidate store or per-document Recent maintenance. External Recent-policy edits take effect through Full Working Build.

Star/Unstar, metadata refresh and eligibility/deletion effects prepare and queue the public Selected payload upstream while retaining excluded selections in the Working source list. Starring continues to preserve document modification dates.

Search retains its explicit Working rebuild owner and complete-index format. A completed explicit Search rebuild queues its exact bytes. Ordinary document changes neither rebuild Search nor queue it automatically; Publish leaves an unqueued Search index untouched and performs no freshness or membership checks.

Public browser configuration is design-time output and remains in the site-code-update inventory. It has no shared-output queue entry and Publish does not write it. One configured default document applies equally to local/public readers; Settings and deletion-time default clearing are retired. Removing a collection or changing output layout still requires the owning development delivery to supply exact document/shared artifact removal identities before its former configuration authority is lost.

### Exact Document-Media Effects

Agreed on 2026-10-15: queue only media referenced by eligible saved documents. Adding media stores Working bytes immediately but an unsaved/cancelled Source buffer supplies no publication reference. Orphaned and draft-only media remains local for manual cleanup; removing a saved reference does not automatically delete stored or published media.

Completed eligible Save/Import/Rebuild and eligibility-restoration preparation supply all media references for each selected document, including assigned thumbnails and completed public Mermaid output. Store these under `media` in that document's current record. No comparison of media bytes or detection of which referenced files changed belongs in Save. There is no cross-document deduplication: when two queued documents reference the same file, Publish processes each document's supplied reference independently.

Media intake/production supplies known same-name byte changes only through eligible saved document reference metadata. Requeue the eligible referring document with its existing completed public payload and complete saved media references; changing media bytes alone requires no document rerender. Thus replacing media used by another eligible saved document still queues that saved document and its media even if the current Source edit is cancelled. Intake alone does not make an otherwise unreferenced file publishable. Referencing a Work or Gallery does not implicitly queue that Catalogue's media; its existing owner supplies any required Catalogue effects.

Maintain each document's saved media references upstream to carry exact identities and handle reference/eligibility changes without source/media-directory scans. A later completed save replaces that document's pending entry including its media lists. Removing a document or excluding it replaces its current record with the exact document-deletion record, which carries no media; other document entries remain untouched. This needs no global reference count or cross-document transfer registry. Publish trusts the supplied records and performs no reference/eligibility recheck.

For each supplied file, Publish copies/compares its Working bytes into Preview and compares the selected R2 object's size and ETag with the Preview byte count and checksum through an exact-object metadata request. Matching remote bytes skip upload; missing/different bytes are uploaded and verified. No remote family listing or cross-document cache suppresses repeated checks: a shared file encountered under another document is checked again and can then skip upload because it matches. These are selected transfer comparisons, not corpus reconciliation or domain-data validation.

Preserve ordinary Source Save's exclusion of registered media scanning, detection and production. Reuse the references known during rendering and the completed media owner's selections; an infrequent persistent media-source edit still uses the explicit media/docs build workflow before Publish.

Deletion scope agreed on 2026-10-15: document-media deletion remains manual and is excluded from this queue and delivery. Removing a document/reference, losing its eligibility or deleting a file manually creates no media-deletion selection. Updating/removing that document's no-longer-required pending media references changes only queue membership; existing Working, Preview and deployed bytes are retained for manual cleanup. Publish performs no reference/ownership scan, missing-file reconciliation, orphan cleanup or remote listing. Existing Catalogue Work/media deletion retains its separate domain owner; this decision concerns Docs-owned document media.

### Selected Preview And Distribution

Replace the complete-snapshot preparation/distribution dependency with selected application through the existing publication owners. Preserve Catalogue per-Work selection ownership and adapt its shared consumer to execute only queued Gallery/system-file effects. Remove existing Catalogue Preview-progress flags and resume branching so all publication units follow the agreed stop-and-report failure contract. Remove content-validation and whole-snapshot requirements from the normal Publish call path, including those that would otherwise be reached through a reused helper.

Publication completion records successful selected work. It must not certify all untouched Preview/destination files, require a complete snapshot inventory or rescan/hash them to produce a receipt. Retire obsolete complete-corpus checks from the normal path without compatibility aliases, shadow copies or a second publication ledger.

## Process

```text
Authoring/build operation
  -> complete local/public generation and upstream eligibility/dependency effects
  -> merge exact completed publication selections
Publish
  -> complete each queued document with its nested media in Preview and deployment
  -> apply queued shared output after its required item work
  -> remove only successfully distributed selections
```

For each current document, apply its supplied media and prepared document bytes to Preview, distribute its media and then its document payload to the configured destinations, and remove the document entry only after all required transfers succeed. Complete this document before starting the next. A failed media/document transfer stops Publish with that document entry still present and earlier effects left in place; there is no per-media progress or persisted checkpoint between Preview and distribution. Deleted documents apply only their supplied document removals. Queued shared output uses the same completion boundary after the required documents; an item queue becoming empty must not erase unfinished shared selections or trigger a new shared build.

Unselected files remain in place. Missing owned deletion targets count as successful removal. All queues empty means no copies, uploads, deletions, generation, corpus validation or timestamp-only output changes.

On any error, stop immediately and report the cause, exact target/phase and already completed effects. Do not run recovery actions or failure-specific queue rewrites. Earlier successful writes, deletions and queue removals remain; failed/unprocessed selections are not cleared. The user diagnoses and corrects the cause and decides whether running Publish again will work. Neither the queue nor Preview guarantees a safe retry, and the application adds no resume logic, automatic repair, rollback, backup tree, transactional swap, authoring lock or concurrency/freshness scan. Repository/R2 effects remain non-atomic, and temporary differences between item and shared output remain possible during an incomplete operation.

External Markdown and policy edits require explicit owning generation before Publish. An omitted queue contribution remains unpublished until its owner queues it. A global renderer/configuration change uses an explicit maintenance build to generate and queue the required set; normal Publish has no bootstrap or drift-repair mode.

## Delivery Steps

### [ ] IDP.0 — Readiness And Implementation Approval

- [x] Complete [Document Media Working And Preview](Document_Media_Working_And_Preview.md) and carry forward its user-confirmed media baseline and accepted code cutover. Completed 2026-10-15, including local-media acceptance and retirement of the former shared folder.
- [x] Agree failure behavior: stop and report any error; diagnosis/correction and the decision to run Publish again are manual. Agreed 2026-10-15; remove progress/resume machinery rather than adding a retry guarantee or authoring lock.
- [x] Agree media publication eligibility: only references from eligible saved documents contribute media writes; unsaved/cancelled additions remain outside Publish. Agreed 2026-10-15.
- [x] Queue all referenced media nested inside each eligible current document record and complete Publish document by document, without a separate media family or cross-document deduplication. Shared files may be checked repeatedly; exact-object size/ETag comparison skips unchanged R2 uploads.
- [x] Keep document-media deletion manual and remove it from this delivery's queue. Agreed 2026-10-15; a possible cleanup delivery would own a separate workflow outside Publish.
- [x] Retire unused Catalogue document-media ownership from configuration, readers/report scans, builders and publication bindings while preserving its document collection and separate Work media. Implemented and statically reviewed on 2026-10-15; live/manual operations remain unexercised.
- [x] Keep public browser configuration design-time-owned, retire Settings and separate local/public default settings, and remove configuration from this queue proposal. Approved 2026-10-15; the existing public default is retained.
- [x] Treat Catalogue host eligibility as the existing document-collection rule, with no additional Catalogue validation or workflow adjustment. Agreed 2026-10-15; collection Draft/Delete controls are already removed, so such changes are design-time-owned.
- [x] Agree Recent ownership: Full Working Build generates and queues the finished Recent file; Publish only transfers queued bytes. Agreed 2026-10-15; ordinary document operations preserve Recent until the next Full Working Build, without incremental candidate maintenance.
- [x] Agree the cutover baseline: the user will complete Full Working Build followed by Publish, ensure all existing queues are empty and make no further document updates during delivery. Agreed 2026-10-15; initialise the Docs queue empty without pending-selection migration or full-set republication.
- [ ] Record the user's confirmation that the pre-delivery Full Working Build and Publish completed and all existing queues are empty before implementation starts.
- [ ] Review the relevant User Facing Rules targets and complete required functional cleanup deliveries, then reconcile the eligibility/dependency assumptions with the accepted targets.
- [ ] Confirm the complete queue-only boundary against the current generation, eligibility, dependency, media and publication owners, including shared Catalogue publication.
- [ ] Confirm saved metadata prerequisites using the agreed cutover baseline and reusing existing records.
- [ ] Obtain explicit implementation approval before code/configuration work. Agree any proposed test work separately under [Test Contract Discipline](../Test_Contract_Discipline.md).

Verification budget: concise read-only owner review; no fixtures, prototype, generated writes, executable tests or live Publish. Stop if required upstream effects or cutover ownership remain unresolved.

Gate: the prerequisite review/required cleanup is complete and one coherent implementation boundary and its genuine stop conditions are approved. Record: proposed; documentation only is authorized. The document-media prerequisite is complete; reconcile the remaining rules review/cleanup and obtain this delivery's implementation approval before proceeding.

### [ ] IDP.1 — Public Preparation And Queue Handoff

- [ ] Implement the Docs queue owner and common completed-generation handoff for application and CLI paths, including deletion and explicit unchanged-byte Rebuild.
- [ ] Prepare final public artifacts upstream through the current projection owners and report incomplete queue persistence.
- [ ] Initialise the Docs queue empty against the user-confirmed published baseline and populate required internal public artifacts/saved metadata upstream, without queuing the unchanged baseline, invoking Publish reconciliation or adding old-format aliases.

Verification budget: focused changed-source lint/syntax and bounded source/output inspection selected after owner inspection. Test work and real workspace writes require their agreed scope; do not add temporary regression scripts without approval.

Gate: completed public artifacts and exact selections are supplied by every in-scope generation path. Record: not started.

### [ ] IDP.2 — Eligibility, Dependencies, Media And Shared Output

- [ ] Complete the distinct eligibility/dependency contract, including subtree and collection-host withdrawal/restoration and affected rendered neighbours.
- [ ] Prepare and queue public index/manifest and Selected effects upstream; queue finished Recent from Full Working Build and connect explicit Search completion without adding ordinary-edit Recent/Search refreshes.
- [ ] Supply each eligible document's complete media references without cross-document deduplication, preserving normal Save's exclusion of media-byte comparison and registered media detection/production; document-media deletion remains manual and outside this delivery.

Verification budget: bounded owner review and selected generated artifacts for the agreed scenarios. Record the exact existing diagnostics/checks, purpose, cost and writes before any non-trivial execution. Manual UI review stays with the user unless requested.

Gate: upstream operations supply the complete effects without requiring Publish to filter, infer dependencies or generate output. Record: not started.

### [ ] IDP.3 — Queue-Only Publish

- [ ] Complete each queued document and its nested media through Preview/distribution before removing its entry and moving to the next document; apply document/shared removals and shared writes without intermediate progress flags.
- [ ] Check each supplied media reference independently with selected size/ETag comparison, skipping unchanged R2 uploads without a global deduplication pass or remote listing.
- [ ] Remove unconditional shared preparation, full snapshots, corpus comparisons, remote listings and data validation from the normal call path, including reused Catalogue/shared helpers.
- [ ] Make empty queues a no-op; stop and report any error with already completed effects, retiring existing Catalogue resume branching without a new ledger or recovery layer.

Verification budget: focused lint/syntax and bounded call-path review for forbidden scans/builds/validation. Any existing executable selection must have understood coverage and an accepted cost/effect budget. Live Publish and real destination writes/deletions remain explicit actions.

Gate: Publish consumes only the supplied queues, reads only selected artifacts and performs no corpus reconciliation or data validation. Record: not started.

### [ ] IDP.4 — Code Review And Selected Evidence

- [ ] Apply the mandatory [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review), including frontend/server ownership, narrow interfaces and hidden dependencies/work in reused helpers.
- [ ] Review the final bounded diff for complete handoffs, selection loss, hidden full passes, validation in reused helpers, public/private projection leaks, dependency omissions, completed selection removal and stop-on-error behavior.
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

A possible follow-on delivery could provide document-media cleanup through its own explicit workflow outside Publish. It would require its own agreed scope; this delivery introduces no cleanup UI, delete operation or cleanup queue. Until then, document-media deletion and orphan cleanup remain manual.

New publication eligibility rules, automatic Search freshness, background publication and atomic multi-destination deployment are also outside this delivery. Complete upstream maintenance remains an explicit operation and must not return as a normal Publish fallback.

[[links|related links]]
