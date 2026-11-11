---
draft: true
doc_id: d-20260526-000000-04ce37
title: library structure
added_date: "2026-05-26 00:00:00"
last_updated: "2026-09-15 19:20:31"
---
# library structure

## book concept

- Library - the reference collection of raw docs (100s docs, varying lengths and styles)
- Books - a curated edited sequence of docs, compatible with an epub structure (e.g. 20 chapters, 100s pages)

## library index
- how to show tree hierarchy without listing all the docs?
- the tree structure can be displayed in the main index panel, and keep the collection report as a flat ordered (numbered) list of documents in the selected section.
- we need this split of tree + list, otherwise just moving the tree into the collection report won’t solve the problem of displaying 100s of docs.
- this makes doc navigation prev/next apply only to the docs listed in the collection report.
- the index panel selected node is not a doc or a collection link, it is a section heading. the collection index structure is persisted in catalogue-index.json, so the collection report displays docs listed in the selected section of that file. the index panel will need to read the section/chapter headings from this file, only for the Library root node. 
- the original package export used parent_id tree structure which has been deprecated so need to check how the package will deal with a returned structure. it will need to be via the catalogue-tree.json.
- in principle, there is no restriction to the structure - it doesn’t need to be consistent - parent nodes could have different number of hierarchy levels underneath.
- however we need to ensure the structure is compatible with a future epub export - so it is likely to a consistent, simple structure.
- this design could then display the selected section heading in the report header in title font, with the docs in that section listed below it.
- this would change the meaning of search within the collection. either we restrict the search to the docs listed in the selected section, or we hide the search when a section is selected. index (site) still has search. conclude that collection search should be retired.
- the catalogue-index.json approach allows the site and any export to use the same structure even though the display and navigation is different.
- this could mean that if you select the root note Library, the collection display all the docs in a flat list, corresponding to the view we have currently. so in manage, we can still see the whole collection and sort AZ or date.

## epub
- the epub is a single doc so the whole compilation needs to fit in the limited number of heading levels, e.g.
- part 1,2…
    - chapter 1,2…
        - sections
- so it is not possible to just squeeze the existing docs into a 3 level structure, because each section would be a doc in itself, and docs already contain h1, h2, h3
- so the likely solution needs to be that the epub is actually a rewrite/rebuild of the docs, i.e. condensing and editing several docs into a single chapter.
- this makes sense because the epub is a curated book/collection, derived from Library.
- therefore we will need the capability to create and edit this book in manage, and then display as documents + publish as a single epub file.