---
draft: false
doc_id: d-20261116-171026-b2c1a5
title: R2 Orphan Report
added_date: "2026-11-16 17:10:26"
last_updated: "2026-11-16"
summary: Save a Manage report of unexpected unreferenced document media in R2 across the configured Docs collections.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# R2 Orphan Report

**Implemented.** The report is available from **Docs Media → R2** in Manage. An explicit Refresh compares R2 keys with Working and both public snapshots, then saves the findings for later review. [Planned Features](../Planned_Features.md) · [R2 orphan report](../Media_And_Asset_Handling.md#r2-orphan-report)

## Requirements

- Check all configured document-media collections in one explicit Refresh. Show unexpected files with their R2 key, collection, and owning document if present. A collection filter uses the loaded findings.
- Treat references in Working, the prepared site, and the deployed site as reasons to retain a key. Exclude exact queued media removals. Use the current successful GitHub Pages deployment to select the deployed Docs data from local Git. If that evidence is unavailable, report the failure and preserve the last saved result.
- Save the completed findings, refresh time, deployed commit, and object count beneath the configured Working report directory. Opening the report reads that file alone.

## Delivery Steps

- [x] **Readiness.** The existing R2 client can list the configured prefix with pagination. GitHub Pages reported a successful deployment with a commit available in local Git. The existing private Docs Media host can provide the new view.
- [x] **Implementation.** Add the saved read and explicit Refresh routes, the comparison of exact object keys, and the filtered Manage view.
- [x] **Code review.** The browser owns view and collection selection. The service resolves the workspace once per Refresh, scans each Working source once, reads both public snapshots, and lists the configured Docs media prefix once. Exact reference parsing and verified deployment identity are necessary to distinguish unused media from draft or still-deployed references. The report checks Working thumbnail presence only for candidate remote thumbnails owned by existing documents. It preserves prior findings on scan failure. The only write is the completed report. [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review)
- [ ] **Manual acceptance.** Open the saved report in Manage, filter it to a collection, navigate away and return, then use Refresh and confirm the refreshed time and findings. Keep cleanup decisions separate from report acceptance.

**Evidence.** Scoped Python and JavaScript lint passed. The Manage Refresh handler checked 103 document-owned R2 objects against deployed commit `65d070c6b37f` and saved seven findings. The saved-read handler returned the same result without a rescan. Browser acceptance is pending.
