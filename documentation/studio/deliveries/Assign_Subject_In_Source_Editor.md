---
draft: false
doc_id: d-20261010-162449-393004
title: Assign Subject In Source Editor
added_date: "2026-10-10 16:24:49"
last_updated: "2026-10-10 17:12:00"
summary: Move Subject assignment and Folder opening into Source, use its current buffer and retire unused Document Info metadata plumbing.
ui_status: in_progress
parent_id: d-20260428-000000-f5ff18
---
# Assign Subject In Source Editor

## Outcome And Status

The user approved this change on 2026-10-10. Assign Subject is now in Source's Directives menu, before Open in VS Code, and absent from the rendered Edit menu. It reads the current complete unsaved buffer. Apply updates its Subject front matter; Save persists the combined document and owns exact document/Links generation and fresh display. Cancel preserves the buffer and returning without Save follows the existing discard prompt. Implementation and static review are complete; manual review and acceptance remain.

The user subsequently approved moving Finder into Source and removing the obsolete Document Info plumbing. **Open Subject folder** follows Assign Subject in Directives and is absent from Edit. It opens the buffer's Folder subject beneath the configured Projects root; Work, None, unsupported documents and invalid source leave it disabled. Canonical Subject meaning and assignment choices retain their existing owners.

## Owners And Payload

`docs-viewer/runtime/js/management/source-editor/directive-actions.js` owns the menu item and mounted Source adapter capture. `source-editor/subject-modal.js` owns Folder/Work/None choice and generated Catalogue search. `source-editor/source-editor.js` owns the buffer revision, dirty state and guarded replacement, retaining body selection and textarea scroll. Unsupported documents have a disabled menu entry; the exact collection's existing registered `authoring_subject` group supplies availability when Source loads.

Catalogue loading is silent. The search input remains disabled until targets are ready; missing current Works, no matching targets and load failures remain visible. Search results use the shared Catalogue image picker's `id-title` layout: the Work ID appears first in small light-grey text, followed by the title, without a type label or year subtitle.

Opening Directives reads the current buffer's Subject through the existing write-free context service. A valid Folder path is captured with the buffer revision and enables Open Subject folder; closing/reopening the menu releases/replaces that capture. Activation encodes the decoded relative target and awaits `/docs/local-link/open` through `docs-viewer-management-source-adapter.js` and the conditional workspace-provider bridge. The existing service owns configured-root confinement and filesystem existence validation. Success is silent and failures remain visible. Neither this read nor Finder activation writes source or generated output.

The write-free `POST /docs/source/context` route in `docs-viewer/services/docs_management_source_service.py` retains ordinary context reads and accepts optional Subject replacement fields:

```json
{
  "collection": "works",
  "doc_id": "d-20260801-212422-60f1db",
  "source_text": "<complete current unsaved Markdown>",
  "subject_fields": {
    "folder_path": "",
    "work_id": "00638"
  }
}
```

Without `subject_fields`, it projects the validated current Subject and assignment capability. With those fields, the exact collection's metadata aspect validates the replacement and `docs-viewer/services/docs_front_matter.py` rewrites only Subject field spans. The response carries the exact target, `subject_assignment_available`, `folder_subject_supported`, optional scalar `subject`, and prepared `source_text`. Folder capability comes from the collection's registered authoring fields. Folder preselects/prefills an existing declaration and accepts decoded relative, absolute or file-URL input; the existing collection normaliser confines/canonicalises it beneath the configured Projects root into `folder_path`, clearing `work_id`. Unsupported collections omit Folder and their metadata owner rejects such writes. None uses both empty fields and removes both declarations. Work remains an exact five-digit string, quoted by the shared formatter. Unrelated front matter, literal Summary content, body and timestamps retain their authored text; Save owns timestamp updates.

The service reads configuration and validates the supplied candidate without reading/writing saved source for this preparation. It writes no file, generated output or report. Source Save remains the sole canonical writer for this workflow. The modal uses its opening snapshot, and a changed revision or replaced editor rejects Apply while preserving the current buffer. Malformed source is reported for correction; an unavailable current Work requires a current Work, Folder or None. Cancel retains the buffer. The missing Folder choice reported for `d-20260801-212422-345458` was corrected by restoring its input and removing the blanket workspace rejection in Source context, leaving value validation with the registered collection metadata owner.

Source context now uses the complete private authoring projection rather than the public Work-only reader projection, which had omitted the current Folder and initialized the modal as None. Folder and Work return their exact scalar; an unassigned buffer omits `subject`. The Catalogue modal adapter accepts Folder responses while its Use document subject shortcut remains Work-only. Public reader projection is unchanged.

The old rendered-menu contribution and fallbacks, `docs-viewer/runtime/js/management/docs-viewer-management-project-subject-modal.js`, `assignManagedDocFieldGroup`, `/docs/assign-field-group`, its route/config entry and immediate mutation plan are retired without aliases. The now-unused `docs-viewer-management-collection-working-subjects.js` and its Manage customisation registry are removed. Collection composition/reports no longer project `projectDetailInfo` or `documentInfo`; shared view context no longer normalises or carries `metadataInfo`, its obsolete assignment flag or the former Info action definition. The old browser assignment-capability helper is also removed. The `working_works` server registration remains the Subject validation, capability and private-manifest authority. Pinned Related Links retains its existing panel shell, controller, host and captured reader context.

## Delivery And Evidence

- [x] User approved the Source-buffer helper and ordinary Save ownership.
- [x] Menu placement, modal, capability projection, guarded buffer replacement and Python field preparation implemented.
- [x] Former immediate-write path removed.
- [x] Finder moved into Source as Open Subject folder; obsolete Document Info projection and unused browser contribution/loader removed.
- [x] Durable Source, toolbar, management, runtime and Subject ownership documentation updated.
- [x] Changed-source JavaScript/Python lint, Python syntax, JSON parsing, whitespace and bounded source/reference review passed. These are static evidence; no live mutation or browser interaction was exercised.
- [x] Follow-on cleanup/Finder checks passed: explicit lint for eleven changed JavaScript modules, removed-path reference review and whitespace; `bin/site-code-update` changed exactly four shared projections, `--check` confirmed all 105 projections current and `bin/site-validate` passed. No Finder activation or browser interaction was exercised.
- [x] Folder-option correction passed explicit JavaScript/Python lint, Python syntax and whitespace review. The named canonical document was read to confirm its existing Folder declaration; no source or generated data was changed and no live Apply/Save was exercised.
- [x] Current-Subject correction passed explicit JavaScript/Python lint and Python syntax. A fresh-process read-only call to `read_source_context` with the named canonical document and configured workspace returned `subject: "projects/100 grasping hands"`, `folder_subject_supported: true` and `subject_assignment_available: true`. The command used the service's ordinary Studio path bootstrap after a first import-only attempt lacked the Catalogue package path. This is direct service evidence; the running HTTP service, browser selection, Apply/Save and Finder activation were not exercised.
- [ ] Manual review: open Source for a Context document, retain an unsaved body edit, choose a Work and Apply, then verify the combined buffer remains unsaved until Save. Check Folder preselection/prefill, changed relative or absolute/file-URL input, replacement from Work/None, None, Cancel, ordinary unsupported documents and Return/discard. Confirm saved Subject/thumbnail projection after Save. For a valid Folder subject, confirm Open Subject folder opens that exact folder, including after an unsaved Folder edit; Work/None remain disabled, missing folders report the existing error and success is silent. Confirm pinned Related Links still opens, retains its capture through navigation and closes normally.
- [ ] User acceptance.

The initial assignment implementation changed local management/service files only. The follow-on cleanup changes shared app/view context and config helpers plus the conditional workspace-provider bridge, requiring projection through `site-tools/config/site-code-update.json`. Public readers acquire no local opener because the bridge exists only when the private Source adapter supplies it. No generated document/Search data, queues, media, Publish, commit or push was changed/run. The running Docs Viewer belongs to the combined `bin/local-all` runner; the initial Python changes require restarting that runner, and subsequent JavaScript changes require a browser force-reload. The runner was inspected without stopping its services.

No test work was authorised or performed. Existing tests still refer to the retired immediate API or metadata contribution: `docs-viewer/tests/js/docs_viewer_stage_target_contract.mjs`, `docs-viewer/tests/js/docs_viewer_processing_working_collection_contract.mjs`, `docs-viewer/tests/python/test_docs_management_routes.py`, `docs-viewer/tests/python/test_docs_management_metadata.py` and `docs-viewer/tests/python/test_docs_workflow_stages.py`. Their retirement/replacement requires a separately agreed test specification under [Test Contract Discipline](../Test_Contract_Discipline.md); they are not evidence for this new workflow.

[Source Editor Scripts](../Source_Editor_Scripts.md), [Subject Associations](../data/subject-associations.md) and [Management Operations](../Management_Operations.md) own the lasting contracts.
