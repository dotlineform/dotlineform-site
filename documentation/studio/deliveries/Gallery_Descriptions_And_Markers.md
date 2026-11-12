---
draft: false
doc_id: d-20261112-150502-9fd713
title: Gallery Descriptions And Markers
added_date: "2026-11-12 15:05:02"
last_updated: "2026-11-12"
summary: Give Galleries an optional short description and visual marker in Catalogue report results.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Gallery Descriptions And Markers

Complete. The user confirmed the Gallery description and marker workflow on 2026-11-12. Retain this delivery pending manual archive. [Planned Features](../Planned_Features.md#reviews) · [Catalogue Work Editor](../Catalogue_Work_Editor.md#gallery-and-series-definitions)

## Agreed Result

- Gallery New/Edit offers an optional single-line description and three icon buttons using `brush.svg`, `video.svg` and `square-library.svg`. Tooltips name the artwork. A selected icon can be clicked again to clear it.
- Canonical Gallery records have optional `description` and `marker` strings. Unset values are omitted. Marker values use the three artwork stems. The icons have approximate editorial meanings, explained by each Gallery’s description.
- Catalogue report Gallery rows show the marker and muted description after the title, followed by the existing matching-Work count.
- An edit to description or marker queues the Gallery and report output. Title and relationship changes retain their own Work and shared effects. Public Work/Gallery by-ID records project Gallery ID and title. Publish consumes the existing queued files.

## Delivery Steps

- [x] **Readiness.** Both Gallery creation paths and the shared Edit dialog can carry the fields. The canonical validator, mutation envelope and report projection currently narrow Gallery data to titles. The existing Work generator copies whole Gallery definitions, so its identity/title projection must become explicit. The shared ID queue can carry the report update without a new queue field.
- [x] **Implementation.** Studio authors and saves the two optional fields. Refresh supplies them to the Catalogue report via `presentation_by_gallery`. The public projection includes the report code, styles and three supplied icons. [Catalogue Work Editor](../Catalogue_Work_Editor.md#gallery-and-series-definitions) · [Catalogue Indexes And Payloads](../Catalogue_Indexes_And_Payloads.md#work-and-gallery-projections)
- [x] **Code review.** Traced both New paths, Edit, unset and cleared values, Gallery deletion and combined title or relevance changes. A presentation edit skips the Work and membership reads and queues the Gallery ID and report output. The existing ID selection still runs through Refresh's by-ID comparison and public handoff. The report carries fields through the existing selected merge and clears them when unset or deleted. Work and Gallery by-ID projection uses the shared ID/title helper. The Redundancy And Defensive Behavior Review removed the unconditional Work and membership loads, whole definition comparison and unchanged Series-pair copy. The existing request shape, exact target and confined write checks retain their persistence roles. Studio owns field values, and explicit Catalogue audits check their stored representation.
- [x] **Manual acceptance.** The user confirmed that the feature worked in normal use. Clearing fields and inspecting the Refresh queue were covered by source review and were not reported separately as live checks.

Focused JavaScript and Python lint, whitespace checks, the exact public runtime projection/check and site validation passed. The projection changed two JavaScript files and one stylesheet and added the three supplied SVGs. These checks address source and asset wiring. Browser interaction and live Save, Refresh and Publish remain unexercised by Codex.
