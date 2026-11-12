---
draft: false
doc_id: d-20260903-154141-7c9e4b
title: Catalogue Media View
added_date: "2026-09-03 15:41:41"
last_updated: "2026-10-25"
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
[[catalogue:media:gallery:179:visible=false|kylie structure 4 (details)]]
```

For a Gallery, clear **Show inline link** to record the association without inserting a visible opener in the rendered body. Place the token on its own source line. **Edit Media View link** restores the saved checkbox state. A missing `visible` flag defaults to `true`. Save after removing the token to remove its contribution to the association.

The authored label remains literal text and does not change when the Catalogue title changes. The rendered opener is a keyboard-accessible button styled as inline link text, with no invented navigation URL. Work text links retain their existing form; unqualified Catalogue text and all Series token forms are retired without aliases. Existing authored Series tokens remain unchanged in Working source and render as literal text after rebuild.

Gallery IDs use the exact canonical spelling: three digits, or at least four digits without a leading zero. Gallery tokens allow no image presentation. Add/Edit Media View link inserts `catalogue:media:gallery` using the loaded target identity/title, and Broken Links separately checks the exact generated Gallery record. Subject assignment offers None, Work and, where the collection supports it, Folder. Series document Subjects were retired on 2026-10-03; Gallery tokens do not imply a new document Subject kind.

**Add Catalogue Image** searches Catalogue Works and uses the selected Work's image. Its result rows use the same grey ID-first presentation, without the `work` label or `year_display` subtitle. Add and Edit modes share this presentation. Its token stores the Work-title caption choice, optional static summary, placement and width settings:

```text
[[catalogue:image:work:03072|use_work_title_caption=true&placement=full&fill_width=true]]
```

Add/Edit Catalogue image and Media View link update only the captured Source range after local token serialization and buffer/editor checks. The picker reads the thumbnail policy for result previews. Apply uses the already selected identity and local fields. Registry and generated-target reads use HTTP revalidation with `no-cache`. Source Save persists the full buffer, awaits exact document/Links generation and displays the fresh result. Cancellation leaves the buffer unchanged.

## Document Build And Presentation

Image opener accessibility labels use `Open <Work title>` in live Manage, prepared public content and static snapshots. The browser renderer and shared Python preparer consume the supplied resolved title and retain their existing escaping.

Catalogue Regenerate formats Entry physical dimensions with compact decimals. It renders `21.0 × 29.7` as `21 × 29.7 cm` and preserves fractional values. Entry resources retain downloads followed by links in supplied order and with supplied labels.

Document Build emits exact ordered Catalogue references and HTML slots, retaining authored caption enablement, restricted summary HTML, placement, width and link labels. It prepares inline image data from adopted Catalogue documents. A Work has `catalogue-work` identity and its five-digit ID. A Gallery has `catalogue-gallery` identity and its exact canonical Gallery ID. Gallery openers render as text in document content and thumbnails appear inside Media View. [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation) owns the envelope and presentation fields.

Text links preserve surrounding Markdown even at the start of a paragraph or list item. Authored labels remain escaped literal text. Work images are block-level figures, including when their visible title caption is omitted; any authored summary remains available. Without a title-caption or summary, Build omits the figcaption.

The shared browser renderer fills Entry, image and text slots from the open document before requesting any referenced Work. The inline image and caption follow the referrer's own Build and publication lifecycle. Opening Media View from an image or text opener reads the exact Catalogue document and uses that Work's current adopted presentation. The media adapter reuses the Work's own open payload and retains successful selections within the document mount. Selecting a Gallery loads its membership and thumbnail inputs.

The Catalogue Work page renders one Gallery section after Entry resources and before **context**. The heading is **galleries** when the Work has direct memberships and **related galleries** when all links are Series-related. When both are present, direct links appear first and a plain `related:` label introduces the Series-related links. The browser preserves supplied order and omits the section when empty. Every link uses `images.svg` and opens Media View, which loads the selected Gallery membership on activation.

Work Media View shows the selected image, title, `cat. <work_id>` reference and Gallery links. Direct Gallery links precede a separate related group from Series–Gallery relationships. `cat.` is plain text and only the five-digit Work ID links to the definitive Catalogue document at `?collection=catalogue&doc=<work-id>`, opened in a new tab. The `docs_media_view_v2` contract omits the former unused descriptive metadata array; Entry fields are independent. Open in new tab targets the supplied selected image. Back to document restores the invoking document, scroll and focus through Content Detail.

Media View centers Back and Open in new tab together in the top row, using the same shared CSS grid as image detail. Home stays on the left; Manage Actions and the theme control stay on the right. This layout applies to local and public views, including narrow public screens, without positioning Open against the image/metadata columns.

Work and Gallery information uses `font-small`, normal upright text and the standard text colour. Its title retains the established bold `font-body` size, without the document H2 divider or padding. Component rules are scoped within `docsViewer__content` so generic figure-caption and heading styles do not override this presentation.

Authored references persist when a Work is removed. The operation that needs a missing adopted input reports its exact Work. Media View shows unavailable-target feedback beside the opener and permits retry. The adapter checks the current mount and selection before applying an asynchronous result.

## Current Catalogue Data

Studio Refresh supplies the selected raw Work data, Gallery relationships and rendition policy. Catalogue Regenerate adopts them into the Work's Catalogue document. Working and public readers use the exact Catalogue by-ID document and route-configured primary image and owned-download roots. Gallery policy reads still supply thumbnail naming. [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation) owns the fields and [Broken Links](Broken_Links_Script.md) owns explicit availability diagnosis.

Width descriptors reflect actual rendition widths, including sources below a configured target. Preparation removes duplicate widths. The browser builds `srcset` from the prepared candidates and `docs-viewer-responsive-image.js` measures the CSS slot width to set `sizes` before the first image request. In-document images retain their authored placement and width. Media View CSS constrains the slot width by its image column, source dimensions, viewport height and aspect ratio. Open in new tab uses the prepared full-image target, currently the 1600px rendition.

Left-aligned Catalogue image tokens can use the existing half-width responsive image, a third-width single-source image from the default primary rendition, or the native square thumbnail. Build prepares the exact inline rendition. Working and public resolve it using the configured primary or thumbnail base. Selecting a thumbnail opens the Work's primary image through Media View. Export packages the exact inline thumbnail and the primary rendition it links to.

## Ownership

| owner | responsibility |
| --- | --- |
| Studio Refresh and Catalogue Regenerate | complete selected Work inputs and adopt Work facts and Gallery references into Catalogue documents |
| Source authoring and Document Build | preserve authored references and prepare inline image render data from adopted Work facts |
| shared workspace provider | resolve exact Catalogue documents, Gallery records and configured asset roots |
| static preparer | materialize selected HTML for Export and content-bearing Prepare Package |
| shared Catalogue browser renderer | render portable Entry, image and text slots in Working and public |
| shared gallery helper | own density, page membership, complete-order neighbours and wrapping |
| Media View adapter | register the current occurrence, load selected Works, render the active gallery page or image, preserve the return page, reject late results and release state |
| Docs Viewer Content Detail | main-pane lifecycle, Back and Open in new tab controls, scroll and focus restoration |
| public and Manage entrypoints | compose the same shared adapter |
| Broken Links | read source tokens and diagnose current generated media availability without mutating content |

The implementation owners are `docs_catalogue_projection.py` for adoption and selected projection, `docs_catalogue_static.py` for static HTML, `docs_builder/semantic_tokens.py` for authored references, and the shared `docs-viewer-workspace-provider.js`, `docs-viewer-catalogue-rendering.js` and Media View modules. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns source grammar, usage and audit behavior.

## Gallery Presentations

Gallery pages show their own title, Work thumbnails in natural, case-insensitive title order and pagination. Numeric title parts sort numerically, so `Study 2` precedes `Study 10`; equal titles use Work ID as the tie-breaker. The shared browser projector sorts the already loaded members once for local and public Media View, without changing generated record order or requesting more data. Gallery links appear only beside a selected Work, including its return link to the active Gallery. Opening a Gallery does not carry forward the last Work's Gallery links, so its presentation is independent of the route taken to it.

Exact Gallery entry uses `galleries/index/<gallery_id>.json` under `gallery_record_v3`. Working reads it through `/docs/catalogue-gallery?gallery_id=<gallery_id>` and public uses its configured Gallery records base. The generated header contains schema, generation time and Gallery ID. Member `work_id` and `title` drive the grid, pagination and exact Catalogue document selection. Empty Galleries show an empty state.

Gallery Media View displays Context documents below the Gallery title with a gap, with the configured Context icon beside each document title. Each Context document appears once if it names the Gallery in a visible or hidden Media View token or references a Work in the full member list. The title opens the exact Context route. The Context manifest supplies optional `catalogue_targets` with distinct `work_ids` and `gallery_ids` from the selected document's completed render. A hidden Gallery can also appear in the document's [Related Links](Related_Links.md) when the author places a `[[links|…]]` directive. Working includes drafts and public preparation carries the same facts for eligible rows. Public shares one lazy manifest read with the Context report for the page session. Working revalidates the saved manifest when a Gallery opens. The browser loads it alongside the Gallery record, and a failed Context read leaves the Gallery available with a status message. Gallery membership changes take effect on the next read of the updated Gallery record.

Work presentations use `images.svg` for Gallery links from the adopted document. Direct links come first, followed by a plain `related:` label and the distinct Series-related links. A Work reached from a Gallery retains a return link to it. Previous/Next follows the loaded Gallery's natural title order and returning restores the page containing the selected Work. Failed or superseded reads preserve the current presentation.

The Gallery projector resolves thumbnail filenames from loaded member identities, the route-configured thumbnail base and the generated size, suffix and format. Opening and paging the Gallery use that member list. Selecting a member loads only its Catalogue document.

Gallery pages display up to eight columns and six rows: 48 Work thumbnails at 64px with 8px gaps. The configured source is the existing 96px WebP Work thumbnail. Only the active page's thumbnail elements are created. Page and Work navigation cycle in both directions through the supplied Gallery order. Successful selection updates the Gallery return page to contain that Work; failed or superseded reads preserve the current selection and page. Direct Work entry does not infer a browsing sequence from Series or Gallery membership. Back to document remains owned by Content Detail.

## Consumer Limits

Interactive Working and public Docs use the same document and Media View contracts. The runtime projection and the prepared public payloads ship together.

Gallery membership, bounded rendering and selected-record loading do not establish network-performance budgets. Neighbour prefetch, persistent caches and measurements on constrained connections are not implemented or claimed. The existing 96px thumbnail rendition is displayed at 64px; higher-resolution display policy remains a separate measured improvement if needed.

[Export](Export.md) and content-bearing [Prepare package](Package_Prepare.md) invoke the shared static preparer on selected reference-bearing content. Export packages emitted Work images and linked files from their configured Working owners; it uses the standard 800px image and fits it to the page without fetching served image URLs. Prepare package retains its existing transformations without media packaging. [Docs Review](Docs_Review.md) retains its separate read-only package/profile contract; no live Catalogue provider was added there. Portable export remains text-first.

## Status

On 2026-11-12, the user observed separate 800 px and 1200 px transfers for Work `04913` after opening it from a Gallery thumbnail in Safari. Source review found that the shared image helper derived `sizes` from the unloaded image's height even though Media View CSS already incorporates the height limit into the width. The helper now reads the slot width and updates `sizes` only when that width changes. Review traced the Media View column, Catalogue Entry frame and authored inline widths. Focused JavaScript lint, whitespace, public projection and site validation passed. After clearing Safari's cache and reopening `04913` from its Gallery thumbnail in Working, the user recorded a single `04913-primary-1200.webp` transfer of 194.04 kB. The previous 800 px transfer added 95.47 kB. A separate refresh of the *3 symbols* document after clearing the cache transferred only `04913-primary-1600.webp` for that Work, at 325.86 kB. The document image follows its authored layout, and Media View caps the image width by the available viewport height and the Work's aspect ratio.

The 2026-10-25 natural-title ordering change passed focused lint for `docs-viewer-catalogue-media.js`, tracked projection/check, deploy-root validation and whitespace review. Code and redundancy review confirmed that sorting the newly mapped member array preserves generated inputs and gives pagination, previous/next and the return page one sequence, including empty Galleries. One shared collator supplies numeric, case-insensitive ordering; no additional reads, validation, title normalization or fallback behavior were added. Exact target and safe media URL checks remain at their existing boundaries. Tests and browser interaction were not run; manual confirmation remains through ordinary use. The public runtime copy is projected; commit, push and deployment remain separate actions.

The 2026-10-22 Gallery simplification removed inherited Work links, their cross-view state and the selection fallback. Source/redundancy review confirmed that return targets resolve from the supplied Gallery before Work-link lookup. Existing supplied-target checks prevent unrelated loads, and stale/released-request guards prevent late rendering; no reads, validation or caches were added. Focused JavaScript lint, tracked projection/check, site validation and whitespace review passed. Tests and browser interaction were not run; manual confirmation remains through ordinary use.

The live/prepared Work presentation delivery was accepted and closed on 2026-10-19. Working conversion, normal Publish, representative Export creation/replacement and Prepare package dry-runs completed. The user accepted the 800px Export correction and confirmed the restored compact Catalogue Related Links styling. Remaining live activation/mutation, repeated-reference, Gallery navigation, failure/empty-unit and actual package-output observations will accumulate through normal use; historical v1 tests remain unchanged and unrun. Commit, push and deployment remain separate explicit actions, with the projected runtime and prepared public payloads shipped together.

The Gallery delivery added exact Gallery tokens, generated-index search in Add Media View link, the local Gallery reader, shared Gallery presentation and Work membership links. Its recorded diagnostics were direct reader/projector results, not browser interaction evidence. Series Media View links and galleries were subsequently retired while Series remained a document Subject and Catalogue grouping. The current local Work presentation adds explicit Series–Gallery relevance without restoring Series Media View; it has focused code and generated-data evidence, while interaction and visual review remain open. No test or fixture changes accompanied these changes.

The trimmed media-record and responsive-image implementation was added on 2026-09-23. Source lint, complete local JSON generation, representative live endpoint/resolver reads, public code projection and static-site validation passed. Code review covered reader wiring, exact identities, thumbnail reconciliation, policy validation, small-source candidate widths, raw-image separation and observer release. Browser layout and rendition selection at different display densities remain manual review gates. Existing media tests that encode per-record rendition arrays, `work_record_v6` or route-owned rendition settings do not establish coverage of this contract and require separately approved test work before adaptation; they were not changed or claimed as passing evidence.

The earlier Work/Detail/Series delivery was accepted on 2026-09-12. The current contract supports Work and Gallery media links and Work images; Detail and Series forms have been retired. Historical validation of the earlier Series gallery does not establish coverage of the new boundary. Static image preparation, shared caching/history and public Catalogue distribution retain their separate owners.
