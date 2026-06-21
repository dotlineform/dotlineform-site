---
doc_id: config-data-sharing-files
title: Data Sharing Config Files
added_date: 2026-06-02
last_updated: 2026-06-21
parent_id: studio
viewable: true
---
# Data Sharing Config Files

Config files:

- `data-sharing/config/adapters.json`
- `data-sharing/config/adapters.schema.json`
- `data-sharing/adapters/documents/config/prepare-profiles.json`

## Contract Role

`adapters.json` is the Data Sharing domain registry.
It defines domain dispatch, adapter modules, operation capabilities, path contracts, source write targets, returned-package staging roots, review output roots, and operation-level UI/action metadata needed by the Data Sharing services.

`data-sharing/adapters/documents/config/prepare-profiles.json` defines documents adapter prepare profiles.
Profiles describe which documents or fields are packaged for outbound documents Data Sharing workflows.

`adapters.schema.json` validates the adapter registry shape.
Documents prepare profiles are validated semantically by the documents package engine; there is no separate profile schema file.

## What Reads Them

Data Sharing services read the adapter registry to dispatch prepare, list-returned, review, and apply operations.
Documents package tooling reads documents prepare profiles during package preparation.
Analytics-hosted Data Sharing browser routes read workflow metadata through `/analytics/api/data-sharing/config`; that endpoint publishes a UI-safe registry view and attaches documents prepare profiles to the prepare capability.
The browser should not fetch these files directly through Analytics static file serving.
The public config endpoint projects only browser-needed fields.
It exposes adapter/domain labels, operation status, selection model, sharing profile identity, UI format choices, limited selection UI flags, apply-action UI copy, confirmations, and result display rows.
It does not expose adapter path contracts, source-write targets, output path patterns, metadata contracts, document field contracts, or activity emit metadata.

## Edit Class

`adapters.json` is maintainer-editable workflow config.
It can change behavior, source-write scope, and adapter dispatch, so changes require focused Data Sharing tests.

`data-sharing/adapters/documents/config/prepare-profiles.json` is user/maintainer-editable documents-adapter workflow config.
It is safer to edit than the adapter registry, but profile changes should still be checked with prepare/export tests.

The adapter registry schema is code infrastructure.

## Cleanup Review

Cleanup should focus on ownership:

- keep Data Sharing domain capability and path contracts in `adapters.json`, not Studio or Analytics route config
- keep route visible copy in Analytics UI-text bundles, not adapter capability records unless the copy is operation-owned
- remove retired domains or operations only with service dispatch tests
- keep source-write targets explicit and narrow
- keep returned-package staging and review output paths under local working output roots

Further work for subsequent sessions:

- keep `/analytics/api/data-sharing/config` as the only browser-facing Data Sharing config lookup for Analytics-hosted Data Sharing routes
- keep the public config response on a whitelist of UI-needed fields; do not expose adapter path contracts, source write targets, output path patterns, metadata contracts, or document field contracts to browser routes
- the 2026-06-03 cleanup review tightened the public config projection so sharing profiles no longer pass through output, metadata, document-field, or non-UI selection internals, and apply actions no longer expose activity emit metadata
- if the public config response needs more shaping or more domains, move the public-payload helpers out of `analytics_data_sharing_api.py` into a focused module and keep the current static-path and payload-whitelist tests
