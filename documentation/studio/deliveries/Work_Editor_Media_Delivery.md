---
draft: false
doc_id: d-20261004-183033-8521af
title: Work Editor Media Delivery
added_date: "2026-10-04 18:30:33"
last_updated: "2026-10-04 18:40:19"
summary: Native Work attachment selection with automatic Work ID naming, explicit image regeneration on confirmed selection, and Finder links for original source locations.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Work Editor Media Delivery

## Current And Next State

Status: proposed. The user requested this delivery document on 2026-10-04; requirements are captured, but code implementation and test work are not authorized by this documentation request. Next: complete the concise readiness gate, summarize the intended code change and obtain implementation approval.

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

- [ ] Native single-file Work attachment selection with filename-based initial labels and existing label editing.
- [ ] Catalogue-owned file transfer and automatic Work ID prefixing into the configured shared attachment destination.
- [ ] Intentional same-name replacement without duplicate references, including Save activation for contents-only changes.
- [ ] Explicit image-regeneration intent from confirmed custom-picker selection through complete Work Save conversion.
- [ ] Finder links for the three displayed source values, using configured source identities and shared OS-opening support.
- [x] Removal of the temporary native chooser demo after manual review.
- [ ] Retirement of code made unused by the production attachment flow, without compatibility aliases.
- [ ] Focused verification, bounded code review, user manual acceptance and updated durable Save/authoring documentation.

## Process

1. Open an existing Work and choose **Add file**. Select a file from any accessible folder; the draft gains its filename-based label. Use **Edit** if a different label is needed, then Save to store the automatically prefixed file and reference.
2. To replace that attachment, choose **Add file** and select a file with the same original filename. Its existing entry and edited label remain; Save writes the replacement contents.
3. To regenerate Work images after editing an original, open **Choose image**, select the original again and click **OK**. The editor requests Save even when all source values are unchanged. Save regenerates the configured renditions from the current original.
4. Click the project folder or subfolder value to open that directory in Finder, or the filename value to reveal the original. These actions are independent of saving.
5. Use the existing explicit Refresh Catalogue operation when current generated reader metadata is needed. Publish and public release retain their separately authorized workflows.

## Delivery Steps

### WEM 0 Readiness

- [ ] Confirm the broad Work-draft, Catalogue Save/media-write, source-resolution and Finder owners against the current product.
- [ ] Confirm upload transport/size limits and how attachment bytes join Save without a persistent staging dependency or a second writer. Confirm retirement of normal Save's staged-download ingestion, preservation of existing ready-file references and same-name replacement with edited labels.
- [ ] Confirm transient image intent can enable Save without a canonical metadata difference and survive the existing partial Save-completion failure until the user retries or discards.
- [ ] Confirm the three Finder targets use the draft's exact source root and the existing path confinement and OS helper.
- [ ] Summarize the bounded code change, select proportionate evidence and obtain implementation approval before promoting the delivery to active.

Verification budget: read-only source/configuration inspection and specification review. No prototype, generated output, media writes, Finder launches or executable tests are needed for readiness.

Gate: resolve any missing attachment ownership/transfer limit, contradictory replacement behavior or unavailable Finder integration before implementation. Stop if the change requires removing original-source metadata, migrating existing downloads or widening Docs Viewer/report/publication behavior.

Record: proposed. Initial source inspection confirmed manually supplied `{filename, label}` downloads, staged-file completion, image selection based on changed source fields, displayed source values and a shared validated-target Finder helper. Complete readiness and implementation approval remain outstanding.

### WEM 1 Attachment Selection And Save

- [ ] Implement native Add file, draft-held contents, filename-based labels and same-name replacement with preserved labels.
- [ ] Implement server-owned naming, bounded byte transfer, confined shared-asset writes and canonical-reference persistence within awaited Save.
- [ ] Preserve existing attachment references, label editing and the current completion/error boundary; retire staged-download ingestion from normal Save.

Verification budget: focused lint/syntax checks for changed source and bounded source/diff review. User manual review in Safari, with an Edge compatibility check, covers chooser cancellation, label editing, a new attachment and a same-name replacement. Any automated write check or test work requires a separately agreed selection/specification; do not exercise real attachment replacement merely to close this step.

Gate: adding and replacing files must produce the agreed deterministic identity without duplicate entries, unintended writes on selection, unsafe paths or a premature Save success claim.

Record: not started.

### WEM 2 Explicit Image Regeneration And Finder Links

- [ ] Record confirmed image-selection intent, include it in dirty/Save state and send it through the owning Save operation.
- [ ] Force complete rendition conversion for that intent while preserving dimensions/version rules and metadata-only behavior.
- [ ] Implement folder opening and file revelation from current draft values through exact source validation and shared Finder support.

Verification budget: focused changed-source lint/syntax and source/diff review. User manual review covers same-path confirmation after an original edit, cancellation, unchanged rendition versions, folder/subfolder opening, file revelation and a missing target. Finder launches and real image writes happen only through that deliberate manual review. No automated browser test or new regression script is included.

Gate: a confirmed same-path selection requests Save and actually converts on Save; cancellation remains clean. Finder targets must match the selected source, and filename activation must reveal the original rather than launch it. Stop for scope drift into automatic watching or report/source migration.

Record: not started.

### WEM 3 Code Review

- [ ] Review the bounded implementation and selected evidence for duplicate upload/naming owners, stale staged-file replacement, source-root drift, unsafe Finder targets, pending-intent lifecycle errors and compatibility residue.
- [ ] Confirm Save completion, contents-only replacement, forced conversion and unchanged-byte version behavior agree across browser and service.
- [ ] Resolve findings within scope and repeat only checks affected by the resulting changes.

Verification budget: final source/diff review and already selected evidence; no automatic test expansion or broad suite.

Gate: resolve material findings before closeout; report any evidence limit rather than treating lint as behavioral verification.

Record: not started.

### WEM 4 Closeout

- [ ] Record the user's manual acceptance and any remaining limitations.
- [ ] Update Catalogue Save And Refresh with shipped attachment naming/replacement, explicit image-regeneration and Finder behavior.
- [ ] Reconcile required local-only/public projection follow-through against the files actually changed; do not run unrelated Build, Search or Publish operations.
- [ ] Present the delivery's completion evidence and retain-or-retire recommendation. Transfer lasting behavior to the durable owner; deletion/archive requires its own approval.

Verification budget: bounded documentation/source review and whitespace checks. Reuse accepted implementation evidence unless closeout reveals a concrete gap.

Gate: close only when all three authoring changes work, the durable owner is current and omissions are explicit. Recommend retaining this delivery for recent-work lookup until manual archive.

Record: not started.

## Follow-on

Native selection for Docs Viewer **Add image** and **Add file** remains a separate delivery through its document-media owner. It can reuse the browser input approach while retaining Docs Viewer's own naming, token, thumbnail, storage and Save boundaries; this Work-editor delivery does not authorize that implementation or a shared cross-app upload framework.
