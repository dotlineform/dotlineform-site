---
doc_id: risk-route-exposure-evidence-plan
title: Risk Route Exposure Evidence - Plan
added_date: 2026-05-31
last_updated: 2026-06-07
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Route Exposure Evidence - Plan

This document defines the planned `route-exposure.json` producer for [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack).

## Current Status

Status: planned.

`route-exposure.json` is a planned producer artifact tracked by [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers). The runner currently omits it.

The producer should answer which routes are public, local-only, manage-only, or retired, and which runtime assets and service surfaces each route exposes.

## Purpose

Route exposure evidence is useful when a risk question depends on:

- public vs local-only runtime behavior
- management UI exposure
- loaded JavaScript/CSS/config surfaces
- backend API availability
- retired or compatibility routes still being referenced
- public read-only routes accidentally loading management-only assets

## Inputs

The producer should read checked-in source and generated-safe config only.

Potential inputs:

| Input | Evidence |
| --- | --- |
| Studio route registry/config | Local Studio route ids, paths, route types, shell ownership, and admin/home navigation. |
| Analytics route config | Analytics route ids, data-sharing route paths, and local API exposure. |
| Docs Viewer route config | `/docs/`, `/library/`, `/analysis/`, manage/public intent, config payloads, and runtime asset roots. |
| Public route files/config | Public pages, route stubs, public catalogue/search/work/moment/series routes. |
| Local app server adapters | API endpoint paths and whether they are read, write, audit, risk, management, or generated-read surfaces. |
| Static asset references | Script/config/CSS files loaded by route shells or app registries. |
| Retired route records | Paths or files that should not be active route targets. |

## Proposed Artifact Shape

```json
{
  "status": "collected",
  "routes": [
    {
      "route_id": "studio-risk",
      "app": "studio",
      "path": "/studio/risk/",
      "exposure": "local-manage",
      "route_type": "javascript-shell",
      "loaded_scripts": ["studio/app/frontend/js/studio-risk.js"],
      "api_surfaces": ["/studio/api/risk/..."],
      "notes": []
    }
  ],
  "api_surfaces": [],
  "retired_path_findings": [],
  "warnings": []
}
```

## Classification Rules

Use stable exposure labels:

| Label | Meaning |
| --- | --- |
| `public-read-only` | Public route, no local write capability expected. |
| `local-manage` | Local manage-mode route with write or operational authority behind backend endpoints. |
| `local-read-only` | Local route without write authority. |
| `generated-read` | Static/generated JSON read surface. |
| `local-api-read` | Local backend read endpoint. |
| `local-api-write` | Local backend write endpoint with validation and write allowlists. |
| `retired` | Historical route/file retained as reference only. |

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory source-of-truth route/config files for Studio, Analytics, Docs Viewer, UI Catalogue, and public-site routes. |
| 2 | planned | Define a small route exposure schema with route id, app, path, exposure label, loaded scripts, config payloads, API surfaces, and warnings. |
| 3 | planned | Implement the producer in `admin-app/checks/risk_evidence_pack.py` or a focused helper it calls. |
| 4 | planned | Add retired-path checks for route ids/files that should not be active. |
| 5 | planned | Add public/manage leakage checks, starting with Docs Viewer public read-only routes and management-only assets. |
| 6 | planned | Add tests using small fixture route/config files. |
| 7 | planned | Summarize route counts and warnings in `summary.json` and `summary.md`. |
