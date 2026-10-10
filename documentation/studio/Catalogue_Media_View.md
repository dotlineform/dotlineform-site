---
draft: false
doc_id: d-20260903-154141-7c9e4b
title: Catalogue Media View
added_date: "2026-09-03 15:41:41"
last_updated: "2026-10-10 15:56:00"
summary: Exact Work and Gallery links, direct and Series-related Gallery navigation, responsive Work images and paginated Media View, with static-consumer and public-data limits.
ui_status: done
parent_id: d-20260903-222617-28475e
---
# Catalogue Media View

## Purpose

Media View presents an exact Catalogue Work or Gallery inside the Docs Viewer main pane. Authors can open these through a text link or insert a Work image that opens the same view. Catalogue owns identity and media; the invoking document supplies browsing context. A corresponding document or document Subject is not required, and these references create no doc-to-doc relationship. Series remains a Catalogue grouping, without a document Subject or Media View target.

The Gallery conversion retired canonical Details. Detail subject assignment, token syntax, image selection, Info fields, report support and media readers are removed, with no old-to-new aliases. Work images and Work or Gallery text links are the supported Catalogue media forms. Series Media View links and galleries are retired without an alias.

## Authoring

**Add Media View link** searches generated Catalogue Work and Gallery titles or identities through the shared Catalogue image modal. Result rows show the exact `work_id` or `gallery_id` first in grey, then the title, without a `work`/`gallery` label or year/count subtitle. Gallery results come from `galleries/galleries_index.json`, whose v2 rows contain only ID/title. Selecting a Work resolves that Work's image directly; selecting a Gallery resolves its membership. Selected or edited text remains the editable label; an untouched default follows the chosen record title. The source forms are:

```text
[[catalogue:media:work:00523|kylie structure 4]]
[[catalogue:media:gallery:179|kylie structure 4 (details)]]
```

The authored label remains literal text and does not change when the Catalogue title changes. The rendered opener is a keyboard-accessible button styled as inline link text, with no invented navigation URL. Work text links retain their existing form; unqualified Catalogue text and all Series token forms are retired without aliases. Existing authored Series tokens remain unchanged in Working source and render as literal text after rebuild.

Gallery IDs use the exact canonical spelling: three digits, or at least four digits without a leading zero. Gallery tokens allow no image presentation. The picker inserts `catalogue:media:gallery`; token Info reads the current Gallery title, and Broken Links checks the exact generated Gallery record. Subject assignment offers None, Work and, where the collection supports it, Folder. Series document Subjects were retired on 2026-10-03; Gallery tokens do not imply a new document Subject kind.

**Add Catalogue Image** searches Catalogue Works and uses the selected Work's image. Its result rows use the same grey ID-first presentation, without the `work` label or `year_display` subtitle. Add and Edit modes share this presentation. Its token stores the Work-title caption choice, optional static summary, placement and width settings:

```text
[[catalogue:image:work:03072|use_work_title_caption=true&placement=full&fill_width=true]]
```

Insertion and token Info edits validate current selected media before changing the captured Source range. Token edits join the existing combined Source session; Save ends at canonical source persistence and the watcher refreshes document output independently. Closing Source releases its token Info ownership; delayed lookups cannot reopen or overwrite a released panel.

## Document Build And Presentation

Document Build preserves exact Catalogue references and authored presentation. For a Work image it reads the exact generated Work record and embeds the selected title-caption and optional authored summary as static, escaped figure text; it embeds no descriptive Work metadata, Catalogue record or image URL. A Work has `catalogue-work` identity and its five-digit ID; a Gallery has `catalogue-gallery` identity and its exact canonical Gallery ID. Gallery entry remains a text link in document content; thumbnail grids exist only inside Media View.

Text links preserve surrounding Markdown even at the start of a paragraph or list item. Authored labels remain escaped literal text. Work images are block-level figures, including when their visible title caption is omitted; any authored summary remains available. Without a title-caption or summary, Build omits the figcaption.

Opening a document resolves inline images through current Catalogue consumer data. Selecting a text link reads the exact Work or Gallery and opens Media View. Selecting an image reads its Work again, updates the inline image and opens Media View from that record. Retired Detail and Series markers do not open Media View.

Work Media View shows the selected image, title, `cat. <work_id>` reference and Gallery links. Direct Gallery links precede a separate related group from Series–Gallery relationships. `cat.` is plain text and only the five-digit Work ID links to the definitive Catalogue document at `?collection=catalogue&doc=<work-id>`, opened in a new tab. The current presentation contract still constructs and validates descriptive metadata, but the Work view does not display it; retiring that unused contract remains separate work in [Public Work JSON Review](Public_Work_JSON_Review.md). Open in new tab targets the supplied selected image. Back to document restores the invoking document, scroll and focus through Content Detail.

Build retains valid text-link references when Catalogue data is unavailable, allowing later runtime recovery. A Work image requires its generated record at Build and fails visibly if the exact identity or title is unavailable. Runtime loading and failure feedback for the image and Media View still appears beside the opener and permits retry. Replaced documents, released mounts, changed child selections and superseded requests cannot apply a late response.

## Current Catalogue Data

The source of consumer records is `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/works/index/<work_id>.json`, as described by [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md). Work records supply identity, optional exact `series_id`, `media_version`, `width_px`, `height_px` and direct Gallery memberships. The separate generated `series-galleries-index.json` supplies explicit links for every valid Series; `media-config.json` supplies shared rendition policy. Per-record media arrays and per-Work related Gallery arrays are not used. Docs consumers require only the Work image base and do not read Detail sections or resolve Detail image paths. Identity is never inferred from a filename, title, document or selected UI row.

Local Docs reads the current generated record through `/docs/catalogue-work?work_id=<work_id>`, the shared policy through `/docs/catalogue-media-config` and, for a Work with a Series, the exact mapping through `/docs/catalogue-series-galleries`. Public Docs uses `catalogue_paths.work_records_base_url`, currently `/assets/data/catalogue/works/index/`, `catalogue_paths.media_config_url`, currently `/assets/data/catalogue/media-config.json`, and `catalogue_paths.series_galleries_index_url`, currently `/assets/data/catalogue/series-galleries-index.json`. Both resolve image URLs from the policy and exact identity/version, currently using R2. Local generated thumbnails do not replace those image sources.

Each activation reads again: local requests use `no-store`, and public requests use HTTP revalidation with `no-cache`. Work and policy requests share only in-flight reads; a Work with a Series also reads the Series–Gallery index, while a Work without a Series skips it. There is no document-lifetime cache. Public freshness is limited to the latest deployed Catalogue output, and the reader makes no local-service or archive fallback request.

The shared projector validates exact identity, titles, positive dimensions/version, safe media policy and the required Series–Gallery index when a Work has a Series. It prepares `docs_media_view_v1` with responsive image candidates, metadata, ordered Gallery links marked `direct` or `series`, and a separate largest-rendition new-tab target. Missing or invalid required index data fails visibly instead of showing a partial related list. Root-relative and credential-free HTTPS media targets are supported. Canonical Studio JSON and guessed media paths are not reader inputs.

`docs-viewer-catalogue-media-policy.js` resolves configured candidates and thumbnail naming. Width descriptors reflect actual output dimensions, including sources below a configured target, and duplicate widths are removed. `docs-viewer-responsive-image.js` sets `srcset` and a pixel `sizes` value measured from the displayed image slot before loading; a ResizeObserver updates it as layout changes. In-document images retain their authored placement and width. Media View constrains width by its image column, source dimensions, viewport height and aspect ratio. The browser chooses a candidate for the measured slot and display density. Open in new tab and token Info image links always use the largest configured rendition, currently 1600, independently of that choice. Supplied demonstration presentations with a single explicit image remain separate supported callers.

## Ownership

| owner | responsibility |
| --- | --- |
| Catalogue generated consumer output | supply exact Work records, direct Gallery membership, explicit Series–Gallery mapping, the Gallery search lookup and existing Work thumbnails independently of documents |
| Source authoring and Document Build | preserve selected identity, literal labels and authored image presentation |
| local management client or public provider | read exact current generated or deployed Work/Gallery records and the Series–Gallery mapping for Works with a Series; apply configured thumbnail paths |
| shared Catalogue projector | validate records and the required Series–Gallery mapping; prepare a selected `docs_media_view_v1` image with distinct ordered Gallery links or `docs_media_gallery_v1` references |
| shared gallery helper | own density, page membership, complete-order neighbours and wrapping |
| Media View adapter | register the current occurrence, load selected Works, render the active gallery page or image, preserve the return page, reject late results and release state |
| Docs Viewer Content Detail | main-pane lifecycle, Back and Open in new tab controls, scroll and focus restoration |
| public and Manage entrypoints | compose the same shared adapter |
| Broken Links | read source tokens and diagnose current generated media availability without mutating content |

The implementation owners are `docs-viewer/services/docs_catalogue_media.py`, `docs-viewer/build/docs_builder/semantic_tokens.py`, the Source editor's `catalogue-media-modal.js` and `catalogue-media-support.js`, and the shared runtime modules `docs-viewer-catalogue-media.js`, `docs-viewer-media-presentation.js`, `docs-viewer-media-gallery.js` and `docs-viewer-media-detail.js`. Route policy is in `docs-viewer/config/routes/docs-viewer-routes.json`; `site-tools/config/site-code-update.json` owns public runtime projection. Historical Series media tests still describe the retired behavior and were not changed for this delivery. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns source grammar, usage and audit behavior.

## Gallery Presentations

Exact Gallery entry uses `galleries/index/<gallery_id>.json`, read locally through `/docs/catalogue-gallery?gallery_id=<gallery_id>`. Its metadata and ordered Work references drive the grid, pagination and selected-Work loading. Empty Galleries display an empty state without pagination. The reader validates matching header/body IDs, member count, distinct exact Work IDs and ascending Work-ID order. Public readers use the explicit `catalogue_paths.gallery_records_base_url`, currently `/assets/data/catalogue/galleries/index/`; public Catalogue distribution remains separately owned.

Work presentations show **Related galleries**. Direct `work.galleries` links come first and carry **Contains this Work**; distinct links from the Work's exact Series–Gallery index entry follow with **Related to this Series**. The projector removes duplicates by exact Gallery ID, so a Gallery that contains the Work appears once as direct. A Work without a Series shows only direct links and does not request the index. A Work reached from a Gallery retains a return link to that Gallery. The Work reader does not fetch a Series by-ID record or supply a Series link. Selecting a Gallery link then reads its exact by-ID presentation in the same Content Detail mount. Previous/next follows that Gallery's complete Work order; returning to it restores the page containing the selected Work. Failed or superseded Gallery reads preserve the current presentation.

The Gallery projector retains ordered member Work identities and labels and resolves existing Work thumbnail filenames through route configuration. It does not read the complete Work index or every Work record. Selecting a member loads only that Work's complete presentation. Local thumbnails use the confined `/docs/catalogue-thumbnails/` route; public readers use configured `/assets/data/catalogue/works/thumbs/`. Thumbnail bases are route-owned; size, suffix and format come from shared generated policy. Selected Work images use that same policy's primary-image resolver.

Gallery pages display up to eight columns and six rows: 48 Work thumbnails at 64px with 8px gaps. The configured source is the existing 96px WebP Work thumbnail. Only the active page's thumbnail elements are created. Page and Work navigation cycle in both directions through the supplied Gallery order. Successful selection updates the Gallery return page to contain that Work; failed or superseded reads preserve the current selection and page. Direct Work entry does not infer a browsing sequence from Series or Gallery membership. Back to document remains owned by Content Detail.

## Consumer Limits

Interactive local and public Docs share the implemented reader. Public Catalogue JSON distribution remains pending separately, so a projected runtime does not establish that the required public records are deployed. Document publication and current Catalogue distribution retain separate owners.

Gallery membership, bounded rendering and selected-record loading do not establish network-performance budgets. Neighbour prefetch, persistent caches and measurements on constrained connections are not implemented or claimed. The existing 96px thumbnail rendition is displayed at 64px; higher-resolution display policy remains a separate measured improvement if needed.

[Export](Export.md) and [Docs Review](Docs_Review.md) do not yet resolve authored Work image references. Document Build emits a hidden image without `src`, so these static consumers need a preparation step before those images can display. The proposed export policy downloads selected R2 images into the export folder; the proposed Review policy resolves ordinary R2 URLs while preparing or explicitly rebuilding the preview. Both must first read generated Catalogue JSON, and neither policy is implemented yet. Existing text-first portable export remains text-first.

## Status

The Gallery delivery added exact Gallery tokens, generated-index search in Add Media View link, the local Gallery reader, shared Gallery presentation and Work membership links. Its recorded diagnostics were direct reader/projector results, not browser interaction evidence. Series Media View links and galleries were subsequently retired while Series remained a document Subject and Catalogue grouping. The current local Work presentation adds explicit Series–Gallery relevance without restoring Series Media View; it has focused code and generated-data evidence, while interaction and visual review remain open. No test or fixture changes accompanied these changes.

The trimmed media-record and responsive-image implementation was added on 2026-09-23. Source lint, complete local JSON generation, representative live endpoint/resolver reads, public code projection and static-site validation passed. Code review covered reader wiring, exact identities, thumbnail reconciliation, policy validation, small-source candidate widths, raw-image separation and observer release. Browser layout and rendition selection at different display densities remain manual review gates. Existing media tests that encode per-record rendition arrays, `work_record_v6` or route-owned rendition settings do not establish coverage of this contract and require separately approved test work before adaptation; they were not changed or claimed as passing evidence.

The earlier Work/Detail/Series delivery was accepted on 2026-09-12. The current contract supports Work and Gallery media links and Work images; Detail and Series forms have been retired. Historical validation of the earlier Series gallery does not establish coverage of the new boundary. Static image preparation, shared caching/history and public Catalogue distribution retain their separate owners.
