---
draft: false
doc_id: d-20261007-152953-7a3bf6
title: Document Index Navigation - Delivery
added_date: "2026-10-07 15:29:53"
last_updated: "2026-10-07 15:53:51"
summary: Browser document navigation, an index shortcut for collection subdocuments and per-tab collection report state.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Document Index Navigation - Delivery

## Current And Next State

Implementation and bounded code review are complete. [Runtime](Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns the durable navigation and report-state contract. JavaScript lint passed for the seven changed modules, `bin/site-code-update --check` confirmed the tracked projection, `bin/site-validate` passed and the whitespace check passed. No tests, browser interaction, Publish, deployment, commit or push ran. User manual review remains for the index shortcut, host/report state restoration and browser Back/Forward behavior; static evidence does not establish those outcomes.

## Requirements And Deliverables

- Browser Back/Forward owns document history. Ordinary documents have no document Back control.
- Collection subdocuments offer `list.svg` with tooltip and accessible label `index`, opening their configured report host as normal navigation regardless of their entry path and explicitly selecting that host in the Index through its existing tree owner.
- Each collection report remembers its last-visible search, filters, sort, page, contribution controls and scroll in the current tab. Index host openings, the shortcut and browser history share that state, including history-triggered reloads.
- Keep only the existing two document/report mounts. Saved state contains no payloads or DOM; remounts use current inventory, prune selection and bound pages. Content Detail returns remain within their document.
- Update durable navigation guidance and the tracked public code/icon projection.

## Delivery Steps

- [x] Readiness: confirmed configured immutable report hosts and the existing two-view lifecycle. The change affects shared Public/Manage navigation and collection reports; other reports retain their existing policy.
- [x] Implementation: replace the toolbar control, retain lightweight collection state independently of mounts and restore after inventory acquisition.
- [x] Evidence: changed-file JavaScript lint, runtime projection/check, site validation and whitespace check passed. These address syntax/style, omitted public assets and deploy-root consistency; cost was seconds with local projection writes and no live source writes or browser interaction. No tests or harnesses were changed or run.
- [x] Code review: reviewed ownership, restoration timing, hidden-list capture, reload paths and public inventory. Resolved pending-search page reset, pre-Source position capture, same-report host reopening and preservation of ordinary heading navigation. The host-selection follow-on reuses the existing explicit Index route after navigation is accepted; focused route lint, projection check and site validation passed. The public inventory includes the state owner and list icon; no compatibility aliases were introduced.
- [x] Closeout: transferred the current contract to Runtime and reconciled the collection owner/checklist. User review remains for the shortcut tooltip, report restoration through all entry paths and browser Back/Forward behavior.

## Follow-On

Publish and public deployment remain separate explicit actions. Keep this delivery available for manual review; its durable destination is Runtime.
