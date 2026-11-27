---
draft: false
doc_id: d-20260725-153656-516b61
title: Semantic Tokens
added_date: "2026-07-25 15:36:56"
last_updated: "2026-11-20"
summary: Explain current Catalogue media and image tokens, authoring, document relationships, and the public boundary.
parent_id: d-20260424-000000-50b63f
---
# Document and Catalogue References

Source stores exact targets and the author's presentation choices. Use **Insert doc link** for an ordinary Markdown document link, **Add Catalogue reference** for a Work image, text opener or hidden Work/Gallery association and **Add image** for a Docs-owned image. [Source editor](Source_Editing.md#directives) · [Related Links](Related_Links.md)

## Supported Source Forms

```text
[[catalogue:media:work:00638|3 symbols]]
[[catalogue:media:work:00638:visible=false|3 symbols]]
[[catalogue:media:gallery:179|details]]
[[catalogue:media:gallery:179:visible=false|details]]
[[catalogue:image:work:00638|use_work_title_caption=true&placement=left&fill_width=true]]
[[catalogue:image:work:00638|use_work_title_caption=true&placement=left&fill_width=true&open_entry=true]]
[[catalogue:image:work:03188:gallery:005|use_work_title_caption=true&placement=full&fill_width=true&gallery_label=3%20symbols]]
[[catalogue:media:work:03188:gallery:005|Explore the Gallery]]
[[catalogue:media:work:03188:gallery:005:visible=false|3 symbols]]
[[catalogue:entry:work:00638]]
```

Use a five-digit Work ID. A Gallery ID has three digits or at least four digits with no leading zero. The required Media View label is literal single-line text. The serializer escapes backslash, pipe and closing bracket. Append `:gallery:<id>` to a Work identity to select the Gallery that opens. Media links are visible by default. **Hidden** adds `:visible=false` after the complete identity and retains every selected association. Direct Gallery links also accept their existing `:visible=true` spelling. Gallery images, Series and Detail targets, Concept tokens and the old three-part Catalogue text form are retired. Document Subjects and **Use document subject** are retired. [Subject retirement](../deliveries/Subject_Retirement.md)

## Catalogue Image

Work image fields use canonical percent encoding and field order. The required fields are `use_work_title_caption`, `placement` and `fill_width`. Optional `summary` follows the caption choice. Left placements may append `left_size=third` or `left_size=thumbnail` after `fill_width`. A thumbnail requires `fill_width=false`. Omitted size uses half width on the left. The caption and alt come from the pictured Work. A paired image ends with `gallery_label`, the Gallery title captured on selection. The Gallery row and opener use this saved label until the author reselects the destination. **Include Work metadata** was retired and migrated out of Working source. Full metadata belongs to Entry.

**Opens → Catalogue entry** appends `open_entry=true` to a Work image. The image links to the pictured Work's exact Catalogue document. A Work image without that field opens in Media View. A Gallery-paired image uses its Gallery as the Media View destination.

### Wrap Body Text

Choose a left or right placement and **Wrap body text** to serialize `wrap-left` or `wrap-right`. Put the token on its own line with a blank line before prose. A new heading starts at full width, and narrow reading columns stack the image and text. The other placements are `full`, `left` and `right`. Both image families render optional summary emphasis and escapes with the restricted summary formatter. Docs-owned image summaries also render inline TeX. Links, HTML and other Markdown in image summaries are literal. [Summary formatter](../../docs-viewer/build/docs_builder/summary_formatting.py) · [Math syntax](Source_Editing.md#math)

### Docs-Owned Images

```text
[[image:docs/img/example.jpg|alt=Evening%20light&placement=full&fill_width=true]]
```

Use the exact registered `img` or `svg` logical path under the document's owner. Slash separators stay literal. Segments and fields use canonical UTF-8 percent encoding with uppercase escapes. Field order is required `alt`, optional `caption`, optional `summary`, required `placement` and required `fill_width`. Optional text fields are independent. Build emits an escaped figure with no caption block when both optional fields are empty. **Thumb** separately assigns document thumbnails. [Image grammar](../../docs-viewer/services/docs_image_tokens.py) · [Media and asset handling](Media_And_Asset_Handling.md#assigned-document-thumbnails)

## Source editing

Invoke the matching Add action with the caret strictly inside a supported token or with its exact range selected to open Edit. Editing loads stored fields. For new text or hidden links, selected source text supplies the label. Otherwise the destination title follows the selection until the author edits it. Edit treats reopened text as authored, even when it matches the previous title. A saved Gallery outside current direct membership stays selected until the author changes it. Apply uses the captured range, buffer revision and mounted editor to update only the dirty source. Cancel leaves the buffer intact. Save writes the complete source and awaits exact generation and fresh display. Inline, fenced and indented code, preformatted HTML and comments are inactive. Unsupported forms remain literal. [Catalogue modal](../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js) · [Source editor ownership](Source_Editing.md)

## Catalogue Target Lookup

Manage's `/docs/catalogue-media-targets` returns exact Work IDs and titles from the Working Catalogue `manage-manifest.json` and Gallery titles and direct memberships from Studio’s `galleries/report-search.json`. The `docs_catalogue_media_targets_v2` response includes `targets` and `gallery_ids_by_work`. The browser searches those targets, ranks Gallery ahead of Work for equal scores and uses the selected identity on Apply. Thumbnail previews use the shared rendition policy. The Source editor and Build parsers define the supported forms and exact ID syntax. [Lookup service](../../docs-viewer/services/docs_catalogue_media.py) · [Picker search](../../docs-viewer/runtime/js/management/source-editor/catalogue-media-targets.js) · [Source editor parser](../../docs-viewer/runtime/js/management/source-editor/source-token-parser.js)

## Build and Runtime Resolution

Regenerate owns the identity-only Entry. Build permits one Entry in the matching Catalogue Work document. Entry has no Source action. Build prepares ordered Catalogue references and rendering slots using adopted Work data, and the reader activates exact Work or Gallery presentations on demand. Visible occurrences emit a slot. Build collects both associations before suppressing hidden slots. On a paired image the Work supplies renditions and caption, and the saved Gallery supplies the opening destination. Export uses prepared static content. [Generated data contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation) · [Media View](Catalogue_Media_View.md) · [Token parser and renderer](../../docs-viewer/build/docs_builder/source_tokens.py)

## Catalogue Identity and Document Associations

Catalogue owns Work and Gallery identities. Work occurrences can link to exact Catalogue documents. Gallery occurrences can open Media View, contribute Gallery rows and supply Context manifest IDs. Projects follows typed Catalogue references to explicit Series and project-folder associations. These uses keep media identity and document relationships distinct. [Related Links](Related_Links.md) · [Media View link sources](Catalogue_Media_View.md#what-links-appear) · [Projects inputs](../deliveries/Subject_Retirement.md#existing-reference-inputs-for-projects)

## Document Relationships and Audit

The relationship builder handles authored document endpoints. Broken Links separately diagnoses exact document and Catalogue/media availability. Docs Media uses parsed image occurrences for asset ownership. Search excludes active Docs image tokens and all hidden Catalogue tokens from ordinary text extraction. The former usage-index report is retired. [Relationship and freshness](Related_Links.md#generated-data-and-freshness) · [Broken Links](Broken_Links.md) · [Search source boundary](Reader_Discovery_And_Return.md#source-boundary)
