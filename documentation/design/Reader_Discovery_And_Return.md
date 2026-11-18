---
draft: false
doc_id: d-20261118-201600-791bc2
title: Reader Discovery And Return
added_date: "2026-11-18 20:16:00"
last_updated: "2026-11-18"
summary: Decisions about independent discovery views, bounded caller retention and collection reading order.
parent_id: d-20261118-151521-a0f9c3
---
# Reader discovery and return

## Discovery beside reading

Search and Recent belong in the Index panel so a reader can keep results available while opening several documents. The hidden tree can track the current document without changing the visible results or moving focus. A title-only Portfolio scope supports broad discovery, while separate collection corpora give full-text or title-and-summary matching where those fields help. The Catalogue keeps its Work and Gallery filters beside the list they control. [Index and Recent delivery](../deliveries/Index_Search_And_Recent.md) · [Scope delivery](../deliveries/Public_Index_Search_Scopes.md)

## A caller for return, a snapshot for browsing

Retaining one caller lets Back restore a live report and its reading position without a fresh load or repeated report work. Releasing older mounts bounds the retained data and subscriptions. Lightweight tab snapshots let a later collection-host opening resume its controls against the current list even after that caller has gone. Shareable queries use URL parameters, so initial entry has explicit search intent independent of the tab's browsing history. [Navigation delivery](../deliveries/Document_View_And_Return_Navigation_Delivery.md) · [Collection index shortcut delivery](../deliveries/Document_Index_Navigation_Delivery.md)

## The invoking order matters

A collection list knows which Works or documents the reader is browsing. Capturing its order at opening gives Previous and Next stable neighbours while the reader moves through that sequence. Book's generated TOC can supply a web order on direct entry. A Gallery's Media View owns its image sequence and returns within its invoking document. [Current return behaviour](../reference/Reader_Discovery_And_Return.md#exact-document-navigation-and-return)

## Static Shuffle Stock

Prefetched random bytes use the existing static delivery path and ordinary caching, keeping browsing independent of an external service's availability, latency and quota. A finite stock deliberately provides a finite set of underlying permutations for a fixed input order. Browser cryptographic randomness chooses file order and starting positions independently; it does not replace the stock's swap draws. Explicit stock replacement can change reconstructed passes. A live service, credential relay or silent alternative random source would change this model and needs its own decision. [Current algorithm and maintenance](../reference/Catalogue_Shuffle_Randomness.md) · [Original comparison and provenance](../deliveries/Catalogue_Shuffle_Stock.md)
