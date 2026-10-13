---
draft: false
doc_id: d-20260607-222033-4b1d77
title: Source Editor Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-13 18:37:00"
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

Returned data includes `ok`, `doc_id`, optional `collection`, complete `source_text`, a provider-safe `path`, `subject_assignment_available`, `folder_subject_supported` and optional scalar `subject`. These Subject fields seed the editor's loaded buffer revision. A Subject projection failure is returned as `subject_error`, leaving Source available for manual correction; Subject consumers report that error. No source revision or separate metadata/body transport is returned.

`media_options` contains `image` and `file` records, each with `accept` (comma-separated native-input suffixes), `max_file_bytes` and `max_metadata_bytes`. These come from the same suffix/limit owners used by intake. The mounted editor reuses them for Add/Edit and clears them on exit, without a separate options request or source-revision invalidation. `/docs/source/media/options` is retired without an alias.

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

This endpoint reads canonical source and does not write files. Ordinary resolution reads `index-order.json` for exact membership/parent information and only the requested confined source; it does not parse unrelated documents. Saved readiness and report validity do not gate opening Source for correction. Strict source parsing and exact document identity remain required; Subject projection errors are returned for the loaded buffer. Index rows and generated payloads do not supply the editable metadata snapshot.

## Source session contract

The manage UI opens Markdown source with one explicit target:

- ordinary document: `{ doc_id }`
- configured collection document: `{ collection, doc_id }`

The editor mounts that target once and uses it for source read, Save, Open in VS Code, diagram-source actions and every registered buffer contribution. Selected-document state, displayed content and URL `doc` or `subdoc` values cannot retarget an active session.

One **Edit document** action opens the complete Markdown buffer without a metadata/token panel or **i** control. It targets the displayed ordinary document, the host from a collection list, or the exact validated collection detail. A detail offers no parent Source action.

The session owns one complete text buffer. Title/Summary and other valid front matter are edited there; token Apply serializes directly into that buffer. One Save validates and persists the complete draft, rebuilds its exact document/Links and loads the fresh rendered result. **Return to doc** is the explicit non-save exit; one discard decision covers the whole draft, and cancellation retains it. Successful Save keeps busy state until fresh rendered display at the unchanged route and reading position. Other completed actions own their required updates explicitly; browser polling is retired. Entering Source closes the reader capture; returning leaves the reader panel closed until a pin is used.

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

**Insert doc link** makes one parameter-free Working lookup when its picker opens. The read-only service selects ordinary sources from Index IDs and lists direct-child Markdown sources once for each configured flat collection. It confines and reads each selected source once, then uses the shared front-matter field parser for identity/title metadata without full source-model or Subject validation. Draft readiness, ordinary ignore membership, publication eligibility and Subject metadata do not filter selection; discovery performs no preliminary recursive source audit.

The `docs_document_link_targets_v2` response contains configured `collections` and `documents`. Each document supplies its stored title, explicit `{collection, doc_id}` target and ordinary `href`; ordinary targets use an empty collection in the picker record. Titles retain their supplied representation without coercion, completeness checks or ID-derived fallback. Source identity must agree with its filename; the canonical route constructor owns immutable-ID syntax and URL encoding. Locations use the exact owner and document independently of report-host placement and omit workflow-stage parameters. Unavailable source collections and actual source/parsing failures remain errors.

The modal consumes the service records directly, without schema/collection/duplicate/target/href-agreement audits or another Title completeness gate. Filtering all documents, ordinary documents or one exact collection, title/ID search, selection and Insert use the loaded response and make no further lookup. The picker performs no publication-eligibility read or public-omission warning. Confirmation inserts the selected title as escaped literal link text and the supplied href through captured, revision-guarded buffer replacement. This guard concerns the mounted buffer, not a disk revision. Insertion does not save, rebuild, change front matter or generate relationships. Public providers expose no local target-lookup capability.

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
- parses the complete candidate once through the source model's strict front-matter splitter, rejecting missing delimiters, malformed lines, duplicate keys and invalid quoted values; retained field spans support later rewrites without another parse
- requires candidate `doc_id` and any declared `collection` to match the mounted target; edited metadata cannot rename, relocate or select a different file
- requires Title and any supplied Summary to be strings and keeps their existing formatting, including removal of a blank Summary; the frontend asks for a nonblank Title before making this request and the server does not repeat that completeness check or substitute a default. Summary normalizes line endings and outer whitespace while preserving internal line/paragraph breaks, with `|`/`|-` literal-block support owned by [Builder](Builder.md#summary-block)
- validates required readiness, collection report rules and Subject customisation through their current owners; Catalogue retains fixed eligibility and rejects `draft`
- preserves other authored metadata lines and the existing canonical membership policy; ordinary hierarchy/order remains owned by `index-order.json`
- normalizes submitted body line endings to `\n`
- replaces Unicode-whitespace-only lines with empty lines outside fenced code and explicit `<pre>` blocks
- applies the normal source timestamp for changed, non-dry-run writes
- carries the prepared source, metadata, report classification and timestamps through one atomic source write and the response
- awaits the existing exact-target document/Links builder in process with that prepared source and resolved configuration/ordinary parent information, without reopening source, repeating candidate validation or rediscovering IDs; generation uses prepared media, without Search, Publish or registered media production

Returned data includes `ok`, the exact target, saved complete `source_text`, provider-safe `path`, `source_changed`, `summary_text` and `dry_run`. An unchanged source skips the write but still rebuilds its exact document and loads the result. Validation or write failure leaves the complete browser draft available for correction. Non-dry-run responses also carry `source_saved`, `generation_complete`, `committed_document` and, on successful generation, `rebuild`.

This is a single-editor snapshot save: there is no disk revision check, external-edit merge or placement operation. The service completes after exact document/Links generation. The editor then awaits a fresh generated read and display before releasing busy state. A generation failure returns HTTP 500 with `ok: false`, `source_saved: true`, `generation_complete: false`, saved `source_text`, committed metadata and a specific `error`. The editor marks that persisted buffer clean and retains it for diagnosis. A display failure is reported separately as completed saving/generation with failed display. Recovery uses explicit Rebuild or reload; there is no source rollback or automatic retry. The filesystem watcher and its suppression machinery are retired.

`POST /docs/source/rebuild` and `POST /docs/update-metadata` are removed without compatibility aliases. Title/Summary editing now uses this combined session write.

## `POST /docs/source/context`

This write-free request accepts an exact target and complete `source_text`, plus optional `subject_fields` containing exactly `folder_path` and `work_id`. It parses front matter once, checks fixed document/collection identity and either projects the configured Subject or prepares the supplied Subject replacement. It performs no Title/Summary completion, readiness validation, body normalization or report parsing; Source Save owns those checks. The response carries `ok`, exact `doc_id`/optional `collection`, `subject_assignment_available`, `folder_subject_supported` and optional scalar `subject`; omission means None. Work Subjects need no Catalogue existence lookup, and saved Folder identities need no live target. Configured owner/root resolution and supported Subject syntax remain required; the public Work-only projection stays separate.

Assign Subject and Catalogue modals share one derived context per mounted buffer revision, including an in-flight read. Source loading seeds the first context from parsed metadata; successful Subject Apply seeds the resulting revision. Buffer input, changed saved-source replacement or editor release invalidates it. Failed requests remain retryable; late responses cannot replace a newer context. The POST retains `no-store`; this is bounded editor state, not an HTTP or process payload cache. Apply uses the registered Subject normaliser and span-preserving writer without a second full candidate-validation pass or unused change comparison. It preserves unrelated front matter, body and timestamps and updates only the captured current buffer. Folder input retains Projects-root path/file-URL conversion. **Use document subject** accepts Work only; a valid Folder response disables that shortcut without an invalid-Subject error. Opening Directives makes no context request. Folder opening is available through [Projects](/docs/?doc=d-20260805-155400-4c341f); ordinary local-folder links retain their opener. This endpoint writes no source/generated output and runs no Search or Publish. [User Facing Rules](data/User_Facing_Rules.md) D.11/M.14 records the current delivery.

## `POST /docs/source/media`

Multipart form data contains exactly `metadata` JSON and one native `file`. Metadata identifies the exact mounted `doc_id`, optional configured `collection`, `media_kind` (`image` or `file`) and `label`. Image intake adds its presentation and thumbnail choices:

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "media_kind": "image",
  "label": "Energy wells diagram",
  "create_thumb": false,
  "add_caption": true,
  "caption": "Energy wells",
  "summary": "First supporting line\nSecond supporting line",
  "placement": "right",
  "fill_width": false
}
```

`label` supplies image alt text. Image requests require boolean `add_caption` and `fill_width`, and allowlisted `placement` (`full`, `left` or `right`); `add_caption: true` requires nonblank plain-text `caption`. Optional `summary` preserves normalized line breaks. `create_thumb` is a boolean and can be true only for a supported raster image. File requests do not use image-presentation fields. The browser supplies no HTML, classes, dimensions, staged paths or caller-selected destinations.

Intake receives no `source_text` and performs no full Source Save candidate validation. It resolves the exact existing document/collection owner and retains upload basename/type/size checks, path confinement, conversion/sanitization, presentation serialization and actual media/storage failures. Existing saved-source target parsing/checks remain. Validation and normalization of Title/Summary, readiness, Subject and reports in the unsaved buffer remain with Source Save.

The service carries the exact target's resolved owner through preparation, reference construction and requested thumbnail storage. It prepares selected bytes in operation-owned temporary storage, then compares the owner/family/filename identity once per request and carries that result into reuse or confirmed storage through the same adapter. Raster/SVG/file intake omits the generic batch publisher's owner reload, MD5 work and repeated destination preflight. New or unchanged media completes in one request. Changed bytes or sanitizer warnings return `requires_confirmation: true` without permanent writes, together with collision and sanitization diagnostics. Confirmed resubmission sends the same native File and metadata with `confirm_replace` and `confirm_sanitization` booleans and prepares those bytes within the new request. Required media and requested thumbnail writes and their verification finish before the response returns insertion Markdown, media identity/token and completion status. The browser edits only the captured current Source occurrence/range and leaves the buffer dirty for Save. Presentation-only token Apply uses local serialization and makes no media request.

Intake does not write document source, build documents or Publish. Discarding Source can leave completed shared media writes unreferenced. The separate staged listing/preview/apply routes are retired without aliases; Docs Import/package staging retains its own owner. [Media And Asset Handling](Media_And_Asset_Handling.md) owns formats, naming, storage and failure boundaries.

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
