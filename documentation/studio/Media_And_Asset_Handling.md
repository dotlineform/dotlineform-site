---
draft: false
doc_id: d-20260514-184303-7914e2
title: Media And Asset Handling
added_date: "2026-05-14 18:43:03"
last_updated: "2026-10-04 14:53:28"
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
| Standalone raster image | No image-content analysis; optional thumbnail derivation. | **Add image…** inserts a semantic image token with alt, optional caption/summary and explicit layout fields into the dirty source buffer, and records an explicitly requested thumbnail assignment. | Unchanged display bytes are managed through `img`; the optional 96px WebP is managed through `thumbs`. |
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
configured media source or import-staging fallback
    |
    v
owning workflow classification
    |
    +-- Docs Import document -------> Markdown / collection plan
    |                                      |
    |                                      v
    |                              embedded-media plan
    |                                      |
    |                                      v
    |                         media write -> source write -> rebuild
    |
    +-- Add image / Add file -------> managed-media preview
                                           |
                                           v
                                confirmed, verified managed write
                                           |
                                           v
                              reference inserted into dirty buffer
```

Managed-media materialisation happens before a document import source write or source-editor insertion, so neither workflow commits a new token for bytes it failed to place. Working writes ready media to its exact shared workspace/collection namespace; callers do not select a provider.

Configured Working media-source roots select Projects-owned originals for **Add image…** and **Add file…**; otherwise the workflow uses import staging. The modals list eligible direct-child files from the selected root or confined descendant and leave originals unchanged. Successful materialisation from a configured root records private exact `{media_type, identity, source_root, source_path}` evidence under its Working source owner. Planning does not write evidence, absolute paths are not stored and evidence is not projected publicly.

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

The [Docs Media Report Refactor](Docs_Media_Report_Refactor.md) records implementation evidence and remaining manual review.

The local [Docs Media](/docs/?doc=d-20260812-212735-6d9cf3) report assembles its rows in `docs-media-data.js`, joining Working's ordinary ready-media and registered build-source listing to exact ordinary and collection document references. One row carries its exact `{collection, role, media_type, identity}` without stage. An unreferenced present file remains visible with a blank Documents cell; a referenced identity absent from the live listing produces no row and remains broken-link territory. Build sources do not inherit references from same-basename outputs. Empty document collections have no host entry; nonempty collections provide their exact configured report-host IDs. The browser builds document links through the existing viewer route helper and owns document deduplication and ordering, file exclusions, search, sorting and rendering.

The report omits files whose exact basename is `.DS_Store`, including nested ready-media and build-source files. This display exclusion leaves the files on disk and the shared media inventory unchanged.

`docs_media_reads.py` owns two generic GET reads, each accepting an optional exact `collection`; omission selects ordinary media. The local owner resolves Working without a stage parameter. `/docs/media-files` returns `docs_media_files_v1` with owner identity and `files` containing exact media targets. `/docs/media-references` returns `docs_media_references_v1` with the same media owner, configured `collection_hosts` and referencing `documents`. Each document contains its exact target, title and source media identities, including references to absent files. Both envelopes carry `ok`, `schema_version` and `collection`. They carry no report rows, presentation URLs or filesystem paths. The reference helper reuses `source_media_references()` and still scans current ordinary and collection sources on each refresh; only referencing documents cross the wire. The report requests both datasets and clears its rows if either read or their validation fails. `POST /docs/media-report` and its report builder are removed without an alias.

File-name activation posts the exact media target to `/docs/open-media-source`, owned by `docs_media_actions.py`. It resolves the configured local Docs media location through the confined artifact adapter and requires an existing file. This is a Manage capability; public readers have no local file action. `docs_local_files.open_in_finder()` owns the shared OS execution, platform check and dry-run suppression; the Docs action and Projects `docs_local_links.py` retain separate identity/root validation and errors. The browser receives no filesystem path, and Docs media does not depend on the Projects base. The report adds no media registry, source-evidence join, mutation, public projection, missing-reference row or second storage path. [Reports](Reports.md) owns registration and presentation.

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

`docs_import_media.py` creates logical links and materializes embedded document-import media. `docs_staged_media_service.py` owns standalone source-editor media planning and materialisation.

- Inline raster data URLs are decoded to deterministic `<doc_id>-image-NN.<ext>` names.
- HTML-inline SVG is sanitized from its original fragment to deterministic `<doc_id>-image-NN.svg` names, preserving case-sensitive SVG names and safe stylesheet text rather than reusing HTML-parser serialization.
- Markdown package images are converted to WebP, limited to 800px width without upscaling, and rejected if animation would be flattened.
- Package attachments retain their bytes and receive readable `<doc_id>-attachment-NN.<ext>` names.
- A replacement `doc_id` retargets generated filenames and source links before write.

Standalone source-editor raster images and opaque files retain their bytes. Standalone SVG is sanitized first. Mermaid source is rendered and sanitized in temporary storage before either canonical build source or managed SVG is written. Add image validates the exact document target and current complete source buffer at the service boundary, then normalizes the selected source filename to a lowercase websafe stem and lowercase supported extension; `My Photo.JPG` becomes `my-photo.jpg`. Document title and `doc_id` do not contribute to the display-image name, and naming never allocates numbered suffixes. Mermaid retains the normalized stem for its `.mmd` source and rendered `.svg`. Existing filenames and references remain in place; neither source-name normalization nor a later title change renames stored media. Add file retains its selected-basename naming and collision confirmation. SVG sanitizer removals can still require review. Source subfolders do not become managed subfolders; the existing flat per-type media identity remains authoritative.

Reimporting an image with the same normalized filename addresses the same asset in the exact configured owner and media family. Matching stored bytes are reused without rewriting that artifact; changed bytes require the existing **Replace** confirmation before the awaited write. Mermaid compares and writes its canonical source and rendered SVG independently. Media is shared within its owner, so replacing an asset changes it for every document that references that identity. Different original source names can normalize to the same filename and receive the same collision treatment. Choosing a distinct source basename is the author's way to retain both images. Thumbnail replacement remains the separately selected operation below.

For raster, sanitized SVG and persistent Mermaid SVG images, the server returns one canonical `[[image:<logical-path>|...]]` token through the same preview/apply owner. The token contains required authored alt and explicit placement/fill-width choices, with optional caption and summary. Unchecked **Add caption** omits the caption while preserving independent summary and layout choices. Build creates escaped static figure/image markup; the portable stylesheet owns full-column, equal-column split and natural-width presentation. Public-composition rules own the narrow-screen image-first fallback; local readers retain the desktop presentation. The browser submits no HTML, classes or dimensions. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md#docs-owned-images) owns the grammar, guarded reopening/editing and consumer boundaries. Existing Markdown/HTML image source remains supported without migration.

Collection records reuse the same inline-raster and per-document apply paths. A declared package asset without an authorized mapping remains a warning and preserves its source reference; a document overwrite decision does not grant asset overwrite authority.

### Assigned Document Thumbnails

The shared Add image dialog offers **Create thumb**, unchecked by default and available for raster images. Checked insertion invokes `docs_document_images.py` within the awaited media operation. Docs Viewer invokes FFmpeg directly for one 96×96px WebP: proportional square-cover Lanczos scaling, including small-input upscaling, centred crop, `libwebp`, `photo`, quality 62, compression level 6 and stripped metadata. Only the first raster frame is used for an animated input. The display image keeps its original bytes, dimensions and format; no primary variants or srcset are generated. Studio's image pipeline remains independently owned.

The thumbnail is stored as `<doc_id>-thumb.webp` in the exact document owner's registered `thumbs` family. Each checked operation immediately replaces that fixed identity without inspecting an existing choice or requesting replacement confirmation. Unchecked insertion leaves any existing thumbnail alone. Media writes complete before insertion into the dirty source buffer; the browser inserts the image reference and optional `thumbnail: true` front-matter assignment together. Save persists canonical source and publishes committed metadata to the retained caller; the watcher independently refreshes generated output. A thumbnail failure after the display write reports the stored image and the failed operation without claiming source insertion or undoing writes.

Canonical assignment is optional boolean `thumbnail`: `true` assigns the fixed document thumbnail; `false` or omission clears its presentation without deleting its stored file. Catalogue source rejects this field because generated Work thumbnails retain their separate owner. Builders project `has_thumbnail: true` only for assigned authored documents, into by-ID metadata and named-collection manifests; committed summaries carry the boolean so Source edits can clear an assignment immediately. Lists derive URLs through the configured media root and exact collection owner, without reading bodies or probing files. Generic collection rows, including Concepts and Moments, share Catalogue's decorative lazy-loaded, asynchronously decoded 64×64px contain box, 6px corners and existing spacing within the title navigation control. When the full collection manifest contains any assigned thumbnail, rows without one reserve an empty decorative 64×64px slot so titles and minimum row heights align across filtering and paging; no image element or media request is created for that slot. Collections without assigned thumbnails retain compact text rows. Missing images hide the artwork while preserving the slot and navigation. Ordinary Index, Search and Recent gain no thumbnail presentation.

Docs Media source-reference extraction includes assigned thumbnails under the exact source document owner. Static document Export continues to package media referenced by its rendered body; it adds no hidden thumbnail images or collection-list presentation. Existing content/tree package profiles do not introduce thumbnail selection, and returned content preserves unrelated current source metadata. Registered media role handling remains configuration-driven.

Cancelling source edits, removing body-image tokens or deleting documents retains all stored display images and thumbnails. Removing a body image does not clear the canonical assignment. Orphan inspection and reconciliation remain manual through Docs Media; neither authoring nor Publish deletes orphan bytes. Existing Moments references were mechanically migrated to the title/ID convention with thumbnails derived from each first source image, preserving display bytes, document identities, titles, dates and authored layout. Original filenames and historical variants remain available for manual reconciliation.

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
- A configured media reference can still point at a missing object because normal document rendering is string-based; run the inventory when existence matters.
- Source evidence exists only for successful manual Add operations from configured roots and evidence carried by exact Copy. Historical, imported, or generated media truthfully remains unrecorded.
- A source-evidence row records an asserted root and path, not current presence, unchanged bytes, backup health, or automatic repair. Reorganising or removing an original may leave stale evidence until a later report surfaces it.
- Publish reconciliation is deliberately non-transactional across documents and media: a missing managed object or failed media copy does not roll back published documents, and a changed R2 object may remain edge-cached under the existing stable URL.

For Catalogue maintenance upload commands and the separate local Docs materialization mode, see [Publish Media To R2](Publish_Media_To_R2.md).
