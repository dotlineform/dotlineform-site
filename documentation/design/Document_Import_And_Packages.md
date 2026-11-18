---
draft: false
doc_id: d-20261118-192505-c4e7b2
title: Document Import And Packages
added_date: "2026-11-18 19:25:05"
last_updated: "2026-11-18"
summary: Rationale for create-only intake, trusted return authority and independent output formats.
parent_id: d-20261118-151521-a0f9c3
---
# Document import and packages

## Create from a selected source

A picked file authorizes conversion into the collection that opened the picker. Other authors can use the same filename, title or front matter, so those fields cannot identify a canonical update target. Allocating a local identity before conversion gives the document, its media and its generated output the same owner. A single native selection grants access to one file. Staged intake serves authors who need to supply a complete folder and its companion files. Both paths reuse normalization, source planning and exact generation. [Import today](../reference/Docs_Import.md) · [Original import architecture](../deliveries/Docs_Import_Architecture.md)

## Overwrite from a prepared selection

The local prepare record binds a return to its original collection, ID set and source versions. That makes omissions and substitutions visible and prevents an older exchange from undoing later local edits. Treat the group as one apply because the editor received its members together and may have revised them in relation to one another. The separate Review projection lets someone judge the returned content without giving the preview editing or publication authority. [Current return contract](../reference/Document_Packages.md#what-a-return-can-overwrite) · [Delivery history](../deliveries/Package_Return_Review.md)

## Two kinds of export

HTML Export freezes a browseable view and its selected owned media for reading outside Docs Viewer. The companion single-file layout supports iPadOS local reading when links between local files are unreliable. The structured package trades source fidelity for predictable, portable text fields that another editor can process. Keeping the body optional on return lets a summary edit use that text without replacing source-only syntax and media references. A separate Book proposal would use edition order for a whole-Book artifact. [HTML artifact](../reference/Export.md#artifact-contract) · [Package contents](../reference/Document_Packages.md#package-output) · [Book export proposal](../_working/Export_Book.md)
