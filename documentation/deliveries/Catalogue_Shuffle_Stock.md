---
draft: false
doc_id: d-20261118-231300-1fc986
title: Catalogue Shuffle Stock
added_date: "2026-11-18 23:13:00"
last_updated: "2026-11-18"
summary: Recorded origin, provider comparison and worked example for the Catalogue's original static random-byte stock.
parent_id: d-20261112-214201-1a6913
---
# Catalogue Shuffle Stock

## Recorded Origin And Decision

The original record reports a 12 November 2026 request for 2,097,152 bytes from the [LfD QRNG API](https://www.lfdr.de/QRNG/), decoding its hex response and splitting the stream consecutively into 64 raw 32,768-byte files, `01.bin`–`64.bin`. The provider describes Quantis PCIe hardware. The files have no headers or separate provenance receipt; this is retained history rather than an independent certification of their origin.

The November 2026 comparison recorded full batches from LfD and Padova, whose cross-origin policies blocked direct browser reads. Free Universe Splitter returned one seed-sized value; Qrypt's batch access required a bearer token and therefore a relay. Those observations explain the original choice and are not a current comparison of services. [Static-stock rationale](../design/Reader_Discovery_And_Return.md#static-shuffle-stock)

## Worked Original Snapshot

The first row of the recorded 64 × 64 bit grid used the first eight bytes of `01.bin`: `46 98 58 70 94 d4 93 cd`. Read as two big-endian 32-bit draws, these fixed the final two slots in the recorded 5,196-Work public snapshot's default order. Slots below start at one.

| Draw | Remaining Works | Slot picked | Work | Final slot |
| ---: | ---: | ---: | --- | ---: |
| 1,184,389,232 | 5,196 | 2,601 | `04169` · *form 61* | 5,196 |
| 2,496,959,437 | 5,195 | 3,468 | `00393` · *model 500* | 5,195 |

The swaps moved `04435` into slot 2,601 and `04433` into slot 3,468; later draws could move those Works again. Both draws were accepted. This illustrates the algorithm for that snapshot, not a promise about today's order. At that size a file allowed 2,997 rejected draws in addition to 5,195 accepted ones.

## Documentation Review Evidence

On 18 November, read-only inspection found 64 files totalling 2,097,152 bytes, each 32,768 bytes, with the same first eight bytes in `01.bin`. Reviewed the reader's fetch, Fisher–Yates/rejection, pass controls and return snapshots, and checked provider documentation. No replacement bytes, browser acceptance, document build, Publish or deployment occurred. [Current algorithm and maintenance](../reference/Catalogue_Shuffle_Randomness.md)
