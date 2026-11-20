---
draft: false
doc_id: d-20261120-130501-7ffcb1
title: Media View Link Authoring
added_date: "2026-11-20 13:05:01"
last_updated: "2026-11-20"
summary: Accepted Source authoring for Work images and Gallery links, the relationship migration, and text-focused Docs Review.
ui_status: done
parent_id: d-20260903-154141-7c9e4b
---
# Media View Link Authoring

Accepted and closed on 20 November 2026. A single Source action can show a Work image, open a directly selected Gallery and retain the Work’s backlink to the referring document. The same action creates inline and hidden links. [Source editing](../reference/Source_Editing.md#directives) · [Source forms](../reference/Document_And_Catalogue_References.md#supported-source-forms)

## Authoring decisions

Opening **Directives** resolves the selection once. The menu item, tooltip and modal say **Edit Media View link** when the caret is inside a supported token or the selection covers it exactly. Otherwise they say **Add Media View link**. The modal uses that same result. Reopening a token treats its saved link text as authored, so changing destination preserves it. For a new link, an untouched default follows the destination title.

**Open in Media View** shows four rows, starting with **This Work** selected for a new Work. Only direct Gallery memberships follow. Edit preserves a saved Gallery even if the membership has since changed. **Display** offers Image, Inline link and Hidden as a single radio group. A directly selected Gallery defaults to Inline link. The browser owns these choices and Source Save owns persistence and generation. [Media View authoring](../reference/Catalogue_Media_View.md#authoring)

## Work identity and Gallery destination

A paired token identifies both the pictured Work and the Gallery that opens. The Work supplies the image, alt text and title caption. The saved Gallery label supplies the image button’s accessible name and its Related Links row. Hidden pairs also contribute both IDs to Context discovery. The picker gets direct membership from Studio’s existing Gallery search data in the same response as the target list. [Generated data contracts](../reference/Generated_Data_Contracts.md#catalogue-reference-and-presentation)

The version-5 Links record keeps one directed edge per document destination. The outgoing flag `explicit_doc_link` records whether an ordinary Markdown link also reaches that destination. A token alone gives the Work its backlink. Adding an explicit link adds the Catalogue document to the referring page’s Related Links. Removing it leaves the backlink and the selected Gallery intact. The pin captures the same list as the document. [Related Links](../reference/Related_Links.md)

## Migration and acceptance evidence

- The Working migration rebuilt relationships across ordinary documents and six collections. It produced 122 records and 70 directed edges, including 53 from Work tokens alone. It refreshed the Links report, changed two ordinary, six Context and 38 Moments document payloads, and queued 5,196 Catalogue document updates without selecting any Work image uploads. Existing Markdown required no bulk rewrite.
- In an isolated Working copy, all eight supported display and destination combinations were added and reopened. Work `02889` offered only **This Work**. For Work `03188`, “3 symbols (composite)”, the saved image button read “Open 3 symbols” and opened Gallery `005`. Back restored the document. A hidden Work `00001` / Gallery `009` pair contributed both associations without a body control.
- The body and pin showed the same Related Links. Adding and removing an explicit link toggled the outgoing Catalogue row while its incoming backlink survived. HTML Export retained the pictured Work’s caption and primary image and rendered the Gallery label as text. The export included only Works used by the document.
- Focused Python and JavaScript lint, tracked reader projection checks and site validation passed. The implementation review removed an obsolete anchor rewrite and a reader condition that prevented a Work image from opening a Gallery. Exact IDs, escaping and the editor’s selection revision guard remain at their owning boundaries. The author confirmed the Source workflow locally. [Verification](../development/Verification.md) · [Development checklist](../development/Development_Checklist.md#redundancy-and-defensive-behavior-review)

## Docs Review

The author chose to keep Docs Review focused on returned writing. For Catalogue tokens present in package Markdown, the preview shows inline labels and authored image summaries and omits hidden references. An unbundled Docs image can still contribute its caption and summary. The package builder uses the supplied document records for its tree and bodies. Richer media presentation can wait for a concrete review use case. [Docs Review](../reference/Docs_Review.md#build-and-asset-rendering)

Two returns were exercised through the package service in a disposable workspace. A four-document Context return showed the inline label in “catalogue randomness” and the image summary in “3 symbols”, and omitted the hidden Gallery in “kylie”. After an external heading edit, Build regenerated the changed preview with zero warnings and preserved all four package Markdown files byte for byte. A two-document Concepts return supplied replacement content and opened both generated bodies. These checks covered the service and generated content.

## Publication and release

Docs Publish completed on 20 November at 16:17 UTC and cleared the Docs and Catalogue queues. Its Git backups were `000b37d` in the Docs data repository and `02a33df3bd` in the site repository. The authoring and projected public reader changes reached `main` in `542ae0127e`. The Docs Review repair followed in `68de547c34`.

At closeout, the latest successful Pages deployment was the 10:03 UTC run for `7657c0f178`, before the content and reader updates. Deploy Public remained a separate manual release. [Pages deployment at closeout](https://github.com/dotlineform/dotlineform-site/actions/runs/44715918767)
