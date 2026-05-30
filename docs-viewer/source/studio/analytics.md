---
doc_id: analytics
title: Analytics
added_date: "2026-05-06 18:19"
last_updated: 2026-05-30
parent_id: ""
---
# Analytics

Analytics is now a standalone local app boundary.
Run it with:

```bash
bin/local-analytics
```

Default local route:

- `http://127.0.0.1:8766/analytics/`

Analytics owns tag groups, tag registry, tag aliases, series tags, series tag editing, Data Sharing routes/APIs, semantic-reference maintenance, document analysis, and future visualisation workflows.
Retired Studio paths under `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, and `/studio/api/data-sharing/...` should not be recreated.

[analysis](/analysis/) is the public-facing Docs Viewer for this data domain.
