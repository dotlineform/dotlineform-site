---
doc_id: docs-viewer-management
title: Docs Viewer Management
added_date: 2026-04-22
last_updated: 2026-05-22
ui_status: done
sort_order: 54000
---
# Docs Viewer Management

This archived planning/reference page now acts as the index for the Docs Viewer management-mode split.
The current implementation is complete for the confirmed local workflow, and the detailed contract has been moved into child references for easier search and review.

## Current Status

Implemented management mode covers:

- local-only `/docs/?mode=manage` availability through the standalone Docs Viewer service
- active-scope management for Studio, Library, and Analysis from `/docs/`
- create, import, metadata edit, status edit, viewability, move, normalize order, archive, delete, settings, source-open, copy-link, and rebuild actions
- dedicated client-side management modules under `docs-viewer/runtime/js/`
- local write service backing through [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)

## Child References

- [Current State](/docs/?scope=studio&doc=docs-viewer-management-current) lists implemented phases, management UI/module responsibilities, unavailable items, and follow-on candidates.
- [Contract](/docs/?scope=studio&doc=docs-viewer-management-contract) preserves the original management-mode goals, scope, guardrails, and phase-1 contract.
- [Write Model](/docs/?scope=studio&doc=docs-viewer-management-write-model) records command semantics, builder implications, non-goals, phases, and decisions.
