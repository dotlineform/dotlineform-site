---
doc_id: config-admin-config-json
title: Admin Config JSON
added_date: 2026-07-15
last_updated: 2026-07-15
parent_id: admin
viewable: true
---
# Admin Config JSON

## Source Contract

`admin-app/app/frontend/config/admin-config.json` owns Admin route registration and sibling-link defaults.

Each route registers:

- stable route ID, label, title, and path;
- HTML template and JavaScript entry module;
- shell type;
- navigation visibility.

`admin_app_config.py` validates required fields, unique normalized paths, file existence, shell type, and boolean navigation before serving the app.

## Runtime Projection

The server copies checked config and adds `app.runtime` with asset version, route/service metadata, and known local output paths. Service endpoints are code-owned rather than editable JSON because they must stay aligned with server dispatch.

The browser loads the projection once and resolves routes/templates from it. Do not add a second JavaScript route inventory.

## Change Method

1. add or change the route template and script;
2. update the checked route entry;
3. update the appropriate API adapter only if the route needs a new server capability;
4. cover config validation, shell dispatch, and route-ready behavior;
5. update [Local Admin App](/docs/?scope=studio&doc=local-admin-app) only when the capability/ownership boundary changes.

## Weak Spot

Runtime config currently exposes route data as checked `app.routes` plus a derived `app.runtime.views` list. Consumers should prefer one registry method; new features should not extend both shapes independently.
