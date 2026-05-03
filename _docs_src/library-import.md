---
doc_id: library-import
title: Library Import v1
added_date: 2026-05-03
last_updated: "2026-05-03 18:19"
ui_status: in-progress
parent_id: library
sort_order: 30
---
# Library Import v1

Status:

- In progress

## Summary

we need to be able to import data files into studio that contain updated document content and metadata previously exported as JSON files. the user needs to then be able to inspect the staged file as a markdown document.

prerequisites:

- user has copied a data file into a staging folder in var/...

purpose:

- create a studio page to manage the import workflow
- display a list of currently staged files with key metadata extracted e.g. doc_id, title
- convert selected files to markdown documents saved in a 'preview' folder, with metadata in front matter and content converted to basic markdown where identifiable from plain text (e.g. based on the minimal formatting hints provided in the plain text library export - obvious header lines, line breaks, bullet lists, quotes).
- if the imported file contains parent-child relationships, enumerate those into a simple markdown tree structure in the preview document.

what this provides:

- enables a human-readable comparison between a doc in _docs_library_src, the html displayed in docs viewer, and an exported json file that has been edited and re-imported.
- is the first step towards the end goal which is to incorporate externally generated content into Library docs, or apply externally generated parent-child relationships to the Library documents.







