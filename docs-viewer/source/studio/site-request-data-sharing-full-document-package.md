---
doc_id: site-request-data-sharing-full-document-package
title: Data Sharing Full Document Package
added_date: 2026-07-11
last_updated: 2026-07-11
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Data Sharing Full Document Package

## Status

In progress as the producer for the complete [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) round trip. Its validated-package interface is implemented by the review consumer; the remaining work is the real full-source export/intake producer.

The external workspace-root slice is complete: Data Sharing registry v3, Analytics/Data Sharing adapters, Docs Viewer export and returned-package services, and Docs Review sessions now use `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/` without repo-local fallback paths. Full-package schema, export, intake, and validation remain to be implemented.

Phase 1 owns full-fidelity export, returned-package intake, validation, and the persistent read-only review projection. It does not own the later configured-source write. [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) specifies schema-aware collection import from the immutable staged JSONL.

## Product Context: Iterative Knowledge Creation

This package implements the portable round-trip part of [Knowledge System Vision](/docs/?scope=studio&doc=knowledge-system-vision). It is a repeatable knowledge-development workspace, not primarily a backup or one-off migration format.

Consequences for the package design:

- repeated export/edit/return cycles are a primary use case
- stable `doc_id` values preserve identity across evolving versions
- hierarchy, summaries, links, references, media, and embedded content are part of the knowledge, not incidental decoration
- source and asset provenance must distinguish current accepted state, exported state, and returned state without treating AI authorship as an error condition
- complete, lossless source and dependency transport matters more than compactness
- the format must support whole collections and newly proposed chapter documents, not only isolated field patches

## Problem

The current `document-content` Data Sharing profile exports document content derived from rendered Docs Viewer HTML. Markdown output is produced by converting that HTML back to Markdown.

That projection is useful for analysis, summaries, hierarchy proposals, and text-oriented tasks, but it is not a source-faithful round trip. Rendering may resolve or discard:

- media tokens and their original attributes
- semantic-reference tokens
- interactive HTML tokens
- source-relative and Docs Viewer link syntax
- raw HTML and embedded-content structure
- comments and source formatting
- referenced media, downloadable files, scripts, styles, and other local dependencies

The returned JSON therefore cannot safely become a complete review source or canonical replacement.

## Outcome

Add a separate Data Sharing profile that exports a complete portable document workspace:

- one JSONL file containing every selected document's exact canonical Markdown, including front matter and source tokens
- one easy-to-parse document record per line
- per-document media, link, reference, and embedded-content manifests inside the JSONL records
- referenced local images and downloadable files
- supported interactive HTML and its resolvable local dependencies
- package-level manifests and trusted export provenance
- external task instructions and package context
- optional asset bundling for transport where the target service supports it

The external service may edit Markdown, reorganize parent relationships, add new chapter documents, replace images, add supported assets, and modify packaged interactive content.

On return, Data Sharing safely stages and validates the complete package, regenerates inventories from the actual files, and exposes a validated folder to Docs Review.

## Decision

Create a new full-package profile rather than changing the meaning of the existing `document-content` JSON/JSONL profile.

The new profile still uses JSONL because combining many documents into one uploadable, machine-readable text file is the central Data Sharing capability. The difference is that each row contains the exact canonical Markdown source rather than content reconstructed from rendered HTML.

JSONL is the default and primary format. A single JSON file containing the same header metadata and document-record array may remain an optional supported target, but the workflow must never require one Markdown upload per document.

Images and other binary assets accompany the JSONL separately and are mapped through embedded and package-level manifests. A folder is the local workspace form. An archive may be offered as an optional transport convenience only when the target service is known to support it; ZIP support is not a requirement for the core workflow.

For reviewed documents intended for import, prefer embedding new or replaced raster images directly in returned Markdown as supported data URLs when the external editing surface can supply them. Data Sharing must validate their package size and content shape, but it does not need to promote them into canonical media paths. The downstream Docs Viewer importer already has a planning/materialization path for PNG, JPEG, WebP, and GIF data URLs. Separate asset files remain necessary for existing packaged dependencies, attachments, interactive content, and unsupported inline forms.

## Ownership Boundary

### Data Sharing

Data Sharing owns:

- document selection and descendant inclusion
- exact canonical-source serialization into one JSONL document stream
- source and asset dependency discovery
- package layout and schema
- external task/context files
- export manifests and trusted internal provenance
- JSONL plus asset-folder output
- returned-package staging and safe extraction
- returned source, hierarchy, asset, link, and embed validation
- regenerated returned-package inventories
- handoff to Docs Review

### Docs Review

Docs Review owns only:

- listing validated returned package folders
- rendering the persistent package-local projection
- initial build or repair of missing derived output
- package asset-inventory display
- canonical counterpart links and manual comparison

Docs Review does not discover export dependencies, validate transport archives, edit preview source, or write configured source.

### Docs Viewer Import Handoff

The immutable staged JSONL associated with a reviewed package may later be handed to managed Docs Viewer Import as a document collection.

Data Sharing supplies:

- a trusted validated package identity
- the immutable staged JSONL identity
- validated record and inventory contracts
- provenance and validation diagnostics

Docs Viewer Import owns target-scope selection, record selection, front-matter normalization, explicit create/overwrite/skip choices, parent/link mapping, embedded-image materialization, configured source writes, and rebuilds. It reads the staged JSONL rather than the derived preview Markdown.

Docs Review may link to that managed import flow, but it must not acquire canonical mutation endpoints. The detailed reuse boundary is specified in [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package).

## External Workspace Root

Packages are user-workspace artifacts outside the repository:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/
  exports/
  import-staging/
  import-preview/
  meta/
```

No phase falls back to repo-local `var/analytics/data-sharing/...` paths.

The shared workspace resolver validates `DOTLINEFORM_PROJECTS_BASE_DIR`, projects marker-rooted display paths, and supplies explicit resolved roots to Data Sharing and Docs Review services.

## Proposed Package Layout

```text
<export-id>/
  documents.jsonl
  manifest.json
  context/
    instructions.md
    package-context.json
    returned-package.schema.json
  assets/
    media/
    files/
    interactive/
  inventories/
    documents.json
    assets.json
    links.json
    semantic-references.json
    embedded-content.json
```

`documents.jsonl` is the primary external editing payload and contains the complete textual corpus. Assets are separate files so ChatGPT can inspect or replace them without encoding binary data into JSONL.

The exact supporting subdirectory names may be refined during schema work, but the single JSONL text payload, transferable assets, context, and package-level inventories must remain separate concerns.

## Canonical JSONL Contract

The export contains one header row followed by one row per selected document. JSONL line order should follow deterministic source/tree order.

Illustrative shape:

```json
{"record_type":"data_sharing_header","schema_version":"documents_full_package_v1","export_id":"...","scope":"library","profile_id":"document-full-source","document_count":50}
{"record_type":"document","doc_id":"example","source_path":"example.md","source_sha256":"...","document":{"title":"Example","parent_id":""},"canonical_markdown":"<exact UTF-8 Markdown file including front matter and source tokens>","assets":[{"asset_id":"asset-001","kind":"image","package_path":"assets/media/example.webp","source_token":"<exact token text>","sha256":"..."}]}
```

`canonical_markdown` is the authoritative editable field for that row. It contains the complete UTF-8 source file, including front matter, body Markdown, media tokens, semantic-reference tokens, raw allowed embeds, comments, and formatting. JSON escaping is transport encoding only; decoding the string must reproduce the original source bytes used for `source_sha256`.

Extracted `document` metadata makes selection, hierarchy analysis, and prompt use easier, but returned validation reparses `canonical_markdown`. It does not trust duplicated title, parent, or summary fields when they disagree with the returned source.

Each document row records at least:

- `doc_id`
- original scope
- original source path
- title and `parent_id`
- source SHA-256
- source byte count
- existing/new classification at export time
- canonical counterpart URL
- exact `canonical_markdown`
- the document's asset/link/reference/embed manifest entries

The `doc_id` and parsed front matter must agree on export. The row record, not filename inference, is authoritative for package identity.

The returned JSONL is a complete corpus, not a changed-field patch. It may contain new document rows created by the external service. Returned validation derives their `doc_id`, title, hierarchy, and hashes from `canonical_markdown` and rejects duplicate identities.

## Asset And Embedded-Content Contract

Data Sharing scans exact source for supported constructs and builds a dependency inventory.

Initial classes:

- Docs Viewer media-token references
- ordinary Markdown images
- links to local PDFs, archives, data files, and other transferable files
- Docs Viewer interactive-HTML-token assets
- directly resolvable local scripts and styles referenced by packaged interactive HTML
- Docs Viewer semantic-reference tokens
- ordinary internal and external Markdown links
- supported raw HTML or embedded-content blocks

For each packaged asset, record:

- stable asset id
- kind and MIME type
- original logical/canonical path
- package path
- SHA-256 and byte count
- image dimensions where applicable
- referencing document ids
- whether the asset was copied, external-only, missing, unresolved, or unsupported

Every document row embeds the manifest entries for assets and other constructs referenced by that document. Package-level inventories provide deduplicated cross-document views over the same asset IDs.

Exact Markdown remains unchanged inside `canonical_markdown`. Package-local copies are connected to source tokens through stable asset IDs, recorded token text, package paths, and the package-aware preview resolver.

An external service may replace an existing packaged asset, add a new supported asset, or update Markdown to reference it. Returned validation rescans the package and creates a new trustworthy inventory; it does not require ChatGPT to maintain manifest JSON perfectly.

Remote URLs are inventoried but not downloaded silently. Dynamic or unresolved script dependencies must produce explicit warnings or blockers rather than an incomplete package presented as portable.

## Trusted Provenance

The transferable JSONL header and `manifest.json` are useful context but become untrusted after the package leaves the application.

Data Sharing retains a separate trusted export record under `meta/`, keyed by `export_id`, containing:

- export schema and profile version
- source scope and selection
- original document and asset hashes
- `documents.jsonl` and package manifest hashes
- generation time
- source/config revisions needed for later comparison

Returned intake uses the trusted record for provenance and regenerates returned inventories from actual files.

## External Task Context

`context/instructions.md` should explain in plain language that `documents.jsonl` contains the complete editable corpus and that supporting assets are mapped by the manifests in each document row.

The task may explicitly authorize the external service to:

- expand and reorganize prose
- change titles, summaries, and `parent_id`
- create new chapter documents
- preserve, reposition, replace, or remove existing media
- add new images or supported files
- update links and semantic references
- edit packaged interactive content when requested

It should also require:

- valid source front matter and unique `doc_id` values
- package-relative asset containment
- no symlinks or absolute filesystem paths
- no secrets, credentials, or environment-specific paths
- a returned `documents.jsonl` plus any changed/new asset files in the declared response layout

## Returned-Package Intake

Data Sharing intake must treat all returned files as untrusted.

Validation includes:

- JSONL header/schema validation and one-object-per-line parsing
- complete `canonical_markdown` string validation for every document row
- configurable total size, file count, and per-file size limits
- safe archive extraction with traversal, absolute-path, device-file, symlink, nesting, and compression-ratio limits only when optional archive intake is enabled
- allowed source and asset types
- duplicate/case-colliding path detection
- returned `canonical_markdown` front-matter parsing and unique `doc_id` validation
- complete hierarchy validation within the returned package context
- asset-reference and missing-file checks
- link/reference inventory regeneration
- interactive-content and script inventory regeneration
- no execution of returned scripts during intake
- concise errors, warnings, and package counts

Successful intake materializes each validated `canonical_markdown` row as persistent read-only `source/<doc-id>.md` inside `import-preview/<package_id>/`, copies validated asset files, and writes regenerated manifests for Docs Review. This materialization is a review-workspace projection; it does not write canonical source or public assets and is not the later import input.

The Docs Review consumer requires the trusted handoff `manifest.json` to use `schema_version: docs_review_validated_package_v1`, carry the matching safe `package_id`, set `status: validated`, identify `source_scope`, and optionally identify `default_doc_id` and a display `title`. Its regenerated `inventories/assets.json` uses asset records with `kind`, the source `token_path`, and a safe `package_path` under `assets/`. These are handoff fields owned by Data Sharing intake, not external-service assertions.

The compact `document-content` Content review action now exercises this handoff for a rendered-derived, text-only package: it validates the materialized Markdown set in memory, then writes the timestamped package and trusted manifest. Existing timestamped package folders are rejected rather than replaced. A document whose parent is outside a partial compact selection is rooted in the derived projection with a preserved validation warning so the package remains buildable. This proves the live producer/consumer seam, but it does not satisfy the full-package contract. `document-full-source` must still provide exact `canonical_markdown`, copied and regenerated asset/dependency inventories, and the complete returned-package checks described here; its hierarchy validation remains complete and strict.

## Review Rendering And Script Safety

Docs Review renders the validated package through a synthetic Docs Viewer builder configuration and a package-aware asset resolver.

Returned interactive HTML and scripts remain untrusted. Preview must use the existing sandbox boundary and should not grant same-origin privileges, canonical write services, repository paths, or management capabilities to packaged content.

Any stronger network or content-security policy should be decided during implementation after auditing current supported interactive content.

## Relationship To Existing Profiles

Keep `document-content` for compact JSON/JSONL tasks such as:

- analysis and rewriting suggestions
- summary creation
- hierarchy proposals
- search enrichment
- text-oriented external reporting

Do not treat its rendered-derived `content` field as canonical Markdown.

Use the new `document-full-source` JSONL profile when the external service needs the complete exact source corpus, media manifests, links, embedded assets, or the ability to return a complete previewable workspace.

Both profiles preserve the core Data Sharing benefit of sending many documents in one JSONL file. They differ in content contract:

- `document-content`: compact rendered-derived content for analysis and selected-field workflows
- `document-full-source`: exact complete canonical Markdown plus asset/dependency manifests for full collection editing

## Implementation Steps

### 1. Supported-Construct Inventory

- enumerate source tokens, Markdown constructs, local asset types, and allowed embedded content
- identify dependency rules and unsupported/dynamic cases
- assemble representative fixtures containing every supported class

### 2. Package Schema And Workspace Resolver

- define the JSONL header, document-row, context, and inventory schemas
- define trusted export metadata
- implement external workspace-root resolution — complete
- define JSONL-plus-assets transport and optional archive rules

### 3. Source-Faithful Export

- serialize every exact selected source file into one `documents.jsonl` stream
- include extracted identity/hierarchy fields and per-document asset manifests without replacing source authority
- compute document hashes and provenance
- preserve source tokens, hierarchy metadata, comments, and formatting without rendered conversion

### 4. Dependency Collection

- inventory media, links, references, and embeds
- copy resolvable local assets and dependencies
- report remote, missing, unsupported, and dynamic dependencies
- write deterministic asset mappings

### 5. External Context And Transport

- generate task instructions and response schema
- write `documents.jsonl` and the asset folder atomically
- optionally create a deterministic safe archive only for confirmed target surfaces
- retain trusted metadata separately

### 6. Returned Intake And Validation

- accept returned JSONL plus separate asset files, with optional safe archive intake
- parse complete returned document rows and materialize persistent read-only preview Markdown
- regenerate inventories from returned JSONL and actual asset files
- validate canonical Markdown, hierarchy, assets, links, and embeds
- create the Docs Review handoff folder

### 7. Docs Review Integration

- expose validated package records
- provide package-aware source and asset roots to the review builder
- verify representative original and modified packages render correctly

### 8. Docs Viewer Import Handoff

- hand the immutable staged JSONL identity to the separate managed Docs Viewer flow
- share the JSONL parser/normalizer between preview materialization and import
- keep persistent preview Markdown read-only and outside import authority
- support explicit create, overwrite, or skip decisions for records
- reuse Docs Import data-URL media planning and materialization

## Acceptance Criteria

Phase 1 is complete when:

- all selected canonical Markdown is exported without content transformation in one JSONL file
- each document row contains complete `canonical_markdown` and its per-document asset/dependency manifest
- all supported referenced local assets are copied or explicitly classified
- manifests and trusted export metadata contain hashes and provenance
- the JSONL can be sent to ChatGPT as the single textual corpus while mapped asset files are supplied separately
- optional archive transport is capability-gated rather than required
- returned packages are safely extracted and validated without executing content
- returned JSONL is materialized into persistent read-only preview Markdown only after validation
- changed/new Markdown and assets are reflected in regenerated inventories
- a validated returned package builds successfully in Docs Review
- the entire workflow uses `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`
- no phase writes canonical source or public assets
- the validated package exposes enough safe identity and inventory context for the separate Docs Viewer import request

## Non-Goals

- replacing the compact `document-content` profile
- configured-scope import in this request
- configured-source create, overwrite, skip, merge, or delete behavior
- implementing canonical mutation inside Docs Review
- silently fetching remote assets
- guaranteeing portability for unresolved dynamic script dependencies
- executing returned scripts during intake
- Git commit or push
