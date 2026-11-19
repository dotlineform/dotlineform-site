---
draft: false
doc_id: d-20260513-105343-6de36b
title: Reports
added_date: "2026-05-13 10:53:43"
last_updated: "2026-11-18"
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer reports

A report block describes a view inside a document. The configured data owner supplies its inputs, and the route composition determines which report can run and which controls it receives. [Collection hosts and Book](Collections_And_Books.md) · [Runtime](Docs_Viewer_Runtime.md#three-surfaces)

## Source Contract

Use one isolated block at column one with blank lines around it. `id` is a registered report token. `collection` is required for `docs_collection` and identifies a configured collection. Other reports use `id` alone.

```md
:::report
id: docs_collection
collection: works
:::
```

The parser accepts exact unquoted `key: value` lines. It rejects duplicate or unknown attributes, including retired `preset`, and legacy `viewer_report*` front matter. Report examples in code or comments remain literal. Edit the host through Source. Generic document Import rejects report blocks or replacing an existing report host. [Report parser](../../docs-viewer/services/docs_report_source.py) · [Source and build validation](../../docs-viewer/services/docs_source_model.py) · [Import](Docs_Import.md)

## Build And Payload Flow

Build replaces the source range with an inert `data-docs-viewer-report-host` element and writes a by-ID `report` descriptor containing `id` and, for `docs_collection`, `collection`. The Index carries only `report_id`. The ordinary document keeps its own identity, placement and eligibility. A report block can name a configured collection for browsing. Workspace `report_host_doc_id` owns the collection's designated navigation and eligibility host. [Payload writer](../../docs-viewer/build/docs_builder/payloads.py) · [Generated data contracts](Generated_Data_Contracts.md) · [Host and collection](Collections_And_Books.md#collection-identity)

## Report Availability

| Authority | Manage | Public |
| --- | --- | --- |
| **Metadata** | The checked `docs-viewer/config/reports/reports.json`. | Explicit `site/assets/data/docs/public-reports.json` projection. |
| **Executable loader** | The Manage report allowlist and optional local composition. | A separate public allowlist with `docs_collection` and `selected_documents`. |
| **Data and actions** | Configured private output, local services and allowed management contributions. | Published manifests, by-ID files and other explicitly public artifacts. |

The route's document-extras hook mounts the selected report in the generated host. The report loader uses the registry entry's `loader_id` to choose a known module, and the report owns its data, presentation and report-specific state. On navigation, the owning mount releases its report and ignores late results after disposal. A local-only report can be named in an eligible document. Public keeps the document and displays an unavailable report. Publication eligibility and report availability therefore have separate owners. [Registry](../../docs-viewer/config/reports/reports.json) · [Manage loaders](../../docs-viewer/runtime/js/reports/docs-viewer-reports.js) · [Public registry](../../site/assets/data/docs/public-reports.json) · [Public loaders](../../docs-viewer/runtime/js/reports/docs-viewer-public-reports.js)

## Composition and capabilities

The shared collection report owns read-only rows, filtering, paging, browsing state and contribution mount points. Manage supplies its contribution with exact targets, selection, committed-record handling and supported actions. Local endpoints check authority at the write boundary. Public instantiates the shared reader through its own module graph without importing the management contribution. The configured authoring service remains separate from report presentation. [Manage composition](../../docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js) · [Shared collection report](../../docs-viewer/runtime/js/shared/docs-collection-report.js)

Catalogue Works illustrates the boundary. It reads private saved data, so its executable report is Manage-only even though browsing it is read-only. Its optional `expandedPresentation` declares a flow or a semantic-table surface and its own toolbar. Manage composes the expanded view and table width tools. That capability's report CSS stays in the local stylesheet. Public uses the canonical shared `docs-viewer-reports.css` through its tracked projection. Manage adds `docs-viewer-local-reports.css` and `docs-viewer-manage.css`. [Report presentation adapter](../../docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js) · [Catalogue Works](Catalogue_Works.md) · [Site-code inventory](../../site-tools/config/site-code-update.json)

A public promotion starts with a public data contract. Add the explicitly promoted registry entry and executable loader, project the required modules and styles, and trace the loaded public graph to its data. A checked-in filename or a hidden button cannot establish that capability. Use the existing projection and deploy-root checks for the code change. [Projection contract](Projection_Contract.md#current-enforcement) · [Composition rationale](../design/Collections_Books_And_Reports.md)

## Current Reports

The checked registry owns the list of report IDs. The table identifies the runtime data owner so changing a report starts in the right place.

| Report IDs | Inputs and refresh owner |
| --- | --- |
| `docs_collection`, `selected_documents` | Shared public-safe manifest or saved Selected data. Manage contributes local actions where configured. [Reader lists](Reader_Discovery_And_Return.md#collection-list-preparation) · [Selected](Source_Organisation.md#selected-documents) |
| `workspace_links` | Saved private Links aggregate. Its explicit Refresh aggregates the current per-document Links records. [Links service](../../docs-viewer/runtime/js/reports/workspace-links-report.js) · [Relationship maintenance](Builder.md#document-relationship-maintenance) |
| `unpublishable` | Configured Working exclusion list, read on opening or Refresh. Generation applies the policy when computing eligibility. [Policy owner](../../docs-viewer/services/docs_publication_ignore.py) |
| `docs_broken_links`, `docs_media` | Saved audits and inventory. Their explicit refresh actions do inspection work. The Docs Media R2 tab uses its own saved orphan findings. [Broken Links](Broken_Links.md#saved-local-report) · [Working and R2 media](Media_And_Asset_Handling.md#docs-media-inventory-report) |
| `project_state` | Projects joins live project folders with refreshed private Catalogue inputs and saved Docs Catalogue references under its own scan/refresh. [Projects report](../../docs-viewer/runtime/js/reports/project-state-report.js) · [Catalogue inputs](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs) |
| `catalogue_works`, `catalogue_medium`, `series_galleries` | Saved private Catalogue report projections. Medium groups the exact saved values from Catalogue Works. Series and Galleries displays explicit pairs and direct-member counts. [Generated reports](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs) |
| `work_downloads`, `work_links` | Refreshed Work resources. Downloads compares exact references with local ready files. Links lists authored labels and URLs. [Work resources](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs) |
| `missing_source_files`, `uncataloged_files` | Refreshed Work-source registrations plus scoped Projects filesystem inspection. Missing Source Files checks expected leaves. Uncatalogued Images opens saved findings and explicitly refreshes represented folders for supported images. [Inspection owner](../../docs-viewer/services/docs_work_source_inspection.py) |

## Inspection And Consumption Boundaries

Opening a saved report reads its configured snapshot; explicit Refresh owns any source/filesystem inspection and replacement. Carry the resolved workspace, parsed inputs and run-local inspections through that operation. The browser owns joins, search/sort preparation, counts and literal display where it already has the data. Saved-data readers trust their producer's domain validity; retain JSON parsing, configured confinement and actual action checks at their owners.

Missing Source Files checks declared leaves without listing folders. Uncatalogued Images scans represented directories for supported image candidates and uses physical identity matching; both share source declarations and run-local path metadata rather than repeated root walks. Projects refresh inspects immediate physical project folders and supplies saved Context/Work/Series/relevance facts; its browser joins them and prepares counts/groups. Later Finder/file-opening actions retain exact target, type, existence and confinement checks independently.

Work Downloads lists its confined ready-file directory and lets the browser match supplied references, including missing/shared/unassigned files. Medium groups exact saved values, counting explicit null as No medium. Links Refresh aggregates participating per-document records; document Build maintains those records without implicitly rebuilding the private report aggregate. Mount disposal releases prepared data/subscriptions and ignores late results. Private report metadata is never made public by adding a report host alone.

[Retired report evidence](../deliveries/Collections_Books_And_Reports_Review.md#retired-report-records) · [Site release workflow](../guide/Publish_And_Deploy.md)
