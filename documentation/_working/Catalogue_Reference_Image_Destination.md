---
draft: false
doc_id: d-20261127-105035-8fb2a6
title: Catalogue Reference Image Destination
added_date: "2026-11-27 10:50:35"
last_updated: "2026-11-27"
parent_id: d-20261118-235100-64ad2e
---
# Catalogue Reference Image Destination

In Source, **Add Catalogue reference** and **Edit Catalogue reference** expose **Catalogue entry** under **Opens** for a Work image. The selected Work supplies both the image and the entry identity. Media View is the default. A Work image can open its Work or a selected Gallery in Media View. The Gallery, inline-link and hidden-association workflows retain their authored choices.

The browser owns the destination choice and writes it into the Source buffer. Source Save uses the current persistence and exact generation path. The builder parses the optional image field and carries it into the prepared reference. The reader uses the current route to create a document link, and static rendering uses its normal document-link convention. The image retains its Work media and authored presentation.

- [x] Add the Source command, destination choice and exact round trip through the JavaScript and Python token parsers.
- [x] Render the selected destination in the reader and static HTML. Update the maintained reference pages.
- [x] Complete focused diagnostics, public projection and redundancy review.
- [ ] Open a Work image from a saved document and verify the exact Catalogue entry and Back behaviour in Manage. Check an existing Media View image alongside it.

Read-only diagnostics recovered the saved choice for Work `00008`, resolved the local and public document routes, and rendered exact Work and Gallery Media View controls and a Catalogue entry link in static HTML. Focused JavaScript and Python lint, public projection and site validation passed.

The destination uses the Work identity already selected in the picker. Source parsing rejects simultaneous Gallery and Catalogue entry destinations through its existing canonical serialization check. The reader reuses the prepared rendition and normal document routing. Static export selects the rendered image and skips the extra full-size Media View asset for entry links. The change adds no lookup, rebuild or write beyond the existing Source Save workflow.
