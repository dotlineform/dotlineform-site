---
doc_id: analytics
title: Analytics
added_date: "2026-05-06 18:19"
last_updated: 2026-06-02
parent_id: ""
---
# Analytics

Analytics is a standalone local app boundary. [analysis](/analysis/) is the public-facing Docs Viewer for this data domain.

Run Analytics with:

```bash
bin/local-analytics
```

Default local route:

- `http://127.0.0.1:8766/analytics/`

Analytics owns:

- tag groups,
- tag registry,
- tag aliases,
- series tags,
- series tag editing,
- Data Sharing routes/APIs,
- semantic-reference product direction and future Analytics-hosted maintenance modules,
- document analysis,
- future visualisation workflows.

Current source boundary:

- `analytics-app/app/server/analytics_app/` owns the Local Analytics HTTP server, route views, runtime config projection, static serving, tag APIs, and Data Sharing API dispatch.
- `analytics-app/app/server/analytics_app/tag_services/` owns reusable tag-domain source path contracts, validation, planning, dry-run/write transactions, backups, route constants, and compact activity projection.
- `analytics-app/app/frontend/` owns Analytics browser modules, route modules, UI text, and runtime config.
- `analytics-app/app/assets/` owns Analytics-only CSS and route assets.
- `analytics-app/tests/` owns Analytics route/API smoke tests and focused Python endpoint tests.
- `analytics-app/data/canonical/` owns canonical tag source data. Raw local browser access, where useful for diagnostics or smoke tests, is under `/analytics/data/canonical/...`.
- `data-sharing/` owns the headless Data Sharing registry, config, workflow dispatch, package I/O, and domain adapters used by Analytics.

Semantic-reference note:

- current `[[ref:...]]` token parsing, generated relationship artifacts, and the management report are still implemented in Docs Viewer because the tokens are authored in Docs Viewer source documents
- Analytics owns the direction for future semantic-reference target support, tag integration, editor support data, document analysis, and visualisation/reference modules
- [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2) tracks the boundary alignment work before expanding the feature
