---
draft: false
doc_id: d-20260607-222033-4b1d77
title: Source Editor Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-16"
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

`media_options` contains `image` and `file` records, each with `accept` (comma-separated native-input suffixes), `max_file_bytes`, `max_total_file_bytes` and `max_metadata_bytes`. These come from the suffix/upload-limit owners used by Source Save. The mounted editor reuses them for Add/Edit and clears them on exit, without a separate options request or source-revision invalidation. `/docs/source/media/options` is retired without an alias.

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

The session owns one complete text buffer and its pending native Files/thumbnail choice. Title/Summary and other valid front matter are edited there; token Apply serializes directly into that buffer without permanent media writes. One Save selects pending Files used by the final buffer/assignment, validates and persists the complete draft/media, rebuilds its exact document/Links and loads the fresh result. **Return to doc** is the explicit non-save exit; one discard decision covers text and pending media, and cancellation retains both. Successful Save keeps busy state until fresh rendered display at the unchanged route and reading position. Other completed actions own their required updates explicitly; browser polling is retired. Entering Source closes the reader capture; returning leaves the reader panel closed until a pin is used.

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

One multipart request contains a `metadata` JSON field and native file fields `file_0`, `file_1`, … matching the selected `media` entries in order. A text-only Save still uses multipart metadata with an empty media list and no file fields.

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "source_text": "---\ndraft: false\ndoc_id: d-20260918-123509-93122f\ntitle: Example\n---\n# Example\n",
  "media": []
}
```

A collection Save also includes its exact `collection`. Metadata accepts only required `doc_id`, string `source_text` and array `media`, plus optional `collection`. Each media entry contains exactly `media_kind` (`image` or `file`) and boolean `body`, `thumbnail` and `replace`. At least one output must be selected. The native file supplies its safe basename and bytes; callers cannot supply destination paths. The browser selects final-buffer membership, the latest independent thumbnail choice and explicit Edit replacement intent. Save does not repeat that membership decision through another source scan.

`docs_source_media_upload.py` bounds each file and their combined bytes at 64 MiB, source/metadata JSON at 1 MiB and multipart overhead at 1 MiB, within a 66 MiB request. Size errors precede media processing/persistence and retain the draft and pending Files. There are no partial uploads, automatic splits, staging sessions or retries. Other JSON routes retain their existing limits. The former JSON-only Save and single-file media-upload contracts have no compatibility aliases.

Actions:

- resolves the fixed Working target and confines its one source before interpreting editable metadata
- parses the candidate once through the strict source splitter, binds the mounted document/collection identity and retains field spans for formatting/timestamp rewrites
- preserves the existing Title/Summary representation, body normalization, readiness, report and Subject rules; nonblank Title feedback belongs to the browser, and ordinary hierarchy/order remains owned by `index-order.json`
- prepares only the supplied media outputs once under the resolved document configuration, including original-raster validation, requested display/thumbnail encodings and SVG sanitization
- compares only selected exact destinations; matching stored bytes are reused, explicit Edit permits replacement, and unexpected new/competing filenames report authoring errors
- sanitizes automatically and carries nonblocking change diagnostics in `media_notes`, with no confirmation/resubmission pass
- completes verified selected media writes before the atomic source write, then carries prepared source/metadata/report/parent information into the exact document/Links builder and completed publication handoff
- compares the already loaded saved body/fields with the prepared candidate in memory, carries current references/removals into generation, durably queues exact public removals and completes confined Working removals without a persisted media baseline or extra by-ID field
- runs no Search, Publish, media inventory, cross-document requeue scan or unrelated registered media producer

Returned data includes the exact target, saved `source_text`, provider-safe `path`, `source_changed`, `summary_text`, `dry_run`, `media_notes`, `media_effects`, `media_complete`, `source_saved` and `generation_complete`. An unchanged buffer skips its source write while still completing selected media and exact generation. Committed metadata is returned only after source persistence; successful generation also supplies `rebuild` and `publication_handoff_complete`.

Preparation errors make no permanent writes. Later failures return HTTP 500 with the failed `phase`, exact target, accurate completion flags and selected media effects identified by role/type/relative identity. Effects distinguish attempted, written, verified and unchanged outputs; partial writes may leave manual cleanup orphans. A source-write failure retains useful Files and the draft. A generation failure reports saved source and completed media, so that persisted buffer is marked clean and Files are released. A completed local generation with failed publication handoff remains a distinct result. Working removal failures identify `phase: "Working media removal"`, the exact failed identity and completed `media_removal_effects`, while preserving queued public removals. Any remaining Working orphan is cleaned manually; Rebuild does not replay an earlier in-memory comparison. Later handoff failures also carry completed removal effects. Display failure reports completed persistence/generation separately. There is no rollback, persistent recovery state or automatic retry.

This remains a single-editor snapshot Save without disk revision checks or external-edit merging. Its busy lifetime includes media/source/generation and the editor's awaited fresh display at the retained route/reading position. Discard releases Files without media/source writes. `POST /docs/source/rebuild` and `POST /docs/update-metadata` remain retired without aliases.

## `POST /docs/source/context`

This write-free request accepts an exact target and complete `source_text`, plus optional `subject_fields` containing exactly `folder_path` and `work_id`. It parses front matter once, checks fixed document/collection identity and either projects the configured Subject or prepares the supplied Subject replacement. It performs no Title/Summary completion, readiness validation, body normalization or report parsing; Source Save owns those checks. The response carries `ok`, exact `doc_id`/optional `collection`, `subject_assignment_available`, `folder_subject_supported` and optional scalar `subject`; omission means None. Work Subjects need no Catalogue existence lookup, and saved Folder identities need no live target. Configured owner/root resolution and supported Subject syntax remain required; the public Work-only projection stays separate.

Assign Subject and Catalogue modals share one derived context per mounted buffer revision, including an in-flight read. Source loading seeds the first context from parsed metadata; successful Subject Apply seeds the resulting revision. Buffer input, changed saved-source replacement or editor release invalidates it. Failed requests remain retryable; late responses cannot replace a newer context. The POST retains `no-store`; this is bounded editor state, not an HTTP or process payload cache. Apply uses the registered Subject normaliser and span-preserving writer without a second full candidate-validation pass or unused change comparison. It preserves unrelated front matter, body and timestamps and updates only the captured current buffer. Folder input retains Projects-root path/file-URL conversion. **Use document subject** accepts Work only; a valid Folder response disables that shortcut without an invalid-Subject error. Opening Directives makes no context request. Folder opening is available through [Projects](/docs/?doc=d-20260805-155400-4c341f); ordinary local-folder links retain their opener. This endpoint writes no source/generated output and runs no Search or Publish. [User Facing Rules](data/User_Facing_Rules.md) D.11/M.14 records the current delivery.

## `POST /docs/source/media`

This is a write-free JSON identity request for a new native selection:

```json
{
  "doc_id": "d-20260918-123509-93122f",
  "media_kind": "image",
  "filename": "Energy wells.png"
}
```

Only the exact `doc_id`, optional configured `collection`, `media_kind` and safe native `filename` are accepted. The service resolves the configured collection/media capability, checks the basename/suffix and returns the target plus `media_identity`. It reads no document source, receives no File bytes, performs no conversion/sanitization/storage comparison and writes no media. Full candidate validity and exact existing target resolution belong to Save.

The identity is `<doc_id>/<readable-filename>` beneath the configured body-media type. Raster output uses WebP and SVG retains its type. The browser retains the native File and serializes authored presentation/link fields locally. Presentation-only Apply and a thumbnail choice using an already pending File need no identity call. Thumbnails keep the independent flat `thumbs/<doc_id>-thumb.webp` identity.

Native bytes are uploaded only through Source Save. Replacement/sanitizer confirmation flags, the former multipart intake and immediate media writes are retired without aliases. [Media And Asset Handling](Media_And_Asset_Handling.md) owns naming, processing and storage.

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
