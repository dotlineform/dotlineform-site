---
doc_id: site-request-studio-source-tree-reorganization-layout
title: Studio Source Tree Reorganization Layout
added_date: 2026-05-24
last_updated: 2026-05-24
parent_id: site-request-studio-source-tree-reorganization
sort_order: 10013
viewable: true
---

This document is archived and is no longer maintained.

---

# Studio Source Tree Reorganization Layout

This is the concrete target layout for [Studio Source Tree Reorganization Request](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization).

This document records `STSR-005`.
It is a planning document for physical source ownership.
It does not move files, create compatibility paths, or authorize dual-read fallback logic.

## Layout Contract

The target boundary is:

```text
studio/
  app/
    server/
    views/
    frontend/
      js/
      config/
    assets/
      css/
      img/
  commands/
  data/
    canonical/
      catalogue/
      catalogue-markdown/
      analytics/
      media/
    config/
      catalogue/
      analytics/
      data-sharing/
      runtime/
    generated/
      catalogue-lookup/
      activity/
      thumbnail-quality/
  services/
    catalogue/
    analytics/
    media/
    data-sharing/
  workflows/
    change-requests/
      logs/
        entries/
      generated/
      reports/
      services/
  checks/
    config/
    public-surface/
    source-boundary/
  tests/
    python/
    smoke/
    fixtures/
  shared/
    python/
    ruby/
  docs-viewer/
    source/
      studio/
      library/
      analysis/
    source-assets/
      interactive/
    runtime/
      js/
      shells/
      reports/
    assets/
      css/
    config/
      reports/
      scopes/
      runtime/
      ui-text/
    build/
    server/
    services/
    tests/
  ui-catalogue/
    demos/
    notes/
    assets/
```

Root-level command wrappers may remain only as deliberate entrypoints.
Their implementation should delegate into `studio/commands/` or the owning Studio/Docs Viewer module and should not preserve old source paths.

## Public Site Boundary

The paths below remain outside `studio/` because they are public Jekyll source, public route integration, public runtime, or generated public output:

| Public path family | Final role |
| --- | --- |
| `_config.yml`, `.ruby-version`, `Gemfile`, `Gemfile.lock` | Jekyll and package infrastructure. |
| `_layouts/default.html`, `_layouts/about.html`, `_layouts/work.html`, `_layouts/series.html`, `_layouts/moment.html`, `_layouts/work_details.html` | Public Jekyll layouts. |
| `_includes/artist_line.html`, `_includes/nav_item.html`, `_includes/work_index_item.html` | Public Jekyll includes used by published routes. |
| `_works/`, `_series/`, `_moments/`, `_work_details/`, `_works_print/` | Public Jekyll collection/page source. |
| `works/`, `series/`, `catalogue/`, `recent/`, `search/`, `analysis/`, `library/`, `docs/`, `data/`, `logs/` | Public route surfaces and minimal route adapters. |
| `assets/js/` | Public browser runtime for published pages. |
| `assets/css/main.css` | Public CSS after Studio-only selectors move out. |
| `assets/data/docs/scopes/`, `assets/data/search/` | Generated public Docs Viewer/search payloads. |
| `assets/data/works_index.json`, `assets/data/series_index.json`, `assets/data/moments_index.json`, `assets/data/recent_index.json` | Generated public catalogue indexes. |
| `assets/works/`, `assets/series/`, `assets/moments/`, `assets/work_details/`, `assets/home/`, `assets/site/` | Public generated or published media/assets. |
| `assets/data/docs/reports.json` | Generated public Docs Viewer report registry copy when read-only installs need it. |

Public route adapters for Docs Viewer should be minimal.
Docs Viewer shell source, management shell source, config, CSS, report runtime, and build/service code belong under `studio/docs-viewer/`.

## Source Moves

| Previous path family | Current / target path family | Notes |
| --- | --- | --- |
| `_docs/` | `studio/docs-viewer/source/studio/` | Studio docs scope source. |
| `_docs_library/` | `studio/docs-viewer/source/library/` | Library docs scope source. |
| `_docs_analysis/` | `studio/docs-viewer/source/analysis/` | Analysis docs scope source. |
| `assets/docs/interactive/` | `studio/docs-viewer/source-assets/interactive/` | Source interactive HTML assets; public copies should be explicit runtime/generated artifacts if needed. |
| `assets/docs-viewer/js/` | `studio/docs-viewer/runtime/js/` | Docs Viewer browser runtime and management modules. |
| `assets/docs-viewer/js/reports/` | `studio/docs-viewer/runtime/js/reports/` | Report browser modules. |
| `assets/docs-viewer/css/` | `studio/docs-viewer/assets/css/` | Docs Viewer CSS. |
| `assets/docs-viewer/data/docs-viewer-config.json` | `studio/docs-viewer/config/runtime/docs-viewer-config.json` | Source runtime config. |
| `assets/docs-viewer/data/docs-viewer-public-config.json` | `studio/docs-viewer/config/runtime/docs-viewer-public-config.json` | Source for generated/served public install config. |
| `assets/docs-viewer/data/ui-text.json` | `studio/docs-viewer/config/ui-text/ui-text.json` | Docs Viewer UI text. |
| `assets/data/docs/reports.json` source/config | `studio/docs-viewer/config/reports/reports.json` | Keep generated public copy outside `studio/` only as needed. |
| `_includes/docs_viewer_shell.html` | `studio/docs-viewer/runtime/shells/docs-viewer-shell.html` | Move shell source; public route adapters should not embed shell internals. |
| `_includes/docs_viewer_management_route.html` | `studio/docs-viewer/runtime/shells/docs-viewer-management-route.html` | Move management shell source. |
| `_includes/docs_viewer_readonly_route.html` | public minimal adapter plus Docs Viewer-owned shell source | Keep only required public adapter outside `studio/`. |
| `scripts/docs/` | `studio/docs-viewer/build/`, `studio/docs-viewer/server/`, `studio/docs-viewer/services/`, `studio/docs-viewer/config/scopes/` | Split by role while preserving the Docs Viewer boundary. |
| `scripts/build_docs.rb` | root wrapper to `studio/docs-viewer/build/build_docs.rb` | Root wrapper is optional convenience, not compatibility source. |
| `studio/docs-viewer/build/build_docs.rb` | `studio/docs-viewer/build/build_docs.rb` | Docs Viewer build implementation. |
| `studio/docs-viewer/build/build_search.rb` | `studio/docs-viewer/build/build_search.rb` | Docs Viewer search builder. |
| `_docs_catalogue/` | `studio/data/canonical/catalogue-markdown/` | Studio-owned canonical publishing Markdown. |
| `assets/studio/data/catalogue/` | `studio/data/canonical/catalogue/` | Canonical catalogue JSON source. |
| `assets/studio/data/catalogue_lookup/` | `studio/data/generated/catalogue-lookup/` | Derived editor read model; disposable cache remains under `var/`. |
| `assets/studio/data/ui_text/` | `studio/app/frontend/config/ui-text/` | Studio UI text/config for route modules. |
| `assets/studio/data/studio_config.json` | `studio/app/frontend/config/studio-config.json` | Browser runtime config source for Studio app. |
| `assets/studio/data/activity_contract.json` | `studio/data/config/runtime/activity-contract.json` | Studio runtime/data contract config. |
| `assets/studio/data/catalogue_field_registry.json` | `studio/data/config/catalogue/catalogue-field-registry.json` | Catalogue editor/config source. |
| `assets/studio/data/data_sharing_adapters*.json` | `studio/data/config/data-sharing/` | Data-sharing adapter config/schema. |
| `assets/studio/data/library_export_configs*.json` | `studio/data/config/data-sharing/` | Library export config/schema. |
| `assets/studio/data/tag_*.json` | `studio/data/canonical/analytics/` | Analytics/tag canonical data. |
| `assets/studio/data/work_storage_index.json` | `studio/data/generated/activity/` | Studio-only derived/read-model data. |
| `assets/studio/data/thumbnail_quality_preview.json` | `studio/data/generated/thumbnail-quality/` | Studio workflow review output. |
| `assets/studio/js/` | `studio/app/frontend/js/` | Studio browser modules. |
| `assets/studio/css/` | `studio/app/assets/css/` | Studio CSS. |
| `assets/studio/img/panel-backgrounds/` | `studio/app/assets/img/panel-backgrounds/` | Studio-only shell/route visual assets. |
| `assets/studio/img/thumbnail-quality/` | `studio/data/generated/thumbnail-quality/img/` | Studio workflow review assets. |
| `_docs_logs/entries/` | `studio/workflows/change-requests/logs/entries/` | Change request workflow source logs. |
| `_docs_logs/generated/` | `studio/workflows/change-requests/generated/` | Generated workflow output. |
| `_docs_logs/reports/` | `studio/workflows/change-requests/reports/` | Generated or workflow-facing reports. |
| `studio/workflows/change-requests/services/` | `studio/workflows/change-requests/services/` | Change request workflow services. |
| `_ui_catalogue_notes/` | `studio/ui-catalogue/notes/` | UI Catalogue notes source. |
| `_includes/ui_catalogue_notes/` | `studio/ui-catalogue/notes/includes/` | Notes include source if still needed. |
| `assets/ui-catalogue/` | `studio/ui-catalogue/assets/` | UI Catalogue assets. |
| `assets/docs/ui-catalogue/` | `studio/ui-catalogue/demos/` | UI Catalogue demo support. |
| `studio/ui-catalogue/` | `studio/ui-catalogue/demos/` and `studio/ui-catalogue/notes/` | Keep under Studio; remove Jekyll layout dependency in cleanup/move slices. |
| `_layouts/studio.html` | `studio/app/views/` or delete | Delete if no active route needs it after cleanup. |
| `_includes/studio_header_nav.html` | delete | Removed in `STSR-007`; Local Studio shell navigation is owned by the local app. |
| `_includes/studio_module_script.html` | delete | Removed in `STSR-007`; active Studio routes no longer use this Liquid entry-module helper. |
| `scripts/studio/` | `studio/app/server/` and `studio/app/views/` | Local app server, API adapters, runtime config, and view renderers. |
| `scripts/catalogue/` | `studio/services/catalogue/` | Catalogue source mutation, generation, validation, import, and projection services. |
| `scripts/analytics/` | `studio/services/analytics/` | Analytics/tag services and workflows. |
| `scripts/media/` | `studio/services/media/` | Media maintenance and preview workflows. |
| `scripts/search/build_search.rb`, `scripts/search/build_config.json` | `studio/services/catalogue/search/` | Catalogue search builder/config. |
| `scripts/search/adapter_registry.json` | `studio/commands/search-adapters.json` or split to owner configs | Root search wrapper may read owner configs; no old-path alias. |
| `scripts/build_search.rb` | root wrapper to owner-specific search builders | Wrapper chooses Studio Catalogue or Docs Viewer owner by scope. |
| former root check scripts | `studio/checks/` | Checks, projection contracts, source-boundary audits, and public-surface audits. |
| former root check runner | `studio/commands/run_checks.py` | Codex/developer test entrypoint; no public-site root wrapper. |
| `scripts/display_paths.py`, `scripts/local_env.py`, `scripts/pipeline_config.py`, `scripts/script_logging.py` | `studio/shared/python/` | Shared development/runtime helpers. |
| `scripts/jekyll_markdown_renderer.rb`, `scripts/render_markdown_with_jekyll.rb`, `scripts/jekyll_webrick_client_reset_filter.rb` | `studio/docs-viewer/build/` or `studio/shared/ruby/` | Place by final consumer during move. |
| `bin/local-studio` | root wrapper to `studio/commands/local-studio` | Deliberate convenience command. |
| `bin/public-site-build`, `bin/public-site-preview` | root wrappers to `studio/commands/public-site-build` and `studio/commands/public-site-preview` | Studio/Codex development tooling for the public site. |
| former root Python tests | `studio/tests/python/` | Python tests. |
| former root smoke tests | `studio/tests/smoke/` | Smoke tests. |
| former root fixtures | `studio/tests/fixtures/` or owner-local fixtures | Fixture ownership follows the tested owner. |

## Local Working Output

These paths are not source and do not need to move as tracked source:

| Current path family | Final treatment |
| --- | --- |
| `var/docs/`, `var/studio/`, `var/catalogue/` | Keep local working output under `var/`; retarget subpaths only where moved source requires it. |
| `var/docs/catalogue/import-staging/` | Keep as local staging output or retarget under a Studio workflow `var/` path. |
| `var/test-runs/`, `.pytest_cache/`, `__pycache__/`, `_site/`, `tmp/` | Generated/cache/build output; do not move as source. |

## Move Constraints

- Do not preserve old `assets/studio/...`, `assets/docs-viewer/...`, `_docs_*`, `_docs_logs/`, or `_docs_catalogue/` source paths through compatibility mounts or dual-read fallback logic.
- Move source files and update imports, config, static serving, route shells, tests, and docs to the new owner paths directly.
- Keep generated public outputs at their current public paths unless a later task explicitly changes a generated-output contract.
- Keep Docs Viewer internally cohesive under `studio/docs-viewer/`; do not scatter its source, runtime, CSS, services, config, or tests across generic Studio folders.
- Keep root command wrappers small and intentional. If a wrapper remains, its implementation belongs under `studio/`.

## Next Use

This layout remains the concrete source-boundary reference as move slices continue.
Move slices should update this document if a concrete path decision changes during implementation.
