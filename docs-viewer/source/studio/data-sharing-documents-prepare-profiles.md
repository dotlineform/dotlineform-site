---
doc_id: data-sharing-documents-prepare-profiles
title: Documents Prepare Profiles
added_date: "2026-05-03 14:15"
last_updated: 2026-07-15
parent_id: data-sharing
viewable: true
---
# Documents Prepare Profiles

## Owner

`data-sharing/adapters/documents/config/prepare-profiles.json` defines configured package shapes for the existing documents adapter family. The documents package engine performs semantic validation; there is no separate profile schema.

The browser receives a safe projection from the Analytics Data Sharing config API. It must not fetch this source file directly.

## Current Profiles

| Profile | Purpose | Container/content | Return path |
| --- | --- | --- | --- |
| `document-content` | selected document context/body rows for external review | JSONL or JSON; rendered-derived Markdown or plain text | supported for returned review/narrow apply and validated Docs Review projection |
| `document-tree` | lightweight selected hierarchy context | nested JSON tree | export only |

Profile IDs describe package shape, not Docs Viewer scope. The request supplies `selection.docs_scope`; current source context supplies documents.

## What A Profile May Configure

- label/description/enabled state and domain;
- container format and record shape;
- content format for body strings;
- explicit/all-matching selection and descendant/non-viewable behaviour;
- output filename pattern below the configured export root;
- document field mapping and supported transforms;
- character/document limits and truncation policy;
- external task/response/field guidance;
- internal metadata fields;
- whether a returned package is eligible for import review.

Exact keys, mappings, transforms, and current values belong in the JSON and validator. A profile can configure only behaviour the package engine already implements.

## Content Method

`document-content` renders the Docs Viewer source document first, then converts visible HTML to Markdown or plain text. That keeps headings, lists, embedded HTML, image/SVG text, and the visible renderer on one path. It is intentionally not an exact raw-Markdown export.

Consequences:

- rendering failure is an export failure rather than silently emitting misleading content;
- source comments/reference definitions/custom syntax/media tokens may be lost or transformed;
- returned content is a text-oriented candidate, not proof that the original source dependency set survived.

The separate full-source export request owns any future exact Markdown/assets package and is export-only unless a later request deliberately designs a trusted return path.

## Return Eligibility

`workflow.supports_return_import` is a gate, not an implementation switch. A profile also needs a supported parser/review/action family in code. Export-only files retain provenance but are kept out of the actionable returned list.

The legacy default is return-enabled when the flag is absent; new/export-only profiles should set `false` explicitly so omission cannot accidentally widen intake.

## Change Method

1. Decide whether the change is an option the documents family already implements.
2. Update config and semantic package/export tests.
3. If a new source field, transform, selector, record shape, or return behaviour is needed, implement/validate it first.
4. Verify safe output containment, browser projection, external context coverage, metadata, and return eligibility.
5. Keep this page at the profile-method level; inspect config for the exhaustive mapping.

## Weak Spots

- runtime-only semantic validation makes invalid config discoverable later than a schema/editor check;
- editable external context shares a file with structural package policy;
- profile field mapping is powerful enough to become a second document schema;
- return-enabled default exists for compatibility and is a poor default for new profiles;
- `max_total_chars` and transform behaviour must be verified in code rather than inferred from config vocabulary.
