---
draft: false
doc_id: d-20260423-155039-e36925
title: Docs Images And Assets
added_date: 2026-04-23 15:50:39
last_updated: "2026-10-16"
summary: Link existing media, add native-selected images and downloads to an active document, or embed self-contained visuals.
parent_id: d-20260424-000000-50b63f

---
# Docs Images And Assets

Use this guide to choose how a document should refer to an image, download, diagram, or interactive asset.

## Choose The Outcome

| goal | use |
| --- | --- |
| Show an existing public-scope image or file. | A `media` token pointing at its R2 object. |
| Show an existing asset in a local or external-local scope. | A `/docs/media/<scope>/...` link. |
| Add an image, Mermaid source, or download to the document being edited. | Source editor **Add image…** or **Add file…**; the filename field's folder-open icon selects a file, then confirmation writes required media and inserts a logical reference. |
| Import the contents of HTML, Markdown, text, or a trusted documents package. | Docs Import; it interprets the supported content and writes document source. |
| Add a reproducible authored diagram. | Select `.mmd` through **Add image…**, or author canonical Mermaid source directly in its configured build-source owner. |
| Keep a small code-owned visual with the explanation. | Inline safe SVG or HTML in the Markdown source. |
| Run a self-contained interactive example. | Published `html` media with an `html-media` sandbox token. |

## Documents And Media Are Separate

Global Docs Import lists only document sources: HTML, Markdown, text, Markdown packages, and trusted document collections. It interprets those sources and creates or overwrites canonical document content.

Ordinary image and downloadable files are media, not document sources. Add them from an active source editor:

```text
example.json -> Add file -> published bytes + link inserted into the current buffer
```

A trusted Data Sharing documents package also uses JSON/JSONL, but it appears in Docs Import only when its package identity and schema are recognized:

```text
trusted documents package -> collection plan -> several canonical documents
```

CSV, TSV, ZIP, ordinary JSON/JSONL, PDF, and supported Office files can be added as opaque downloads. Their contents are not converted into document content. [Media And Asset Handling](Media_And_Asset_Handling.md) owns the complete capability distinction and code pointers.

## Link Existing Public Media

Public scopes use literal media tokens so source does not hardcode the shared media origin.

Image:

<pre><code>![Example](&#91;&#91;media:docs/analysis/img/example.jpg&#93;&#93;)</code></pre>

SVG image:

<pre><code>![Diagram](&#91;&#91;media:docs/analysis/svg/diagram.svg&#93;&#93;)</code></pre>

Download:

<pre><code>[Download data](&#91;&#91;media:docs/analysis/files/example.json&#93;&#93;)</code></pre>

An image token may include positive integer dimensions:

<pre><code>![Example](&#91;&#91;media:docs/analysis/img/example.jpg width=800 height=600&#93;&#93;)</code></pre>

To show a literal token in documentation, encode each bracket as <code>&amp;#91;</code> or <code>&amp;#93;</code> inside a raw HTML code element. Token expansion runs before Markdown rendering, so backticks and fenced code blocks do not protect token text.

The docs builder replaces the token with `<media_base>/docs/<scope>/<class>/<filename>` before rendering. The token does not upload the object or prove that it exists.

For a manually staged public asset, use the dry-run-first [Publish Media To R2](Publish_Media_To_R2.md) command. Prefer a new filename when a replacement must appear immediately because Docs media has no cache-version contract.

## Link Existing Local Media

Repo-backed and external-local scopes use the confined local media route:

```md
![Example](/docs/media/studio/img/example.png)
![Diagram](/docs/media/studio/svg/diagram.svg)
[Download data](/docs/media/studio/files/example.json)
```

Place the file at `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media/<scope>/<type>/`. Every scope's private managed media uses this external namespace. The local service resolves the URL through scope configuration and rejects traversal and symlink escapes; public repository or R2 copies are not a fallback.

Do not put local design documents or working references in `site/`; that tree is the public deploy artifact.

## Add A New Image Or Download

1. Open the target document's Markdown source editor and choose **Add image…** or **Add file…**.
2. Click the folder-open icon beside the filename field. Select one supported file in the native chooser; its basename fills the field. Empty files and files above 64 MiB are rejected. Cancelling preserves the previous selection.
3. Enter useful alt text or a link label. For an image, review caption, summary and layout settings; optionally select **Create thumb** for a static raster image.
4. Choose **Add image** or **Add file** to insert the reference and retain the selected File in this Source session. Media is stored only when you Save.
5. Review the draft, then use **Save**. It prepares and stores the selected media, persists source, rebuilds the exact document and displays the fresh result before completing.

Save writes body media under the exact configured document owner's `<doc_id>/<filename>` folder. Thumbnails retain one flat `thumbs/<doc_id>-thumb.webp` per document. Import staging is unnecessary, and the original selected file stays untouched. The editor never asks the author to choose a provider and does not mutate a public repository or R2 projection.

JPEG, PNG, static WebP and single-frame GIF selections become one proportional WebP with an exactly 800px long edge, scaling up or down without cropping. `My Photo.JPG` becomes `my-photo.webp`; selecting `My Photo.png` addresses that same managed identity. Already-WebP selections use the same conversion. Animated inputs are rejected with a request to choose a static image. SVG and Mermaid retain their vector workflows, and downloads retain their bytes. Optional thumbnails are generated from the original upload as 96px square WebP images. Upscaling cannot recover detail, and fine text or large display areas may look softer at 800px.

Discard releases unsaved Files without media writes. Add then remove before first Save stores no body image; a retained thumbnail assignment can still request thumbnail-only output. Pending replacement bytes and thumbnail choices count as unsaved changes even if the text is unchanged. A file or combined pending-media selection above 64 MiB reports an error for you to resolve while retaining the draft/Files. Public publication remains a separate action.

To edit an existing semantic image token, reopen it in Source. The same filename field initially shows its stored basename; select replacement bytes or edit presentation alone. **Apply** changes the captured occurrence locally. Add file over a captured authored file link also opens Edit file. Selecting replacement bytes through Edit supplies replacement intent to Save; no second Replace dialog appears. Unexpected filename conflicts are authoring errors, with the draft/Files retained. Different documents can independently use the same readable body-media basename. Existing stored images are not migrated or deleted merely by editing the draft.

For Mermaid `.mmd`, insertion retains the File and inserts its SVG reference. Save renders/sanitizes once, then writes the editable source and same-stem SVG under their configured document-owned locations. The diagram-title link in rendered Document Info's **Diagrams** section opens the saved editable source. Persistent external media-source changes require the explicit Rebuild docs and Search action; there is no filesystem watcher.

Save sanitizes SVG automatically and reports changes as a nonblocking note. Invalid SVG or processing failure stops Save. Preparation errors make no permanent writes; later persistence failures identify the failed phase and completed effects. Partial media writes can leave orphans for manual cleanup, and saved source is reported accurately if generation subsequently fails.

Markdown package imports are different: one Markdown source becomes one document, package images are converted to readable WebP outputs, and supported attachments are copied and linked. HTML and Markdown imports can also extract raster data URLs written as Markdown images. [Docs Import](Docs_Import.md) owns those operator workflows.

## SVG, Mermaid, And Interactive Assets

Use **Add image…** for new SVG. Insertion retains the selected File; Source Save sanitizes and writes it through the document owner's configured `svg` media class. Docs Import uses the same sanitizer and class when it extracts inline SVG from imported HTML. Historical SVG tokens beneath `img` and manually authored inline SVG are not migrated automatically.

Use Mermaid when the diagram should remain reproducible and editable as source. Canonical `.mmd` is build media rather than reader media; the registered producer renders, sanitizes, publishes, and byte-verifies the SVG. Readers load only that static SVG and never receive Mermaid, Node, or Puppeteer runtime code.

HTML is stored once at the scope's configured published `html` root, regardless of whether it is interactive. Embed it with a logical token such as:

<pre><code>&#91;&#91;html-media:docs/analysis/html/example.html height=546&#93;&#93;</code></pre>

The renderer resolves that identity through scope configuration and emits a lazy iframe with `sandbox="allow-scripts"`. HTML is not served through `/docs/media/` and role-marked interactive companions are not selected as ordinary document sources.
