---
doc_id: library-import-ui
title: Library Import - UI refinements
added_date: 2026-05-05
last_updated: "2026-05-05"
ui_status: done
parent_id: library
sort_order: 50
---
# Library Import - UI Refinements

Status:

- Implemented

These UI refinements apply to the page `/studio/library-import/`.

## Text and messages

- implemented: removed the row that contains details about the staged file (path, format, size, modified)

## Import result panel

- implemented: replaced the results below the documents list with a modal that displays when preview generation or an apply operation completes
- implemented: modal only has a `Close` button
- implemented: counts appear in a compact vertical stack of labels, with numeric values right-aligned close to the labels
- implemented: issues appear below the counts when present, with smaller issue text and extra spacing before the `Issues` heading
- implemented: preview completion messages use context-aware singular/plural wording for generated preview files
- implemented: after a successful preview, a small `results` button appears beside the success message and reopens the last preview result modal while that message remains current

## Buttons and controls

- implemented: on desktop, the staged-file dropdown takes half the command row; on mobile, it fills the available width and the command buttons wrap below it
- implemented: `Generate preview`, `Update summary`, and `Apply hierarchy` now sit after the dropdown on the same command row

## Document list

- implemented: preview file paths are no longer shown in the document list metadata column
