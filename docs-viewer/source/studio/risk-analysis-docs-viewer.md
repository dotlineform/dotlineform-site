---
doc_id: risk-analysis-docs-viewer
title: Risk Analysis - Docs Viewer
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: admin
---
# Risk Analysis - Docs Viewer

Policy: [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).

## Priority Order

1. Structural
2. Performance / cost
3. Architectural fit
4. Workflow

## Risk Analysis

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Runtime and controller families | Structural | Docs Viewer has focused owners, but management, bookmark, search, config, and remaining runtime handoffs still need clear app-owned boundaries. [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) currently has 62 focused Docs Viewer rows, with 14 above target score 4 and 7 at score 6 or higher. The active rows are concentrated in app runtime coordination, management, bookmarks, scope lifecycle, import, config, search, document, reports, and router controllers. | Track focused slices in [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction). Future route/document workflow changes should extend focused runtime owners rather than adding responsibility back to the app runtime coordinator. |
| Public read-only installs | Performance / cost | `/library/` and `/analysis/` use Docs Viewer runtime on the public site, so frontend payload and interaction cost are public concerns, not only local tooling concerns. A prior evidence pack collected Docs Viewer static metrics, generated payload counts, git touch counts, and JavaScript inventory guardrail output; new evidence packs should write under `var/admin/risk/runs/`. | Use focused evidence packs before prioritising payload or route-load work, and keep public-safe hosted views separate from management-only surfaces. |
| Docs generation/search | Architectural fit | Docs Viewer generation and search are now Python app-generation paths rather than app-facing Ruby/Jekyll builders. The Python/Ruby inventory classifies `docs-viewer/` as high maintenance, medium structure, and medium performance risk across 34 Python files and 13,266 lines. | Keep builder, watcher, management response, and search contracts documented together when generated Docs Viewer schema changes. Treat Ruby/Jekyll as public-site preview/build only. |
| Management writes and rebuilds | Workflow | Source mutation, generated payloads, search, diagnostics, imports, and exports cross local service and builder boundaries. The Python/Ruby inventory identifies docs build, import, export, management mutations, generated reads, live rebuild, and search coordination as Python-owned risk where targeted docs payload/search rebuilds help but resolver-data fallbacks still need care. | Keep rebuild diagnostics, import/export evidence, and management write contracts in this app inventory. Do not move management writes, imports, settings, scope lifecycle, rebuilds, source opening, or local-only reads outside the named management service boundary. |
