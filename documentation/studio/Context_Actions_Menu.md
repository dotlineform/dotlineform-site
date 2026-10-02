---
draft: false
doc_id: d-20261002-120000-28682b
title: Context Actions Menu
added_date: "2026-10-02 12:15:13"
last_updated: "2026-10-02 12:15:13"
summary: Consolidate document and collection commands into the main Actions menu with exact targets and visible disabled states.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Context Actions Menu

This bounded feature is parented to [Planned Features](Planned_Features.md). The user approved implementation with unavailable items shown disabled. Durable placement and target rules belong to [Toolbar Model](Toolbar_Model.md), runtime ownership to [Runtime Module Ownership](Runtime_Module_Ownership.md), and star storage to [Source Organisation](Source_Organisation.md#selected-documents).

Status: implementation and selected static verification complete. Visual fit and interaction remain manual user review.

- [x] Move New, Open in VS Code, Draft/Ready and Star into one context group in the main Actions menu.
- [x] Remove duplicate main-view and collection-toolbar controls and their obsolete callbacks.
- [x] Keep exact ordinary/collection targets, create placement, collection refresh/open and immediate draft projection.
- [x] Show unavailable items disabled, including Catalogue New/readiness exceptions, loading, source-mode and capability states.
- [x] Keep workspace Import, Export, Rebuild docs and Search, Publish and Settings below a separator; retain the inward-opening menu placement.
- [x] Complete selected static checks, public projection and bounded code review.

Verification is limited to explicit changed-source JavaScript lint, whitespace checks, required shared-code projection consistency and site validation, followed by source review of target, mode and mutation wiring. These existing diagnostics address missing imports, stale callbacks and public/local asset boundaries at low setup cost. No tests, browser checks or live source writes are approved for this delivery. Visual fit and interaction remain user review; no Docs/Search rebuild, Publish, commit or push is part of implementation.

Explicit lint passed for all 13 changed/new canonical JavaScript modules. `git diff --check`, `bin/site-code-update --check` and `bin/site-validate` passed. The public projection changes only the shared collection report and app runtime: committed draft projection moves into the published context, and obsolete local create/draft bridge callbacks are removed. Bounded code review covered exact target capture, Catalogue exceptions, busy/source/expanded-view availability, stale selection reads, committed draft projection, event dispatch and removal of duplicate controls. No test files or runtime generated document/Search payloads changed.
