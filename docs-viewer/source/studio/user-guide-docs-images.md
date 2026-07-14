---
doc_id: user-guide-docs-images
title: Docs Images And Assets
added_date: 2026-04-23
last_updated: 2026-07-14
summary: Link existing media, import new images and downloads, or embed self-contained visuals in a Docs Viewer document.
parent_id: docs-viewer
viewable: true
---
# Docs Images And Assets

Use this guide to choose how a document should refer to an image, download, diagram, or interactive asset.

## Choose The Outcome

| goal | use |
| --- | --- |
| Show an existing public-scope image or file. | A `media` token pointing at its R2 object. |
| Show an existing asset in a local or external-local scope. | A `/docs/media/<scope>/...` link. |
| Turn a staged image or downloadable file into its own document. | Docs Import; it creates a wrapper document and stores the bytes. |
| Import the contents of HTML, Markdown, text, or a trusted documents package. | Docs Import; it interprets the supported content and writes document source. |
| Keep a small diagram with the explanation. | Inline safe SVG or HTML in the Markdown source. |
| Run a self-contained interactive example. | An `interactive-html` asset and token, not ordinary media. |

## Accepted Does Not Mean Interpreted

Docs Import accepts several downloadable file extensions because it can store the file and create a document linking to it. It does not necessarily understand the file's contents.

For example, ordinary `.json` or `.jsonl` is imported as a downloadable file:

```text
example.json -> stored bytes + wrapper document with a download link
```

A trusted Data Sharing documents package also uses JSON/JSONL, but its package identity and schema are recognized before the generic-file fallback:

```text
trusted documents package -> collection plan -> several canonical documents
```

CSV, TSV, ZIP, and Office files similarly become downloads; they are not converted into document content. [Media And Asset Handling](/docs/?scope=studio&doc=docs-viewer-media-handling) owns the complete capability distinction and code pointers.

## Link Existing Public Media

Public scopes use literal media tokens so source does not hardcode the shared media origin.

Image:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.jpg&#93;&#93;)</code></pre>

Download:

<pre><code>[Download data](&#91;&#91;media:docs/library/files/example.json&#93;&#93;)</code></pre>

An image token may include positive integer dimensions:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.jpg width=800 height=600&#93;&#93;)</code></pre>

The docs builder replaces the token with `<media_base>/docs/<scope>/<class>/<filename>` before rendering. The token does not upload the object or prove that it exists.

For a manually staged public asset, use the dry-run-first [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2) command. Prefer a new filename when a replacement must appear immediately because Docs media has no cache-version contract.

## Link Existing Local Media

Repo-backed and external-local scopes use the confined local media route:

```md
![Example](/docs/media/studio/img/example.png)
[Download data](/docs/media/studio/files/example.json)
```

For repo-backed scopes, place the file under the configured media root, currently `docs-viewer/source/<scope>/media/img/` or `files/`. External-local scopes use their derived external media root. The local service resolves the URL through scope configuration and rejects traversal and symlink escapes.

Do not put local design documents or working references in `site/`; that tree is the public deploy artifact.

## Import A New Image Or Download

1. Put the source file in `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/`.
2. Open Docs Import in the target scope.
3. Select the file and run the import.
4. Inspect the generated wrapper document and media result.

The target scope decides what happens to the bytes: public scopes publish to R2, repo-backed scopes copy into repo media, external-local scopes copy into their derived external media root, and manual storage reports a copy instruction.

Importing a standalone image or download creates a new canonical document. If you only need to reference an asset that already exists, add the appropriate link instead.

Markdown package imports are different: one Markdown source becomes one document, package images are converted to readable WebP outputs, and supported attachments are copied and linked. HTML and Markdown imports can also extract raster data URLs written as Markdown images. [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import) owns those operator workflows.

## Inline And Interactive Assets

Use inline SVG for a small self-contained diagram that belongs to the explanation. Docs Import sanitizes standalone or imported SVG markup rather than publishing it as ordinary raster media.

Interactive HTML has a separate sandboxed iframe contract and asset location. It is not downloadable media, is not served through `/docs/media/`, and is not selected as an ordinary import source. Use it only when the document genuinely needs executable interaction.
