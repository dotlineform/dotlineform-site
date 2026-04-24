---
doc_id: servers
title: "Servers"
added_date: 2026-04-17
last_updated: 2026-04-17
parent_id: ""
sort_order: 140
---
# Servers

This section documents local server processes used by Studio and build tooling.

Use this section for:

- local server architecture and boundaries
- route namespace decisions
- shared security rules for localhost APIs
- the target shape for future Studio server requirements

Keep command-level usage in **[Scripts](/docs/?scope=studio&doc=scripts)**. Script docs should describe how to run a server, its flags, and its current endpoints. Server docs should describe why the server boundary exists and how the pieces should evolve.

Read this section in this order:

1. **[Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)**

Current local server scripts:

- **[Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)**
- **[Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)**
