---
doc_id: config-studio-ui-text-json
title: Studio UI Text Config
added_date: 2026-06-02
last_updated: 2026-06-02
parent_id: studio
viewable: true
---
# Studio UI Text Config

Config files:

- `studio/app/frontend/config/ui-text/activity-log.json`
- `studio/app/frontend/config/ui-text/bulk-add-work.json`
- `studio/app/frontend/config/ui-text/catalogue-field-registry-review.json`
- `studio/app/frontend/config/ui-text/catalogue-moment-editor.json`
- `studio/app/frontend/config/ui-text/catalogue-series-editor.json`
- `studio/app/frontend/config/ui-text/catalogue-status.json`
- `studio/app/frontend/config/ui-text/catalogue-work-detail-editor.json`
- `studio/app/frontend/config/ui-text/catalogue-work-editor.json`
- `studio/app/frontend/config/ui-text/project-state.json`
- `studio/app/frontend/config/ui-text/studio-audits.json`
- `studio/app/frontend/config/ui-text/studio-risk.json`
- `studio/app/frontend/config/ui-text/studio-works.json`

## Contract Role

These files hold route-scoped visible copy for Local Studio browser modules.
They keep button labels, empty states, status messages, modal labels, and route-specific copy out of route controllers.

They do not define route ownership, service endpoints, generated data schemas, write behavior, or public-site URLs.

## What Reads Them

`studio/app/frontend/js/studio-config.js` loads a scoped bundle through `loadStudioConfigWithText(group)`.
The configured bundle URL comes from `paths.data.ui_text.<group>` in `studio/app/frontend/config/studio-config.json`.

Route modules then read strings with `getStudioText(config, "<group>.<key>", fallback, tokens)`.
Fallback copy remains in the caller so a missing text bundle does not prevent route boot.

## Edit Class

These files are maintainer-editable copy config.
They are safe to edit for wording changes, but keys should be changed only with the route module that reads them.

Do not add domain behavior or path policy here.
If a string implies a service, endpoint, route, or build contract, the underlying behavior belongs in the owning service or route module.

## Cleanup Review

For each bundle:

- verify the group key exists under `paths.data.ui_text`
- search for `getStudioText(..., "<group>.` and remove unused keys
- remove bundle files for retired routes only after their route and UI-text path are gone
- keep route names aligned with `app.routes` and route-local module names

Current cleanup status:

- `site-series-index.json` was removed after active call-site review found no Local Studio route consuming `paths.data.ui_text.site_series_index`
