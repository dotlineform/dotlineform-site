---
doc_id: studio
title: Studio
added_date: 2026-04-23
last_updated: "2026-05-08"
parent_id: ""
sort_order: 20
---
# Studio

This section documents the Studio routes used to review and edit site data, catalogue records, and related operational workflows.

Studio is a site-owned admin toolset, not a separate app. Each page is rendered by Jekyll under `/studio/`, uses the shared Studio layout, and links its implementation notes into the scoped Docs Viewer.

Studio is a local service-backed workspace. The live `.com` routes may render the page shells, but catalogue editing and mutable catalogue review data require `bin/dev-studio` and the localhost services it starts. When a required local service is unavailable, Studio pages should make that state visible and disable affected controls rather than reading stale static editor data.

The current Studio shell is organized around domain dashboards:

- `Catalogue`
- `Library`
- `Analytics`
- `Search`
- `Docs`

The public site nav remains user-facing and separate from this admin layer. Public `Works` and public `Library` routes do not become Studio routes.

The Library dashboard includes `/studio/library-documents/` for reviewing generated Library document records, `/studio/export/` for running configured exports from generated Library Docs Viewer data, and `/studio/import/` for generating preview Markdown from staged Library import data.
Those pages depend on the docs-management local service for file writes; when the service is unavailable, command execution stays unavailable.
Export pattern definitions live in `assets/studio/data/library_export_configs.json`, not in route code or `studio_config.json`.

## Route Ready State

Studio landing and dashboard routes expose the shared route-ready contract:

- `/studio/` uses `#studioHomeRoot` with `data-studio-mode="landing"` and static ready state
- `/studio/catalogue/`, `/studio/library/`, `/studio/analytics/`, and `/studio/search/` use dashboard roots with `data-studio-mode="dashboard"`
- dashboard routes set `data-studio-busy="true"` while lightweight metric hydration runs, then mark ready after metric reads settle
- these routes are framework markers for future dashboard behavior; they do not imply a formal dashboard test suite

Related references:

- **[Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)** for the short Studio UI implementation checklist and preflight
- **[Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)** for Studio-specific UI patterns, naming rules, and modal behavior
- **[UI Framework](/docs/?scope=studio&doc=ui-framework)** for site-wide interaction defaults, including shared docs-viewer and search UI standards
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** for the shared `/docs/` implementation that now hosts Studio documentation

Read this section in this order:

1. **[Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)** for Studio UI preflight before implementing or revising a Studio page
2. **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the route shell, page wiring, and Docs Viewer integration
3. **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for shared config, local-write behavior, and operational boundaries
4. **[Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)** for Codex-run browser smoke-test harness rules
5. Technical route and workflow docs:
	   - **[Studio Activity](/docs/?scope=studio&doc=studio-activity)**
	   - **[Studio Audits](/docs/?scope=studio&doc=studio-audits)**
   - **[Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)**
   - **[Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)**
   - **[Library Documents](/docs/?scope=studio&doc=library-documents)**
   - **[Studio Data Export](/docs/?scope=studio&doc=studio-data-export)**
   - **[Studio Data Import](/docs/?scope=studio&doc=studio-data-import)**
   - **[Library Export v1](/docs/?scope=studio&doc=library-export)**
   - **[Library Import v1](/docs/?scope=studio&doc=library-import)**
	   - **[Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status)**
	   - **[Project State Page](/docs/?scope=studio&doc=project-state-page)**
   - **[Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)**
   - **[Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)**
   - **[Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)** compatibility route note
   - **[Tag Groups](/docs/?scope=studio&doc=tag-groups)**
   - **[Tag Registry](/docs/?scope=studio&doc=tag-registry)**
   - **[Tag Aliases](/docs/?scope=studio&doc=tag-aliases)**
   - **[Series Tags](/docs/?scope=studio&doc=series-tags)**
   - **[Tag Editor](/docs/?scope=studio&doc=tag-editor)**
   - **[Studio Works](/docs/?scope=studio&doc=studio-works)**

Practical page-use guides, including the catalogue work/series editors, live under [User Guide](/docs/?scope=studio&doc=user-guide).

Current Studio landing routes:

- `/studio/`
- `/studio/catalogue/`
- `/studio/library/`
- `/studio/analytics/`
- `/studio/search/`
- `/docs/`

Current workflow/detail routes:

- `/studio/activity/`
- `/studio/audits/`
- `/studio/catalogue-field-registry/`
- `/studio/docs-broken-links/`
- `/studio/docs-import/`
- `/studio/library-documents/`
- `/studio/export/`
- `/studio/import/`
- `/studio/catalogue-status/`
- `/studio/project-state/`
- `/studio/bulk-add-work/`
- `/studio/catalogue-moment/`
- `/studio/catalogue-moment/?moment=<moment_id>`
- `/studio/catalogue-moment-import/` compatibility redirect
- `/studio/catalogue-work/?work=<work_id>`
- `/studio/tag-groups/`
- `/studio/tag-registry/`
- `/studio/tag-aliases/`
- `/studio/series-tags/`
- `/studio/series-tag-editor/?series=<series_id>`
- `/studio/studio-works/`

## Local Development

Use the repo-local runner from `dotlineform-site/`:

```bash
bin/dev-studio
```

Current runner behavior:

- rebuilds Docs Viewer data from `_docs_src/`
- starts Jekyll on `127.0.0.1:4000`
- starts `scripts/studio/tag_write_server.py`
- starts `scripts/studio/catalogue_write_server.py`
- starts `scripts/docs/docs_management_server.py`
- starts `scripts/studio/audit_service.py`
- keeps all long-running processes attached to the current terminal
- stops all long-running processes on `Ctrl+C`
- serves mutable catalogue source and lookup reads through the local catalogue server rather than through Jekyll-served static JSON

Current limits:

- it does not enable `--livereload`
- it does not rebuild docs-search artifacts
- it does not replace the standalone scripts documented in **[Scripts](/docs/?scope=studio&doc=scripts)**
- local server architecture and future consolidation strategy are documented in **[Servers](/docs/?scope=studio&doc=servers)**

If you edit docs after the runner has started, rebuild the docs payloads manually:

```bash
./scripts/build_docs.rb --write
```
