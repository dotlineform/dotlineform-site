---
doc_id: site-request-analytics-app-split
title: Analytics App Split Request
added_date: 2026-05-30
last_updated: 2026-05-30
ui_status: urgent
parent_id: change-requests
viewable: true
---
# Analytics App Split Request

Status:

- proposed
- urgent structural risk-reduction work

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
- no attempt to remove all historical references in old change logs

## Target Ownership

### Studio

Studio owns:

- catalogue editors
- catalogue import, save, delete, publication, and build actions
- catalogue field registry review
- project state
- Studio audits, activity, backup retention, and admin pages unless later split out

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
| `/studio/api/analytics/...` | `/analytics/api/...` or `/analytics/api/tags/...` |
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

## Risks

- The current frontend modules may import generic Studio helpers and CSS.
  Decouple these during the split where it is cheap, obvious, and does not turn the cutover into a redesign.
  If meaningful Studio helper or CSS coupling remains after the lift-and-shift, create a follow-on slice or request so Analytics owns its CSS, frontend helpers, UI text/config helpers, and route-shell primitives.
- Data Sharing currently touches documents and tags.
  Analytics should own the workflow, but Docs Viewer can remain the focused owner for document conversion/source helpers.
- Existing tests and docs use Studio naming for analytics checks.
  Rename active checks to Analytics ownership where they are purely Analytics checks, and split mixed Studio/Analytics checks where one test currently covers both future service responsibilities.
- Removing old routes without compatibility aliases may break bookmarks.
  This is acceptable for the maintenance-risk goal; update visible navigation and docs in the same slice.
- Activity/audit ownership may need a later service split.
  Keep them in Studio for now unless a moved Analytics workflow already has a natural Analytics activity record.
- UI Catalogue may still depend on some Studio visual primitives.
  Keep those dependencies explicit and static rather than making UI Catalogue a Studio route.
- Thumbnail-quality archival can become busywork if it tries to preserve every historical runtime path.
  Prefer a clear retired tooling location plus a short note about why it is not active.

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
- `studio/app/server/studio/studio_analytics_api.py`
- `studio/app/server/studio/studio_data_sharing_api.py`
- `studio/services/analytics/`
- `data-sharing/`
- `ui-catalogue-app/`
- `bin/local-ui-catalogue`
- `studio/retired/thumbnail-quality/thumbnail-quality.js`
- `studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py`
- `studio/app/frontend/js/tag-*.js`
- `studio/app/frontend/js/series-tag*.js`
- `studio/app/frontend/js/data-sharing-*.js`
- `studio/app/frontend/config/ui-text/tag-*.json`
- `studio/app/frontend/config/ui-text/series-tags.json`
- `studio/app/frontend/config/ui-text/series-tag-editor.json`
- `studio/app/frontend/config/ui-text/data-sharing-*.json`
