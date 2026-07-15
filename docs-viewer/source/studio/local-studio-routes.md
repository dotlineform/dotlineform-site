---
doc_id: local-studio-routes
title: Local Studio Routes
added_date: 2026-06-02
last_updated: 2026-07-15
summary: Exact mounted Local Studio route, template, and route-script inventory from the checked-in registry.
parent_id: studio
viewable: true
---
# Local Studio Routes

## Authority

`studio/app/frontend/config/studio-config.json` `app.routes` is the source registry. `studio_app_config.py` validates it before the server mounts any shell path or publishes runtime config.

## Mounted Routes

| route id | path | template | script | purpose |
| --- | --- | --- | --- | --- |
| `studio_home` | `/studio/` | `studio-home.html` | `studio-home.js` | catalogue workflow entry links |
| `project_state` | `/studio/project-state/` | `project-state.html` | `project-state.js` | project/catalogue comparison report |
| `bulk_add_work` | `/studio/bulk-add-work/` | `bulk-add-work.html` | `bulk-add-work.js` | workbook import preview and apply |
| `catalogue_field_registry` | `/studio/catalogue-field-registry/` | `catalogue-field-registry.html` | `catalogue-field-registry-review.js` | field/build-impact review |
| `catalogue_status` | `/studio/catalogue-status/` | `catalogue-status.html` | `catalogue-status.js` | draft and incomplete record list |
| `studio_works` | `/studio/studio-works/` | `studio-works.html` | `studio-works.js` | work browser |
| `catalogue_series_editor` | `/studio/catalogue-series/` | `catalogue-series.html` | `catalogue-series-editor.js` | series create/edit workflow |
| `catalogue_work_editor` | `/studio/catalogue-work/` | `catalogue-work.html` | `catalogue-work-editor.js` | work and embedded detail-section workflow |

Template paths are rooted under `studio/app/frontend/routes/`; scripts are under `studio/app/frontend/js/`.

There are no separate Work Detail or Moment editor routes in the current registry. Work detail sections are managed inside the Work editor. Public Moments remain a public catalogue surface, not a mounted Local Studio editor.

## Route Contract

All mounted routes use the shared template shell:

```text
registered path
  -> studio-shell.html
  -> studio-app.js
  -> configured route template
  -> configured route script
```

Templates own stable DOM; scripts own behavior, dynamic rendering, local API calls, and route ready/busy state. All current `nav` flags are false, so Studio home provides the workflow entry list rather than a global primary navigation menu.

## Changing The Inventory

- update the registry, template, and script together
- keep route paths beneath `/studio/`
- remove retired routes rather than leaving aliases or template stubs
- verify server config validation and the focused route-boot smoke
- update this inventory only when the mounted route set or ownership actually changes

[Studio Runtime](/docs/?scope=studio&doc=studio-runtime) owns the reusable shell architecture. Sibling app routes belong to their own entry documents.
