---
draft: false
doc_id: d-20261008-184804-84d5c2
title: Browser Polling Retirement Delivery
added_date: "2026-10-08 18:48:04"
last_updated: "2026-10-08 19:24:55"
summary: Optionally replace recurring Working viewer reads with explicit refreshes owned by completed application actions.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Browser Polling Retirement Delivery

Status: optional proposed delivery, parented to [Planned Features](../Planned_Features.md). Depends on completed [Source Save And Watcher Retirement](Source_Save_And_Watcher_Retirement_Delivery.md). It is a separate complete outcome and is not required to finish the preceding delivery.

## Requirements

- Remove the browser's two-second Working refresh timer and its recurring index/displayed-document reads. Refresh is application code, not automatic browser behavior.
- Each relevant completed application action explicitly reloads or updates its affected current document, index, collection/report view and open information or retained metadata as required by that action. A successful operation must not leave a stale view that previously depended on polling.
- Preserve initial loads, explicit reloads, navigation and Back/Forward retained state, reading position, exact route/identity guards and public read-only isolation.
- Treat deliberate external or CLI changes as explicit workflows: rebuild generated output as needed, then refresh/reopen the relevant view. Continuous synchronization of other open tabs/windows is outside this delivery unless readiness identifies it as a required product behavior.
- Use existing action completion and reader-load owners. Do not replace the timer with server push, another polling loop, a global event framework or a background freshness mechanism.

## Deliverables

- Explicit refresh completion for any remaining application workflow that currently relies on polling, with the affected view scope recorded during implementation.
- Removal of the timer and exclusively polling-owned comparisons, state and listeners; preserve shared code still used for normal loading or explicit refresh.
- Current durable runtime documentation describing when views update and how deliberate external changes become visible.
- Canonical/shared runtime projection and validation wherever the public inventory includes a changed file.

## Process

Use Save, Rebuild and other application management actions normally. Their completed result updates the relevant view directly. Idle viewers make no recurring refresh requests. A deliberate change made outside the current application workflow becomes visible through explicit rebuild and refresh/reopen rather than a timer.

## Delivery Steps

### BP-0 Readiness

- [x] Confirm the preceding delivery is complete and Source Save awaits its fresh displayed result.
- [ ] Check broad management completion, route loading and retained-view owners for reliance on polling, including index/collection/report and open information updates.
- [ ] Confirm external-edit and other-tab/window expectations and the existing explicit refresh/reopen path.
- [ ] Identify the shared/public projection boundary and agree the bounded remaining action-refresh work.

Gate: promote to planned only when every required view update has an explicit owner and external/cross-tab automatic synchronization is not required. If a broader synchronization feature is needed, separate that requirement before removing polling. Readiness remains read-only.

Record: prerequisite complete and user-accepted on 2026-10-08. Source Save now awaits its fresh displayed result. The current shared route workflow still starts a two-second refresh timer for the local management-enabled rendered view and compares fetched Working index/document data. Remaining action-to-view coverage and external/cross-tab expectations require read-only readiness before this optional delivery can be promoted; implementation is not authorized by the preceding acceptance.

### BP-1 Explicit Refresh And Polling Removal

- [ ] Complete any remaining action-owned refreshes identified during readiness, reusing existing exact-target loading and retained-state owners.
- [ ] Remove the polling timer and exclusive refresh machinery while preserving initial, navigational and explicit loads.
- [ ] Update [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) and other affected durable action owners with shipped refresh behavior.
- [ ] Project changed shared/public runtime files through `bin/site-code-update`, inspect the exact tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate`.

Verification budget: bounded completion/load/caller review, changed-source JavaScript lint and whitespace checks, plus the required projection/site validation. Expected static-check cost is seconds; site validation cost follows the existing command. User manual review covers the changed action results, navigation/retained state and an idle viewer without recurring Working refresh reads. No browser automation, temporary regression scripts or test changes are authorized; any proposed test work follows [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md). No document, media, Search or Publish build is required merely to remove a timer.

Gate: required action results are fresh without the timer, idle refresh traffic is gone, and ordinary navigation/public loading remain intact.

Record: not started.

### BP-2 Code Review

- [ ] Review action-to-view coverage, failure outcomes, exact-target reads, history/retained state and open information updates.
- [ ] Check for unused polling state, duplicated refreshes, unintended background replacements and public capability leakage.
- [ ] Resolve findings and rerun only affected checks.

Gate: no material unresolved finding; record remaining manual evidence limits.

Record: not started.

### BP-3 Closeout

- [ ] Record the delivered outcome, selected evidence and user manual acceptance.
- [ ] Confirm durable refresh documentation and Planned Features are current.
- [ ] Recommend retaining or retiring this delivery and its prerequisite link once their routing value is exhausted.

Gate: relevant application actions own view freshness and recurring browser refresh reads are removed. Publish, deployment, commit and push remain separate actions.

Record: not started. This document is an option for later implementation, not authorization to remove polling now.

## Follow-on

None required for this bounded outcome. Any later requirement for automatic external or cross-tab updates needs its own explicit scope rather than restoring an implicit background dependency.
