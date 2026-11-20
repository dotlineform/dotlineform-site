---
draft: false
doc_id: d-20261120-130501-7ffcb1
title: Media View Link Authoring
added_date: "2026-11-20 13:05:01"
last_updated: "2026-11-20"
summary: Use one Source action to show a Work image, open its Gallery and retain the Catalogue backlink while keeping Related Links focused on Galleries and document links.
ui_status: proposed
parent_id: d-20261118-235100-64ad2e
---
# Media View Link Authoring

## Outcome

An author can insert a Work image that opens one of its Galleries and adds that Gallery to the document’s Related Links. One source token records both choices. The Work’s Catalogue document still links back to the referring document. This delivery also covers inline and hidden references, editing existing occurrences, and the pinned Related Links panel.

The authoring and navigation behaviour below is agreed. The source spelling, JSON changes, new insertion defaults and Gallery label rule are proposed implementation decisions. The next step is review before implementation. [Current source forms](../reference/Document_And_Catalogue_References.md) · [Current Related Links](../reference/Related_Links.md)

## One Source action

Expand the existing **Add Catalogue image** action and relabel it **Add Media View link**. Retire the former standalone **Add Media View link** action, its action ID, menu entry and separate text-link mode. The Directives menu has one Catalogue insertion action. Its Edit form recognises either kind of authored Catalogue occurrence. **Add image** continues to insert Docs-owned media. [Directive actions](../../docs-viewer/runtime/js/management/source-editor/directive-actions.js) · [Current Catalogue modal](../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js)

1. **Search Catalogue** uses the current Media View link search for Works and Galleries, including its ID/title matching, Work thumbnails and keyboard selection.
2. Selecting a **Work** reveals a second list labelled **Open in Media View**. Its first and default option is **This Work**, followed by the Galleries of which the Work is a direct member. Series-related Galleries do not qualify. For a Work with no direct memberships, **This Work** is the only option. Changing Work resets this list to **This Work**.
3. Selecting a **Gallery** in the main search goes straight to display options. A Gallery selected this way has no associated Work. Selecting the same Gallery through a Work retains both IDs in every display mode.
4. **Display** offers **Image**, **Inline link** and **Hidden**. For new insertions, default a Work to **Image** and a directly selected Gallery to **Inline link**, with **Image** disabled for that Gallery. Choosing a Gallery in the second list leaves Image available. Edit always restores the saved display mode.

| Display | Controls | Result in the document body |
| --- | --- | --- |
| **Image** | **Title caption** (initially on), optional **Summary**, **Layout** (Full, Left or Right, initially Full), and **Fill available width** (initially on). Left and Right offer **Wrap body text**. Left also offers **Image width** of 50%, 33% or Thumbnail. Thumbnail hides the fill control and saves natural width. | Display the selected Work’s image, alt text and chosen caption. Activating the image opens the Work or the selected Gallery grid. Its accessible button name identifies the destination. |
| **Inline link** | Required **Link text**. Use selected source text when present, otherwise the destination title. An untouched default follows a changed destination. Preserve an authored label. | Display that text as a Media View opener for the Work or Gallery. |
| **Hidden** | The same **Link text** field and defaults. A Gallery label can appear in Related Links. A hidden Work-only label remains editable in Source. | Emit no inline text, image or focusable control. Record the selected associations. |

**Add** inserts one token at the captured selection. With the caret inside a supported token or its exact range selected, **Edit Media View link** restores the search selection, second-list choice, display and applicable fields. **Apply** replaces that occurrence and **Cancel** preserves the buffer. Keep the current selection and revision guard. Save remains the action that persists and builds the document. A later membership change must never silently retarget a saved occurrence to **This Work**. On Edit, identify a saved Gallery that is no longer offered and let the author keep it or deliberately choose another destination. [Source editor](../reference/Source_Editing.md) · [Image controls](../../docs-viewer/runtime/js/management/source-editor/catalogue-image-presentation.js)

## Proposed Markdown

Keep the existing single-target forms. For a Work with a selected Gallery, append `:gallery:<id>` after the Work ID. **Hidden** appends `:visible=false` to the complete media identity. Examples use Work `00638`, a direct member of Gallery `005`, “3 symbols”. [Gallery record](../../site/assets/data/catalogue/galleries/index/005.json)

**Work → Gallery.** In order, Image, Inline link and Hidden all retain both selections.

```text
[[catalogue:image:work:00638:gallery:005|use_work_title_caption=true&placement=full&fill_width=true&gallery_label=3%20symbols]]
[[catalogue:media:work:00638:gallery:005|Explore the Gallery]]
[[catalogue:media:work:00638:gallery:005:visible=false|3 symbols]]
```

**Work → This Work.** The same three modes refer only to the Work.

```text
[[catalogue:image:work:00638|use_work_title_caption=true&placement=full&fill_width=true]]
[[catalogue:media:work:00638|See the Work]]
[[catalogue:media:work:00638:visible=false|3 symbols]]
```

**Gallery directly.** The two available modes are Inline link and Hidden.

```text
[[catalogue:media:gallery:005|Explore the Gallery]]
[[catalogue:media:gallery:005:visible=false|3 symbols]]
```

Use the existing exact ID, literal link-text escaping and image-field encoding rules. The proposed final image field `gallery_label` captures the selected Gallery title in the editor. It supplies the Gallery row label and the image opener’s accessible name without adding a Link text control to Image or looking up the title during Build. A later Catalogue rename leaves that saved label intact until the author reselects the Gallery. Inline and hidden Gallery references use the authored Link text. If several occurrences name the same Gallery, the first occurrence supplies its row label, following the current rule.

## Related Links and backlinks

Suppose a Context document uses the paired image above. Its body shows Work `00638` and opens Gallery `005`. Its `[[links|]]` section shows the Gallery once. The Catalogue document for `00638` shows the Context document as an incoming link. If the author also writes an ordinary Markdown link to that Catalogue document, the Context document shows **both** the Catalogue document and the Gallery.

| Evidence on the document being rendered | Related Links row |
| --- | --- |
| An incoming document relationship, including a backlink created by another document’s Work token | Show the referring document. |
| An outgoing explicit Markdown document link, including a link to a Catalogue document | Show its destination document. |
| An outgoing Work association supplied only by an image, inline or hidden media token | Keep the directed relationship and its backlink. This outgoing occurrence contributes no document row. |
| An explicitly selected Gallery, direct or through a Work, in any display mode | Show one Gallery opener. Other Galleries containing the Work contribute no rows. |

Apply these rules **before** combining and deduplicating document rows. An incoming relationship qualifies even when an outgoing Work-only association reaches the same document. Removing the last explicit link while keeping its Work image removes that reason to show the outgoing row and preserves the backlink. Removing the final Work or explicit-link occurrence removes the underlying edge. Preserve existing self-link omission, ordering and empty-section rules. The pin captures the same rendered section. [Relationship builder](../../docs-viewer/build/docs_builder/links_builder.py) · [Section renderer](../../docs-viewer/build/docs_builder/related_links.py)

## JSON and builder changes

| Owner | Proposed contract and work |
| --- | --- |
| **Manage picker response** | Extend `/docs/catalogue-media-targets` to `docs_catalogue_media_targets_v2`. Keep Work choices from the adopted Manage manifest. Source Gallery titles and `gallery_ids_by_work` from Studio’s existing `galleries/report-search.json`, which already contains both. Return the direct membership map alongside the targets. The browser builds the second list from that response. The separate Thumb picker continues using only Work choices. [Lookup](../../docs-viewer/services/docs_catalogue_media.py) · [Membership producer](../../studio/services/catalogue/catalogue_gallery_report_search.py) |
| **Document by-ID JSON** | For generated Catalogue envelopes propose `docs_catalogue_presentation_v2`. Keep `reference_id`, `presentation`, `options` and `target`. **Target always names what opens.** A paired visible occurrence adds `work_id` for the separately selected Work. For an image it supplies the renditions, alt and caption. Single-target records already carry the needed ID in `target`. The paired image carries its Gallery label in `options.gallery_label`. Entry and the adopted `catalogue.work` facts retain their existing fields. [Reference builder](../../docs-viewer/build/docs_builder/source_tokens.py) · [Work projection](../../docs-viewer/services/docs_catalogue_projection.py) |
| **Context manifests** | Keep the existing optional `catalogue_targets: {work_ids, gallery_ids}` in Working and eligible public rows. Derive these sets from parsed occurrences, including hidden ones, before suppressing their body slots. A paired occurrence contributes both IDs. Gallery-only contributes no Work ID. By-ID `references` continues to describe visible slots. A hidden-only document can therefore have associations without a visible reference. [Context projection](../../docs-viewer/build/docs_builder/collection_metadata.py) |
| **Working Links JSON** | Advance `links-by-id/<doc_id>.json` from version 4 to 5. Each outgoing summary adds one boolean, `explicit_doc_link`. Set it true if **any** ordinary document link reaches that endpoint and false when only Work tokens do. Keep one edge per endpoint and keep `self` and `incoming` summaries as they are. A Gallery has no document endpoint. Advance the Links report aggregate that embeds these records on its own Refresh. Diagnostic counts still include Work edges. [Saved schema](../../docs-viewer/build/docs_builder/links_schema.py) · [Links report](../../docs-viewer/services/docs_workspace_links.py) |

For the paired image, Build produces this reference and then attaches the selected Work renditions in `render`.

```json
{
  "reference_id": "c1",
  "presentation": "image",
  "target": {"kind": "catalogue-gallery", "id": "005"},
  "work_id": "00638",
  "options": {"use_work_title_caption": true, "summary_html": "", "placement": "full", "fill_width": true, "gallery_label": "3 symbols"}
}
```

The same example adds `{"work_ids":["00638"],"gallery_ids":["005"]}` to the Context row’s `catalogue_targets`. Its outgoing Links row is `{"collection":"catalogue","doc_id":"00638","title":"3 symbols","explicit_doc_link":false}`. Adding an explicit link changes that boolean to true even if its destination was already recorded. The incoming row on the Work continues to identify the referring Context document.

## Existing documents and other consumers

- **Existing Markdown.** Existing Work images open as Image with **This Work**. Work media tokens open as Inline link with **This Work**. Direct Gallery tokens reopen as Inline link or Hidden according to their saved visibility, including the existing explicit `:visible=true` spelling. Their source is already valid. Preserve labels, summaries and layout. Existing Work references acquire no Gallery automatically. A Work image and a separately authored Gallery token remain two occurrences until the author chooses to combine them. The Regenerate-owned Entry stays outside the modal.
- **Build and Media View.** Extend the browser and Python token parsers together. Build collects both identities and the Gallery row label before producing a visible slot or suppressing a hidden one. Prepare image renditions from the selected Work. Bind the live opener to the saved destination in Manage and Public. Media View’s exact Gallery grid, Work-to-Catalogue-document route, Back behaviour and Context manifest lookup already serve these destinations. Direct membership limits new selections in the editor. Build and Publish use the saved identities. [Shared renderer](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-rendering.js) · [Media View](../reference/Catalogue_Media_View.md)
- **Search and diagnostics.** Search indexes visible link text under its existing rules and skips hidden labels. Broken Links checks both exact identities on a paired occurrence and identifies which one is unavailable. The Links report retains its full directed graph. Editing, retitling or moving a document must preserve the outgoing explicit-link flag during neighbour updates. [Search builder](../../docs-viewer/build/build_search.py) · [Broken Links](../../docs-viewer/services/docs_broken_links.py)
- **Projects.** Refresh currently derives Context associations from visible by-ID references. Read both identities on a paired visible reference so the Work’s Series and the Gallery’s expressly associated Series can each contribute. Keep the existing visibility policy for Projects in this delivery. Switching Projects to the Context manifest would also start counting existing hidden Gallery mentions, a separate product decision. [Projects snapshot](../../docs-viewer/services/docs_project_state.py)
- **Export, content-bearing packages and Docs Review.** Carry the pictured Work through static preparation and the export transform even when the surrounding opener names a Gallery. HTML Export should retain the Work image and caption, with the Gallery using its existing static treatment. Hidden references produce no body placeholder. Check the filtered Related Links rows and packaged image paths. A Gallery selection alone should never pull every member image into an export or publication. [Static preparer](../../docs-viewer/services/docs_catalogue_static.py) · [Export transform](../../docs-viewer/services/docs_static_html_export_media.py) · [Docs Review](../reference/Docs_Review.md)

## Delivery sequence and acceptance

- [ ] Review the proposed token, JSON shapes, label and insertion defaults. Confirm the existing membership output and action ownership before editing code.
- [ ] Implement picker and Source editing, then the token, relationship and document builders. Carry prepared selections through exact Save/Rebuild, direct-neighbour updates and the shared reader. Update the affected static and report consumers.
- [ ] Rebuild generated relationships from authored source for the version-5 cutover. Version 4 cannot distinguish explicit from Work-derived links. Use the workspace relationship pass before rendering ordinary and named-collection output. Account for Catalogue’s separately owned documents and retained adopted Work data using its design reconciliation where required. Full Working Build excludes bulk Catalogue generation. Refresh the saved Links report through its own action. Source needs no bulk rewrite. [Build ownership](../reference/Builder.md) · [Catalogue reconciliation](../reference/Catalogue_Save_And_Refresh.md)
- [ ] Check all eight token examples through Add/Edit, including **This Work** with no direct Galleries. Verify the paired image opens the Gallery while displaying the correct Work, and that a hidden pair contributes both associations. Compare the originating section and pin with the incoming Catalogue backlink. Add and then remove an explicit link to the same Work to verify both directions and deduplication.
- [ ] Run focused static checks, inspect public code projection with `bin/site-code-update`, then run `bin/site-code-update --check` and `bin/site-validate`. Complete the bounded implementation and defensive-behaviour review. Update Source Editing, Catalogue references, Related Links and Generated Data Contracts at acceptance. Coordinate queued public data with the matching reader for release. Publish and deployment retain their existing separate actions. [Verification](../development/Verification.md) · [Development checklist](../development/Development_Checklist.md)
