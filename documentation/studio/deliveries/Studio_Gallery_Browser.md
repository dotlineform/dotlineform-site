---
draft: false
doc_id: d-20261109-171627-ead0f6
title: Studio Gallery Browser
added_date: "2026-11-09 17:16:27"
last_updated: "2026-11-09"
summary: Browse saved Gallery membership in the Studio Work Editor's existing Series panel.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Studio Gallery Browser

## Current And Next State

Parked at proposal. The priority is Gallery discovery in the Docs Viewer Catalogue index using Studio's existing Gallery index. Resume this delivery when inspecting saved Gallery membership in Studio is the next priority. [Planned Features](../Planned_Features.md) parents both outcomes.

## Outcome And Scope

Extend the Work Editor's left-hand Series browser to search Series and Galleries by title or ID. Label each result by type so that shared titles or numeric IDs remain distinguishable. Selecting a Gallery shows its saved direct members, including Works across different Series, in the existing thumbnail list with a count and an empty state. Selecting a Series or Gallery preserves the open Work draft. Opening a member uses the existing Work selection and unsaved-change flow.

The browser already has both definition registries and the saved Work search rows with Gallery IDs. It owns matching, member selection and display over those rows. Saved membership is available in Studio without Refresh or Regenerate. Server work is limited to the existing full Work read when a member is opened. [Catalogue Work Editor](../Catalogue_Work_Editor.md#startup-lookup-reads) owns those boundaries.

The first slice covers Gallery inspection and opening a single member. Bulk editing, Series definition controls and the default Series for New Work retain their existing Series context. Gallery definition and membership edits stay with the existing Studio controls. Catalogue index discovery and any ownership migration are separate work.

## Delivery Steps

- [ ] **Readiness.** Confirm search result labels, the selected Gallery state and how the panel presents its Series-only controls while browsing a Gallery. Confirm that opening a Gallery member uses the existing Work flow, including draft protection. Obtain implementation approval when the delivery is resumed.
- [ ] **Implementation.** Extend the existing Studio panel and reuse the loaded definitions, Work rows, list renderer and Work opener. Use the editor's saved-state updates to reflect membership changes.
- [ ] **Review and acceptance.** Use focused lint and the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Confirm mixed-title search, empty and cross-Series Galleries, saved membership updates and ordinary Series browsing in manual use. Record the accepted behavior in [Catalogue Work Editor](../Catalogue_Work_Editor.md).
