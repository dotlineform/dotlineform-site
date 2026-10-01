---
draft: false
doc_id: d-20260607-222033-704641
title: Source Editor Scripts
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-01 16:39:11"
parent_id: d-20260607-222033-2a494e
---
# Docs Viewer Source Editor Scripts

## `docs-viewer/services/docs_management_source_service.py`

Purpose: read and save one complete Source session, plus local editor open helpers.

Ownership: owns the source-editor API contract and local source-open behavior.

Responsibilities:

- resolves exact Working document targets through the configured workspace and collection owners
- confines source paths to their configured roots and checks immutable document identity
- returns full parsed metadata, the loaded front-matter block, body and safe Subject projection
- validates Title, Summary and the complete candidate source before one atomic write
- preserves non-edited metadata lines and applies the normal source timestamp on changed writes
- normalizes submitted body line endings and Unicode-whitespace-only prose lines
- completes Save at source persistence; the watcher independently owns targeted document and Links generation
- opens source docs with the configured or preferred local Markdown editor
- logs open-source events

Not responsible for:

- source-revision checks, external-edit merging, document placement or Subject assignment
- document/Links builds, watcher suppression, Search rebuilding or viewer-refresh waits during Save
- staged import conversion
- route path constants

## Editor Selection

`DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP` in `.env.local` wins when set. Without that setting, default editor selection checks:

```text
MarkEdit
Typora
Marked 2
Marked
```

If none are installed, macOS Launch Services chooses the default application for the Markdown file.

## `docs-viewer/runtime/js/management/source-editor/source-editor.js`

Purpose: own the exact mounted Working target, loaded front matter, body, Title/Summary and pending token occurrence edits as one session. The session owns dirty/busy state, complete validation, a single Save and one leave/discard decision.

**Edit document** opens this session with the metadata panel visible. It targets the ordinary document, the report host from a collection list, or the exact validated document from a collection detail. A detail does not offer a separate parent Source action. Open in VS Code retains its separate action.

`source-metadata-view.js` binds Title/Summary inputs to the session. `source-editor-token-drafts.js` retains raw occurrence values outside panel mounts, rebases unaffected ranges after body changes and prepares validated replacements for Save. `catalogue-token-info-view.js` supplies the selected occurrence's fields. Closing or switching the panel cannot discard pending input; a failed validation or source write retains the draft.

Source mounts beside the existing rendered DOM, which management CSS hides while editing. It does not detach the collection report or end its lifecycle. Successful Save removes the editor and returns to the existing rendered view immediately. [Runtime](Docs_Viewer_Runtime.md#automatic-working-refresh) owns the independent polling that later refreshes generated content and Info while retaining the report toolbar.

For local-folder authoring it reads the latest runtime capability only during a `paste` event. A recognized replacement is applied to the current range and emits the normal dirty-buffer `input` path. Conversion is silent and does not implement or intercept Undo.

Registered contributions now provide **Insert doc link**, **Add Media View link** and **Add Catalogue Image**. **Add Catalogue Token** and **Insert Subject Link**, their exclusive handlers and their old text-token serializer are retired. Subject metadata retains its independent read/assignment owners.

## Directives

`directive-actions.js` owns the captured-range Directives menu. **Insert icon** inserts `[[icon:refresh-cw]]` inline and selects `refresh-cw` for manual filename-stem editing. It adds no line breaks and preserves any selected source text after the new token. The existing Table detail directive retains its block insertion.

**Insert related links** inserts `[[links|related links]]` as a block directive and selects its plain-text heading for editing. It preserves selected source text after the token. [Related Links](Related_Links.md) owns the generated sorted list, icons, empty-section suppression and full-build freshness.

Insertion changes only the dirty buffer through the current Source adapter and revision guard. Save persists source; the watcher independently generates the document. [Icon Tokens](Icon_Tokens.md) owns exact SVG lookup, portable rendering, literal examples and export behaviour.

## Insert Doc Link

**📄 Insert doc link** is a Source contribution in `docs-viewer/runtime/js/management/source-editor/document-link-contribution.js`; `document-link.js` owns response validation, collection filtering, literal Markdown encoding and guarded insertion.

The mounted source adapter requests the management client's read-only `GET /docs/document-link-targets` endpoint without stage context. `docs-viewer/services/docs_document_link_targets.py` reads ordinary and configured collection identity/title metadata through the source and location owners. Draft/readiness validity, ordinary ignore membership, inherited publication exclusion, prepared-document membership and Subject metadata do not filter target discovery. The picker does not load full document/report models or read publication policy. It retains exact identity, source-filename agreement, symlink rejection, path confinement and configured collection hosts; unavailable collections and malformed target identities fail visibly. This selection does not rewrite existing links or restrict typed/pasted references.

The picker filters all documents, ordinary documents or an exact configured collection, with title or immutable-ID search. Selection identifies `{collection, doc_id}` explicitly, with an empty collection for ordinary documents; titles and Subject metadata do not select a target. Configuration supplies collection report hosts and portable document hrefs. Public providers expose no local target-lookup capability.

Insertion uses the selected document's title as escaped literal link text and its supplied href. It replaces the captured selection or inserts at the captured cursor, provided that the same editor remains mounted and its buffer revision is unchanged. This changes the dirty buffer only; Save owns the combined source write. It does not automatically save or maintain relationships. Build preserves explicit collection destinations, fragments and HTML escaping when rewriting local document links; external URLs, including protocol-relative URLs with a hostname, retain their authored destination.

The watcher observes the source write and independently invokes targeted document generation and the [Builder's relationship maintenance](Builder.md). Inserted, typed and pasted document links receive the same Build treatment. [Related Links](Related_Links.md) expands the refreshed records into generated content; the Source contribution does not write relationship JSON. Search remains separately requested.

## Catalogue Media And Image Contributions

`catalogue-media-link.js` authors explicit `catalogue:media:work` tokens from generated Catalogue Work targets. `catalogue-image-modal.js` uses those targets and exact generated Work Details for image insertion. Both retain captured Source mutation, Catalogue-owned selection and validation of the selected current media presentation; neither requires a related document.

`catalogue-token-parser.js` owns the supported explicit Catalogue `media` and `image` forms, source ranges and serializers. `catalogue-token-contribution.js` contributes the Catalogue context resolver. `catalogue-token-info-view.js` edits occurrence fields through the mounted session's token drafts; it has no separate Update or persistence operation. The immutable target stays fixed, and Save validates all pending occurrence fields before writing. [Semantic Tokens Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) describes the interaction.

The old three-part Catalogue text grammar has no compatibility alias. Its exclusive Source action, Subject-link contribution, rendering and audit branches, validation transport and fixture-only tests are removed. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) records the retained Build/runtime boundary.

## `docs-viewer/runtime/js/management/source-editor/local-folder-links.js`

Purpose: own browser-side local-path recognition, canonical Markdown encoding, Markdown-context exclusion, and rendered Manage activation.

The module accepts only one exact supported absolute path below the supplied base. It performs no shell, variable, home, filesystem, or existence expansion. Paste authoring does not require the target to exist. Rendered activation uses the local-link service's existing confinement and existence checks before opening the exact folder.

Its delegated rendered-link handler sends only the canonical encoded relative target through the management client; it supplies no scope, document, selected parent, label, URL, or fallback target.
