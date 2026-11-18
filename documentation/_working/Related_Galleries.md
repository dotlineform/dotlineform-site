---
draft: false
doc_id: d-20260927-221737-07fbbf
title: Related Galleries
added_date: "2026-09-27 22:17:37"
last_updated: "2026-11-18"
summary: Related Galleries implementation and durable contracts are ready; local visual review and retain-or-retire decision remain.
ui_status: in_progress
parent_id: d-20261118-235100-64ad2e
---
# Related Galleries

Implemented. Local visual acceptance and the retain-or-retire decision remain open. [Current Media View behaviour](../reference/Catalogue_Media_View.md#what-links-appear) · [Series–Gallery source model](../reference/Catalogue_Source_Model.md) · [Design rationale](../design/Media_View_And_Document_Relationships.md)

The implementation seeded 302 exact Series–Gallery pairs for 302 Galleries across 139 Series. Refresh produced the verified `catalogue_series_galleries_index_v1` covering all 139 valid Series, and the public inventory selected its prepared bytes. Gallery `307` had no saved pair in the local read. Review confirmed separate membership and relevance ownership, owned pair removal with Gallery/Series deletion, and selected Gallery reads on activation. Focused lint, syntax, JSON, source and whitespace checks were recorded in the September delivery. The full implementation record is in Git at `c76f6608ef:documentation/studio/Related_Galleries.md`.

- [ ] Confirm the Gallery New/Edit checkbox and exact Series context locally. Check direct and Series-related rows, a mixed-Series Gallery, a Work with no Series and the return to the invoking Gallery.
- [ ] Record the local result and decide whether the compact delivery evidence warrants retaining this record.
