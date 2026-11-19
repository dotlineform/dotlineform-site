# Dotlineform workflow guide

This guide explains how the Dotlineform site is edited, built and released. It is for people working on the site and for technically skilled readers who want to understand how the repository fits together. Each chapter explains the workflow, who owns the important steps and why the boundaries exist. Follow its references for exact configuration and implementation details.

To use the public reader, start with [Find and read things](Find_And_Read_Things.md). To run the local apps or preview the repository snapshot, start with [How the site fits together](How_The_Site_Fits_Together.md#start-a-local-surface).

## Contents

1. [How the site fits together](How_The_Site_Fits_Together.md) — the public website, the local apps and the source of each kind of data.
2. [Author and organise documents](Author_And_Organise_Documents.md) — Working, collections, Books, media and links.
3. [Maintain the Catalogue](Maintain_The_Catalogue.md) — Works, Series, Galleries, and Save → Refresh → Regenerate.
4. [Publish and deploy](Publish_And_Deploy.md) — prepare changes, publish them to the configured destinations and release the static site.
5. [Find and read things](Find_And_Read_Things.md) — the Index, Search, Recent, Catalogue browsing and Media View.
6. [Change the system safely](Change_The_System_Safely.md) — where to make a change, how to check it and how to handle failures.

## Using The Documentation

Use `documentation/reference/` for how the system works today and its code/configuration owners; `design/` for rationale and alternatives; `deliveries/` for useful completed evidence and deferred outcomes. [Development](../development/README.md) owns current development practice. Review [Working](../_working/README.md) for active/proposed work and writing in progress; there is no separate feature register. Processing has its own [project documentation](https://github.com/dotlineform/dotlineform-processing/blob/main/documentation/README.md).

A missing related link can be a behaviour problem, an intentional design choice or unfinished work. Follow the relevant Reference, Design and delivery record to distinguish them. Keep evidence links purposeful and preserve current explanations without copying historical logs. Repository Markdown is maintained directly; these edits need no Docs or Search rebuild.
