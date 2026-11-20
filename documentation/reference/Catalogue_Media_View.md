---
draft: false
doc_id: d-20260903-154141-7c9e4b
title: Catalogue Media View
added_date: "2026-09-03 15:41:41"
last_updated: "2026-11-20"
summary: Exact Work and Gallery links, direct and Series-related Gallery navigation, responsive Work images and paginated Media View, with static-consumer and public-data limits.
ui_status: done
parent_id: d-20260519-000000-a0da45
---
# Catalogue Media View

Media View opens an exact Catalogue Work or Gallery in the Docs Viewer main pane. Working and public use the same view and read Catalogue data for their own route. [Reader workflow](../guide/Find_And_Read_Things.md) · [Generated data contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation)

## What links appear

| Surface | Links and their source |
| --- | --- |
| **Work in Media View** | The image caption shows the Work title and a `cat.` link to the exact Catalogue document in the current viewer, retaining the Index search. Gallery links list direct memberships first, then distinct Galleries explicitly related to the Work's Series. The invoking Gallery or Discovery grid also has a return link. Context rows list documents whose built references name that exact Work. |
| **Gallery in Media View** | The Gallery title and member grid use the exact Gallery record. Each Context document appears once if it names the Gallery through a visible or hidden Gallery token, or names a Work anywhere in its member list. |
| **Work's Catalogue document** | Entry shows the image, Work metadata and resources. A separate Gallery section uses the adopted direct and Series-related links. The generated `[[links|context]]` section lists the Work document's incoming and outgoing relationships, which can include documents in collections other than Context. A reader can pin that list in Info. [Related Links](Related_Links.md) |

**If expected Context links are missing**, check the referring document's collection and its exact Work ID. A Work image or Work Media View token in Context supplies that ID. An ordinary Markdown link to the Catalogue document contributes to its document relationships only. Referring to a Gallery can give that Gallery a Context link without giving every member Work the same link. The `context` heading on the Catalogue document names its Related Links section and places no collection filter on that list. [Document and Catalogue references](Document_And_Catalogue_References.md) · [Related Links](Related_Links.md#generated-data-and-freshness)

Save the referring Context source or rebuild the exact saved document. Generation writes the distinct `work_ids` and `gallery_ids` as optional `catalogue_targets` on its manifest row. Working can show draft Context rows and reads the current manifest once per Media View opening. Public shares a lazy page-session read of eligible rows. Check the publication queue and deployed snapshot for a public change, then reload the public reader. **Context links are unavailable.** means the manifest read failed. A successful read with no matches omits those rows. The image or grid is usable while these links load. [Context projection](../../docs-viewer/services/docs_generation.py) · [Reader provider](../../docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js) · [Publication workflow](../guide/Publish_And_Deploy.md)

For missing **Gallery links**, check direct Work membership and the separately authored Series–Gallery association. Refresh generates the current inputs, including `series-galleries-index.json`. Regenerate adopts the affected Work's data into its Catalogue document. Open the updated presentation in Working, then follow the ordinary queue and deployment for Public. Missing image or Gallery data is a separate exact-target failure. [Catalogue Save and Refresh](Catalogue_Save_And_Refresh.md) · [Catalogue workflow](../guide/Maintain_The_Catalogue.md) · [Broken Links](Broken_Links.md)

## Authoring

Choose **Directives → Add Media View link** in Source. Selecting a Work defaults to its image and **This Work**. Choose a direct Gallery under **Open in Media View** to open its grid while showing the Work image. A directly selected Gallery defaults to **Inline link**. **Hidden** records the selected associations and omits the body control. Save or rebuild the document to update the reader. [Source forms and editing](Document_And_Catalogue_References.md#supported-source-forms)

## Gallery Presentations

A Gallery reads one exact `gallery_record_v3` via `/docs/catalogue-gallery?gallery_id=…` in Working or the configured Gallery records base in Public. The browser orders the loaded members by natural, case-insensitive title with exact Work ID as the tie-breaker. Only the active page of thumbnails is mounted, with up to 64 per page. Empty Galleries show an empty state. A Work's full presentation is read by exact ID when selected. Previous and Next follow the invoking Gallery sequence. The invoking Gallery link returns to the page containing the selected Work. An unavailable or superseded selection leaves the current view in place. [Shared Media View](../../docs-viewer/runtime/js/shared/docs-viewer-media-detail.js)

In Public, Work images and Gallery grids share a layout based on the width inside the Media View panel. At 36rem or wider, the metadata sits alongside the image or grid. In a narrower panel it follows below. Gallery thumbnails wrap to the available column width at their normal size, keeping the active page in its existing order. [Reader stylesheet](../../docs-viewer/static/css/docs-viewer.css)

The Content Detail host owns the outer **Back** and **Open in new tab** controls. Back restores the invoking document or result context, scroll and focus. A link from a pinned Related Links list opens against the document displayed when selected. [Info Panel](Info_Panel.md) · [Reader return rules](../guide/Find_And_Read_Things.md)

## Discovery Grid

In the unfiltered Catalogue **List**, **Open selection in Media View** passes its displayed IDs, titles and thumbnails in order for up to 64 Works. **Catalogue Discovery** returns from a Work to that grid. Outer Back returns to the List opener. The rolling Catalogue Gallery opens Work documents directly. [Reader workflow](../guide/Find_And_Read_Things.md)

## Data and consumers

Media View resolves the selected Work through the adopted Catalogue by-ID payload and configured rendition roots. Build prepares inline image renditions and reference slots for rendered documents. The shared renderer uses actual rendition widths and measures the responsive slot. **Open in new tab** uses the prepared full-image target. Export and content-bearing Prepare package use the shared static preparer. Docs Review uses its package contract. [Adoption](../../docs-viewer/services/docs_catalogue_projection.py) · [Catalogue renderer](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-rendering.js) · [Export](Export.md) · [Prepare package](Document_Packages.md) · [Docs Review](Docs_Review.md)

The design explains how Media View and document relationships fit together. The delivery records cover the reader and the Source authoring workflow, including the migration and backlink checks. [Design rationale](../design/Media_View_And_Document_Relationships.md) · [Reader delivery](../deliveries/Media_View_And_Document_Relationships_Review.md) · [Media View link authoring](../deliveries/Media_View_Link_Authoring.md)
