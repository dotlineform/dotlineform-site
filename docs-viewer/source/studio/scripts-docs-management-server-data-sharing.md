---
doc_id: scripts-docs-management-server-data-sharing
title: Docs Management Service Data Sharing (Retired)
added_date: 2026-05-19
last_updated: 2026-05-30
parent_id: scripts-docs-management-server
---
# Docs Management Service Data Sharing (Retired)

Docs Viewer no longer publishes Data Sharing HTTP endpoints.
The transitional `GET /data-sharing/returned-packages`, `POST /data-sharing/prepare`, `POST /data-sharing/review`, and `POST /data-sharing/apply` routes were removed before Data Sharing moved to the standalone Local Analytics app.

Current ownership:

- Analytics owns the Data Sharing pages and API endpoints under `/analytics/api/data-sharing/...`.
- `data-sharing/` owns shared workflow dispatch, adapter registry/config loading, schemas, path contracts, package I/O, and domain adapters.
- Docs Viewer still owns docs-domain helpers for Library generated reads, returned-package review, source writes, and docs/search rebuild follow-through.
- The documents adapter calls those docs-domain helpers in-process through `data-sharing/data_sharing/adapters/documents/adapter.py`; it does not route through Docs Viewer HTTP.
- Local Studio does not provide Data Sharing API compatibility routes.

Use [Data Sharing](/docs/?scope=studio&doc=data-sharing) and [Analytics Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec) for the current endpoint contract.
