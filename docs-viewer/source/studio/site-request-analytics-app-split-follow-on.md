---
doc_id: site-request-analytics-app-split-follow-on
title: Analytics App Split Follow-On Tasks
added_date: "2026-05-30 17:24"
last_updated: "2026-05-30 18:26"
ui_status: in-progress
parent_id: site-request-analytics-app-split
---
# Analytics App Split Follow-On Tasks

This sets out the work required following completion of [Analytics App Split Request](/docs/?scope=studio&doc=site-request-analytics-app-split).

This is the second-phase tracker for making Local Analytics self-contained after the lift-and-shift split.
The split removed Studio route/API ownership, but intentionally left some path, helper, naming, and inventory carryover in place so the initial cutover could stay small and verifiable.

The purpose of this phase is to remove that carryover without adding new Analytics features.
Analytics should become the durable owner for tag data, tag mutation helpers, tag UI, Data Sharing workflow ownership, and future analysis/semantic-reference work.
Studio should focus on catalogue/public-site maintenance and should not know Analytics tag source paths directly unless a narrow app-specific adapter is explicitly required.

Key boundary decisions:

- Analytics may read catalogue/public-site generated data where needed, but it should do so through Analytics-owned helpers or app-specific adapters, not Studio helper imports.
- Data Sharing is an Analytics-owned workflow. Shared package dispatch/path mechanics can stay under `data-sharing/`, and Docs Viewer can remain the focused owner for document conversion/source helpers.
- Data Sharing should exchange document and tag data through adapters. It should not route through Docs Viewer HTTP endpoints, import broad Docs Viewer management authority, or depend on Studio tag helpers.
- Search should be treated as app-specific. Studio should not keep tag awareness just because old search build code read tag paths directly; any tag-enriched public or Analytics search behavior needs an explicit adapter/owner decision.
- No old-path compatibility shims should be added for retired Studio Analytics routes, source-data paths, helper imports, or runtime artifact roots.

## Status

### just done

- Reviewed the follow-on gaps left by the completed lift-and-shift split.
- Expanded the follow-on work into concrete implementation tasks with target contracts, ownership boundaries, and verification expectations.

### steer for next task

- Start with an inventory task before moving files. The old names and paths are spread across Analytics frontend modules, Data Sharing config, Python helpers, catalogue/search/audit consumers, smoke fixtures, and durable docs.
- Treat search as a first-class boundary question. The likely direction is that search is app-specific, so Studio should not directly know tag source paths.
- Preserve behavior while changing ownership. The task is decoupling, not redesign or feature work.
- Do not add aliases, redirects, proxy handlers, fallback reads, import fallbacks, or static shims for old Studio paths to make tests easier.

### baseline verification set

Run only the checks warranted by each touched slice.
The final follow-on close-out should include:

- focused Python syntax/import checks for moved Analytics helpers and Data Sharing modules
- focused pytest for tag source/mutation/transaction helpers
- focused pytest for Data Sharing registry/path/adapter behavior
- focused catalogue/search/audit checks where those consumers previously read tag source paths directly
- `analytics-smoke` for route/API/module/modal/ready-state coverage after frontend naming/path changes
- stale-reference scans for retired Studio tag source paths, Data Sharing artifact roots, Analytics helper imports, and old frontend naming
- `git diff --check`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when the product code is healthy.

### general steer

- Keep current Analytics UI behavior, write safeguards, dry-run behavior, backup behavior, compact logging, and Data Sharing package semantics.
- Move ownership by changing active contracts, not by preserving old paths with compatibility layers.
- Studio may consume Analytics-owned data only through a narrow adapter/helper where the owning Studio feature genuinely needs that data.
- Prefer app-owned adapters for cross-app data. Docs Viewer owns document conversion/source helpers; Analytics owns the Data Sharing workflow; Studio should not become the coordinator for either.
- Keep implementation docs source-only unless a separate generated-payload rebuild is intentionally run.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Confirm target contracts before moving files: canonical tag data moves out of `studio/data/canonical/analytics/...`; browser access uses an Analytics-owned static/API path; Data Sharing artifacts move from `var/studio/data-sharing/...` to `var/analytics/data-sharing/...`; old Studio paths are not kept as aliases, fallback reads, redirects, or static shims. |
| 2 | planned | Inventory all live references to `studio/data/canonical/analytics`, `/studio/data/canonical/analytics`, `var/studio/data-sharing`, `studio.services.analytics`, `studio/services/analytics`, `tagStudio*`, `tag-studio*`, and Analytics frontend `studio-*` helper names. Use the result as the pre-change move map and final stale-reference checklist. |
| 3 | planned | Move Analytics tag-domain Python helpers out of `studio/services/analytics/` into an Analytics-owned package, for example `analytics-app/app/server/analytics_app/tag_services/`. Update `analytics_api.py`, the tags Data Sharing adapter, check profiles, Python tests, smoke imports, and docs so Analytics no longer depends on Studio helper modules. |
| 4 | planned | Add an Analytics-owned source path/helper contract for canonical tag data. Use it from Analytics APIs, Data Sharing tags adapter, and any catalogue/search/audit consumers that still need tag data. The helper should make Analytics the path owner and keep Studio from embedding tag source constants directly. |
| 5 | planned | Resolve the search ownership boundary. Decide whether tag-enriched public search belongs to the public search builder through an Analytics tag adapter, to an Analytics-specific search surface, or should be removed from Studio-owned search work. Update build/search code so Studio does not directly know Analytics tag source paths. |
| 6 | planned | Move canonical tag JSON from `studio/data/canonical/analytics/` to the chosen Analytics-owned source location, likely `analytics-app/data/canonical/`. Update Analytics static serving, read endpoints, runtime config/UI text, Data Sharing adapter config, projection contracts, catalogue/search consumers, tests, and docs. Old source paths should fail in active checks. |
| 7 | planned | Move Data Sharing runtime artifact roots from `var/studio/data-sharing/` to `var/analytics/data-sharing/`. Update `data-sharing/config/*.json`, schemas, `data_sharing.services.paths`, Analytics server constants, smoke fixtures, tests, docs, validation messages, and examples. Do not add fallback reads for existing old artifacts. |
| 8 | planned | Verify and tighten the Docs Viewer/Data Sharing boundary. Data Sharing should call document-domain adapters or helper functions for conversion/source work, not Docs Viewer HTTP endpoints or broad management-service handles. Tags should flow through an Analytics tags adapter. Document the adapter contract in the Data Sharing technical spec. |
| 9 | planned | Rename Analytics frontend helper modules and exported APIs that still imply Studio ownership, including `studio-config.js`, `studio-data.js`, `studio-transport.js`, `studio-ui.js`, `studio-modal.js`, `studio-route-state.js`, `studio-theme.js`, `studio-navigation.js`, and related imports. Use Analytics-owned names such as `analytics-config.js`, `analytics-ui.js`, and `analytics-modal.js`. |
| 10 | planned | Rename tag UI/module naming from `tagStudio*` and `tag-studio-*` to Analytics-owned naming. Include CSS classes in `analytics.css`, JS class tokens/templates, modal selectors, smoke tests, and docs. Use one consistent family such as `analytics*`, `analyticsModal*`, `analyticsForm*`, `analyticsList*`, and `analyticsToolbar*`. |
| 11 | planned | Rename remaining runtime event/state names that still imply Studio ownership, including `studio:open-modal`, `initializeStudioRouteState`, and Analytics-local activity-context helper names where appropriate. Preserve behavior; only change ownership language and route-local contracts. |
| 12 | planned | Refresh JavaScript and Python inventory docs for the post-follow-on state. Replace stale pre-split `assets/studio/js/tag-*` and `data-sharing-*` inventory rows with actual `analytics-app/app/frontend/js/` rows and rescore maintenance risk. Update Python/Ruby inventory rows for the moved Analytics helper package. |
| 13 | planned | Update durable docs: Analytics, Data Sharing, Data Sharing technical spec, Source Tree Ownership, Run Checks, local setup/runtime docs, projection/data-model docs, tag docs, search docs, and script docs that mention old Studio-owned paths or helper ownership. Update source docs only; do not manually rebuild generated docs payloads. |
| 14 | planned | Run the final focused verification set: Python syntax/import checks, focused tag helper pytest, focused Data Sharing adapter/path pytest, affected catalogue/search/audit tests, `analytics-smoke`, stale-reference scans for retired Studio paths/names, and `git diff --check`. |
| 15 | planned | Close out the follow-on request with moved-path summary, removed old paths, adapter/search ownership decisions, verification results, generated-payload status, remaining risks, and structured docs-log entry. |
