---
draft: false
doc_id: d-20261004-183033-8521af
title: Work Editor Media Delivery
added_date: "2026-10-04 18:30:33"
last_updated: "2026-10-04 19:14:30"
summary: Native Work attachment selection with automatic Work ID naming, explicit image regeneration on confirmed selection, and Finder links for original source locations.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Work Editor Media Delivery

## Current And Next State

Status: active. The user approved the bounded implementation and 64 MiB combined attachment limit on 2026-10-04 after clarification that retained media intent does not imply another Save will fix an unresolved failure. WEM 1 and WEM 2 are implemented, focused lint/syntax checks and WEM 3 code review passed, and the durable Save/authoring owner is updated. Next: restart local Studio, reload the Work editor and complete the user's Safari/Edge, deliberate media-write and Finder acceptance. WEM 4 remains open; no tests, real media writes, Finder launches, generated rebuilds, Publish, commit or push have run.

The temporary native-file chooser demo was removed at the user's request on 2026-10-04 after manual review. This cleanup does not start the production delivery; the custom image-picker folder-list fix remains in place.

Complete result: the local Studio Work editor adds or replaces attachment files through the native browser chooser, regenerates image renditions after an explicitly confirmed image selection even when its path is unchanged, and opens its recorded source folders or reveals its original image in Finder.

This standalone delivery is parented to [Planned Features](../Planned_Features.md). [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) owns the durable Save/completion boundary and will receive the shipped authoring behavior. [Development Checklist](../Development_Checklist.md) and [Development Workflow](../Development_Workflow.md) govern implementation and closeout.

## Requirements

### Native Add File And Automatic Naming

- **Add file** opens the standard browser `<input type="file">` chooser directly and selects one file. Safari is the primary manual-review browser; Edge is also supported. A separate label-entry modal is unnecessary when adding a file.
- Selection adds the file to the current Work draft and marks it unsaved. The initial display label is the selected original filename, including its extension. Cancelling the chooser leaves the draft unchanged.
- **Edit** allows the attachment label to change. Keep the stored filename identity separate from the editable label; changing a label does not rename the stored file or require another upload.
- The server automatically derives the stored filename as `<work_id>-<selected_filename>`, using the exact five-digit Work ID and a validated safe basename. For Work `00008`, selecting `nerve.pdf` stores `00008-nerve.pdf` with initial label `nerve.pdf`. Preserve the selected basename and extension; reject unsafe names rather than accepting paths. Apply naming at the write owner rather than trusting a browser-generated destination.
- Selecting the same filename for the same Work intentionally replaces that attachment's contents on the next Work **Save**. Reuse its existing download entry and preserve any edited label. Do not add a duplicate entry, random suffix or replacement-confirmation modal.
- An attachment selection or replacement must enable Save even when the download filename and label are unchanged. Keep the selected file contents with the current draft until Save; selection alone does not write to permanent storage. Discarding that draft discards its pending upload.
- Save transfers the selected contents to the local service, stores the opaque file bytes in the configured shared Work-download destination, and persists its canonical `downloads` reference. Existing `downloads` records retain their `{filename, label}` shape. Complete the awaited Save operation before returning the editor to ready.
- Normal Save uses the pending native upload when present and otherwise retains the existing managed attachment. Retire automatic matching-file ingestion from Catalogue download staging when this flow replaces it, so an old staged file cannot overwrite a native replacement on this or a later Save. Leave those staged files on disk for manual cleanup; introduce no compatibility fallback.
- Existing attachment names and references remain valid. There is no bulk rename or migration of previously stored files. Existing downloads continue to load and publish through their current owners.

The current download flow accepts a manually supplied filename and copies a matching staged file into configured shared assets. It does not currently add a Work ID prefix or accept browser file bytes. Extend the Catalogue-owned Save/upload boundary with a bounded file transfer; do not raise the general JSON request limit as a substitute for an owned upload contract. Resolve permanent storage through Docs workspace configuration, independently of the selected file's original folder.

### Confirmed Image Selection Requests Regeneration

- Retain Studio's custom **Choose image** picker and the canonical source root, project folder, subfolder and filename. Those references continue to support Projects, Missing Source Files and Uncataloged Files.
- Clicking **OK** with a valid image selection explicitly requests image regeneration, including selection of the exact same source root/folder/subfolder/filename as the saved Work. Mark the editor unsaved, enable Save and show the existing unsaved/Save indication. Do not invent a metadata change solely to make the draft dirty.
- Closing or cancelling the image modal without confirming a selection does not request regeneration. Confirming a selection does not convert or write images before Work Save.
- Carry the explicit regeneration intent through Save independently of source-field differences. This is transient operation state, not a new persisted canonical Work property.
- On Save, read the selected original's current contents and regenerate the complete configured primary/srcset and thumbnail set. A confirmed request bypasses both the unchanged-source-field check and any modification-time decision that would otherwise skip conversion.
- Retain the existing measured-dimension and media-version rules: changed existing rendition bytes advance `media_version`; identical regenerated bytes or missing-rendition repair retain it. A forced conversion is not automatically a new content version.
- Clear pending regeneration only after image completion succeeds, or when the user discards the draft. If canonical data saves but image completion fails, report that distinction through the current Save failure boundary and keep the explicit regeneration request available for a user-initiated Save. Add no automatic retry or persistent recovery marker.
- Metadata-only saves continue to avoid image conversion. Refresh Catalogue continues to generate reader data separately; it does not regenerate images or become part of Save.

### Finder Links For Source Values

Make the displayed project folder, project subfolder and project filename values keyboard-accessible links using the current draft selection and its exact configured media source.

| Displayed value | Finder action |
| --- | --- |
| Project folder | Open the selected source root's project folder. |
| Project subfolder | Open that subfolder beneath the selected project folder. |
| Project filename | Reveal and select the original file in its containing folder; do not launch the file's default application. |

Empty values remain plain empty-state displays. A newly confirmed selection updates the link targets immediately, including in New Work; opening Finder does not save, change the draft or request regeneration. Keep links unavailable during the existing busy operation boundary and in bulk mode, where there is no single source target.

Resolve link targets at the owning local service through the existing configured Work-media root/path validation. The browser supplies source identity and safe relative components, not an arbitrary absolute path or shell command. Reuse the existing shared OS-opening helper after domain validation rather than duplicating Finder process handling or importing Docs Viewer frontend code into Studio. Missing targets and unavailable roots/platforms report a clear failure without opening a substitute location. Finder actions remain local capabilities and do not enter public readers.

### Scope And Completion Boundaries

The scope is Studio's Work editor, its Catalogue-owned local service, managed attachment writes, image conversion intent and Finder activation. Preserve source-file report semantics and the existing custom image picker's folder capture. Preserve Save's canonical-success versus incomplete-media distinction, explicit Refresh ownership, publication ownership and manual media cleanup.

Docs Viewer native Add image/Add file changes are a separate follow-on. Automatic image watching, batch regeneration, original-image copying, source-reference migration, report redesign, automatic media deletion, Publish, deployment, commit and push are outside this delivery. The temporary native-file chooser demo has already been removed after manual review; retain the delivered image-picker folder-list fix.

## Deliverables

- [x] Native single-file Work attachment selection with filename-based initial labels and existing label editing.
- [x] Catalogue-owned file transfer and automatic Work ID prefixing into the configured shared attachment destination.
- [x] Intentional same-name replacement without duplicate references, including Save activation for contents-only changes.
- [x] Explicit image-regeneration intent from confirmed custom-picker selection through complete Work Save conversion.
- [x] Finder links for the three displayed source values, using configured source identities and shared OS-opening support.
- [x] Removal of the temporary native chooser demo after manual review.
- [x] Retirement of code made unused by the production attachment flow, without compatibility aliases.
- [ ] Focused verification, bounded code review, user manual acceptance and updated durable Save/authoring documentation.

## Process

1. Open an existing Work and choose **Add file**. Select a file from any accessible folder; the draft gains its filename-based label. Use **Edit** if a different label is needed, then Save to store the automatically prefixed file and reference.
2. To replace that attachment, choose **Add file** and select a file with the same original filename. Its existing entry and edited label remain; Save writes the replacement contents.
3. To regenerate Work images after editing an original, open **Choose image**, select the original again and click **OK**. The editor requests Save even when all source values are unchanged. Save regenerates the configured renditions from the current original.
4. Click the project folder or subfolder value to open that directory in Finder, or the filename value to reveal the original. These actions are independent of saving.
5. Use the existing explicit Refresh Catalogue operation when current generated reader metadata is needed. Publish and public release retain their separately authorized workflows.

## Delivery Steps

### WEM 0 Readiness

- [x] Confirm the broad Work-draft, Catalogue Save/media-write, source-resolution and Finder owners against the current product.
- [x] Assess upload transport/size limits and how attachment bytes join Save without a persistent staging dependency or a second writer. Confirm retirement of normal Save's staged-download ingestion, preservation of existing ready-file references and same-name replacement with edited labels. The user approved the proposed limit.
- [x] Confirm transient image intent can enable Save without a canonical metadata difference and survive the existing partial Save-completion failure until the user retries or discards.
- [x] Confirm the three Finder targets use the draft's exact source root and the existing path confinement and OS helper.
- [x] Summarize the bounded code change, select proportionate evidence and obtain implementation approval before promoting the delivery to active.

Verification budget: read-only source/configuration inspection and specification review. No prototype, generated output, media writes, Finder launches or executable tests are needed for readiness.

Gate: resolve any missing attachment ownership/transfer limit, contradictory replacement behavior or unavailable Finder integration before implementation. Stop if the change requires removing original-source metadata, migrating existing downloads or widening Docs Viewer/report/publication behavior.

Record: readiness complete and implementation approved. Studio owns the draft and native `File` references; the Catalogue mutation/completion owners separate canonical success from incomplete local media. The configured Docs asset owner resolves the Work-download destination independently of Projects originals. Existing conversion accepts a force flag, compares rendition bytes for version changes and retains versions for missing-rendition repair. The exact configured Work-media resolver rejects traversal and symlinks, and `docs_local_files.open_in_finder` distinguishes directory opening from file revelation. No owner or scope blocker was found.

Approved implementation decisions:

- Send native files as multipart data on the existing Work create/Save request, together with bounded JSON metadata. Retain the existing 1 MiB metadata limit and cap combined attachment bytes at 64 MiB per Save; bound multipart overhead separately. Reject over-limit selections before transfer and enforce the limits again at the service. Keep files in the browser draft until Save and use only operation-owned temporary handling, with no persistent upload stage or separate permanent writer.
- Derive the destination basename at the Catalogue write owner from the validated five-digit Work ID and original filename. Same-name replacement matches that resulting stored filename and preserves its edited label. Existing differently named legacy references remain unchanged; a new prefixed identity does not migrate or rename a legacy attachment.
- Keep pending files and confirmed image-regeneration intent outside the canonical Work record. Count them in dirty/Save state. On canonical success with incomplete media, adopt the returned saved record/revision and retain pending work, including when New Work becomes an existing Work. Clear pending work after successful local completion or deliberate draft discard. Metadata-only Save continues to skip conversion.
- Resolve folder, subfolder and filename actions from current draft source identity through the local Catalogue service, reuse the confined source resolver and shared OS helper, and preserve busy/bulk restrictions. No Finder launch is needed for implementation verification.
- Retire normal Save's staged-download ingestion and the superseded manual attachment-filename entry. Source inspection also found redundant Work request shapes (`record`, `work` and top-level fields) and picker-selection aliases; simplify the touched boundaries to their current callers' explicit shapes without adding compatibility aliases. Leave staged bytes and existing managed attachments for manual cleanup.

Selected evidence remains changed-source JavaScript/Python lint and syntax, whitespace checks and a distinct bounded code review. These checks address source errors and ownership/path/lifecycle defects; they do not prove file replacement, conversion or Finder behavior. Safari/Edge chooser review, deliberate real-media saves and Finder actions remain user manual acceptance. No test creation, changes, execution, browser automation, generated output, media writes or OS opening occurred during readiness. The inspected runtime owners are local Studio/service files and require no public projection unless implementation changes a represented shared/public asset.

### WEM 1 Attachment Selection And Save

- [x] Implement native Add file, draft-held contents, filename-based labels and same-name replacement with preserved labels.
- [x] Implement server-owned naming, bounded byte transfer, confined shared-asset writes and canonical-reference persistence within awaited Save.
- [x] Preserve existing attachment references, label editing and the current completion/error boundary; retire staged-download ingestion from normal Save.

Verification budget: focused lint/syntax checks for changed source and bounded source/diff review. User manual review in Safari, with an Edge compatibility check, covers chooser cancellation, label editing, a new attachment and a same-name replacement. Any automated write check or test work requires a separately agreed selection/specification; do not exercise real attachment replacement merely to close this step.

Gate: adding and replacing files must produce the agreed deterministic identity without duplicate entries, unintended writes on selection, unsafe paths or a premature Save success claim.

Record: implemented. Changed JavaScript/Python lint, Python syntax and whitespace checks passed. Source review confirmed one awaited create/Save transport, server-owned naming and the existing confined media-write owner. Native file bytes stay in the browser draft until Save; contents-only replacement retains the entry and label. New Work exposes the resource panel and follows edits to its Work ID. Safari/Edge chooser, cancellation, new upload and replacement remain unconfirmed manual acceptance; no real attachment was written or replaced during implementation.

### WEM 2 Explicit Image Regeneration And Finder Links

- [x] Record confirmed image-selection intent, include it in dirty/Save state and send it through the owning Save operation.
- [x] Force complete rendition conversion for that intent while preserving dimensions/version rules and metadata-only behavior.
- [x] Implement folder opening and file revelation from current draft values through exact source validation and shared Finder support.

Verification budget: focused changed-source lint/syntax and source/diff review. User manual review covers same-path confirmation after an original edit, cancellation, unchanged rendition versions, folder/subfolder opening, file revelation and a missing target. Finder launches and real image writes happen only through that deliberate manual review. No automated browser test or new regression script is included.

Gate: a confirmed same-path selection requests Save and actually converts on Save; cancellation remains clean. Finder targets must match the selected source, and filename activation must reveal the original rather than launch it. Stop for scope drift into automatic watching or report/source migration.

Record: implemented. Focused lint/syntax and source review passed. Confirmed selection carries transient regeneration intent through candidate selection and the converter's force flag; the existing byte-comparison/dimension/version owner remains authoritative. Saved canonical records/revisions are adopted before the optional editor lookup, with unsatisfied requests retained until local media succeeds or the draft is discarded. Finder targets use current draft source identity, exact confined components and the shared open/reveal helper. Real conversion, version outcomes and Finder behavior remain unconfirmed manual acceptance; neither conversion nor Finder was launched during implementation.

### WEM 3 Code Review

- [x] Review the bounded implementation and selected evidence for duplicate upload/naming owners, stale staged-file replacement, source-root drift, unsafe Finder targets, pending-intent lifecycle errors and compatibility residue.
- [x] Confirm Save completion, contents-only replacement, forced conversion and unchanged-byte version behavior agree across browser and service at source-review scope.
- [x] Resolve findings within scope and repeat only checks affected by the resulting changes.

Verification budget: final source/diff review and already selected evidence; no automatic test expansion or broad suite.

Gate: resolve material findings before closeout; report any evidence limit rather than treating lint as behavioral verification.

Record: bounded review complete. Resolved findings: New Work's containing panel initially hid the attachment actions; completion handling now clears fulfilled media intent even if a later response/Refresh-status step fails, while retaining actual unsatisfied requests; saved revisions are adopted before a lookup can fail. Changed-source lint and Python syntax passed after the corrections. Removed staged ingestion, manual Add download modal/copy, retired standalone Work file/link route declarations and touched Work/picker request aliases. No represented shared/public runtime file changed, so public projection and site validation are not applicable. Existing historical test code remains unchanged and unreviewed for these contracts; lint/source review does not establish browser, transfer, conversion or OS behavior.

### WEM 4 Closeout

- [ ] Record the user's manual acceptance and any remaining limitations.
- [x] Update Catalogue Save And Refresh with implemented attachment naming/replacement, explicit image-regeneration and Finder behavior, identifying pending manual acceptance.
- [x] Reconcile required local-only/public projection follow-through against the files actually changed; do not run unrelated Build, Search or Publish operations.
- [ ] Present the delivery's completion evidence and retain-or-retire recommendation. Transfer lasting behavior to the durable owner; deletion/archive requires its own approval.

Verification budget: bounded documentation/source review and whitespace checks. Reuse accepted implementation evidence unless closeout reveals a concrete gap.

Gate: close only when all three authoring changes work, the durable owner is current and omissions are explicit. Recommend retaining this delivery for recent-work lookup until manual archive.

Record: manual acceptance pending. The durable owner describes the implemented behavior and evidence limits. Restart local Studio and reload the editor before acceptance because the backend routes/request contract changed. Retain this delivery for acceptance and recent-work lookup; do not close or archive it before the user confirms the scoped manual outcomes.

## Follow-on

Native selection for Docs Viewer **Add image** and **Add file** remains a separate delivery through its document-media owner. It can reuse the browser input approach while retaining Docs Viewer's own naming, token, thumbnail, storage and Save boundaries; this Work-editor delivery does not authorize that implementation or a shared cross-app upload framework.
