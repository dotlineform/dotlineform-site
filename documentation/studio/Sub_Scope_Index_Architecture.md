---
draft: false
doc_id: d-20260728-113139-763354
title: Sub-Scope Index Architecture
added_date: "2026-07-28 11:31:39"
last_updated: "2026-10-20"
summary: Collection-list ownership, exact document identity, standard management controls, retained selection and explicit management adoption.
parent_id: d-20260801-084127-752d7e
---
# Sub-Scope Index Architecture

## Architecture Outcome

`docs_collection` is the generic collection index and default report for a configured named collection. The shared public-safe report owns list browsing. All rows open the common document reader. Manage supplies standard controls and workflows through its explicit contribution without loading management modules on public routes.

The shared report owns read-only list preparation, filtering, sorting, pagination and retained browsing state. Its Manage composition owns indexed document updates, selection and collection actions. [Runtime](Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns exact document rendering, actions and browser-history caller return. Persistence and generation remain owned by validated local services.

## Collection Identity

The browser and services share one normalized collection model:

```text
ordinary collection: {}
named collection:    { collection }

document target:     { doc_id }
                 or { collection, doc_id }

selection target:     collection + checked doc_ids
```

`collection` identifies one explicit configured owner. It is not an arbitrary source path or a caller-selected publishing stage. Configuration and package formats retain their own explicitly defined collection fields.

Raw named-document IDs are unique only inside their owning collection. Every cache key, request, operation log, package metadata record or action handoff crossing the report boundary retains that identity. Ordinary URLs use `?doc=<id>`; named URLs use `?collection=<owner>&doc=<id>`. Report hosts identify browsing and publication eligibility, and never substitute for the displayed document. Retired host-plus-`subdoc` document routes fail without aliases.

## Shared Report Ownership

The shared `docs_collection` report owns:

- validating the configured sub-scope;
- loading the public manifest or supplied local inventory;
- title search, deterministic list ordering, pagination and row rendering;
- exact document links supplied through the configured provider;
- validation of the loaded collection inventory;
- retained list controls and committed-record reconciliation;
- contained unavailable and failure states; and
- isolated filter, list-row, list-toolbar, selection-toolbar and lifecycle contribution positions.

The shared report does not own:

- management capability checks;
- checkbox selection state;
- management action definitions or dispatch;
- preview/apply mutation workflows;
- package preparation;
- public promotion of management data.

The report owns no detail payload read, duplicate document shell or collection-specific Back action. The common reader opens a configured by-ID target directly without loading a list manifest as a prerequisite. Retained report models receive complete committed records and confirmed deletions through the provider; their owners reapply filtering, order, grouping, page bounds and eligible selection in memory. Back restores the caller without a discovery scan or unchanged manifest fetch. An explicit collection refresh retains its owning reload behavior.

An extension host exists only when the caller supplies a contribution.
Public mode therefore receives neither an empty management toolbar nor an
import path to its implementation.

## Standard Collection Behaviour

A configured collection record selects the shared list's title search, standard title/date sorting, normal empty/error states and exact document links. Manage adds draft indicators, supported sort controls, selection and Prepare Package. New uses the main Actions menu. The common exact-document context mounts supported collection actions in Edit, including Copy Link and Delete. Subject assignment and Folder opening belong to Source. Action availability follows the current document/collection policy.

Default title search, including Moments and Concepts, matches the query anywhere in the title, consistently with Context. Both title and query use Unicode NFKC normalization, collapsed whitespace and case-insensitive comparison; `test` therefore matches `1 test`. An empty query retains every document. This filters the loaded collection titles without using the overall Docs Viewer Search index.

The server-only `collection_customisation: {id, settings}` selects one known authoring registration. It owns Subject validation, assignment, import and publication preparation, independently of report composition. Browser configuration and manifests carry no customisation identity or data.

Manage uses one standard adapter for selection, row status and supported actions against exact supplied targets. Collection-specific filter, heading, comparator and selection extension hooks are retired. Subject assignment and Folder opening live in Source, rather than the list or detail contribution. Public routes retain the shared reader without management controls.

## Flat Book Collections

Library is a named collection with `collection_type: book-collection`, host `d-20260809-130120-870cc2` and icon `library`. The optional type is projected into browser configuration and selects shared collection browsing capabilities. It has the standard collection inventory, authored thumbnails, title search, title/recent sorting, selection, Import, Prepare Package and common document reader. It has no book data or tree renderer yet. Its documents participate in site Search and Recent through the explicit `include_in_site_search` policy and retain ordinary non-Catalogue draft exclusion.

The shared report separates search-delay and sort-control capabilities from current pagination state. Context and Catalogue retain paginated browsing and other collections retain their current behavior. Library is paginated publicly; its explicit Manage-only contribution defaults pagination off and supplies a toggle using `dlf-paginate-on.svg` or `dlf-paginate-off.svg` to show the current mode. The existing toolbar mask supplies theme tint and sizing, with both icon mappings owned by the management stylesheet. A toggle clears checked/range selection, exits selection mode and resets the page to the start, keeping query and sort. The tab-scoped report snapshot remembers the chosen pagination mode. Rendering reuses the loaded inventory; the toggle performs no request, source write or generation and adds no search-pending guard. Public composition imports none of the local control or selection implementation.

The collection report supplies its current pagination mode with the match count and page position to the shared pager. The pager alone owns its navigation visibility: controls appear only when pagination is enabled and more than one page exists. Unpaged lists show every matching row and no page controls, including when they exceed the normal 20-document page size.

## Reachability Is Not Ownership

A configured collection, a parent document that loads `docs_collection`, and the registered report module are independent records:

- a sub-scope may exist without any document surfacing it;
- a report module may remain registered without any document loading it; and
- deleting a parent document that loads the report deletes that parent
  document under the ordinary parent hierarchy contract, but does not delete
  the report module, configured sub-scope, or child documents.

No lifecycle or cascade relationship is inferred from a parent document's report block or its `sub_scope` attribute.

## Public And Manage Projections

Public mode supplies compact collection rows:

```json
{"doc_id": "<id>", "title": "<title>", "last_updated": "YYYY-MM-DD"}
```

Manage mode supplies one compact inventory containing:

```json
{
  "doc_id": "<id>",
  "title": "<title>",
  "draft": true,
  "last_updated": "YYYY-MM-DD"
}
```

Working non-Catalogue rows carry the source's boolean `draft`. Catalogue rows omit it and have fixed document eligibility. Works additionally retains optional scalar `subject` metadata; this field does not create a Subject column.

The compact inventory supports collection rendering and the Working recency sort. Generation owns valid dates for Works and Catalogue; the other collections sort undated rows after dated rows, then by title and `doc_id`. The browser consumes these completed facts without another date audit. Full source metadata and body content remain exact-document reads. The report must not issue one full record request per row.

Every collection manifest contains only its `docs` inventory:

```json
{
  "docs": [{"doc_id": "<id>", "title": "<title>", "last_updated": "YYYY-MM-DD", "draft": true}]
}
```

The configured Works server registration supplies Subject validation, source assignment capability and publication preparation. Collection manifest customisation projection, browser descriptors/loaders, custom filters, headings and comparators are retired. Readers use the configured collection and standard title/date sorting directly.

Rows and actions use `doc_id` as identity. Title remains display data; this
feature introduces no title-uniqueness, collision, or deduplication contract.

## Collection List Preparation

The local and public compositions resolve the exact collection once through the active workspace's `collectionsById` map and supply that configured record to the shared report. Manage passes the same record into its contribution loader. The report checks that the supplied owner matches its declared collection and uses its normalized `manifestUrl`; it does not merge route/workspace arrays, rescan configuration or accept a raw `manifest_url` alias. The caller supplies the optional management contribution promise; public composition supplies no management contribution.

The shared [browsing data owner](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) prepares the public manifest as a read-only inventory. Each row carries its literal title and original record, exact navigation URL, normalized search text, title/date keys and selected thumbnail URL. Public preparation creates no edit index, complete/filtered selection-ID arrays, per-row reload revisions or committed-change subscription. The Manage-only [collection list controller](../../docs-viewer/runtime/js/management/docs-viewer-management-collection-list.js) reuses the same presentation preparation and ordering, adding its own document-ID map, selection IDs, reload revisions and mutable inventory. Catalogue retains normalized title ordering with literal-title/ID ties and Work-ID substring search; Context retains numeric-aware title collation; other collections retain folded/literal title ordering. Date-only values compare directly, with undated rows last. The default remains Catalogue recent first and other collections title first, with existing Working sort controls.

The presentation owner lazily caches each title/recent ordering for the current inventory. Search filters that ordered array without another sort or per-row normalization. One current projection is reused when query and ordering are unchanged; page changes reuse its rows. Manage additionally carries the complete filtered ID list. A title change invalidates both orderings and search projection, a date-only change invalidates recent ordering only, and membership changes invalidate both. Other metadata changes keep ordered row references. Manage applies a committed record to one indexed row and its thumbnail; additions append one prepared row, and deletions remove the known row and its pending thumbnail. Existing exact URLs and authored reload nonces survive Manage's explicit manifest rereads for surviving identities. Its full ID array is carried during preparation and membership changes; it is not rediscovered from records on page or checkbox actions.

Authored thumbnails retain precedence outside Catalogue. Context uses an exact five-digit Work subject only when no authored thumbnail is assigned; Folder subjects create no Work-thumbnail choice. Catalogue uses its exact Work document ID. Prepared URLs and the inventory's thumbnail presence are reused during row rendering. Only an actual Work-thumbnail choice reads the configured media policy, once for the retained view. Empty lists and lists with only authored or no thumbnails make no policy request. Initial loading awaits required thumbnail URL preparation after reading the manifest. Public then releases its pending thumbnail array and retains no policy settings for future edits. Manage additionally handles a later committed assignment that first needs policy: labels, membership and placeholder slots render immediately; one pending policy read fills only current queued rows and rerenders only when it completed thumbnail work. Replaced/deleted choices leave its pending set. There is no policy retry or persistent policy cache; existing media-policy and URL-safety owners remain authoritative.

Paged Context/Works and Catalogue lists use eager thumbnail loading in both public and Manage readers. Only the current page's maximum 20 rows create image elements, including after search or a page turn; other pages make no image requests. Asynchronous decoding and reserved 64px dimensions remain, and titles do not wait for image completion. The shared thumbnail helper accepts the caller's loading choice and defaults to lazy loading for unpaged lists, including Moments and Selected Documents. There is no preloading, priority override, image-completion wait or additional policy request. On 2026-10-14 the user confirmed that thumbnail appearance was noticeably better after this change. This is manual confirmation of perceived improvement; browser timings and separate public/Manage variants were not measured or itemised.

Retained disposal is registered before awaiting the contribution or reading the manifest. Only actual disposal ends the list's lifetime; a detached retained list may finish reads or a debounced search and remain ready for Back. Disposed views ignore contribution, manifest, policy and search continuations, release prepared rows/orderings/pending work, and cancel their timer. Manage additionally releases selection IDs and update bookkeeping and ignores disposed refresh/commit continuations. Its controller explicitly connects the saved-document subscription; the document controller owns subscription cleanup, without a DOM-removal observer or second unsubscribe owner. The existing tab snapshot still owns remembered query, sort, page, optional Manage selection and reading position across new mounts; its DOM visibility checks concern coordinate capture/restoration, not report lifetime. JSON-safe browser-state parsing and reconciliation against current inventory remain at that restoration boundary.

The local [Source adapter](../../docs-viewer/runtime/js/management/docs-viewer-management-source-adapter.js) owns document-change listeners and projects each completed Source Save exactly once, including a saved-source partial failure. The workspace provider forwards those capabilities only from an available local Source adapter; public composition has no commit or subscription capability, so the common reader, Search and public reports register no saved-document listeners. Manage alone constructs the mutable list controller and wires its explicit Import/Regenerate refresh; public has no collection-refresh callback. This changes no persistence, generation, route retention, publication or Search rebuilding behavior.

Manage receives complete inventory IDs on refresh and complete filtered IDs for toolbar/page projection, with no record-array copying, ID normalization or deduplication. Membership refreshes alone reconcile the checked set; metadata-only commits retain it. Restoration uses the full inventory, preserving surviving checks outside the current filter. Select all and range selection use the complete filtered result across pages. Each rendered page projects selection after creating its row controls, so new checkboxes receive the current checked/active state. Existing action resolution, fixed collection/checked-ID targets and package workflow boundaries remain unchanged.

The existing selection-rule owner still forms and reconciles its own immutable checked state, including at the browser-snapshot restoration boundary. Its authoritative selection operations do not mutate the prepared ID arrays. This change removes the redundant report/contribution projection passes rather than changing the shared ordinary/collection selection rules.

Build/Import authoring owners establish manifest identity, uniqueness, labels, dates, draft and Subject validity. The shared report therefore omits envelope/schema/row/thumbnail-field audits, raw-record cloning/freezing, title coercion/fallback labels, repeated date parsing and the duplicate management Work-ID adapter. Search normalization remains a display decision. Retained safeguards are HTTP/JSON parsing, exact configured collection/refresh targets, reader navigation identity, configured authored media, established Work-thumbnail URL/policy safety and the existing management/package/clipboard boundaries. No Python service, source, manifest schema, generated payload, publication selection or UI workflow changes are required.

On 2026-10-14, focused JavaScript lint and read-only production preparation consumed the four actual Working manifests with 235 Context, 246 Concepts, 58 Moments and 4,620 Catalogue rows, and their public counterparts with 4, 246, 57 and 4,619 rows. The public/Manage separation repeated preparation through the two production data owners. It called `replace`, selected actual policy settings when required, projected title/recent order and a real first-title query, and constructed exact `/docs/` and `/analysis/` links through the production route owner. Working thumbnails numbered 23, 0, 37 and 4,620; public thumbnails numbered 4, 0, 36 and 4,619. Concepts and Moments required no Work-thumbnail policy. Public instances exposed neither edit methods nor selection-ID inventories and their rows omitted revisions; the public provider exposed only read capabilities. These are real-data composition diagnostics without synthetic records, assertions, test scripts, network requests or workspace writes; they establish neither measured performance nor DOM, committed-change, selection, restoration, failure or disposal behavior. Tests, fixtures, harnesses and profiles remain unchanged and unrun.

The distinct Redundancy And Defensive Behavior Review traced normal, empty, undated, filtered and paged lists; title/date/draft/thumbnail/addition/deletion effects; queued thumbnail replacement/deletion; explicit refresh; immediate/late disposal; remembered restoration; and reused configuration, route, media, controller, selection and contribution helpers. Review preserved trimmed comparison keys independently of literal labels, removed a copied old identity map by carrying it into replacement preparation, retained existing row URLs and constructed Manage inventory IDs during the necessary preparation pass. It separated full restoration IDs from filtered eligibility, moved checkbox projection after every page render, and left pager visibility with its single pager owner. The public/Manage follow-up removed public edit indexes, selection arrays, row revisions, change-event setup and explicit-refresh wiring. Review retained one Source Save projection owner and controller-owned unsubscription; date-only edits keep cached title projections. Manage committed metadata renders immediately while first-needed policy work resolves current pending rows; disposed work cannot trigger a render, and refresh failures remain visible without recovery. Shared selection-state formation/restoration, HTTP/JSON, exact target/configuration, navigation/media and operation-specific action safeguards remain at their existing boundaries. No new domain audit, freshness/concurrency check, alias, fallback, repair, cache beyond the retained view or background refresh was introduced.

Shared/public runtime changes reach the tracked site artifact through the existing explicit projection inventory. The Manage list controller and Source event owner remain local and require no new public inventory entry. No saved manifest, by-ID payload, source, media, Search or publication output is rebuilt. Force reload the local and public-preview readers for manual acceptance; code projection does not deploy or Publish content.

## Row Presentation

Working draft indicators prefix the title text inside the title cell. They are part of the displayed title treatment, not separate columns or canonical `title` data. Their icons remain hidden from assistive technology while the title control's accessible name includes `Draft`.

Checkboxes occupy a dedicated first cell or column before the title. Each checkbox remains a sibling of the title navigation control so selection cannot also navigate or create nested interactive controls. The checkbox cell is contributed only in Working selection mode and is omitted or collapsed otherwise; public rows load no selection module. Catalogue thumbnails appear inside the title navigation control in both Working and public lists. There are no collection-specific column layouts or Subject heading rows.

When Working selection is inactive, the shared management stylesheet hides the outer leading-cell host as well as its checkbox gutter. This prevents an empty grid row from adding space above the thumbnail/title. Every collection row retains equal `0.65rem` top and bottom padding; active selection restores the checkbox column and centers the checkbox beside the thumbnail/title across all local collection reports.

The shared report stylesheet resets collection-row margins to zero in both local and public compositions. The public site's base `li` rule otherwise contributes a bottom margin between rows, making the next row appear to have more space above its thumbnail. Catalogue, Concepts, Context and Moments rows, along with dotlineform's Selected Documents rows, omit bottom borders in both compositions. Row padding remains symmetric, and the tracked public stylesheet receives these rules through `bin/site-code-update`. Visual review remains user-owned.

```text
selection mode:  [checkbox] [optional Draft icon + title]
ordinary Manage:            [optional Draft icon + title]
public:                     [title]
Catalogue:                  [thumbnail + title], with Working selection when active
```

## Manage-Only Contribution

A focused manage-owned adapter supplies the standard collection controls. It owns:

- exact-document actions mounted by the common reader inside Edit after target validation;
- a list toolbar for deterministic sorting, collection actions, and
  selection commands;
- a dedicated sibling checkbox cell before each list-row title;
- collection-local selection projection and event handling;
- capability-aware action state;
- lazy workflow loading; and
- refresh/reconciliation after a committed collection mutation.

The list and common reader pass explicit hosts, records and validated targets to their respective contributions. Management code does not infer targets from a retired route field, scrape private report markup or fall back to the Index selection.

Presentation for these controls belongs in the manage stylesheet. Public CSS
may retain only the shared report layout required for public reading.

The shared list loads the configured manifest and accepts the standard management contribution supplied by its caller. It receives leading, title-prefix, trailing and list hosts plus collection-scoped mount, state, refresh and unmount events. Its action registrar captures the exact collection for both import callbacks; committed records and explicit completion callbacks update retained collection views. The common reader separately supplies exact document actions, metadata and refresh callbacks after by-ID identity validation. Empty hosts are not mounted. Registered actions consume only an explicit collection, checked IDs or validated document target and declare their empty-state and refresh effects. Selection stays with the default owner; no collection customisation selection callbacks remain.

## Selection Lifecycle

Collection checkbox selection belongs to its list owner. Collection Actions owns Export and Prepare package for checked IDs and Import doc/Import docs for the exact collection, including an empty collection with no checks. The Index has explicit row targeting and no checkbox selection; it retains subtree Delete but has no import, Export or Prepare package entry point.

The collection selection owner is keyed by `{ collection }` and owns:

- selection mode;
- checked IDs;
- range anchor;
- Select all, Clear, and Done;
- pruning after inventory refresh or deletion; and
- exit when the report unmounts, the collection changes, or management mode is
  left.

Opening a document retains the mounted caller list, headings, controls and selection. Native browser Back to that immediate caller restores its controls, scroll and surviving invocation focus, then consumes the return context and releases the document being left. Repeating list → document → browser Back reuses that same list. Following another document link releases the older list, including its subscriptions and lifecycle. Collection reports retain a lightweight last-visible controls/position snapshot per tab, independently of those mounts; reopening through the Index host, the document's `list.svg` shortcut or browser history restores it against current inventory. The shortcut's tooltip and accessible label are `index`, and opening it adds a normal browser entry while explicitly selecting its report host in the Index and revealing its ancestors. The active Index view and query stay independent. Native destinations outside the retained pair reload by exact URL. Content Detail stays inside its document and uses no history slot. Committed metadata and deletions update the retained model through its list owner before return; unchanged rows are reused. Direct/new-tab documents offer the configured report shortcut without inventing a browser caller. A missing target shows its exact error without opening its report host. [Runtime](Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns tab storage and restoration details.

Working collection loads do not display transient loading messages in the report layout. The collection search keeps the same top inset from shell mount through list loading, so completing the manifest read does not reposition it. Loading still gates management actions, and failures remain visible.

Only checked IDs are supplied to collection selection actions. The displayed document, focused row and Index selection are never fallback targets.

Select all replaces the checked set with the complete eligible filtered collection result across pages. Clear empties the complete checked set.

Checkboxes remain siblings of row navigation controls. Selecting a document
for an action must not also navigate to its detail.

## Function Adoption

Existing functions adopt sub-scope collections only when their complete
contract can carry the collection identity:

| function | target | stance |
| --- | --- | --- |
| list and detail read | collection/document | shipped baseline |
| source and metadata editing | exact document | shipped baseline |
| detail Delete | exact validated document | shipped |
| New | explicit collection other than Catalogue | shared create-only action |
| Regenerate | Working Catalogue collection | shipped; creates/replaces documents from generated Work data |
| app-level ordinary Import | explicit displayed collection | shipped create-only |
| Prepare Package | checked selection | shipped export-only |
| overall search | collection | deferred; later adoption uses the overall search surface, not a child-specific index |
| app-level returned-package and edited-folder Import | trusted package/collection | shipped through manifest-owned routing |
| scope settings, rename, lifecycle, publish | top-level scope | remain scope-only |

This is a positive adoption model. The presence of `sub_scope` in one resolver
does not make every scope action collection-aware.

## Context Collection Browsing And Working Subjects

The `works` collection host `d-20260801-073826-8865a8` is displayed as **Context**. Its immutable document identity, internal collection ID, paths and `working_works` customisation remain unchanged. It uses the [shared browsing module](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) for 20-row pages, normalized case-insensitive title-fragment search after a 180 ms typing pause, immediate clear, and cached ordered filtering before pagination. Context opens in title A–Z order with the existing numeric-aware collation; a Working-only shared toolbar button switches to document `last_updated` descending, with title and exact document ID ties. Public lists retain their default order. The Subject column and Title/Subject heading sorts were removed on 2026-10-03. Pending search disables sort/page controls. Search/sort resets page 1; detail return preserves query, sort, page and return position. Select all still covers the complete eligible filtered set across pages. Context uses the standard Working title/draft/selection presentation and authored-first, Work-alternative decorative thumbnails described above.

The configured collection display title is `Context`, used by Search/Recent result metadata and the Manage Import destination. Browsing copy uses `documents` for search, paging and empty states. The common reader supplies an `index` shortcut to the configured host; browser history owns document return. Collection lists render and announce no total or filtered counts; loading, empty and error messages remain. The search placeholder is `title`; there is no column-heading row. Browser configuration and Working Search/Recents generation project the configured title; Preview and Site Preview receive snapshot data through their normal lifecycle.

Docs generation owns document membership, titles, dates, readiness and exact subject declarations. Working reads `manage-manifest.json`; Preview/public read `manifest.json`, whose Works rows contain `doc_id`, `title` and date-only `last_updated`. Subject declarations remain in source and authoring metadata without a list column. Complete and targeted builds preserve source timestamps; old-shape saved metadata fails visibly. Snapshot adoption remains owned by Publish, separately from Catalogue Save.

The retired Subject column used a private Catalogue title reader and `reports/works/manifest.json` to display and sort Work/Series subject titles. With its last consumer removed, the reader, metadata generator, Catalogue Refresh step and private report-serving allowance were removed together. Context list loading requires no Catalogue title-file read. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) retains its other generated-reader and freshness responsibilities.

The `working_works` server registration supplies Subject validity, source assignment capability and private manifest projection. Its former browser contribution and Manage customisation loader are retired with the unused Document Info projection. Assign Subject is in Source's Directives menu, offering Folder, Work and None and updating the unsaved buffer. Work selection uses its separately owned generated Catalogue provider; Folder input uses the collection's existing path normaliser and registered authoring-field capability. Open Subject folder follows it, reads the current buffer and enables only for a valid Folder subject. On 2026-10-03 Series was separately retired as a document Subject after all Working declarations were reassigned. Document `series_id` fields and normalized Series subject records fail explicitly, while Studio Series, report columns and Work-derived Series associations remain supported. [Subject Associations](data/subject-associations.md) owns the current field and report boundaries.

Local folder links and Source's Open Subject folder action open silently on success; failures still display an error.

Implementation/static review, initial metadata generation, a targeted no-change preview and direct HTTP serving checks passed on 2026-09-26. The user confirmed review through Site Preview, accepted the final count/placeholder/heading changes, confirmed Studio Save testing and authorized closeout. Current Preview/site manifests include the required timestamps. This establishes user manual acceptance; it does not claim browser automation, measured performance, failure injection or exhaustive mutation/selection/subject-action coverage. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns Save freshness and recovery.

The 2026-10-03 Subject-column removal passed explicit lint for the three changed JavaScript modules and two changed Python modules, site-code projection/check, site validation and whitespace review. The obsolete private Working title file was removed. Tests, browser review, Catalogue Refresh, Build, Publish, commit and push were not run. The legacy [Working-subject collection test](../../docs-viewer/tests/js/docs_viewer_processing_working_collection_contract.mjs) still imports a retired module and asserts the removed Subject helpers/styles; it remains unchanged and unreviewed under the separate test-work policy.

## Catalogue Work Records

Regenerate sits in the shared document toolbar, aligned with the document view's left edge. The top-row layout uses the same document axis when Regenerate is present as it does for the collection Index control and Media View Back.

Working Catalogue's management contribution replaces New with Regenerate and omits independent document Delete. Studio Works editor owns Work creation, metadata and generated JSON. [Regeneration service](../../docs-viewer/services/docs_catalogue_regeneration.py) reads the generated Work index and selected `works/index/<work_id>.json` records through the configured Catalogue output reader. Each Catalogue document uses the exact five-digit Work ID as its one immutable `doc_id`: quoted front matter, `<work_id>.md`, `by-id/<work_id>.json`, manifest membership and direct viewer child identity all agree. Source and manifests have no separate `work_id`, old document-ID alias or mapping file. Regenerate inventories source once and creates, updates, deletes and selects Build targets by that same ID. Updates retain identity, filename, added date and existing Links unless their source relationships change. Ordinary documents, other collections and the ordinary Catalogue report host retain `d-...` IDs; numeric document IDs are valid only in Catalogue context. Direct Catalogue New/Delete management requests are rejected; other collections retain their actions.

Catalogue documents represent Works with generated content and are always publishable at the document level. Their source, management metadata, list manifests and by-ID payloads omit `draft`; creation and Regenerate do not seed it. Their Draft control is omitted, Set Draft is rejected, and source reads for owning writes or Build reject any `draft` field. Build, Publish, Search and Recents use fixed Catalogue eligibility. Publication still depends on the ordinary report host's eligibility. Other document collections retain their required boolean draft fields, controls and defaults.

The collection action supplies the exact Working Catalogue target and report-refresh callback. The modal has one Run and consumes refreshed queued Works without a mode selector. It awaits each required source/document Build, publication-queue merge and updates-entry removal, then refreshes the report. Counts remain Updated, Created and Deleted. Busy and committed-failure handling remain with the existing owners.

Explicit design maintenance reconciles source templates and completes one full Catalogue document build, then queues completed document changes without inventing media transfers. It leaves false-readiness entries unconsumed. Normal Regenerate reads only exact queued sources. Missing or malformed private queues stop operations without empty-state fallback; failed operations retain completed effects and identify the Work/step. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns maintenance commands and queue transitions.

New Catalogue documents receive their normal creation and update timestamps. For an existing document, Regenerate advances `last_updated` only when the Work-derived front-matter title changes. Generated-body/template changes and source-format normalization preserve both `added_date` and `last_updated`, even when Full reconciliation rewrites the Markdown. Build-only work also preserves those source dates. Publish copies the resulting source metadata and does not advance document timestamps. This policy applies to subsequent regeneration; it does not restore dates already advanced by earlier operations.

[Work-record generator](../../docs-viewer/services/docs_catalogue_work_record.py) defines the body in code. New bodies contain one identity-only `[[catalogue:entry:work:<work_id>]]` token, followed by a blank line and the separate `[[links|context]]` directive. Entry has no authoring UI or presentation fields. Its Work H1 and metadata sit alongside the proportional image frame. A combined resource list without a heading contains downloads with file icons and external links with link icons, with one Small-text line of CSS spacing above it. Gallery navigation stays with Media View through the Context document's media links. Related links uses H2 `context` in Catalogue documents. The Work's own token creates no self-relationship; Related links displays recorded document references and creates no graph record by itself. [Related Links](Related_Links.md) owns the rebuild sequence. The front-matter title also comes from the Work title, while the token stores no literal Work-derived text. The document builder resolves the current generated Work title and selected metadata on each Build, in this order:

```text
<year_display>
<medium>
<height × width × optional depth cm>
cat. <work_id>
```

Catalogue Entry omits empty metadata/resources, uses positive physical dimensions and technical intrinsic image dimensions, and keeps storage private. Generated source contains Entry plus `[[links|context]]`. Normal Regenerate updates Work-derived titles and builds selected queued documents; explicit design maintenance replaces templates while preserving dates when titles are unchanged. Referring documents require their own Rebuild. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns rendering.

### Catalogue Collection Browsing

The [collection builder](../../docs-viewer/build/docs_builder/collection.py) projects the current operation's Catalogue list manifest with exactly `doc_id`, `title` and date-only `last_updated` (`YYYY-MM-DD`). It validates the five-digit string `doc_id` and full source timestamp before projecting the date; Catalogue list rows carry no separate `work_id`, generic `subject` object or `added_date`. Targeted Working generation requires that current shape and a valid calendar date only in the saved management manifest, otherwise it fails with a complete Catalogue Build instruction. Working builds and reads only `manage-manifest.json`; temporary publication builds produce `manifest.json` for Preview/public readers. Both projections use the same day-level update order and `doc_id` for Work-ID search and thumbnails. Updates on the same day tie by title, then document ID. Full `last_updated` and `added_date` timestamps remain in source and by-ID payloads for document metadata. All other collections also use date-only update values and omit `added_date` from their reader/management manifests while retaining their own subject and readiness fields. Catalogue remains excluded from site Search and Recents by its configured inclusion setting. [Generated Data Contracts](Generated_Data_Contracts.md#collection-manifest-ownership) owns manifest lifecycle and the shared date projection rule.

Catalogue by-ID document payloads omit both `subject`, including the null projection that the shared document writer normally emits for an absent subject, and `draft`. This applies to Working and Preview Build and therefore to published Catalogue documents. The ordinary Catalogue report host and other document collections retain their existing subject projection and readiness behavior.

Local and public browser configuration expose the configured Catalogue by-ID base. Media View and Catalogue Works compose `?collection=catalogue&doc=<work-id>` without a document lookup. The common reader opens that exact Catalogue payload without loading its list manifest or thumbnail settings. Browser Back returns to the calling document/report, including a retained Catalogue list; the document's `index` shortcut opens the Catalogue report and resumes its last-visible browsing state independently of the caller. A link from Media View uses its underlying document as caller; Media View's own Back returns within that document. Invalid Work IDs and missing or mismatched payloads fail visibly without a replacement target.

The [shared browsing module](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) prepares normalized title search values, timestamps and Catalogue thumbnail descriptors once per loaded manifest. [The shared collection reader](../../docs-viewer/runtime/js/shared/docs-collection-report.js) opens Catalogue with 20 documents ordered by `last_updated` descending, then title and document ID. Its Working-only sort control switches between latest-updated and title order; public lists retain the default order. Search uses normalized case-insensitive substring matching over document titles and exact Work-ID fields across the complete collection. Typing waits for a 180 ms pause; clearing applies immediately. Sorting and paging are disabled while a query is pending, and deferred work is cancelled on detail navigation, refresh, errors or unmount. Search/sort changes reset to page 1; page turns reuse cached matches. There is no persistent search index or change to site Search/Recents.

Only the current page's rows and thumbnail elements are mounted. The pager shows current/total pages when results span multiple pages; single-page and empty results hide the entire pager. Previous is disabled on page 1; Next on the last page returns to page 1 using cached matches. Pending filtering disables paging. On the last of multiple pages, Next's tooltip and accessible label identify the first-page destination. Collection totals and filtered counts are neither rendered nor announced. Working selection and Select all use the complete filtered result across pages, while checkboxes exist only on rendered rows. Rows open the common reader. Browser-history return reuses the retained list and restores page, query, sort, selection, scroll and row focus. Manifest replacement or committed-record reconciliation rebuilds prepared values and bounds the page against current matches. Works shares the pager/search timing and return behavior with its separately described ordering, inputs and presentation.

Each row displays the existing 96px Work thumbnail at 64px beside its title. The existing media provider supplies configured generated media policy, using static files on public routes and the existing generated-data read locally; the shared media helper combines it with the route-owned thumbnail base. There are no runtime server changes or per-row Work JSON reads. Current-page thumbnails use eager loading, asynchronous decoding and reserved dimensions; other pages create no image elements. The image and title share one document navigation control; an unavailable image leaves title navigation usable. Public code projection and static site validation are required when these shared modules/styles change.

The Catalogue search placeholder is `work`. Row thumbnails have 6px rounded corners.

Implementation and static review are complete, and the user confirmed review through Site Preview on 2026-09-26. The subsequent count/placeholder copy and rounded-thumbnail adjustments await final visual confirmation. Snapshot data adopts the required manifest through the normal Prepare Preview and Publish operations; old-shape manifests fail visibly. Static checks and the reported manual review do not establish measured browser performance, automated failure-path coverage or a public deployment.

## App-Level Import

The list publishes its mounted `{collection}` target to the management host; the common reader publishes the displayed document's exact collection independently of its caller. Import has no list-toolbar action and remains independent of selection mode and checked IDs.

The one app-level Import modal uses that collection as the frozen destination
for ordinary Word, HTML, Markdown, text, and one-document Markdown-folder
sources. Returned packages and edited review-source folders ignore display
context and retain their exact manifest-owned target, including when it is a
different collection. No browser destination or source-type selector exists.

Every successful Import response returns an exact target, validated `viewer_url` and complete committed record. Completion owners notify retained lists for confirmed created/overwritten records, including confirmed partial results; failed or rolled-back writes supply no successful summary. Explicit Import follow-through retains its own collection refresh where required. Returning to a caller performs no additional reload. Public reports have no Import control or management-module reachability.

## Detail Delete

Delete is a common rendered-document action over one validated `{collection, doc_id}` target. Catalogue omits independent document Delete.

The shipped management workflow:

1. requests a write-free preview;
2. shows the exact source and generated consequences;
3. requires explicit confirmation;
4. re-resolves and deletes only the confined source document;
5. rebuilds the affected collection outputs;
6. notifies retained owners of the confirmed deleted target;
7. returns through browser history to a known caller, or to a surviving ordinary root/empty state when no caller exists; and
8. retains only blocker, unavailable-data, stale-state, and error feedback.

The mutation does not inspect or update Studio canonical data. Deleting a Concept document removes that definition on the next collection build. Missing-document fallbacks for the future relationship model remain separate work.

Normal success must not reload the parent `index-tree`, select another parent
document, or redraw unrelated sidebar state.

## Package Export

The existing Prepare Package workflow remains the modal and export owner with
an explicit collection boundary.

Sub-scope adoption requires:

- document-list reads scoped by `{ scope, sub_scope }`;
- request and server validation that preserve `sub_scope`;
- source loading from the configured child collection;
- package metadata that records the complete collection identity;
- checked-ID eligibility against that exact collection;
- flat-collection profile behavior rather than assumed parent hierarchy; and
- operation records that retain the collection target.

The shipped checked-ID adoption is export-only. App-level Import is a separate
selection-independent workflow. Returned-package and edited-review-folder
Import retain the complete trusted collection identity and never consume the
report's checked IDs.

## Independent Canonical Ownership

Sub-scope management acts only on Docs Viewer sources and projections.

- It does not synchronize fields with Studio records.
- It does not cascade Studio edits or deletes.
- It does not prevent document deletion because an external record refers to
  the document.
- It does not repair or infer external associations.
- It may display or diagnose stale relationships through a separately owned
  feature.

This applies the
[Independent Canonical Documents](Independent_Canonical_Documents.md)
concept without adding cross-application coupling to the report or Docs
management service.

## Risks And Pressure Points

- A large flat collection uses default title search plus any registered
  collection filters over its supplied list. This is loaded-list filtering,
  not overall Docs Viewer search and not a parallel search index.
- Checkbox gutters and toolbars need explicit review at representative laptop/desktop widths.
- Direct detail Delete and future selection-backed bulk Delete are different
  interaction contracts and should not be conflated.
- Collection reconciliation must preserve valid local selection without reloading the
  parent index.
- Public import-graph coverage must continue to reject manage-owned controllers,
  clients, workflows, and package modules.

## Likely Authorities To Inspect

- shared report:
  `docs-viewer/runtime/js/shared/docs-collection-report.js`
- server authoring registry: `docs-viewer/services/docs_collection_customisations.py`
- manage bridge, default, and composition:
  `docs-viewer-management-document-reports.js`,
  `docs-viewer-management-collection-default-contribution.js`, and
  `docs-viewer-management-collection-composition.js`
- managed target normalization and resolution:
  `docs-viewer-management-document-target.js` and
  `docs_management_document_target.py`
- existing selection model and controller:
  `docs-viewer-index-selection.js` and
  `docs-viewer-management-index-controller.js`
- package browser and service:
  `docs-viewer/runtime/js/packages/` and
  `docs-viewer/services/docs_document_packages/`
- local management routes, capability projection, mutation planning, and
  targeted rebuild services; and
- focused public import-boundary, report-module, management-service, selection,
  and package tests.

These are inspection starting points. A delivery should confirm current
ownership before naming exact changed files.
