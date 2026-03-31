---
doc_id: studio
title: Studio
last_updated: 2026-03-31
parent_id: ""
sort_order: 5
---

# Studio

This section documents the Studio routes used to review and edit the site’s tag data.

Studio is a site-owned toolset, not a separate app. Each page is rendered by Jekyll under `/studio/`, uses the shared Studio layout, and links its implementation notes into the scoped Docs Viewer.

Related references:

- **[Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)** for Studio-specific UI patterns, naming rules, and modal behavior
- **[UI Framework](/docs/?scope=studio&doc=ui-framework)** for site-wide interaction defaults, including shared docs-viewer and search UI standards
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** for the shared `/docs/` implementation that now hosts Studio documentation

Read this section in this order:

1. **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)** for the route shell, page wiring, and Docs Viewer integration
2. **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)** for shared config, local-write behavior, and operational boundaries
3. Page-specific docs:
   - **[Tag Groups](/docs/?scope=studio&doc=tag-groups)**
   - **[Tag Registry](/docs/?scope=studio&doc=tag-registry)**
   - **[Tag Aliases](/docs/?scope=studio&doc=tag-aliases)**
   - **[Series Tags](/docs/?scope=studio&doc=series-tags)**
   - **[Tag Editor](/docs/?scope=studio&doc=tag-editor)**
   - **[Studio Works](/docs/?scope=studio&doc=studio-works)**

Current Studio pages:

- `/studio/`
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
- keeps both processes attached to the current terminal
- stops both processes on `Ctrl+C`

Current limits:

- it does not enable `--livereload`
- it does not rebuild docs-search artifacts
- it does not replace the standalone scripts documented in **[Scripts](/docs/?scope=studio&doc=scripts)**

If you edit docs after the runner has started, rebuild the docs payloads manually:

```bash
./scripts/build_docs_data.rb --write
```
