---
draft: false
doc_id: d-20260903-154141-7c9e4b
title: Catalogue Media View
added_date: "2026-09-03 15:41:41"
last_updated: "2026-10-20"
summary: Exact Work and Gallery links, direct and Series-related Gallery navigation, responsive Work images and paginated Media View, with static-consumer and public-data limits.
ui_status: done
parent_id: d-20260903-222617-28475e
---
# Catalogue Media View

## Purpose

Media View presents an exact Catalogue Work or Gallery inside the Docs Viewer main pane. Authors can open these through a text link or insert a Work image that opens the same view. Catalogue owns identity and media; the invoking document supplies browsing context. A Context document or document Subject is not required. Work image, Entry and Media View references contribute relationships to the Work's Catalogue document through the shared [Related Links](Related_Links.md) graph; Gallery references and self-references add none. Series remains a Catalogue grouping, without a document Subject or Media View target.

The Gallery conversion retired canonical Details. Detail subject assignment, token syntax, image selection, Info fields, report support and media readers are removed, with no old-to-new aliases. Work images and Work or Gallery text links are the supported Catalogue media forms. Series Media View links and galleries are retired without an alias.

## Authoring

**Add Media View link** searches generated Catalogue Work and Gallery titles or identities through the shared Catalogue image modal. Result rows show the exact `work_id` or `gallery_id` first in grey, then the title, without a `work`/`gallery` label or year/count subtitle. Gallery results come from the Refresh-owned `galleries/galleries_index.json` ID/title rows. Selection and Apply use those loaded identities and titles without resolving images, Gallery membership or Media View presentations. Selected or edited text remains the editable label; an untouched default follows the chosen record title. The source forms are:

```text
[[catalogue:media:work:00523|kylie structure 4]]
[[catalogue:media:gallery:179|kylie structure 4 (details)]]
```

The authored label remains literal text and does not change when the Catalogue title changes. The rendered opener is a keyboard-accessible button styled as inline link text, with no invented navigation URL. Work text links retain their existing form; unqualified Catalogue text and all Series token forms are retired without aliases. Existing authored Series tokens remain unchanged in Working source and render as literal text after rebuild.

Gallery IDs use the exact canonical spelling: three digits, or at least four digits without a leading zero. Gallery tokens allow no image presentation. Add/Edit Media View link inserts `catalogue:media:gallery` using the loaded target identity/title, and Broken Links separately checks the exact generated Gallery record. Subject assignment offers None, Work and, where the collection supports it, Folder. Series document Subjects were retired on 2026-10-03; Gallery tokens do not imply a new document Subject kind.

**Add Catalogue Image** searches Catalogue Works and uses the selected Work's image. Its result rows use the same grey ID-first presentation, without the `work` label or `year_display` subtitle. Add and Edit modes share this presentation. Its token stores the Work-title caption choice, optional static summary, placement and width settings:

```text
[[catalogue:image:work:03072|use_work_title_caption=true&placement=full&fill_width=true]]
```

Add/Edit Catalogue image and Media View link update only the captured Source range after local token serialization and buffer/editor checks. They make no selected-record or media-policy request. Registry and generated-target reads use HTTP revalidation with `no-cache`; the optional Use document subject context request retains its separate owner. Source Save persists the full buffer, awaits exact document/Links generation and displays the fresh result. Cancellation leaves the buffer unchanged.

## Document Build And Presentation

Image opener accessibility labels use `Open <Work title>` in live Manage, prepared public content and static snapshots. The browser renderer and shared Python preparer consume the supplied resolved title and retain their existing escaping.

Catalogue Entry physical dimensions use compact decimal display: `21.0 × 29.7` renders as `21 × 29.7 cm`, preserving fractional values without rounding. Manage's live provider and the shared Python static preparer own that formatting; authoring/import retains numeric validation. Entry resources retain downloads followed by links in supplied order and with supplied labels.

Document Build emits exact ordered Catalogue references and HTML slots, retaining authored caption enablement, restricted summary HTML, placement, width and link labels. It reads no Work record for presentation and bakes no Work-derived title, alt text, dimensions, URLs, Entry resources or relationships. A Work has `catalogue-work` identity and its five-digit ID; a Gallery has `catalogue-gallery` identity and its exact canonical Gallery ID. Gallery entry remains a text link in document content; thumbnail grids exist only inside Media View. [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation) owns the envelope and presentation fields.

Text links preserve surrounding Markdown even at the start of a paragraph or list item. Authored labels remain escaped literal text. Work images are block-level figures, including when their visible title caption is omitted; any authored summary remains available. Without a title-caption or summary, Build omits the figcaption.

Manage document activation resolves Work-derived Entry, image and caption values through its live Working provider without a referring-document Build. For documents containing Catalogue Image or Entry references, the document body stays hidden until those existing presentation requests complete and their markup includes intrinsic width/height. Distinct Works resolve in parallel with the operation's existing read reuse. The body is then revealed and image downloads proceed into the reserved layout. No timer, polling, image-download wait, token dimension copy or generation-time Work read is involved. Documents without inline Catalogue images retain ordinary display.

The [Catalogue mounter](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-rendering.js) returns separate `ready` and `release` handles. The media adapter registers disposal before awaiting work and reports whether the completed mount remains current. The [document controller](../../docs-viewer/runtime/js/shared/docs-viewer-document-controller.js) owns visibility for fresh render, Source Save redisplay and retained/Back activation; navigation awaits restoration before capturing state or restoring scroll/focus. Work lookup failures settle into the existing per-reference error/Retry UI and permit the document to appear. Released or superseded mounts cannot reveal another document. This sequencing changes the Manage browser lifecycle only; Working payloads remain reference-only.

Text-only Catalogue links render their authored labels immediately without an eager Work presentation read. Media View activation resolves current Work inputs; simultaneous reads and values within one operation are reused. Public binds complete prepared markup and embedded Work presentation without a Work-record, policy or Series–Gallery lookup. Selecting a Gallery reads its membership/thumbnail inputs lazily; selecting a Work from it reads that Work's prepared Catalogue document. Retired Detail and Series markers do not open Media View.

The 2026-10-20 readiness change passed focused lint for the four changed shared JavaScript owners, whitespace review, tracked projection/check and deploy-root validation. The projection changed exactly four runtime copies; validation covered 104 projected code files and 71 Docs Viewer runtime modules. Distinct source/redundancy review traced initial/restored/Save display, repeated Works, handled failures/Retry, disposal, text-only references and prepared public binding. The user accepted the implementation and requested closeout on 2026-10-20; individual manual scenarios were not itemised, and further confirmation continues through ordinary use. Codex did not run tests, browser layout/navigation, live Source Save or request-failure interaction. The delivery required no backend, token/schema or media changes, document Build, Search, Refresh or Publish.

Work Media View shows the selected image, title, `cat. <work_id>` reference and Gallery links. Direct Gallery links precede a separate related group from Series–Gallery relationships. `cat.` is plain text and only the five-digit Work ID links to the definitive Catalogue document at `?collection=catalogue&doc=<work-id>`, opened in a new tab. The `docs_media_view_v2` contract omits the former unused descriptive metadata array; Entry fields are independent. Open in new tab targets the supplied selected image. Back to document restores the invoking document, scroll and focus through Content Detail.

Media View centers Back and Open in new tab together in the top row, using the same shared CSS grid as image detail. Home stays on the left; Manage Actions and the theme control stay on the right. This layout applies to local and public views, including narrow public screens, without positioning Open against the image/metadata columns.

Work and Gallery information uses `font-small`, normal upright text and the standard text colour. Its title retains the established bold `font-body` size, without the document H2 divider or padding. Component rules are scoped within `docsViewer__content` so generic figure-caption and heading styles do not override this presentation.

Build retains valid references independently of Work availability. Manage resolves required current inputs at activation; static preparation fails when a selected required input is unavailable. Both consume the UI-completed Work title without another nonblank check or fallback title. Runtime failure feedback remains beside the opener and permits retry. Replaced documents, released mounts, changed child selections and superseded requests cannot apply a late response.

## Current Catalogue Data

The source of consumer records is `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/works/index/<work_id>.json`, as described by [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md). Work records supply identity, optional exact `series_id`, `media_version`, `width_px`, `height_px` and direct Gallery memberships. The separate generated `series-galleries-index.json` supplies explicit links for every valid Series; `media-config.json` supplies shared rendition policy. Per-record media arrays and per-Work related Gallery arrays are not used. Docs consumers require only the Work image base and do not read Detail sections or resolve Detail image paths. Identity is never inferred from a filename, title, document or selected UI row.

Local Docs reads the current generated record through `/docs/catalogue-work?work_id=<work_id>`, shared policy through `/docs/catalogue-media-config` and, for a Work with a Series, the exact mapping through `/docs/catalogue-series-galleries`. That live provider resolves local Working image/download URLs. Python static preparation resolves current Working records against their public policy and embeds complete presentation. Public's provider has no Work-record or Series–Gallery reader; its policy route remains for Gallery and other thumbnail consumers. Physical Catalogue Work/relationship JSON distribution remains unchanged pending separate consumer review and agreed removal scope.

Each live operation requests current Working data with HTTP revalidation, reusing its distinct Work, policy and required relationship reads. Later document or Media View activation creates a new operation. Public Work values reflect the prepared document's publication; ordinary image loading retains current object locations and browser behavior. Neither provider adds mutation subscriptions, a completed live presentation cache across activations or a legacy reader fallback.

The media readers consume valid Refresh-owned Catalogue output without complete Gallery-index, member, Series–Gallery-map, ordering, uniqueness or title-completeness audits. The Work projector selects only its exact Series entry and combines direct and Series-related Galleries, retaining the existing deduplication needed for that combined display. Request/response identity, required consumed representation, media version, confined paths, escaping and URL safety remain. Browser rendition-policy safety is checked once when its provider reads the policy; candidate and thumbnail helpers consume that checked policy. Presentation constructors return their prepared payload without a discarded validation pass, and the consuming image/Media View renderer performs presentation conversion. Intrinsic pixels and derived candidate widths retain Save's measurements without revalidation or fallback sizes. Work and Gallery labels retain their supplied strings; Year display and optional Medium retain their supplied text, and optional physical dimensions retain each supplied value. Missing required data fails visibly without a partial-list fallback. [Broken Links](Broken_Links_Script.md) separately owns requested availability/record audits; normal browsing does not perform them.

`docs-viewer-catalogue-media-policy.js` resolves configured candidates and thumbnail naming. Width descriptors reflect actual output dimensions, including sources below a configured target, and duplicate widths are removed. `docs-viewer-responsive-image.js` sets `srcset` and a pixel `sizes` value measured from the displayed image slot before loading; a ResizeObserver updates it as layout changes. In-document images retain their authored placement and width. Media View constrains width by its image column, source dimensions, viewport height and aspect ratio. The browser chooses a candidate for the measured slot and display density. Open in new tab and token Info image links always use the largest configured rendition, currently 1600, independently of that choice. Supplied demonstration presentations with a single explicit image remain separate supported callers.

## Ownership

| owner | responsibility |
| --- | --- |
| Catalogue generated consumer output | supply exact Work records, direct Gallery membership, explicit Series–Gallery mapping, the Gallery search lookup and existing Work thumbnails independently of documents |
| Source authoring and Document Build | preserve selected identity, literal labels and authored image presentation |
| Manage live provider | resolve current selected Working Work/policy/relationship inputs into `docs_media_view_v2` |
| static preparer / public provider | prepare selected complete markup and embedded Work presentations; public consumes those values and navigates to prepared Catalogue documents |
| shared Catalogue browser renderer | mount live Entry/image/caption values or bind complete public markup, responsive images and provider-driven Media View; retain `docs_media_gallery_v1` Gallery references |
| shared gallery helper | own density, page membership, complete-order neighbours and wrapping |
| Media View adapter | register the current occurrence, load selected Works, render the active gallery page or image, preserve the return page, reject late results and release state |
| Docs Viewer Content Detail | main-pane lifecycle, Back and Open in new tab controls, scroll and focus restoration |
| public and Manage entrypoints | compose the same shared adapter |
| Broken Links | read source tokens and diagnose current generated media availability without mutating content |

The implementation owners are `docs-viewer/services/docs_catalogue_media.py` for local saved inputs, `docs_catalogue_static.py` for selected static preparation, `docs_builder/semantic_tokens.py` for authored references, the management-only `docs-viewer-catalogue-live.js` provider, and the shared `docs-viewer-catalogue-rendering.js`/Media View modules. Route policy remains with its local/public configuration owners; `site-tools/config/site-code-update.json` owns public runtime projection. Historical Series media and v1 presentation tests remain unreviewed for the current contract and were not changed or run. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns source grammar, usage and audit behavior.

## Gallery Presentations

Exact Gallery entry uses `galleries/index/<gallery_id>.json` under `gallery_record_v3`, read locally through `/docs/catalogue-gallery?gallery_id=<gallery_id>`. Its metadata and supplied ordered Work references drive the grid, pagination and selected-Work loading. The generated header contains schema, generation time and Gallery ID; each member contains `work_id` and `title`. Readers consume this completed handoff without another header/schema/member/order/uniqueness audit or an older-schema fallback. Exact request/response identity and safe thumbnail URLs remain required. Selecting a Work resolves its complete presentation through the active live/prepared provider. Empty Galleries display an empty state without pagination, and display/pagination totals derive from the loaded member list. Public readers use the explicit `catalogue_paths.gallery_records_base_url`, currently `/assets/data/catalogue/galleries/index/`; public Catalogue distribution remains separately owned.

Work presentations show **Related galleries**. Direct `work.galleries` links come first and carry **Contains this Work**; distinct links from the Work's exact Series–Gallery index entry follow with **Related to this Series**. The projector removes duplicates by exact Gallery ID, so a Gallery that contains the Work appears once as direct. A Work without a Series shows only direct links and does not request the index. A Work reached from a Gallery retains a return link to that Gallery. The Work reader does not fetch a Series by-ID record or supply a Series link. Selecting a Gallery link then reads its exact by-ID presentation in the same Content Detail mount. Previous/next follows that Gallery's complete Work order; returning to it restores the page containing the selected Work. Failed or superseded Gallery reads preserve the current presentation.

The Gallery projector retains ordered member Work identities and labels and resolves existing Work thumbnail filenames through route configuration. It does not read the complete Work index or every Work record. Selecting a member loads only that Work's complete presentation. Local thumbnails use the confined `/docs/catalogue-thumbnails/` route; public readers use configured `/assets/data/catalogue/works/thumbs/`. Thumbnail bases are route-owned; size, suffix and format come from shared generated policy. Selected Work images use that same policy's primary-image resolver.

Gallery pages display up to eight columns and six rows: 48 Work thumbnails at 64px with 8px gaps. The configured source is the existing 96px WebP Work thumbnail. Only the active page's thumbnail elements are created. Page and Work navigation cycle in both directions through the supplied Gallery order. Successful selection updates the Gallery return page to contain that Work; failed or superseded reads preserve the current selection and page. Direct Work entry does not infer a browsing sequence from Series or Gallery membership. Back to document remains owned by Content Detail.

## Consumer Limits

Interactive local and public Docs share presentation components with separate live/prepared providers. Projection validation establishes the runtime inventory; initial payload conversion, normal queued publication, Git/deployment and manual acceptance remain distinct execution evidence. Physical Catalogue JSON distribution retains its existing owner.

Gallery membership, bounded rendering and selected-record loading do not establish network-performance budgets. Neighbour prefetch, persistent caches and measurements on constrained connections are not implemented or claimed. The existing 96px thumbnail rendition is displayed at 64px; higher-resolution display policy remains a separate measured improvement if needed.

[Export](Export.md) and content-bearing [Prepare package](Package_Prepare.md) invoke the shared static preparer on selected reference-bearing content. Export packages emitted Work images and linked files from their configured Working owners; it uses the standard 800px image and fits it to the page without fetching served image URLs. Prepare package retains its existing transformations without media packaging. [Docs Review](Docs_Review.md) retains its separate read-only package/profile contract; no live Catalogue provider was added there. Portable export remains text-first.

## Status

The live/prepared Work presentation delivery was accepted and closed on 2026-10-19. Working conversion, normal Publish, representative Export creation/replacement and Prepare package dry-runs completed. The user accepted the 800px Export correction and confirmed the restored compact Catalogue Related Links styling. Remaining live activation/mutation, repeated-reference, Gallery navigation, failure/empty-unit and actual package-output observations will accumulate through normal use; historical v1 tests remain unchanged and unrun. Commit, push and deployment remain separate explicit actions, with the projected runtime and prepared public payloads shipped together.

The Gallery delivery added exact Gallery tokens, generated-index search in Add Media View link, the local Gallery reader, shared Gallery presentation and Work membership links. Its recorded diagnostics were direct reader/projector results, not browser interaction evidence. Series Media View links and galleries were subsequently retired while Series remained a document Subject and Catalogue grouping. The current local Work presentation adds explicit Series–Gallery relevance without restoring Series Media View; it has focused code and generated-data evidence, while interaction and visual review remain open. No test or fixture changes accompanied these changes.

The trimmed media-record and responsive-image implementation was added on 2026-09-23. Source lint, complete local JSON generation, representative live endpoint/resolver reads, public code projection and static-site validation passed. Code review covered reader wiring, exact identities, thumbnail reconciliation, policy validation, small-source candidate widths, raw-image separation and observer release. Browser layout and rendition selection at different display densities remain manual review gates. Existing media tests that encode per-record rendition arrays, `work_record_v6` or route-owned rendition settings do not establish coverage of this contract and require separately approved test work before adaptation; they were not changed or claimed as passing evidence.

The earlier Work/Detail/Series delivery was accepted on 2026-09-12. The current contract supports Work and Gallery media links and Work images; Detail and Series forms have been retired. Historical validation of the earlier Series gallery does not establish coverage of the new boundary. Static image preparation, shared caching/history and public Catalogue distribution retain their separate owners.
