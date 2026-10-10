---
draft: false
doc_id: d-20260422-000000-fb2894
title: Catalogue Services
added_date: "2026-04-22 00:00:00"
last_updated: "2026-10-10 10:42:03"
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

`catalogue_write_service.py` dispatches Work, Series, Gallery, bulk and delete operations. The deletion service carries its already loaded before/after canonical records into the shared completion owner without repeated source reads. Catalogue publication and document generation belong to Docs services, rather than separate Studio media-publish API actions.

| Responsibility | Owner |
| --- | --- |
| Canonical Save completion and known mutation selections | `catalogue_output_service.py` prepares required media, persists the updates contribution and returns current editor records. |
| Projects-owned staged image/download paths | `catalogue_staged_media.py`; Work `image_staged` and per-download `staged` independently select staging or Working. |
| Exact queue validation and persistence | `catalogue_pending_state.py`; schemas and headers belong to `catalogue_pending_updates.py` and `catalogue_pending_publication.py`. |
| Updates accumulation | `catalogue_pending_updates.py`; mutation owners reset their known affected entries to false and mark shared output pending. |
| Refresh and status | `catalogue_refresh_service.py`; handoff completes each selected Work before true readiness, and full completion clears shared pending and advances the last Refresh time. Status reads only the queue. |
| Catalogue source/document generation | Docs `docs_catalogue_regeneration.py`; true-readiness entries complete before publication merge and updates removal. Normal Regenerate is queue-only. |
| Completed publication contributions | `catalogue_pending_publication.py`; Regenerate, design maintenance and Docs exact-document Rebuild merge through this owner while preserving initialized Publish progress and timestamps. |
| Per-Work Preview and repository/R2 Deploy | Docs `docs_catalogue_publication.py`; Publish advances `preview_done`, removes completed entries and timestamps completion of a nonempty Work queue. |
| Final shared Publish | Docs `docs_publish.py`, `docs_prepare_preview.py` and `docs_deploy_repo.py`; one shared pass follows the Work queue, including when initially empty. |

[Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns updates schema `catalogue_updates_pending_v3`, field ownership and readiness. [Catalogue Deployment](Catalogue_Deployment.md) owns publication schema `catalogue_publish_pending_v3`, Preview progress, exact media selection and failure behavior. Both queue files live directly below configured Docs Working storage; their headers are written first. No separate Refresh receipt or Catalogue/configuration hash determines readiness.

## Transactions And Failure

Canonical source is below `studio/data/canonical/catalogue/`. `catalogue_source.py` owns loading, normalization, serialization and validation; focused planners own changes; `catalogue_transactions.py` owns validated single- and multi-file writes. Saves check revisions. Work deletion targets selected IDs, reads current records and memberships once, validates the resulting data and writes the complete removal together. Series deletion keeps its existing revision and empty-membership checks.

Local completion follows canonical persistence. Save stages required media, records exact mutation effects in the private updates queue and returns current editor records. Delete captures its media descriptor before canonical removal, persists downstream selection and cleans owned staging. Failures retain canonical success and identify incomplete completion. Refresh consumes selected false-readiness entries rather than discovering changes from generated-file comparisons; [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the detailed contract.

Work Delete confirms exact selected identities, removes canonical records and Gallery memberships together, retains Gallery/Series definitions and carries the captured image/download deletion descriptor through Refresh, Regenerate and Publish. Known owned media is removed at each boundary, without cross-Work ownership scans. Missing owned deletion targets succeed. Browser confirmation does not replace server identity, data or write validation.

## Safety And Extension

- Reads and writes are allowlisted; request values cannot select arbitrary repository paths.
- Media discovery uses the exact configured source identity and confines resolved paths below its root.
- Generated output and staging stay within their configured external boundaries; the archive is excluded.
- Credentials stay server-side. Operational logs under `var/studio/catalogue/logs/` record compact identities, state and errors.

Extend the focused service that owns the transaction and use the existing completion owner for downstream effects. Add a browser endpoint only for a distinct author operation and update the API inventory. Test work for validation, applicable revisions, path confinement and partial completion requires its separately reviewed specification.

The HTTP adapter combines reads, mutation dispatch and local-machine capabilities. Some source and generated projections still load the whole Catalogue; preserve exact affected-output ownership when improving that cost.
