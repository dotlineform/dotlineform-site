---
draft: false
doc_id: d-20261126-214901-b9fd03
title: Publish A Text Edition
added_date: "2026-11-26 21:49:01"
last_updated: "2026-11-26"
summary: Prepare a web edition in Texts and link it to its Catalogue Work.
parent_id: d-20261118-235100-64ad2e
---
# Publish A Text Edition

**Texts** is the collection for reading poems, stories and longer works on the site. **Writing** is the Catalogue Gallery for discovering the corresponding Works. The first planned web edition is *nerve*, Catalogue Work `00008`. Its Catalogue entry describes the 48-page loose-bound book and offers the PDF. The separate *nerve* Context draft contains an excerpt and an account of how the work was written and compiled.

## Author And Link The Edition

1. In Docs Viewer Manage, open **Texts** beside Catalogue in the Index. Use **Collection Actions → New doc…** or **Import doc…** to start an edition. Review the complete text, headings, line breaks and illustrations in the web reader. [Author and organise documents](../guide/Author_And_Organise_Documents.md)
2. In the edition’s Source, use **Insert doc link** to add a **Catalogue entry** link to the exact Work. For *nerve*, choose `00008`. On Save, the relationship also supplies a link from the Work’s generated **context** section. [Related Links](../reference/Related_Links.md#generated-data-and-freshness)
3. For a prominent reading link, open the Work in Studio and choose **Add link**. Use **Read nerve online** and the public edition URL, in the form `https://www.dotlineform.com/?collection=texts&doc=<edition-id>`. Save the Work, run **Refresh Catalogue**, then **Regenerate** in Docs Viewer Manage. The link appears with the Work’s other resources. [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md)
4. When the edition is ready, mark the **Texts** landing page and the edition ready. Choose **Actions → Refresh Search and Recent** to include their titles in Portfolio Search. Publish the edition, refreshed Work and queued search data. In public preview, follow the Catalogue reading link and the edition’s link back to the Work, and find the edition by title. Then deploy the reviewed site. [Publish and deploy](../guide/Publish_And_Deploy.md)

Keep the existing PDF available as the fixed-page version. A later EPUB can be offered as a separately labelled download. A hosted EPUB can be linked now. Docs Viewer’s **Add file** would need `.epub` support to attach it directly. [Export Book](Export_Book.md)

## Draft Setup

- [x] Register `texts` as a document and media owner, with a draft Index host and the standard Manage collection actions.
- [x] Use an A–Z public list and keep alternate sorting available in Manage.
- [ ] Review Texts in Manage and author the *nerve* web edition. Check both directions of the link in public preview when the edition is ready.

Registration established an empty public manifest in Working and queued that initial artifact so the landing page can open when released. The ordinary host’s draft status controls public eligibility. The local Docs Viewer service returned the draft host and the empty Manage manifest after generation.
