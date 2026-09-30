---
draft: false
doc_id: d-20260910-202325-53b5f9
title: Links View
added_date: "2026-09-10 20:23:25"
last_updated: "2026-09-30 19:01:32"
summary: The single-document Links presentation, exact generated-data reads, Content Detail hosting and navigation boundaries.
parent_id: d-20260331-000000-c313fd
---
# Links View

Links displays the documents related to the exact displayed document. It uses the shared Content Detail host alongside Media View, with its own adapter and presentation module. The current enabled context is Working, including its configured collections. [Builder](Builder.md) owns extraction, eligibility, both-end updates and the separate relationship records; [Source Editor Scripts](Source_Editor_Scripts.md) owns ordinary document-link insertion.

## Display And Identity

The **🔀 Links** document-toolbar action follows the mounted document. When a collection document is displayed, it uses that document's exact `{collection, doc_id}`; ordinary documents use an empty collection. A report list or a loading child does not substitute its host document as the relationship target.

The heading uses the displayed document's title. The presentation groups entries in this order:

| Section | Membership |
| --- | --- |
| Concepts | Documents in the `concepts` collection. |
| Works | Documents in the `works` or `catalogue` collection, independently of their authoring Subject. |
| References | Ordinary documents with an empty collection. |

Empty sections are hidden and entries sort A–Z by title. Incoming and outgoing entries are combined by exact `{collection, doc_id}` so repeated and reciprocal links display once. Distinct documents with the same title remain distinct. Saved incoming and outgoing lists retain direction, with each document appearing once per list. Moments has no section and Processing presentation remains deferred. A broader collection-based or plain-list UI remains a separate redesign; the prepared schema already supplies identity, collection and title for it.

Links uses normal document width without an outer border and keeps the index panel's existing state. `mainLayoutByTargetKind` in the view registry lets this presentation select `normal` while Media, diagrams, tables and expanded reports retain their expanded layout. The title aligns with the normal document title.

Selecting an entry derives its document location from exact identity and the current viewer configuration, using the configured report host for a collection document. **Back to document** restores the invoking document or child detail, its scroll and toolbar focus. The view stays one document deep; it does not traverse neighbours or infer additional associations.

## Data Reads

The configured workspace provider exposes `canReadLinks`, `readLinks` and `documentHref`. Browser availability comes from `links_enabled`, projected from `docs-viewer/config/links-builder.json` for Working. There is no document allowlist.

Locally, the generated-data runtime calls `GET /docs/links` with the exact collection and immutable document ID. The service reads configured Working `generated/documents/links-by-id/<doc_id>.json`, checks schema version 4 and the flat `self.collection`/`self.doc_id` against the request, and rejects paths outside the owned directory. It does not build, repair or search another collection.

One version 4 response contains only `schema_version`, `self`, `incoming` and `outgoing`. `self` and every entry directly in the incoming/outgoing arrays use the same flat `{collection, doc_id, title}` summary. Occurrence details, counts and the counterpart `document` wrapper are removed. Each direction contains unique document identities. `docsViewerLinksDocumentHref` resolves navigation from the reader's already loaded viewer route and exact collection report host; it fetches neither an aggregate, a collection manifest nor each neighbour's ordinary payload. `links_schema.py` owns the JSON projection independently of `links_model.py` and reference maintenance. Earlier schemas are rejected and require explicit saved-data migration.

An existing record with no displayable entries, or a missing relationship file for the mounted document, shows **No links.** Records are created lazily when a resolved relationship needs them, so absence is normal. A failed read other than a missing file, or an identity/schema mismatch, reports an error. These states do not cause the browser to create or repair data.

The public-safe provider can read a configured static `links_by_id_url_base` without local service URLs or capability probes. Public configuration currently leaves Links disabled. Prepared published relationship data, public activation and deployment belong to their separate workflow.

## Loading And Hosted State

The Links adapter prepares data before requesting Content Detail. Its mount generation and request version prevent a late response from opening for a replaced document, changed child or removed invoking control. Presentation state belongs to the exact mount; it is not a stored document identity or a browser-history format.

Currently each opening reads the relationship record again. Shared page-session reuse and browser Back/Forward restoration of the same hosted view, without first flashing the underlying document, remain planned work. The implemented **Back to document** control is independent of that future browser-history behavior.

## Implementation Owners

| Owner | Responsibility |
| --- | --- |
| `docs-viewer-links-detail.js` | Exact mounted target, loading, stale-read rejection and presentation lifecycle. |
| `docs-viewer-links-presentation.js` | Version/identity validation and the shallow grouped display projection. |
| `docs-viewer-document-controller.js` and `docs-collection-report.js` | Ordinary/collection document state supplied to the adapter. |
| `docs-viewer-workspace-provider.js` and `docs-viewer-generated-data-runtime.js` | Configured availability, derived navigation and one generated-data read. |
| `docs-viewer-content-detail-view.js`, `docs-viewer-main-view-host.js` and `docs-viewer-view-registry.js` | Shared hosting, layout, toolbar and return lifecycle. |
| `docs-viewer/services/docs_generated_reads.py` | Exact configured local relationship-file read. |

The browser modules above are canonical under `docs-viewer/runtime/js/shared/`; their public-safe projection is tracked under `site/docs-viewer/`. Existing files `docs-viewer/tests/js/docs_viewer_links_contract.mjs`, `docs-viewer/tests/python/test_docs_links_builder.py` and `docs-viewer/tests/python/test_docs_generated_reads.py` predate the version 4 schema and contain retired contracts. They have not been migrated or run as evidence for this change; test work requires its separately agreed specification. Ordinary visual and navigation acceptance remains manual.
