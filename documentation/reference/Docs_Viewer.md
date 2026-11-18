---
draft: false
doc_id: d-20260424-000000-50b63f
title: Docs Viewer
added_date: "2026-04-24 00:00:00"
last_updated: "2026-11-18"
summary: Entry point for using, operating, and changing the shared Docs Viewer reader and its local management and review surfaces.
parent_id: ""

---
# Docs Viewer

Docs Viewer owns the shared document reader, Working document authoring, generated outputs and package exchange. Studio separately owns canonical Catalogue facts and Refresh. Use the [workflow guide](../guide/README.md) for an editing or publication task.

## Surfaces And Authority

| Surface | Owner and authority |
| --- | --- |
| Public `/` | Static shell and public entrypoint read prepared documents, discovery and media |
| Manage `/docs/` | Local composition reads Working and invokes exact authoring, generation and publication operations |
| Review `/docs-review/` | Package-rooted composition inspects/builds returned-package output; canonical acceptance uses Manage Import |

[Runtime](Docs_Viewer_Runtime.md#three-surfaces) owns execution and imports. [Configuration](Configuration_And_Extension_Points.md) owns workspace/routes/capabilities. [Repository ownership](Source_Tree_Ownership.md) identifies canonical code and separate projects.

## Find The Owner

| Development question | Maintained reference |
| --- | --- |
| What do readers load, and what does Back restore? | [Discovery and return](Reader_Discovery_And_Return.md), [generated data](Generated_Data_Contracts.md) |
| How does a source edit or document mutation complete? | [Source editing](Source_Editing.md), [mutations](Source_Mutation_Endpoints.md) |
| Who owns collection hosts, Book curation and reports? | [Collections and Books](Collections_And_Books.md), [reports](Reports.md) |
| What survives import/export/package review? | [Import](Docs_Import.md), [Export](Export.md), [packages](Document_Packages.md), [Review](Docs_Review.md) |
| Where do media, Work facts and links come from? | [Document media](Media_And_Asset_Handling.md), [Catalogue adoption](Catalogue_Save_And_Refresh.md), [relationships](Related_Links.md) |
| Who owns browser state, controls and presentation? | [Runtime modules](Runtime_Module_Ownership.md), [shared UI](Shared_UI.md), [control surfaces](Panel_Hosts_And_Control_Surfaces.md), [CSS](CSS_Ownership.md), [icons](Toolbar_Icons.md) |
| Which service/build/publication boundary changes? | [Local service map](Endpoint_Overview.md), [Builder](Builder.md), [public shell](Public_Docs_Route_Shell.md) |

Exact modules, fields and endpoint membership remain code/config-owned. Active policy and proposed work stay under [Dev Home](../development/README.md) and [Working](../_working/README.md). Native reader reuse is a [separate App proposal](../app/Docs_Viewer_App_Roadmap.md), retained for review when app development resumes.
