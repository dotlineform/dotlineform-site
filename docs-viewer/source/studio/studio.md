---
doc_id: studio
title: Studio
added_date: 2026-04-23
last_updated: 2026-05-24
parent_id: ""
sort_order: 2000
---
# Studio

This section documents the Local Studio app routes used to review and edit public site data, catalogue records, and related operational workflows.

Studio is a local service-backed workspace. Editing and mutable review data require `bin/local-studio` and the localhost services it starts. When a required local service is unavailable, Studio pages should make that state visible and disable affected controls rather than reading stale static editor data.

The current Studio shell is organized around active admin entry points:

- `Catalogue`
- `Analytics`
- `Data Sharing`
- `Docs`

Document management and Docs Import are inside `/docs/` manage-mode.

Sharing profile definitions live in `assets/studio/data/library_export_configs.json`, not in route code or `studio_config.json`.

## Route Ready State

Studio landing and dashboard routes expose the shared route-ready contract:

- `/studio/` uses `#studioHomeRoot` with `data-studio-mode="landing"` and static ready state
- `/studio/catalogue/?mode=manage` and `/studio/analytics/?mode=manage` use dashboard roots with `data-studio-mode="dashboard"`
- dashboard routes set `data-studio-busy="true"` while lightweight metric hydration runs, then mark ready after metric reads settle
- these routes are framework markers for future dashboard behavior; they do not imply a formal dashboard test suite

## Key Documents

- **[Development Workflow](/docs/?scope=studio&doc=development-workflow)**
  end-to-end lifecycle guidance for human and Codex implementation work, including rules for maintaining the site change log.
- **[Change History Reports](/docs/?scope=studio&doc=change-history-reports&mode=manage)**
  manage-only structured change-history views generated from `_docs_logs/`.
- **[Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)**
  checked-in dependency sources, critical versus workflow-specific packages, and local/cloud dependency expectations.
- **[UI Audits](/docs/?scope=studio&doc=ui-audits)**
  saved page-level UI conformance reviews and follow-up audit records.

- **[UI](/docs/?scope=studio&doc=ui)** for UI framework and maintenance
- **[UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)** for UI patterns, naming rules, and modal behavior
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** for the shared `/docs/` implementation that hosts Studio documentation
- **[Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)** for the implemented route-ready contract, helper modules, route inventory, and audit coverage
- **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the route shell, page wiring, and Docs Viewer integration
- **[Local Studio App](/docs/?scope=studio&doc=local-studio-app)** for the app server, mounted local routes, local API ownership, and current route-level checks
- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for shared config, local-write behavior, and operational boundaries
- **[Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)** for Codex-run browser smoke-test harness rules

Technical route and workflow docs:

- **[Studio Activity](/docs/?scope=studio&doc=studio-activity)**
- **[Studio Audits](/docs/?scope=studio&doc=studio-audits)**
- **[Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory)**
- **[Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)**
- **[Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)**
- **[Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)**
- **[Library Documents](/docs/?scope=studio&doc=library-documents)**
- **[Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)**
- **[Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec)**
- **[Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status)**
- **[Project State Page](/docs/?scope=studio&doc=project-state-page)**
- **[Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)**
- **[Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)**
- **[Tag Groups](/docs/?scope=studio&doc=tag-groups)**
- **[Tag Registry](/docs/?scope=studio&doc=tag-registry)**
- **[Tag Aliases](/docs/?scope=studio&doc=tag-aliases)**
- **[Series Tags](/docs/?scope=studio&doc=series-tags)**
- **[Tag Editor](/docs/?scope=studio&doc=tag-editor)**
- **[Studio Works](/docs/?scope=studio&doc=studio-works)**

## Practical page-use guides

- [User Guide](/docs/?scope=studio&doc=user-guide).

## Local Development

Use the repo-local runner from `dotlineform-site/`:

```bash
bin/local-studio
```

Current runner behavior:

- optionally rebuilds Docs Viewer data when `DOCS_STARTUP_REBUILD_SCOPES` is set
- starts the local Studio app server for Studio shell, Docs management, Analytics tag APIs, and Studio audit APIs
- skips the standalone `studio/docs-viewer/services/docs_management_server.py` by default because Docs management is hosted by the local Studio app
- has no standalone Studio audit HTTP service; browser audit APIs are hosted by the local Studio app and direct automation uses `studio/app/server/studio/audit_runner.py`
- starts the docs live rebuild watcher by default
- keeps all long-running processes attached to the current terminal
- stops all long-running processes on `Ctrl+C`
- serves mutable catalogue source and lookup reads through the local Studio app rather than through Jekyll-served static JSON

Current limits:

- it does not enable `--livereload`
- it does not rebuild docs or docs-search artifacts on startup unless `DOCS_STARTUP_REBUILD_SCOPES` is set
- it does not start Jekyll; use `bin/public-site-preview` for public-site preview
- it does not replace the standalone scripts documented in **[Scripts](/docs/?scope=studio&doc=scripts)**
- local server architecture and future consolidation strategy are documented in **[Servers](/docs/?scope=studio&doc=servers)**

If you disable the watcher or need an explicit rebuild, rebuild docs payloads manually by scope:

```bash
./scripts/build_docs.rb --scope studio --write
```
