---
draft: false
doc_id: d-20261009-110914-712f45
title: Incremental Updates
added_date: "2026-10-09 11:09:14"
last_updated: "2026-10-10 12:39:52"
summary: Active delivery of incremental Catalogue mutation, Refresh and Regenerate steps, with Work-by-Work Preview and Deploy, one publication progress flag and a final shared-output pass.
ui_status: active
parent_id: d-20261007-221414-48ff3f
---
# Incremental Updates

We need to make incremental updates to the Catalogue metadata **and** media, and apply the same principle to Publish. This is a self-contained delivery separate from [Public Work JSON Review](../Public_Work_JSON_Review.md), which will need to be updated following delivery.

## Delivery State

- [x] User approved IU-1–IU-4 implementation, queue-only normal Regenerate and a separate design-maintenance command on 2026-10-09.
- [x] Implemented staged Save, mutation-owned updates, selected Refresh/Regenerate and per-Work Preview/Deploy followed by shared output.
- [x] User resolved the old document queue with Refresh/Regenerate and ran the old Publish for Works `00639` and `04625`. That Publish predates the new incremental workflow.
- [x] User copied the initial Working/Preview Work media. The old Publish removed the first Preview copy; snapshot replacement now prunes stage-local media, and the user confirmed the repeated Preview copy.
- [x] Cutover initialized 4,618 Work image flags and six download flags false, created empty updates/publication queues and retired the empty old queue. Original shared media remains retained; active Work readers now use Working or Preview.
- [x] User approved direct Catalogue Source Save/Rebuild as a metadata-only publication contributor. Editing remains available for this delivery; removing Catalogue editing from the UI is a follow-on.
- [x] On 2026-10-10, replaced hash-based Refresh status with Work readiness flags and the updates queue header. Schema `catalogue_updates_pending_v3` stores `schema`, `last_refreshed_at_utc` and `shared_refresh_pending` in a header at the top. The separate receipt is removed; Save/Refresh/Regenerate preserve the agreed header ownership. Existing entries were preserved during migration; at migration the queue was empty with a null timestamp and shared pending true. Exact Gallery/Series queue selections remain a follow-on.
- [x] On 2026-10-10, moved publication schema into a header written first, then added nullable `last_published_at_utc` using `catalogue_publish_pending_v3`. It records completion of a nonempty Catalogue Work queue independently of the later shared-output pass. Contributors, partial failures and initially empty queues preserve the previous timestamp. Migration preserved the current/deleted selections and initialized `preview_done` progress; at migration the saved queue was empty and its timestamp was initialized null.
- [x] Focused lint (35 Python and eight JavaScript files), Python syntax, module imports, field registry, current canonical/queue diagnostics, projection check, site validation and whitespace checks passed. Bounded source review covered mutation contributions, selected handoffs, deletion descriptors and retained Preview media/documents. No tests or browser automation ran.
- [x] On 2026-10-10, the user confirmed new Work creation through Save → Refresh → Regenerate → Publish to R2, followed by deletion through to R2. Publish seemed quicker in this Catalogue queue case; this is qualitative feedback, with no timing measurement.
- [x] Durable Catalogue editor, services, Save/Refresh, deployment, media and storage owners now describe the implemented workflow, both queue schemas/timestamps, selected deletion and retained-progress behavior, and the confirmed/remaining evidence. Documentation transfer is complete independently of further manual testing.
- [x] On 2026-10-10, removed timestamp-only shared Refresh writes by reusing the existing generated-content comparison. Unchanged Gallery records, indexes, media policy and Series/Galleries report retain their bytes/timestamps; written-file reporting includes only actual writes. Changed-module lint and Python syntax passed. Live Refresh/Publish confirmation remains pending; Gallery/Series queues remain separately scoped.
- [ ] User completes remaining manual acceptance. Managed-file, timestamp-retention and other unexercised variants remain unverified.

The next gate is user manual acceptance under IU-6. Test work remains separately scoped under [Test Contract Discipline](../Test_Contract_Discipline.md). Live Publish, real media deletion and Git actions remain explicit actions. Detailed changed-owner and command context is retained in the temporary [implementation handoff](Incremental_updates_handoff.md).

## Current State

- Studio Save writes complete prepared image/thumbnail sets and new/replacement downloads into Projects-owned `catalogue/media-staging/`. Independent canonical flags select staging or Working for each media family/file.
- Known mutation effects accumulate in `working/catalogue-updates-pending.json`; Refresh completes selected false-readiness metadata/media handoffs and clears staging flags before readiness becomes true.
- Queue-only Regenerate completes refreshed Catalogue sources/documents, merges publication selections and removes completed updates entries. Explicit design maintenance performs full source/document reconciliation without inventing media changes.
- Direct Catalogue Source Save/Rebuild queues the completed document as metadata only, preserving already queued media and initialized publication progress.
- Publish completes each queued Work's Preview/Deploy, then builds/deploys shared output once. Unchanged Catalogue documents and Work metadata are retained from completed Preview; stage-local media is excluded from snapshot scanning/replacement.
- Catalogue prose survives ordinary Regenerate unless the Work title changes. A title change or explicit design maintenance replaces the body with its generated template.

## Agreed Workflow

- Studio Save retains prepared images, thumbnails and new/replacement downloads in `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media-staging/`.
- `works.json` carries a separate Work-level image staging flag and a `staged` flag on each download. Studio selects the media location independently for the image set and each file.
- Refresh copies changed staged media and required missing files into `working/assets/works/`, alongside its matching Catalogue metadata handoff. A successful Refresh leaves Working media and metadata aligned.
- Media is published to `preview/assets/works/` and updated by Publish. Preview retains its last published media between operations.
- Metadata is generated by Studio Refresh in `working/generated/catalogue/works/index/<work_id>.json` and is current in Working after Refresh.
- Save and the other canonical mutation owners accumulate their known changed/deleted Work IDs, metadata/image flags and exact changed download filenames in `working/catalogue-updates-pending.json`, setting each affected entry's `refreshed` flag to false. Refresh sets it to true after that Work's handoff succeeds; entries remain until the required Catalogue Regenerate source/Build work completes.
- When a Work has completed its required Catalogue update, merge its pending record into `working/catalogue-publish-pending.json`. Initialise `preview_done: false` only for a new record; leave an existing record's flag untouched without inspecting it. This records that Work's changes awaiting Preview and Deploy.
- Publish processes one queued Work through Preview and Deploy before starting the next. Preview applies its selected metadata into `preview/catalogue/`, Catalogue document into `preview/collections/catalogue/` and media into `preview/assets/works/`, then sets `preview_done: true`. Deploy copies or removes that Work's configured repository files and completes its R2 uploads/deletions using Preview and the retained queue selection. Successful Deploy removes the entry.
- After all queued Works complete, Publish prepares and deploys indexes and other shared output in one final pass. This pass also runs when the Work queue is already empty.
- Work Delete captures its media deletion details before removing the canonical record and clears its staged media. Refresh removes the queued Working metadata/media, Regenerate removes the document, and Publish removes the corresponding Preview and R2 media using the retained deletion details.

## Data Files And Handoffs

Paths beginning with `working/` or `preview/` are relative to the configured `$DOTLINEFORM_DOCS_BASE_DIR`. Paths beginning with `studio/`, `site/`, `site-tools/` or `docs-viewer/` are repository-relative. Studio staging is explicitly rooted at `$DOTLINEFORM_PROJECTS_BASE_DIR`. `<work_id>` is the exact five-digit Work ID; `<filename>` is a managed download basename. Working and Preview use their separate configured Work-media roots; shared ordinary document media retains its existing owner.

| Data | File or location | Writer and consumer |
| --- | --- | --- |
| Canonical Work records and Studio staging flags | `studio/data/canonical/catalogue/works.json` | Studio mutations write Work records and staging flags; Refresh reads selected Works and clears completed staging flags. |
| Canonical Gallery membership | `studio/data/canonical/catalogue/galleries-by-work.json` | Studio membership mutations and Work Delete write it; Refresh supplies the resulting relationships. |
| Prepared Studio media awaiting Refresh | `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media-staging/` | Studio Save writes prepared images/thumbnails/downloads; Refresh copies the selected bytes into Working. |
| Working handoff/regeneration selection | `working/catalogue-updates-pending.json` | Studio mutations accumulate changes/deletion descriptors; Refresh updates `refreshed`; Regenerate consumes completed handoffs and removes completed entries. |
| Refreshed Work metadata | `working/generated/catalogue/works/index/<work_id>.json` | Refresh writes the by-ID JSON. Regenerate reads its `work` object, including `work.downloads[].filename`, for the Catalogue document and publication merge. Preview reads the selected metadata for publication. |
| Catalogue document source | `working/source/collections/catalogue/documents/<work_id>.md` | Regenerate creates/updates/deletes the source; the document builder renders it. Direct Source Save remains available. |
| Rendered Working Catalogue document | `working/generated/collections/catalogue/documents/by-id/<work_id>.json` | The document Build writes it; the Work's Preview step consumes the completed document presentation. |
| Working prepared media | `working/assets/works/primary/`, `working/assets/works/thumbs/`, `working/assets/works/media/files/<filename>` | Refresh supplies prepared bytes; Regenerate/Build consume them, and Preview copies selected media. The stage-local roots retain the currently configured relative media-family layout. |
| Publication selection and progress | `working/catalogue-publish-pending.json` | Regenerate, design maintenance and completed direct Catalogue Source Save/Rebuild merge changes; only Publish checks or changes an initialised `preview_done` flag and removes completed entries. |
| Preview Work metadata | `preview/catalogue/works/index/<work_id>.json` | The Work's Preview step applies metadata changes/deletion; Deploy copies/removes `site/assets/data/catalogue/works/index/<work_id>.json`. |
| Preview Catalogue document | `preview/collections/catalogue/documents/by-id/<work_id>.json` | The Work's Preview step applies the document change/deletion; Deploy projects/copies/removes `site/assets/data/docs/catalogue/by-id/<work_id>.json`. |
| Preview prepared media | `preview/assets/works/primary/`, `preview/assets/works/thumbs/`, `preview/assets/works/media/files/<filename>` | The Work's Preview step applies selected media changes/deletions; Deploy uploads primary images/downloads to R2 and copies thumbnails to the repository's `site/assets/data/catalogue/works/thumbs/` destination. |
| Storage/public destination configuration | `docs-viewer/config/workspace/docs-workspace.json` and `site-tools/config/site-tools.json` | Workspace configuration owns storage and repository projection; site media configuration owns Work image/download R2 prefixes. Implementation updates the stage-local media resolution while retaining these configuration owners. |

For Work `00008`, the refreshed metadata input is specifically `working/generated/catalogue/works/index/00008.json`. Its `work.downloads` entries supply the current download references used by Regenerate; `studio/data/canonical/catalogue/works.json` supplies the earlier Studio/Refresh handoff. Deleted Works use the retained descriptors in the two queue files because their canonical and refreshed by-ID records may already be absent.

## Operation Responsibilities

| Operation | Responsibility |
| --- | --- |
| Studio Save | Persist canonical Work metadata and stage its changed image rendition/thumbnail set or individual new/replacement downloads. Complete canonical dimensions and `media_version` with the prepared image bytes, set staging flags, accumulate exact changes in `catalogue-updates-pending.json`, reset affected entries to `refreshed: false` and update editor records. |
| Studio Delete | Capture image/download deletion details before removing the canonical Work and memberships, persist the deletion entry with `refreshed: false`, and delete that Work's known staged renditions, thumbnails and downloads as part of awaited local completion. |
| Studio Refresh | Select updates/deletions with `refreshed: false`. Apply current metadata/media handoffs or delete the queued Working Catalogue metadata and media. Complete required staging-flag updates for current Works, then set each successful entry to `refreshed: true`; retain its change/deletion details for Regenerate. |
| Catalogue Regenerate | Select entries with `refreshed: true`, reconcile Catalogue source documents and complete the required document Build using Working metadata and media. Merge completed changes into publication pending state, then remove their updates entries. |
| Docs Publish | Process each queued Work through Preview and then Deploy. Complete selected Preview writes/deletions before setting `preview_done: true`; complete repository and R2 deployment before removing that Work's entry. After the Work queue is empty, prepare and deploy shared output. Stop and report the failed Work/stage or shared-output step, retaining completed effects. |

Studio staging resolves under the configured Projects root. Working and Preview resolve under the configured Docs workspace root. These are distinct owners; Docs Build, Regenerate and Publish consume supplied Working inputs without reading Studio staging or canonical authoring data directly. Refresh remains the explicit bridge.

Save already knows what it changed and records that information once. Refresh consumes the queued selection and reads the inputs needed to carry it out. It does not scan the Catalogue for staging flags, compare the whole Catalogue with the previous Working input or inspect media bytes to rediscover changes. Every canonical mutation owner must record its own known effects for this approach to be complete.

## Required Save Behaviour Change

Redirect Save's completed rendition, thumbnail and managed-download destinations from shared Docs assets to persistent Studio staging. Retain the complete prepared rendition set there after Save returns, with matching dimensions/version committed to canonical Work metadata. Conversion may use operation-local temporary files before committing the completed set to staging. New and replacement downloads must also persist there for the later Refresh, including replacements whose filename is unchanged.

The Studio editor must resolve images/thumbnails and each download independently from their `works.json` staging flags. A staged item is read from Studio staging; an unstaged item is read from Working. Download validation and image-change comparison must use the corresponding selected location. Further Saves advance only the edited media's staged state; Refresh owns advancing the supplied Working state.

Refresh transfers already prepared bytes and the corresponding metadata; it does not regenerate images or advance their versions. Save records image staging separately from per-download staging and persists the exact changes in the updates queue, including same-name download replacements. Queue persistence is required Save completion work; a failure must report the saved-but-incomplete state rather than lose the change selection silently.

This direction separates Studio staging, Working and Preview media ownership. An image edit stages its complete rendition/thumbnail set; a download edit stages only its new/replacement files. Unrelated media can continue to be read from Working. Routine transfers are limited to changed assets and required missing files. The user will perform the initial media copies into Working and Preview as described under Manual Initial Media Setup; implementation does not need an automated media migration or reconciliation operation.

## Proposed Work Deletion

Prepared images, thumbnails and managed downloads are unique to their Work. Authoring and manual review of the associated media report enforce that ownership. Deletion uses this agreed ownership directly; it does not scan other Works or check whether another Work references a file. Project originals retain their Projects owner.

Studio Delete must capture the media deletion selection before removing the canonical record: `image` indicates whether the prepared rendition/thumbnail set is to be deleted, and `file_names` lists exact download basenames to delete. The image filenames are derived from the Work ID and configured srcset/rendition policy. These details remain in the queues after `works.json` no longer contains the Work.

| Operation | Deletion responsibility |
| --- | --- |
| Studio Delete | Remove the canonical Work and its memberships, persist its deletion descriptor and delete its known staged images, thumbnails and downloads. |
| Refresh | Remove its Working Catalogue metadata and the indicated Working image/download files, then set the deletion entry's `refreshed` flag to true. |
| Regenerate | Complete Catalogue source/document deletion and required generated-output updates, forward the full deletion descriptor to the publication queue, then remove the updates entry. |
| Publish | Apply the Work's deletion to Preview Catalogue metadata/documents/media, then set `preview_done: true`. Deploy removes the corresponding repository files and R2 image/download objects. Remove that Work's publication entry only after its Deploy succeeds, then continue to the next Work. |

Staging cleanup is part of awaited Studio Delete completion. If canonical deletion succeeds but staging cleanup fails, report a saved-but-incomplete deletion with the affected Work and media identities; retain the queued downstream deletion details. No additional staging-deletion flag is proposed. `refreshed` continues to mean the required Working deletion completed.

Already absent owned files/objects count as successfully deleted. Other failures stop processing and retain the relevant pending entry. Publish retains the deletion descriptor through Preview and Deploy so exact repository/R2 deletion identities remain available after Preview files have been removed. It must not try to reconstruct them from the removed canonical, Working or Preview Work record.

## Proposed Staging Flags In works.json

Propose `image_staged` as a boolean on the Work record and `staged` as a boolean on each existing `downloads` entry. These are independent media-location selectors. The following illustrative Work fragment shows a staged download while its image remains in Working:

```json
{
  "work_id": "00008",
  "image_staged": false,
  "downloads": [
    {
      "filename": "00008-nerve.pdf",
      "label": "nerve.pdf",
      "staged": true
    }
  ]
}
```

| Flag | `true` | `false` | What updates it | What reads it |
| --- | --- | --- | --- | --- |
| Work `image_staged` | Read the Work's complete rendition and thumbnail set from Studio staging. | Read the Work's images and thumbnails from Working. | Image Save sets true after preparation; successful Refresh clears it. | Studio editor/thumbnails and image-change comparison; Refresh resolves the queued image's current location. |
| Download `staged` | Read that exact filename from Studio staging. | Read that exact filename from Working. | Download Save sets true after preparation; successful Refresh clears it. | Studio download links/validation; Refresh resolves that queued filename's current location. |

Paths remain configuration-owned; full filesystem paths are not stored in Work records. There is no Work-level download staging selector: each download owns its own flag, so a replacement does not move unrelated downloads or images to staging. The editor's thumbnail/list projections must carry `image_staged`, and download presentations must retain their entry's flag when resolving Studio media.

- An image Save sets `image_staged: true` only after the complete image set and matching canonical dimensions/version have been prepared successfully. It preserves download staging flags.
- A download Save sets `staged: true` on each successfully staged new/replacement file, including a replacement with the same filename. It preserves image staging and other download flags.
- A metadata-only Save preserves all existing staging flags.
- Save records the exact changed Work and media selection in `working/catalogue-updates-pending.json` as part of its completion.
- Refresh selects entries with `refreshed: false`, copies their staged media and completes the matching Working handoff and canonical staging-flag clears before setting each successful entry to `refreshed: true`. Failed or unprocessed entries remain false. Refresh retains the change flags and filenames for Regenerate.
- Refresh returns the updated Studio records so the editor adopts Working locations. Only complete success advances `header.last_refreshed_at_utc` and clears `header.shared_refresh_pending`; status uses that header and queued readiness without canonical/configuration hashing.

Staging flags select where Studio reads media. Pending `image` and `file_names` separately record which media changed for regeneration/publication. Save records the exact changed download basenames in `file_names` when downloads are staged. Those filenames remain queued after Refresh clears the per-download staging flags. Clearing a staging flag must not clear the document/publication pending change or enqueue another authored change.

Staging state is Studio-owned. Docs readers/builders use their supplied Working media, and public projections omit these operational flags. The private Working handoff must preserve that ownership boundary.

## Working Catalogue Updates Queue

File: `working/catalogue-updates-pending.json`.

This queue records known Catalogue changes awaiting the Working handoff and document regeneration. Each current Work entry carries metadata/image change flags, exact changed download filenames and a `refreshed` readiness flag. Deleted Works have structured entries carrying an image deletion flag, exact download basenames and their own `refreshed` flag. The queue records what changed and which handoffs completed, while `works.json` records where Studio currently reads the media.

### What Updates It

- Studio Save accumulates the exact changes it has just made, including metadata-only edits, image changes and individual new/replacement downloads. Every further queued change resets the affected entry to `refreshed: false`.
- Create, Delete, bulk edits and Gallery/Series relationship mutation owners record their own known affected Work IDs with `refreshed: false`. Delete captures the image deletion flag and download basenames before removing the Work, then adds that structured deletion entry.
- Repeated mutations merge change flags with logical OR and accumulate changed filenames. A later metadata-only edit retains earlier image/file changes while resetting readiness. Deletion supersedes a current entry; recreation replaces the deletion entry with the required current changes and resets readiness.
- Refresh sets an entry's `refreshed` flag to true only after that Work's required metadata/media handoff or Working metadata/media deletion succeeds, including required canonical staging-flag updates for current Works. It retains the original change/deletion selection.
- Catalogue Regenerate removes only entries whose required source/delete and document Build work has completed and whose publication pending entries have been persisted.

Refresh updates readiness in this queue; it does not rediscover or add authored changes. Its canonical staging-flag clears are media-location bookkeeping, not new changes to enqueue.

### What Reads It

**Refresh** selects only current/deleted entries with `refreshed: false` from `working/catalogue-updates-pending.json`, reading their Work IDs, change flags and changed filenames. For current Works, it resolves their canonical records from `studio/data/canonical/catalogue/works.json` and writes matching `working/generated/catalogue/works/index/<work_id>.json` metadata. For queued media that is still staged under `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media-staging/`, it copies the indicated image set or exact download into the corresponding `working/assets/works/` media family; media already handed off is not recopied merely because its document entry remains pending. Required missing output handling is scoped to the selected inputs. Entries already marked true are skipped. Refresh does not discover the selection by scanning every Work or comparing the complete current and previous Catalogue.

For a deletion, Refresh reads `image` and `file_names` from the retained descriptor, removes the Working Catalogue metadata and indicated media, and marks readiness true only after all required Working deletions complete. It does not require the deleted Work to remain in canonical `works.json`.

**Regenerate** selects only entries with `refreshed: true` from `working/catalogue-updates-pending.json`. For current Works, it reads `working/generated/catalogue/works/index/<work_id>.json`, reconciles `working/source/collections/catalogue/documents/<work_id>.md` and completes the required Build output at `working/generated/collections/catalogue/documents/by-id/<work_id>.json`. Deleted Work entries select the corresponding source/generated document removals. This per-entry flag supplies the readiness information; Regenerate does not infer successful Refresh from queue presence or staging flags. Entries still marked false remain pending and require Refresh. Further mutations reset only their affected entries to false; other ready entries remain ready.

### Clearing And Failure

Entries survive successful Refresh with `refreshed: true` because the required document work is still pending. Regenerate first completes that work, then merges the current change flags/filenames or full media deletion descriptor into `working/catalogue-publish-pending.json`, then removes the completed updates entry. Writing a document alone does not complete an entry if required Build work or the publication-queue merge remains outstanding. Failure stops processing; failed and unprocessed entries remain. Earlier completed effects remain for diagnosis and manual retry.

### Pending Record Shape

Current `working/catalogue-updates-pending.json`:

Current v3 shape. `header` is the first section, with schema, nullable last successful UTC Refresh time and shared pending boolean. `current_works` and `deleted_works` are objects keyed by exact Work ID. A Work cannot occur in both. Work flags are explicit booleans; `file_names` contains sorted distinct download basenames, with no paths.

`file_names` alone selects download operations: an empty list means no download operation; a populated list selects those exact downloads for transfer on current Works or deletion on deleted Works. The same rule applies to both pending queues.

```json
{
  "header": {
    "schema": "catalogue_updates_pending_v3",
    "last_refreshed_at_utc": null,
    "shared_refresh_pending": true
  },
  "current_works": {
    "00008": {
      "metadata": true,
      "image": true,
      "file_names": [
        "00008-nerve.pdf"
      ],
      "refreshed": false
    },
    "04625": {
      "metadata": true,
      "image": false,
      "file_names": [],
      "refreshed": true
    }
  },
  "deleted_works": {
    "03181": {
      "image": true,
      "file_names": [
        "03181-book.pdf"
      ],
      "refreshed": false
    }
  }
}
```

In this example, Work `00008` still needs Refresh, Work `04625` is ready for Regenerate, and deletion `03181` still needs Working metadata/media removal. Studio Delete owns its staged-media cleanup. The deletion's `image` flag selects its complete prepared image/thumbnail set, and `file_names` lists the downloads to remove. Its membership in `deleted_works` already requires metadata/document deletion, so it needs no separate `metadata` flag.

### Flag And Field Ownership

| Flag or field | Meaning | What updates it | What reads it |
| --- | --- | --- | --- |
| Current `metadata` | Work metadata/resources or relevant relationships changed. | Save/other mutation owners accumulate true; Regenerate removes it with the completed entry. | Refresh selects matching metadata handoff; Regenerate consumes and forwards the change to publication pending state. |
| Current `image` | Image changes must survive through document regeneration and publication. | Image Save/other media mutation owner accumulates true; Regenerate removes it with the entry. | Refresh selects the image set, using `image_staged` for its location; Regenerate forwards the flag to publication pending state. |
| Current `file_names` | Exact changed download basenames retained beyond staging. | Download Save merges changed filenames; a later reference removal removes obsolete transfer names and queues the metadata change; Regenerate removes the list with the entry. | Refresh copies selected files; Regenerate carries their identities into publication pending state. |
| Current `refreshed` | False means the current queued changes need Refresh; true means their required Working handoff completed. | Save/other mutation owners create/reset false; Refresh sets true after successful handoff; Regenerate removes it with the entry. | Refresh processes false entries; Regenerate processes true entries. |
| Deleted `image` | Delete the Work's prepared renditions and thumbnails. | Studio Delete captures the image deletion selection; Regenerate removes it with the completed entry. | Studio Delete cleans known staged images; Refresh deletes the derived Working image set; Regenerate forwards the flag for Preview/R2 deletion. |
| Deleted `file_names` | Exact owned download basenames to delete, retained after canonical deletion. | Studio Delete captures them before removing the record; Regenerate removes the list with the completed entry. | Studio Delete cleans selected staged downloads; Refresh deletes selected Working files; Regenerate forwards their identities for Preview/R2 deletion. |
| Deleted `refreshed` | False means Working metadata/media deletion is pending; true means all required Working deletion completed. | Delete creates false; Refresh sets true after deletion succeeds; Regenerate removes the entry after required document deletion and publication-queue merge. | Refresh processes false deletions; Regenerate processes true deletions. |
| `current_works` / `deleted_works` membership | Identifies current updates versus Work deletions. | Mutation owners add/replace the relevant entry; Regenerate removes completed entries. | Refresh and Regenerate select exact Work IDs and the operation. |
| `header.schema` | Identifies the updates queue format. | Initialization/migration establishes the version. | Queue readers validate it before processing. |
| `header.last_refreshed_at_utc` | Last complete successful Refresh time, or null before one exists. | Full Refresh completion advances it; mutations and Regenerate preserve it. | Studio displays the time independently of later pending changes. |
| `header.shared_refresh_pending` | Shared output still needs Refresh, including changes without Work entries or interrupted Refresh. | Mutations/Refresh start set true; only full Refresh completion clears it. | Refresh status combines it with false Work readiness. |

Staging flags are cleared by Refresh, but `metadata`, `image` and `file_names` remain unchanged through that handoff. They are still needed by Regenerate and Publish. A same-Work Save after successful Refresh retains those accumulated changes and sets only readiness back to false alongside its new changes. A Save that makes no actual change need not reset readiness.

## Working Catalogue Publication Queue

File: `working/catalogue-publish-pending.json`.

This queue records completed Working Catalogue changes awaiting Work-by-Work Preview and Deploy. It retains current Work change flags/filenames and full image/file deletion descriptors after the updates queue and canonical staging flags have been cleared. Entry creation means the required Refresh and Regenerate work completed. Each current or deleted Work carries one explicit boolean `preview_done`: false means its queued changes still need Preview; true means Preview completed and Deploy remains outstanding. The updates queue's `refreshed` flag is not carried into this queue.

During normal operation between Publishes, queued entries have `preview_done: false` and can accumulate further completed changes. Outside an active Publish, a retained true flag records an interrupted Deploy that needs correction and completion before normal operation resumes. Its progress and selection are preserved; newer changes do not reset it to false.

Publish alone checks or changes an existing record's `preview_done` flag. Regenerate initialises a new Work record with `preview_done: false` and ignores the flag thereafter. Further changes are merged into an existing Work record without inspecting or modifying its flag.

### What Updates It

**Regenerate** merges each completed Work's changes from `working/catalogue-updates-pending.json` into `working/catalogue-publish-pending.json` before clearing that Work's updates entry. If the Work has no publication record, Regenerate initialises one with `preview_done: false`. If it already has a record, Regenerate merges the changes and leaves `preview_done` untouched, without checking its value. It accumulates change flags and retains only still-referenced changed download filenames across repeated completed regenerations, using the current Work merge rules below. It carries full media deletion descriptors forward for deleted Works. A completed deletion replaces the Work's current change selection with its deletion descriptor; a completed recreation replaces the deletion selection with current changes. These changes preserve the flag on an existing record. Save and Refresh do not add incomplete changes here: the required document work must complete first.

**Publish** sets a Work's `preview_done` to true only after all its required Preview writes/deletions complete. It then runs that Work's Deploy and removes its entry only after both repository and R2 work complete. Earlier completed Works remain removed if a later Work or the final shared-output pass fails.

### Current Work Merge Rules

For a current Work, Regenerate takes incoming change flags and filenames from its entry in `working/catalogue-updates-pending.json`, the existing publication record from `working/catalogue-publish-pending.json`, and the latest refreshed Work metadata from `working/generated/catalogue/works/index/<work_id>.json`. For Work `00008`, that last file is `working/generated/catalogue/works/index/00008.json`; the current download references are the `filename` values in its `work.downloads` list. Regenerate already consumes this same by-ID JSON for document regeneration. Merge uses these selected inputs without scanning other Works, comparing the Catalogue or inspecting media bytes.

| Field | Merge rule |
| --- | --- |
| `metadata` | Logical OR of the existing and incoming change flags. Adding or removing a download reference is a metadata/resource change. |
| `image` | Logical OR of the existing and incoming change flags, preserving any outstanding image transfer. |
| `file_names` | Combine the Work's existing filenames in `working/catalogue-publish-pending.json` with incoming changed filenames in `working/catalogue-updates-pending.json`, then retain only names present in `work.downloads[].filename` from `working/generated/catalogue/works/index/<work_id>.json`. Store the resulting sorted, distinct basenames. Apply the same reference filter when initialising a new record. |
| `preview_done` | Initialise false only for a new Work record. When merging into an existing record, leave it untouched without inspecting its value. |

For example, adding `00008-nerve.pdf`, completing Refresh and Regenerate, and leaving Publish unrun gives Work `00008` this publication record:

```json
{
  "metadata": true,
  "image": false,
  "file_names": [
    "00008-nerve.pdf"
  ],
  "preview_done": false
}
```

If that download is then removed and Refresh and Regenerate complete again before Publish, the incoming filename list in `working/catalogue-updates-pending.json` may be empty, but its absence from `work.downloads` in `working/generated/catalogue/works/index/00008.json` also removes it from Work `00008`'s existing entry in `working/catalogue-publish-pending.json`:

```json
{
  "metadata": true,
  "image": false,
  "file_names": [],
  "preview_done": false
}
```

The Work remains queued so its metadata/document update removes the download reference. The cancelled download is neither copied to Preview nor uploaded to R2. No R2 deletion is needed for this newly added, never-published file. Other still-referenced pending downloads and image changes remain selected. Publish receives this final selection and performs no reference filtering itself.

### What Reads It

**Publish** reads one Work's selection and `preview_done` from `working/catalogue-publish-pending.json`. When false, its Preview step consumes `working/generated/catalogue/works/index/<work_id>.json`, the completed Catalogue document at `working/generated/collections/catalogue/documents/by-id/<work_id>.json` and the selected media under `working/assets/works/`. It applies them to `preview/catalogue/works/index/<work_id>.json`, `preview/collections/catalogue/documents/by-id/<work_id>.json` and the corresponding `preview/assets/works/` media families. Exact `file_names` select downloads from `working/assets/works/media/files/<filename>` for copying to `preview/assets/works/media/files/<filename>`, without recopying the Work's other files. Once true, Deploy consumes those Preview files and the retained queue deletion selection; it does not repeat Preview or read newer Working media to perform deployment.

For `deleted_works`, Publish reads the retained image flag and download basenames, deletes the corresponding Preview metadata/documents/media and sets `preview_done` to true. Deploy uses that retained descriptor to remove the corresponding repository files and R2 objects. Canonical, Working and Preview records may already be absent, so the queue retains the deletion selection until Deploy completes.

This queue selects incremental Catalogue Work changes. Indexes, Gallery relationships, report data and other shared output are prepared and deployed once after all queued Works complete. Ordinary documents, other collections, Search copying and publication eligibility retain their existing processing within that final pass; the Work queue alone does not define publication membership. Unchanged content remains in place. Initial media population is the user's manual setup step.

### Clearing And Failure

Remove each publication entry after that Work's Deploy completes, including its repository output and R2 uploads/deletions. There is no separate Deploy completion flag or R2 queue: entry removal records successful Deploy and retains the deletion descriptor until it is no longer needed.

On failure, stop and report the affected Work and whether Preview or Deploy failed, or identify the failed shared-output step. Retain the failed and unprocessed entries with their last completed `preview_done` state. Earlier completed Works remain removed; partial Preview, repository or R2 effects remain in place. Temporary differences between those destinations and shared output are acceptable during an incomplete Publish. The user diagnoses and fixes the cause, then explicitly runs Publish again to finish the interrupted operation before normal authoring, Refresh and Regenerate resume; no rollback, automatic retry or restoration to a perfectly aligned state is required.

If Preview failed, the entry remains false and the next explicit Publish repeats its Preview step before Deploy. If repository copying completed but R2 failed, the entry remains true and the next explicit Publish repeats the Work's combined Deploy step. Already absent owned files/objects count as successfully deleted. If the shared-output pass fails after all Works completed, the Work queue remains empty; the next Publish still runs the shared-output pass. Publish reports complete success only after that pass succeeds.

The publication header's nullable `last_published_at_utc` refers to this Catalogue Work queue. The final queued Work's successful Deploy removes its entry and advances the timestamp in the same queue write. A partial queue failure preserves the previous successful queue time; a later shared-output failure retains the new Catalogue completion time. An initially empty queue leaves the timestamp unchanged.

### Pending Record Shape

Publication queue after the example changes have successfully completed their required Refresh and Regenerate work, shown after Work `00008` has completed Preview but its Deploy has failed:

```json
{
  "header": {
    "schema": "catalogue_publish_pending_v3",
    "last_published_at_utc": null
  },
  "current_works": {
    "00008": {
      "metadata": true,
      "image": true,
      "file_names": [
        "00008-nerve.pdf"
      ],
      "preview_done": true
    },
    "04625": {
      "metadata": true,
      "image": false,
      "file_names": [],
      "preview_done": false
    }
  },
  "deleted_works": {
    "03181": {
      "image": true,
      "file_names": [
        "03181-book.pdf"
      ],
      "preview_done": false
    }
  }
}
```

Current Work change fields and deleted Work media fields match the updates queue. Regenerate drops `refreshed` and initialises `preview_done: false` only when creating a publication record; it ignores the flag when merging into an existing record. In this example, the user fixes the Deploy failure and reruns Publish, which performs only Deploy for Work `00008`; Work `04625` and deletion `03181` still require both Preview and Deploy. The true flag is preserved until Work `00008` completes Deploy and its entry is removed. Publication deletions retain their structured descriptors through Deploy because repository/R2 deletion identities are still needed after Working and Preview deletion. A Work cannot be both current and deleted in this queue. All `preview_done` values are explicit booleans; `file_names` retains the same sorted, distinct basename rules as the updates queue.

### Flag And Field Ownership

| Flag or field | Meaning | What updates it | What reads it |
| --- | --- | --- | --- |
| Current `metadata` | Completed Work metadata/resource/relationship changes need publication. | Regenerate merges the updates flag with logical OR; Publish removes it with the entry after that Work's Deploy succeeds. | Preview selects the corresponding Catalogue metadata; Deploy copies that Work's Preview metadata/document. Shared relationships are handled in the final pass. |
| Current `image` | Changed Working renditions/thumbnails need publication. | Regenerate merges the updates flag with logical OR; Publish removes it with the entry after that Work's Deploy succeeds. | Preview copies the selected Working image set; Deploy transfers the selected Preview media to its configured destinations. |
| Current `file_names` | Exact changed download basenames still referenced by the refreshed Work and awaiting transfer. | Regenerate combines existing and incoming pending filenames, filters them against `work.downloads[].filename` in `working/generated/catalogue/works/index/<work_id>.json` and stores sorted distinct names; Publish removes the list with the entry after that Work's Deploy succeeds. | Preview copies `working/assets/works/media/files/<filename>` to `preview/assets/works/media/files/<filename>`; Deploy distributes those Preview bytes without rediscovering the selection. |
| `current_works` membership | A current Work's required document regeneration completed and its changes await Preview and/or Deploy. | Regenerate adds/merges the entry; a completed deletion replaces it; Publish removes the entry after that Work's Deploy succeeds. | Publish selects the current Work's metadata, document and indicated media by Work ID. |
| Deleted `image` | Remove the Work's prepared renditions and thumbnails from Preview and their public destinations. | Regenerate forwards the deletion flag; Publish removes it with the entry after that Work's Deploy succeeds. | Preview removes the derived image set; Deploy resolves its configured repository/R2 identities from the retained descriptor. |
| Deleted `file_names` | Exact download basenames to delete, captured before canonical deletion. | Regenerate forwards the deletion list; Publish removes it with the entry after that Work's Deploy succeeds. | Preview removes the selected files; Deploy removes their configured public objects using the retained identities. |
| `deleted_works` membership | Required Working/document deletion completed and must be applied to Preview and Deploy, including indicated media. | Regenerate adds deletion descriptors or replaces them on completed recreation; Publish removes the entry after that Work's Deploy succeeds. | Publish removes the Work's owned Catalogue metadata/document and selected media at each destination. |
| Current/deleted `preview_done` | False means this queued Work change still needs Preview; true means Preview completed and Deploy remains outstanding. Outside active Publish, true records interrupted Deploy progress. | Regenerate initialises false only on a new Work record and ignores it on existing records. Publish alone changes the initialised flag, setting true after required Preview work completes and removing the entry after Deploy succeeds. | Only Publish checks the flag: false requires Preview, while true proceeds directly to combined repository/R2 Deploy. |
| `header.schema` | Identifies the publication queue format; the header is written before Work maps. | Initialisation/migration establishes the version; every contributor and Publish preserves it. | Publish and the Regenerate merge owner validate it. |
| `header.last_published_at_utc` | Nullable UTC time of the last completed nonempty Catalogue Work publication queue. | The final Work's successful Deploy records it with entry removal; upstream contributors, partial failures and initially empty queues preserve it. The later shared pass does not own this time. | Queue readers validate it; inspection reports completed Catalogue queue publication. |

`preview_done` is the only publication progress flag. There are no separate repository, R2 or Deploy completion flags: successful Deploy removes the entry immediately. An empty Work queue means all queued Works completed, but overall Publish still needs its shared-output pass. Changes between successful Publishes are passed forward and accumulated by the upstream owners, which are responsible for keeping the queued selections and supplied Working metadata, documents and media aligned. Publish acts on those supplied instructions and inputs; it does not look back at canonical records or the updates queue to discover changes or infer readiness.

## Per-Work Processing

### Regenerate

Successful direct Catalogue Source Save/Rebuild also contributes a completed metadata/document update to the publication queue, with no new media selection. It preserves existing media and initialized progress and does not consume updates entries. Editing remains available in this delivery. Normal Regenerate preserves the source body unless the Work title changes; a title change or design maintenance restores the generated template and can replace added prose.

1. Select current/deleted entries with `refreshed: true`, then regenerate one Work at a time using supplied Working metadata and media: reconcile its Catalogue source and complete its required Catalogue document regeneration. Entries with false readiness remain pending for Refresh. Referring documents are updated by the separate manual Full Rebuild described below.
2. After the required processing completes, pass the Work's changes or full deletion descriptor, including the image flag and exact download filenames, into `working/catalogue-publish-pending.json`. Initialise a record with `preview_done: false` if the Work is absent; otherwise merge its changes without inspecting or modifying the existing flag.
3. Remove that Work's regeneration entry only after the publication pending update succeeds.
4. Stop on error and report the `work_id` and failed step. Earlier completed Works remain completed; the failed and unprocessed Works remain pending.

### Publish

1. Select one current/deleted Work from `working/catalogue-publish-pending.json` and retain its complete change/deletion selection through Preview and Deploy.
2. If `preview_done` is false, complete that Work's selected Preview metadata/document/media writes or deletions, then persist `preview_done: true`. If it is already true, proceed directly to Deploy.
3. Deploy that Work's repository files and selected R2 media, including queued deletions. Repository copying and R2 transfers form one Deploy completion boundary; transfers use Preview bytes and the retained deletion selection.
4. Remove the entry only after the Work's combined Deploy succeeds, then process the next Work. Do not begin the next Work while the current Work's required Preview, Deploy or queue update is incomplete.
5. Once the Work queue is empty, prepare and deploy indexes and other shared output in one pass. Run this pass even when Publish starts with an empty Work queue. Report complete Publish success only after shared output completes.
6. Stop on any failure and report the affected Work/stage or shared-output step. Retain completed effects and the remaining queue state for diagnosis, manual correction and the next explicit Publish.

## Clarifications

### Refresh Completion And Failure

Persistent Studio staging resolves the earlier successful-handoff timing issue: Save changes Studio's prepared state and records the updates queue with false readiness; Refresh advances the matching Working media and metadata together. It sets each entry's `refreshed` flag to true only after that Work's required transfers, metadata/report writes or deletion and canonical staging-flag clears complete. It retains the change selection for Regenerate.

The awaited operation does not make its individual filesystem writes atomic, but completion ordering and partial-failure handling are not relevant: Stop on failure, report the affected Work and failed step, and retain completed effects for diagnosis and manual correction. There is no rollback or recovery.

### Mutation Coverage

- Each owner records its known effects as part of completion; missing coverage must not be compensated for by a routine Refresh discovery scan.
- Single Work Save/Create and subfolder batch creation supply exact changed/created Work IDs, metadata/resource changes, completed image changes and exact staged download basenames. Same-name download replacement is a media change even when canonical reference fields are unchanged.
- Bulk Work metadata and Gallery-membership edits supply only their actually changed Work IDs. Unchanged selected Works do not acquire new pending changes or lose completed readiness.
- Gallery definition, deletion and membership owners supply the affected member Work IDs when their embedded Gallery metadata or relationships change. Series definition, membership and Series–Gallery association owners supply the exact Works whose metadata or Catalogue presentation depends on the change; shared indexes and reports must still update when a definition has no affected Works.
- Work Delete supplies its exact deleted Work IDs and the captured media deletion descriptors; empty Series deletion preserves the independent Gallery definitions and updates the remaining shared relationships/reports.
- Refresh's staging-flag clears are completion bookkeeping and must not be routed back through authored-change recording.
- Deliberate external canonical edits are outside the scope of this delivery.
- Initial media population uses the baseline following manual copying of current media.
- Queue flags and filenames solely determine changes; `image_staged` and per-download `staged` flags identify the current media location for those selected inputs.
- Metadata-only updates must transfer no image bytes.
- Same-name download replacement is recorded by its Save owner in `file_names`, with that download's `staged` flag set to true.
- No operation should read/hash the complete media corpus or compare the complete Catalogue to rediscover or validate the selection.

### Publish And Deployment

- This delivery concerns Work-by-Work publishing of Catalogue by-ID JSON, Catalogue documents and Work media. Each Work completes Preview and then Deploy before the next Work starts.
- Preview and Deploy remain separate internal actions invoked sequentially by the single Publish control. Deploy includes both configured repository output and R2 transfers/deletions; its media inputs come from Preview.
- Gallery relationships, indexes and report data are prepared and deployed once after all queued Works complete. Normal/non-Catalogue documents, Search copying and publication eligibility retain their existing processing in that shared-output pass.
- The explicit deletion descriptors extend publication to owned Preview and public media removal. Implement exact identity/configuration resolution and retain the descriptors until that Work's Deploy succeeds.
- Work media uniqueness is an authoring/manual-report-review requirement; this flow must not add cross-Work file-ownership scans.
- Publish is independent of Regenerate. It consumes completed Work changes in `working/catalogue-publish-pending.json`; it does not perform Regenerate.
- `preview_done` records each queued Work's Preview completion. Regenerate initialises false on new Work records and ignores it thereafter; changes are merged into existing records without inspecting or modifying the flag. Only Publish checks or changes the initialised flag. Successful combined repository/R2 Deploy removes that Work's entry.
- Upstream actions pass changes forward and supply aligned Work metadata, documents and media. Publish consumes its queue and supplied inputs without looking back at canonical records or the updates queue to rediscover changes or decide readiness.
- An empty Work queue still runs the shared-output pass. Queue emptiness alone does not establish complete Publish success.
- Failure stops processing and reports its context. Completed and partial effects remain in place; temporary differences between destinations and shared output are acceptable while the user corrects the cause and explicitly completes Publish before normal operation resumes.
- Git commit, push and GitHub Pages deployment remain separate explicit actions.

### Referring Document Rebuilds

- Regenerating only a Catalogue document would leave baked captions and media presentations in Context and ordinary documents stale. A manual Full Rebuild after Catalogue Regeneration will update any referring documents.

## Delivery Steps

Complete the dependent writers/readers before cutover, and retain the explicit Save → Refresh → Regenerate → Publish responsibilities without compatibility aliases.

Stop and ask for clarification and discussion if any issues arise during implementation.

### Manual Initial Media Setup

The user completed the initial Working/Preview media copies on 2026-10-09. The old Publish removed the first Preview copy; the new snapshot owner excludes stage-local Work assets, and the user confirmed the repeated Preview copy. Existing Works now have false staging flags and read Working media. Studio stages subsequent edits; no initial staging copy is needed. The original shared media remains retained.

Cutover completed after the dependent implementation: 4,618 Work image flags and six download flags were initialized false; both new queues are empty and the empty old queue was retired. Canonical authored values were preserved. The user's old Publish resolved the previously regenerated Works; new per-Work publication has not yet been exercised.

No automated corpus reconciliation, source/destination comparison, bulk hashing, ownership scan or historical-media migration is needed for this setup. Normal operation validates selected inputs and acts on explicitly queued changes.

### [x] IU-0 — Readiness and initial setup

- [x] Confirm the required Studio staging, Working and Preview locations and the queue contracts.
- [x] Confirm every canonical mutation owner's required queue contribution, including Work Save/Create/Delete, subfolder batch creation, bulk changes and Gallery/Series relationship changes.
- [x] Ensure this document contains these details ready for the implementation steps.
- [x] User completed Refresh/Regenerate and confirmed the initial Working/Preview media copies.
- [x] Complete cutover after dependent implementation; initialize flags/new queues and retire the empty old queue.

Gate:

- the initial Working/Preview media baseline is user-confirmed and the old document-pending queue is empty.
- the dependent implementation and new state files are ready without automated reconciliation.

### [x] IU-1 — Save and other mutation actions

- redirect prepared images/downloads to Studio staging;
- add the Work image flag and per-download staging flags and wire editor/list/download readers.
- Make Work Save/Create, bulk edits and Gallery/Series mutation owners record their exact effects, filenames and `refreshed: false`.
- Extend Delete to capture downstream media deletion details and clean staged media.

Gate: each mutation returns with complete editor/state updates or a clear saved-but-incomplete result, and its known changes remain queued.

### [x] IU-2 — Refresh

- consume only queued current/deleted entries with `refreshed: false`; apply their matching Working metadata/media updates or deletions, complete required relationship/report output and clear transferred canonical staging flags.
- Set each entry true only after its required handoff succeeds; skip entries already true.

Gate: successfully processed Works are aligned in Working and ready for Regenerate, while failed/unprocessed entries remain false and no change-discovery scan is introduced.

### [x] IU-3 — Regenerate

- [x] Direct Catalogue Source Save/Rebuild queues completed document changes as metadata only, preserving existing media selections and initialized progress.

- consume only refreshed entries, create/update/delete the corresponding Catalogue sources and complete the agreed document Build scope.
- Pass current changes or full deletion descriptors into the publication queue before removing updates entries. Initialise a new Work record with `preview_done: false`, or merge into its existing record without inspecting or modifying the flag. Publish alone owns the initialised flag.
- For current Works, OR metadata/image change flags and combine filenames from `working/catalogue-updates-pending.json` and `working/catalogue-publish-pending.json`, then remove names absent from `work.downloads[].filename` in `working/generated/catalogue/works/index/<work_id>.json`. Preserve other outstanding selections and the Work entry needed for its metadata/document update.

Gate: completed required documents and their publication selections are ready; false-readiness, failed and unprocessed entries remain pending, with the failing Work/step reported.

### [x] IU-4 — Publish

- consume the publication queue one Work at a time; apply selected Preview changes/deletions only when `preview_done` is false, then persist true.
- Complete that Work's combined repository/R2 Deploy using Preview bytes and retained deletion identities; remove its entry only after Deploy succeeds, then process the next Work.
- After the queue is empty, prepare and deploy indexes and other shared output once, including when Publish starts with no queued Works.
- Consume the publication queue and aligned inputs supplied by upstream owners, retain unchanged content and preserve interrupted Deploy progress without resetting true flags or consulting earlier workflow state.
- Stop and report the failed Work/stage or shared-output step, preserving completed effects and remaining queue progress for manual correction and the next explicit Publish.

Gate: each Work completes Preview and Deploy before the next begins; one final shared-output pass completes overall Publish. Failures retain only unfinished Work entries with accurate Preview completion, allow temporary differences between destinations and support an explicit rerun without automatic recovery or full media reconciliation.

### [x] IU-5 — Code review and selected evidence

Selected evidence passed on 2026-10-09: explicit-path Python/JavaScript lint, Python syntax, configured service imports, field registry/canonical/queue diagnostics, runtime projection check, site validation and whitespace. Review corrected Preview asset pruning, metadata-only document queue coverage and configured Preview document path resolution. These checks provided static and diagnostic evidence; subsequent user manual evidence is recorded under IU-6. No automated workflow tests ran.

- review the bounded production/configuration/documentation changes for complete mutation coverage, flag transitions, file selection, deletion ownership and partial-failure reporting.
- Select proportionate existing lint, syntax and direct diagnostics, and resolve findings. Test creation, changes and runs require their own agreed scope; ordinary UI/manual media review remains with the user.

Gate: review findings are resolved and evidence limits are explicit.

### [ ] IU-6 — Manual acceptance and closeout

- [x] User confirmed new Work creation and subsequent deletion through the complete workflow to R2 on 2026-10-10, and reported a quicker Publish in this Catalogue queue case.
- [ ] Remaining manual acceptance covers managed-file and other unexercised variants; no exhaustive scenario coverage or measured performance is claimed.
- [x] Update durable workflow and ownership documentation now, with confirmed/remaining evidence; full manual testing may continue later.
- [ ] Resolve final acceptance and document retention recommendation. Keep this delivery and temporary handoff while that state remains open; document deletion needs approval.
- Publish, real media deletion, commit and push remain explicit actions.

Gate: the complete agreed workflow is accepted and durable ownership documentation is current.

## Follow-ons

- Remove Catalogue document editing from the UI so Catalogue content is authored through Work edits and generated templates. Determine the complete editing surface in that bounded follow-on; exact-document Rebuild remains useful for applying current generated inputs.
- Introduce similar mutation-owned queue tracking for Gallery/Series definitions and relationship changes, including changes with zero affected Works. [Gallery And Series Incremental Updates](Gallery_And_Series_Incremental_Updates.md) proposes extending both existing queue files with exact Gallery/Series and shared-output selections, preserving affected-Work contributions and replacing the coarse shared pending flag; no Catalogue discovery scans. Its schemas and completion boundaries remain proposed until implementation approval.
- Incremental Publish of normal and non-Catalogue collection docs.
- Optimisation of index and lookup JSON build, validation and Publishing.
