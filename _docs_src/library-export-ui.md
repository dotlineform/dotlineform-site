---
doc_id: library-export-ui
title: Library Export - UI refinements
added_date: 2026-05-04
last_updated: "2026-05-06 18:12"
ui_status: done
parent_id: archive
sort_order: 210
---
# Library Export - UI Refinements

Status:

- implemented

These UI refinements apply to the page `/studio/export/`.

## Text and messages

- remove text 'Select a Library export pattern and the documents to include.'
- remove message 'Select documents for the export, then run the export.'
- don't report on number of missing summaries
- change message 'Exported 5 document(s)...' to 'Exported 5 documents...' - i.e. context aware 's'

## Export result panel

- replace the panel with a modal which displays when the export completed
- modal only has a 'Close' button.
- show the counts in a vertical stack of labels
- only display a list of files created (filename only) in a read-only text box, one file per line
- do not display a separate 'format' label next to the file

## Buttons and options

- change 'Select all' and 'Clear' to a pills immediately above the list.
- move 'Run export' button to after the 'export pattern' dropdown (on the same row)
- move the 'missing summaries only' checkbox to under the 'export pattern' dropdown label (left aligned)

## Outcome

- the introductory and idle-status helper text was removed
- the selection summary now reports selected document count only
- export service summary text now uses `document` or `documents` according to the exported count
- completed exports open a shared Studio modal with vertical counts, a read-only filename list, optional issues/warnings, and a single `Close` button
- select-all and clear are compact pills directly above the checklist
- run export now sits on the export-pattern row, while the missing-summaries option sits under the dropdown
