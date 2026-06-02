---
doc_id: site-request-analytics-app-split
title: Analytics App Split Request
added_date: 2026-05-30
last_updated: 2026-05-30
ui_status: done
parent_id: change-requests
viewable: true
---
# Analytics App Split Request

Status:

- done
- clean split implemented, verified, documented, and logged

## Summary

Split the current Studio analytics and data-sharing surfaces into a standalone local Analytics app.

The first implementation should be a lift-and-shift cutover:

- preserve the current UI, workflows, and data behavior
- create a works-as-is Analytics service
- move ownership quickly with minimal refactoring
- avoid new feature work
- avoid compatibility routes and dual ownership
- pause existing local services during the split

The split is primarily a maintenance-risk reduction.
Studio should become focused on catalogue/public-site maintenance, while Analytics becomes the owner for tags, semantic references, data sharing, document analysis, and future data visualisation.

## Reason

Studio currently acts as an umbrella local app for catalogue maintenance, analytics/tag maintenance, data sharing, audits, activity, and admin surfaces.
That makes the Studio service and frontend route surface harder to reason about than the actual work requires.

The key architecture decision is to separate Studio and Analytics now, before semantic-reference editing and analysis workflows add more responsibilities.
The split should make future risk reduction easier in both apps:

- Studio can focus on catalogue data integrity, public-site maintenance, publication workflows, and Studio-owned operational pages.
- Analytics can focus on tag definitions, semantic references, data sharing, document analysis, and visualisation.
- Docs Viewer can stay focused on docs viewing, docs source management, docs publishing payloads, and docs conversion helpers.

The public site remains published by GitHub Pages.
Local services do not publish the public website.
A local Jekyll service is only optional public-site preview tooling and must stay separate from Studio, Docs Viewer, and Analytics services.

## Goals

- add a standalone local Analytics app/service
- move current analytics routes from `/studio/analytics/...` to Analytics-owned routes
- move current data-sharing routes from `/studio/data-sharing/...` to Analytics-owned routes
- move Analytics API endpoints from `/studio/api/analytics/...` to Analytics-owned API paths
- move Data Sharing API endpoints from `/studio/api/data-sharing/...` to Analytics-owned API paths
- keep the current frontend UI and interaction behavior working as-is
- keep current tag and data-sharing source data paths unless moving them is needed for ownership clarity in the lift-and-shift
- make Analytics the durable owner for future semantic-reference editor work
- remove Studio route handlers, nav links, runtime-config endpoints, and API dispatch for analytics and data sharing
- keep Studio audits, activity, and admin in Studio unless a later request defines a separate audit/activity service
- update request and source-ownership docs to reflect the new service boundary

## Non-Goals

- no new Analytics features in the split slice
- no semantic-reference editor implementation in the split slice
- no visualisation implementation in the split slice
- no broad redesign of tag or data-sharing UI
- no CSS class rename pass just to remove `tagStudio` names
- no compatibility aliases for old `/studio/analytics/...` or `/studio/data-sharing/...` routes
- no dual-read or dual-write service path fallback
- no public-site publishing changes
- no local Jekyll integration with the Analytics service
- no redesign or feature work for UI Catalogue
- no active thumbnail-quality workflow replacement
- no attempt to remove all historical request references

## Target Ownership

### Studio

Studio owns:

- catalogue editors
- catalogue import, save, delete, publication, and build actions
- catalogue field registry review
- project state
- Studio audits, activity, and admin pages unless later split out

Studio should not own:

- tag registry, aliases, groups, or assignments
- data-sharing prepare/review/apply workflows
- semantic-reference editing
- document analysis or visualisation workflows
- the retired thumbnail-quality experiment page
- UI Catalogue demos and isolated UI-pattern pages

### Analytics

Analytics owns:

- tag groups
- tag registry
- tag aliases
- series tags and tag assignment editing
- data sharing prepare, review, apply, and adapter dispatch
- future semantic-reference editor
- future document analysis and visualisation

Analytics may use Docs Viewer modules for docs conversion or document-source handling where that is the focused owner.
Analytics remains the owner of the analysis workflow and semantic-reference maintenance UI.

### Docs Viewer

Docs Viewer owns:

- docs viewing
- docs source management
- docs import/export/conversion helpers
- docs runtime payloads and search payloads
- public read-only Docs Viewer runtime behavior

Docs Viewer should not maintain semantic references through a semantic-reference editor.
The previous semantic-reference editor request should be reframed so the editor is delivered through Analytics, not Docs Viewer.

### Public Preview

Public-site preview remains separate optional tooling.
It may use local Jekyll for development preview only.
It must not become part of Studio, Docs Viewer, or Analytics service startup semantics.

### UI Catalogue

UI Catalogue remains useful as a local design/development reference.
It should no longer be a Studio route or Studio-server concern.

The target is a standalone local page or small static local HTML server that can serve the UI Catalogue demos without coupling them to Studio route config, Studio navigation, Studio APIs, or Studio service startup.
The current UI Catalogue CSS and JavaScript helpers can remain isolated and should not be merged into Studio app code during the Analytics split.

### Thumbnail Quality Experiment

The thumbnail quality page and script were one-off tooling used to reduce thumbnail asset and payload sizes.
That work is complete and not in the current plan.

The split should remove the thumbnail-quality page from Studio.
The code can be archived inside the repo if that is useful for future primary-image payload experiments, but it should not remain an active Studio route, navigation item, runtime-config entry, or smoke-test target.

## Proposed Routes

Use direct Analytics-owned routes in the first cutover.
Do not keep old Studio aliases.

Initial route shape:

| Current route | Target route |
| --- | --- |
| `/studio/analytics/series-tags/` | `/analytics/series-tags/` |
| `/studio/analytics/series-tag-editor/` | `/analytics/series-tag-editor/` |
| `/studio/analytics/tag-registry/` | `/analytics/tag-registry/` |
| `/studio/analytics/tag-aliases/` | `/analytics/tag-aliases/` |
| `/studio/analytics/tag-groups/` | `/analytics/tag-groups/` |
| `/studio/data-sharing/prepare/` | `/analytics/data-sharing/prepare/` |
| `/studio/data-sharing/review/` | `/analytics/data-sharing/review/` |
| `/studio/api/analytics/...` | `/analytics/api/...` |
| `/studio/api/data-sharing/...` | `/analytics/api/data-sharing/...` |

The exact API subpath shape can be chosen during implementation, but old Studio API paths should not remain as compatibility shims.

## Lift-And-Shift Rules

- Pause local services before moving the app boundary.
- Move complete route/API ownership in one coherent slice.
- Keep existing UI modules mostly intact.
- Prefer small import/path edits over structural refactors.
- Preserve current write allowlists, backup behavior, dry-run behavior, and compact logging.
- Keep data integrity checks at least as strong as the current Studio-owned paths.
- Remove old Studio ownership immediately after the Analytics app works.
- Update tests and smokes to the new Analytics service rather than keeping Studio-named copies as active checks.
- Keep implementation docs source-only in the split unless a separate generated-payload rebuild is intentionally run.

## Implementation Tracker

Use [Analytics App Split Tasks](/docs/?scope=studio&doc=site-request-analytics-app-split-tasks) for the implementation sequence, baseline verification set, test split, post-basic-split decoupling activity, and close-out checklist.

The implementation target is a clean split with no compatibility layers and no planned cleanup pass.
Analytics may inherit some of the current structural problems in the first cutover, but those problems should become self-contained inside Analytics rather than remaining shared with Studio.

## Implemented Boundary Snapshot

As of the task 16 close-out:

- Local Studio is started with `bin/local-studio` and owns `/studio/`, catalogue APIs, audit APIs, activity/admin routes, and docs-watcher startup behavior.
- Local Analytics is started with `bin/local-analytics` and owns `/analytics/...`, `/analytics/api/...`, and `/analytics/api/data-sharing/...`.
- Docs Viewer is started with `docs-viewer/bin/docs-viewer` and owns `/docs/` manage mode, Docs Viewer runtime/static assets, generated reads, and docs management APIs.
- UI Catalogue is started with `bin/local-ui-catalogue` and owns `/ui-catalogue/demos/...`.
- Public preview is started with `bin/public-site-preview` and remains an optional Jekyll preview service.
- `bin/local-all` supervises those sibling services together without merging their ownership boundaries.
- Retired Studio Analytics/Data Sharing paths, Studio UI Catalogue routes, and thumbnail-quality route/API/static mounts have no aliases, redirects, proxies, dual-read/write fallbacks, or static shims.
- Current preserved data/artifact contracts include `studio/data/canonical/analytics/...` tag source data and `var/studio/data-sharing/...` package/review/backups output.

## Close-Out Summary

Moved active ownership:

- Analytics app server and views: `analytics-app/app/server/analytics_app/`
- Analytics browser modules, runtime config, and UI text: `analytics-app/app/frontend/`
- Analytics CSS/static assets: `analytics-app/app/assets/`
- Analytics tests and smokes: `analytics-app/tests/`
- UI Catalogue app, source, assets, and smokes: `ui-catalogue-app/`
- UI Catalogue launcher: `bin/local-ui-catalogue`
- Local Analytics launcher: `bin/local-analytics`
- Start-all sibling-service orchestration: `bin/local-all`
- Thumbnail-quality reference tooling: `studio/retired/thumbnail-quality/`

Retired active Studio routes and endpoints:

- `/studio/analytics/...`
- `/studio/data-sharing/...`
- `/studio/api/analytics/...`
- `/studio/api/data-sharing/...`
- `/studio/thumbnail-quality/`
- `POST /studio/api/catalogue/thumbnail-quality-preview`
- Studio-hosted UI Catalogue routes and static mounts

Verification recorded during the split:

- focused Python and JavaScript syntax/import checks
- focused Analytics app and Data Sharing pytest
- focused tag mutation/source/transaction and data-sharing adapter checks
- full `analytics-smoke`
- Local Studio navigation/catalogue smoke checks after removing Analytics/Data Sharing/UI Catalogue links
- standalone `ui-catalogue-smoke`
- thumbnail-quality absence checks
- stale-reference scans for retired Studio route/API/static paths
- `git diff --check`

Generated-payload status:

- source docs were updated as the durable documentation source
- the local docs watcher regenerated affected `docs-viewer/generated/docs/studio/...` and `docs-viewer/generated/search/studio/index.json` payloads after source edits
- no manual public Jekyll publication step was run as part of this close-out

Remaining risks are self-contained inside the new ownership boundaries rather than deferred split cleanup:

- Analytics still intentionally preserves `tagStudio*` frontend class/function naming from the lift-and-shift
- canonical tag source data remains under `studio/data/canonical/analytics/...` as a preserved data contract
- Data Sharing artifacts remain under `var/studio/data-sharing/...` as a preserved local artifact contract
- Analytics still uses focused helper modules under `studio/services/analytics/`; those helpers are domain services, not Studio route/API ownership
- the JavaScript inventory now records the post-split app boundaries, but a full rescored inventory refresh remains future maintenance work

No split cleanup has been deferred.
Old Studio routes, endpoint aliases, proxy handlers, dual-read/write fallbacks, static serving shims, and tests depending on retired Studio Analytics/Data Sharing paths were removed rather than preserved.

## Change Log Entries

- `change-2026-05-30-split-analytics-and-data-sharing-into-a-local-analytics-app`
- `change-2026-05-30-separated-ui-catalogue-and-retired-thumbnail-quality-from-studio`

## Original Risks And Resolution

- Generic Studio helper and CSS coupling was reduced during the split.
  Remaining `tagStudio*` naming, `studio/services/analytics/` helper use, and preserved tag source paths are documented as Analytics-local carryover rather than deferred split cleanup.
- Data Sharing still touches documents and tags by design.
  Analytics owns the browser/API workflow, `data-sharing/` owns headless dispatch and adapters, and Docs Viewer remains the focused owner for document conversion/source helpers.
- Studio-named Analytics/Data Sharing tests and docs were retargeted or retired.
  Active checks now live under Analytics ownership where they cover Analytics routes/APIs, and durable docs describe `/analytics/...` and `/analytics/api/...` as the active paths.
- Old route bookmarks may break because compatibility aliases were intentionally not added.
  Visible navigation, runtime config, docs, and tests now point at the new owner routes.
- Activity and audit remain Studio-owned unless a moved Analytics workflow naturally appends activity rows.
  A broader activity/audit service split is out of scope for this request.
- UI Catalogue was moved to a standalone local app.
  It no longer depends on Studio route config, Studio navigation, Studio APIs, or Studio service startup.
- Thumbnail quality was retired into repo-local tooling.
  It no longer has an active Studio route, API endpoint, runtime-config entry, static data mount, or smoke target.

## Related Docs And Files

- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Development Workflow](/docs/?scope=studio&doc=development-workflow)
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
- [Analytics App Split Tasks](/docs/?scope=studio&doc=site-request-analytics-app-split-tasks)
- `studio/app/server/studio/studio_app_server.py`
- `studio/app/server/studio/studio_app_config.py`
- `studio/app/server/studio/studio_app_views.py`
- `analytics-app/app/server/analytics_app/analytics_app_server.py`
- `analytics-app/app/server/analytics_app/analytics_app_config.py`
- `analytics-app/app/server/analytics_app/analytics_app_views.py`
- `analytics-app/app/server/analytics_app/analytics_api.py`
- `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py`
- `studio/services/analytics/`
- `data-sharing/`
- `ui-catalogue-app/`
- `bin/local-analytics`
- `bin/local-ui-catalogue`
- `bin/local-all`
- `studio/retired/thumbnail-quality/thumbnail-quality.js`
- `studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py`
- `analytics-app/app/frontend/js/tag-*.js`
- `analytics-app/app/frontend/js/series-tag*.js`
- `analytics-app/app/frontend/js/data-sharing-*.js`
- `analytics-app/app/frontend/config/ui-text/tag-*.json`
- `analytics-app/app/frontend/config/ui-text/series-tags.json`
- `analytics-app/app/frontend/config/ui-text/series-tag-editor.json`
- `analytics-app/app/frontend/config/ui-text/data-sharing-*.json`
