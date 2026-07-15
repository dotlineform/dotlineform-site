---
doc_id: scripts-catalogue-lookup
title: Catalogue Lookup Export
added_date: 2026-04-17
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Lookup Export

## Command

Preview or write the complete Studio lookup family:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/export_catalogue_lookup.py
$HOME/miniconda3/bin/python3 studio/services/catalogue/export_catalogue_lookup.py --write
```

Defaults:

- source: `studio/data/canonical/catalogue/`
- output: `studio/data/generated/catalogue-lookup/`

`--source-dir` and `--lookup-dir` override those roots for focused testing or migration work.

## What It Produces

The exporter builds Work search, Series search, and focused Series list projections used by Studio. They are non-canonical and can be regenerated from catalogue source.

Focused Work and detail editor records are service projections, not generated per-record lookup files. The [Catalogue Indexes And Payloads](/docs/?scope=studio&doc=data-models-catalogue-indexes) page explains that read split.

## Normal Refresh Path

Catalogue mutations use `catalogue_lookup_refresh.py` to select a focused, related, or complete refresh. Run the exporter directly when a deliberate full refresh is needed outside a mutation workflow.

`catalogue_lookup.py` owns payload schemas and serializers; `export_catalogue_lookup.py` owns only CLI input/output and full-export orchestration.
