---
doc_id: data-sharing-overview
title: Data Sharing Overview
added_date: 2026-07-15
last_updated: 2026-07-15
parent_id: data-sharing
viewable: true
---
# Data Sharing Overview

## What Data Sharing Is

Data Sharing is a headless, adapter-driven workflow for sending selected canonical data out of the repository and safely understanding returned files. Analytics provides its browser and HTTP host; domain owners provide canonical reads, validation, and writes.

It is not a generic file importer, background synchronization system, or second owner of documents/tags.

## Canonical Operations

- `prepare` — select canonical records and write an outbound package plus provenance/context.
- `list_returned` — list staged JSON/JSONL files that have resolvable export metadata.
- `review` — parse/validate a returned package and write review evidence or a validated read-only projection.
- `apply` — preview then explicitly confirm a narrow domain-owned mutation.

Selectable-record lookup supports prepare but is not a fifth registry operation.

## Round-Trip Path

```text
canonical domain source
  -> adapter prepare profile/family
  -> exports/<package> + meta/<export_id>.meta.json
  -> external review/edit
  -> operator places returned file in import-staging/
  -> export_id resolves trusted internal metadata
  -> registry dispatches domain review
  -> preview/report or immutable Docs Review package
  -> optional narrow confirmed apply
  -> canonical domain helper + focused follow-through
```

Every runtime artifact root is resolved beneath `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`. `services/paths.py` validates the workspace, marker paths, containment, distinct roots, and readable/writable status. The checked config never stores a machine-specific absolute path.

## Authority Boundaries

### Registry And Dispatch

`data-sharing/config/adapters.json` maps `(data_domain, canonical operation)` to one adapter and declares server-side path/source/write/capability policy. `data_sharing_adapters.py` validates/resolves it at the Analytics boundary. `services/dispatch.py` selects a registered handler.

### Adapter Families

An adapter translates generic operations into one domain. A family owns one source/package/review/apply shape. Profiles select/configure an existing family; they do not create behaviour by declaration alone.

### Browser

Analytics receives a whitelisted projection from `/analytics/api/data-sharing/config`. Paths, source/write targets, activity metadata, package internals, and implementation modules stay server-side.

### Canonical Writes

Documents use Docs Viewer source/write/rebuild helpers. Tags use Analytics tag planners/transactions. Data Sharing orchestrates those owners but does not bypass them.

## Extension Method

- Existing family, different safe options: add/change a profile and its validation tests.
- New source/package/review/apply shape: add a family plus detection, registry capability, artifacts, UI projection where needed, and focused tests.
- New domain: add one adapter, register all implemented operations explicitly, provide canonical domain helpers, and prove the browser projection leaks no server-only paths.
- New apply action: define one narrow candidate field/action, dry-run evidence, confirmation, domain write boundary, result counts, activity, and recovery expectation.

## Known Gaps And Pressure Points

- The registry combines dispatch/security policy with UI labels, confirmations, and result-display metadata; it is useful but large and easy to mistake for implementation.
- Documents prepare profiles have semantic runtime validation but no standalone schema.
- Returned files depend on retained internal metadata keyed by `export_id`; a copied package without its metadata cannot be reviewed and should fail closed.
- Analytics document apply currently omits `record_indices` even though the review UI renders selectable rows, so summary/hierarchy preflight and apply default to every staged record. Treat row-level apply selection as unimplemented until the request carries it.
- Apply does not create repo-local backups. Recovery relies on Git or external filesystem backup.
- A lower-level `document-full-source` import-normalization branch exists even though that profile is not an enabled returned-package workflow; code presence must not be read as capability.
- Summary/hierarchy apply and Docs Import overlap near document mutation. The boundary is narrow field update versus explicit collection create/overwrite/skip; keep that distinction visible.
- Generic workflow modules are currently very thin dispatch wrappers. They preserve an ownership seam but add little logic of their own.

## Where To Look First

- capability or dispatch: adapter registry, validator/resolver, `services/dispatch.py`;
- workspace/path failure: `services/paths.py` and environment;
- prepare shape: selected adapter profile and family;
- staged-file identity: `services/returned_metadata.py` and export metadata;
- review/apply: adapter `returned.py`, family module, then domain helper;
- browser mismatch: Analytics config projection, route workflow module, and API request payload.
