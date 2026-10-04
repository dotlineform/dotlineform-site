---
draft: false
doc_id: d-20261004-213558-9ef277
title: Docs Native Media Picker Delivery
added_date: "2026-10-04 21:35:58"
last_updated: "2026-10-04 22:23:32"
summary: Native single-file selection for Docs Viewer Add image and Add file, retaining document-media naming, replacement confirmation, tokens, thumbnails, storage and Source Save ownership.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Docs Native Media Picker Delivery

## Current And Next State

Status: complete and accepted on 2026-10-04. The user approved closeout after the shared filename/icon implementation and toolbar hover-style/size refinements. Native Add image/Add file and existing-image selection, bounded Docs-owned upload, staged-path retirement and durable intake documentation are complete. Changed-source lint/syntax, service-import diagnostics, public code projection/check, site validation and bounded code review passed. Individual browser, upload, replacement, thumbnail, SVG/Mermaid and failure scenarios were not itemised in the acceptance, so no exhaustive manual coverage is claimed. Retain this delivery for recent-work lookup until manual archive. Codex ran no tests, browser automation, real media writes, document/Search builds, Publish, commit or push.

Complete result: an author editing an ordinary or named-collection document uses a filename field with an adjacent folder-open icon in the media modal. The icon opens the browser's native file chooser, and selection fills the filename field. The same image control serves new insertion and existing-token editing; confirmation uses Docs Viewer's own awaited media operation. Required media writes finish before insertion; Source **Save** persists the document separately.

This standalone delivery is parented to [Planned Features](../Planned_Features.md). [Media And Asset Handling](../Media_And_Asset_Handling.md) owns document-media intake, naming, storage and completion; [Semantic Tokens Architecture](../Semantic_Tokens_Architecture.md#docs-owned-images) owns image tokens. [Development Checklist](../Development_Checklist.md) and [Development Workflow](../Development_Workflow.md) govern implementation and closeout.

## Requirements

### Native Selection And Authoring

- **Add image** opens its authoring modal with an image filename field and an adjacent icon button using the existing [folder-open.svg](../../../docs-viewer/static/icons/folder-open.svg). **Add file** uses the same filename-field/icon pattern in its own modal. The icon button reuses the standard toolbar icon button style and size: no border and a grey circular background on hover. It is keyboard-accessible and has an accessible file-selection label; a separate file/folder list is unnecessary.
- Clicking the icon opens a standard single-file `<input type="file">` chooser. Selecting a file enters its original basename into the filename field and retains its bytes with the modal. Safari is the primary manual-review browser; Edge is also supported. Select from any folder accessible to that browser without first copying the file to import staging or browsing a server-owned folder list.
- Retain the other existing authored fields in the same modal. Add image retains required alt text, optional caption and summary, placement, fill-width choice and optional **Create thumb**. Add file retains its editable link label. Preserve the current label suggestions and field defaults rather than adopting Work attachment labels.
- Use the same filename field and icon when editing an existing image token, initially showing the basename from its current media identity. Presentation-only editing requires no file selection or upload. Clicking the icon and selecting a file updates the field and requests that selected file through the same media intake owner when the edit is confirmed. There is no separate replacement-selection button or replacement-selection modal.
- Choosing another file uses the same icon. Preserve deliberately edited authoring fields where applicable. Cancelling the chooser retains the current filename, selection and authored fields; cancelling the modal before materialisation leaves source and managed media unchanged. Selecting the same file again must remain possible.
- Keep one selected browser `File` with the current modal operation until confirmation or cancellation. Track actual file selection independently of the displayed filename so selecting new bytes with the same name still invokes media intake. Selection alone neither uploads nor writes permanent media. Explicit **Add image**, **Add file** or image-edit **Apply**, together with any required replacement/sanitization decision, authorizes the awaited media operation.
- Derive the chooser's extension filter from the existing capability allowlists. Retain server enforcement: a browser filter or supplied MIME type is not authority. Preserve current raster, SVG and persistent Mermaid `.mmd` image intake and opaque-download support without adding formats, directory selection, multiple selection or drag-and-drop.
- Preserve guarded image-occurrence editing when applying either presentation changes or a newly selected file. The filename field reflects the selected/current file; it does not introduce manual managed-file renaming or change the server-owned naming rules.

### Docs-Owned Transfer And Validation

Transfer the selected bytes and bounded authoring metadata through the Docs management client to the Docs Viewer media service using multipart upload. Reuse the browser input technique demonstrated by the Work editor without importing Catalogue upload, Save, naming or image-pipeline code and without creating a shared cross-app upload framework.

The Docs-owned limits are 64 MiB for one selected file, 1 MiB for metadata and 1 MiB for multipart overhead (66 MiB total request). They are explicit Docs policy rather than a dependency on Work upload code. Browser checks reject unsupported suffixes, empty files and over-limit selections/metadata before transfer; the service enforces basename, type, metadata, file and envelope bounds again. Preserve existing renderer/converter limits where applicable.

Validate the exact current document/collection capability, selected basename, media kind and authored fields at the service. Add image continues to validate the current complete source buffer. The browser supplies selected bytes and a basename, never a server source path, destination root, provider or shell command. Resolve the destination through existing workspace configuration and retain traversal/symlink confinement.

Use only operation-owned temporary handling needed for transfer, SVG sanitization or Mermaid rendering, with cleanup when the operation finishes. Do not require persistent upload staging, read a same-name staged file as a fallback, or introduce a second permanent-media writer. Native input provides no reliable original folder path: do not invent configured-root provenance, infer a Projects source association or persist browser placeholder paths. The retired intake had no active source-evidence writer to migrate.

### Naming, Replacement And Representation

- Retain the current image source-basename convention: normalize the original stem and supported extension to the existing lowercase websafe identity. `My Photo.JPG` becomes `my-photo.jpg`; document title, `doc_id` and Work ID do not prefix the display image, and no numbered suffix is allocated.
- Retain current Add file basename naming and safety normalization. A safe selected download basename remains its managed identity; its authored link label remains independent. This delivery introduces no Work ID prefix, attachment-record shape or migration of existing files/references.
- Resolve collisions within the exact ordinary/collection owner and media family. Reuse identical stored bytes; require the existing **Replace** or **Cancel** decision for changed bytes at the same identity. Preserve that confirmation for Docs media even though Work attachments intentionally replace without it. Shared-asset replacement affects every document referencing that identity; a distinct selected basename retains a separate asset.
- Return the existing canonical semantic image token for raster, sanitized SVG and persistent Mermaid SVG, with the authored image settings. Return the existing labelled logical download reference for Add file. The server/token owner determines these references; the browser does not author HTML, arbitrary classes, dimensions or physical media URLs.
- Preserve SVG sanitization and review when unsafe content is removed. Mermaid retains its normalized `.mmd` build-source identity and same-stem managed `.svg`, with rendering and required verification completed before reference insertion. Do not add a second sanitizer, converter or token grammar.

### Thumbnails, Storage And Save

**Create thumb** remains unchecked by default and available only for raster images. When selected, use the current Docs-owned 96×96px WebP recipe and immediately replace `<doc_id>-thumb.webp` under that document owner's registered `thumbs` family, without another thumbnail-replacement confirmation. Leave display-image bytes, dimensions and format unchanged; generate no primary variants or srcset. Unchecked insertion leaves the existing thumbnail alone.

Write through the configured shared ordinary or exact named-collection media owner: `img`, `svg`, `files` and `thumbs` retain their roles, and persistent Mermaid source retains its registered build-source owner. A collection report host does not own its documents' media. Missing configured storage reports failure without a replacement root, parent-owner fallback or public/R2 fallback. Native selection does not change media inventory, publication eligibility, local/public URL resolution or Catalogue media ownership.

Keep the existing media-before-source boundary. Complete and verify required media writes before inserting the returned reference and, when requested, `thumbnail: true` into the dirty source buffer. The Add operation does not save canonical Markdown. Source **Save** remains the validated combined metadata/body write, with committed-record reconciliation at that boundary; watcher document/Links generation and reader refresh remain independent. Search is not rebuilt by this workflow.

Keep the operation busy until its required work completes. On failure, identify any already completed media writes without claiming insertion or Save success. A thumbnail/rendering/write failure must not insert a reference for an incomplete operation. If insertion fails after successful media writes, report that distinction. Cancelling or abandoning the later Source edit leaves stored media, including thumbnail overwrites, in place for manual reconciliation. Add no rollback, automatic retry, backup copies, orphan deletion or persistent recovery marker.

### Scope

The delivery covers local Docs Source authoring, native selection, bounded upload and its existing document-media materialisation. Retire superseded source-editor file/folder listing, staged request fields, endpoints and picker code only after checking their active consumers; preserve global Docs Import, package/Review intake and any separately owned staging use. Do not retain a staged-selection fallback or compatibility alias for the replaced authoring flow.

Work editor changes, Finder actions, original-file path capture, automatic source watching, media migrations, new formats, new thumbnail/list behavior and a general upload framework are outside this result. Publish, deployment, Search rebuild, commit and push remain separate explicitly authorized actions.

## Deliverables

- [x] Filename field with the existing folder-open icon for native single-file Add image/Add file selection, cancellation and reselection, retaining the Docs authoring fields.
- [x] The same image filename/icon control when editing an existing occurrence, initialized from the current token and without upload for presentation-only edits or a separate replacement-selection button.
- [x] Docs-owned bounded transfer, validated naming and existing replacement/sanitization decisions through one media-write owner.
- [x] Preserved image/download references, raster thumbnail assignment, exact storage ownership and media-before-Source-Save completion.
- [x] Retirement of superseded source-editor staged/folder picker paths without affecting document/package Import or adding aliases.
- [x] Focused evidence, bounded code review, user manual acceptance and current durable intake/author instructions.

## Process

1. Open an authored document's Source editor and choose **Add image** or **Add file**, or reopen an existing image token. The modal shows the filename field and adjacent folder-open icon; an existing image starts with its current filename.
2. Click the icon and select one supported file in the native chooser. Selection fills the filename field; cancelling preserves its previous value and the current edit. Skip selection for a presentation-only image edit.
3. Review the filename and authoring fields. For a selected raster image, including a replacement, optionally select **Create thumb**. Confirm with **Add image**, **Add file** or image-edit **Apply**.
4. For a selected file, resolve an existing **Replace** or SVG sanitization decision when required and wait for the complete media operation; success inserts or updates the reference and any selected thumbnail assignment in the dirty buffer. Presentation-only **Apply** updates the guarded token occurrence directly without a media operation.
5. Review the source and use **Save** to persist it. Media already written remains stored if this later edit is discarded. Generated document refresh follows the existing watcher; public publication remains separate.

## Delivery Steps

### DNM 0 Readiness

- [x] Confirm the shared Source editor, management transport, document-media write, token/thumbnail and Save owners against the current product.
- [x] Confirm the common filename-field/icon control, existing-token initialization and actual file-selection state; resolve single-file and request limits, empty-file behavior, temporary byte handling and any affected source-evidence semantics.
- [x] Check active consumers of the superseded listing/staged/folder-selection paths; bound their retirement while preserving separately owned Import/package intake.
- [x] Summarize the intended code change and proportionate evidence, resolve stop conditions, and obtain implementation approval before promotion to active.

Verification budget: concise read-only source/configuration and specification review, expected minutes with no media writes, uploads, prototype, generated output or executable tests.

Gate: agree transfer limits and coherent cancellation/replacement/failure behavior before implementation. Stop if the result requires changing Source Save timing, migrating existing assets, expanding accepted formats or introducing a cross-app upload owner.

Record: complete; the user approved proceeding on 2026-10-04. Current Source action/adapter/provider and Docs management service owners were confirmed. Configured-folder branches had no matching server support and were removed with the staged source-editor intake. Native input supplies no original path; there was no active source-evidence writer in this intake to preserve or migrate. Implementation uses a 64 MiB single-file cap, existing 1 MiB JSON metadata cap and separately bounded 1 MiB multipart overhead, with empty-file rejection and operation-owned temporary handling. Global Import/package staging, media naming and canonical Source Save are retained.

### DNM 1 Native Selection And Editor Integration

- [x] Replace Add image/Add file staged selection with the filename field and adjacent folder-open icon; populate the field from native single-file selection within the existing authoring modal.
- [x] Reuse that image control for existing-token editing, preserving its current filename, presentation-only editing, cancellation, same-file reselection and guarded occurrence capture.
- [x] Remove the separate replacement-selection button, superseded picker UI and source-editor listing calls within the confirmed consumer boundary.

Verification budget: changed-source JavaScript lint and bounded source/diff review, expected minutes without managed media writes. User manual review in Safari and Edge covers icon/keyboard chooser activation, filename population, existing-token initialization, cancellation, field preservation and same-file reselection. No browser automation or test work is included automatically.

Gate: selection alone causes no source or permanent-media write; existing image presentation remains editable without a chooser. Do not count this step as the complete delivery until the transfer/write step is integrated.

Record: complete and accepted. One read-only filename display and keyboard-accessible icon use the native input inside Add image, Add file and Edit image. The chooser button reuses `docsViewer__toolbarIconButton` for the requested borderless appearance and grey circular hover background. A local CSS binding gives it the existing toolbar control-height token because the modal does not inherit the toolbar row's size setting. Actual `File` state is independent of basename changes; chooser cancellation retains the previous selection. Presentation-only Apply edits the captured token directly. Raster selection enables the optional thumbnail in either insertion or replacement. Explicit JavaScript lint passed for all seven changed canonical JS files; focused lint/whitespace checks passed after the button-style correction, and scoped source/whitespace review covers the size binding. The user accepted the overall delivery after style/size refinements; individual browser and interaction scenarios were not itemised.

### DNM 2 Transfer And Document-Media Completion

- [x] Implement accepted byte/request limits and Docs-owned transfer into the existing validation, naming, sanitization/rendering and confined materialisation owners.
- [x] Preserve replacement confirmation, semantic/download reference construction, optional thumbnail behavior and failure reporting before source insertion.
- [x] Preserve canonical Source Save and watcher ownership; retire superseded staged contracts and any exposed compatibility residue within scope.
- [x] If represented shared/public runtime changes, run `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`. Keep local-only upload code excluded by the projection inventory.

Verification budget: explicit changed-source JavaScript/Python lint, relevant Python syntax and scoped whitespace/diff checks, expected minutes with no real media writes. Required static projection/validation applies only when its represented boundary changes. User manual review covers ordinary and named-collection insertion, a same-name reuse/replacement, SVG/Mermaid handling, requested thumbnail creation and later Source Save/discard. State failure-evidence gaps explicitly; any automated upload/write check or test creation/change/run needs a separately agreed selection/specification under [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md).

Gate: native bytes reach the exact configured owner without staging fallback; required writes finish before insertion, while canonical source remains unsaved until Save. Failed/cancelled operations report their actual effects. Public readers retain their read-only boundary.

Record: complete and accepted with the overall delivery. `/docs/source/media/options` supplies accepted suffixes and browser-checkable limits; bounded multipart `/docs/source/media` carries metadata and one file through the existing management/origin boundary. New/reused media completes in one request; replacement or sanitizer review returns a write-free decision and uses explicit resubmission of the same File. The staged service/routes were retired without aliases; native intake uses existing naming, storage, token, Mermaid and thumbnail owners. Python lint and syntax passed for six changed/new production files, and direct imports of the management and HTTP services passed. `bin/site-code-update` changed only the tracked shared workspace provider; its exact delta was reviewed, projection check and site validation passed. Codex ran no upload/media write or browser check; individual transfer, conversion and failure scenarios were not itemised in user acceptance.

### DNM 3 Code Review

- [x] Review the final bounded implementation for duplicate upload/write owners, unsafe paths or byte limits, stale staged/folder branches, token/thumbnail drift and incorrect completion/failure claims.
- [x] Review cancellation/reselection, shared-asset replacement, image presentation editing and ordinary/collection isolation against the agreed result.
- [x] Resolve findings within scope and rerun only affected evidence; record omitted manual/failure scenarios.

Verification budget: bounded final source/diff review, expected minutes without runtime/media effects. Passing lint does not replace this review; no broad audit or test suite is a gate.

Gate: resolve material findings before closeout and ensure evidence supports the claimed scope.

Record: bounded code review complete. Fixed the remaining directive caller after renaming the media API, used the existing toolbar icon styling, corrected filename/raster suffix handling, retained thumbnail selection for replacement and enforced multipart overhead independently. Mermaid partial-write failures identify completed source/SVG effects. Follow-up changed-source lint/syntax and import diagnostics passed; whitespace checks cover the final source/documentation delta. No obsolete runtime caller or staged-route alias remains. Existing staging/scope tests are unreviewed for native intake and remain unchanged; their affected selection is recorded under the durable media owner's weak spots. Browser interaction, multipart transfer, actual writes and failure scenarios remain explicit evidence gaps.

### DNM 4 Closeout

- [x] Record user manual acceptance and the exact completed evidence, remaining risks and omissions.
- [x] Update [Media And Asset Handling](../Media_And_Asset_Handling.md) for native intake/transport ownership and the Add workflow in [Docs Images And Assets](../Docs_Images_And_Assets.md), replacing the superseded staging instructions within this boundary.
- [x] Mark complete only when both native actions and image replacement work through the retained completion owners.
- [x] Recommend retaining or manually archiving this delivery and its Planned Features link; do not delete planning documents without approval.

Verification budget: documentation/source review and reuse of accepted implementation evidence. Repository Studio documentation is edited directly and requires no watcher, Docs/Search rebuild or Publish. Do not repeat checks without a newly identified risk.

Gate: the complete result and durable author instructions agree. Public publication and Git actions remain separate.

Record: closed on the user's explicit acceptance on 2026-10-04. Durable intake architecture, author instructions and the diagram intake pointer are current. Closeout changed documentation only, used bounded source review and reused the accepted implementation evidence; no new executable check or runtime operation was needed. Retain this delivery and its Planned Features link for recent-work lookup until manual archive. No documents were deleted. Tests, generated document/Search output, Publish, deployment, commit and push did not run.

## Follow-on

The retired staging/scope test selections identified in [Media And Asset Handling](../Media_And_Asset_Handling.md#weak-spots) need separately specified test retargeting or retirement if that work is requested. Broader native document/package Import, original-source path tracking, batching, format expansion or a shared upload framework also require their own requirements and authorization.
