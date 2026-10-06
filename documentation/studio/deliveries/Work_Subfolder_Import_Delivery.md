---
draft: false
doc_id: d-20261006-143427-866b9d
title: Work Subfolder Import Delivery
added_date: "2026-10-06 14:34:27"
last_updated: "2026-10-06 15:37:37"
summary: Create one new Work per image in a selected project subfolder, using shared New Work metadata and manual import tracking.
parent_id: d-20260428-000000-f5ff18
---
# Work Subfolder Import Delivery

## Current And Next State

Status: complete and accepted on 2026-10-06. The user accepted the delivered workflow after the sequential-ID and matching icon-button refinements and authorized closeout. Parent: [Planned Features](../Planned_Features.md).

Complete result: in the [Catalogue Work Editor](../Catalogue_Work_Editor.md) at `/studio/catalogue-work/`, New Work mode can load all supported images from one selected project subfolder, accept shared metadata in the existing form and save one independent canonical Work per image. Each title comes from its filename stem. The user tracks completed imports through existing reports.

No implementation work remains in this slice. Retain this delivery for recent-work lookup pending manual archive. Refresh Catalogue, publication and Git actions remain separate.

## Requirements And Decisions

- Add an **Open subfolder** icon button beside **project subfolder**, available in New Work mode. Reuse the Select file button's folder-open artwork and icon-button styling, keeping **Open subfolder** as the tooltip and accessible label. Use the configured media source and project-folder/subfolder selection boundary; source originals remain in their existing locations.
- Reuse the existing **Select file** modal with an explicit folder-selection mode titled **Select folder**. Retain folder/subfolder navigation and show supported image filenames in the existing modal file list, using read-only text rows. Display filenames only; this does not add thumbnails or rendered image previews. Individual file selection does not determine the import; **OK** confirms the loaded folder and every listed image. Disable confirmation while loading, after a load failure or when no supported images are available.
- Load every supported image directly inside the selected subfolder, using the current Catalogue image-file policy. Do not recurse into descendant folders. Non-image files, hidden files and symbolic links follow the existing picker exclusions.
- Return the configured media-source identity, project folder, subfolder and complete filename list already loaded by the picker. Return relative source identities rather than absolute filesystem paths. The editor builds the pending batch from this result without another folder-listing request.
- Folder selection creates an unsaved batch in the editor. It does not create canonical Works, convert media or trigger Catalogue Refresh. Retain the returned filenames internally and show the selected folder through the existing source fields. Use the ordinary New Work editing and Save flow without a pending-image summary, file-count display or additional confirmation; cancelling the modal leaves the draft unchanged.
- Create exactly one new Work per included image. Use the filename with only its final extension removed as the initial title: `blue flower.jpg` becomes `blue flower`. Titles need not be unique. Retain each image's exact configured media source, project folder, subfolder and original filename in its Work source fields.
- Treat the existing New Work metadata form as a shared template. Series, Year, Year display, Galleries and other entered metadata apply to every addition; title, Work ID and source filename are determined separately for each image. Required shared fields must be complete before Save.
- Assign consecutive five-digit Work IDs through the server-owned batch-create operation, using deterministic filename order and starting one above the highest current canonical Work ID. Lower unused IDs may be reserved and must remain untouched by batch import; they can be filled deliberately through individual creation. Validate IDs against current canonical Works before writing; batch creation must not overwrite an existing Work. Reject a batch that exceeds the five-digit range before any write, without falling back to gaps.
- Do not detect, skip or prevent previously imported images. Every invocation includes all supported images in the selected folder, including on reimport. Do not use title uniqueness, image hashes, source-path comparisons or a saved import ledger to deduplicate. The user manually tracks imports with existing reports.
- Save creates the batch in one awaited local operation and completes the normal Work image renditions and thumbnails. The editor remains busy until the complete outcome is known. Validation errors retain the pending batch; failures after canonical persistence identify the created Works and incomplete step under the existing [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) completion model. Never present an incomplete operation as wholly unsaved or automatically reimport it.
- The confirmed filename list defines the batch through Save. Resolve and validate each required image within its configured source as it is read; do not enumerate the folder again to rediscover or expand membership. Images added after **OK** are included only by reopening the picker; missing or unreadable confirmed images fail visibly through the normal Save completion owner.
- Preserve ordinary single-Work creation and editing, existing bulk Gallery editing and their draft-discard protection. Batch import is a new creation capability; retired Work Detail browsers, records, endpoints and compatibility aliases are not restored.
- Refresh Catalogue remains an explicit separate action. Docs Build, Search, Publish, Git commit/push and public deployment are outside this delivery.

## Key Design

The Work editor owns the unsaved batch and shared metadata, while the existing project-media picker/service owns confined folder navigation and supported image listing. Extend the shared [File Picker](../File_Picker.md) with an explicit folder-selection mode and use it through the current Work editor modal adapter. Preserve the existing single- and multiple-file selection contracts. In folder mode, file rows are informational and confirmation depends on a valid loaded folder with supported images, rather than a selected filename. Reuse the current form, busy-state and unsaved-change owners. Use the configured Projects media source without an inferred filesystem root or replacement workspace. The feature is local Studio authoring and adds no public browser capability.

The picker already has the complete supported filename list for its current folder. **OK** returns that list together with the folder identity, so the editor can retain the unsaved batch and derive its titles without another request. The existing modal filename list is the only file listing required for this flow; the editor adds no pending summary or count. Do not request another listing after confirmation or during Save. The returned list establishes import membership; server-side source confinement and validation of each actual image remain required when those inputs are used.

A focused batch-create service owns complete-batch validation, Work-ID allocation and one combined canonical Works/Gallery-membership transaction. Read and validate the required Catalogue state once for the operation, rather than issuing a separate create request and rewriting the full Catalogue for each image. Reuse the normal Work source, membership and media-completion owners. The existing bulk-save path remains scoped to edits of saved Works.

Keep the interface to one folder action, the reused selection modal, the shared metadata form and the existing Save/Cancel flow. Pending-summary UI, file counts and additional confirmation are excluded by user decision. Per-image metadata editing before Save, individual image selection, arbitrary-depth folders and import-history management are outside this slice; saved Works can be edited individually through the normal editor.

## Deliverables

- [x] New-mode **Open subfolder** control, confined folder selection and internal unsaved batch state using the ordinary form/Save flow.
- [x] Shared picker folder-selection mode, **Select folder** modal title, existing filename list with read-only text rows and a return value containing folder identity plus the complete loaded filename list.
- [x] Shared metadata handling, required-field validation, pending-batch cancellation and normal unsaved-change protection.
- [x] Server-owned batch creation with consecutive IDs above the highest current canonical ID, filename-stem titles, exact per-image source references and shared metadata/memberships.
- [x] Awaited normal media completion, accurate success/incomplete results and editor/list reconciliation for all created Works.
- [x] Durable Work Editor and Save/Refresh documentation updated after implementation, with focused evidence and independent code review.
- [x] User acceptance of the delivered creation workflow and authorization to close.

## Process

1. Open `/studio/catalogue-work/` and enter New Work mode. Choose the appropriate media source/project context as needed.
2. Click **Open subfolder** to open **Select folder**. Navigate to the project subfolder and use the existing read-only filename list. Click **OK** to return the folder identity and all loaded filenames; the editor retains them internally and updates the existing source fields without rescanning, displaying a pending summary or asking for another confirmation.
3. Complete the shared form fields, including required Series, Year and Year display. Every pending Work receives these shared values; each retains its own filename-stem title and source filename.
4. Click **Save**. The server validates and creates Works for the confirmed filename list, then completes their normal local media. It resolves and validates each required source image as it is read without enumerating the folder again. Editing remains unavailable until completion or a reported failure.
5. Report success through the existing Save status owner and reconcile the created Works into the editor's normal list/search state so they can be opened individually. On incomplete completion, show the created IDs and exact unfinished step for manual diagnosis; do not offer an automatic replay of the batch.
6. Track imported folders/images through the existing reports. Run Refresh Catalogue when generated readers should receive the new Works; publishing remains separate.

## Delivery Steps

### WSI-0 — Readiness

- [x] Record the agreed workflow, shared metadata and explicit absence of duplicate detection.
- [x] Record the agreed shared-modal folder mode, existing filename list with read-only text rows and reuse of the loaded filename list through Save.
- [x] Record that the normal form/Save flow needs no pending summary, file-count display or additional confirmation.
- [x] Identify the current Work editor, project-media picker, canonical create/membership services and media-completion owners through read-only inspection.
- [x] Confirm that the specification is one finishable slice and approve implementation.
- [x] Confirm configured media storage is available and note the pending-batch/editor adoption boundary before implementation starts.

Verification budget: source/documentation inspection only, with no executable tests or data writes. Stop for unavailable configured storage or a requirement that changes the agreed folder, shared-field or Save boundary; resolve that requirement before implementation.

Record: the request to start delivery authorizes the agreed implementation. Configured Projects, Processing and Docs asset directories are available. The editor will retain the picker result until validation and Save; canonical success releases the pending creation batch and adopts saved Works even when media completion fails. The shared picker contains historical loader/initial-selection aliases; its sole active adapter will explicitly map service records to the direct picker contract, allowing those aliases to be removed. No runtime import or test changes have been performed.

### WSI-1 — Implementation And Focused Evidence

- [x] Implement the complete folder-to-pending-batch-to-Save workflow through the current owners.
- [x] Preserve existing file-selection modes while adding read-only folder confirmation and reuse the returned filenames without further directory enumeration.
- [x] Preserve normal single/New Work behavior, bulk Gallery editing and explicit Refresh timing.
- [x] Update the durable authoring/completion documentation and record the exact focused evidence and remaining limits.

Verification budget: changed-path JavaScript/Python lint, Python syntax and bounded whitespace/source review address module, syntax, ownership and request/response defects. These have small local cost and do not create canonical Works or media. Select any additional existing evidence only after inspecting its actual coverage and side effects. No automatic suites, browser automation, new tests, fixtures or temporary regression scripts are authorized by this proposal; test work requires a separate specification and approval under [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md).

Gate: the full batch is validated before canonical mutation, required local completion is awaited and editor results distinguish success from incomplete completion. Source/request review confirms that the loaded filenames flow from picker confirmation through Save without another directory enumeration. Folder navigation, read-only filename rows, loading/empty/error confirmation states, cancellation, unchanged ordinary file selection, shared metadata, filename titles, repeated import behavior and the resulting Works/media receive user manual review. A real Save writes canonical Works, memberships when assigned and shared local image renditions; its time and resource cost depend on image count and source sizes and must be stated before any agreed automated real-data run.

Record: the shared picker and Work adapter return exact loaded filenames; the editor retains them internally, makes ID/title batch-owned and uses the ordinary shared metadata and Save flow. The focused batch-create service validates all proposed records/memberships and writes one combined transaction before normal media completion. Every saved Work enters live search/list state and the first opens individually; canonical success releases creation intent even on incomplete completion. Changed-path JavaScript lint passed for all 14 changed/new JavaScript files; Python lint and syntax passed for all 10 changed/new Python files. Whitespace review passed. No tests were authored, changed or run, and no real Save, browser review, media conversion, Refresh, Build, Search, Publish, commit or push was performed. The changed shared picker is excluded from the explicit public runtime inventory, so no site projection was required. Durable [Work Editor](../Catalogue_Work_Editor.md#import-a-project-subfolder), [Save/Refresh](../Catalogue_Save_And_Refresh.md#save-boundary) and [File Picker](../File_Picker.md#returned-boundary) documentation is current. Static evidence does not establish runtime success or failure-path coverage.

### WSI-2 — Code Review

- [x] Independently review the final bounded code/config/documentation diff after implementation and selected evidence.
- [x] Check picker-mode separation, folder/filename return agreement, confirmed-batch membership without rescanning, ordinary form/Save flow without summary or extra confirmation, path confinement, complete-batch validation, ID uniqueness, unchanged original files, shared/per-image field separation, write/media completion, failure adoption, busy-state handling and absence of deduplication or retired Detail compatibility code.
- [x] Resolve findings and rerun only evidence affected by review changes.

Verification budget: bounded source/diff review, followed only by checks justified by a concrete finding. Gate: no unresolved issue prevents the agreed result; report evidence limits rather than claiming unexercised failure coverage.

Record: a distinct final source/diff review found and resolved case-insensitive picker filtering of distinct names, trimming/unquoting of exact source components across picker/request/source/media owners, cancellation of the read-only batch ID field, and reused-ID renditions that could otherwise survive a new creation. The unused historical picker aliases were removed and service mapping stays in the adapter. Batch media/editor errors include created IDs; an unavailable response reports an unconfirmed outcome without automatic replay. A superseded picker load cannot enable confirmation for a different folder. Only affected lint/syntax checks were repeated after fixes; no unresolved source-review finding remains. Runtime acceptance comes from the user's closeout confirmation; no automated browser, real-write, conversion or incomplete-operation coverage is claimed.

Allocation review: the user's 2026-10-06 clarification is implemented. Batch IDs now advance consecutively above the highest current canonical ID, preserving lower gaps that may be reserved. The complete batch fails before writes if it would exceed `99999`. Read-only canonical inspection found highest ID `04623`, so the next batch starts at `04624` in that snapshot. Focused batch-service lint, Python syntax and whitespace checks passed; source review confirms no gap-fill fallback. No canonical Work mutation or real import was run for this change.

### WSI-3 — Closeout

- [x] Record user acceptance and closeout authorization, preserving the limits of the reported manual evidence.
- [x] Reconcile the complete result and evidence with current durable Work Editor and Save/Refresh documentation.
- [x] Update Planned Features and present whether this delivery should be retained for lookup or retired after durable transfer; document deletion requires approval.
- [x] Report remaining omissions and separate Refresh, publication and Git outcomes accurately.

Verification budget: documentation/source review and accepted implementation evidence. Do not repeat builds or tests solely for closeout. Gate: the complete creation workflow is accepted and its durable owner is current.

Record: the user said “great! ok to close” on 2026-10-06 after accepting the ID-allocation and icon-button refinements. This records acceptance of the delivered slice without inventing a per-scenario manual test record. Durable Work Editor, Save/Refresh and File Picker documentation is current, and Planned Features now records completion. Retain this delivery for recent-work lookup pending manual archive. Closeout changed documentation only and reused the accepted source review, lint, syntax and whitespace evidence; no further tests, real-data operations or builds were run. Codex did not run Refresh, publication, commit or push.

## Follow-on

No additional capability is scheduled. Duplicate detection and import-history tracking remain outside scope by explicit user decision. Any later per-image draft editing or deeper folder traversal needs a separately agreed requirement.
