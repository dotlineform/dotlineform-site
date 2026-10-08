---
draft: false
doc_id: d-20260422-000000-fb2894
title: Catalogue Services
added_date: "2026-04-22 00:00:00"
last_updated: "2026-10-08 11:05:40"
parent_id: d-20260423-000000-d015e6
---

# Catalogue Services

## Ownership

Catalogue services provide Local Studio's validated canonical reads and mutations, Work subfolder creation, exact deletion, confined media discovery and local Save completion. The loopback API is `/studio/api/catalogue/...`; [Local Studio APIs](Local_Studio_APIs.md) owns the exact route inventory.

```text
browser command
  -> studio_catalogue_api.py
  -> registered mutation service
  -> combined validation and canonical transaction
  -> catalogue_output_service.py
  -> required local media and current editor records
```

`catalogue_write_service.py` dispatches Work, Series, Gallery, bulk and delete operations. The deletion service carries its already loaded before/after canonical records into the shared completion owner, without repeated source reads or media work. There are no separate Catalogue publication, Build or media-publish API actions.

## Transactions And Failure

Canonical source is below `studio/data/canonical/catalogue/`. `catalogue_source.py` owns loading, normalization, serialization and validation; focused planners own changes; `catalogue_transactions.py` owns validated single- and multi-file writes. Saves check revisions. Work deletion targets selected IDs, reads current records and memberships once, validates the resulting data and writes the complete removal together. Series deletion keeps its existing revision and empty-membership checks.

Local completion runs after persistence. Save completes required shared media and returns current editor records; deletion invalidates Catalogue freshness without media preparation. A completion failure preserves the saved canonical outcome and identifies the unfinished step. Generated Catalogue JSON and private Docs metadata update through the separate awaited Refresh Catalogue operation. See [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md).

Work Delete confirms the selected identities in the browser, then sends one apply request for single or multiple selection. Its service removes current Work records and their Gallery memberships in one transaction, retaining Gallery/Series definitions and shared images/files. The preliminary Catalogue delete-preview route and generic `id` request aliases are retired. Browser confirmation does not replace server input, data or write-boundary validation.

## Safety And Extension

- Reads and writes are allowlisted; request values cannot select arbitrary repository paths.
- Media discovery uses the exact configured source identity and confines resolved paths below its root.
- Generated output and staging stay within their configured external boundaries; the archive is excluded.
- Credentials stay server-side. Operational logs under `var/studio/catalogue/logs/` record compact identities, state and errors.

Extend the focused service that owns the transaction and use the existing completion owner for downstream effects. Add a browser endpoint only for a distinct author operation and update the API inventory. Test work for validation, applicable revisions, path confinement and partial completion requires its separately reviewed specification.

The HTTP adapter combines reads, mutation dispatch and local-machine capabilities. Some source and generated projections still load the whole Catalogue; preserve exact affected-output ownership when improving that cost.
