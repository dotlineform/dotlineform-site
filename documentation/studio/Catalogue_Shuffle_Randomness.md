---
draft: false
doc_id: d-20261112-214201-1a6913
title: Catalogue Shuffle Randomness
added_date: "2026-11-12 21:42:01"
last_updated: "2026-11-12"
summary: Where the Catalogue shuffle bytes come from, how the browser uses them, and how far one file can go.
parent_id: d-20260728-113139-763354
---
# Catalogue Shuffle Randomness

## From quantum measurements to files

A quantum random bit generator (QRBG) converts measurements of a quantum process into a stream of random bits. The LfD laboratory exposes the output of its ID Quantique Quantis PCIe hardware through an API that takes a length in bytes. Each byte contains eight bits. With `format=HEX`, the API returns a JSON response whose `qrn` field represents each byte as two hexadecimal digits. For example, `46` represents the byte `01000110`. [LfD QRNG API](https://www.lfdr.de/QRNG/)

On 2026-11-12, we fetched 2,097,152 bytes (2 MiB) in one request. We decoded the hex and split the resulting stream in order into 64 consecutive files of 32,768 bytes (32 KiB) each. The files run from `01.bin` through `64.bin` under `site/assets/data/catalogue-shuffle/`. Each file starts directly with the random bytes. The file size and the grouping of bytes into numbers are choices made by Catalogue. Another consumer could read the same bytes in groups of a different size.

## From bytes to shuffle draws

The browser uses `crypto.getRandomValues()` to choose the order of the 64 files and independently choose the starting position of each pass. It fetches one file from the site's own origin at the start of a pass and reads it four bytes at a time, most significant byte first. Each group gives one unsigned 32-bit integer in the range 0 to 4,294,967,295, so each file supplies 8,192 candidate draws. The first four bytes of the original `01.bin` are `46 98 58 70`. Together they make the integer `0x46985870`, or `1,184,389,232` in decimal. [Dice progression](../../docs-viewer/runtime/js/shared/docs-collection-report.js) · [Shuffle implementation](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js)

Fisher–Yates starts at the last slot and works backward through the list. At each step, it selects one of the remaining Works, including the Work already in that slot, and swaps the selected Work into place. A shuffle of `n` Works needs `n − 1` accepted draws because the final Work is already in place.

The range of a 32-bit integer does not always divide evenly by the number of remaining Works. With ten Works left, for example, `2³²` leaves a remainder of six when divided by ten. Catalogue skips the six highest values and takes the remainder modulo ten for each accepted value. Each slot then has the same number of input values that select it. A draw of `1,184,389,232` would pick index `2`, the third remaining slot.

### The first row of `01.bin`

The first row of the 64 × 64 bit grid shows the first eight bytes of `01.bin`, `46 98 58 70 94 d4 93 cd`. Those 64 bits give two draws. Using the repository's public Catalogue snapshot of 5,196 Works in its default order, both draws were accepted and fixed the last two slots. Slot numbers below start at 1. [Public Catalogue manifest](../../site/assets/data/docs/catalogue/manifest.json)

| Draw | Remaining Works | Slot picked | Work | Final slot |
| ---: | ---: | ---: | --- | ---: |
| 1,184,389,232 | 5,196 | 2,601 | `04169` · *form 61* | 5,196 |
| 2,496,959,437 | 5,195 | 3,468 | `00393` · *model 500* | 5,195 |

Each draw selects a slot, and the entry at that slot supplies the Work ID. The first swap moved `04435` to slot 2,601 and the second moved `04433` to slot 3,468. Later draws could still move those two Works.

## Capacity and repeatability

The error **The shuffle batch ran out of draws for this Catalogue** means the browser reached the end of the file while it still needed another accepted draw. At 5,196 Works, a shuffle needs 5,195 accepted draws and can spare up to 2,997 rejections. At 8,193 Works, every draw has to be accepted. At 8,194 Works or more, the file is always too small.

The same file and starting Work order reproduce the same shuffle. For a fixed starting order and stock, the 64 files can produce up to 64 distinct permutations. Catalogue Discovery uses each file once per cycle in a randomly chosen order, and independently chooses where to start each pass. The tab saves the file order, current file, starting position and progress. The browser uses ordinary HTTP caching when it reads the current file again. A change to the file or the default Work order can produce a different result. [Catalogue browsing](Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) · [Stock origin and replacement](deliveries/Catalogue_Shuffle.md#stock-and-operation)
