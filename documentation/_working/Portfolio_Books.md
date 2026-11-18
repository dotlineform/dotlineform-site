---
draft: false
doc_id: d-20261117-195407-09ee00
title: Portfolio Books
added_date: "2026-11-17 19:54:07"
last_updated: "2026-11-17"
summary: Curate downloadable books from the public portfolio collections, starting with Moments.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Portfolio Books

Catalogue, Context, Concepts and Moments are all candidates for downloadable books. **Moments is the first candidate.** Each book is an edited selection with its own reading order and opening and closing pages. The existing public collection is where readers browse the original material and find the finished book.

| Collection | Possible book |
| --- | --- |
| **Moments** | An anthology of selected pieces. Start with a few that exercise different line and stanza arrangements, including an axis-aligned piece such as *all the little cracks*. The existing Moments HTML snapshot already has styles for this verse. [Collection Export](../studio/Export.md#artifact-contract) |
| **Context** | A thematic selection of texts about Works, with an editorial sequence and the illustrations needed to read them offline. |
| **Concepts** | A sequence of essays organised around a subject or argument, with an introduction where it helps the reader. |
| **Catalogue** | A selection of Works, or several volumes grouped by Series, Gallery or theme. A literal work-per-page edition would be on the order of 5,000 pages before introductory material or Works that need more than one page. If a complete reference catalogue becomes a goal, define its audience, volumes and rendering separately. Canonical Work data is the inventory for that edition. [Catalogue concept](../deliveries/Analysis_Catalogue_Concept.md) |

## Author And Release Moments

1. Register a new curated Book with its own ordinary Index host and Book Tree, using the same model as Living Memory. Put the authored `[[toc]]` in the host. Add the **new Book host’s ID** to Working’s `unpublishable.json` before marking the host ready. The existing exclusion covers the host and its Book collection, so the TOC and chapters can be ready in Manage while the public Moments host and collection continue to serve the originals. [Book source ownership](../reference/Source_Organisation.md#book-source-and-provenance) · [Publication eligibility](../reference/Source_Organisation.md#operations)
2. Create independent Book drafts for the selected Moments pieces. Bring across the text and referenced media, arrange the chapters in the Tree, and add the cover, preface or back matter as needed. **Copy to Book** currently takes Library sources, so a small pilot can use individually created chapters. Consider a bulk copy only after deciding which pieces and source details the edition needs. [Book curation in Manage](../studio/Sub_Scope_Index_Architecture.md#book-curation-in-manage)
3. Use the proposed **Export Book** action to produce a local file from the ready export edition. Review the actual file with the intended reader apps before offering it on the existing public Moments page. Attach the approved PDF using **Add file**, then Save and Publish the public Moments page through its ordinary workflow. A direct EPUB attachment needs support for the `.epub` file type. [Export Book](Export_Book.md) · [Add a new image or download](../studio/Docs_Images_And_Assets.md#add-a-new-image-or-download)

Moments supplies the case where the Book has never had a web edition. Living Memory supplies the case where web and export editions can share chapters while using different opening or closing pages. Both use the same exporter. [Book editions](../studio/Sub_Scope_Index_Architecture.md#book-editions)
