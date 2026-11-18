---
draft: false
doc_id: d-20261117-202611-8119c2
title: Site Optimisation
added_date: "2026-11-17 20:26:11"
last_updated: "2026-11-17"
summary: Measure public site payloads and loading, then choose improvements from the observed costs.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Site Optimisation

Understand what the public site loads to open a page and what it fetches as the reader moves through it. Start with representative entry, collection, search, document and media routes. Measure transferred bytes, request counts and the time until the visible content is usable. Compare cold and warm caches on representative devices and connections before selecting a first change. [Public execution path](../studio/Docs_Viewer_Runtime.md#public-execution-path) · [Generated data contracts](../studio/Generated_Data_Contracts.md)

## Catalogue And Media View

- Measure the initial Catalogue view, successive dice rolls, List and Gallery toggles, opening a Work and returning, and Media View page changes. Record image requests and revalidations, transferred bytes and time until the first visible thumbnails are usable.
- Separate the Catalogue manifest, the 32 KiB shuffle file at a pass boundary, thumbnail transfers, and the larger image fetched when a Work opens. A Gallery roll adds at most eight thumbnail elements. Check the requests and transferred bytes when surviving columns shift and when the reader returns to a retained view.
- Measure a full Media View page of 64 thumbnails. Compare it with the former 48-thumbnail page if a comparable baseline is available. Count a `304` as a revalidation with no image body transfer and a network `200` with a body as a transfer. [Catalogue browsing](../studio/Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) · [Shuffle stock](../studio/Catalogue_Shuffle_Randomness.md) · [Gallery presentations](../studio/Catalogue_Media_View.md#gallery-presentations)

## First Readiness Review

- [ ] Agree the representative routes, devices, connection conditions and cache states for a baseline. Use the baseline to identify which payloads and requests matter to the reader.
- [ ] Choose the first improvement and how to check it. Visible-thumbnail loading, request priority, thumbnail renditions and cache policy are candidates. Set targets after seeing the measurements.

Pane width and touch behaviour have their own review. [Mobile Layouts](Mobile_Layouts.md)
