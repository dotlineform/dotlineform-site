---
draft: false
doc_id: d-20261112-204203-de3fcd
title: Catalogue Shuffle
added_date: "2026-11-12 20:42:03"
last_updated: "2026-11-12"
summary: Shuffle the Catalogue collection with a reusable stock of quantum random bytes.
ui_status: in-progress
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Shuffle

## Requirements

Add a dice icon labelled **Shuffle** next to Search in Public and Working Catalogue. A click gives a new opportunity to browse the full Work list in a different order, from page one. Each shuffle holds its order through paging and retained Work navigation. Return via the collection icon or after visiting another page restores the shuffle and page within the same browser tab. Search uses the usual Catalogue results and clearing it restores the shuffled list. Library keeps its current browsing behavior and date metadata. Public collection controls offer the Catalogue Shuffle action while conventional sorting stays in Working.

## Stock And Operation

The separate [Catalogue Shuffle Randomness reference](../Catalogue_Shuffle_Randomness.md) explains the bytes, draw selection, capacity and repeatability with a worked example from the original download.

The initial stock is 2 MiB from the [LfD laboratory's Quantis QRBG](https://www.lfdr.de/QRNG/), fetched on 2026-11-12 as one unauthenticated HTTPS response and split into 64 consecutive 32 KiB files under `site/assets/data/catalogue-shuffle/`. The existing Working static handler serves the same files as the public deploy root. The browser picks `01.bin` through `64.bin` with `Math.random()` and reads one file on demand. Fisher–Yates uses its unsigned 32-bit values, discarding the incomplete interval at each shrinking bound to avoid modulo bias. Identical bytes and starting order produce the same permutation. Repeat selections are possible.

The existing tab snapshot saves the batch number alongside the page, query and sort. A retained view can reuse its prepared shuffle. A remount reads the same file with ordinary browser caching and recreates the order before rendering the page. Changing the stock or the starting inventory can change the restored order.

Replace the stock only when desired. Request 2,097,152 bytes using the documented LfD `qrng_api/qrng` endpoint with `format=HEX`, decode the `qrn` response and confirm the declared and decoded lengths. Split the completed stream into the same 64 numbered files of 32,768 bytes. Review the replacement in Git. Working serves the replacement from the repository and Public receives it through the next site deployment. The pool is independent of Studio Refresh, Docs generation and Publish queues.

## API Decision

Live service requests would make each click depend on a third-party response and quota. LfD and the University of Padova returned full batches without a key, and their CORS responses prevented dotlineform's browser from reading them directly. Free Universe Splitter allowed direct browser access and returned a single mixed-source value suitable as a seed. Qrypt could provide a full batch in one request. Its bearer token would need a relay such as Google Cloud Run with Secret Manager, and its published paid plan was US$2,000 per month for up to 2 GB. A prefetched static stock gives the Catalogue the quantum draws it needs and lets it reuse them across visitors. [LfD API](https://www.lfdr.de/QRNG/) · [Padova QRBG](https://qrng-qtech.vs-ix.net/) · [Free Universe Splitter API](https://freeuniversesplitter.com/about-api) · [Qrypt API](https://docs.qrypt.com/eaas/) · [Qrypt Marketplace pricing](https://aws.amazon.com/marketplace/pp/prodview-nnnpvfnemx226)

## Delivery Steps

- [x] Readiness. The shared collection report owns the loaded Work rows, paging and retained view. The existing static route serves the repository asset directly in both readers.
- [x] Implementation. Added the Catalogue control, downloaded and split the initial stock, and wired the browser shuffle and retained ordering.
- [x] Code review. Traced initial load, Shuffle, paging, search and clear, retained return, a fresh mount, a changed Working inventory, and failed batch reads. The browser fetches a single file per click, reuses loaded rows and retains the result for rendering and navigation. HTTP status and length checks protect the fetched binary boundary. Exhausted draws surface as an error and the current order remains usable. Disposed views ignore completion. The existing static file handler supplies the bytes without a new service or publication handoff. Focused JavaScript lint, whitespace, projection check and site validation passed. Verified 64 files of 32,768 bytes and matched the bytes for `01.bin` served by both Working and Site Preview to the repository file.
- [x] Tab restore and dice icon follow-up. Reviewed remount, retained return, search, Working sort and failed file reads. The browser accepts only a saved integer in the published batch range, reuses a matching retained shuffle and otherwise loads one batch. It displays the list only after restoring the order and page. A failed read displays an error and uses the ordinary list. Focused JavaScript lint, whitespace, projection and site validation passed. The projected icon matches the supplied SVG.
- [ ] Closeout. The user confirmed that the initial implementation retained the shuffled list on browser Back. Review the dice control and tab restore in Working and Site Preview by shuffling, moving past page one, opening a Work and returning via the collection icon, visiting another page and returning, and searching then clearing. Deploy through the normal public workflow after acceptance. Retain this delivery as the source and API decision record.
