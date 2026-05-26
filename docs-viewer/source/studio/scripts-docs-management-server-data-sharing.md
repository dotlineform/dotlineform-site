---
doc_id: scripts-docs-management-server-data-sharing
title: Docs Management Service Data Sharing (Retired)
added_date: 2026-05-19
last_updated: 2026-05-26
parent_id: scripts-docs-management-server
sort_order: 15300
---
# Docs Management Service Data Sharing (Retired)

Docs Viewer no longer publishes Data Sharing HTTP endpoints.
The transitional `GET /data-sharing/returned-packages`, `POST /data-sharing/prepare`, `POST /data-sharing/review`, and `POST /data-sharing/apply` routes were removed after the Local Studio same-origin API became the durable browser boundary.

Current ownership:

- Studio owns the Data Sharing pages and API endpoints under `/studio/api/data-sharing/...`.
- `data-sharing/` owns shared workflow dispatch, adapter registry/config loading, schemas, path contracts, package I/O, and domain adapters.
- Docs Viewer still owns docs-domain helpers for Library generated reads, returned-package review, source writes, backups, and docs/search rebuild follow-through.
- The documents adapter calls those docs-domain helpers in-process through `data-sharing/data_sharing/adapters/documents/adapter.py`; it does not route through Docs Viewer HTTP.

Use [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing) and [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec) for the current endpoint contract.
