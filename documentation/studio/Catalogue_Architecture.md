---
draft: false
doc_id: d-20260401-000000-a11bf3
title: Catalogue Architecture
added_date: "2026-04-01 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6
---

# Catalogue Architecture

## Current Shape

Studio owns canonical Catalogue editing. A Work belongs to exactly one Series and may belong to multiple Galleries. Series and Galleries may be empty. Canonical Work, Series, Gallery and relationship sources live under `studio/data/canonical/catalogue/`. Detail records, source-owned publication state and parallel Catalogue Markdown prose are retired.

The data model map traces the five canonical families through Studio, Working and publication. The workflow guide follows a Work image change and a Gallery rename through those steps. [Catalogue Data Model Map](Catalogue_Data_Model_Map.md) · [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md)

[Catalogue Source Model](Catalogue_Source_Model.md) owns exact identities, fields and relationships. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns operation completion and reader timing. [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) owns generated JSON shapes; [Catalogue Deployment](Catalogue_Deployment.md) owns public distribution.

[Catalogue Media View](Catalogue_Media_View.md) describes how Docs Viewer opens Works and Galleries, traverses the invoking sequence and returns to the caller.

## Separate Authorities

The canonical source is the editable authority. Studio Work/Series search and focused editor reads are live projections of that source. Save prepares selected image renditions, thumbnails and downloads in Projects staging. The editor can use those saved bytes and canonical versions before Refresh hands them to Working.

Refresh Catalogue uses the updates queue to prepare selected records, indexes, media policy and private report inputs under `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. Refresh queues completed shared public output and marks completed Work handoffs ready. Regenerate uses those Work records to build Catalogue documents and queue their publication. Public readers use the separately published output.

The historical `studio/data/generated/catalogue-lookup/` files are retired and removed. The persisted lookup exporter and completed one-time Gallery converter are also removed; live Work and Series lookup payload builders remain in the Studio API. They build current canonical projections at read time without persisted-file fallbacks or a Save export dependency. The frozen legacy `site/archive/` payloads and media are outside active generation.

Unused legacy public-path and route tables, the old Markdown title-sort repair script and the completed v5 queue migration are removed. The old full/selected generator and its previous-membership output selector are also removed; normal Refresh uses the supplied queue, and explicit family repair remains in the current Refresh CLI. Pure Catalogue payload builders and unchanged-content comparison remain shared by the current Refresh paths. Source writes retain the canonical transaction owner; unused direct-writer and parser helpers are removed.

The related obsolete tests, fixture dependency and profile registrations are retired within the approved [Catalogue Service Retirement](Testing.md#catalogue-service-retirement) scope. Remaining historical tests are not accepted current workflow evidence merely because they remain in the repository.

## Change Method And Weak Spots

Change canonical fields through the source definition, serializer, validation, editor and affected projections together. Keep exact IDs and one owner for each relationship; do not infer Gallery or document associations from titles, filenames or routes. Use focused service/generator evidence for the changed boundary.

Normal Refresh reads the authorities needed by the supplied queue. Explicit canonical validation and family repair retain complete audits. Save and Refresh latency has not been measured. A failed Refresh can leave partial generated files and unfinished selections. Use the reported phase to correct the cause before rerunning the owning operation.

## Design History

The unification work kept the old public Catalogue frozen while testing a shared reader over independently owned Catalogue records and authored documents. The consumer studies separated exact media presentation from document links and held off on schema changes until a reader needed one. [Unification record](archive/Analysis_And_Catalogue_Presentation.md) · [Consumer study findings](archive/UAC_3_Findings.md)

The first document regeneration proved Work-backed documents in a bounded pilot and then across the collection. The next delivery made exact pending IDs the normal input so routine changes could carry their completed effects forward without rebuilding the whole Catalogue. [Initial regeneration](archive/Catalogue_Work_Regeneration.md) · [Targeted regeneration delivery](archive/Catalogue_Changed_Regeneration_Delivery.md)

## Approved Persisted Lookup Test Cleanup

The approved retirement removes `studio/tests/python/test_catalogue_lookup_refresh.py::test_metadata_only_save_refreshes_revision_and_reassignment_refreshes_both_series`. It used a temporary canonical Catalogue fixture, changed Work provenance and Series membership, invoked the deleted persisted exporter, then asserted generated-file counts, exact Work search and affected Series payloads, and a current member revision. It exercised temporary source/output writes with no service or network; it provides no retained coverage after deletion.

Only three `tests/run_checks.py` entries change: the deleted exporter's compile entry and this test module's compile and pytest entries in the `quick` profile's `python-syntax` and `quick-python-pytest` commands. All other command selections remain unchanged. This does not certify the retained profiles or authorize a profile run.

`studio/tests/python/test_studio_app_runtime_config.py::test_static_path_policy_serves_current_studio_allowlists` loses only its obsolete lookup-file allow assertion. The remaining handler assertions, import environment and fixtures are unchanged and remain unreviewed; no replacement retirement assertion is added. The projection manifest at `tests/contracts/projection_contract.json` loses only this directory's repository and forbidden-public path entries; the Catalogue field-registry classification and public restriction remain.

The agreed cleanup is implemented. The bounded maintenance uses source/diff review, Python lint and syntax checks, JSON validation and reference inspection at low local cost. It creates no tests, runs no tests or profiles, starts no services and performs no live canonical, workspace, media or network writes. Other historical Catalogue tests and profile entries remain outside this cleanup; their presence is not evidence of current coverage. Final review confirmed the agreed removal scope, live API ownership and retained Catalogue field-registry restriction.
