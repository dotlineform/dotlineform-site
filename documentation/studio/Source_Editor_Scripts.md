---
draft: false
doc_id: d-20260607-222033-704641
title: Source Editor Scripts
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-01 17:58:55"
parent_id: d-20260607-222033-2a494e
---
# Docs Viewer Source Editor Scripts

## `docs-viewer/services/docs_management_source_service.py`

Purpose: read and save one complete Source session, plus local editor open helpers.

Ownership: owns the source-editor API contract and local source-open behavior.

Responsibilities:

- resolves exact Working document targets through the configured workspace and collection owners
- confines source paths to their configured roots and checks immutable document identity
- reads and saves the complete Markdown through `source_text`, including front matter and body
- uses the source model's strict splitter, required Title/readiness rules, exact collection contract and Subject customisation before one atomic write
- preserves unaffected authored metadata lines, normalizes Title/Summary and applies the normal source timestamp on changed writes
- normalizes body line endings and Unicode-whitespace-only prose lines outside literal blocks
- projects the validated unsaved buffer's Subject through a write-free context request for Catalogue modals
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

Purpose: own the exact mounted Working target and one complete Markdown buffer, including front matter. The session owns dirty/busy state, a single Save and one leave/discard decision; the service owns candidate validation and persistence.

**Edit document** opens the complete buffer without a side panel. It targets the ordinary document, the report host from a collection list, or the exact validated document from a collection detail. A detail does not offer a separate parent Source action. Open in VS Code retains its separate action.

Title, Summary and other valid authored fields are edited directly in the same buffer. Save submits only that text with the fixed target; an identity conflict, malformed header, invalid collection metadata or write failure retains the full draft. Ordinary hierarchy/order stays with `index-order.json`. There is no metadata draft, pending token-field draft, Source hosted panel or **i** control. Entering Source releases the captured reader panel; returning to rendered content leaves it closed until a related-links pin is used.

The exact splitter lives in `docs_source_model.py`, including the strict key/value and quoted-scalar checks used by Source and existing Import/Review consumers. It uses the maintained front-matter value grammar rather than YAML or a separate browser field parser. `source-buffer.js` locates only the body boundary for buffer contributions; it does not interpret metadata. The modal's write-free context request projects the current buffer's Subject through the service and the owning collection customisation.

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

`catalogue-media-link.js` authors explicit Work/Gallery Media View tokens. `catalogue-image-contribution.js` authors Work images. Both use `catalogue-media-modal.js`, the same generated Catalogue picker and validation of the selected current media presentation; neither requires a related document.

`catalogue-token-parser.js` owns the supported explicit Catalogue `media` and `image` forms, literal-context exclusions, ranges and serializers. `catalogue-token-contribution.js` captures a corresponding occurrence only when its explicit action is used with the caret inside it or its exact range selected. Recognition is limited to the body; ranges include the current front-matter offset. The shared modal initializes every authored field and the stored target, allows target changes through its existing picker, and uses **Apply** to replace only that occurrence in the unsaved buffer. Creation keeps its insertion action. Cancellation and failed validation retain source unchanged; failed media reads retain the stored identity and entered fields.

Captured text/range, buffer revision and mounted adapter guard Apply. A replaced editor cannot mutate a new session, even when its buffer and revision match. Work-derived title/alt updates do not reset stored image choices or link text. The serialized token becomes authoritative immediately; Save has no later token-draft serialization. [Semantic Tokens Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) describes the interaction.

Current Source service and browser tests still contain retired scope/revision or body-only contracts and are unreviewed for this workflow. This delivery uses explicit-path lint, Python syntax, bounded source review and shared-runtime projection/validation. Live Save failure/atomic-write behavior, Import/Review flows and editor/modal interaction are not automated evidence; test changes require a separately agreed specification under [Testing](Testing.md).

The old three-part Catalogue text grammar has no compatibility alias. Its exclusive Source action, Subject-link contribution, rendering and audit branches, validation transport and fixture-only tests are removed. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) records the retained Build/runtime boundary.

## `docs-viewer/runtime/js/management/source-editor/local-folder-links.js`

Purpose: own browser-side local-path recognition, canonical Markdown encoding, Markdown-context exclusion, and rendered Manage activation.

The module accepts only one exact supported absolute path below the supplied base. It performs no shell, variable, home, filesystem, or existence expansion. Paste authoring does not require the target to exist. Rendered activation uses the local-link service's existing confinement and existence checks before opening the exact folder.

Its delegated rendered-link handler sends only the canonical encoded relative target through the management client; it supplies no scope, document, selected parent, label, URL, or fallback target.
