---
draft: false
doc_id: d-20261012-112453-211357
title: Incremental Document Publish
added_date: "2026-10-12 11:24:53"
last_updated: "2026-10-14 15:55:24"
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

Prerequisite agreed on 2026-10-14: complete [Document Media Working And Preview](Document_Media_Working_And_Preview.md) before implementing this delivery. The user will Publish and manually copy the approximately 43 MB ready document-media folder into Working and Preview, then the prerequisite cuts over code/configuration with light verification. That delivery establishes media storage and the publication baseline; this delivery retains ownership of exact queue effects, retained progress and queue-only operation.

Complete proposed result: Save/build owners prepare exact public artifacts and record their completed writes/removals; Publish applies only those queued effects to Preview and configured repository/R2 destinations. Unselected files retain their bytes. When all publication queues are empty, Publish performs no publication work.

## Review Handoff — 2026-10-13

The [User Facing Rules](../data/User_Facing_Rules.md) prerequisite review has completed its agreed code cleanup. M.01–M.04 are agreed with no code changes; all six Settings/Export/package groups for M.05/M.06/M.22 are implemented with manual checks pending. Earlier source/generation, discovery, Catalogue Regenerate and Publish cleanup records remain in that document. This handoff preserves the existing Incremental Document Publish gaps and does not approve implementation or close IDP.0.

Key findings to carry into the Publish delivery:

- The browser owns editorial availability and choices resolvable from loaded state. Exact invoked/displayed targets and ordinary/collection identity remain separate. Settings now validates default membership against the loaded Index, projects browser configuration without a document/media build and applies its returned default without reloads. Committed state and unfinished projection remain distinct, including explicit unchanged-Save recovery. Public configuration still needs its own completed queued contribution in this delivery.
- Export capability discovery checks configured locations without document-payload audits; subtree/workspace actions use loaded IDs and add no capability refresh. Export consumes its server response directly, retaining its separate overwrite confirmation, one Apply comparison and one output file-set/byte verification. Those guards belong to user-owned Export; they do not justify another Publish planning, confirmation or destination-reconciliation pass.
- Package options now makes one metadata-only request for captured subtree/checked targets. Application Prepare trusts final UI IDs/formats, reads selected sources once and uses saved relationship metadata plus a lazy content renderer; tree output needs no manifest or renderer. CLI selection and returned-package validation retain their independent owners. Reuse these ownership principles when preparing public artifacts upstream, without moving package/source validation or body rendering into Publish.
- Source/generation and Catalogue owners already carry resolved inputs and completed effects through their operations. Docs Viewer trusts Refresh-owned generated Catalogue data through completed handoffs; Catalogue queues preserve existing media selections and initialized progress. Publish cleanup removed repeated queue/content/identity/manifest/Mermaid audits and reused selected media inputs. Required parsing, exact configured artifact authority, path/symlink confinement and selected transfer/output verification remain execution concerns.
- Busy/status flow reports actual completion and partial effects. Publish refreshes Recent only after its response reports completed Working persistence and adds no detached capability refresh. Preserve that completion-driven follow-through when Recent moves upstream; do not retain a redundant Publish-time Recent write solely to support the current marker.

Ownership and structure are contributing concerns to address within this delivery. The reviews suggest that starting from existing server helpers, reusing full generation contexts and hiding dependencies in shared state can bring unnecessary preparation/audits into simple operations. Small files alone do not resolve that coupling. [Development Checklist](../Development_Checklist.md#workflow-ownership-and-structure) now owns the cross-app principles; apply them here without a blanket language migration or unrelated module-splitting delivery:

- Choose the decision owner from the required data and agreed local operating model. The frontend owns loaded-state choices and awaited user-visible completion; Python owns required upstream artifact preparation and selected filesystem/media transfers. Existing server code must not pull browser-owned choices or upstream generation into Publish.
- Separate public preparation and queue handoff from selected Preview application and destination transfer. Give each responsibility narrow inputs/outputs and explicit side effects. Reuse existing projection/rendering owners with supplied selected inputs; avoid a general builder/context loader whose defaults recapture the corpus or repeat authoring validation.
- Keep one visible Publish workflow owner for supplied selections, Preview writes/removals, persisted progress, destination transfers and completed selection removal. Carry the resolved workspace, parsed queues and completed artifact/effect identities forward. Empty queues must return before expensive setup, and required selected work must be visible at the call site.
- Refactor the relevant responsibility seams while implementing IDP.1–IDP.3 when that removes an implicit dependency or unnecessary pass. Do not treat file-size reduction as completion evidence or expand this delivery into repository-wide restructuring. Required maintenance/full-generation owners remain separate and explicit.
- IDP.4 must trace reused Catalogue/shared/build/transfer helpers beyond the changed lines, including constructors, mixins and missing-input branches, for hidden reads, rendering, scans or audits. Record the removed work, clarified ownership and justified retained execution checks. Normal-use failures or surprising processing costs should guide bounded follow-up fixes; this adds no automatic tracing, benchmark or test infrastructure.

The remaining gaps map to the existing delivery steps:

| Review entries | Remaining Publish work | Delivery owner |
| --- | --- | --- |
| M.18/M.19 | Ordinary and non-Catalogue generation, including exact Rebuild, lacks a completed public-artifact/effects queue handoff. External source/policy edits can still enter publication through Publish's current source capture. Prepare and queue writes/removals upstream across application and CLI paths; deliberate external edits require explicit owning generation. | IDP.1 |
| M.26 | Publish still calculates eligibility from current sources. Upstream owners must supply exact subtree/host withdrawal/restoration, move and affected rendered-dependency effects using sufficient saved private metadata. Missing prerequisites require explicit upstream repair, without a corpus-scan fallback in Publish. | IDP.2 |
| M.27 | Recent and eligible Selected are still prepared during Publish; Search is copied every time without a queued transfer. Move Recent/Selected effects upstream and queue explicit Search rebuild bytes, plus finished public index/manifests/configuration. Unqueued shared output remains untouched; ordinary edits do not automatically refresh Search. | IDP.2 |
| M.25 | Empty Catalogue selections still enter full source/eligibility/build/shared-snapshot preparation; ordinary/other collection queues do not exist. Remove the unconditional pass and consume completed selections only. All publication queues empty must produce no generation, transfer, deletion, scan or timestamp-only change. | IDP.1/IDP.3 |
| M.28 | Shared distribution still depends on a complete snapshot, repository-tree comparison and referenced-media reconciliation, including remote family listings. Apply exact document/media/shared writes and removals through existing destination owners, verifying only selected transfers and retaining unselected bytes. | IDP.2/IDP.3 |
| M.29 | Catalogue Works retain per-Work Preview progress, but shared retry prepares another snapshot from current Working and shared media uses a live asset root. General document/media/shared units need accurate retained progress and retry from completed Preview bytes, with successful distribution alone removing selections. | IDP.3 |

Before implementation, IDP.0 must reconcile the accepted rules with the saved eligibility/dependency metadata, upstream Recent candidate maintenance, exact media/public-configuration effects and deliberate baseline/cutover approach. Resolve how interrupted publication is completed before further authoring/generation; the current UI does not enforce that rule. These decisions must not introduce automatic retry, rollback, polling, a second ledger, compatibility aliases or a normal Publish reconciliation fallback.

Evidence remains focused lint, syntax/import diagnostics and distinct source/diff review recorded in User Facing Rules. Live/manual acceptance is pending; no tests or live Settings/Export/Prepare/Build/Refresh/Regenerate/Publish were run for the cleanup. Existing retired-contract tests require separately agreed review/migration, and this note adds no test scope. This handoff edit is documentation only, so code review is not applicable; bounded documentation review and whitespace checking apply. Keep the delivery proposed and all implementation/acceptance gates open until their own approval and evidence are recorded.

## Requirements

- **Publish is strictly queue-only. It performs no corpus reconciliation or data validation.** It trusts the completed artifacts and effects supplied by upstream owners.
- Publish does not load document sources, recalculate eligibility, expand dependencies, render Markdown, prepare public payloads, generate media, rebuild discovery data, check links or audit document/collection/Catalogue content.
- Publish does not enumerate source/output directories or remote media to rediscover changes, infer deletion from absence, compare complete corpora, hash complete snapshots or establish whole-corpus consistency.
- Every published document, media item and shared output has an explicit queued write/removal. There is no unconditional final preparation or distribution pass and no missing-queue fallback to reconciliation.
- Preserve the single awaited empty-body `POST /docs/publish` action, configured storage/destinations and synchronous operation ordering. Working owns generation; Preview retains the last applied publication artifacts; distribution consumes those Preview bytes.
- Publish treats prepared Working document/media artifacts as read-only. It updates publication queue metadata in Working for progress, completed selection removal and completion timestamps. Published-artifact writes and deletions target Preview and configured deployment destinations. Document-media stage ownership and its initial baseline come from the prerequisite delivery.
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

Proposed file: `working/docs-publish-pending.json`, relative to the configured Docs workspace root. It stays alongside `working/catalogue-updates-pending.json` and `working/catalogue-publish-pending.json` so queue state remains together. This file is private workflow metadata, not an artifact copied into Preview or deployed. Upstream owners merge completed selections; Publish writes progress, removes successfully distributed selections and records completion. Prepared Working artifacts remain read-only during Publish. The exact schema and artifact locations remain implementation decisions within this boundary, not frozen by this proposal.

| Selection family | Pending writes | Pending deletions | Supplied publication identity |
| --- | --- | --- | --- |
| Documents | `current_documents` | `deleted_documents` | Exact document ID and optional configured collection owner. |
| Media | `current_media` | `deleted_media` | Exact configured owner/type/relative filename. |
| Shared outputs | `current_shared_outputs` | `deleted_shared_outputs` | Exact owner/output name, such as the ordinary public index, collection manifest, Recent, Selected, Search or public configuration. |

**Current** means selected completed bytes awaiting Preview application and/or deployment; these maps are pending selections, not complete inventories. **Deleted** means the selected artifact must be deleted from `preview/` and its configured deployment destinations. It describes the publication effect, including eligibility withdrawal. A deleted selection retains the target identity needed to complete those deletions and requires no corresponding Working input bytes.

Queue entries supply identities, with current/deleted map membership selecting the effect. They supply no absolute paths, destination providers or new publication authority. The queue owner coalesces repeated completed contributions to the latest intended state. A later deletion moves the identity into the corresponding deleted map; a later completed write moves it into the current map. An identity occurs in only one of its family's current/deleted maps. Independent document, media and shared selections remain pending until their own completion.

Source Save, Create, Import, Move, Delete, exact Rebuild and CLI generation use one common generation-to-publication handoff. The generation result supplies its completed target writes/removals and affected shared artifacts; services do not each rediscover that selection. An explicitly requested Rebuild can queue replacement even when generated bytes are unchanged, so it can repair missing publication output without a Publish-time comparison.

Initialize Publish progress only for new publication units. Upstream contributors preserve initialized progress; Publish owns its transitions. Finish an interrupted Publish before resuming authoring or generation, following the existing Catalogue workflow.

#### Example Pending Record Shape

Illustrative `working/docs-publish-pending.json`, following the JSON example and field-ownership format in [Incremental Updates](Incremental_updates.md#pending-record-shape-1). All selection families use objects keyed by their identities. The schema name, field names and shared-output labels remain proposed examples for review, not an implemented or frozen contract. The example uses the configured `concepts` collection and the `workspace` owner for ordinary media and workspace-wide outputs. Artifact locations and repository/R2 destinations come from their configured owners, not from this file.

```json
{
  "header": {
    "schema": "docs_publish_pending_v1",
    "last_published_at_utc": null
  },
  "current_documents": {
    "d-20261014-090000-001a2b": {
      "preview_done": true
    },
    "d-20261014-091000-003c4d": {
      "collection": "concepts",
      "preview_done": false
    }
  },
  "deleted_documents": {
    "d-20261012-100000-005e6f": {
      "preview_done": false
    },
    "d-20261012-101000-007a8b": {
      "collection": "moments",
      "preview_done": false
    }
  },
  "current_media": {
    "workspace": {
      "img": {
        "guide-overview.png": {
          "preview_done": false
        }
      }
    },
    "concepts": {
      "svg": {
        "concept-map.svg": {
          "preview_done": false
        }
      }
    }
  },
  "deleted_media": {
    "workspace": {
      "files": {
        "retired-guide.pdf": {
          "preview_done": false
        }
      }
    }
  },
  "current_shared_outputs": {
    "workspace": {
      "ordinary_index": {
        "preview_done": false
      },
      "search": {
        "preview_done": false
      }
    },
    "concepts": {
      "collection_manifest": {
        "preview_done": false
      }
    }
  },
  "deleted_shared_outputs": {
    "moments": {
      "collection_manifest": {
        "preview_done": false
      }
    }
  }
}
```

This example shows an interrupted Publish: the first ordinary document has completed Preview and still awaits distribution, so the next explicit Publish uses its retained Preview bytes. The Concepts document, current media and current shared outputs still require their Preview writes and distribution. The deleted maps select removal of an ordinary document, a Moments document and public manifest, and an ordinary download from Preview and deployment destinations. The Search selection represents a completed explicit Search rebuild; the document changes do not imply it. Recent, Selected and public configuration use the workspace shared-output shape when their owners explicitly contribute them.

Document IDs are immutable and unique across the whole corpus. `current_documents` and `deleted_documents` are keyed by document ID, following the Catalogue queue pattern; the ID is not repeated inside each value. Document `collection` is routing metadata for its configured owner, not part of the queue key; ordinary documents omit it, while named collection documents supply it.

Both media maps are keyed by owner, then type, then owner/type-relative filename. Both shared-output maps are keyed by owner, then output name. These families use the same owner keys: `workspace` or the exact configured non-Catalogue collection ID. The nested keys carry the complete identity without repeating it in each leaf or encoding composite keys into strings. Each document value, media filename value and shared-output value is one publication unit. The queue owner coalesces repeated contributions at that exact key to the latest intended effect. Media/shared leaves contain only `preview_done`; current/deleted membership supplies the effect. Empty objects select no work for their family. All publication queues empty retain the no-op behavior specified above. Publish owns the required item-before-shared sequencing rather than deriving it from JSON member order.

#### Flag And Field Ownership

| Flag or field | Meaning | What updates it | What reads it |
| --- | --- | --- | --- |
| `header.schema` | Identifies the proposed queue representation; it does not assert corpus validity or publication readiness. | Queue initialization establishes it; contributors and Publish preserve it. | The queue owner and Publish decode the agreed representation. |
| `header.last_published_at_utc` | Nullable UTC time of the last completed nonempty Docs publication queue, covering its document, media and shared-output units. | Initialization sets null. Publish records completion in the same queue write that removes the final successfully distributed unit. Upstream contributors, partial failures and initially empty Publishes preserve the previous value. | Queue inspection reports completed Docs queue publication independently of Catalogue publication. |
| `current_documents` membership | A completed public document artifact awaits selected Preview/deployment completion. Membership selects a write without a separate action flag. | Completed generation adds/coalesces entries; completed deletion replaces a write; Publish removes each successfully distributed entry. | Publish selects only the supplied document artifacts. |
| `deleted_documents` membership | Exact owned document files await deletion from Preview and deployment destinations, including publication eligibility withdrawal. | The upstream owner contributes the exact deletion selection; a completed write replaces it; Publish removes each successfully distributed entry. | Publish deletes the selected output using the retained identity, without requiring Working input bytes or inferring deletion from absence. |
| Document-map key | Immutable document ID, unique across the whole corpus, used directly as the key in `current_documents` or `deleted_documents`. | The originating generation/deletion owner supplies it and coalesces completed effects under that key. | Publish resolves the exact document artifact and deletion targets through the supplied owner. |
| Document `collection` | Routing metadata naming the exact configured non-Catalogue collection owner; omitted for ordinary documents and not part of the queue key. | The collection's generation/deletion owner supplies it. | Publish resolves the configured collection owner without rediscovering membership. |
| `current_media` membership | Selected completed media bytes await Preview writes and deployment, independently of document completion. | Media intake/production owners contribute completed writes; Publish removes each successfully distributed entry. | Publish transfers only the selected media. |
| `deleted_media` membership | Exact selected media awaits deletion from Preview and deployment destinations. | The media owner contributes explicit deletion identities; Publish removes each successfully distributed entry. | Publish deletes only the selected owned media, without reference scans or Working input bytes. |
| Media/shared owner key | `workspace` or the exact configured non-Catalogue collection owning the media namespace or shared output. Both families use the same owner values. | The owning upstream operation supplies it and retains exact deletion identities before configuration authority is lost. | Publish resolves the configured media or shared-output owner. |
| Media type key | Ready-media category within that owner. | The media intake/production owner supplies it. | Publish resolves the configured media family. |
| Media filename key | Exact filename relative to that owner's selected media type, retained for writes and deletions. Together with owner/type it identifies one asset. | The owning upstream operation supplies the known identity and coalesces effects at that key. | Publish resolves read-only current input bytes or exact Preview/deployment deletion targets. |
| `current_shared_outputs` membership | Explicit finished shared bytes await Preview writes and deployment; an empty document queue does not clear these selections or trigger a shared build. | Index/manifest, Recent, Selected, Search and configuration owners contribute finished writes; Publish removes each successfully distributed entry. | Publish transfers shared selections after their required item work. |
| `deleted_shared_outputs` membership | Exact shared artifacts await deletion from Preview and deployment destinations. | The owning upstream operation contributes exact deletion identities; Publish removes each successfully distributed entry. | Publish deletes the supplied owned shared outputs after their required item work. |
| Shared output key | Allowed logical output name beneath its owner key. | The corresponding upstream output owner supplies it and coalesces effects at that key. | Publish resolves the allowed artifact through configuration; the label grants no new file authority. |
| Entry `preview_done` | Explicit boolean progress: false requires selected Preview application; true means Preview completed and distribution remains pending. It is the only progress flag in this example. | Contributors initialize false only for new units and preserve existing progress. Publish sets true after Preview succeeds and removes the entry only after distribution succeeds. | Only Publish uses the flag to choose Preview plus distribution or distribution from retained Preview bytes. |

#### Schema Values

| `header.schema` value | Meaning |
| --- | --- |
| `docs_publish_pending_v1` | Proposed first representation of this Docs publication queue. This label does not imply that the queue has been implemented. |

#### Publication Timestamp Values

| `header.last_published_at_utc` value | Meaning |
| --- | --- |
| `null` | No completed nonempty Docs publication queue has been recorded yet. |
| UTC timestamp string | Time when the final selected unit completed distribution and this Docs queue became empty. |

This timestamp records Docs queue completion independently of Catalogue publication and makes no claim about whole-corpus freshness. An initially empty Docs queue leaves it unchanged, preserving the no-op behavior.

#### Collection Values

The following current values apply to document `collection` and collection-owned media/shared-output owner keys. They come from `stages.working.collections` in [Docs Workspace Configuration](../../../docs-viewer/config/workspace/docs-workspace.json). Ordinary documents omit `collection`; ordinary media and workspace-wide shared output use `workspace`. Future collection values require explicit configuration/registration through their owning delivery. Deleted selections retain their exact former identities through completion.

| Collection value | Configured collection |
| --- | --- |
| `works` | Context documents; distinct from Catalogue Work records and Work media. |
| `concepts` | Concepts documents. |
| `moments` | Moments documents. |

`catalogue` is also configured, but its document, Work/Gallery/Series, media and shared selections retain their existing Catalogue queue ownership and are not duplicated in this Docs queue.

#### Owner Values

This table applies to owner keys directly beneath `current_media`, `deleted_media`, `current_shared_outputs` and `deleted_shared_outputs`.

| Owner key | Meaning |
| --- | --- |
| `workspace` | Shared media namespace for ordinary documents and workspace-wide shared outputs. |
| `works` | Media and shared outputs owned by the Context collection. |
| `concepts` | Media and shared outputs owned by the Concepts collection. |
| `moments` | Media and shared outputs owned by the Moments collection. |

#### Media Type Values

These ready-media types follow the workspace's configured media families and [Media And Asset Handling](../Media_And_Asset_Handling.md#workspace-configuration-and-storage). Editable `mermaid`/`build-source` inputs are upstream preparation inputs; their completed public SVG output is queued under `svg`.

| Type key beneath a media owner | Meaning |
| --- | --- |
| `img` | Ready raster images. |
| `thumbs` | Document thumbnail derivatives. |
| `svg` | Ready SVG assets, including completed Mermaid diagram output. |
| `files` | Downloadable files. |
| `html` | Ready HTML media and its owned companion assets. |

#### Shared Output Values

These are the proposed logical output names for this delivery. Their configured owners resolve the finished artifacts and exact destinations; they are not filesystem paths or destination-provider selectors.

| Output key | Owner | Meaning |
| --- | --- | --- |
| `ordinary_index` | `workspace` | Finished public ordinary-document navigation index. |
| `recent` | `workspace` | Finished eligible Recent output prepared upstream. |
| `selected` | `workspace` | Finished eligible public Selected output. |
| `search` | `workspace` | Exact bytes from an explicitly completed Search rebuild. |
| `public_configuration` | `workspace` | Finished public browser configuration projection. |
| `collection_manifest` | `works`, `concepts`, `moments` | Finished public manifest for that exact non-Catalogue collection. |

#### Preview Progress Values

| `preview_done` value | Required next work |
| --- | --- |
| `false` | Apply the Preview write selected by current membership or deletion selected by deleted membership, persist true after success, then distribute the effect. |
| `true` | Distribute using retained Preview bytes or the retained deletion selection; successful distribution removes the leaf. |

Document IDs and media filenames are exact supplied identities rather than enumerated options. These tables describe the proposed queue handoff; they do not add Publish-time authoring validation, content audits or configuration-discovery scans.

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

- [ ] Complete [Document Media Working And Preview](Document_Media_Working_And_Preview.md) and carry forward its user-confirmed media baseline and accepted code cutover.
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

- [ ] Apply the mandatory [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review), including frontend/server ownership, narrow interfaces and hidden dependencies/work in reused helpers.
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
