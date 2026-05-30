---
doc_id: data-sharing
title: Data Sharing
added_date: "2026-05-13 17:16"
last_updated: 2026-05-30
parent_id: ""
---
# Data Sharing

Data Sharing is now hosted by the standalone Local Analytics app.
Run it with:

```bash
bin/local-analytics
```

Default local routes:

- `http://127.0.0.1:8766/analytics/data-sharing/prepare/?mode=manage`
- `http://127.0.0.1:8766/analytics/data-sharing/review/?mode=manage`

Default local APIs:

- `/analytics/api/data-sharing/health`
- `/analytics/api/data-sharing/selectable-records`
- `/analytics/api/data-sharing/returned-packages`
- `POST /analytics/api/data-sharing/prepare`
- `POST /analytics/api/data-sharing/review`
- `POST /analytics/api/data-sharing/apply`

Runtime packages, returned-package staging, review artifacts, and backups continue to use `var/studio/data-sharing/<domain>/...` as the local artifact contract.
Retired Studio paths under `/studio/data-sharing/...` and `/studio/api/data-sharing/...` should not be recreated.
