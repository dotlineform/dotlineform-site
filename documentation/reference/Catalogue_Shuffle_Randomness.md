---
draft: false
doc_id: d-20261112-214201-1a6913
title: Catalogue Shuffle Randomness
added_date: "2026-11-12 21:42:01"
last_updated: "2026-11-18"
summary: Where the Catalogue shuffle bytes come from, how the browser uses them, and how far one file can go.
parent_id: d-20260728-113139-763354
---
# Catalogue Shuffle Randomness

Implemented reader behaviour. [Reader discovery](Reader_Discovery_And_Return.md#catalogue-collection-browsing) owns List/Gallery controls and return; this page owns the byte stock, algorithm, capacity and replacement.

## Stock And Serving

Catalogue uses 64 raw binary files, `01.bin` through `64.bin`, under [site/assets/data/catalogue-shuffle](../../site/assets/data/catalogue-shuffle/). Each is 32,768 bytes; the stock totals 2,097,152 bytes. Manage and Public read that same repository stock from their own origin. These are tracked site data, outside document generation/publication and the canonical runtime projection inventory.

The original stock's recorded source is a 12 November 2026 LfD quantum-random request, decoded from hex and split consecutively. The files contain bytes without a header or provenance receipt. [Origin and worked example](../deliveries/Catalogue_Shuffle_Stock.md) · [Why prefetch](../design/Reader_Discovery_And_Return.md#static-shuffle-stock)

## Draws And Permutations

[`shuffleCatalogueWorks`](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) fetches one file and requires its exact size. It copies the supplied Work order, reads unsigned 32-bit values most-significant byte first and performs Fisher–Yates from the last slot backwards. There are 8,192 candidate draws per file; `n` Works require `n − 1` accepted draws.

For `choices` remaining slots, values at or above `2^32 − (2^32 mod choices)` are rejected. Each accepted value selects `draw mod choices`. Discarding that partial interval avoids modulo bias. Rejection uses another draw from the same file.

The report supplies its current addition-day/title/identity order. For fixed input order and bytes, a file reproduces one permutation; the stock therefore supplies at most 64 underlying permutations for that order. Browser `crypto.getRandomValues()` separately randomizes file order and each pass's starting position. It does not replace the file's swap draws.

## Cycles, Return And Capacity

[The report](../../docs-viewer/runtime/js/shared/docs-collection-report.js) keeps independent List/Gallery pass controls and displayed Work identities in its tab snapshot. A live pass reuses its permutation. Restoring controls after releasing that permutation can fetch the same file through ordinary HTTP caching. Changed stock or input order can change reconstruction.

List rolls reveal up to 64 Works. Gallery adds eight at a time, skipping a final remainder smaller than eight. Each mode consumes its file order before starting another cycle. Detailed view/return rules remain with Reader Discovery.

The error **The shuffle batch ran out of draws for this Catalogue** means another accepted draw was needed after file exhaustion. At 8,193 Works every candidate must be accepted; at 8,194 or more the file is always too small. Smaller lists can also exhaust a file through rejections. A failed request, wrong size or exhaustion is reported by the existing report owner; there is no live QRNG request or replacement random source.

## Replace The Stock

1. Request `https://lfdr.de/qrng_api/qrng?length=2097152&format=HEX`. The provider's documented `length` is bytes, and `qrn` represents each byte with two hex digits. Check the returned length and decoded bytes are exactly 2,097,152. [Provider API documentation](https://www.lfdr.de/QRNG/)
2. Split the decoded stream in order into 64 raw 32,768-byte files with the existing names. This is explicit stock replacement, separate from Save, Search or Publish.
3. Review the replacements in Git and release the committed site snapshot through the normal Pages path. Local readers serve the repository files. Existing saved pass controls can reconstruct different Works after replacement; ordinary HTTP caching is not a content-version promise.

Changing file count/size also requires its reader contract to change.
