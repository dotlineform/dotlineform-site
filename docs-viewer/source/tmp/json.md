---
doc_id: json
title: "json"
added_date: 2026-06-09
last_updated: 2026-06-09
---

## keys

`jq 'keys' admin-app/checks/config/admin-checks.json`

```
[
  "areas",
  "config_id",
  "families",
  "reports",
  "routes",
  "scopes",
  "source",
  "version"
]
```

## scopes

`jq '{scopes}' admin-app/checks/config/admin-checks.json`

```
{
  "scopes": {
    "admin": {
      "label": "Admin",
      "include": [
        "admin-app/"
      ],
      "exclude": [
        "admin-app/**/__pycache__/**"
      ]
    },
    "analytics": {
      "label": "Analytics",
      "include": [
        "analytics-app/"
      ],
      "exclude": [
        "analytics-app/**/__pycache__/**",
        "analytics-app/data/canonical/"
      ]
    ...
```

show all at once:

`jq '{source, scopes, families, areas, routes, reports}' admin-app/checks/config/admin-checks.json`

## families

```
"families": {
    "runtime-js": {
      "label": "Runtime JavaScript",
      "include": [
        "admin-app/app/frontend/js/",
        "admin-app/ui-catalogue/assets/js/",
        "analytics-app/app/frontend/js/",
        "assets/js/",
        "docs-viewer/runtime/js/",
        "studio/app/frontend/js/"
      ]
    },
```

list the families:

`jq -r '.families | keys[]' admin-app/checks/config/admin-checks.json`

```
admin-route
build
config
public-route
runtime-js
services
source-docs
tests
```

`jq -r '.families | to_entries[] | "\(.key): \(.value.label)"' admin-app/checks/config/admin-checks.json`

```
runtime-js: Runtime JavaScript
services: Services
build: Build scripts
source-docs: Source documents
config: Configuration
tests: Tests and smokes
admin-route: Admin routes
public-route: Public routes
```