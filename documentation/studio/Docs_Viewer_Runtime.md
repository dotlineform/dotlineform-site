---
draft: false
doc_id: d-20260331-000000-c313fd
title: Runtime
added_date: "2026-03-31 00:00:00"
last_updated: "2026-10-07 11:49:40"
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
- which server endpoint finally authorizes an operation

## Three Surfaces

| surface | browser composition | data and service authority |
| --- | --- | --- |
| Public `/analysis/` | Static shell, public entrypoint, public-safe shared reader, and explicitly promoted public features. | Published static config and generated payloads. No local source or management services. |
| Manage `/docs/` | Service shell, manage entrypoint, shared reader, and manage-owned views, controls, reports, imports, and scope workflows. | Independent generated-data, source, and management service surfaces, constrained by live capabilities and server validation. |
| Review `/docs-review/` | Review shell, shared reader, returned-package provider, and package toolbar/workflow. | Independently gated reads over validated package previews. No canonical source write or general management authority. |

Public and Manage share the top-row renderer and theme control. The `dotlineform` home link opens the configured default document at `/analysis/` publicly or `/docs/` in Manage. Document and management controls occupy the shared top row; Recent and Search occupy the first row inside the Index panel. The public footer remains part of the site shell, and the shared toolbar has no breadcrumb trail. Theme changes retain the public themed-diagram event and the local inline-Mermaid callback.

The shared Docs Viewer stylesheet owns the page inset and reader-control sizing across the public and local shells. The archive header is the spacing reference: 18px top padding and 2rem controls in the top row and Index header. Modal controls retain their own dimensions.

The shared [focus-mode owner](../../docs-viewer/runtime/js/shared/docs-viewer-focus-mode.js) controls visible focus indicators across Public, Manage and Review, including report rows, Media View and management modals. Initial and pointer-driven focus stays visually quiet. Tab, arrow, Home/End and Page Up/Down navigation enables keyboard indicators until the next pointer press; typing alone does not enable them. Document capture listeners set the mode before controls move focus. Actual focus, modal trapping and restoration after Back or modal closing retain their existing owners. Search halos and Import's containing-table outline follow the same mode; selection, ordinary borders and drag/drop indicators remain independent.

[Toolbar Icons](Toolbar_Icons.md) owns the reusable mask helper, independent artwork-size and button-size tokens, button states, artwork classes and extension method. The selected reader, management, source-editor, content-detail and report toolbars, collection list/detail controls, toolbar menus, index header and Info close control use this foundation; the Shared Icons mapping records their artwork and visual-review status.

Manage shows its Actions controls in the top row. The Index tree context menu owns Copy Link, Open, Open in VS Code, New Sibling, New Child, Position, Export, Prepare package and Delete. Every menu action captures the invoked ordinary tree node independently of the main pane, including a collection host while its detail document is displayed. Export, Prepare package and Delete use that node and its complete subtree, including collapsed descendants; package profiles and filters still determine the effective package set. Position moves the node with its descendants. No second-row Index management controls, checkboxes or selection commands remain. Collection Actions shares the top row with the other document and collection actions and retains its own checked-row workflow. The public reader has no management controls.

Right-click or Shift+F10/the context-menu key opens the menu for its row. A temporary outline identifies the target without changing the displayed-document marker; arrow keys, Home/End, Escape and Tab provide keyboard navigation and dismissal. Existing capability and busy rules govern availability. Position and Delete remain disabled during source editing. The operation modals identify their target by title and ID and describe descendant scope; New Sibling/Child also identify their relative document. Opening or dismissing the menu does not load a document. Position and deletion of another subtree refresh the Index while preserving the surviving main-pane document, collection detail, route and reading position. Delete navigates to a surviving document only when the displayed node is removed. Modal focus restoration resolves the current target row after a tree refresh, or the displayed row when the target is gone or hidden.

“Shared” does not mean public. A module is part of the public surface only when the public entrypoint imports it or a public-safe lazy path can reach it.

## Document Action Context And Toolbar Placement

The [document controller](../../docs-viewer/runtime/js/shared/docs-viewer-document-controller.js) owns the exact displayed target and record for ordinary and named-collection documents. The [collection list](../../docs-viewer/runtime/js/shared/docs-collection-report.js) contributes its host document and containing collection context while that list is displayed; it owns no document detail reader. Named documents obtain their supported Manage actions and private metadata through the existing collection contribution owner, independently of a manifest or calling report. Loading, invalid and error states supply no action target. A retained hidden report cannot replace the active document's context.

The [management control resolver](../../docs-viewer/runtime/js/management/docs-viewer-management-report-controls.js) and [collection action composition](../../docs-viewer/runtime/js/management/docs-viewer-management-collection-composition.js) consume the common reader's resolved targets. Edit, Open in VS Code, Draft/Ready and named-document actions use the displayed document; New and Regenerate use the containing collection; checked-row actions use the explicit collection selection. Source keeps its captured target, including when opening that source in VS Code. Management operations retain capability, busy, service and committed-result checks. Lists retain filtering, sorting, selection and reconciliation.

The ordinary-document Draft/Ready button stays visible but disabled when the document or an ancestor is listed in `unpublishable.json`. Its tooltip and accessible label read “Excluded from Publish by unpublishable.json”; its icon still reflects the saved draft value. Collection report hosts use their ordinary-document exclusion state while displaying the collection list. The local `/docs/index-tree` response supplies an explicit `publication_ignored` boolean for each ordinary document, derived from the current ignore list and canonical `index-order.json` through the shared publication-exclusion reader. This state exists only in the service response; generated files, public payloads and authored draft values are unchanged. The existing Working index refresh observes ignore-list and hierarchy edits, and the Draft/Ready click handler requires a current unexcluded record. This control describes ignore policy only; Publish remains the owner of complete eligibility, including draft subtrees and collection-host exclusions.

The [main toolbar renderer](../../docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js) presents document and collection actions in the existing page-wide top row beside management controls. The general Back control uses browser history and is visible only with a known caller in this page session. Content Detail uses the same history owner. Existing spacing, narrow-header wrapping and document-width placement remain with the shared renderer and styles.

Collection search and filters remain beside the list. Sort and row-selection controls are Manage-only; public lists retain their default order: recently updated for Catalogue and title A–Z for the other collections. Manage's sort button follows the collection search field with the standard report toolbar gap (`0.55rem`). There is no duplicate detail action row. Source and Content Detail hide the collection controls while retaining their mounted nodes; generated detail refresh updates content and context without rebuilding those controls. [Shared layout](../../docs-viewer/static/css/docs-viewer.css), [report styling](../../docs-viewer/static/css/docs-viewer-reports.css) and [Manage styling](../../docs-viewer/static/css/docs-viewer-manage.css) own these presentation rules.

The shared [Docs Viewer palette](../../docs-viewer/static/css/docs-viewer-theme.css) owns two neutral UI roles across Public, Manage and Review. Panel borders and report dividers use `--docs-viewer-theme-border` through `--docs-viewer-border` (`#e6e6e6` in light mode; `#2b2b30` in dark mode). Search icons, placeholder text, the enabled inactive Index Recent button and enabled Manage collection sort icons use `--docs-viewer-theme-text-placeholder` (`#8c8c8c` in light mode; `#9b9ba3` in dark mode); shared search fields consume it through `--shared-search-muted`. Normal text, selected controls, disabled states and focus indicators retain their own semantic roles. Studio defines its matching search-grey values in its separate palette.

## Retained Index Views

The shared view registry registers Index tree, Search results and Recent results in the Index panel. Panel layout alone selects their visibility. The Index shell mounts controls, the retained tree and one results area; the main shell owns only document content and its toolbar. Review retains its existing top-row package-control surface, with Search and Recent gated by its route features.

The sidebar owns an explicit tree selection independently of the displayed document. Clicking a tree row selects it and deliberately reveals its ancestors; double-click Source uses the clicked row. Initial default or direct ordinary-document loading selects its matching visible Index row once; direct named-document loading selects no collection host. Later document links from reports, body content, Related links, Search or Recent neither select a collection host nor move tree expansion or scroll. Branch toggles retain their mounted child lists. Initial loading, authoritative Index replacement and actual hierarchy changes retain their existing rendering owners.

Visible navigation scrolls the current row only when needed; hidden tracking neither scrolls results nor moves focus. Revealing the tree scrolls its already current selection without fetching the Index, rebuilding nodes or reloading a document. Search and Recent keep query/ranking/paging and mounted results independent of document navigation and Info capture. [Docs Viewer Search](Docs_Viewer_Search.md#index-results-and-navigation) owns list acquisition, compact rows, history and clearing/toggling behavior.

Back to a retained caller restores the document/report and its reading position while preserving the Index panel's current tree/Search/Recent view, query, paging, tree selection/expansion and list scroll. The panel is not part of a document restoration record. Existing result highlighting follows the restored exact target without rerendering rows or moving the list; focus restoration ignores invocation controls that are now hidden. The restored document URL uses the panel's current query. Initial/reloaded routes still apply their URL query once.

## Exact Document Navigation And Return

The [route workflow](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js) opens ordinary `?doc=<id>` and named `?collection=<owner>&doc=<id>` targets through one provider and renderer. Collection configuration selects by-ID storage; browser configuration provides an explicit ordinary document URL template. No full collection manifest or Index record is a document-loading prerequisite. Host-plus-`subdoc`, scope and stage routes are rejected without aliases. Copy Link identifies only the document. Review preserves the selected package and its membership checks; package-local source identities remain supported within that authority.

The [navigation owner](../../docs-viewer/runtime/js/shared/docs-viewer-navigation.js) retains only the current document/report and one immediate caller, identified by browser entries. Each entry carries a page-session ID, entry ID, browser position and caller ID. Small restoration records hold document/report controls, reading position and focus; document roots and report models stay with their owners, while Index panel state remains independent. Opening another document drops the older caller. Back restores the immediate caller, consumes that return context and releases the document being left; toolbar Back is then hidden. There is no retained Forward destination, `from` parameter, independent ordered return stack, persistent cache or expiry policy. Direct loads, new tabs and reloads begin without a caller.

Document openings push browser entries. Same-document heading changes and filter/sort/group/page/Search/Recent adjustments update the current entry. Repeated list → document → Back cycles reuse the same list model and mount without loading an unchanged manifest or rerunning Projects. List → Doc A → Doc B releases the list; Back returns to Doc A with no earlier toolbar Back. Opening that discarded list through Index loads it again. Browser-native Back/Forward outside the retained pair reloads the exact URL and starts a fresh page session. Changed metadata can move or remove an invocation row; focus resolves its current link when possible. Missing or deleted targets display an error without substituting a collection host. Deleting the displayed document returns to its immediate caller, or uses the existing surviving ordinary-root/empty destination when none exists.

Media, Table, Diagram and expanded Report views are temporary Content Detail presentations inside the current document. They add no browser entry or document slot and preserve its immediate caller. Their Back releases the presentation, returns to that document and restores its position and invocation focus. Following a document link from Content Detail closes the presentation and records the underlying document as caller. Content Detail marks the active `.docsViewer__documentMount` with `data-docs-content-detail-active`; shared CSS hides its rendered children while showing its `data-docs-content-detail-view` presentation. Returning removes that marker and releases the presentation root. There is no suspended presentation history.

Discarding or refreshing a document releases its report subscriptions, collection-list lifecycle and content adapters; discarding also removes its mount and cached payload. Report subscriptions share the document mount's lifetime, including asynchronously mounted reports. Retained caller lists continue receiving committed updates. Search/Recent and Index retain their separately owned browsing data; the two-view bound concerns document/report mounts rather than those application panels.

Source confirms dirty navigation before the view changes. Cancelling browser traversal returns to the active browser position with its buffer intact, without pushing a duplicate entry. Source Save completes at canonical persistence; generated rendering remains with the watcher and active-document refresh.

Committed Save, Assign Subject, readiness, Create, confirmed Delete and Import records pass through the workspace provider to retained list owners. Full Source Save summaries come from the validated in-memory metadata, including complete supported list fields, date-only list precision and private Subject/customisation fields. A changed Assign Subject response supplies the same complete record from its validated updated metadata; the existing document action completion forwards it to retained lists before returning. Omitted metadata clears previous values. Collection lists, Selected Documents, Index and retained Search/Recent projections update their own data; Projects and Works reproject title and Subject placement against retained folder, Work and Series inputs. Docs Media and workspace Links update known document labels and remove confirmed deletions without rediscovering references. Confirmed partial Import items are forwarded individually; rolled-back or uncommitted items are excluded. Projection failures are reported separately from successful source persistence. The saved Search index is unchanged; metadata-only in-session Search projection does not refresh body postings or expand Search membership.

On 2026-10-03 the user confirmed the original general navigation, Source editor opening, title changes and list updates, then reopened the delivery to approve the two-view follow-on and accepted its closeout. Further testing continues during normal work; individual two-view scenarios and detailed failure/cancellation, Delete/Import and public/Review cases were not separately confirmed. Acceptance and static diagnostics do not establish those individual interactions. Public runtime and the newly prepared document/configuration snapshot must be released together through an explicitly authorized Publish; runtime projection alone does not migrate existing public data.

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

Public capabilities are promoted deliberately. A public report, view, or control needs a public-safe loader and data source plus route/config and import-graph coverage; it is not made public by hiding its management controls.

The executable public boundary is protected by `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py`, which walks the public entrypoint's static import graph and rejects manage-, review-, import-, source-editor-, and local-report-owned modules.

## Local HTTP Caching

The Docs Viewer service uses browser-private HTTP caching for normal browsing. `docs_http_cache.py` owns cache lifetimes and ETag comparison; the HTTP handlers select the policy after their existing route, capability and path checks. There is no process payload cache or workspace-wide hashing step.

| Response | Policy |
| --- | --- |
| App JavaScript, CSS, icons and fonts | `private, max-age=86400`: reuse for one day. |
| Catalogue primary images carrying a positive `v` media version | `private, max-age=31536000, immutable`: reuse that versioned URL for one year. |
| Unversioned shared media, document/collection/report data, HTML shells and configuration | `private, no-cache`: store the response and revalidate before reuse. |
| Source editing, capabilities, management operations and JSON errors | `no-store`: read current state directly. |

Requested-file responses use weak validators based on nanosecond modification/change times and size. Unchanged conditional reads return `304` without opening or transferring the file. Transformed HTML and JSON API responses use an ETag of their actual response bytes. They still perform the owning read and validation before comparison, so missing files and failed requests remain errors rather than cached success. API cache responses vary by Origin and retain their allowed CORS headers on `304`.

Generated-data, collection refresh, Catalogue presentation and generated-report clients use browser revalidation rather than `no-store`. The browser handles `304` and supplies the cached body to the existing renderer. Working's independent two-second refresh remains in place. Save/watcher output and Prepare Preview changes produce current responses through their existing workflows; document editing requires no manual cache clearing. Source/management clients and Studio canonical-data reports retain their own freshness boundaries. Docs Review package endpoints retain their existing policy.

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

Route intent is not authority. `app_kind: manage`, `management_ui: true`, a visible action, or a non-empty service URL cannot authorize a write. The owning endpoint still validates the active scope, operation, paths, payload, and filesystem conditions.

Named-collection New uses the configured Working destination without a directory-existence preflight or listing, reading or validating existing source documents. It retains create-request checks, allocates an immutable ID and uses an atomic create-only write that refuses an existing destination. The existing write/rebuild owner builds the new document and initializes its Links file before the browser selects the exact committed target and opens Source. Shared generated-manifest checks belong to the builder. Ordinary hierarchical document creation retains its existing source inventory and parent validation.

Working Catalogue exposes Regenerate as its creation/maintenance action and omits independent New and Delete. `docs_catalogue_work_record.py` generates a bound image-token body from generated Studio Work data; `docs_catalogue_regeneration.py` owns one document-to-Work inventory per requested action, exact `work_id` matching and the awaited batch write/build. `POST /docs/catalogue/regenerate` accepts Pending updates or Full reconciliation, without a preview/apply receipt. Shared creation supplies new IDs, timestamps and create-only writes; existing documents retain their identity, added date, draft state and Links except where deleted documents require cleanup. Direct Catalogue New/Delete requests are rejected. Only new document IDs are selected for Links initialization. Search is unchanged.

The management-only Regenerate workflow and modal own mode selection, one awaited Run, result/error display and the owning collection refresh. Management keeps background actions gated while the modal is open; its controls become busy only during Run and the awaited collection refresh. The Regenerate modal suppresses the page-wide busy cursor within its own surface while open. It shows Updated, Created and Deleted counts on separate lines and one Close button; successful completion is not repeated in the viewer status. A failed write/build reports committed source operations and its incomplete outcome; it does not retry creation. The caller's committed-write receipt keeps those changes under the existing watcher suppression so a failed batch is not rebuilt automatically. Ordinary Build resolves bound Work text from generated JSON; Regenerate updates Catalogue source titles and tokens as needed, then builds the selected documents. [Catalogue Work Records](Sub_Scope_Index_Architecture.md#catalogue-work-records) owns the generation definition and collection reader behavior.

Single-document index drag/drop owns placement through the management placement planner. In Working, Root selects the ordinary collection, an ordinary document selects a parent, and an exact configured collection host selects its flat collection. The server validates placement against current source. Source's Title/Summary editor has no Parent or Location control and cannot move or reparent a document; existing stored placement values remain intact. Pre-publish remains read-only.

For ordinary reparenting, `POST /docs/move` commits the source change, completes the affected document rebuild, and returns the exact target and canonical `doc_id`/`parent_id` record. The browser updates its document and ordered-child models, reinserts the existing mounted subtree, updates affected parent chrome and ancestry, and invalidates the moved payload plus search and recent caches. This path preserves the route and displayed document without rereading `index-tree` or redrawing the complete sidebar. Search rebuild remains separately requested.

A collection change completes source relocation, affected authored-reference rewrites and source/destination document rebuilds in one awaited operation. The response carries the committed `{stage, collection, doc_id}`, destination-owned metadata fields and its exact viewer URL. The placement client reloads through that destination, including the host/subdoc selection for a collection document. An ignored placement is not projected as a move. Revision conflicts identify the exact changed document, including a referring document, and the attempted operation. Validation, write and rebuild failures remain visible; a failure after source changes explicitly reports incomplete results rather than returning success.

If the committed record cannot be reconciled with the current browser model, the management action reports the projection failure and performs one authoritative index reload. This is explicit recovery after a server commit, not optimistic rollback or a compatibility success path.

## Source Editing And Save

**Edit document** opens one Source session and its metadata panel for the exact Working target. An ordinary view targets its document, a collection list targets its report host, and a validated collection detail targets only that detail. Invalid or loading details do not fall back to the host. Separate Source and Subdoc Source buttons are removed; Open in VS Code remains separate.

`GET /docs/source` supplies the full loaded front matter and body. The session owns Title/Summary, typed Markdown and raw pending semantic-token occurrence fields, including invalid values. Panel mounts only project that state. Switching context or closing the panel preserves the draft, and leaving Source asks for one discard decision covering all edits. The [Info Panel](Info_Panel.md) owner describes the context table.

The single `POST /docs/source/save` validates the complete draft and performs one atomic source write, preserving non-edited metadata and exact document/collection identity. It has no disk-revision or external-merge workflow. Save completes at source persistence; it does not run or await document/Links generation, suppress the watcher, rebuild Search or await viewer refresh. Source-write failure retains the draft; later generated-output failure belongs to its own owner. [Source Editor Endpoints](Source_Editor_Endpoints.md) defines the request and response.

Source Save uses the viewer's shared busy state while the source request completes. Save and management Build show a waiting cursor throughout the local viewer, including links, editor text and disabled controls; the cursor clears on success or failure. Modals that explicitly suppress the page busy cursor retain their ordinary control cursors.

Source mounts beside the existing rendered content and hides that content with management-only CSS. It does not detach a collection report and trigger its unmount observer. Successful Save removes only the editor and restores rendered display immediately, with read-only Info when the panel is open. The existing rendering can briefly lag behind source until independent generation and refresh complete.

## Automatic Working Refresh

The watcher independently observes changed canonical source and performs its existing targeted document projections and affected Links maintenance. The browser consumes generated output separately through `docs-viewer-route-workflow.js` and its existing two-second Working poll. Polling runs only while the page is visible, management is idle and Source is inactive.

Each poll reads the index and the exact displayed generated payload independently, so a token-only edit can refresh even when the parent index is unchanged. Ordinary payloads use the collection provider; a validated collection detail uses its own generated by-ID reader in `docs-collection-report.js`. Unchanged payloads are left mounted. Before applying a response, the reader verifies the captured route, request, displayed document and rendered mode; collection reads also retain their exact detail identity. Late reads cannot replace another target or a reopened Source session.

Changed content updates the rendered body and open Info while retaining route, selection and reading position. A collection detail's action mount is created once when opening its detail shell and presented in the shared top row. Content refresh does not create, replace or remove that mount. Refresh errors have their own status and cannot reverse or repeat a successful Source Save. Pre-publish, Published and public routes remain read-only and do not join this Working authoring poll.

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

### Named Service Surfaces

Generated reads, source reads/writes, and management workflows have separate browser service contexts. Local generated reads do not logically depend on management UI, and source authority is not inferred from the current route name.

### Live Capabilities And Server Validation

Capabilities describe what the current service can do after environment flags, configured scopes, external workspaces, and filesystem conditions are known. Endpoints remain the final enforcement boundary.

[Configuration And Extension Points](Configuration_And_Extension_Points.md) maps the config, code registry, and capability gates in detail.

## Extension Method

### Links Presentation

[Related Links](Related_Links.md) owns the author-inserted `[[links|related links]]` directive. Its plain heading, sorted incoming/outgoing list and decorative collection icons are embedded in `content_html` at build time. Rendering uses the normal document mount, with no relationship request or additional manifest read. Generated anchors carry `data-docs-related-link` so authored-link collection omits them. Documents Linking Here and its separate backlinks loader, payload, browser setting and API are retired.

The per-document Links control, adapter, hosted presentation and `/docs/links` generated-read endpoint are removed. The separate local workspace Links diagnostic report remains. Content Detail continues to host Table, Diagram, Media and Report presentations. [Builder](Builder.md) owns persisted-record expansion and existing relationship maintenance; [Source Editor Scripts](Source_Editor_Scripts.md#directives) owns insertion.

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
- Public promotion has no plugin mechanism. Each promotion still needs a deliberate asset, data, access, and test review.

These are useful constraints to expose, not invitations to add another coordination layer.

## Code And Evidence

- public entrypoint: `docs-viewer/runtime/js/public/docs-viewer-public.js`
- manage and review entrypoints: `docs-viewer/runtime/js/management/docs-viewer-manage.js` and `docs-viewer/runtime/js/review/docs-viewer-review.js`
- shared boot and runtime: `docs-viewer/runtime/js/shared/`
- local service and capability projection: `docs-viewer/services/docs_viewer_service.py` and `docs-viewer/services/docs_management_capabilities_service.py`
- committed move projection: `docs-viewer/runtime/js/shared/docs-viewer-tree-move-projection.js` and `docs-viewer/runtime/js/management/docs-viewer-management-actions.js`
- move service evidence: `docs-viewer/tests/python/test_docs_document_move_apply.py`; browser projection is accepted manually
- public import boundary tests: `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py`
- service separation tests: `docs-viewer/tests/python/test_docs_viewer_service_config.py`

Local Manage and Review serve canonical browser code from `docs-viewer/`. Public preview and GitHub Pages serve the explicit tracked subset projected under `site/docs-viewer/`; that deploy tree is not a fallback source for local runtime loading.

The action-context and toolbar changes have focused source/diff review, changed-file JavaScript lint, public projection/site validation and user acceptance of the layout, Back spacing and Sort placement. No behavior tests, automated browser checks or live document writes were exercised for that change. Keyboard behavior, the Back-only public case and narrow public layout have no separately recorded manual run; static checks do not establish those presentation and interaction outcomes.

Use [Runtime Module Ownership](Runtime_Module_Ownership.md) when an implementation change needs the current grouped module map. Use [Generated Data Contracts](Generated_Data_Contracts.md) for payload and read authority.
