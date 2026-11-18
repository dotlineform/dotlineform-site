---
draft: false
doc_id: d-20260401-000000-ebf14a
title: Catalogue Works
added_date: "2026-04-01 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6

---

# Catalogue Works

Open the local Catalogue Works report in Docs Viewer Manage. It reads the private Working projection supplied by Refresh. Studio remains the editor, and Catalogue documents open through their exact Work IDs. [Report composition](Reports.md#composition-and-capabilities) · [Work editor](Catalogue_Work_Editor.md)

## Live Report

Search Work ID/title or Series ID/title. Empty search displays no rows. The report sorts by Work ID initially and defaults to 20 matching rows per page. Its pagination toggle displays all matches when switched off. Search and sort reset to the first page. The last-page Next control wraps to page one.

The embedded sortable columns are Work, Year, Title, Series and Storage. Expanded presentation adds Medium and Source image as the final two unsortable columns. Copy table exports every sorted match as five-column embedded or seven-column expanded TSV. Source image joins the saved folder/subfolder/filename literally for display and copy and stays outside search. Series labels are plain text.

## Data And Ownership

Parameter-free `GET /docs/catalogue-works-report` runs through Docs Viewer's local report service and reads only `working/generated/catalogue/reports/catalogue-works/metadata.json`. The saved `catalogue_works_report_metadata_v3` envelope has `header: {schema}` and a Work map. Rows carry the exact Work ID, Title, Year/Year display, Medium, optional Storage and source-image components, plus the saved Series ID/title pair. [Saved reader](../../docs-viewer/services/docs_catalogue_works_report.py) · [Row producer](../../studio/services/catalogue/catalogue_works_metadata.py)

The browser's `catalogue-works-data.js` prepares literal display/TSV values, normalized matching fields and sort values once per load. Search follows a 180 ms pause, with immediate clearing. Filtering runs when the normalized query changes, sorting reorders the retained matches, and page/Copy operations reuse them. The report module owns requests, rendering, controls, Work links and async lifetime. [Data owner](../../docs-viewer/runtime/js/reports/catalogue-works-data.js) · [Report owner](../../docs-viewer/runtime/js/reports/catalogue-works-report.js)

A successful Save changes canonical/editor state first. Refresh updates only selected rows and explicit deletions in the saved report. Series title changes select member rows. Missing or malformed saved metadata stops normal updating. The report requires reopening or a fresh mount to read refreshed output. Work links use the five-digit ID and exact Catalogue collection. Missing Work documents are repaired through Regenerate. [Refresh and Regenerate timing](Catalogue_Save_And_Refresh.md)

For deliberate initial population, schema change or repair, run the existing complete private metadata producer with the project interpreter.

```bash
python3 studio/services/catalogue/catalogue_works_metadata.py --write
```

This writes only the private metadata aggregate using the normal row projector. Queue/lifecycle state stays with Save and Refresh. [Private report inputs](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs)

## Expanded Presentation

Manage rehosts the same live table and toolbar through the report's `expandedPresentation` handle. Query, sort, page, pagination mode, links and event listeners remain with that instance. Back restores the embedded presentation. Temporary column widths are released by Back, navigation or Reset widths. The local pagination button helper shares button presentation with Library, while each report owns its state and initial mode. [Presentation owner](../../docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js)

A retained report can complete a pending search while detached. Releasing it clears the pending timer and prevents later work from rendering. A failed fresh metadata read shows failure. [Retained reader views](Reader_Discovery_And_Return.md#retained-index-views)

## Extension

Add a column through the metadata projector and the browser's single column model, naming its visibility, sort and TSV behavior. Private storage context remains in the local report. Current browser acceptance and stale-test follow-ups are recorded separately. [Delivery evidence](../deliveries/Studio_And_Catalogue_Ownership_Review.md#catalogue-works-report)
