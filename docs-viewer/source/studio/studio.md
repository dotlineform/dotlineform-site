---
doc_id: studio
title: Studio
added_date: 2026-04-23
last_updated: 2026-07-11
parent_id: ""
---
# Studio

This section documents the Local Studio app routes used to review and edit public site data and catalogue records.

Studio is a local service-backed workspace. Editing and mutable review data require `bin/local-studio` and the localhost services it starts. When a required local service is unavailable, Studio pages should make that state visible and disable affected controls rather than reading stale static editor data.

The current Studio shell is organized around Studio-owned catalogue entry points:

- `Catalogue`
- `Docs`

Analytics and Data Sharing now belong to the standalone Local Analytics app.
Studio may link to those workflows, but it does not host their routes or APIs.

Document management and Docs Import are inside the standalone Docs Viewer service's `/docs/` manage-mode.
Local Studio keeps Docs as a navigation integration point, but does not serve the Docs Viewer shell or Docs Viewer runtime/static/config files.

Sharing profile definitions live in `data-sharing/adapters/documents/config/prepare-profiles.json`, not in route code or `studio_config.json`.

## Route Ready State

Studio landing and operational routes expose the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state) contract.
The same page owns Studio helper, route inventory, and audit guidance so the contract is not split across app-specific child docs.

## Key Documents

- **[Knowledge System Vision](/docs/?scope=studio&doc=knowledge-system-vision)** for the shared purpose of Studio, Analytics, Docs Viewer, Data Sharing, and the Analysis scope
- **[Development Workflow](/docs/?scope=studio&doc=development-workflow)**
  end-to-end lifecycle guidance for human and Codex implementation work.
- **[Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)**
  checked-in dependency sources, critical versus workflow-specific packages, and local/cloud dependency expectations.
- **[UI](/docs/?scope=studio&doc=ui)** for UI framework and maintenance
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** for the shared `/docs/` implementation that hosts Studio documentation
- **[Route Ready State](/docs/?scope=studio&doc=route-ready-state)** for the shared ready/busy contract across local app route shells
- **[Studio Static Route Template](/docs/?scope=studio&doc=studio-static-route-template)** for Studio route template ownership and route script boundaries
- **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the route shell architecture, route registry, shared browser modules, and Docs Viewer integration
- **[Local Studio App](/docs/?scope=studio&doc=local-studio-app)** for the app server boundary, sibling-service split, runtime config shape, and server module ownership
- **[Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)** for mounted local routes, route template ownership, retired route notes, page-level doc links, and route checks
- **[Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis)** for `/studio/api/...` endpoint groups and adapter ownership
- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for shared config, local-write behavior, and operational boundaries
- **[Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing)** for Codex-run browser smoke-test harness rules

## Local Development

Use the repo-local runner from `dotlineform-site/`:

```bash
bin/local-studio
```

Use the start-all runner when the same terminal should supervise public-site Live Preview, Local Studio, Local Analytics, UI Catalogue, and Docs Viewer together:

```bash
bin/local-all
```

If you disable the watcher or need an explicit rebuild, rebuild docs payloads manually by scope:

```bash
./docs-viewer/build/build_docs.py --scope studio --write
```
