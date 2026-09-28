---
draft: false
doc_id: d-20260401-000000-a11bf3
title: Catalogue Architecture
added_date: "2026-04-01 00:00:00"
last_updated: "2026-09-28 13:01:30"
parent_id: d-20260423-000000-d015e6
---

# Catalogue Architecture

## Current Shape

Studio owns canonical Catalogue editing. One Work belongs to exactly one Series and may belong to multiple Galleries; Series and Galleries may be empty. Canonical Work, Series, Gallery and membership sources live under `studio/data/canonical/catalogue/`. Detail records, Catalogue publication state and parallel Catalogue Markdown prose are retired.

```text
canonical Works, Series, Galleries and memberships
  -> validated Studio Save + required shared local media
  -> live canonical Studio editor/search views
  -> explicit Refresh Catalogue: Working generated JSON + private Docs metadata
  -> Docs Publish: completed Preview and configured public destinations
```

[Catalogue Source Model](Catalogue_Source_Model.md) owns exact identities, fields and relationships. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns operation completion and reader timing. [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) owns generated JSON shapes; [Catalogue Deployment](Catalogue_Deployment.md) owns public distribution.

## Separate Authorities

The canonical source is the editable authority. Studio Work/Series search and focused editor reads are live projections of that source, so Save does not depend on a persisted lookup export. Save prepares required primary images, thumbnails and downloads in the configured shared Docs assets; those bytes and canonical image versions can be current before generated JSON is refreshed.

Refresh Catalogue reconciles complete replaceable Work, Series and Gallery records, compact discovery indexes, media policy and private Docs report metadata under `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. Generated output is a reader projection, not another editable source. Docs Viewer local Catalogue, subject and report readers can lag behind Save until Refresh completes. Public readers use the separately published Catalogue revision; Docs Publish does not run Refresh or enforce its receipt.

The inactive manual `studio/data/generated/catalogue-lookup/` export and one-time Gallery converter still reference persisted lookup files. Neither is an active Studio editor or Docs reader dependency. Retiring those code paths requires a separately scoped review. The frozen legacy `site/archive/` payloads and media are outside active generation.

## Change Method And Weak Spots

Change canonical fields through the source definition, serializer, validation, editor and affected projections together. Keep exact IDs and one owner for each relationship; do not infer Gallery or document associations from titles, filenames or routes. Use focused service/generator evidence for the changed boundary.

Canonical validation and complete Refresh still process the full corpus. Save and Refresh latency has not been measured. A failed Refresh can leave partial generated files but no current receipt; rerun it after fixing the cause. Publishing while Refresh is needed can capture older Catalogue JSON with current media. Shared and remote media cleanup is separate from Save, Refresh and Publish.
