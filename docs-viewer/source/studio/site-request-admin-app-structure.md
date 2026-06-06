---
doc_id: site-request-admin-app-structure
title: Admin App Structure Request
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: change-requests
viewable: true
---
# Admin App Structure Request

Status:

- being planned

## Summary

Create a separate local Admin app/server for cross-repo operational work that no longer fits cleanly inside Studio, Docs Viewer, Analytics, or UI Catalogue.

The Admin app should become the home for:

- audit and risk operations
- activity reporting
- UI Catalogue access and ownership decisions
- repo-scope testing, check profiles, and verification review

This is an architecture boundary change.
The current durable docs still say that risk operations belong in Local Studio and that a separate risk server should not be created.
That decision was right for the previous stage, but the repository has since added clearer sibling app boundaries for Analytics, Docs Viewer, and UI Catalogue.
This request proposes updating the boundary so Studio can focus on maintaining public-site catalogue data.

## Reason

Studio is still carrying several operational responsibilities that are useful but not catalogue maintenance:

- audit launch and review
- risk evidence generation and review
- unified activity reporting
- project/repo health views
- repo-scope check orchestration
- links to sibling development surfaces such as UI Catalogue

Keeping those in Studio makes Studio feel like a general admin console rather than a focused catalogue/public-site maintenance app.
It also makes test and risk ownership harder to review because repo-wide checks live under Studio even when they validate Docs Viewer, Analytics, UI Catalogue, public routes, or repository structure.

The proposed Admin app makes the local app model more explicit:

- Studio maintains public-site catalogue source data and catalogue-generated outputs.
- Admin reviews operational health, risk, activity, and test coverage across the repo.
- Analytics owns tag, semantic-reference, analysis, and Data Sharing workflows.
- Docs Viewer owns documentation viewing, management, imports, exports, and docs payloads.
- UI Catalogue owns reusable UI demos and visual reference surfaces, with final hosting shape to be decided.

## Goals

- add an `admin-app/` source boundary for local admin operations
- move audit/risk route ownership out of Studio
- move activity reporting out of Studio
- move repo-scope check runner ownership out of Studio
- make test coverage easier to review by grouping repo-scope checks and smoke orchestration under Admin
- move UI Catalogue under Admin and retire the standalone UI Catalogue app server
- use `/admin/...` as the Admin route namespace
- move repo-scope check run output to `var/admin/test-runs/`
- build a visible Admin home before moving existing functional routes
- remove `?mode=manage` from local Studio routes as part of the local-only route cleanup
- update durable ownership docs before implementation begins
- compatibility aliases, dual ownership, broad proxy routes, and dual-read/write fallbacks are prohibited.

## App Boundaries

### Admin

Admin owns cross-repo operational review and verification:

- The Admin route namespace is `/admin/...`.
- `/admin/` home and local admin navigation
- `/admin/audits/`
- `/admin/risk/`
- `/admin/activity/`
- `/admin/testing/`
- `/admin/ui-catalogue/...`
- `/admin/api/audits/...`
- `/admin/api/risk/...`
- narrow Admin APIs for activity and test-run summaries
- repo-scope check orchestration and run summaries
- risk evidence producers, audit allowlists, and generated local risk artifacts
- UI Catalogue demo routes, palette/reference routes, and demo assets
- Admin routes do not use `?mode=manage` because there is no public Admin mode.

### Studio

Studio owns catalogue and public-site data maintenance:

- `/studio/` catalogue maintenance home
- plain local Studio route paths without `?mode=manage`
- catalogue editors for works, work details, series, and moments
- bulk add work
- catalogue status and draft review
- catalogue field registry review
- project state
- catalogue save, delete, publication, build, lookup, and generated-output workflows
- catalogue APIs under `/studio/api/catalogue/...`
- catalogue source and generated Local Studio read models under `studio/data/...`
- Studio should not own audit/risk/activity/testing surfaces after this split.
- Studio is entirely local, so it does not need a public/manage route mode split.
- Admin may report repo-scope check results that include Docs Viewer, but Docs Viewer remains the owner of its routes, APIs, writes, and app-local tests.

### Analytics

Analytics remains the local app for:

- tag registry, aliases, groups, and assignments
- Data Sharing prepare, review, and apply workflows
- semantic-reference maintenance
- analysis and visualisation workflows
- Admin may report repo-scope check results that include Analytics, but Analytics remains the owner of its routes, APIs, writes, and app-local tests.

### Docs Viewer

Docs Viewer remains the local app and runtime for:

- docs viewing
- docs source management
- docs import/export/conversion helpers
- Docs Viewer generated payloads and search
- Docs Viewer management APIs
- Admin may report repo-scope check results that include Docs Viewer, but Docs Viewer remains the owner of its routes, APIs, writes, and app-local tests.

### UI Catalogue

UI Catalogue should be visible from Admin because it is a cross-app design and verification aid rather than catalogue data maintenance:

- UI Catalogue should move under `admin-app/`.
- The standalone `ui-catalogue-app` server should be retired, deleted in its entirety with no links to it remaining.

This does not require UI Catalogue code to merge into generic Admin UI code:

- The target route family is `/admin/ui-catalogue/...`.
- demo CSS remains UI Catalogue-scoped
- demo JavaScript remains UI Catalogue-scoped
- demo class names remains isolated from Admin route class names
- palette/reference source remains in a dedicated UI Catalogue subdirectory
- Admin only becomes the route and server owner

Implementation should move the existing standalone route behavior into Admin without adding a second server, proxy, redirect, or app-launch dependency.

## Proposed Source Layout

| Path | Proposed owner / role |
| --- | --- |
| `admin-app/app/server/admin_app/` | Admin app server, admin route views, runtime config projection, local API dispatch, static serving. |
| `admin-app/app/frontend/` | Admin browser modules, route modules, shell helpers, route registry, and UI text config. |
| `admin-app/app/assets/css/admin.css` | Admin-specific stylesheet for Admin shell, navigation, route layout, and Admin-owned pages. |
| `admin-app/app/assets/` | Admin-only static assets. |
| `admin-app/checks/` | Repo-scope checks, risk evidence producers, source-boundary audits, public-surface audits, CSS/JS inventories, and other checks not owned by one app. |
| `admin-app/commands/run_checks.py` | Top-level optional check runner and profile registry. |
| `admin-app/tests/python/` | Admin server tests, runner tests, risk/audit contract tests, and repo-scope deterministic tests. |
| `admin-app/tests/smoke/` | Admin browser smokes and repo-scope smoke orchestration. |
| `admin-app/data/config/` | Admin-visible config such as audit allowlists, risk producer registry, and testing profile metadata. |
| `admin-app/ui-catalogue/` | UI Catalogue demo source, scoped demo CSS/JS, palette/reference source, and demo assets. UI Catalogue CSS remains demo-scoped rather than merged into `admin.css`. |
| `var/admin/` | Ignored local Admin output such as risk runs, audit reports, activity views, and test-run summaries. |

Notes:

- Existing app-local tests should stay with their app when they verify that app's direct behavior.
- Admin should own cross-app orchestration, check profiles, and repo-level verification summaries.

## Proposed Route Migration

| Current route or surface | Target |
| --- | --- |
| `/studio/audits/?mode=manage` | `/admin/audits/` |
| `/studio/risk/?mode=manage` | `/admin/risk/` |
| `/studio/activity/?mode=manage` | `/admin/activity/` |
| `/studio/catalogue-field-registry/?mode=manage` | `/studio/catalogue-field-registry/` |
| `/studio/project-state/?mode=manage` | `/studio/project-state/` |
| other retained Studio local routes with `?mode=manage` | remove `?mode=manage` |
| `studio/commands/run_checks.py` | `admin-app/commands/run_checks.py` |
| `studio/checks/` repo-scope checks | `admin-app/checks/` |
| `var/studio/risk/` | `var/admin/risk/` |
| `var/studio/activity/` for unified admin activity | `var/admin/activity/` |
| `var/test-runs/` | `var/admin/test-runs/` |
| `ui-catalogue-app/` | move under `admin-app/ui-catalogue/` and retire the standalone server |

Notes:

- Old Studio admin routes should be removed rather than retained as aliases once the Admin routes are implemented and verified.
- Old standalone UI Catalogue server routes should be replaced by Admin-hosted UI Catalogue routes rather than retained as a second local app.

## Testing Ownership Model

The testing split should make owner responsibilities visible:

- app-local deterministic tests remain under the owning app, such as `studio/tests/python/`, `analytics-app/tests/python/`, `docs-viewer/tests/python/`, and `ui-catalogue-app/tests/python/`
- app-local smoke tests remain under the owning app when they validate that app's route behavior
- tests currently under an app should move when they validate another app, a retired route surface, repo-scope orchestration, public-surface structure, or cross-app risk rather than that app's direct behavior
- fixtures should move with the tests or owner contracts that use them; `studio/tests/fixtures/` should not remain a hidden shared bucket for Admin, Docs Viewer, Analytics, UI Catalogue, or repo-scope checks
- Admin owns check profiles, repo-scope orchestration, run summaries, and cross-app verification views
- Admin owns tests for the runner, profile metadata, risk/audit allowlists, public-surface audits, and source-tree ownership rules
- The runner can still execute app-local tests by path.
- Ownership should be expressed by the profile registry and docs
- The split should include an explicit pass over current app test folders and `studio/tests/fixtures/` to move misplaced tests and fixtures to the correct app or to Admin.

## Migration Rules

- Functionality remains the same as current.
- Build a visible Admin home first so existing functional pages have a real destination before route moves begin.
- Move complete route/API ownership in coherent slices.
- Update durable ownership docs before or alongside code moves.
- Retire old Studio admin route handlers, runtime-config entries, navigation links, and smoke targets once Admin replacements pass.
- Do not add compatibility aliases for retired `/studio/audits`, `/studio/risk`, or `/studio/activity` paths. Task batching and ordering must ensure no temporary compatibility layers are needed.
- Do not create generic browser-controlled command execution, file read, or shell APIs.
- Keep audit and risk execution allowlisted in trusted Python code.

## Docs To Update During Implementation

Durable docs that will need updates include:

- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)
- [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis)
- [Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Testing](/docs/?scope=studio&doc=testing)
- [Development Checklist](/docs/?scope=studio&doc=development-checklist)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)

## Open Questions

- none.

## Initial Recommendation

Start with a docs-first task that locks the ownership map, then implement the smallest useful Admin app:

1. Create `admin-app/` with a basic `/admin/` home and health endpoint.
2. Add visible Admin home navigation for audits, risk, activity, testing, UI Catalogue, and sibling app links.
3. Move audit/risk/activity route ownership from Studio to Admin without redesigning the workflows.
4. Move `studio/commands/run_checks.py` to `admin-app/commands/run_checks.py`, keeping a direct command shape and updating docs/tests.
5. Move repo-scope checks from `studio/checks/` to `admin-app/checks/` only when their ownership is clearly repo/admin rather than catalogue-specific.
6. Move UI Catalogue routes, scoped code, CSS, palette/reference data, and tests under Admin, then retire the standalone UI Catalogue server.

This preserves momentum while making the new boundary explicit.