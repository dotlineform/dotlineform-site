---
draft: false
doc_id: d-20260424-000000-fc8b5d
title: Docs Import
added_date: "2026-04-24 00:00:00"
last_updated: "2026-11-19"
summary: Import one native document or select Data Sharing sources and packages for a configured Docs Viewer collection.
parent_id: d-20260424-000000-50b63f

---

# Docs Import

In Docs Viewer Manage, open the destination collection. **Import doc…** takes one file from the native picker. **Import docs…** takes one candidate from a Projects folder, including a complete trusted package. Both are available in empty authored collections and use the collection that opened the action. Checked rows and the visible document do not determine placement. Catalogue uses Work edits and Regenerate. [Collection identity](Collections_And_Books.md#collection-identity)

## Import One Native File

1. In **Concepts → Collection Actions → Import doc…**, choose a Markdown file such as `Surface studies.md`. The chooser accepts one nonempty Word `.docx`, HTML `.html`/`.htm`, Markdown `.md`/`.markdown` or text `.txt` file up to 64 MiB. Cancel closes the action without uploading.
2. Check the filename and choose **Import**. The browser sends the selected bytes and the captured Concepts identity. A first Markdown H1 supplies the title. If there is no H1, a scalar `title` in valid Markdown front matter can supply it. Other incoming front matter is stripped and ignored with a warning. Malformed front matter blocks intake. Word uses the mapped Title style or a humanized filename. Native HTML includes recognized prompt/meta blocks. [Word mapping](HTML_Import_Mapping.md#word-style-mapping) · [HTML mapping](HTML_Import_Mapping.md)
3. The service converts the file, allocates an immutable local `doc_id` and creation timestamp, and prepares supported embedded media under that ID. It validates the candidate, writes Working media and the new Draft source, then awaits exact generation. The returned identity opens that document. Its converted prose and supported media survive. The original file stays where it was, and the original ID, date, hierarchy, status and layout carry no authoring authority. Repeat imports create separate drafts. [Import media preparation](#import-media-preparation) · [Exact generation](Builder.md#exact-generation)

If generation fails after the media, draft source and any Book placement are saved, the modal names the saved draft and changes its primary action to **Rebuild**. Correct the reported issue and choose **Rebuild** to generate and open that same draft. **Close** leaves the saved ID and error in the Manage status. If generation succeeds and display fails, reopen the committed document. After import, review the converted body and media, then set the draft ready when appropriate. [Exact Rebuild](Source_Mutation_Endpoints.md#post-docsrebuild-document) · [Publish](../guide/Publish_And_Deploy.md)

## Choose The Source Folder

**Collection Actions → Import docs…** starts in `$DOTLINEFORM_PROJECTS_BASE_DIR/dotlineform-site/data-sharing/import-staging/`. **Choose folder…** browses Data Sharing and its descendants. The local service supplies both directories to the picker, which remembers an accepted source folder. **Use import staging** restores the default. Changing folders leaves the destination fixed.

Select one direct-child candidate. Ordinary inputs are the native file types or a folder containing one Markdown document with its local images or attachments. Use this path for separate local assets. HTML has an **Include obvious prompt/meta blocks** option, checked by default. Ordinary staged intake shares the native conversion and creates a new draft. Source files are left in place.

Returned JSON/JSONL and complete edited Docs Review source folders must be direct children of import staging. A recognized trusted source outside staging or owned by another collection is shown with a blocking reason. Open the owning collection to confirm a return. A single Markdown source from Docs Review cannot be imported by itself. [Follow a checked-document package round trip](Document_Packages.md#follow-a-checked-document-round-trip)

## Import A Trusted Collection

Choose the trusted candidate from its owning collection. Inspect the complete overwrite plan and confirm once. The matched package can also offer **Open in Docs Review**, which opens a separate read-only projection. To use edits made in that projection's local source, build and inspect it there, then stage the complete edited `source/` folder and select its `(reviewed)` entry. Both return paths use exact prepared existing members. [Overwrite authority and recovery](Document_Packages.md#what-a-return-can-overwrite) · [Docs Review](Docs_Review.md#optional-edited-source-round-trip)

## Import Media Preparation

Native intake sees only the selected file. Converters can extract embedded Word images, inline raster data URLs or supported inline SVG. Markdown folders can supply local images, normally converted to WebP up to 800 px, and supported attachments. Import prepares document-owned references and ready bytes together. Unreadable or unsupported media may be omitted with warnings. Use Source to add an individual image or download to an existing document. [Import materialization](Media_And_Asset_Handling.md#import-materialization)

Import emits an editable `[[image:…]]` token for a new raster image in its own top-level paragraph. The token preserves the imported alt text and uses the image's natural width. Images in prose and references with empty alt text or an explicit Markdown image title retain their Markdown form. [Image source form](Document_And_Catalogue_References.md#docs-owned-images)

A staged ordinary document may bring a separate HTML companion marked `<meta name="dlf:docs-import-role" content="interactive-html">`. A collision at the configured stable asset name requires explicit replacement confirmation. Use the resulting `html-media` token where it should appear. Native intake rejects that asset when selected on its own. [Interactive assets](Media_And_Asset_Handling.md#svg-and-interactive-assets)

## Implementation Boundary

- `POST /docs/import-doc` takes exactly two multipart fields, UTF-8 JSON `metadata` with `filename`, `collection` and optional `include_prompt_meta`, and one `document` byte part. The service requires a safe basename, bounds metadata and envelope overhead to 1 MiB each, and removes its request-local converter input when the operation ends. Completion returns `target`, committed `record` and conversion `warnings`. A generation or publication-handoff failure after persistence returns the saved target and record with `source_saved`, the failing `phase` and `error`. The modal sends that target to exact Rebuild. [Native service](../../docs-viewer/services/docs_import_doc.py)
- `GET /docs/import-source-directories` and `GET /docs/import-source-files` list confined directories and direct candidates. `POST /docs/import-source` accepts the exact collection, approved directory and candidate name. For trusted collections, the first plan is write-free and Apply carries the confirmed plan inputs. [Staged service](../../docs-viewer/services/docs_import_source_service.py) · [Discovery routes](Generated_Data_Contracts.md#local-generated-reads)
- Conversion produces authoring intent. The document planner owns target tests and candidate validation. The write and generation owners carry forward the prepared source and media effects. Independent document creation belongs to `POST /docs/create`. [Import planner](../../docs-viewer/services/docs_import_document.py) · [New document](Source_Mutation_Endpoints.md#post-docscreate)
