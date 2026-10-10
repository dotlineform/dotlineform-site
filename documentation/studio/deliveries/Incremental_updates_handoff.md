---
draft: false
doc_id: d-20261009-205717-a763b4
title: Incremental Updates Handoff
added_date: "2026-10-09 20:57:17"
last_updated: "2026-10-10 11:03:37"
summary: Temporary implementation handoff for manual acceptance of incremental Catalogue updates.
ui_status: active
parent_id: d-20261009-110914-712f45
---
# Incremental Updates Handoff

This temporary sibling preserves implementation context while [Incremental Updates](Incremental_updates.md) awaits manual acceptance. Retire it with the delivery after durable conclusions are transferred and the user approves document removal.

## Completed State And Decisions

- User approved IU-1–IU-4 implementation and removal of Full reconciliation from normal Regenerate. Normal requests are exactly `{collection: "catalogue"}`.
- Save stages complete prepared image sets and native new/replacement downloads in Projects-owned `catalogue/media-staging/`. Independent `image_staged` and download `staged` booleans select staging or Working in Studio. Public projections omit these flags.
- Mutations supply known Work IDs, metadata/image flags and exact filenames to the updates queue. Refresh selects false readiness, supplies Working metadata/media and clears flags before setting true. Regenerate selects true readiness, builds the document, merges publication selection and only then removes the update.
- On 2026-10-10, Refresh status was moved entirely into the updates queue: schema, nullable last successful UTC time and shared pending boolean form the first header section. Current/deleted `refreshed` flags remain authoritative for Work handoff. Mutations mark shared pending without losing the timestamp; full Refresh completion clears the flag and advances the time. Regenerate preserves the header. The separate receipt and Catalogue/configuration hashing are removed. Similar exact Gallery/Series queue tracking remains a follow-on.
- Publish owns initialized `preview_done`: each Work completes Preview then repository/R2 Deploy before removal. Upstream merges preserve initialized progress without inspecting its value. An interrupted Deploy must be completed before normal editing resumes.
- Final shared preparation retains completed Catalogue by-ID metadata/documents, rebuilds ordinary and other collection documents and copies saved Search unchanged. The Preview snapshot walker prunes `assets/` before enumeration so replacement cannot remove or hash the Work-media corpus.
- The separate `python3 docs-viewer/build/reconcile_catalogue_design.py --write` command reconciles source templates, performs one full Catalogue build and merges completed publication changes once. It does not consume false-readiness entries or invent media transfers.
- User approved direct Catalogue Source Save/Rebuild as a document-only contributor. `docs_document_rebuild.py` queues successful Catalogue builds with metadata true and no new media, preserving existing selections/progress. Source Save already uses this owner.
- Catalogue sources remain editable in this delivery. Normal Regenerate preserves body text except when the Work title changes; title change or design maintenance restores the generated template. Removing Catalogue editing from the UI is recorded as a follow-on.
- The user ran the old Publish for previously regenerated Works `00639` and `04625`. The old snapshot owner removed the first manual Preview media copy; the new pruning fix landed and the user confirmed the repeated copy. Working media remained intact.
- One-time cutover initialized 4,618 image flags and six download flags false, created two empty private queues and retired the empty old queue. Canonical authored values were preserved. Do not rerun the initializer; it intentionally refuses existing queues. Original shared Work media remains retained.

## Owning Changes

The private queues live directly below the configured Docs Working root: `catalogue-updates-pending.json` uses `catalogue_updates_pending_v3` in its header; `catalogue-publish-pending.json` uses `catalogue_publish_pending_v3`, with `schema` then nullable `last_published_at_utc` in its header. Both headers are written before their current/deleted Work maps. Publication contributors preserve the last queue completion time. The final Work's successful Deploy advances it with entry removal, independently of the later shared pass; partial failures and initially empty queues preserve it. Missing/malformed files stop operations. No runtime aliases read old queue/receipt formats.

Workspace schema is `docs_workspace_v5`. Configuration owns separate Working/Preview Work-media roots and shared document media. Temporary Preview builds explicitly use the real Preview Work asset root through `--work-assets-base-dir`, independently of shared document assets.

Changed repository paths at handoff are listed below. The separate dirty `site/assets/data/docs/` files are the user's old Publish output and were preserved.

```text
docs-viewer/build/build_preview.py
docs-viewer/build/docs_builder/runtime_bootstrap.py
docs-viewer/build/reconcile_catalogue_design.py
docs-viewer/config/workspace/docs-workspace.json
docs-viewer/runtime/js/management/docs-viewer-management-catalogue-regenerate-modal.js
docs-viewer/runtime/js/management/docs-viewer-management-catalogue-regenerate.js
docs-viewer/services/docs_catalogue_artifacts.py
docs-viewer/services/docs_catalogue_publication.py
docs-viewer/services/docs_catalogue_regeneration.py
docs-viewer/services/docs_catalogue_source_inventory.py
docs-viewer/services/docs_deploy_repo.py
docs-viewer/services/docs_document_rebuild.py
docs-viewer/services/docs_prepare_preview.py
docs-viewer/services/docs_preview_snapshot.py
docs-viewer/services/docs_public_media_reconciliation.py
docs-viewer/services/docs_publish.py
docs-viewer/services/docs_workspace_config.py
docs-viewer/services/docs_write_rebuild.py
documentation/studio/Catalogue_Deployment.md
documentation/studio/Catalogue_Save_And_Refresh.md
documentation/studio/Catalogue_Services.md
documentation/studio/Catalogue_Work_Editor.md
documentation/studio/Configuration_And_Extension_Points.md
documentation/studio/Development_Checklist.md
documentation/studio/Docs_Viewer_Runtime.md
documentation/studio/Media_And_Asset_Handling.md
documentation/studio/Planned_Features.md
documentation/studio/Public_Work_JSON_Review.md
documentation/studio/Source_Organisation.md
documentation/studio/Sub_Scope_Index_Architecture.md
documentation/studio/deliveries/Incremental_updates.md
documentation/studio/deliveries/Incremental_updates_handoff.md
studio/app/frontend/js/catalogue-editor-shell-media.js
studio/app/frontend/js/catalogue-media-preview.js
studio/app/frontend/js/catalogue-work-action-records.js
studio/app/frontend/js/catalogue-work-editor.js
studio/app/frontend/js/catalogue-work-sections.js
studio/app/frontend/js/catalogue-work-series-browser.js
studio/app/server/studio/studio_app_config.py
studio/data/canonical/catalogue/works.json
studio/data/config/catalogue/catalogue-field-registry.json
studio/services/catalogue/catalogue_build_media.py
studio/services/catalogue/catalogue_delete_service.py
studio/services/catalogue/catalogue_gallery_service.py
studio/services/catalogue/catalogue_incremental_cutover.py
studio/services/catalogue/catalogue_json_build.py
studio/services/catalogue/catalogue_lookup.py
studio/services/catalogue/catalogue_media_version.py
studio/services/catalogue/catalogue_output_media.py
studio/services/catalogue/catalogue_output_paths.py
studio/services/catalogue/catalogue_output_service.py
studio/services/catalogue/catalogue_pending_publication.py
studio/services/catalogue/catalogue_pending_state.py
studio/services/catalogue/catalogue_pending_updates.py
studio/services/catalogue/catalogue_refresh_service.py
studio/services/catalogue/catalogue_series_service.py
studio/services/catalogue/catalogue_source.py
studio/services/catalogue/catalogue_source_mutation.py
studio/services/catalogue/catalogue_staged_media.py
studio/services/catalogue/generate_work_pages.py
```

## Evidence And Commands

- `bin/lint-python <35 explicit changed/new Python paths>`: passed. The exact submitted boundary is every Python path in the inventory above.
- `bin/lint-js <8 explicit changed JavaScript paths>`: passed. The exact submitted boundary is every JavaScript path above.
- Project Python `-m py_compile <the same 35 paths>`: passed; only normal ignored bytecode cache writes.
- `python3 studio/services/catalogue/verify_catalogue_field_registry.py`: passed against the current canonical model.
- With `.env.local` exported and the existing `ensure_studio_python_paths` bootstrap, imports of Publish, Regenerate, exact-document Rebuild, Refresh, Save completion and cutover passed. Earlier ad hoc import diagnostics omitted the shared bootstrap and failed on `local_env`; the corrected diagnostic passed without a production change.
- Existing canonical validation and strict queue readers completed: 4,618 Works, six downloads, zero true staging flags and both queues empty. Exact `00639-primary-800.webp` exists in Working and Preview. This is one selected file observation, not a corpus audit.
- `bin/site-code-update --check`: passed, 105 projected runtime files unchanged. Changed browser files are local management/Studio files outside the public inventory, so no projection write was required.
- `bin/site-validate`: passed (61 required files, seven directories, 105 projected code files, 73 runtime modules).
- `git diff --check`: passed after the handoff/document update.
- Focused changed-file scan for private machine paths, API keys and private-key markers: no matches.
- Source review covered mutation contributions, staged media selection, queue transitions, retained deletion descriptors, Preview completion, configured repository/R2 identities, final snapshot ownership and direct document queue contribution. Removed discovery/full-mode runtime references were checked; the old queue path remains only in the explicit cutover initializer.

The 2026-10-10 header migration preserved the current/deleted selections. The queue was empty and no receipt existed, so its initial header has a null time and shared pending true; the next successful Refresh supplies the first time. The obsolete receipt path is absent. Explicit-path lint and project Python syntax passed for the six changed modules: `studio/services/catalogue/catalogue_pending_state.py`, `studio/services/catalogue/catalogue_pending_updates.py`, `studio/services/catalogue/catalogue_output_service.py`, `studio/services/catalogue/catalogue_refresh_service.py`, `studio/services/catalogue/catalogue_incremental_cutover.py`, `docs-viewer/services/docs_catalogue_regeneration.py`. Configured Save/cutover/Regenerate imports and strict updates/publication readers passed; status returned `{ok: true, needed: true}`. The updates file was inspected with the header first and its fields in the requested order. Source review confirmed Save preserves the timestamp while marking shared pending, Refresh persists pending state before effects and advances time only on full completion, and Regenerate iterates only Work families while preserving the header. `git diff --check` passed. No new tests or live Refresh writes ran; failure and timestamp-transition behavior received source review only.

The subsequent publication header migration changed three Python owners: `studio/services/catalogue/catalogue_pending_state.py`, `studio/services/catalogue/catalogue_pending_publication.py` and `studio/services/catalogue/catalogue_incremental_cutover.py`. The saved v1 queue was empty; migration carried its Work maps into the v2 header format without altering entries or progress. Explicit-path `bin/lint-python`, project Python `-m py_compile`, configured Publish/Regenerate/cutover imports, strict readers for both saved queues and `git diff --check` passed. The publication file was inspected with `header.schema: catalogue_publish_pending_v2` first. The updates header remained at null time and shared pending true. Source review confirmed publication merge and removal paths preserve the header; no live Publish ran.

The publication timestamp follow-up migrated the saved empty queue from v2 to v3, preserving its maps and initializing `last_published_at_utc: null`. The user clarified that this time belongs to the Catalogue Work queue. Its final successful Deploy records the timestamp in the same write that removes the final entry; an initially empty queue or partial queue failure preserves the previous time, and later shared-output failure retains completed Catalogue time. The four changed Python owners were `studio/services/catalogue/catalogue_pending_state.py`, `studio/services/catalogue/catalogue_pending_publication.py`, `studio/services/catalogue/catalogue_incremental_cutover.py` and `docs-viewer/services/docs_catalogue_publication.py`. Explicit-path lint and project Python syntax, configured Publish/Regenerate/cutover imports, both saved strict queue readers and `git diff --check` passed. The saved v3 header order and null time were inspected; updates header values remained unchanged. Timestamp success/failure transitions received source review only; no live Publish or new tests ran.

No tests, test/fixture/harness changes, browser automation, new-workflow image conversion, Refresh/Regenerate/Publish, real deletion, R2 calls, Git commit/push or public deployment were performed by Codex. No performance measurements are claimed.

The 2026-10-10 timestamp-only shared-output fix exposes the existing `same_generated_content` comparison in `studio/services/catalogue/generate_work_pages.py` and reuses it in `studio/services/catalogue/catalogue_refresh_service.py`. Refresh compares each generated shared payload with its saved Working JSON, ignoring only `header.generated_at_utc`, and skips unchanged writes while retaining exact bytes. Missing or invalid replaceable JSON is written from canonical inputs. The result's written list includes only actual writes. Selected Work handoffs and queue completion time retain their existing behavior. Explicit-path lint and project Python syntax passed for those two modules. No live Refresh/Publish or tests ran for this fix. Restart Local Studio before the next manual check; the existing timestamp-only `site/` changes are retained. Gallery/Series selection queues remain follow-on work.

## User Manual Evidence

On 2026-10-10, the user confirmed adding a new Work through the complete workflow to R2 and then deleting it through to R2. During the creation check, Work `04626` displayed its newly staged image immediately, and later read-only inspection showed its completed Refresh readiness. Existing Working images for `04626` and `04627` matched the copied baseline; `04627` had no current canonical Work. Reused `04626` image identities with different old bytes explained the initial media version 2. These observations do not establish managed-download or interrupted-operation behavior.

The user reported that Publish seemed quicker with the Catalogue queue. This is qualitative user feedback; no benchmark or elapsed-time comparison was performed. Managed-file and other variants remain unverified by this report. The live R2 add/delete evidence is the user's manual confirmation; Codex did not repeat those operations or independently inspect remote objects.

## Durable Documentation Transfer

Current behavior is maintained independently of further manual testing in [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md), [Catalogue Deployment](../Catalogue_Deployment.md), [Catalogue Work Editor](../Catalogue_Work_Editor.md), [Catalogue Services](../Catalogue_Services.md), [Media And Asset Handling](../Media_And_Asset_Handling.md) and [Source Organisation](../Source_Organisation.md). These owners now include the everyday operation sequence, strict v3 headers/entry shapes and flag ownership, completion timestamp scope, selected media locations, deletion lifecycle, failure handling and evidence limits. Existing Docs runtime documentation retains queue-only Regenerate and exact-document queue contributions. The Work Editor's obsolete blanket media-retention statement was replaced with the selected staged/Working/Preview/repository/R2 deletion ownership.

This transfer does not depend on finishing every manual scenario. New-Work creation and deletion through R2 are user-confirmed; managed-file and other variants and live partial failures remain unverified. Subsequent testing can update evidence without reconstructing the implementation from this handoff. Documentation-only whitespace and linked-owner/source review are the current checks; no lifecycle operation or executable workflow test was added for the transfer.

## Remaining Work And Limits

1. Continue user manual acceptance for managed-file and other unexercised variants.
2. Keep the delivery active until the remaining acceptance gate is resolved. Preserve the user's published `site/` delta; Git actions remain explicit.
3. After acceptance, update the already-current durable evidence, mark the delivery complete and recommend retention/removal. Do not delete documentation without approval.

If an eligible Catalogue source has no retained Preview document, shared Publish stops with instructions to queue Regenerate or run explicit design maintenance. In particular, restoring an excluded Catalogue collection may require design maintenance to repopulate documents. No unqueued implicit Working-to-Preview fallback is provided.

File/media effects are not atomic. Stop at the reported Work/step, correct the cause and explicitly rerun the owning operation. Completed effects remain; no rollback, backup corpus, ownership scan or automatic retry exists. Live failure handling remains unexercised; the new-Work creation and deletion lifecycle has the user manual confirmation above.

