---
draft: false
doc_id: d-20260503-202500-316d29
title: Package Return Parser
added_date: "2026-05-03 20:25:00"
last_updated: "2026-08-14 20:31:55"
parent_id: d-20260424-000000-50b63f
---
# Package Return Parser

This CLI parses a staged trusted document return and prints the validation report. The operational Review and Import controls have separate owners. [Docs Review](Docs_Review.md) · [Import a trusted collection](Docs_Import.md#import-a-trusted-collection)

## Commands

Place the returned JSON or JSONL file in the configured Projects workspace's `data-sharing/import-staging/` folder. From the repository root, use the project interpreter.

```bash
python3 docs-viewer/services/docs_import.py --file document-content.jsonl
```

Add `--no-records` to omit normalized records from the result. Exit status `0` indicates a valid result, `2` a failed validation report and `1` an execution error. The parser resolves the return from its staged file and saved prepare-run identity. Canonical application and document generation belong to explicit Import. [CLI implementation](../../docs-viewer/services/docs_import.py) · [Package provenance](Package_Export_Metadata.md)
