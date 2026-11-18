---
draft: false
doc_id: d-20261118-180200-5de1c9
title: Document Media And Thumbnails
added_date: "2026-11-18 18:02:00"
last_updated: "2026-11-18"
summary: Decisions behind per-document media ownership, independent list artwork and selected publication.
parent_id: d-20261118-151521-a0f9c3
---
# Document media and thumbnails

## Ownership at Save

The document ID gives each document its own readable filenames and an exact deletion boundary. Two documents can use different files named `photo.webp`. When text moves between documents, Save copies the foreign ready bytes and rewrites the references while the original bytes are still available. This gives each document an independent lifecycle without a shared asset registry or reference counts. Exact byte equality makes adoption repeatable, and differing bytes at one destination leave the filename decision with the author. [Media adoption](../reference/Media_And_Asset_Handling.md#source-save-media-adoption)

Native intake keeps the chosen files with the dirty editor until Save. The browser already knows which pending references survive. Python owns preparation and storage and writes selected media before source, so committed references have their required file bytes. The loaded saved body and candidate already establish which owned references disappeared. Persisting only completed queue effects avoids another media baseline or another interpretation of source at Publish. An external edit whose previous body was never supplied or a partial write can leave Working files for manual cleanup. [Exact removals](../reference/Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Separate presentation choices

Document thumbnails belong to list presentation. An independent file lets an author choose artwork from a rendered image or another exact Catalogue Work and change it without editing source or keeping the source image in the body. File presence stays authoritative after a rebuild. Style and sizing for body images remain occurrence choices, including the optional image-detail opener. [Thumbnail workflow](../reference/Media_And_Asset_Handling.md#assigned-document-thumbnails) · [Image detail](../reference/Document_Image_Detail.md) · [Subject retirement](../deliveries/Subject_Retirement.md#manual-thumbnail-authoring)

## Stable references and selected transfer

Canonical source expresses the logical identity while the configuration selects the serving and publication locations. This let the R2 namespace move without rewriting those source identities. Publish applies exact writes and removals already selected in Working. R2 removal can precede the Pages deployment of the document change. The workflow accepts that interval and keeps the deploy decision explicit. Inventory and orphan reports support human review as separate operations. [Publication lifecycle](../reference/Media_And_Asset_Handling.md#link-resolution-and-delivery) · [Migration evidence](../deliveries/Document_Media_And_Thumbnails_Review.md)
