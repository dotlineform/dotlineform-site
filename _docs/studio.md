---
doc_id: studio
title: Studio
added_date: 2026-04-23
last_updated: 2026-05-13
parent_id: ""
sort_order: 3000
---
# Studio

This section documents the Studio routes used to review and edit site data, catalogue records, and related operational workflows.

Studio is a site-owned admin toolset, not a separate app. Each page is rendered by Jekyll under `/studio/`, uses the shared Studio layout, and links its implementation notes into the scoped Docs Viewer.

Studio is a local service-backed workspace. The live `.com` routes may render the page shells, but catalogue editing and mutable catalogue review data require `bin/dev-studio` and the localhost services it starts. When a required local service is unavailable, Studio pages should make that state visible and disable affected controls rather than reading stale static editor data.

The current Studio shell is organized around active admin entry points:

- `Catalogue`
- `Analytics`
- `Data Sharing`
- `Docs`

The public site nav remains user-facing and separate from this admin layer. Public `Works` and public `Library` routes do not become Studio routes.
There is no standalone Studio Search dashboard. Catalogue search configuration or review pages belong under the Catalogue dashboard; Docs Viewer search metrics or configuration belong in `/docs/` manage mode.

Library workflows now live with their owning surfaces: Library document management and Docs Import are inside `/docs/` manage mode, generated Library document review is the [Library Documents](/docs/?scope=studio&doc=library-documents) report, and Library package preparation/review starts from `/studio/data-sharing/`.
Those write-capable pages depend on the docs-management local service; when the service is unavailable, command execution stays unavailable.
Sharing profile definitions live in `assets/studio/data/library_export_configs.json`, not in route code or `studio_config.json`.

## Route Ready State

Studio landing and dashboard routes expose the shared route-ready contract:

- `/studio/` uses `#studioHomeRoot` with `data-studio-mode="landing"` and static ready state
- `/studio/catalogue/?mode=manage` and `/studio/analytics/?mode=manage` use dashboard roots with `data-studio-mode="dashboard"`
- dashboard routes set `data-studio-busy="true"` while lightweight metric hydration runs, then mark ready after metric reads settle
- these routes are framework markers for future dashboard behavior; they do not imply a formal dashboard test suite

Related references:

- **[Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)** for the implemented route-ready contract, helper modules, route inventory, and audit coverage
- **[Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)** for the short Studio UI implementation checklist and preflight
- **[Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)** for Studio-specific UI patterns, naming rules, and modal behavior
- **[UI Framework](/docs/?scope=studio&doc=ui-framework)** for site-wide interaction defaults, including shared docs-viewer and search UI standards
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** for the shared `/docs/` implementation that now hosts Studio documentation

Read this section in this order:

1. **[Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)** for Studio UI preflight before implementing or revising a Studio page
2. **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the route shell, page wiring, and Docs Viewer integration
3. **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for shared config, local-write behavior, and operational boundaries
4. **[Studio Ready State](/docs/?scope=studio&doc=studio-ready-state)** for the implemented route-ready contract and audit expectations
5. **[Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)** for Codex-run browser smoke-test harness rules
6. Technical route and workflow docs:
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

Practical page-use guides, including the catalogue work/series editors, live under [User Guide](/docs/?scope=studio&doc=user-guide).

Current Studio landing routes:

- `/studio/`
- `/studio/catalogue/?mode=manage`
- `/studio/analytics/?mode=manage`
- `/studio/data-sharing/?mode=manage`
- `/docs/`

Current workflow/detail routes:

- `/studio/activity/`
- `/studio/audits/`
- `/studio/catalogue-field-registry/`
- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`
- `/studio/catalogue-status/?mode=manage`
- `/studio/project-state/?mode=manage`
- `/studio/bulk-add-work/`
- `/studio/catalogue-moment/`
- `/studio/catalogue-moment/?moment=<moment_id>`
- `/studio/catalogue-moment/?file=<moment_id>.md`
- `/studio/catalogue-work/?work=<work_id>`
- `/studio/analytics/tag-groups/`
- `/studio/analytics/tag-registry/`
- `/studio/analytics/tag-aliases/`
- `/studio/analytics/series-tags/`
- `/studio/analytics/series-tag-editor/?series=<series_id>`
- `/studio/studio-works/`

## Local Development

Use the repo-local runner from `dotlineform-site/`:

```bash
bin/dev-studio
```

Current runner behavior:

- optionally rebuilds Docs Viewer data when `DOCS_STARTUP_REBUILD_SCOPES` is set
- starts Jekyll on `127.0.0.1:4000`
- starts the local Studio app server for Studio shell, Docs management, Analytics tag APIs, and Studio audit APIs
- starts `scripts/catalogue/catalogue_write_server.py`
- skips the standalone `scripts/docs/docs_management_server.py` by default because Docs management is hosted by the local Studio app
- skips the standalone `scripts/studio/audit_service.py` by default because Studio audit APIs are hosted by the local Studio app
- starts the docs live rebuild watcher by default
- keeps all long-running processes attached to the current terminal
- stops all long-running processes on `Ctrl+C`
- serves mutable catalogue source and lookup reads through the local catalogue server rather than through Jekyll-served static JSON

Current limits:

- it does not enable `--livereload`
- it does not rebuild docs or docs-search artifacts on startup unless `DOCS_STARTUP_REBUILD_SCOPES` is set
- it does not replace the standalone scripts documented in **[Scripts](/docs/?scope=studio&doc=scripts)**
- local server architecture and future consolidation strategy are documented in **[Servers](/docs/?scope=studio&doc=servers)**

If you disable the watcher or need an explicit rebuild, rebuild docs payloads manually:

```bash
./scripts/build_docs.rb --write
```
