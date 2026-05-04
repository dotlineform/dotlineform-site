---
doc_id: library-export-import-v2
title: Library Export/Import v2
added_date: 2026-05-04
last_updated: "2026-05-04"
ui_status: proposed
parent_id: library
sort_order: 50
---

# Library Export/Import v2

Status:

- proposed

## Purpose

This request adds UI and workflow refinements to the export and import workflows. The primary focus is import because export has already had refinements made to its UI.

Current behaviour is described in places for clarification/context.

## Export

page:`/studio/library-export/`

- No need to preview or manually edit files, export straight to staging as v1 does.

### list filter options

create new pills that act as list filters:

- show all
- no content
- not viewable

### export options

add new checkboxes:

- **JSON** - JSON is an option for all config patterns
- **JSONL** - JSONL is default for when document content field is included in the export config pattern

### Staging

folder:`var/docs/exports/library`

- export creates a JSON/L which includes the metadata defined by the config for the selected documents.

## Import

page:`/studio/library-import/`

### workflow

1. **staging**: a JSON file is manually copied into the staging folder.
2. **preview**: the staged file has been split into separate documents and formatted to plain text with front matter 

### staging

folder:`var/docs/import-staging/library`

workflow:

1. JSON files are manually copied into staging.

### preview

folder:`var/docs/import-preview/library`

workflow:

1. user selects a staged file in the dropdown on the import page
2. Preview button creates files in the preview folder

for all config patterns:

- the staged file is split into separate documents (as current)
- an additional tree hierarchy file is created if there is parent-child data available in the staged JSON
- the tree file displays the parent-child metadata from the staged JSON as a hierarchical tree in the {content}.
- each document is formatted as plain text with front-matter and saved as .txt
- front-matter is split into two sections:
    - first section contains any fields that match the fields from the export config
    - second section contains any new fields in the staged JSON that do not appear in the config.
- no validation or further processing is applied to the preview files.

example preview file:
```
---
doc_id: “my-test”
title: “my title”
summary: “my summary paragraph”
etc...
---
tags: “tag1,tag2”
etc...
---

{content}
```

### file naming for preview files

```[doc_id]-[timestamp].json | jsonl```

where:

- timestamp is the timestamp suffix of the staged file as displayed in the file name
- if staged file is missing a timestamp suffix, use the current local time.

### UI

- the page mirrors the design of the export page
- Preview files created are displayed in a list
- the list mirrors the design of the list on the export page, with checkboxes and document titles
- the list shows the parent-child relationships by indenting the displayed titles

list selection buttons: add two new buttons (as on the export page):

- select all
- clear

## Import Actions

The following actions are available on the library-import page:

1. Update summary
2. Apply hierarchy

### Update summary

- sets the source _docs_src/*.md summary metadata field with the summary text in the staged JSON for the documents selected in the list
- a confirmation modal is displayed which shows the count of documents that will be updated
- the modal has OK | Cancel buttons

### Apply hierarchy

- sets the parent_id field for each document in the staged JSON
- the staged JSON will contain a list of parent_id for each doc:

example:
```
"documents":[
    {
        doc_id: “....”,
        parent_id: “....”
    }
]
```

- a confirmation modal is displayed which shows the count of documents that will be updated
- the modal has OK | Cancel buttons