---
doc_id: site-request-admin-app-structure-tasks
title: Admin App Structure Tasks
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: site-request-admin-app-structure
viewable: true
---
# Admin App Structure Tasks

This is the tracker for implementing [Admin App Structure Request](/docs/?scope=studio&doc=site-request-admin-app-structure).

### baseline verification set

Use focused checks for the touched batch:

- Admin server and route checks after Admin app batches.
- Admin route smoke checks for `/admin/`, `/admin/audits/`, `/admin/risk/`, `/admin/activity/`, `/admin/testing/`, and `/admin/ui-catalogue/...` after each route family moves.
- Admin runner checks after `admin-app/commands/run_checks.py` moves.
- App-local tests for Studio, Analytics, Docs Viewer, and Admin when their owned code changes.
- Source/config review for retired route entries, retired app scripts, and moved fixtures.
- Syntax checks for changed Python and JavaScript.

Codex sandbox note: local service, browser, and temporary localhost checks will need elevated permissions even when the product code is healthy.

### general steer

- Build a visible Admin home before moving current functional pages.
- Keep Admin focused on operational review, testing, risk, audit, activity, and UI Catalogue.
- Keep `bin/local-all` as the sibling-service supervisor.
- Use plain `/admin/...` route paths.
- Use plain local Studio routes without `?mode=manage`.
- Implement direct reference updates for moved paths.
- Tests should assert that Admin-owned routes, APIs, runner behavior, and UI Catalogue routes work.
- Cleanup evidence should come from source/config ownership review and focused app behavior checks.
- Move tests and fixtures to the owner that uses them.

## Implementation Tasks

Work through the table by ID order.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | title |
| --- | --- | --- |
| 1 | planned | [Batch 1: Admin Foundation](/docs/?scope=studio&doc=site-request-admin-app-structure-batch-1) |
| 2 | planned | [Batch 2: UI Catalogue Under Admin](/docs/?scope=studio&doc=site-request-admin-app-structure-batch-2) |
| 3 | planned | [Batch 3: Audits, Risk, and Activity Routes](/docs/?scope=studio&doc=site-request-admin-app-structure-batch-3) |
| 4 | planned | [Batch 4: Runner, Checks, Tests, and Fixtures](/docs/?scope=studio&doc=site-request-admin-app-structure-batch-4) |
| 5 | planned | [Batch 5: Studio Local Route Cleanup and App Script Cleanup](/docs/?scope=studio&doc=site-request-admin-app-structure-batch-5) |
| 6 | planned | [Batch 6: Durable Docs, Verification, and Closeout](/docs/?scope=studio&doc=site-request-admin-app-structure-batch-6) |

### task: update docs

Durable docs updated in Batch 6 should describe:

- Admin app boundary, route namespace, assets, and local output paths.
- Studio catalogue-only local route boundary.
- UI Catalogue as Admin-hosted source and route ownership.
- Admin-owned runner/check profile behavior.
- Test and fixture ownership after moves.
- Local setup and `bin/local-all` startup behavior.

### task: cleanup

Cleanup is split across implementation batches:

- Batch 2 covers standalone UI Catalogue server, launcher, tests, and route references.
- Batch 4 covers runner/check scripts, misplaced tests, and fixtures.
- Batch 5 covers retained Studio route paths, Studio route registry/config, Studio app scripts, and stale source references.

### task: verification

Final verification should include the smallest useful combination of:

- Admin Python server tests.
- Admin route smoke checks.
- Admin runner/profile tests.
- UI Catalogue Admin route smoke checks.
- Focused Studio route checks for retained catalogue routes.
- Focused tests for moved checks and fixtures.
- Syntax checks for changed Python and JavaScript.
- Source/config review for route registries and launchers.

### task: close out

Close out the parent request and this tracker by recording:

- moved source paths
- moved route ownership
- moved test and fixture ownership
- retired app scripts
- verification results
- remaining follow-on work, if any
