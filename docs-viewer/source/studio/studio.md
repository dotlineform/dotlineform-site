---
doc_id: studio
title: Studio
added_date: 2026-04-23
last_updated: 2026-06-06
parent_id: ""
---
# Studio

This section documents the Local Studio app routes used to review and edit public site data and catalogue records.

Studio is a local service-backed workspace. Editing and mutable review data require `bin/local-studio` and the localhost services it starts. When a required local service is unavailable, Studio pages should make that state visible and disable affected controls rather than reading stale static editor data.

The current Studio shell is organized around Studio-owned catalogue entry points:

- `Catalogue`
- `Docs`
- sibling Admin links

Analytics and Data Sharing now belong to the standalone Local Analytics app.
Studio may link to those workflows, but it does not host their routes or APIs.

Document management and Docs Import are inside the standalone Docs Viewer service's `/docs/` manage-mode.
Local Studio keeps Docs as a navigation integration point, but does not serve the Docs Viewer shell or Docs Viewer runtime/static/config files.

Sharing profile definitions live in `data-sharing/config/library-export-configs.json`, not in route code or `studio_config.json`.

## Route Ready State

Studio landing and operational routes expose the shared route-ready contract:

- `/studio/` uses `#studioHomeRoot` with `data-studio-mode="landing"` and static ready state
- retired Catalogue dashboard entry points should stay retired; their links live on the `/studio/` home page
- page-local metrics should live on the individual workflow pages where they are relevant

## Key Documents

- **[Development Workflow](/docs/?scope=studio&doc=development-workflow)**
  end-to-end lifecycle guidance for human and Codex implementation work.
- **[Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)**
  checked-in dependency sources, critical versus workflow-specific packages, and local/cloud dependency expectations.
- **[UI Audits](/docs/?scope=studio&doc=ui-audits)**
  saved page-level UI conformance reviews and follow-up audit records.

- **[UI](/docs/?scope=studio&doc=ui)** for UI framework and maintenance
- **[UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)** for UI patterns, naming rules, and modal behavior
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** for the shared `/docs/` implementation that hosts Studio documentation
- **[Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)** for the implemented route-ready contract, helper modules, route inventory, and audit coverage
- **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the route shell architecture, route registry, shared browser modules, and Docs Viewer integration
- **[Local Studio App](/docs/?scope=studio&doc=local-studio-app)** for the app server boundary, sibling-service split, runtime config shape, and server module ownership
- **[Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)** for mounted local routes, route-local shell ownership, retired route notes, page-level doc links, and route checks
- **[Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis)** for `/studio/api/...` endpoint groups and adapter ownership
- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for shared config, local-write behavior, and operational boundaries
- **[Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)** for Codex-run browser smoke-test harness rules

Technical route and workflow docs:

- **[Studio Activity](/docs/?scope=studio&doc=studio-activity)**
- **[Studio Audits](/docs/?scope=studio&doc=studio-audits)**
- **[Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy)**
- **[Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)**
- **[Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)**
- **[Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)**
- **[Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)**
- **[Library Documents](/docs/?scope=studio&doc=library-documents)**
- **[Data Sharing](/docs/?scope=studio&doc=data-sharing)**
- **[Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status)**
- **[Project State Page](/docs/?scope=studio&doc=project-state-page)**
- **[Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)**
- **[Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)**
- **[Studio Works](/docs/?scope=studio&doc=studio-works)**

## Local Development

Use the repo-local runner from `dotlineform-site/`:

```bash
bin/local-studio
```

Use the start-all runner when the same terminal should supervise public-site Live Preview, Local Studio, Local Analytics, UI Catalogue, and Docs Viewer together:

```bash
bin/local-all
```

Current runner behavior:

- starts the local Studio app server for the Studio shell and Catalogue APIs
- does not start Local Admin, Local Analytics, public-site preview, or the standalone Docs Viewer service; use each runner directly or `bin/local-all` for the supervised sibling-service workflow
- has no Studio audit HTTP service; browser audit APIs are hosted by the Local Admin app and direct automation uses `admin-app/app/server/admin_app/audit_runner.py`
- starts the docs live rebuild watcher by default
- keeps all long-running processes attached to the current terminal
- stops all long-running processes on `Ctrl+C`
- serves mutable catalogue source and lookup reads through the local Studio app rather than through Jekyll-served static JSON

Current limits:

- it does not enable `--livereload`
- it does not serve `/docs/`; Docs Viewer manage mode belongs to the standalone Docs Viewer service
- it does not serve `/admin/`, `/admin/api/...`, `/analytics/`, `/analytics/api/...`, `/ui-catalogue/...`, or Data Sharing APIs
- it does not rebuild docs or docs-search artifacts on startup
- it does not start Jekyll; use `bin/public-site-preview` for public-site preview
- it does not replace the standalone scripts documented in **[Scripts](/docs/?scope=studio&doc=scripts)**

If you disable the watcher or need an explicit rebuild, rebuild docs payloads manually by scope:

```bash
./docs-viewer/build/build_docs.py --scope studio --write
```
