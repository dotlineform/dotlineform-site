---
draft: false
doc_id: d-20261126-214901-b9fd03
title: Publish A Text Edition
added_date: "2026-11-26 21:49:01"
last_updated: "2026-11-27"
summary: Prepare a web edition in Texts and link it to its Catalogue Work.
ui_status: done
parent_id: d-20260728-113139-763354
---
# Publish A Text Edition

**Texts** is the collection for reading poems, stories and longer works on the site. **Writing** is the Catalogue Gallery for discovering the corresponding Works. *Nerve* was the first Texts web edition. Its Catalogue entry, Work `00008`, describes the 48-page loose-bound book and offers the PDF. The separate *nerve* Context draft contains an excerpt and an account of how the work was written and compiled.

## Author And Link The Edition

1. In Docs Viewer Manage, open **Texts** beside Catalogue in the Index. Use **Collection Actions → New doc…** or **Import doc…** to start an edition. Review the complete text, headings, line breaks and illustrations in the web reader. [Author and organise documents](../guide/Author_And_Organise_Documents.md)
2. In the edition’s Source, use **Insert doc link** for a text link to the Catalogue entry. For an image link, use **Directives → Add Catalogue reference**, select the Work, and choose **Catalogue entry** under **Opens**. On Save, the relationship also supplies a link from the Work’s generated **context** section. [Catalogue image destination](Catalogue_Reference_Image_Destination.md) · [Related Links](../reference/Related_Links.md#generated-data-and-freshness)
3. To add a separate reading link among the Work’s resources, open the Work in Studio and choose **Add link**. Give it a label such as **Read nerve online** and use the public edition URL in the form `https://www.dotlineform.com/?collection=texts&doc=<edition-id>`. Save the Work, run **Refresh Catalogue**, then **Regenerate** in Docs Viewer Manage. [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md)
4. When the edition is ready, mark it and its **Texts** landing page ready. Choose **Actions → Refresh Search and Recent** to include their titles in Portfolio Search. Publish the edition, the Work document and queued search data. In public preview, follow both links and find the edition by title. Then deploy the reviewed site. [Publish and deploy](../guide/Publish_And_Deploy.md)

Keep the existing PDF available as the fixed-page version. A later EPUB can be offered as a separately labelled download. A hosted EPUB can be linked now. Docs Viewer’s **Add file** would need `.epub` support to attach it directly. [Export Book](../_working/Export_Book.md)

## Nerve Delivery

Closed on 27 November 2026. The tracked public snapshot contains the ready **Texts** landing page and the ready *Nerve* edition `d-20261127-100053-b77c4f` in the collection manifest. Both titles appear in Portfolio Search. The edition’s cover image opens Work `00008`, and the Work’s generated **context** section links back to *Nerve*. The user confirmed the updated image token in site-preview. [Current collection behaviour](../reference/Collections_And_Books.md#texts) · [Authored reading pages](Authored_Page_Breaks_For_Texts.md)
