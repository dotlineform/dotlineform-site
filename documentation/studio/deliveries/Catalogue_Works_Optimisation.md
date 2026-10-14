---
draft: false
doc_id: d-20261014-203254-e627a1
title: Catalogue Works Optimisation
added_date: "2026-10-14 20:32:54"
last_updated: "2026-10-14 20:32:54"
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Works Optimisation

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Catalogue Works](../Catalogue_Works.md). The user approved the reviewed scope on 2026-10-14, including documentation updates and leaving tests unchanged.

## Agreed Result

The browser consumes completed Refresh metadata without repeating schema, identity, field or Series audits. One pure data owner prepares literal rows and derived search/sort fields, filters only changed normalized queries, reorders retained matches and prepares TSV cell values once per exported row. It removes the data operations' DOM/network import dependency and the repeated full-dataset filter on sort/restore. Keep headers mounted, create exact Work URLs only for displayed Works and reuse them through the mounted view. Preserve search-required display, NFKC/English matching and numeric ordering, 20-row paging, all-match five/six-column TSV and the existing expanded table/width contract.

The existing view lifetime owns pending searches, restored loading/page state, timer/data/listener release and late load/clipboard completion. A retained report remains valid when detached; disposal is the authority for stopping its updates. Studio classifies known Catalogue routes without a workspace lookup and reuses one loaded workspace when serving metadata, retaining report allowlisting, local-origin policy, filesystem confinement and file checks. Refresh merging, metadata v3, explicit maintenance, shared resizing and public runtime remain unchanged. No compatibility aliases, canonical fallback, persistent cache, extra authoring checks or repair workflow is required.

## Completion Gates

- [x] Readiness: traced saved projection/Refresh, Studio route/serving configuration, browser audits/search/sort/Copy, exact navigation, header/render notifications, expanded resize and retained-view ownership. User approved this complete slice.
- [x] Implement direct prepared data, query/order result reuse, one-row TSV preparation, stable headers, lazy Work navigation, disposal and request-local configuration reuse; update the stale six-column/direct-link and updater-validation descriptions.
- [x] Focused lint for two JavaScript modules and the Studio server and Python compilation passed. One read-only production invocation prepared 4,620 current Works, searched a real Series with 149 matches, reordered by descending Title and serialized all 149 data rows into both five-column and six-column TSV. No synthetic inputs, assertions, regression scripts, clipboard or test code were created.
- [x] Complete the distinct code review and mandatory Redundancy And Defensive Behavior Review. Reviewed initial/empty/search/order/page/Copy, pending query/Back, pre-load restore, immediate and late disposal, failed-load, literal/null values, exact route and shared presentation paths. The data owner filters only changed queries; sort copies/reorders matches and page/Copy perform neither operation. Review removed remaining undefined-to-blank presentation handling and reused embedded copy columns. Route tracing found an additional eager workspace lookup in classification; known Catalogue prefixes now bypass that lookup before the serving owner reuses its configuration. Shared resize validation remains at its existing extension boundary. No actionable findings remained; durable safeguard ownership/costs and evidence limits are recorded in Catalogue Works.
- [x] Update durable owner, Reports, the implementation guardrail and this parented delivery.
- [x] Review-affected JavaScript lint and final whitespace/reference/security review passed. No retired normalizer/projection references or compatibility aliases remain; the focused security scan found only the retained URL-credential rejection. Tests, metadata generation, shared resize code and application/public output are untouched, and earlier report changes remain intact. The review-only UI changes did not require another data diagnostic.
- [ ] User manual acceptance after restarting Local Studio and force-reloading Docs Viewer: initial/search/no-match/clear, both sort directions and Year/Series/null ordering, page reset/wrap, exact Work links, literal labels, all-match embedded/expanded Copy, pending search and restored Back/page state, disposal, unavailable metadata and expanded widths/resize/Back.

[Catalogue Works](../Catalogue_Works.md#extension-and-weak-spots) records exact diagnostic limits. Tests, fixtures, harnesses and profiles remain unchanged and unrun under [Test Contract Discipline](../Test_Contract_Discipline.md); the existing source-contract test remains unreviewed/stale. No source/metadata, queues, media, Docs/Search or publication output was written. No browser automation, server restart, Build, Publish, deployment, commit or push ran. Both browser modules are local-only and outside the public projection inventory. Earlier report changes remain in the worktree.
