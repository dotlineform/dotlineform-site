---
draft: false
doc_id: d-20260503-141500-98fa03
title: Package Prepare Profiles
added_date: "2026-05-03 14:15:00"
last_updated: "2026-10-20"
parent_id: d-20260424-000000-50b63f
---
# Package Prepare Profiles

## Owner

`docs-viewer/config/document-packages/profiles.json` defines the fixed package shapes supported by integrated Docs Viewer. The document-package engine performs semantic validation; there is no separate profile schema.

The [Prepare Package](Package_Prepare.md) workflow receives profiles and captured-target metadata from one `POST /docs/packages/prepare-options`. It does not fetch this source file directly. The separate config/documents GET routes are retired without aliases.

## Current Profiles

| Profile | Purpose | Container/content | Return path |
| --- | --- | --- | --- |
| `document-content` | selected document context/body rows for external review | JSONL or JSON; rendered-derived Markdown or plain text; optional modal missing-summary filter | supported for returned whole-package review and validated Docs Review projection when the exact collection also opts in; full Docs Viewer Import owns apply |
| `document-tree` | selected document metadata without body content | JSON tree container; application records are flat checked collection members, while the independent CLI retains ordinary subtree expansion | export only |

Profile IDs describe package shape, independently of configured collection identity. Application Prepare submits required exact `collection`, final explicit `doc_ids`, `profile_id` and target/content formats; Working is resolved at the service. Scope/stage/sub-scope aliases and application `select_all`/filter flags are retired. Both the profile and exact named collection must opt in to returned Import. The independent CLI retains ordinary package formats/capabilities, but ordinary packages have no application Import entry point.

## What A Profile May Configure

- label/description/enabled state and domain;
- container format and record shape;
- content format for body strings;
- supported selection choices and descendant requirements;
- output filename pattern below the configured export root;
- document field mapping and supported transforms;
- character/document limits and truncation policy;
- internal metadata fields;
- whether a returned package is eligible for import review.

Exact keys, mappings, transforms, and current values belong in the JSON and validator. A profile can configure only behaviour the package engine already implements.

## Shipped Selection Options

The browser-safe profile projection declares which options the compact **Prepare package** modal may show and their defaults.

| Profile | Application selection | Missing summaries | Draft/publication-excluded documents |
| --- | --- | --- | --- |
| `document-content` | exact checked collection IDs | supported, off by default | included |
| `document-tree` | exact checked collection IDs | unsupported | included |

For the content profile, the modal's missing-summary choice means source `summary` metadata is empty after trimming whitespace. Draft and publication eligibility do not filter package membership. Flat collection targets have no descendant expansion; filtering can subtract only from their exact checked IDs.

The modal sends final effective explicit IDs and supported formats. Application Prepare consumes that choice without reapplying filters or limits. Both profiles currently have `max_documents: null` and `max_total_chars: null`; only the content profile's 50,000-character per-document truncation is active. CLI selection retains its separate explicit/all/summary owner.

## Content Method

`document-content` renders the Docs Viewer source document first, then converts visible HTML to Markdown or plain text. That keeps headings, lists, embedded HTML, image/SVG text, and the visible renderer on one path. It is intentionally not an exact raw-Markdown export.

Consequences:

- rendering failure is an export failure rather than silently emitting misleading content;
- source comments/reference definitions/custom syntax/media tokens may be lost or transformed;
- returned content is a text-oriented candidate, not proof that the original source dependency set survived.

The separate full-source export delivery owns any future exact Markdown/assets package and is export-only unless a later delivery deliberately designs a trusted return path.

## Return Eligibility

`workflow.supports_return_import` is a gate, not an implementation switch. A profile also needs a supported parser/review/action family in code. Export-only files retain provenance but are kept out of the actionable returned list.

Named-collection returned Import requires the exact collection's `supports_return_import` as well as the profile's capability. Returned listing, Docs Review and Import retain trusted provenance and complete-package validation. Export-only profiles explicitly set `false`; absent flags do not opt in.

## Change Method

1. Decide whether the change is an option the documents family already implements.
2. Update configuration. Specify any proposed semantic package/export test work separately and obtain its approval before changing tests.
3. If a new source field, transform, selector, record shape, or return behaviour is needed, implement/validate it first.
4. Verify safe output containment, browser projection, metadata, and return eligibility.
5. Keep this page at the profile-method level; inspect config for the exhaustive mapping.

## Weak Spots

- runtime-only semantic validation makes invalid config discoverable later than a schema/editor check;
- profile field mapping is powerful enough to become a second document schema;
- `max_total_chars` and transform behaviour must be verified in code rather than inferred from config vocabulary.
