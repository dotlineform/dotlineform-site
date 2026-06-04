---
doc_id: site-request-docs-viewer-public-manage-entrypoints-baseline
title: Docs Viewer Public/Manage Entrypoint Baseline Inventory
added_date: 2026-06-04
last_updated: 2026-06-04
ui_status: done
parent_id: site-request-docs-viewer-public-manage-entrypoints
viewable: true
---
# Docs Viewer Public/Manage Entrypoint Baseline Inventory

Status:

- done

## Purpose

This child document is the pre-split baseline inventory for [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints).

It should be filled before implementation starts.
The inventory is not a one-off audit; later tasks consume its named sections when defining entrypoints, shell renderers, CSS/UI-text splits, report gating, nav/tree payloads, tests, and compatibility cleanup.

## Inventory Sections

### Current Public Route Loads

Public `/library/` and `/analysis/` are Jekyll routes that include `_includes/docs_viewer_readonly_route.html`, which delegates to `_includes/docs_viewer_shell.html` with `allow_management=false` and `route_config_url='/docs-viewer/config/routes/docs-viewer-public-routes.json'`.

Current public shell loads:

- JavaScript entrypoint before the first split slice: `docs-viewer/runtime/js/docs-viewer.js`
- CSS: `docs-viewer/static/css/docs-viewer-base.css`, `docs-viewer/static/css/docs-viewer.css`, and `docs-viewer/static/css/docs-viewer-reports.css`
- route registry: `docs-viewer/config/routes/docs-viewer-public-routes.json`
- Docs Viewer config: `docs-viewer/config/defaults/docs-viewer-public-config.json`
- UI text: `docs-viewer/config/ui-text/ui-text.json`
- report registry configured in route records: `assets/data/docs/reports.json`
- docs index: `assets/data/docs/scopes/library/index.json` or `assets/data/docs/scopes/analysis/index.json`
- search index: `assets/data/search/library/index.json` or `assets/data/search/analysis/index.json`
- selected document payloads from each index record's `content_url`, currently under `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`

Current public static JavaScript graph starts from `docs-viewer.js` and statically imports `docs-viewer-app-boot.js`, `docs-viewer-app-context.js`, `docs-viewer-route-config.js`, `docs-viewer-app-shell.js`, `docs-viewer-app-runtime.js`, and their shared controller/render/state dependencies. The static graph includes public reader features such as search, bookmarks, sidebar tree rendering, hosted views, config loading, generated-data reads, and panel layout. It also includes mixed public/manage owners:

- `docs-viewer-app-runtime.js` statically imports `docs-viewer-runtime-lazy-controller.js` and wires management runtime callbacks even when `allowManagement=false`.
- `docs-viewer-document-controller.js` statically imports `docs-viewer-report-service.js` and can dynamically import `docs-viewer-reports.js` when a payload contains `viewer_report`.
- `docs-viewer-hosted-views.js` contains a dynamic loader for `modules/source-editor/source-editor.js`, gated by hosted-view access.
- `docs-viewer-generated-data-runtime.js` includes local generated-read capability probing and preferred local generated-read paths, although public routes have no `generatedBaseUrl`.

Current public route config records do not include manage routes, hosted views, or management access. Public route boot therefore does not load `docs-viewer-management.js`, `docs-viewer-management-actions-renderer.js`, `docs-viewer-management-shell-renderer.js`, `docs-html-import.js`, or `docs-viewer-scope-lifecycle.js` during normal public route startup. Public route boot still downloads the broad shared entrypoint and report CSS, and still has report registry URLs in public route records.

Consumed by parent tasks:

- task 3: target public/manage import graphs
- task 6: public/manage UI text split
- task 7: public/manage CSS split
- task 8: report runtime and registry gating
- task 15: public-route absence tests

### Current Manage Route Loads

Local/manage `/docs/` is rendered from `docs-viewer/shell/docs-viewer-shell.html` by `docs-viewer/services/docs_viewer_service.py`.

Current manage shell loads:

- JavaScript entrypoint before the first split slice: `docs-viewer/runtime/js/docs-viewer.js`
- CSS: `docs-viewer/static/css/docs-viewer-base.css`, `docs-viewer/static/css/docs-viewer.css`, `docs-viewer/static/css/docs-viewer-reports.css`, and, when management is enabled, `docs-viewer/static/css/docs-viewer-management.css`
- route registry: `docs-viewer/config/routes/docs-viewer-routes.json`
- Docs Viewer config: `docs-viewer/config/defaults/docs-viewer-config.json`
- UI text: `docs-viewer/config/ui-text/ui-text.json`
- report registry: `assets/data/docs/reports.json`
- default docs index: `docs-viewer/generated/docs/studio/index.json`
- default search index: `docs-viewer/generated/search/studio/index.json`
- selected document payloads from local generated docs by-id paths

`docs_viewer_service.render_route_config_registry()` injects the local loopback service base URL into the manage route when local generated reads or management are enabled. In that case `createDocsViewerServiceContext()` treats the generated-read authority as `local generated-read service`, and `docs-viewer-generated-data-runtime.js` can request:

- `<managementBaseUrl>/capabilities`
- `<managementBaseUrl>/docs/generated/index?scope=<scope>`
- `<managementBaseUrl>/docs/generated/payload?scope=<scope>&doc_id=<doc_id>`
- `<managementBaseUrl>/docs/generated/search?scope=<scope>`
- `<managementBaseUrl>/docs/generated/references?scope=<scope>`
- `<managementBaseUrl>/docs/generated/reference-target?...`

Manage startup can dynamically load:

- `docs-viewer-theme.js` from `docs-viewer-app-boot.js`
- `docs-viewer-management-actions-renderer.js` and `docs-viewer-management-shell-renderer.js` from `docs-viewer-app-shell.js`
- `docs-viewer-management.js` from `docs-viewer-runtime-lazy-controller.js`
- `docs-html-import.js` from `docs-viewer-management.js` when import is opened
- `docs-viewer-scope-lifecycle.js` from `docs-viewer-management.js` for scope create/delete workflows
- `docs-viewer-management-client.js` from source-editor services in `docs-viewer-app-runtime.js`
- report modules from `docs-viewer-reports.js` when a rendered document payload declares `viewer_report`
- `modules/source-editor/source-editor.js` from `docs-viewer-hosted-views.js` when the source-editor hosted view is requested

Management boot checks service capability through `docs-viewer-management-capabilities.js` and `docs-viewer-management-client.js`. Additional management service requests are triggered by user actions, including metadata writes, status/viewability writes, rebuilds, source reads/rebuilds, import, settings, scope lifecycle, source opening, and report service calls.

Consumed by parent tasks:

- task 3: target public/manage import graphs
- task 5: manage shell path
- task 16: manage-route smoke coverage

### Current Shared Static Import Graph

Current entrypoint root:

- before the first split slice, `docs-viewer/runtime/js/docs-viewer.js` statically imported only `docs-viewer-app-boot.js`

Public-safe shared primitive candidates:

- `docs-viewer-access.js`
- `docs-viewer-asset-url.js`
- `docs-viewer-render.js`
- `docs-viewer-router.js`
- `docs-viewer-search.js`
- `docs-viewer-tree.js`, except its current callers pass management filtering flags
- `docs-viewer-view-state.js`
- `docs-viewer-hosted-view-capabilities.js`

Public app-owned or public-safe reader modules:

- `docs-viewer-app-context.js`
- `docs-viewer-route-config.js`, after compatibility cleanup and public/manage route-registry separation
- `docs-viewer-config-service.js`, for browser-safe config and UI text reads
- `docs-viewer-config-controller.js`, except scope-query/manage-mode handoff should stay manage-owned where possible
- `docs-viewer-bookmarks.js`
- `docs-viewer-favourites.js`
- `docs-viewer-search-controller.js`
- `docs-viewer-route-workflow.js`, except manage-mode and management callback wiring
- `docs-viewer-sidebar.js`, once drag/status/manage text hooks are separated
- `docs-viewer-document-index-state.js`, once manage-only filtering/status behavior is layered above a shared tree primitive
- `docs-viewer-index-panel-renderer.js`
- `docs-viewer-main-view-renderer.js`, except hidden manage edit/source buttons
- `docs-viewer-info-panel-renderer.js`
- `docs-viewer-metadata-info-view.js`
- `docs-viewer-info-panel-host.js`
- `docs-viewer-info-panel-controller.js`
- `docs-viewer-main-view-host.js`
- `docs-viewer-panel-layout.js`
- `docs-viewer-app-session.js`
- `docs-viewer-view-context.js`
- `docs-viewer-top-bar-renderer.js`
- `docs-viewer-viewer-toolbar-renderer.js`
- `docs-viewer-scope-select-menu.js`

Manage app-owned modules:

- `docs-viewer-management.js`
- `docs-viewer-management-action-workflow.js`
- `docs-viewer-management-actions.js`
- `docs-viewer-management-actions-renderer.js`
- `docs-viewer-management-capabilities.js`
- `docs-viewer-management-client.js`
- `docs-viewer-management-config.js`
- `docs-viewer-management-interactions.js`
- `docs-viewer-management-modal-shell.js`
- `docs-viewer-management-modals.js`
- `docs-viewer-management-parent-picker.js`
- `docs-viewer-management-render.js`
- `docs-viewer-management-shell-renderer.js`
- `docs-viewer-runtime-lazy-controller.js`
- `docs-viewer-drag-drop.js`
- `docs-viewer-theme.js`

Report-owned modules:

- `docs-viewer-report-service.js`
- `docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/*.js`

Source-editor/import/scope-lifecycle/settings/status-owned modules:

- `modules/source-editor/source-editor.js`
- `docs-html-import.js`
- `docs-html-import-modals.js`
- `docs-html-import-render.js`
- `docs-html-import-workflow.js`
- `docs-viewer-scope-lifecycle.js`
- settings behavior inside `docs-viewer-management.js`, `docs-viewer-management-modals.js`, and `docs-viewer-management-client.js`
- status/viewability mutation behavior inside `docs-viewer-management.js`, `docs-viewer-management-actions.js`, and `docs-viewer-management-client.js`

Unclear or mixed responsibility modules:

- `docs-viewer-app-boot.js`: public/manage shared boot with manage-only theme toggle import.
- `docs-viewer-app-shell.js`: shared shell renderer that conditionally imports manage shell/actions.
- `docs-viewer-app-runtime.js`: public runtime plus management adapter/context wiring.
- `docs-viewer-app-composition.js`: public app composition plus management constants/startup phases and generated-read service authority.
- `docs-viewer-service-context.js`: route access projection plus generated-read/local management service authority.
- `docs-viewer-generated-data-runtime.js`: static JSON reads plus manage/local generated-read capability probes and fallback/preferred generated reads.
- `docs-viewer-data.js`: low-level static fetches plus reload and management generated-read path switching.
- `docs-viewer-document-controller.js`: rendered document loading plus report service/context/dynamic report import.
- `docs-viewer-hosted-views.js`: metadata/info defaults plus source-editor hosted view registration.

Consumed by parent tasks:

- task 3: target public/manage import graphs
- task 10: shared core boundary
- task 11: public/manage mode switch and manage capability switch cleanup
- task 13: nav/tree renderer and payload adapter placement

### Current JSON Config And Data Loads

Public JSON/config/data loads:

- `docs-viewer/config/routes/docs-viewer-public-routes.json`
- `docs-viewer/config/defaults/docs-viewer-public-config.json`
- `docs-viewer/config/ui-text/ui-text.json`
- `assets/data/docs/reports.json` when a report payload is rendered, and also present as route config data even for normal public docs
- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/analysis/index.json`
- `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`
- `assets/data/search/library/index.json`
- `assets/data/search/analysis/index.json`
- `assets/data/docs/scopes/<scope>/references/index.json` and reference-target payloads only when hosted/reference behavior requests them

Manage JSON/config/data loads:

- `docs-viewer/config/routes/docs-viewer-routes.json`
- `docs-viewer/config/defaults/docs-viewer-config.json`
- `docs-viewer/config/ui-text/ui-text.json`
- `assets/data/docs/reports.json` for reports
- `docs-viewer/generated/docs/studio/index.json` and other configured local scope indexes
- `docs-viewer/generated/docs/<scope>/by-id/<doc_id>.json`
- `docs-viewer/generated/search/studio/index.json` and other configured local search indexes
- `docs-viewer/generated/docs/<scope>/references/index.json` and reference-target payloads when reference features request them
- loopback generated-read equivalents through `/docs/generated/...` when capabilities permit
- loopback management payloads for source config, settings, source reads, source writes/rebuilds, import, scope lifecycle, status/viewability, and reports

The single UI text bundle currently contains public reader copy and management/import/scope lifecycle/settings/status copy. The public route registry currently carries `config_urls.report_registry` even though no public route currently needs reports.

Consumed by parent tasks:

- task 6: UI text split
- task 8: report registry gating
- task 12: compatibility and fallback cleanup in boot/config/data surfaces
- task 13: public/manage nav/tree payload design
- task 14: public index slimming coordination

### Current CSS Loads And Selectors

Docs Viewer CSS files:

- `docs-viewer/static/css/docs-viewer-base.css`: base `.docsViewer` tokens, service-body layout, hidden utilities, muted/small text, and pre formatting. Public-safe if service-body rules remain acceptable for both installs.
- `docs-viewer/static/css/docs-viewer.css`: shared shell layout, sidebar/index, top bar, viewer toolbar, search, scope select, recently-added, status line, bookmark row/pills, main-view meta/content, info panel, metadata info, status-pill/menu styling, rendered content, search results, and "more" controls.
- `docs-viewer/static/css/docs-viewer-reports.css`: report root, toolbar, filters, report search, tables, sort controls, report rows, config report layout, references/change rows, pager, and report status.
- `docs-viewer/static/css/docs-viewer-management.css`: import UI, manage-mode theme colors, draft/non-viewable nav styling, drag/drop states, context menu, modals, metadata/settings fields, parent picker, scope lifecycle, source editor, import-in-modal layout, manage action row/menu, theme toggle, and status/viewability management controls.

Selector classification:

- Public reader shell: `.docsViewer`, root panel grid/data states, hidden utility, top bar, viewer toolbar, index/main/info mounts.
- Public index/main/info/search: `.docsViewer__sidebar*`, `.docsViewer__nav*`, `.docsViewer__toggle*`, `.docsViewer__main*`, `.docsViewer__meta*`, `.docsViewer__content*`, `.docsViewer__search*`, `.docsViewer__result*`, `.docsViewer__more*`, `.docsViewer__infoPanel*`, `.docsViewer__metadataInfo*`, `.docsViewer__bookmark*`.
- Report: all `.docsViewerReport*` selectors in `docs-viewer-reports.css`.
- Management shell/actions/modals: `.docsViewer__manageRow`, `.docsViewer__manageActions`, `.docsViewer__actionsMenu*`, `.docsViewer__actionMenu*`, `.docsViewer__contextMenu*`, `.docsViewer__modal*`, `.docsViewer__field*`, `.docsViewer__parentPicker*`, `.docsViewer__settingsWarnings`.
- Source editor/import/scope lifecycle/settings/status: `.docsViewerSourceEditor*`, `.docsViewerImport*`, `.docsViewerScopeLifecycle*`, `.docsViewer__draft*`, `.docsViewer__statusPills`, `.docsViewer__statusMenu*`, `.docsViewer__navRow.is-draft`, drag/drop classes, management busy textarea rules.
- Host public-site CSS outside Docs Viewer ownership: public Jekyll routes still inherit `assets/css/main.css` and surrounding site styles outside this split.

Current public routes already omit `docs-viewer-management.css`, but still load `docs-viewer-reports.css` and the broad `docs-viewer.css` selectors for status menus and manage-adjacent controls.

Consumed by parent tasks:

- task 7: public/manage CSS split
- task 9: public DOM cleanup for hidden manage controls
- task 15: public-route CSS absence tests

### Current Public DOM Controls

Public Jekyll shell markup with `allow_management=false` renders:

- `#docsViewerRoot`
- `#docsViewerHeaderControlsMount`
- `#docsViewerStatus`
- `#docsViewerBookmarkRow`
- `#docsViewerIndexPanelMount`
- `#docsViewerMainViewMount`
- `#docsViewerInfoPanelMount`

Public boot-created controls include:

- header/viewer toolbar: recently-added button, search input, index panel toggle, info panel toggle; scope select is omitted because public route records set `allow_scope_query=false`
- index panel: sidebar shell, collapse/expand buttons, nav tree rows/links/toggles
- main view: toolbar, meta row, path/updated text, status-pills mount, bookmark toggle, content, results status/list, more control
- info panel: metadata info panel and close/toolbar controls

Public route does not render:

- `#docsViewerManagementShellMount`
- `#docsViewerManageActionsMount`
- management action menu
- context menu
- metadata modal
- import modal
- settings modal
- scope lifecycle modal content

Current public DOM still contains hidden manage-only main-view controls because `docs-viewer-main-view-renderer.js` always creates `#docsViewerManageEditButton` and `#docsViewerManageSourceButton`. It also creates `#docsViewerStatusPills`, which is a mixed status display/write surface: public runtime hides it when no management controller is present, but the DOM and shared CSS still exist.

Consumed by parent tasks:

- task 4: public shell renderer/path
- task 9: removal of public hidden manage DOM
- task 15: public-route DOM absence tests

### Current Manage DOM Controls

Manage service shell markup renders the same core mounts as public plus `#docsViewerManagementShellMount` when management is enabled. During boot, `docs-viewer-app-shell.js` renders manage action markup into the top-bar management mount and management shell markup into `#docsViewerManagementShellMount`.

Current manage DOM controls include:

- management toolbar/action row: `#docsViewerManageRow`, `#docsViewerManageActionsButton`, `#docsViewerManageActionsMenu`, `#docsViewerManageRebuildButton`, `#docsViewerManageSettingsButton`, `#docsViewerManageNewScopeButton`, `#docsViewerManageDeleteScopeButton`, `#docsViewerManageImportButton`, `#docsViewerManageNewButton`, `#docsViewerManageDeleteButton`, `#docsViewerManageViewableButton`, `#docsViewerDraftToggle`, and theme toggle controls
- main-view management entry points: `#docsViewerManageEditButton`, `#docsViewerManageSourceButton`, and `#docsViewerStatusPills`
- context menu and drag/drop: `#docsViewerContextMenu`, context menu action buttons, draggable nav links, and nav row drop-state classes
- metadata modal: `#docsViewerMetadataModal`, metadata form fields, status select, non-viewable checkbox, parent picker, cancel/save buttons
- import host: `#docsViewerImportModal`, `#docsHtmlImportRoot`, import controls and import status/result/warning elements
- settings controls: `#docsViewerSettingsModal`, settings form, updated-date checkbox, warnings/status, cancel/save buttons
- scope lifecycle controls: rendered dynamically from `docs-viewer-scope-lifecycle.js` when create/delete scope workflows open
- source editor view: loaded as `modules/source-editor/source-editor.js` when requested through hosted views/source actions

Consumed by parent tasks:

- task 5: manage shell renderer/path
- task 16: manage-route smoke coverage

### Current Fallback And Compatibility Paths

Compatibility and fallback paths found in touched boot/config/data surfaces:

| owner file | behavior | context | removal target | removal blocker / verification |
| --- | --- | --- | --- | --- |
| `docs-viewer/runtime/js/docs-viewer-route-config.js` | Accepts both snake_case and camelCase for route/config fields through `firstPresent()`. | public and manage | Single current schema field naming. | Requires updating route fixtures/tests and confirming generated route registries only emit the chosen schema. |
| `docs-viewer/runtime/js/docs-viewer-route-config.js` | Infers `routeType` from `allowManagement` when route type is missing. | public and manage | Require explicit `route_type`. | Requires route-registry validation and test updates. |
| `docs-viewer/runtime/js/docs-viewer-route-config.js` | Selects registry route by requested route id, then falls back to path matching. | public and manage | Decide whether route-id or path is the sole contract per entrypoint. | Requires shell/rendered route templates to always provide the chosen selector. |
| `docs-viewer/runtime/js/docs-viewer-route-config.js` | `pathMatchesRoute()` accepts `route_path`, `routePath`, `viewer_base_url`, and `viewerBaseUrl`. | public and manage | Require current route path field. | Requires confirming no active route registry depends on viewer-base matching. |
| `docs-viewer/runtime/js/docs-viewer-route-config.js` | Panel defaults accept snake_case and camelCase and default missing panel state/view values. | public and manage | Require normalized generated route config or explicit defaults owned by route config. | Needs panel config contract update. |
| `docs-viewer/runtime/js/docs-viewer-config-service.js` | Missing UI text URL resolves to `null` rather than visible boot failure. | public and manage | Public/manage UI text should be required by the route context that needs it. | Needs UI-text split and config-service tests. |
| `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` and `docs-viewer/runtime/js/docs-viewer-data.js` | Prefer local generated-read service when capability says available, otherwise read static JSON. | manage; public has no generated base URL | Split public static reader from manage generated-read adapter. | Requires entrypoint split and manage smoke for local generated reads. |
| `docs-viewer/runtime/js/docs-viewer-data.js` | Reload nonce can switch static URL reads to management reload paths. | manage | Keep only in manage generated-read adapter. | Requires source/rebuild workflow tests. |
| `docs-viewer/runtime/js/docs-viewer-reports.js` | Falls back to an in-code `FALLBACK_REPORT_REGISTRY` if `assets/data/docs/reports.json` fails. | public and manage when report payload renders | Remove fallback; report registry absence should be visible. | Needs report gating behind manage entrypoint and report tests. |
| `docs-viewer/runtime/js/docs-viewer-management.js` | Import boot uses hardcoded fallback config/UI text URLs if context/service values are absent. | manage | Require manage service context values. | Needs import modal smoke update. |
| `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js` and `docs-viewer-app-shell.js` | Management dynamic imports catch failures and continue with no management controller/shell. | manage | Manage route should render explicit unavailable state when required management modules fail. | Needs manage-shell failure test; not removed in baseline slice. |
| `docs-viewer/runtime/js/docs-viewer-document-controller.js` | Report rendering is optional and dynamically imported based on payload metadata from the shared runtime. | public and manage | Reports should be manage-owned until explicitly public-promoted. | Requires report runtime move and public negative asset-load test. |

Consumed by parent tasks:

- task 11: shared module mode/capability cleanup where relevant
- task 12: compatibility and silent fallback cleanup

### Current Index Tree Construction

Current public and manage index trees are built in the browser from flat index payloads.

Flat payloads used:

- public: `assets/data/docs/scopes/<scope>/index.json`
- manage: `docs-viewer/generated/docs/<scope>/index.json` or the loopback `/docs/generated/index?scope=<scope>` equivalent when generated reads are available

Browser-time shaping:

- `docs-viewer-route-workflow.js` sorts `payload.docs` with `compareDocs()`, stores `viewer_options.non_loadable_doc_ids`, `viewer_options.manage_only_tree_root_ids`, and `viewer_options.show_updated_date`, then calls `documentIndex.applyDocVisibility()`.
- `docs-viewer-document-index-state.js` builds `allDocsById`, filters viewable docs for public mode, keeps non-viewable docs in manage mode when `showNonViewable` is true, handles manage-only tree root exclusion in public mode, sorts docs, and builds `childrenByParent`.
- `docs-viewer-tree.js` groups records by `parent_id` and sorts each sibling group by title/doc_id.
- `docs-viewer-sidebar.js` recursively renders `<ul>` trees from `childrenByParent`, computes trails at runtime, adds current-doc highlighting, expansion state, status icons, non-viewable markers, draggable links, and generated viewer URLs.

Build-time fields already available in flat records include at least `doc_id`, `title`, `parent_id`, `last_updated`, `viewable`, `ui_status`, `content_url`, and other metadata consumed by document/info rendering. `viewer_options` already carries `non_loadable_doc_ids`, `manage_only_tree_root_ids`, and `show_updated_date`.

Public nav fields needed for reader navigation:

- stable id
- label/title
- parent or prebuilt children
- selected-document target id for non-loadable/group nodes
- content/document target enough to build route URLs
- optional updated date if still shown in nav/meta
- optional status display only if public status indicators remain public-safe

Manage nav fields currently needed:

- id/title/parent/children/order
- viewability/non-viewable state
- non-loadable/group-node state
- manage-only tree root state
- UI status value for status indicators and menus
- drag/drop eligibility and parent constraints
- source/metadata action target id
- context-menu action eligibility
- fields needed for create sibling/child, delete, viewability update, metadata update, status update, and source opening

Fields needing confirmation before entering a manage nav/tree payload:

- complete drag/drop constraints and blocked descendant sets
- context-menu action availability per row
- scope lifecycle action state
- source path or source-open metadata, because source/open authority should remain behind management endpoints
- status write capability per doc versus per scope
- whether summary/updated date should be in nav payload or selected-document payload only

Consumed by parent tasks:

- task 13: public/manage nav/tree payloads and payload-agnostic tree renderer
- task 14: public index slimming coordination

## Output Requirements

The completed baseline should make later slices traceable.

Each parent task that depends on the baseline should cite the relevant section name and summarize what decision it took from the inventory.
If a section is incomplete, the dependent task should not guess; it should either finish the section first or record a blocker.

Do not use compatibility fallbacks to compensate for unknown inventory state.
