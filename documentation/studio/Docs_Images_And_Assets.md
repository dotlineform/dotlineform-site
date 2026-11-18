---
draft: false
doc_id: d-20260423-155039-e36925
title: Docs Images And Assets
added_date: 2026-04-23 15:50:39
last_updated: "2026-11-18"
summary: Link existing media, add native-selected images and downloads to an active document, or embed self-contained visuals.
parent_id: d-20260424-000000-50b63f

---
# Docs Images And Assets

Use this guide to choose how a document should refer to an image, download, diagram, or interactive asset.

## Choose The Outcome

| goal | use |
| --- | --- |
| Show an existing managed image or file. | Use its exact Docs media token. Working and public readers resolve the same logical reference through their configured locations. |
| Add an image or download to the document being edited. | **Add image** or **Add file** inserts the reference in Source. Save writes the selected media. |
| Import the contents of HTML, Markdown, text, or a trusted documents package. | Docs Import; it interprets the supported content and writes document source. |
| Add an authored diagram. | Create/edit it externally, export SVG and select it with **Add Image**. |
| Keep a small code-owned visual with the explanation. | Inline safe SVG or HTML in the Markdown source. |
| Run a self-contained interactive example. | Use the configured `html` media owner and an `html-media` sandbox token. |

## Documents And Media Are Separate

Docs Import interprets supported document sources such as HTML, Markdown, text, Markdown packages and trusted document collections. It creates or overwrites canonical document content.

Ordinary image and downloadable files are media, not document sources. Add them from an active source editor:

```text
example.json -> Add file -> link in the Source draft -> Save stores Working bytes
```

A trusted documents package can also use JSON/JSONL. Docs Import recognizes the package identity and schema.

```text
trusted documents package -> collection plan -> several canonical documents
```

CSV, TSV, ZIP, ordinary JSON/JSONL, PDF, and supported Office files can be added as opaque downloads. Their contents are not converted into document content. [Media And Asset Handling](Media_And_Asset_Handling.md) owns the complete capability distinction and code pointers.

## Link Existing Public Media

Use the logical media reference so the same source works in Manage and Public. Ordinary documents use `docs/<type>/<identity>`. A named collection uses `docs/collections/<id>/<type>/<identity>`. Body media owned by a document includes that document's ID in the identity. These ordinary examples use an already saved document's media.

Image:

<pre><code>![Example](&#91;&#91;media:docs/img/d-20261118-090000-abcdef/example.webp&#93;&#93;)</code></pre>

SVG image:

<pre><code>![Diagram](&#91;&#91;media:docs/svg/d-20261118-090000-abcdef/diagram.svg&#93;&#93;)</code></pre>

Download:

<pre><code>[Download data](&#91;&#91;media:docs/files/d-20261118-090000-abcdef/example.json&#93;&#93;)</code></pre>

An image token may include positive integer dimensions:

<pre><code>![Example](&#91;&#91;media:docs/img/d-20261118-090000-abcdef/example.webp width=800 height=600&#93;&#93;)</code></pre>

To show a literal token in documentation, encode each bracket as <code>&amp;#91;</code> or <code>&amp;#93;</code> inside a raw HTML code element. Token expansion runs before Markdown rendering, so backticks and fenced code blocks do not protect token text.

Working generation retains a portable `docs-media:` identity in the prepared payload. The reader resolves that identity through its configured media base. Publish transfers the queued ready media for eligible documents. [Media token resolution](Media_And_Asset_Handling.md#link-resolution-and-delivery) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Link Existing Local Media

Use the same logical media token for existing Working media. For example, Context media uses the configured collection ID `works`.

<pre><code>![Example](&#91;&#91;media:docs/collections/works/img/d-20261118-090000-abcdef/example.webp&#93;&#93;)</code></pre>

The corresponding Working file is under `working/assets/media/collections/works/img/` in the Docs workspace. The local reader resolves the identity through `/docs/assets/media/collections/works/img/`. Reusing another document's body media in the same owner can copy it into the destination's folder during Save. [Source Save media adoption](Media_And_Asset_Handling.md#source-save-media-adoption)

## Add A New Image Or Download

1. Open the target document's Markdown source editor and choose **Add image…** or **Add file…**.
2. Click the folder-open icon beside the filename field. Select one supported file in the native chooser; its basename fills the field. Empty files and files above 64 MiB are rejected. Cancelling preserves the previous selection.
3. Review the suggested alt text or enter a link label. For an image, review caption, summary and layout settings. Select **Preserve original resolution** for a raster when the detail calls for it.
4. Choose **Add image** or **Add file** to insert the reference and retain the selected File in this Source session. Media is stored only when you Save.
5. Review the draft, then use **Save**. It prepares and stores the selected media, persists source, rebuilds the exact document and displays the fresh result before completing.

Save writes body media under the exact configured document owner's `<doc_id>/<filename>` folder. Thumbnails retain one flat `thumbs/<doc_id>-thumb.webp` per document. Import staging is unnecessary, and the original selected file stays untouched. The editor never asks the author to choose a provider and does not mutate a public repository or R2 projection.

JPEG, PNG, static WebP and single-frame GIF selections become one proportional WebP, with an 800px long edge by default. **Preserve original resolution** keeps the selected pixel dimensions through WebP encoding. `My Photo.JPG` and `My Photo.png` both address `my-photo.webp` within that document. Choose a static image when an input is animated. SVG retains its vector workflow and downloads retain their bytes.

Discard releases unsaved files. Add then remove an image before the first Save and the body image is never stored. Pending replacement bytes count as unsaved changes even when the text matches. The editor retains the draft and files when the selection exceeds the upload limit. Assign or remove a collection document's thumbnail separately with **Edit → Thumb**. [Assigned document thumbnails](Media_And_Asset_Handling.md#assigned-document-thumbnails)

To edit an existing semantic image token, reopen it in Source. The same filename field initially shows its stored basename; select replacement bytes or edit presentation alone. **Apply** changes the captured occurrence locally. Add file over a captured authored file link also opens Edit file. Selecting replacement bytes through Edit supplies replacement intent to Save; no second Replace dialog appears. Unexpected filename conflicts are authoring errors, with the draft/Files retained. Different documents can independently use the same readable body-media basename. Existing stored images are not migrated or deleted merely by editing the draft.

For a diagram, export SVG from its external authoring tool and use Add Image. Replacing the finished SVG uses the ordinary Edit/Save workflow.

Save sanitizes SVG automatically and reports changes as a nonblocking note. Invalid SVG or processing failure stops Save. Preparation errors make no permanent writes; later persistence failures identify the failed phase and completed effects. Partial media writes can leave orphans for manual cleanup, and saved source is reported accurately if generation subsequently fails.

After document ownership has been recorded by generation, removing the last saved reference to an owned body file selects its exact Working file for deletion and queues its Preview/public removal. Use **Edit → Thumb** to remove the separate thumbnail. Draft or exclusion preserves media. Confirmed document Delete selects its owned media folders and fixed thumbnail for Working removal and queues their Preview/public removal. Publish applies those removals, including R2, before the separate manual Pages deployment. [Saved ownership and exact removals](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals) · [Document Delete media cleanup](Media_And_Asset_Handling.md#document-delete-media-cleanup)

Markdown package imports are different: one Markdown source becomes one document, package images are converted to readable WebP outputs, and supported attachments are copied and linked. HTML and Markdown imports can also extract raster data URLs written as Markdown images. [Docs Import](Docs_Import.md) owns those operator workflows.

## SVG And Interactive Assets

Use **Add image…** for new SVG. Insertion retains the selected File; Source Save sanitizes and writes it through the document owner's configured `svg` media class. Docs Import uses the same sanitizer and class when it extracts inline SVG from imported HTML. Historical SVG tokens beneath `img` and manually authored inline SVG are not migrated automatically.

Keep editable diagram source with the external tool/project that owns it. The finished SVG is ordinary document media and has one authored appearance. Repository documentation diagrams use an external Markdown viewer. [Document Diagrams](Document_Diagrams.md) explains the current workflow.

An interactive HTML example uses the document owner's configured `html` media type. Embed an existing ordinary document asset with its logical reference.

<pre><code>&#91;&#91;html-media:docs/html/d-20261118-090000-abcdef/example.html height=546&#93;&#93;</code></pre>

The renderer resolves the identity through the configured owner and emits a lazy iframe with `sandbox="allow-scripts"`. Docs Import treats an interactive companion as media when its package role declares it.
