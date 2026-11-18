---
draft: false
doc_id: d-20260331-000000-c313fd
title: Runtime
added_date: "2026-03-31 00:00:00"
last_updated: "2026-11-18"
summary: Public, manage, and review execution paths; browser/server authority boundaries; extension method; rationale; and known weak spots.
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Runtime

Docs Viewer has one shared reader model and three deliberately separate application surfaces: public reading, local management, and validated-package review.

The runtime boundary is not “which controls are hidden.” It is the combination of:

- which entrypoint and static imports are shipped
- which behaviour route config composes
- which code definitions are registered
- which live services and capabilities are available
- which service validates and executes a requested local operation

## Three Surfaces

| surface | browser composition | data and service authority |
| --- | --- | --- |
| Public `/` | Static shell, public entrypoint, public-safe shared reader, and explicitly promoted public features. | Published static config and generated payloads. No local source or management services. |
| Manage `/docs/` | Service shell, manage entrypoint, shared reader, and Working views, authoring controls, reports and imports. | Independent generated-data, source, and management service surfaces, constrained by live capabilities and server validation. |
| Review `/docs-review/` | Review shell, shared reader, returned-package provider, and package toolbar/workflow. | Independently gated reads over validated package previews. No canonical source write or general management authority. |

Public and Manage share the top-row renderer and theme control. The `dotlineform` home link opens the configured default document at `/` publicly or `/docs/` in Manage. Document and management controls occupy the shared top row; Recent and Search occupy the first row inside the Index panel. The shared toolbar has no breadcrumb trail. Theme changes apply shared reader colours and retain the public theme event; imported SVG keeps its authored appearance.

The shared reader's [CSS owner](CSS_Ownership.md#layout-and-prose) defines page insets, sticky desktop controls, collection reading widths and specialised prose. [Control surfaces](Panel_Hosts_And_Control_Surfaces.md) separates placement from the focused action/state owner.



Loading and other in-flight work are textually quiet across Public, Manage and the shared Review composition. Reports, inline images, Media View, Search/Recent, Source and its pickers, management actions, Import/Export/package flows and Regenerate do not insert loading/running/preparing messages or temporary availability-check tooltips. Existing request lifetimes, disabled controls, busy cursors, `aria-busy`, action labels and error/completion/empty-state feedback remain with their owning workflows. Control availability uses explicit busy/readiness/selection flags independently of explanatory text; removing a message must not enable an action before its inputs are ready. Errors retain their visible status nodes, and a new request clears old feedback without replacing it with progress prose.

[Focus presentation](CSS_Ownership.md#focus-and-feedback) uses one shared keyboard-navigation mode. Actual focus, modal trapping and restoration remain with their workflow owners.

[Toolbar Icons](Toolbar_Icons.md) owns mask/button styling, artwork selection and explicit public assets.

Manage shows its Actions controls in the top row. The Index tree context menu owns Copy Link, Open, Open in VS Code, New Sibling, New Child, Position, Sort Children A–Z, Prepare package and Delete. Every menu action captures the invoked ordinary tree node independently of the main pane, including a collection host while its detail document is displayed. Prepare package and Delete use that node and its complete subtree, including collapsed descendants; package profiles and filters still determine the effective package set. Position moves the node with its descendants. No second-row Index management controls, checkboxes or selection commands remain. Collection Actions shares the top row with the other document and collection actions and retains its own checked-row workflow. [Export](Export.md) is available only there, using one captured collection selection and one browser workflow. The public reader has no management controls.

Sort Children A–Z saves a one-off order of the invoked parent's immediate ordinary Index children, including collapsed branches; each child's descendants retain their existing structure and order. The browser sorts loaded literal titles with English case/accent-insensitive natural numeric collation, preserves existing order for equivalent titles and sends `{parent_doc_id, child_doc_ids}` to `POST /docs/order-children`. Already sorted children require no request. Fewer than two children disables the action. Later title changes and additions retain normal authored order until the action runs again. Named-collection report rows keep their own sorting controls. [Builder](Builder.md) owns the shared navigation-only completion with same-parent Position; the server trusts the supplied child membership.

Right-click or Shift+F10/the context-menu key opens the menu for its row. A temporary outline identifies the target without changing the displayed-document marker; arrow keys, Home/End, Escape and Tab provide keyboard navigation and dismissal. The frontend action resolver and existing capability/busy rules govern availability. Position, Sort Children A–Z and permitted Delete remain disabled during source editing. The operation modals identify their target by title and ID and describe descendant scope; New Sibling/Child also identify their relative document. Opening or dismissing the menu does not load a document. Position, sorting and deletion of another subtree refresh the Index while preserving the surviving main-pane document, collection detail, route and reading position. Delete navigates to a surviving document only when the displayed node is removed. Focus restoration resolves the current target row after a tree refresh, or the displayed row when the target is gone or hidden.

“Shared” does not mean public. A module is part of the public surface only when the public entrypoint imports it or a public-safe lazy path can reach it.

## Document Action Context And Toolbar Placement

The [document controller](../../docs-viewer/runtime/js/shared/docs-viewer-document-controller.js) owns the exact displayed target and record for ordinary and named-collection documents. The [collection list](../../docs-viewer/runtime/js/shared/docs-collection-report.js) contributes its host document and containing collection context while that list is displayed; it owns no document detail reader. Named documents obtain their supported Manage actions and private metadata through the existing collection contribution owner, independently of a manifest or calling report. Loading, invalid and error states supply no action target. A retained hidden report cannot replace the active document's context.

One design-time default feeds both readers through [configuration projection](Configuration_And_Extension_Points.md#workspace-and-target-contracts).

**Edit doc → Rebuild** rebuilds only the displayed ordinary or named-collection document when its frontend action resolution permits it. The UI excludes Catalogue Work documents. The local client posts its exact `{doc_id}` or `{collection, doc_id}` target to `/docs/rebuild-document`; the [document rebuild owner](../../docs-viewer/services/docs_document_rebuild.py) resolves the confined existing source, requires Working authoring capability and awaits the existing targeted builder. Incremental Links maintenance runs for that document and its relationship records; neighbouring document content is not rebuilt. Source bytes/dates, Search, Catalogue Refresh and media production are unchanged. Source Save uses the same build owner. The menu combines the frontend action resolution with existing rendered-document and busy availability rules. Management remains busy through the build and forced reload, validates the response's exact target, replaces the current browser entry and reports build/reload failure through the existing status. Forced reader loads bypass retained content and read a fresh generated payload; ordinary navigation and Back/Forward retain their existing records. Rebuilding uses current generated image inputs; regenerating actual media remains with its owning workflow.

The [management control resolver](../../docs-viewer/runtime/js/management/docs-viewer-management-report-controls.js) and [collection action composition](../../docs-viewer/runtime/js/management/docs-viewer-management-collection-composition.js) consume the common reader's resolved targets. Edit, Open in VS Code, Draft/Ready and named-document actions use the displayed document; New and Regenerate use the containing collection; checked-row actions use the explicit collection selection. Source keeps its captured target, including when opening that source in VS Code. Management operations retain capability, busy, service and committed-result checks. Lists retain filtering, sorting, selection and reconciliation.

Documents permitted to use Draft/Ready retain that action when publication policy excludes them. Its icon reflects the saved draft value; collection hosts and maintained private reports omit the action through the frontend action resolver. `/docs/index-tree` reads saved Working navigation without publication-policy or canonical-ancestry reads. The obsolete exclusion flag, its browser carry-through and its retired control wording are removed. Publication generation retains complete eligibility, including draft subtrees and collection-host exclusions.

The [main toolbar renderer](../../docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js) presents document and collection actions in the existing page-wide top row beside management controls. Document navigation uses browser Back/Forward. A rendered named-collection document has a `list.svg` shortcut with tooltip and accessible label `index`; it opens the configured ordinary report host regardless of the document's entry path and adds a normal browser entry. The active Index view and search query remain independent of that opening. Ordinary documents have no document Back or index shortcut. Source and Content Detail hide the shortcut; Content Detail keeps its own within-document return control. Existing spacing, narrow-header wrapping and document-width placement remain with the shared renderer and styles.

Collection search and filters remain beside the list. Sort and row-selection controls are Manage-only; public lists retain their default order: recently updated for Catalogue and title A–Z for the other collections. Manage's sort button follows the collection search field with the standard report toolbar gap (`0.55rem`). The clock switches to recently updated, and the A–Z icon switches to title order. The tooltip and accessible label name the current order and the action. There is no duplicate detail action row. Source and Content Detail hide the collection controls while retaining their mounted nodes; generated detail refresh updates content and context without rebuilding those controls. [Shared layout](../../docs-viewer/static/css/docs-viewer.css), [report styling](../../docs-viewer/static/css/docs-viewer-reports.css) and [Manage styling](../../docs-viewer/static/css/docs-viewer-manage.css) own these presentation rules.

[Theme and neutral colour roles](CSS_Ownership.md#themes-and-shared-fields) belong to the palette and owning stylesheet; controls consume those roles without changing their selection or workflow state.

## Document Action Policy

The existing [frontend action registry and resolver](../../docs-viewer/runtime/js/management/docs-viewer-action-definitions.js) own document-action availability. `resolveDocsViewerAction` accepts an exact document or collection/selection target, the ordinary Index subtree when needed and configured collection-host IDs. It returns target IDs, visibility, enablement and the disabled reason together. Edit menus, Index actions/shortcuts, Source invocation and collection contributions consume this result through the existing management action resolver. The shared control registry continues to own route/view placement, feature and capability gates; public controls need no management server.

Catalogue permits only Star and Copy link for its Work documents and omits New and package/selection controls for its collection. All configured collection hosts and the 15 explicit private-report IDs omit Delete, Star and Draft. Hosts derive from the existing browser workspace configuration without source discovery or hierarchy validation. Private-report IDs are code-owned in the action registry, independently of report type and publication exclusions; future unlisted public reports retain ordinary defaults, including Star. Add a new fixed private report's ID there when the same product restriction is intended.

Report-host Source editing, Open in VS Code and Rebuild remain available. Catalogue Work source editing, source opening, Draft, independent Rebuild and independent creation/deletion remain unavailable in the frontend; Work edits, Refresh and Regenerate own the normal authoring lifecycle. The Edit trigger remains available for Star/Copy independently of Source-editor availability. Restricted Star actions skip selection reads and restricted collection Delete contributions are omitted before workflow loading. Workspace Import, Rebuild, Publish and Settings remain independent of the displayed document's restrictions; collection Regenerate remains available. Collection selection can be entered with no checked rows; Export requires a nonempty selection and remains available in Catalogue, where Prepare Package retains its restriction.

These are frontend product restrictions, not endpoint authorization rules. Services retain their existing exact identity, confined path, source/schema, authoring-workspace, request/revision and operation validation. Direct service callers are governed by those operation requirements, including Catalogue's intrinsic prohibition of a draft field. The shared Catalogue document builder still contributes completed document-only changes to the publication queue for direct build/Source Save callers. No document-action rules are loaded or projected by the server, and capabilities describe actual service availability. Temporary service/loading/busy conditions remain with the existing control and workflow owners. Publication eligibility and authored draft values retain their existing owners.

The 2026-10-11 simplification removes the separate JSON policy, Python matcher, endpoint guards and browser policy resolver. Restart Docs Viewer and hard-refresh its page to adopt the service and frontend changes together; cached JavaScript can retain the previous action resolver. Catalogue Work menus hide Source editor, Rebuild, Open in VS Code, Draft and Delete, leaving Star and Copy link visible. Star retains its temporary loading, busy and service availability states.

## Retained Index Views

The Index panel owns its tree, Search and Recent independently of the displayed document and Info capture. The main pane owns document and report mounts. [Reader data and retained state](Reader_Discovery_And_Return.md#retained-index-views)

## Exact Document Navigation And Return

The route workflow opens ordinary `?doc=<id>` or named `?collection=<owner>&doc=<id>` through the configured provider. Copy Link identifies the document, while the collection shortcut opens its configured host. Review opens exact package members under its own authority. Content Detail runs inside the current document mount and releases it back to its invocation position. [Reader return paths](Reader_Discovery_And_Return.md#exact-document-navigation-and-return)

## Public Execution Path

```text
static public route shell
        |
        v
public entrypoint
        |
        +--> public route registry + public browser config
        |
        +--> shared boot + public-safe code definitions
                         |
                         v
              published docs/search/report data
                         |
                         v
              tree, document, search and panels
```

Public route records contain blank local service URLs. The browser reads published assets and does not probe the local Docs Viewer service.

Public capabilities are promoted deliberately. A public report, view or control needs a public-safe loader and data source. Review route configuration and trace imports from the public entrypoint so Manage, Review, Import, Source Editor and local report modules stay outside the public runtime. The site-code inventory controls which files ship. [Verification](../development/Verification.md#docs-viewer-site-code-projection)

## Local HTTP Caching

The Docs Viewer service uses browser-private HTTP caching for normal browsing. `docs_http_cache.py` owns cache lifetimes and ETag comparison; the HTTP handlers select the policy after their existing route, capability and path checks. There is no process payload cache or workspace-wide hashing step.

| Response | Policy |
| --- | --- |
| App JavaScript, CSS, icons and fonts | `private, max-age=86400`: reuse for one day. |
| Catalogue primary images carrying a positive `v` media version | `private, max-age=31536000, immutable`: reuse that versioned URL for one year. |
| Unversioned shared media, document/collection/report data, HTML shells and configuration | `private, no-cache`: store the response and revalidate before reuse. |
| Source editing, capabilities, management operations and JSON errors | `no-store`: read current state directly. |

Requested-file responses use weak validators based on nanosecond modification/change times and size. Unchanged conditional reads return `304` without opening or transferring the file. Transformed HTML and JSON API responses use an ETag of their actual response bytes. They still perform the owning read and validation before comparison, so missing files and failed requests remain errors rather than cached success. API cache responses vary by Origin and retain their allowed CORS headers on `304`.

Generated-data, collection refresh, Catalogue presentation and generated-report clients use browser revalidation rather than `no-store`. Catalogue token authoring uses the same `no-cache` request policy for its repository token registry and generated target lookup. `no-cache` permits storage and requires revalidation; `no-store` bypasses storage. The browser handles `304` and supplies the cached body to the existing renderer. Initial loads, navigation and completed application actions request their required current data explicitly; an idle Working viewer makes no recurring index or document reads. Source/management clients and Studio canonical-data reports retain their own freshness boundaries. Docs Review package endpoints retain their existing policy.

App code URLs currently use a fixed shell version marker, not automatic code-version invalidation. After developing JavaScript, CSS or icons, use a forced reload or clear cached files as needed. Browser history need not be removed. Do not apply the one-day app policy to generated JSON or authored media, and do not treat an arbitrary query parameter on an unversioned asset as a Catalogue media version. Public hosting keeps its own response-header policy; shared client changes reach the tracked site through the runtime projection.

## Manage Execution Path

```text
standalone Docs Viewer service
        |
        +--> manage shell
        +--> route registry with enabled local service URLs
        +--> capability response derived from config, environment and filesystem
        |
        v
manage entrypoint --> shared boot + manage code definitions
                              |
                              v
                   generated/source/management clients
                              |
                              v
                   validated server endpoint
                              |
                              v
                   operation-owned source and derived results
```

The local service injects generated-data, source, and management base URLs independently when it serves route config. The browser then fetches live capabilities before offering operations that depend on the backend.

Route intent is not authority. `app_kind: manage`, `management_ui: true`, a visible action, or a non-empty service URL cannot authorize a write. The owning endpoint still validates the exact target, operation, paths, payload, and filesystem conditions.

Named-collection New uses the configured Working destination without a directory-existence preflight or listing, reading or validating existing source documents. It retains create-request checks, allocates an immutable ID and uses an atomic create-only write that refuses an existing destination. The existing write/rebuild owner builds the new document and initializes its Links file before the browser selects the exact committed target and opens Source. Shared generated-manifest checks belong to the builder. Ordinary hierarchical document creation retains its existing source inventory and parent validation.

Working Catalogue exposes queue-only Regenerate and omits independent New/Delete. `POST /docs/catalogue/regenerate` accepts exactly `{collection: "catalogue"}`. The owner reads only refreshed queue entries and exact matching sources/Working records, completes each selected source/document Build, merges publication selection, then removes the updates entry. False-readiness entries remain pending. Catalogue Entry plus Related Links is the generated body; numeric Work ID is the immutable document ID. Search is unchanged. Full design reconciliation is a separate maintenance command under [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md).

The management-only Regenerate modal has one awaited Run and no mode choice. It stays busy through source/Build completion and collection refresh, then displays Updated, Created and Deleted counts with Close. Failures report the Work/step and committed effects. Ordinary Build resolves bound Work content from supplied Working JSON. Referring documents remain explicit Rebuild work; no automatic retry or workspace-wide rebuild is added.

Single-document index drag/drop owns placement through the management placement planner. In Working, Root selects the ordinary collection, an ordinary document selects a parent, and an exact configured collection host selects its flat collection. The server validates placement against current source. Source's Title/Summary editor has no Parent or Location control and cannot move or reparent a document; existing stored placement values remain intact. Pre-publish remains read-only.

For ordinary reparenting, `POST /docs/move` commits the source change, completes the affected document rebuild, and returns the exact target and canonical `doc_id`/`parent_id` record. The browser updates its document and ordered-child models, reinserts the existing mounted subtree, updates affected parent chrome and ancestry, and invalidates the moved payload plus search and recent caches. This path preserves the route and displayed document without rereading `index-tree` or redrawing the complete sidebar. Search rebuild remains separately requested.

A collection change completes source relocation, affected authored-reference rewrites and source/destination document rebuilds in one awaited operation. The response carries the committed `{stage, collection, doc_id}`, destination-owned metadata fields and its exact viewer URL. The placement client reloads through that destination, including the host/subdoc selection for a collection document. An ignored placement is not projected as a move. Revision conflicts identify the exact changed document, including a referring document, and the attempted operation. Validation, write and rebuild failures remain visible; a failure after source changes explicitly reports incomplete results rather than returning success.

If the committed record cannot be reconciled with the current browser model, the management action reports the projection failure and performs one authoritative index reload. This is explicit recovery after a server commit, not optimistic rollback or a compatibility success path.

## Source Editing And Save

**Edit document** opens the complete Markdown buffer for the displayed exact Working target. A collection detail has its own target, and a displayed list uses its host. Source hides the current rendered mount and closes pinned Info. Cancel or decline a dirty navigation to keep the draft. [Source controls](Source_Organisation.md#source-controls)

`GET /docs/source` supplies the buffer and file-picker limits. Source Save validates the complete draft, adopts the selected media and awaits exact generation and fresh display. A post-save generation or display error reports the completed phase and preserves saved source. The fresh read updates the current browser entry and retains reading position. [Source editor endpoints](Source_Editing.md) · [Media and Save](Media_And_Asset_Handling.md#add-a-new-image-or-download)

## Explicit Working Refresh

The filesystem watcher and browser refresh timer are retired. Application completion owns required view updates through the existing route workflow, workspace provider and list owners. There is no server push, recurring freshness read or cross-tab synchronization. Initial loads, explicit reloads, ordinary navigation and browser Back/Forward retain their existing owners.

| Completed action | Owned view update |
| --- | --- |
| Source Save | Project the complete committed metadata to Index and retained lists, then read and display the fresh exact generated document. |
| Draft/ready | Project the changed front-matter record to the menu and retained lists; do not reload the document body. |
| Create | Project the committed record, refresh the ordinary Index where required, and open the exact created target in Source through the existing ordinary or collection owner. |
| Edit doc → Rebuild | Reload ordinary Index metadata where applicable, read exact current management metadata for retained lists, and refresh the displayed generated payload. |
| Refresh Search and Recent | Await the discovery build, then refresh the Search and Recent caches and any active discovery view. |
| Import | Forward confirmed committed records, including individually completed files before later cancellation/failure. Refresh an overwritten displayed target, reload the ordinary Index at terminal completion, and refresh the current named collection report for a completed collection import. Open the selected single-file result through the existing route owner. |
| Delete / Position / Sort Children A–Z | Commit confirmed deletions and reparenting metadata to retained list owners and reload the ordinary Index after an ordinary mutation, including before returning to a caller after deleting the displayed document. Same-parent Position and sorting change navigation only. Keep a surviving main-pane target in place. |
| Catalogue Regenerate | Await the owning collection's explicit manifest/report refresh. |
| Publish | Await the selected publication result before releasing management busy state. Search and Recent view updates belong to the separate discovery refresh. |

`docs-viewer-route-workflow.js` owns the shared `refreshDocument` completion command. It preserves Source's existing leave/discard confirmation; only the Source Save service adapter marks its already persisted source as safe to leave directly. It reads the exact ordinary or named-collection by-ID payload from the generated-data owner, verifies the request, displayed target, current route and mode, then refreshes the retained mount and current browser entry without adding history or resetting reading position. Retained payloads do not satisfy this fresh-result read. Read, display and retained-list failures remain visible after a completed write/build; recovery is explicit reload or Rebuild, without background retry.

The [Info Panel](Info_Panel.md) is an intentional detached capture of a pinned document, independent of the main pane and its updates. Navigation or content refresh does not retarget or reopen it. Source entry closes it. Draft changes affect operational metadata absent from the capture. These owners require no polling-based Info update.

For a deliberate external Markdown change, rebuild the exact document and refresh/reopen the relevant view. A targeted CLI build changes generated files without notifying existing browser models. Reload the browser to start a fresh view after a CLI build or a change in another tab. Use the explicit full Working rebuild command for persistent-media edits. [External edits and rebuilds](Source_Organisation.md#explicit-external-edit-and-media-rebuilds)

## Review Execution Path

```text
review shell --> review entrypoint --> returned-package provider
                                           |
                                           v
                                  gated review endpoints
                                           |
                                           v
                               retained derived package preview
                                           |
                                           +--> identity-only handoff to Docs Import
```

Review reuses the reader without becoming a configured Docs Viewer scope. It can list and render validated package previews, inspect assets, and link to canonical counterparts. It cannot edit canonical source, apply an import, or reach general management endpoints.

[Docs Review](Docs_Review.md) owns the package workflow and its Data Sharing boundary.

## Why The Layers Exist

### Separate Entrypoints

Entrypoints enforce the delivery boundary. Public routes do not download management code and then rely on runtime checks to hide it. Manage and review can contribute their own shell composition, providers, views, and controls without widening the public import graph.

### Route Features And Policy

Route config chooses from known features and may narrow known views, modes, or controls. It lets route surfaces reuse the same reader without inventing executable behaviour in JSON.

### Code Registries

Views, modes, controls, actions, report loaders, and import formats are code-owned because they connect to executable lifecycle, rendering, parsing, or mutation behaviour. Entrypoints contribute the definitions appropriate to their app kind.

UI copy lives directly in the calling renderer, action, controller or modal, with template literals for dynamic messages. Browser configuration supplies viewer settings and data addresses; it has no text registry or keyed text lookup. The 2026-10-11 cleanup retires the import text table and formatter, management/settings/modal copy tables and the unused text accessor/formatter exposed by the shared config controller and management context. Startup is labelled for viewer-settings loading. The three affected public shared modules use the existing tracked projection; import and management modules remain local-only. [Studio Runtime](../deliveries/Studio_And_Catalogue_Ownership_Review.md#studio-retirement-evidence) records the joint cleanup and its focused evidence.

### Named Service Surfaces

Generated reads, source reads/writes, and management workflows have separate browser service contexts. Local generated reads do not logically depend on management UI, and source authority is not inferred from the current route name.

### Live Capabilities And Server Validation

Capabilities describe what the current service can do after environment flags, configured scopes, external workspaces, and filesystem conditions are known. Endpoints remain the final enforcement boundary.

[Configuration And Extension Points](Configuration_And_Extension_Points.md) maps the config, code registry, and capability gates in detail.

## Extension Method

### Links Presentation

[Related Links](Related_Links.md) owns the author-inserted `[[links|related links]]` directive. Its plain heading, sorted incoming/outgoing list and decorative collection icons are embedded in `content_html` at build time. Rendering uses the normal document mount, with no relationship request or additional manifest read. Generated anchors carry `data-docs-related-link` so authored-link collection omits them. Documents Linking Here and its separate backlinks loader, payload, browser setting and API are retired.

The per-document Links control, adapter, hosted presentation and `/docs/links` generated-read endpoint are removed. The separate local workspace Links diagnostic report remains. Content Detail continues to host Table, Image, Media and Report presentations. [Builder](Builder.md) owns persisted-record expansion and existing relationship maintenance; [Source editing](Source_Editing.md#directives) owns insertion.

### Choosing An Extension Owner

Add a feature at the narrowest layer that owns the difference:

1. Keep it in scope data when only content, routes, generated locations, or display policy vary.
2. Contribute a route-specific view, control, provider, or workflow when behaviour differs but the reader model remains the same.
3. Extract a public-safe shared primitive only when it carries no local authority or manage-owned dependency.
4. Promote to public through an explicit entrypoint, asset, data, config, and test decision.
5. Fork the runtime only when navigation, rendering, URL state, or loading strategy becomes a competing application model rather than a variation of the shared reader.

Views should attach through the code registry, explicit hosted-view context, and panel lifecycle rather than reading broad runtime state or modifying route-shell markup. [Panel Hosts](Panel_Hosts_And_Control_Surfaces.md) owns that focused lifecycle.

## Weak Spots

- Availability is intentionally distributed across entrypoint imports, route features, code registration, live capabilities, and endpoint validation. Debugging requires following that order.
- A path under `shared/` is not proof that code is public-safe. Import-graph tests remain necessary.
- The local service modifies route service URLs and management access when serving the checked-in registry. Reading the JSON file alone does not show the live route record.
- Generated, source, and management services are separate browser contracts, but the current local service still enables source and management together under the main management flag.
- Public promotion has no plugin mechanism. Each promotion needs a review of assets, data, access and the verification appropriate to the change.

These are useful constraints to expose, not invitations to add another coordination layer.

## Code And Evidence

- public entrypoint: `docs-viewer/runtime/js/public/docs-viewer-public.js`
- manage and review entrypoints: `docs-viewer/runtime/js/management/docs-viewer-manage.js` and `docs-viewer/runtime/js/review/docs-viewer-review.js`
- shared boot and runtime: `docs-viewer/runtime/js/shared/`
- local service and capability projection: `docs-viewer/services/docs_viewer_service.py` and `docs-viewer/services/docs_management_capabilities_service.py`
- committed ordering: `docs-viewer/services/docs_navigation_order.py`, `docs-viewer/services/docs_management_position.py` and `docs-viewer/runtime/js/management/docs-viewer-management-actions.js`

Local Manage and Review serve canonical browser code from `docs-viewer/`. Public preview and GitHub Pages serve the explicit tracked subset projected under `site/docs-viewer/`; that deploy tree is not a fallback source for local runtime loading.

The document index shortcut and tab-scoped collection report state have focused source/diff review, changed-file JavaScript lint and public projection/site validation. No behavior tests, automated browser checks or live document writes were exercised for that change. Report restoration through the shortcut, Index host and native history, keyboard behavior and narrow public layout remain manual review; static checks do not establish those presentation and interaction outcomes.

Use [Runtime Module Ownership](Runtime_Module_Ownership.md) when an implementation change needs the current grouped module map. Use [Generated Data Contracts](Generated_Data_Contracts.md) for payload and read authority.
