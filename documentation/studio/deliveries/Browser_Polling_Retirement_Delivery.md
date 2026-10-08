---
draft: false
doc_id: d-20261008-184804-84d5c2
title: Browser Polling Retirement Delivery
added_date: "2026-10-08 18:48:04"
last_updated: "2026-10-08 19:54:24"
summary: Replace recurring Working viewer reads with explicit refreshes owned by completed application actions.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Browser Polling Retirement Delivery

Status: complete; user accepted closeout on 2026-10-08. Parented to [Planned Features](../Planned_Features.md). Follows completed [Source Save And Watcher Retirement](Source_Save_And_Watcher_Retirement_Delivery.md).

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
- [x] Check broad management completion, route loading and retained-view owners for reliance on polling, including index/collection/report and open information updates.
- [x] Confirm external-edit and other-tab/window expectations and the existing explicit refresh/reopen path.
- [x] Identify the shared/public projection boundary and agree the bounded remaining action-refresh work.

Gate: promote to planned only when every required view update has an explicit owner and external/cross-tab automatic synchronization is not required. If a broader synchronization feature is needed, separate that requirement before removing polling. Readiness remains read-only.

Record: complete. Read-only readiness confirmed the accepted Save prerequisite, existing route/provider/list ownership and the shared/public projection boundary. The user's start request authorizes this delivery. Remaining work is bounded to content-changing action completion, exact Rebuild metadata/Index refresh, Import completion and loaded Search/Recent invalidation after their owning actions. Draft already projects its front-matter change to the menu and retained collection report; the user confirmed that scope, so no body reload is added. Info retains its existing detached capture. External/CLI changes and other tabs/windows retain this delivery's explicit rebuild and refresh/reopen expectation; continuous synchronization is outside scope. No new event framework or server mechanism is needed.

### BP-1 Explicit Refresh And Polling Removal

- [x] Complete any remaining action-owned refreshes identified during readiness, reusing existing exact-target loading and retained-state owners.
- [x] Remove the polling timer and exclusive refresh machinery while preserving initial, navigational and explicit loads.
- [x] Update [Docs Viewer Runtime](../Docs_Viewer_Runtime.md) and other affected durable action owners with shipped refresh behavior.
- [x] Project changed shared/public runtime files through `bin/site-code-update`, inspect the exact tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate`.

Verification budget: bounded completion/load/caller review, changed-source JavaScript lint and whitespace checks, plus the required projection/site validation. Expected static-check cost is seconds; site validation cost follows the existing command. User manual review covers the changed action results, navigation/retained state and an idle viewer without recurring Working refresh reads. No browser automation, temporary regression scripts or test changes are authorized; any proposed test work follows [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md). No document, media, Search or Publish build is required merely to remove a timer.

Gate: required action results are fresh without the timer, idle refresh traffic is gone, and ordinary navigation/public loading remain intact.

Record: implementation complete. The exact Save refresh is generalized to the existing shared document-completion command, with no compatibility alias. Rebuild preserves current history/position and forwards exact metadata; changed Subject and Import results receive fresh displayed payloads; ordinary Index creation/deletion and named collection Import use explicit owners. Full Rebuild refreshes loaded Search/Recent data without resetting the Index query/view/scroll, and Publish awaits visible Recent refresh. Draft's metadata-only completion and Info's detached capture remain intact. All eight changed canonical JavaScript files passed explicit lint; whitespace checks passed. The three changed shared/public files were projected, the exact site delta reviewed, and projection check plus site validation passed. No tests, browser automation, document/media/Search Build or Publish have run. Static evidence does not establish live interaction, request traffic or failure recovery.

### BP-2 Code Review

- [x] Review action-to-view coverage, failure outcomes, exact-target reads, history/retained state and open information updates.
- [x] Check for unused polling state, duplicated refreshes, unintended background replacements and public capability leakage.
- [x] Resolve findings and rerun only affected checks.

Gate: no material unresolved finding; record remaining manual evidence limits.

Record: complete. Bounded source/diff review covered initial/navigation loads, exact identity/route/mode guards, retained metadata and caller ownership, Source completion, document-only Rebuild, full Rebuild, Settings, Create, Import, Delete/Position, Subject, Draft, Regenerate, Publish/Recent and the pinned Info capture. Resolved duplicate single-file Import projections, missing Index insertion for individually committed new imports, surfaced Import/retained-list refresh failures and preserved the underlying caught error. General refresh preserves Source's leave/discard confirmation; only completed Source Save bypasses it, keeping unsaved Source safe when another action refreshes generated output. Polling-only state, comparisons and pagehide cleanup are removed without a replacement mechanism; management reads remain outside the public projection. Affected lint and required projection/site checks passed after review fixes. No material source-review finding remains. Live action completion, native history/reading-position behavior, idle network traffic and partial-failure recovery remain unexercised manual evidence limits.

### BP-3 Closeout

- [x] Record the implemented outcome and selected evidence.
- [x] Record user acceptance and the limits of itemised manual evidence.
- [x] Confirm durable refresh documentation and Planned Features are current.
- [x] Recommend retaining or retiring this delivery and its prerequisite link once their routing value is exhausted.

Gate: relevant application actions own view freshness and recurring browser refresh reads are removed. Publish, deployment, commit and push remain separate actions.

Record: complete. On 2026-10-08 the user accepted the delivered outcome and authorized closeout with “great ok to close”. Acceptance was not accompanied by an itemised record of action, navigation/reading-position, idle-network or partial-failure scenarios; retain that evidence limit without claiming separate confirmation of each case. Full Rebuild and Publish completion paths were reviewed without invoking those broader operations. Existing changed-source lint, whitespace, shared/public projection and site-validation evidence is reused for this status-only closeout. No tests, browser automation, document/media/Search Build, Publish, deployment, commit or push were performed by Codex. Durable runtime and Source documentation describe explicit completion and external-change refreshes. Retain this delivery and its prerequisite for recent-delivery/evidence lookup pending manual archive; recommend archiving both when that routing value is exhausted.

## Follow-on

None required for this bounded outcome. Any later requirement for automatic external or cross-tab updates needs its own explicit scope rather than restoring an implicit background dependency.
