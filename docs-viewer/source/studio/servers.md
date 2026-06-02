---
doc_id: servers
title: Servers
added_date: 2026-04-17
last_updated: 2026-06-02
parent_id: ""
---
# Servers

This section documents local server processes used by Studio, Analytics, Docs Viewer, UI Catalogue, public preview, and build tooling.

Use this section for:

- local server architecture and boundaries
- route namespace decisions
- shared security rules for localhost APIs
- the target shape for future Studio server requirements

Keep command-level usage in **[Scripts](/docs/?scope=studio&doc=scripts)**. Script docs should describe how to run a server, its flags, and its current endpoints. Server docs should describe why the server boundary exists and how the pieces should evolve.

Read this section in this order:

1. **[Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)**

Current local server scripts:

- **[Local Studio App](/docs/?scope=studio&doc=local-studio-app)** for the Studio app server boundary and server module ownership
- **[Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)** for Studio shell routes, route-local body modules, retired routes, and route checks
- **[Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis)** for Catalogue, audit, and risk endpoint groups
- `bin/local-analytics` for Analytics tag routes/APIs and Data Sharing routes/APIs
- `bin/local-ui-catalogue` for isolated UI Catalogue demos
- `docs-viewer/bin/docs-viewer` for Docs Viewer `/docs/` manage mode, generated reads, and docs management APIs
- `bin/public-site-preview` for optional public Jekyll preview
- **[Catalogue Write Services](/docs/?scope=studio&doc=scripts-catalogue-write-server)** for catalogue API service modules hosted by the Local Studio app

Risk operations do not have a separate server.
[Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations) records the decision that risk dashboards, app inventories, audit launching, unified activity review, and risk-related local artifacts use the Local Studio app server.
