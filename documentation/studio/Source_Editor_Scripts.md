---
draft: false
doc_id: d-20260607-222033-704641
title: Source Editor Scripts
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-17"
parent_id: d-20260607-222033-2a494e
---
# Docs Viewer Source Editor Scripts

## `docs-viewer/services/docs_management_source_service.py`

Purpose: read and save one complete Source session, plus local editor open helpers.

Ownership: owns the source-editor API contract and local source-open behavior.

Responsibilities:

- resolves exact Working document targets through the configured workspace and collection owners, reading ordinary Index membership/parent information and only the selected source
- confines source paths to their configured roots and checks immutable document identity
- reads and saves the complete Markdown through `source_text`, including front matter and body
- parses the candidate once through the source model's strict splitter, retains field spans and applies Title/Summary string representation, readiness, exact collection, report and Subject rules before one atomic write; the frontend owns nonblank Title feedback
- preserves unaffected authored metadata lines, normalizes Title/Summary and applies the normal source timestamp on changed writes
- normalizes body line endings and Unicode-whitespace-only prose lines outside literal blocks
- consumes Source Save's bounded selected uploads, prepares media once under the resolved document owner, completes selected writes before source persistence and reports exact media/source/generation effects on failure
- projects the validated unsaved buffer's Subject through a write-free context request for Catalogue modals
- prepares Subject-only front-matter changes in that unsaved buffer through the same context endpoint, using the exact collection's registered assignment group and shared field writer
- carries prepared source, metadata, report, dates and ordinary parent information into the existing in-process exact document/Links builder through `docs_document_rebuild.py`, without reopening the saved source or rediscovering its ID; saved-source and generation outcomes remain separate
- opens source docs with the configured or preferred local Markdown editor
- logs open-source events

Not responsible for:

- source-revision checks, external-edit merging or document placement
- Search rebuilding, unrelated registered media production, Publish or browser display during Save
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

Purpose: own the exact mounted Working target and one complete Markdown buffer, including front matter. The session owns dirty/busy state, a single Save and one leave/discard decision; the service owns candidate validation, persistence and exact generation; the editor awaits fresh display.

**Source editor** in Edit opens the complete buffer without a side panel. It targets the ordinary document, the report host from a collection list, or the exact validated document from a collection detail. A detail does not offer a separate parent Source action. Source's toolbar contains Return to doc, Save Markdown source and Directives, in that order, on one row beginning at the document's left edge. VS Code remains in Edit for rendered documents and is also available inside Source's Directives menu using the adapter's immutable document target.

Title, Summary and other valid authored fields are edited directly in the same buffer. Save submits that text with the fixed target and only selected pending native Files. The mounted `source-editor-pending-media.js` owner retains Files through text edits/Undo, joins them to active final-buffer references and independently selects the latest requested thumbnail while its assignment remains. Pending replacement bytes or a thumbnail choice make unchanged text dirty. Removing a pending reference before first Save submits no body image; a retained thumbnail can request thumbnail-only output. An identity conflict, malformed header, invalid collection metadata or write failure retains the draft and useful Files. Successful media/source completion clears pending Files even if later generation fails; discard and release also clear them. Ordinary hierarchy/order stays with `index-order.json`. There is no metadata draft, pending token-field draft, Source hosted panel or **i** control. Entering Source releases the captured reader panel; returning to rendered content leaves it closed until a related-links pin is used.

The exact splitter lives in `docs_source_model.py`, including the strict key/value and quoted-scalar checks used by Source and existing Import/Review consumers. Save retains the parsed field spans for formatting, membership and timestamp changes and supplies its completed report classification to generation. It uses the maintained front-matter value grammar rather than YAML. `source-buffer.js` locates the body boundary and gives narrow local Title feedback before Save, handling quoted text, numeric/boolean scalar forms and Summary literal-block boundaries; complete front-matter syntax remains service-owned. The modal's write-free context request projects the current buffer's Subject through the service and the owning collection customisation.

New ordinary, child, sibling and non-Catalogue collection documents use the same required Title modal, initially containing `New Doc`; clearing it asks for a Title rather than restoring a default. Repeated titles are valid. The server requires a string without another completeness check or fallback, constructs a draft source and carries its known ID/source and updated ordinary tree into exact generation. Ordinary creation retains its generated Index refresh before opening Source. A committed creation whose build failed retains its exact target and generation error while attempting to open Source; later presentation failure reports both outcomes. Recovery uses Source correction or explicit Rebuild, without retrying Create.

Source context uses `docs_document_subjects.py`'s complete authoring projection, including Folder and Work, with omission for None. The public Work-only projection remains separate. Source loading supplies initial Subject/capabilities or a projection error without blocking the editor. Assign Subject and Catalogue modals share context for the exact buffer revision and coalesce in-flight reads. Buffer changes and editor release invalidate it; successful Subject Apply seeds the resulting revision. Failed requests remain retryable and late responses cannot replace a newer result. Catalogue shortcuts accept Folder responses while selecting Work only.

Source load also supplies `media_options.image` and `media_options.file`, each with accepted suffixes and file/aggregate/metadata byte limits. The mounted editor carries them into `source-editor-media.js` and releases them with the session; buffer edits need no capability refresh. Add/Edit makes no options request. Presentation-only Apply serializes locally. New selected files make a write-free identity request containing the fixed target, kind and basename; the browser retains the File and serializes its image/file reference locally. Add file over a captured authored file link opens Edit file and carries explicit replacement intent, like Edit image. A pending image's already selected File can supply a later thumbnail choice without another identity request. Source Save alone submits bytes, validates the full candidate, prepares and persists selected media, saves source and awaits exact generation. There is no Replace/sanitizer confirmation workflow, persistent upload staging or automatic split/retry. [Media And Asset Handling](Media_And_Asset_Handling.md) and [Source Editor Endpoints](Source_Editor_Endpoints.md) own storage and transport.

Source mounts beside the existing rendered DOM inside the common reader's active `.docsViewer__documentMount`. Management CSS keeps that mount and the editor visible while hiding only the mount's rendered children; inactive retained document mounts stay hidden. It does not detach the collection report or end its lifecycle. Successful Save awaits a fresh generated payload, removes the editor and refreshes the current retained mount while preserving its route, history and reading position. Persistence, generation and display failures remain distinct; persisted source is marked clean even when generation fails. [Runtime](Docs_Viewer_Runtime.md#explicit-working-refresh) owns application completion and explicit external-change refreshes; no browser timer remains.

For local-folder authoring it reads the latest runtime capability only during a `paste` event. A recognized replacement is applied to the current range and emits the normal dirty-buffer `input` path. Conversion is silent and does not implement or intercept Undo.

The Directives menu provides **Add image**, **Add Catalogue image**, **Add file**, **Add Media View link**, **Insert doc link**, **Assign Subject** and **Open in VS Code**, followed by a separator and the existing directive insertion items. Source loaded/busy state and management availability gate this flat menu. Assign Subject uses the exact collection's registered capability supplied on Source load. Opening Directives makes no Subject-context request. Retired Catalogue-token and Subject-link actions remain absent.

**Assign Subject** uses `source-editor/subject-modal.js` and the current complete buffer. It uses the editor's shared context; after a buffer change the first consumer requests `/docs/source/context`. Work selection uses generated Catalogue targets; None clears `folder_path` and `work_id`. The exact owner's `folder_subject_supported` controls Folder authoring. Folder input accepts a decoded relative path, absolute path or file URL beneath Projects; its normaliser returns a canonical relative path and clears Work. Apply requests a write-free rewrite and changes the captured buffer only while the adapter/revision remain current. The service parses once, binds identity and consumes the normalized choice without Source Save validation, another full parse or an unused old/new comparison. The writer preserves unrelated front matter, body and timestamps. Apply retains selection/scroll, marks changed text dirty and seeds the returned context. Cancel preserves the buffer; Save owns complete candidate validation, persistence and generation. [User Facing Rules](data/User_Facing_Rules.md) D.11/M.14 records the current simplification.

Folder opening is available through [Projects](/docs/?doc=d-20260805-155400-4c341f). Open Subject folder and its menu-only action, Source adapter methods and workspace-provider opener bridge are removed. Ordinary local-folder links and report-owned folder opening retain their existing request and confinement owners.

## Directives

`directive-actions.js` owns the Source action menu, its disclosure, keyboard navigation and captured adapter/range. Opening the menu captures the current selection before moving focus; choosing an action closes it before opening a modal or invoking a workflow. Catalogue image/Media View and document-link items reuse their existing modal owners with that capture. Add image/file calls the mounted adapter's `addStagedMedia` operation, which keeps Source busy through the existing media workflow and inserts using the captured range and revision. VS Code invokes the existing management source-opening workflow with the captured adapter's exact target; it does not save the buffer. The old standalone insertion-control definitions/renderers and image/file dispatch events are retired.

The final menu group contains Table detail, Insert related links, Insert icon and **Summary**, in that order. **Insert icon** inserts `[[icon:refresh-cw]]` inline and selects `refresh-cw` for manual filename-stem editing. It adds no line breaks and preserves any selected source text after the new token.

**Table detail** inserts `<!-- dotlineform:table-detail title="Table" -->` as a block and selects `Table` for editing. Place the directive immediately before its Markdown table, with optional blank lines between them. The optional double-quoted title is plain text; use `&quot;` for a quote within it. The shared Markdown renderer decodes HTML entities and carries the title in `data-docs-content-detail-title`, using its existing escaped attribute rendering. The browser displays the authored title, preserving capitalisation, in the expanded view, Open tooltip and accessible labels. An empty `title=""` or a directive without a title displays `Table`. There is no automatic numbering or required-title validation; internal table identifiers distinguish tables independently of their titles. Normal Source Save owns persistence and exact generation. [Table Detail Titles](deliveries/Table_Detail_Titles.md) records the delivery and evidence limits.

**Insert related links** inserts `[[links|]]` as a block directive with an empty heading and places the caret between `|` and `]]` for optional heading text. It preserves selected source text after the token. [Related Links](Related_Links.md) owns the generated sorted list, icons, empty-section suppression and full-build freshness.

**Summary** uses the local `summary.svg` toolbar mask and inserts `[[summary]]` as a standalone block, supplying the blank-line separation needed around surrounding prose and preserving selected text after the token. It opens no modal and changes no front matter. [Builder](Builder.md#summary-block) owns expansion of the document's current Summary, empty-block suppression and presentation.

Insertion changes only the dirty buffer through the current Source adapter and revision guard. Save persists source, awaits exact generation and displays the fresh result. [Icon Tokens](Icon_Tokens.md) owns exact SVG lookup, portable rendering, literal examples and export behaviour.

## Insert Doc Link

**📄 Insert doc link** is a Source contribution in `docs-viewer/runtime/js/management/source-editor/document-link-contribution.js`; `document-link.js` owns collection filtering, literal Markdown encoding and guarded insertion. The contribution consumes service records directly without response schema, collection, duplicate, target/href-agreement or Title completeness audits. The removed response-normalization helper has no alias.

The mounted source adapter makes one read-only `GET /docs/document-link-targets` request when the picker opens. The client, source adapter and workspace provider carry no collection target or query; discovery always supplies every configured owner. `docs-viewer/services/docs_document_link_targets.py` selects ordinary sources from Index IDs and lists only direct-child Markdown sources for each flat collection. It confines and reads each selected source once and uses the shared front-matter field parser without invoking full source-model or Subject validation. The preliminary recursive source audit is removed. Draft/readiness validity, ordinary ignore membership, inherited publication exclusion, prepared-document membership and Subject metadata do not filter target discovery. Stored titles are consumed literally without coercion, completeness checks or ID-derived fallback. Source-filename agreement, symlink rejection, path confinement, canonical route identity/encoding and actual file/parser failures remain with their owners. This selection does not rewrite existing links or restrict typed/pasted references.

The picker filters all documents, ordinary documents or an exact configured collection, with title or immutable-ID search. Filtering, selection and Insert consume the loaded response without another lookup or publication-policy read. Selection identifies `{collection, doc_id}` explicitly, with an empty collection for ordinary documents; titles and Subject metadata do not select a target. Portable document hrefs address that exact owner and document independently of report-host placement. Draft or excluded destinations remain available without a public-omission warning; links do not confer publication eligibility. Public providers expose no local target-lookup capability.

Insertion uses the selected document's title as escaped literal link text and its supplied href. It replaces the captured selection or inserts at the captured cursor, provided that the same editor remains mounted and its buffer revision is unchanged. This changes the dirty buffer only; Save owns the combined source write. It does not automatically save or maintain relationships. Build parses a rendered link's query once and preserves explicit collection destinations, fragments and HTML escaping when rewriting local document links; external URLs, including protocol-relative URLs with a hostname, retain their authored destination.

Source Save awaits exact document generation and the [Builder's relationship maintenance](Builder.md) before fresh display; the filesystem watcher is retired. Inserted, typed and pasted document links receive the same Build treatment. [Related Links](Related_Links.md) expands the refreshed records into generated content; the Source contribution does not write relationship JSON. Search remains separately requested, and Broken Links owns explicit destination diagnosis.

## Catalogue Media And Image Contributions

The Directives menu's Catalogue items author explicit Work/Gallery Media View tokens and Work images through `catalogue-media-modal.js` and the same generated Catalogue picker. Selection and Apply consume the loaded exact ID/title without requesting a Work/Gallery record, media policy, membership or Series–Gallery index. Token syntax and captured-buffer guards remain local; document Build and rendered activation own their required Catalogue reads. Neither authoring form requires a related document. Their former standalone toolbar wrapper modules are retired.

Add/Edit Catalogue image, Add/Edit Media View link and Assign Subject select the shared picker's `id-title` layout: the exact Work/Gallery ID is the first column in the same light grey as the search icon and the smaller caption font size, followed by its title, with no type label or subtitle. IDs retain their leading zeroes. `catalogue-target-picker.js` keeps Work/Gallery type in selection identity while omitting its visible label in this layout; the document-link caller uses its existing presentation. The Work year remains in the shared lookup for its other consumers. Styling is local-only in `docs-viewer/static/css/docs-viewer-source-editor.css`.

`semantic-token-targets.js` ignores leading zeroes in numeric ID searches: `8`, `008` and `00008` all match Work `00008`; `work:8` and `gallery:8` support type-qualified searches. Exact numeric matches rank above ID-prefix and title matches. Title matching retains its existing rules. The shared matcher also supplies Work-subject selection. Normalisation affects search comparisons only; displayed IDs, selection identity and saved tokens retain the exact canonical strings.

`catalogue-token-parser.js` owns the supported explicit Catalogue `media` and `image` forms, literal-context exclusions, ranges and serializers. `catalogue-token-contribution.js` captures a corresponding occurrence only when its explicit action is used with the caret inside it or its exact range selected. Recognition is limited to the body; ranges include the current front-matter offset. The shared modal initializes every authored field and the stored target, allows target changes through its existing picker, and uses **Apply** to replace only that occurrence in the unsaved buffer. Creation keeps its insertion action. Cancellation and failed validation retain source unchanged; unavailable picker targets cannot be selected. The token registry and generated target lookup use browser HTTP revalidation with `no-cache`, consistently with other Catalogue configuration/data reads; there is no retained payload cache in the modal.

Captured text/range, buffer revision and mounted adapter guard Apply. A replaced editor cannot mutate a new session, even when its buffer and revision match. Work-derived title/alt updates do not reset stored image choices or link text. The serialized token becomes authoritative immediately; Save has no later token-draft serialization. [Semantic Tokens Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) describes the interaction.

Current Source service and browser tests still contain retired scope/revision or body-only contracts and are unreviewed for this workflow. This delivery uses explicit-path lint, Python syntax, bounded source review and shared-runtime projection/validation. Live Save failure/atomic-write behavior, Import/Review flows and editor/modal interaction are not automated evidence; test changes require a separately agreed specification under [Testing](Testing.md).

The old three-part Catalogue text grammar has no compatibility alias. Its exclusive Source action, Subject-link contribution, rendering and audit branches, validation transport and fixture-only tests are removed. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) records the retained Build/runtime boundary.

## `docs-viewer/runtime/js/management/source-editor/local-folder-links.js`

Purpose: own browser-side local-path recognition, canonical Markdown encoding, Markdown-context exclusion, and rendered Manage activation.

The module recognizes one exact supported absolute path below the supplied Projects or Docs workspace base. Unqualified `dlf-local:<encoded-relative-path>` targets belong to `DOTLINEFORM_PROJECTS_BASE_DIR`; `dlf-local:docs:<encoded-relative-path>` targets belong to `DOTLINEFORM_DOCS_BASE_DIR`. Each root has one maintained target form; an absolute path is never stored in the token. Paths matching both supplied roots retain normal paste behavior. The module performs no variable, home, filesystem, or existence expansion. Paste authoring does not require the target to exist. Rendered activation uses the local-link service's canonical path validation, exact configured root, existence and resolved-path confinement before opening a directory or revealing a file in Finder. An unavailable selected root fails without fallback. Preview renders either form as plain text.

Its delegated rendered-link handler sends only the canonical target, including the `docs:` selector when present, through the management client; it supplies no scope, document, selected parent, label, URL, or fallback target. The document renderer and activation service share `docs_local_links.decode_local_link_target`; Project-owned Subject fields continue using the separate Projects-relative path grammar.
