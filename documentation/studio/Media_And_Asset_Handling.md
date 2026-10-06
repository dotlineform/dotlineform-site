---
draft: false
doc_id: d-20260514-184303-7914e2
title: Media And Asset Handling
added_date: "2026-05-14 18:43:03"
last_updated: "2026-10-06 12:35:24"
summary: Media intake, content interpretation, document representation, storage, link resolution, extension methods, and safety boundaries.
parent_id: d-20260424-000000-50b63f

---
# Docs Viewer Media And Asset Handling

Media support is not one capability. A useful description must answer five separate questions:

1. Can the workflow accept these source bytes?
2. Does it interpret the contents or treat the file as an opaque download?
3. What document source or link does it create?
4. Where are the bytes stored?
5. How does the rendered viewer reach them?

[Docs Images And Assets](Docs_Images_And_Assets.md) answers author and operator questions. This document owns the architecture, configuration, extension method, and weak spots.

## Capability Map

| intake | content interpretation | document representation | asset handling |
| --- | --- | --- | --- |
| Standalone raster image | Static-image validation and proportional display conversion; optional thumbnail derivation. | **Add image…** inserts a semantic image token with alt, optional caption/summary and explicit layout fields into the dirty source buffer, and records an explicitly requested thumbnail assignment. | One 800px-long-edge WebP is managed through `img`; the optional 96px WebP is managed through `thumbs`. |
| Ordinary PDF, ZIP, CSV, TSV, JSON, JSONL, or supported Office file | None; the file is opaque. | **Add file…** inserts a labelled link into the active source buffer. | Ready bytes are managed through `files`. |
| Trusted Data Sharing documents JSON/JSONL | Package metadata and document schema are interpreted. | Complete collection plan producing canonical documents. | Embedded raster data URLs can become media; other declared assets need an explicit mapping. |
| HTML, Markdown, or text | Converted or normalized into Markdown content. | New canonical document. | Markdown-image data URLs become `img`; HTML-inline SVG becomes sanitized `svg`. |
| Markdown package folder | Markdown plus supported local links are interpreted. | One canonical document with rewritten links. | Images become WebP; attachments are copied unchanged. |
| Standalone SVG | SVG markup is sanitized as a self-contained image. | **Add image…** inserts an image reference into the active source buffer. | Sanitized bytes are managed through `svg`. |
| Persistent Mermaid `.mmd` | Source is rendered by the registered, pinned Mermaid producer and then sanitized. | **Add image…** inserts a same-basename SVG reference into the active source buffer. | Canonical `.mmd` is copied to external build source; verified output is managed through `svg`. |
| Role-marked HTML companion | Treated as a companion application asset. | No automatic document placement; the author adds an `html-media` token. | Written to the exact document/collection owner's shared `html` location. |

Inline fenced Mermaid is deliberately not a media capability. Its source remains inside canonical Markdown, and the managed reader renders it in memory in the local workspace; external-local storage does not change eligibility. Inline rendering creates no `.mmd` media item, stored SVG, media token, filename, or inventory record. Public projection instead prepares validated light and dark SVG pairs, replaces the fence only in the public payload copy, and ships neither Mermaid source nor the managed Mermaid runtime. [Document Diagrams](Document_Diagrams.md) owns the complete authoring, build, managed-reader, and public-projection boundary.

The exact document and media suffix allowlists remain in `docs_import_common.py`. “Supported format” should not be used alone: say whether a format is interpreted by global Docs Import, accepted by **Add image…**, accepted as an opaque **Add file…** download, or recognized as a trusted collection.

## Execution Paths

### Document Import And Source-Editor Media

```text
Docs Import configured source ---> Markdown / collection plan
                                             |
                                             v
                                     embedded-media plan
                                             |
                                             v
                                media write -> source write -> rebuild

Add image / Add file modal ------> filename field + folder-open icon
                                             |
                                             v
                                   native single-file selection
                                             |
                                             v
                                  confirmed bounded byte upload
                                             |
                                             v
                             replacement / sanitization decision if needed
                                             |
                                             v
                                  verified managed-media write
                                             |
                                             v
                             reference inserted into dirty source buffer
```

Managed-media materialisation happens before a document import source write or source-editor insertion, so neither workflow commits a new token for bytes it failed to place. Working writes ready media to its exact shared workspace/collection namespace; callers do not select a provider.

**Add image…** and **Add file…** use one filename field with an adjacent `folder-open.svg` icon in their authoring modal. The button uses the standard borderless toolbar icon style and toolbar size setting, including the grey circular hover background. Clicking the icon opens the browser's native single-file input and selection fills the read-only filename display. Existing image-token editing initializes the same field from its current media basename and uses the same icon; a presentation-only edit needs no file, upload or media write. A selected `File` is tracked independently of the displayed name, so selecting replacement bytes with the same filename still invokes intake. The image settings and optional raster thumbnail remain in the same modal. Cancelling the chooser preserves the previous selection and authored fields.

`docs_source_media_upload.py` owns a 64 MiB single-file limit, 1 MiB metadata limit and 1 MiB multipart overhead limit (66 MiB total envelope). Empty files and unsupported suffixes are rejected. `/docs/source/media/options` exposes only accepted suffixes and browser-checkable byte limits; `/docs/source/media` accepts exactly metadata JSON and one native file through the existing local management/origin boundary. Global JSON request limits remain unchanged. Server validation owns the actual basename, format, exact document/collection capability and destination; browser filters and MIME declarations grant no write authority.

Native bytes use operation-owned temporary storage, with no persistent upload stage or dependency on Projects/import-staging availability. Normal insertion completes in one request. Changed target bytes or SVG sanitizer warnings return a write-free decision; after confirmation the browser resubmits the same selected file. Original files remain untouched. The browser supplies no original folder path, and this workflow records no configured-root or Projects provenance. The retired staged listing/preview/apply routes, folder-selection branches and their request fields have no aliases; separately owned Docs Import/package staging remains available.

### Authored Links

Ordinary logical tokens use `[[media:docs/<type>/<file>]]`; collection tokens use `[[media:docs/collections/<id>/<type>/<file>]]`. The builder resolves these to configured shared `/docs/assets/media/workspace/` or `/docs/assets/media/collections/<id>/` paths locally. Public projection maps the same identity to its configured public URL. Stage selects document/Catalogue JSON, not a second media copy.

Authoring a link does not copy, publish, validate, index or establish ownership of the target asset.

## Source Classification

Document suffix classification is code-owned by `SOURCE_FORMAT_BY_SUFFIX` in `docs_import_common.py`. It contains HTML, Markdown, and text only. Direct-child Markdown packages and trusted collections are classified separately.

JSON and JSONL appear in global Docs Import only when `docs_import_document_package.py` recognizes a trusted supported document package. An ordinary JSON/JSONL download is available through **Add file…**, not as a generic Docs Import fallback.

Markdown package folders and interactive HTML companions are also classified outside the ordinary suffix registry. [Docs Import Architecture](Docs_Import_Architecture.md) owns the complete source-dispatch and document-planning boundary.

## Workspace Configuration And Storage

`docs-viewer/config/workspace/docs-workspace.json` uses `docs_workspace_v4`. Working registers document media types and code-owned build producers once; Preview derives that configuration. Each media type has one shared `asset_location`, with `asset_root` supplying confined relative identities. [Configuration And Extension Points](Configuration_And_Extension_Points.md) owns the full workspace contract.

Current managed types are `img`, `thumbs`, `svg`, `files` and `html`; `mermaid` is an editable build-source type. Ordinary ready bytes live in `assets/media/workspace/<type>/`; collection bytes live in `assets/media/collections/<id>/<type>/`. The `thumbs` type is document-owned derivative media, with configured local and public projections; it is not an input chooser or editable build-source format. Editable build inputs and private source evidence remain under Working source. There are no ready-media copies under Working source/generated or Preview.

Catalogue uses the same shared asset root with separately owned `works/primary/`, `works/thumbs/` and `works/media/files/` families. Studio owns their local preparation; Projects-owned originals remain separate. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns dimensions/version completion.

| Provider | Current use | Policy |
| --- | --- | --- |
| External local | Shared ready media, Working build inputs and private source evidence. | Exact configured family, collection and type; no fallback root. |
| Repository | Configured public assets, including Catalogue thumbnails. | Public projection only; never private authoring authority. |
| R2 | Configured public document media and Work primaries/downloads. | Transfer referenced local bytes at Publish; credentials remain server-side. |

Config parsing is read-only. Owning lifecycle operations create required directories within the existing configured workspace. `docs_media_inventory.py` inventories registered document asset/build-source roles, not arbitrary Projects roots or Catalogue media.

## Docs Media Inventory Report

The local [Docs Media](/docs/?doc=d-20260812-212735-6d9cf3) report opens saved metadata and scans only when Run/Refresh is selected. It covers the ordinary workspace and every configured Working collection, using each owner's configured ready-media and registered build-source locations. The generator skips all `thumbs/` families and thumbnail references; shared thumbnail authoring, reference extraction and publication retain their own behavior. `.gitkeep` placeholders are omitted by inventory, while the browser omits exact `.DS_Store` basenames, including nested files. No stored media is deleted.

`docs_media_metadata.py` owns the saved read and explicit refresh. Workspace configuration's `media_report_metadata` selects `working/generated/reports/docs-media/metadata.json` beneath the existing external root. `GET /docs/media-metadata` accepts no parameters and returns `{ok: true, metadata: ...}`; a missing file returns `metadata: null` and displays an empty table, with no first-run prompt or invented refresh time. Run/Refresh remains available. Invalid, unsupported or unreadable metadata reports an error. Opening the report never scans, creates storage or regenerates missing data.

An empty-object `POST /docs/media-refresh` inventories each configured owner and reads only that owner's document collection once. It reuses `list_collection_media()` and `source_media_references()`, retaining referencing documents with exact source identities, including references to absent files. After all owners succeed, it validates and writes one `docs_media_metadata_v1` artifact containing `refreshed_at` and per-owner `collection`, `title`, `files` and `documents`. Ordinary docs use an empty collection identity and the label Ordinary docs. Files retain `{collection, role, media_type, identity}`; each document retains `{target: {collection, doc_id}, title, references}`. Exact document targets are sufficient for direct reader links; report-host IDs remain in their owning workspace configuration. The service returns the newly saved data directly, without a second source scan or metadata read. The artifact contains no rendered rows, presentation URLs, filesystem paths, credentials or publishing-stage fields.

The browser joins each owner's datasets independently in `docs-media-data.js`, derives exact document links through the viewer route helper and owns deduplication, ordering and presentation. The sortable columns are Collection, Type, File name and Documents. The collection filter initially selects All and uses saved configured owner titles; search includes those titles, filenames and document titles. Search, filtering and sorting use loaded rows only. Present unreferenced files retain a blank Documents cell, while absent referenced files produce no row and remain Broken Links' territory. Build sources do not inherit references from same-basename outputs.

The header displays `Last refreshed: DD/MM/YYYY, HH:mm` in the browser's local time, then a blank line and `<orphans>/<total> orphaned files.`. Both counts use all displayable files in the selected collection, or every owner when All is selected; an orphan has no associated document in the saved snapshot. Search and sorting do not change these counts. Missing metadata displays `0/0 orphaned files.` without a refresh timestamp. Run/Refresh remains busy through generation, persistence and row assembly. A failed owner scan identifies that owner and leaves the previous saved file untouched; the browser retains an already loaded snapshot with its original timestamp and reports failure. A write/response failure also reports failure; there are no partial per-owner writes, retries, backups or rollback. A write failure may leave unreadable metadata, recovered by a later explicit Run/Refresh. A valid empty snapshot is a successful empty report.

This is deliberately saved inspection data: source saves, media operations, document deletion, watcher passes, document/Search builds and Publish do not refresh it. Loaded rows receive no live label/deletion reconciliation. Working Build completion excludes the configured report directory, and document writes preserve it. Preview capture, public distribution, Search and document/package exports do not consume the artifact. The former live media-file/reference routes are removed without aliases. [Reports](Reports.md) owns registration and presentation.

File-name activation posts the exact media target to `/docs/open-media-source`, owned by `docs_media_actions.py`. It resolves the configured local Docs media location through the confined artifact adapter and requires an existing file, so a saved target deleted since the scan reports an opening error. This is a Manage capability; public readers have no local file action. `docs_local_files.open_in_finder()` owns the shared OS execution, platform check and dry-run suppression; the Docs action and Projects `docs_local_links.py` retain separate identity/root validation and errors. The browser receives no filesystem path, and Docs media does not depend on the Projects base. The report adds no media registry, source-evidence join, public projection, missing-reference row or second storage root.

## Link Resolution And Delivery

The docs builder resolves `media` and `html-media` tokens in `docs_builder/rendering.py`. Working and Preview by-ID payloads keep Docs-owned media as `docs-media:<workspace-or-collection>/<type>/<identity>`; they contain no local served URL or R2 URL for that media. Each local/public browser configuration exposes one Docs media root, and the reader resolves images, SVGs, files and HTML media before mounting content. Static Export packages referenced media under its own paths; Review resolves inventoried package assets. Canonical Markdown keeps its existing logical token. Prepare Preview records selected asset identities, and Publish transfers their current bytes without changing by-ID media identities.

The builder does not contact R2 or prove that every referenced object exists. `docs_media_inventory.py` supplies provider-independent file listing and shared source-reference extraction; consumers own associations and missing-reference policy.

The preparation phase of Publish captures document/Catalogue JSON and records referenced shared asset identities without copying media. Assigned document thumbnails are explicit references even when absent from body HTML: Preview capture and distribution reference collection derive `<doc_id>-thumb.webp` from each prepared by-ID payload's `has_thumbnail` flag and exact ordinary/collection owner. Excluded documents contribute no thumbnail references. Preview retains references to current shared bytes, not historical renditions. Distribution receives the same completed snapshot and transfers only its referenced current assets; it does not reread source/generated output. Missing required local bytes block reconciliation without remote fallback. Destination comparisons are carried into apply, and completed transfers are verified. Transfers do not change media versions or automatically delete shared/remote assets. Failed distribution can leave completed repository/R2 effects and retains completed Preview; fix the cause and run a fresh Publish. Review the repository result through site-preview.

`docs_artifact_locations.py` owns provider resolution, confinement, authentication, I/O, byte verification, staging, and served-reference behavior. `docs_media_storage.py` applies that boundary to managed-media writes and local serving:

- Document R2 keys use `docs/analysis/media/workspace/<type>/<identity>` and `docs/analysis/media/collections/<collection>/<type>/<identity>`, matching the suffixes beneath the local `/docs/assets/media/` served root. The configured public root is `https://media.dotlineform.com/docs/analysis/media/`.
- Local paths resolve only from the configured shared asset family and exact collection/type identity.
- Local `/docs/assets/` routes validate the registered family and safe identity, then confine the resolved filesystem target. Retired stage-media routes are not aliases.
- Traversal and symlink escape are rejected; `files` responses remain attachments with `nosniff`.
- `html-media` uses its registered served path and the sandboxed iframe handler rather than the ordinary download route.

## Import Materialization

`docs_import_media.py` creates logical links and materializes embedded document-import media. `docs_source_media_service.py` owns native source-editor media validation, naming, decisions and materialisation; `docs_source_image_conversion.py` prepares native raster display images, while the existing storage, sanitizer, Mermaid and document-thumbnail owners perform the required writes.

- Inline raster data URLs are decoded to deterministic `<doc_id>-image-NN.<ext>` names.
- HTML-inline SVG is sanitized from its original fragment to deterministic `<doc_id>-image-NN.svg` names, preserving case-sensitive SVG names and safe stylesheet text rather than reusing HTML-parser serialization.
- Markdown package images are converted to WebP, limited to 800px width without upscaling, and rejected if animation would be flattened.
- Package attachments retain their bytes and receive readable `<doc_id>-attachment-NN.<ext>` names.
- A replacement `doc_id` retargets generated filenames and source links before write.

Native source-editor raster additions and selected-file replacements produce one static WebP with an exactly 800px long edge, scaling up or down proportionally without cropping. `docs_source_image_conversion.py` uses the pinned Pillow decoder to validate JPEG, PNG, static WebP and single-frame GIF contents, rejecting animated inputs before permanent writes. FFmpeg performs Lanczos scaling and uses `libwebp`, `photo`, quality 82, compression level 6 and stripped metadata. These initial encoding settings match Works primary images but are explicitly Docs-owned; native sizing does not use Works' width-based/no-upscale rule or import Studio pipeline code/configuration. Conversion happens in operation-owned temporary storage before collision comparison. No srcset or additional display variants are generated. Small-input upscaling standardizes dimensions without recovering detail; large or text-heavy images may need author review at 800px. Missing dependencies, invalid images and conversion failures stop the operation without storing display media or a thumbnail.

The selected file remains untouched, and Add file retains opaque bytes. Standalone SVG is sanitized first. Mermaid source is rendered and sanitized in temporary storage before either canonical build source or managed SVG is written. Add image validates the exact document target and current complete source buffer at the service boundary, then names raster output using the selected lowercase websafe stem plus `.webp`; `My Photo.JPG` becomes `my-photo.webp`. SVG retains its normalized `.svg` name; Mermaid retains the normalized stem for its `.mmd` source and rendered `.svg`. Document title and `doc_id` do not contribute to the display-image name, and naming never allocates numbered suffixes. Existing filenames and references remain in place; selecting a replacement applies the new raster rule and updates that token, without migrating or deleting the previous asset. Presentation-only token edits do not upload or convert media. Add file retains its selected-basename naming and collision confirmation. SVG sanitizer removals can still require review. Source subfolders do not become managed subfolders; the existing flat per-type media identity remains authoritative.

Reimporting an image with the same normalized filename addresses the same asset in the exact configured owner and media family. Raster comparison uses converted WebP bytes, including when the selected input is already WebP. Matching stored bytes are reused without rewriting that artifact; changed bytes require the existing **Replace** confirmation before the awaited write. Mermaid compares and writes its canonical source and rendered SVG independently. Media is shared within its owner, so replacing an asset changes it for every document that references that identity. Different original source names can normalize to the same filename and receive the same collision treatment; `Photo.jpg` and `Photo.png` both address `photo.webp`. Choosing a distinct source basename is the author's way to retain both images. Thumbnail replacement remains the separately selected operation below.

For raster, sanitized SVG and persistent Mermaid SVG images, the server returns one canonical `[[image:<logical-path>|...]]` token through the same preview/apply owner. The token contains required authored alt and explicit placement/fill-width choices, with optional caption and summary. Unchecked **Add caption** omits the caption while preserving independent summary and layout choices. Build creates escaped static figure/image markup; the portable stylesheet owns full-column, equal-column split and natural-width presentation. Public-composition rules own the narrow-screen image-first fallback; local readers retain the desktop presentation. The browser submits no HTML, classes or dimensions. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md#docs-owned-images) owns the grammar, guarded reopening/editing and consumer boundaries. Existing Markdown/HTML image source remains supported without migration.

Collection records reuse the same inline-raster and per-document apply paths. A declared package asset without an authorized mapping remains a warning and preserves its source reference; a document overwrite decision does not grant asset overwrite authority.

### Assigned Document Thumbnails

The shared Add image dialog offers **Create thumb**, unchecked by default and available for raster images. Checked insertion invokes `docs_document_images.py` within the awaited media operation, using the original static upload rather than the converted display WebP. Docs Viewer invokes FFmpeg directly for one 96×96px WebP: proportional square-cover Lanczos scaling, including small-input upscaling, centred crop, `libwebp`, `photo`, quality 62, compression level 6 and stripped metadata. Native animation rejection happens before either display or thumbnail storage. Studio's image pipeline remains independently owned.

The thumbnail is stored as `<doc_id>-thumb.webp` in the exact document owner's registered `thumbs` family. Each checked operation immediately replaces that fixed identity without inspecting an existing choice or requesting replacement confirmation. Unchecked insertion leaves any existing thumbnail alone. Media writes complete before insertion into the dirty source buffer; the browser inserts the image reference and optional `thumbnail: true` front-matter assignment together. Save persists canonical source and publishes committed metadata to the retained caller; the watcher independently refreshes generated output. A thumbnail failure after the display write reports the stored image and the failed operation without claiming source insertion or undoing writes.

Canonical assignment is optional boolean `thumbnail`: `true` assigns the fixed document thumbnail; `false` or omission clears its presentation without deleting its stored file. Catalogue source rejects this field because generated Work thumbnails retain their separate owner. Builders project `has_thumbnail: true` only for assigned authored documents, into by-ID metadata and named-collection manifests; committed summaries carry the boolean so Source edits can clear an assignment immediately. Lists derive URLs through the configured media root and exact collection owner, without reading bodies or probing files. Generic collection rows, including Concepts and Moments, share Catalogue's decorative lazy-loaded, asynchronously decoded 64×64px contain box, 6px corners and existing spacing within the title navigation control. When the full collection manifest contains any assigned thumbnail, rows without one reserve an empty decorative 64×64px slot so titles and minimum row heights align across filtering and paging; no image element or media request is created for that slot. Collections without assigned thumbnails retain compact text rows. Missing images hide the artwork while preserving the slot and navigation. Ordinary Index, Search and Recent gain no thumbnail presentation.

Context selects the authored document thumbnail first. With no authored assignment, a scalar Work `subject` selects the existing Catalogue thumbnail through its configured policy and local/public base; current policy resolves Work `00635` to `00635-thumb-96.webp`. Folder and unassigned rows make no Work-thumbnail request. Any authored or Work-derived thumbnail in the full Context manifest enables the same empty-slot alignment across filtering and paging. Selection follows metadata: a failed selected image remains hidden in its slot without requesting an alternative. Subject and Source assignment commits reevaluate the retained row in memory, so clearing an authored assignment reveals the Work alternative and changing a Subject preserves an authored assignment. [Subject Associations](data/subject-associations.md#generation-and-publication-rules) owns mutually exclusive public-row fields. Catalogue continues producing/distributing Work renditions through its inventory; assigned document thumbnails remain captured from by-ID metadata, including documents with both assignments. Neither owner generates or copies thumbnails merely to render Context.

Shared source-reference extraction includes assigned thumbnails under the exact source document owner; Docs Media excludes those derived references and files from its saved report. Static document Export continues to package media referenced by its rendered body; it adds no hidden thumbnail images or collection-list presentation. Existing content/tree package profiles do not introduce thumbnail selection, and returned content preserves unrelated current source metadata. Registered media role handling remains configuration-driven.

Cancelling source edits, removing body-image tokens or deleting documents retains all stored display images and thumbnails. Removing a body image does not clear the canonical assignment. Display-media inspection and reconciliation remain manual through Docs Media; derived-thumbnail reconciliation is outside the report. Neither authoring nor Publish deletes orphan bytes. Existing Moments references were mechanically migrated to the title/ID convention with thumbnails derived from each first source image, preserving display bytes, document identities, titles, dates and authored layout. Original filenames and historical variants remain available for manual reconciliation.

## Extension Methods

### Accept Another Opaque Download Type

Extend the **Add file…** server allowlist only after deciding that storing and linking uninspected bytes is safe. Add listing, preview, content-type, publication, and route/download tests. Do not add the format to global Docs Import or describe it as content import.

### Interpret A New Content Format

Add a focused parser or trusted wrapper adapter and normalize its output through Docs Import. Do not overload the opaque **Add file…** path or infer structured behavior from an extension alone.

### Add A Media Type

Extend the type allowlist, reference/location mapping, import representation, rendering/serving behavior, and tests together. A type is a delivery contract, not just another folder name.

### Add A Build-Source Type

Register a code-owned producer under `media.build_sources`, name the managed target type, and register that input on `media.types.<type>`. Full and targeted builder behavior, staged intake if applicable, watcher invalidation, materialisation verification, and reader-runtime exclusion need focused tests together. Build source is not itself a served media type.

### Add Or Change A Public Projection

Register the repository or R2 target and served prefix for every public media type. Reconcile public copies explicitly; never change the external managed location or teach ordinary Add to write public bytes. Format converters continue to emit logical media intent without choosing physical storage.

### Add A New Reference Form

The docs builder owns source-token resolution; the local/public delivery layer owns the resulting URL. Do not hide a new token inside import-only code.

### Add Or Change Source-Editor Figure Presentation

Keep semantic request values in the existing **Add image…** modal, validate/serialize them in `docs_image_tokens.py`, and route preview/apply through the same media owner. Static figure rendering and escaping belong to `docs_builder/semantic_tokens.py`. Add an allowlisted field and fixed builder-owned class only for a concrete presentation contract. Specify any test changes separately under the test policy. Do not accept HTML, arbitrary classes, widths or styles from the browser, or add a general template/fragment registry for one figure format.

## Why This Structure Exists

- Source classification decides meaning before media storage is involved.
- One external managed-media contract keeps intake independent of public repository/R2 projection policy.
- Logical tokens keep the backing provider out of canonical Markdown.
- Confined local routes avoid exposing absolute roots or arbitrary filesystem reads.
- Media-before-source ordering prevents newly generated links from committing ahead of required managed bytes.
- Typed HTML handling and SVG image sanitization keep executable or markup behavior explicit without turning each format into a storage class.

## Weak Spots

- JSON/JSONL has dual availability: trusted packages are interpreted by Docs Import, while ordinary files are opaque **Add file…** downloads. Picker labels and documentation must preserve that distinction.
- The generic download allowlist proves only suffix acceptance, not content validity, usefulness, or safety beyond download handling.
- Docs media has no asset registry, reference count, automatic remote deletion, or cache-version contract. Shared or orphaned objects require manual judgment, and changed R2 bytes may remain edge-cached.
- Interactive companions are discovered across the shared staging root rather than explicitly associated with one selected source.
- Native source-editor intake has changed-source lint/syntax, service-import diagnostics and bounded code-review evidence. The user accepted the overall delivery on 2026-10-04 after chooser button style/size refinements; individual browser selection, multipart transfer, real media writes and failure scenarios were not itemised. `docs-viewer/tests/python/test_docs_staged_media_service.py` and `test_docs_workflow_stages.py::test_child_media_insertion_replace_build_and_read_stay_in_collection` still import the retired staged service and exercise obsolete staging/scope contracts. They were not changed or run and do not cover native intake; retargeting or retirement requires separately specified test work.
- Native 800px display conversion and animation rejection have no approved automated test selection. The user accepted the delivery on 2026-10-06 after confirming a successful Add image saved at 800px. That specimen confirms addition/sizing; input format/orientation, upscaling, image quality, selected-file replacement/collision, thumbnails, animation rejection and failure scenarios were not individually confirmed. Static checks and source review provide no additional runtime coverage; test work is separately scoped.
- A configured media reference can still point at a missing object because normal document rendering is string-based; run the inventory when existence matters.
- Source evidence exists only for successful manual Add operations from configured roots and evidence carried by exact Copy. Historical, imported, or generated media truthfully remains unrecorded.
- A source-evidence row records an asserted root and path, not current presence, unchanged bytes, backup health, or automatic repair. Reorganising or removing an original may leave stale evidence until a later report surfaces it.
- Publish reconciliation is deliberately non-transactional across documents and media: a missing managed object or failed media copy does not roll back published documents, and a changed R2 object may remain edge-cached under the existing stable URL.

For Catalogue maintenance upload commands and the separate local Docs materialization mode, see [Publish Media To R2](Publish_Media_To_R2.md).
