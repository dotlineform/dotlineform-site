---
draft: false
doc_id: d-20260607-222033-4b1d77
title: Source Editor Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-08 19:10:43"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Source Editor Endpoints

## `GET /docs/source`

Query parameters:

```text
doc_id=d-20260918-123509-93122f
```

For a configured collection document, add its explicit `collection` identity and supply that document's exact `doc_id`.

`doc` is not a source-target alias. Source reads require `doc_id`.

Returned data includes `ok`, `doc_id`, optional `collection`, complete `source_text` and a provider-safe `path`. `source_text` contains the loaded front matter and body. No source revision or separate metadata/body transport is returned.

Used for:

- loading the manage-mode Markdown source editor
- loading the complete Markdown draft for one editing session
- displaying the provider-safe source path for the mounted target

Validation:

- the service resolves Working; caller-selected `stage`, `scope` and `sub_scope` are rejected
- a supplied `collection` must be configured
- `doc_id` must resolve inside that exact ordinary or named-collection source root
- the source path must remain inside the configured target root
- existing front matter must parse and contain the requested `doc_id`
- missing, unlisted, mismatched, nested, or path-escaping targets are rejected

This endpoint reads canonical source and does not write files. Index rows and generated payloads do not supply the editable metadata snapshot.

## Source session contract

The manage UI opens Markdown source with one explicit target:

- ordinary document: `{ doc_id }`
- configured collection document: `{ collection, doc_id }`

The editor mounts that target once and uses it for source read, Save, Open in VS Code, diagram-source actions and every registered buffer contribution. Selected-document state, displayed content and URL `doc` or `subdoc` values cannot retarget an active session.

One **Edit document** action opens the complete Markdown buffer without a metadata/token panel or **i** control. It targets the displayed ordinary document, the host from a collection list, or the exact validated collection detail. A detail offers no parent Source action.

The session owns one complete text buffer. Title/Summary and other valid front matter are edited there; token Apply serializes directly into that buffer. One Save validates and persists the complete draft, rebuilds its exact document/Links and loads the fresh rendered result. **Return to doc** is the explicit non-save exit; one discard decision covers the whole draft, and cancellation retains it. Successful Save keeps busy state until fresh rendered display at the unchanged route and reading position. Independent Working polling remains for other generated changes. Entering Source closes the reader capture; returning leaves the reader panel closed until a pin is used.

## Local folder-link paste

Manage Source authoring consumes the current runtime-only capability:

```json
{
  "local_folder_links": {
    "authoring": true,
    "activation": true,
    "base_path": "/configured/projects/base",
    "docs_base_path": "/configured/docs/base"
  }
}
```

`base_path` and `docs_base_path` are used only to recognize one complete `text/plain` paste. Each is empty when its configured root is unavailable; authoring is available when either root is available. An absolute POSIX path, shell-backslash-escaped absolute path, or local `file:` URL strictly below the Projects base becomes a canonical marked link such as `[3 symbols](dlf-local:projects/3%20symbols)`. A path below the Docs base becomes a Docs-selected target such as `[links.json](dlf-local:docs:working/generated/documents/links.json)`. The absolute base is not inserted into source or generated output, and authoring does not require the target to exist.

Conversion runs only in ordinary Markdown prose. Code, comments, `<pre>`, outside-root, mixed, multiline, or ambiguous input, including a path matching both roots, retains normal browser paste behaviour. Successful conversion is silent, marks the buffer dirty, and makes no claim on the browser's native Undo history. It calls no management endpoint; activation occurs only from a rendered valid link. `POST /docs/open-local-target` receives only the canonical encoded target, resolves its selected existing root, validates confinement and reveals a file or opens a directory in Finder. It never falls back to the other root.

## `GET /docs/document-link-targets`

**Insert doc link** reads Working through the owning service. The read-only service enumerates ordinary documents and every configured collection through their source owners. Draft readiness, ordinary ignore membership, publication eligibility and Subject metadata do not filter selection.

The `docs_document_link_targets_v2` response contains configured `collections` and `documents`. Each document supplies its title, explicit `{collection, doc_id}` target and ordinary `href`; ordinary targets use an empty collection in the picker record. Collection locations use the configured host and exact document identity. Authored hrefs omit workflow-stage parameters. Unavailable collections and ambiguous hosts fail visibly without fallback.

The modal filters all documents, ordinary documents or one exact collection and searches by title or immutable ID. Confirmation inserts the selected title and href through captured, revision-guarded buffer replacement. This guard concerns the mounted buffer, not a disk revision. Insertion does not save, rebuild, change front matter or generate relationships. Public providers expose no local target-lookup capability.

**Insert Subject Link** and its exclusive `POST /docs/validate-local-target` endpoint are retired. Subject metadata reads and assignment remain supported by their own consumers. Local-folder paste and `POST /docs/open-local-target` activation retain their existing confinement owner.

## `POST /docs/source/save`

Expected data:

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "source_text": "---\ndraft: false\ndoc_id: d-20260918-123509-93122f\ntitle: Example\nsummary: An edited summary.\n---\n# Example\n"
}
```

A collection Save also includes its exact `collection`. The only accepted fields are required `doc_id` and string `source_text`, plus optional `collection`. The previous split `source_front_matter`, `source_body` and editable `metadata` contract is removed without aliases.

Actions:

- resolves the fixed Working target and confines its source path before interpreting editable metadata
- parses the complete candidate through the source model's strict front-matter splitter, rejecting missing delimiters, malformed lines, duplicate keys and invalid quoted values
- requires candidate `doc_id` and any declared `collection` to match the mounted target; edited metadata cannot rename, relocate or select a different file
- normalizes Title and Summary, rejects an empty Title and removes a blank Summary; Summary normalizes line endings and outer whitespace while preserving internal line/paragraph breaks, with `|`/`|-` literal-block support owned by [Builder](Builder.md#summary-block)
- validates required readiness, collection report rules and Subject customisation through their current owners; Catalogue retains fixed eligibility and rejects `draft`
- preserves other authored metadata lines and the existing canonical membership policy; ordinary hierarchy/order remains owned by `index-order.json`
- normalizes submitted body line endings to `\n`
- replaces Unicode-whitespace-only lines with empty lines outside fenced code and explicit `<pre>` blocks
- applies the normal source timestamp for changed, non-dry-run writes
- validates the complete candidate through the source schema before one atomic source write
- awaits the existing exact-target document/Links rebuild using prepared media, without Search, Publish or registered media production

Returned data includes `ok`, the exact target, saved complete `source_text`, provider-safe `path`, `source_changed`, `summary_text` and `dry_run`. An unchanged source skips the write but still rebuilds its exact document and loads the result. Validation or write failure leaves the complete browser draft available for correction. Non-dry-run responses also carry `source_saved`, `generation_complete`, `committed_document` and, on successful generation, `rebuild`.

This is a single-editor snapshot save: there is no disk revision check, external-edit merge or placement operation. The service completes after exact document/Links generation. The editor then awaits a fresh generated read and display before releasing busy state. A generation failure returns HTTP 500 with `ok: false`, `source_saved: true`, `generation_complete: false`, saved `source_text`, committed metadata and a specific `error`. The editor marks that persisted buffer clean and retains it for diagnosis. A display failure is reported separately as completed saving/generation with failed display. Recovery uses explicit Rebuild or reload; there is no source rollback or automatic retry. The filesystem watcher and its suppression machinery are retired.

`POST /docs/source/rebuild` and `POST /docs/update-metadata` are removed without compatibility aliases. Title/Summary editing now uses this combined session write.

## `POST /docs/source/context`

This write-free request accepts the same exact target and complete `source_text` as Save. The source service validates the unsaved candidate through the same parser, identity and collection owners and returns `{ok, doc_id, collection?, subject}`. It resolves the configured collection without rereading document sources; Save independently resolves the actual file before persistence. The safe Work/Series Subject projection powers **Use document subject** in Catalogue modals; it is derived from the captured current buffer, not a loaded metadata draft. Invalid source disables that optional choice with a visible error while the modal preserves its token values and Catalogue picker. The adapter rejects a late context response after the buffer or mounted editor changes. This endpoint performs no source write, timestamp advancement, generation, Search rebuild or Publish.

## `GET /docs/staged-media-files`

Query parameters:

```text
media_kind=image
```

`media_kind` must be `image` or `file`. The service lists only safe, non-symlink direct children of the shared staging root:

- `image`: supported raster formats plus `.svg`
- `file`: allowlisted opaque download formats

Returned records contain safe staging identity, kind/format, suggested label, size, and modification time. Document sources are not listed here, and media is not listed by global Docs Import.

## `POST /docs/staged-media-preview`

Expected data:

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "media_kind": "image",
  "staged_filename": "diagram.svg",
  "label": "Energy wells"
}
```

A captioned image adds the semantic presentation fields:

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "media_kind": "image",
  "staged_filename": "diagram.svg",
  "label": "Energy wells diagram",
  "add_caption": true,
  "caption": "Energy wells",
  "summary": "First supporting line\nSecond supporting line",
  "placement": "right",
  "fill_width": false
}
```

`label` remains the required image alt text. `add_caption: true` requires a
nonblank plain-text `caption`, one allowlisted `placement` value (`full`,
`left`, or `right`), and a JSON boolean `fill_width`. `summary` is optional
plain text and preserves normalized line breaks. Missing or non-boolean
`fill_width` fails validation; the service does not infer a default. When
`add_caption` is false or absent, the presentation fields are omitted and the
response retains the plain Markdown image fragment. File requests do not use
image-presentation fields.

The write-free preview resolves the configured target media class (`img` for raster, `svg` for SVG, or `files` for downloads), sanitizes SVG when applicable, and returns:

- stable logical media identity and token;
- exact source fragment: a plain Markdown image, semantic figure, or file link;
- `new`, `unchanged`, or `replace` collision state;
- replacement-confirmation requirement;
- sanitized-SVG title and diagnostics when applicable.

It exposes no physical provider path and does not create or identify a document.

The semantic figure is image-first source with escaped attributes and text. It
uses `docsViewerFigure` plus one fixed placement class. `fill_width: false`
adds `docsViewerFigure--natural-width`; `true` uses the available full or split
column. The browser never supplies source HTML, class names, or dimensions.

The source editor consumes this preview internally. It proceeds directly for `new` and `unchanged`, and opens a follow-up modal only for changed-byte replacement or SVG sanitizer diagnostics that require review.

## `POST /docs/staged-media-apply`

Expected data is the preview request plus `confirm_replace: true` when changed bytes would replace an existing media identity.

Apply repeats safe resolution and sanitization, publishes through the configured provider-neutral media boundary, byte-verifies the result, and returns the preview contract plus publication status and Markdown. It does not write document source; the browser inserts the returned Markdown at the current source-editor selection and leaves the buffer dirty for `POST /docs/source/save`.

Publication precedes insertion. Staged files are retained. The action may leave unreferenced published media if the author later abandons the dirty source edit, but it cannot insert a reference after failed publication.

## `POST /docs/open-source`

Expected data:

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "editor": "default"
}
```

Add `collection` for a configured collection target.

`editor` must be `default` or `vscode`.

The manage toolbar supplies the target explicitly. On an ordinary document or collection report list, **Open in VS Code** supplies the selected document or host target. On a validated collection detail, it supplies that detail's `{collection, doc_id}`. Loading, failed, unknown or unlisted details disable the action without falling back to the host. In Source mode, the action supplies the editor's fixed mounted target.

Actions:

- resolves the explicit source Markdown target inside its configured ordinary or collection root
- for `editor: "vscode"`, opens the file with Visual Studio Code
- for `editor: "default"`, uses `DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP` when configured, otherwise prefers `MarkEdit`, `Typora`, `Marked 2`, then `Marked`, then macOS Launch Services defaults
- logs a `docs-open-source` event when the open command succeeds

Returned data includes `ok`, optional `collection`, `doc_id`, `editor`, `preferred_app`, provider-safe `path`, summary text and `dry_run`.

This endpoint opens a local application. It does not modify docs source or generated output.
