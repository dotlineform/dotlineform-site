---
doc_id: risks
title: risks
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
---

## Risk evidence pack

Use [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) for current deterministic reruns.
The old ad hoc `find`, `wc`, and inline Python snippets have been replaced by the `script-family-inventory.json` producer.

Run this from `dotlineform-site/`:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/risk_evidence_pack.py --app all --area script-family-inventory --write
```

Read:

```text
var/admin/risk/runs/<run-id>/script-family-inventory.json
```

When updating this doc from an evidence pack, keep the three risk classifications separate.
A large file can be low performance risk if it is rarely run, and a small file can be high performance risk if it sits on a repeated save or rebuild path.


# old evidence

## Family Risk Matrix

| Area | Files | Lines | Maintenance | Structure and consistency | Performance | Main reason |
| --- | ---: | ---: | --- | --- | --- | --- |
| `studio/services/catalogue/` | 48 | 17,013 | high | medium | high | Large source/build/write surface with multiple generated artifact families, field-aware build planning, media derivation, lookup refreshes, Python catalogue search rebuilds, publication flows, prose rendering, and local write-service orchestration. |
| `docs-viewer/` | 34 | 13,266 | high | medium | medium | Docs build, import, export, management mutations, generated reads, live rebuild, and docs search are now Python-owned. Targeted docs payload/search rebuilds reduce routine write cost, while builder/watcher/management contracts and resolver-data fallbacks still need care. |
| `studio/` | 18 | 5,165 | medium | medium | low | Catalogue helper entrypoints should remain orchestration surfaces rather than owning domain behavior. |
| `admin-app/checks/` | 10 | 3,647 | medium | medium | medium | Audit scripts intentionally span many site contracts, especially `audit_site_consistency.py`; risk grows when new checks are added without grouping or shared report contracts. |
| `analytics-app/app/server/analytics_app/` | 9 | 2,653 | medium | medium | low | Analytics API and Data Sharing dispatch stay Python-owned; keep route adapters thin and domain behavior in focused helper modules. |
| `studio/app/server/studio/` | 8 | 2,352 | medium | medium | low | Shared Studio services are small, but catalogue, audit, risk, and Activity mechanics overlap with docs and catalogue services. |
| `analytics-app/app/server/analytics_app/tag_services/` | 10 | 2,131 | medium | medium | low | Analytics-owned tag helper package for source path contracts, validation, planning, dry-run/write transactions, backups, route constants, and compact activity projection. Data Sharing and tag import/apply flows remain broad enough to watch. |
| `data-sharing/` | 19 | 1,947 | medium | medium | low | Headless Data Sharing adapters are Python-owned and should keep package I/O, adapter registry behavior, and apply boundaries explicit. |


### Check and audit scripts

- Group `audit_site_consistency.py` checks by source family and report section before adding many more checks.
- Keep check output machine-readable first, with Markdown as a presentation layer.
- Add focused tests for check helpers when a check becomes complicated enough to have edge cases.
- Keep `run_checks.py` as the user-facing profile runner, but avoid making it own check logic directly.