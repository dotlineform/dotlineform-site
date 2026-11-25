---
draft: false
doc_id: d-20260607-222033-647b52
title: Endpoint Overview
added_date: "2026-06-07 22:20:33"
last_updated: "2026-11-25"
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Local Service Map

Use this map to follow a browser request into its filesystem/workflow owner. [Runtime ownership](Runtime_Module_Ownership.md) identifies the caller; the domain references below own exact inputs and completion rules. The accepted method/path inventory is code-owned rather than copied here.

## Service And Dispatch

[`docs_viewer_service.py`](../../docs-viewer/services/docs_viewer_service.py) serves Manage, Review, canonical static files and local APIs. It owns HTTP framing, process flags, allowed-origin checks at the selected boundaries, bounded JSON or route-specific multipart intake, response status and caching. [Local Setup](Local_Setup.md#service-health-and-capabilities) owns startup flags and capability diagnostics. The static public reader consumes configured public artifacts through its own composition.

[Management route constants](../../docs-viewer/services/docs_management_routes.py) select the accepted paths. [The GET dispatcher](../../docs-viewer/services/docs_management_read_service.py) selects generated/source/report reads; [the POST dispatcher](../../docs-viewer/services/docs_management_service.py) delegates to the focused operation. Integrated packages have [separate constants](../../docs-viewer/services/docs_document_package_routes.py) and a [package dispatcher](../../docs-viewer/services/docs_document_packages/service.py). Review has its own [constants](../../docs-viewer/services/docs_review_routes.py) and [dispatcher](../../docs-viewer/services/docs_review_service.py).

Generated reads, management and Review have independent process gates. Management gates its POSTs, packages and selected source/private GETs; support/report GET membership has its own HTTP routing. The exact gated sets remain in the handler. A shell loading or a browser action being visible does not establish operation authority. Capabilities describe available service work; frontend action policy owns editorial restrictions and exact selections.

## Operation Map

| Intent | Local boundary | Maintained owner |
| --- | --- | --- |
| Read saved reader output | `GET /docs/index-tree`, `/docs/doc`, `/docs/recent`, `/docs/search`, `/docs/workspace-links`; configured collection artifact routes | [Generated reads](Generated_Data_Contracts.md#local-generated-reads) |
| List, load, save as new or delete a private saved result set | `GET /docs/saved-searches` with optional `name`, `POST /docs/saved-searches`, `POST /docs/saved-searches/delete` | [Saved results in Manage](Reader_Discovery_And_Return.md#saved-results-in-manage) |
| Read or save the complete source buffer | `GET /docs/source`; multipart `POST /docs/source/save` | [Source editing](Source_Editing.md) |
| Create, change readiness/Star/order, or delete | Exact-target metadata and mutation requests | [Source mutation endpoints](Source_Mutation_Endpoints.md) |
| Generate one saved document | `POST /docs/rebuild-document` | [Exact Rebuild](Source_Mutation_Endpoints.md#post-docsrebuild-document) |
| Refresh discovery | `POST /docs/refresh-discovery` with `{}` | [Search and Recent](Source_Mutation_Endpoints.md#post-docsrefresh-discovery) |
| Read/refresh an operational report | Report-specific API; Broken Links uses GET saved / POST Refresh | [Reports](Reports.md), [Broken Links](Broken_Links.md#saved-local-report) |
| Import, Export or prepare/return a package | Native multipart Import, staged Import, static HTML Export and `/docs/packages/…` | [Import](Docs_Import.md), [Export](Export.md), [Packages](Document_Packages.md) |
| Adopt refreshed Catalogue facts | `POST /docs/catalogue/regenerate` | [Save, Refresh and Regenerate](Catalogue_Save_And_Refresh.md) |
| Apply prepared publication selections and back up saved Docs data and site content | `POST /docs/publish` with `{}` | [Publish and backup](Builder.md#preview-and-deployment-boundary) |
| Inspect or build a returned package | Independently gated `/docs-review/packages/…` | [Review authority and API](Docs_Review.md#api-surface) |
| Open a canonical local target | `POST /docs/open-local-target` with `{target}` | [Local folder links](Source_Mutation_Endpoints.md#local-folder-links) |

An exact document Rebuild, discovery Refresh and Publish are distinct operations. Full Working Build remains an explicit maintenance CLI. A report read can inspect current inputs or return a saved snapshot according to its owner; the HTTP verb alone does not describe its cost. Review's package-local materialization is a separate contract from ordinary saved Working reads.

## Follow A Readiness Change

Take an already displayed Concepts member. The browser owns its resolved `{collection, doc_id}`, current record, intended boolean and busy state. The [context action](../../docs-viewer/runtime/js/management/docs-viewer-management-context-actions.js) calls the [Draft workflow](../../docs-viewer/runtime/js/management/docs-viewer-management-draft-workflow.js), which sends one `POST /docs/set-draft` through the [management client](../../docs-viewer/runtime/js/management/docs-viewer-management-client.js).

The HTTP owner checks management/origin/body framing. Dispatch selects [set_draft](../../docs-viewer/services/docs_management_draft.py). That owner resolves and reads the exact configured source, checks authoring/readiness validity, rewrites only the intended field when changed and carries prepared source, report and committed metadata to [exact generation](../../docs-viewer/services/docs_document_rebuild.py). Text and dates survive; an unchanged boolean still completes generation.

Generation owns document/Links output and eligible public selections or withdrawals. It preserves saved Search/Recent. The response supplies the exact target, committed record and separate source/generation completion. The browser projects that record into retained lists and controls; a later generation failure still carries saved readiness for projection. [Mutation completion](Source_Mutation_Endpoints.md#completion-and-recovery)

Publish is a later explicit request over the completed Docs/Catalogue queues. Its transfer phase uses upstream eligibility, verifies selected writes and removals, and clears successful units. After that phase succeeds, the request awaits the private Docs and site content Git backups. The response keeps publication `complete` and uses `backup_error` to identify any failed backup. The browser displays that message as an error. [Publish and backup](Builder.md#preview-and-deployment-boundary)

## Failure And Cache Boundaries

The client retains structured error payloads as `error.payload`. Read the operation's saved effects and phase before deciding whether to correct source, rerun its Build, reload the display or repeat Publish. A failed HTTP operation can have completed writes; success at the service can also precede failed browser projection. [Recovery](Local_Setup.md#recover-the-failed-owner)

Selected generated/report GETs and collection file responses use ETag revalidation. Source/capability reads, POST responses and JSON errors retain `no-store`; route configuration and static resources have their own policies. [HTTP caching](Docs_Viewer_Runtime.md#local-http-caching) owns the exact distinction. Ordinary generated reads return saved data and do not trigger Build or freshness reconciliation.
