---
draft: false
doc_id: d-20260607-222033-d9b8b1
title: Source Config Endpoints
added_date: 2026-06-07 22:20:33
last_updated: "2026-10-15"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Source Config Endpoints

`GET /docs/source-config` and both `GET` and `POST /docs/source-config-settings` are retired without aliases. The Settings menu action, modal, browser workflow, server settings owner and capability flags are removed.

The single top-level `default_doc_id` in `docs-viewer/config/workspace/docs-workspace.json` is design-time configuration shared by local and public readers. [Configuration And Extension Points](Configuration_And_Extension_Points.md#workspace-and-target-contracts) owns its editing and browser-projection workflow. Normal authoring, Delete and Publish do not edit the setting.
