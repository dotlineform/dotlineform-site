---
doc_id: scripts-main-pipeline
title: Build Catalogue
added_date: 2026-04-18
last_updated: "2026-05-09 21:28"
sort_order: 6000
---
# Deprecated: Build Catalogue

Status:

- retired workbook-led pipeline reference
- kept only as an archive stub so old docs links do not break

`scripts/build_catalogue.py` has been removed and is not part of the live catalogue workflow. Current catalogue metadata is maintained as canonical JSON source under `assets/studio/data/catalogue/`, and runtime artifacts are refreshed through the scoped JSON build path.

Use:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id <work_id>
```

Add `--write` only when intentionally applying the generated changes.

Current references:

- [Build Catalogue JSON](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
