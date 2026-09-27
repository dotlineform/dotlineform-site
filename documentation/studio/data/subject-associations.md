---
draft: false
doc_id: d-20260927-135604-05446e
title: Subject Associations
added_date: "2026-09-27 13:56:04"
last_updated: "2026-09-27 13:56:04"
summary: Current subject-association data, its UI actions and consumers, and its generation and publication rules.
parent_id: d-20260423-000000-d015e6
---
# Subject Associations

## Purpose And Review Boundary

This is a current-state inventory, inspected on 2026-09-27, for understanding document relationships before deciding whether their data model or presentation should change. Record each data product's purpose, the UI actions that read or change it, its consumers, and its update/publication rules. Use the same questions when reviewing semantic tokens, document links, and their UI actions.

`subject-associations.json` is a collection-specific reverse index: an explicitly declared subject maps to the documents about that subject. It supports exact document navigation and report joins. It does not collect semantic-token references, Markdown links, or all documents related through Catalogue membership. Ordinary documents have no corresponding association index from this builder.

The proposed UI idea is to present document relationships as **related links**, regardless of how they were derived. That is an exploration aim, not an implemented or agreed replacement model. This document records current behavior separately from questions for that review.

## Key Data Files

All workspace paths below are relative to the configured `$DOTLINEFORM_DOCS_BASE_DIR`. [Workspace configuration](../../../docs-viewer/config/workspace/docs-workspace.json) resolves storage and collection ownership; these are external workspace files, not repository-owned generated documents.

| File | Purpose And Authority | UI Actions And Consumers | Update And Publication Rules |
| --- | --- | --- | --- |
| `working/source/collections/<collection>/documents/*.md` | Canonical document identities and subject declarations in front matter. | Assign/Change Subject writes the configured subject field group. Open Source permits direct file editing. Collection Regenerate can replace generated document source, including Catalogue Work declarations. | Source changes feed collection document builds. Publish captures eligible source and builds temporary Preview output. Canonical Working source is not distributed as reader data. |
| `working/generated/collections/<collection>/documents/manage-manifest.json` | Private document list with normalized `authoring_subject` per row when subject projection is enabled, plus `subject_generation`. Retains missing, malformed, and conflicting subject states for management. | Collection management uses the rows for Subject display and assignment context. Project State joins the Works manifest with its association index. | Written by the collection builder alongside the association index. Targeted builds merge selected rows with saved rows. Excluded from the completed Preview snapshot and public distribution. |
| `working/generated/collections/<collection>/documents/subject-associations.json` | Reverse lookup from valid exact subjects to document identities and Manage locations; schema `docs_subject_associations_v2`. | Catalogue Works and the Working Works Subject column read Catalogue's file. Project State reads Works' file. | Generated conditionally by collection document builds. Working includes draft documents. Never edit it as source. Publish rebuilds the corresponding Preview product from eligible source rather than copying this file unchanged. |
| `working/generated/collections/<collection>/documents/manifest.json` | Reader document list. Catalogue rows carry `work_id`; other collection rows carry a public-safe Work/Series `subject` or `null`. | Collection readers use this list; it is a separate subject representation from the private reverse index. | Written by the collection builder. Preview rebuilds its reader list from the prepared document set, and distribution projects that list into `site/assets/data/docs/<collection>/manifest.json`. Folder subjects and authoring diagnostics are not reader subject data. |
| `preview/collections/<collection>/documents/subject-associations.json` | Association product generated during the temporary build of eligible documents. Currently still contains `access: "manage"` locations. | Snapshot validation checks it. There is no Preview browsing surface or public association-file reader. | Retained in the completed Preview snapshot when generated. Explicitly omitted from repository distribution; it does not reach `site/assets/data/docs/<collection>/`. |

Catalogue Works' private `working/generated/catalogue/reports/catalogue-works/metadata.json` is an adjacent product: it supplies Work/Series display and search data, while Catalogue's association index supplies exact document destinations. Studio Work Save updates the report metadata but does not regenerate the Docs association index or rewrite the linked Catalogue documents. [Catalogue Works](../Catalogue_Works.md) owns that distinction.

## Subject And Association Shape

The recognized declarations are `work_id` → `work`, `series_id` → `series`, and `folder_path` → `folder`. A document must have exactly one valid declaration to enter the reverse index. No declaration normalizes to `none`; multiple declared fields normalize to `conflicting`; a bad value or unsupported folder declaration normalizes to `malformed`. These states remain management evidence, while only `valid` subjects produce associations.

Work keys are exact five-digit strings. Series keys use the canonical lowercase alphanumeric/hyphen format. Supported folder keys are normalized relative targets. Normalization does not check current Work/Series registry membership or folder existence, and never infers identity from titles, filenames, body text, selected rows, or route context.

The payload contains `schema_version`, `collection`, `subject_generation`, and an `associations` array. Each association has one `subject: {kind, key}` and a deterministic list of `documents`. Each document entry has `target: {collection, doc_id}` and `locations: [{access: "manage", url}]`. The URL is composed from the configured collection report host and immutable subdocument ID. There is no publishing-stage discriminator.

Several documents may share a subject. That is valid for the producer and Project State. The Catalogue navigation consumer has a narrower requirement: one exact Catalogue document per associated Work. It rejects duplicate or ambiguous Work mappings and invalid document locations. A Work with no association remains plain text; failure to load or validate the whole file is an error.

## UI Action Map

| UI Action | Effect On Association Data | Completion Or Freshness Boundary |
| --- | --- | --- |
| Assign Subject / Change Subject, including clearing it | Writes the exact document's configured front-matter field group, then rebuilds its collection outputs. | The management operation awaits its source-write and collection-build follow-through. Current assignment rejects non-empty Folder subjects, although existing Working Works folder declarations remain readable. |
| Open Source and edit canonical Markdown | A subject declaration change can add, replace, or remove an association. | The Working watcher rebuilds affected document output independently after the file changes. |
| Source Editor Save | Saves body plus editable Title/Summary while preserving subject fields. The resulting document build can rewrite output, but Save is not a subject-assignment UI. | Save completes at canonical source persistence; watcher generation is independent. |
| Working document Build or collection document rebuild | Recomputes normalized subjects and the reverse index for the collection being built. | A successful build owns the generated result. Targeted collection builds reconstruct the aggregate from merged saved metadata, preserving unselected documents. |
| Collection Regenerate | Rewrites collection-owned generated source and rebuilds its document outputs; Catalogue declarations therefore feed the same association producer. | Source regeneration and its owning rebuild are the update boundary, separate from Studio Work Save. |
| Document create, import, or delete with collection rebuild follow-through | Can add or remove subject-bearing documents and their index entries. | The source operation's collection build owns reconciliation; the association file is not an independent write target. |
| Publish | Captures eligible source, builds Preview associations in temporary storage, validates/replaces Preview, then distributes the completed snapshot. | One awaited Publish action. It does not refresh the live Working association file; distribution excludes Preview association files. Git commit, push, and Deploy Public are separate actions. |
| Open Catalogue Works | Reads Catalogue's association file alongside private Catalogue Works metadata to construct Work ID/title links. | One association read per report mount; the read blocks report readiness. No association writes. |
| Open Working Works collection | Reads Catalogue's association file to make Work subjects navigate to exact Catalogue documents. | Loaded with the collection subject contribution. Series subjects open Media View separately; folder subjects retain their local-folder action. No association writes. |
| Project State Run/Refresh | Reads Works' association file and management manifest, then joins them with project folders and canonical Catalogue data. | Returns a newly assembled report; it does not rebuild or repair the association inputs. |
| Follow a document link or open a Series gallery | Uses the selected exact destination or the separate Media View owner. | Navigation only; no association writes. |

## Generation And Publication Rules

The producer is [CollectionDocsBuilder](../../../docs-viewer/build/docs_builder/collection.py), using [docs_document_subjects.py](../../../docs-viewer/services/docs_document_subjects.py). A collection enables private subject projection when its customisation declares subject support, at least one input document declares a recognized subject field, or its output already contains `subject-associations.json`. A saved management manifest's subject generation also participates in targeted reconstruction. Therefore absence is not automatically an error, and an existing index can persist as an empty file after its final declaration is removed.

The builder writes the management manifest and association file from the same normalized subject set, only when their serialized bytes change. `subject_generation` is a deterministic hash of collection identity and normalized per-document subjects, not a receipt for all document content, current Catalogue state, or every composed URL. Project State requires matching manifest/index generations and checks their association membership; the Catalogue link reader reads the association file alone and does not perform that join.

Working subject indexing is independent of publication readiness and includes draft documents. Publish selects documents using explicit `draft`, ordinary `unpublishable.json` exclusions and inherited exclusions; exclusion of a collection's report host excludes the collection. [Preview preparation](../../../docs-viewer/services/docs_prepare_preview.py) then rebuilds the eligible set in isolated temporary storage, so associations can differ from Working.

The configured Works publication owner removes authoring subject fields and retains only a valid Work or Series declaration. Folder subjects and invalid/conflicting subject declarations do not survive that projection. This specialization belongs to Works; other collection source fields are not globally stripped. Preview also removes other Working collection customisations, retaining Works' derived subject support. A fresh temporary output directory has no historical association file to keep an otherwise unnecessary empty product enabled.

[Snapshot assembly](../../../docs-viewer/services/docs_preview_snapshot.py) validates and retains generated association files, while excluding management manifests. [Repository distribution](../../../docs-viewer/services/docs_deploy_repo.py) explicitly skips association files because they have no public reader. Search rebuilding is separate and neither generates nor refreshes this index.

## Active Consumer Owners

| Owner | Input And Responsibility |
| --- | --- |
| [Catalogue document link reader](../../../docs-viewer/runtime/js/management/docs-viewer-management-catalogue-document-links.js) | Loads the configured Catalogue association file and validates exact Work-to-document mappings. Shared by the two navigation consumers below. |
| [Catalogue Works report](../../../docs-viewer/runtime/js/reports/catalogue-works-report.js) | Combines those mappings with separately generated Work/Series report metadata; Work IDs and titles link to Catalogue documents. |
| [Working collection subjects](../../../docs-viewer/runtime/js/management/docs-viewer-management-collection-working-subjects.js) | Working Works uses those mappings for Work Subject navigation. The Subject row itself comes from document management metadata; it does not read Works' own reverse index for this navigation. |
| [Project State producer](../../../docs-viewer/services/docs_project_state.py) | Reads Works' association index and matching management manifest, then places documents against project folders using folder, Work, and Series relationships. Invoked by Project State Run/Refresh through `/docs/project-state`. |

## Observed Workspace State

These counts were read from the configured files on 2026-09-27. They are a dated observation, not required collection membership or an acceptance target. Counts below are document associations, not distinct subjects.

| Collection | Working | Preview |
| --- | --- | --- |
| Catalogue | 4,616 Work associations | 4,616 Work associations |
| Works | 209 Folder, 19 Series, 6 Work associations | 10 Series, 1 Work association |
| Processing | 1 Work association | File absent; reader manifest contains no documents |
| Moments | Empty association file | Association file absent; reader manifest contains 57 documents |
| Concepts | Association file absent | Association file absent; reader manifest contains 246 documents |

The different presence and counts follow conditional generation, source eligibility, Works' subject projection, and the fresh temporary build boundary. They are not evidence that public distribution missed required association files: distribution deliberately omits them.

## Questions For The Relationship Review

- Should a document's related links include other documents declaring the same exact subject, documents directly linked in its body, and documents reached through semantic-token references? Which Catalogue relationships should contribute?
- Should the UI show one destination once when several derivations find it, and what ordering or grouping would make that list useful?
- Can one presentation consume a consistent relationship projection while retaining derivation, direction, and exact identity for maintenance and explanation?
- Which relationships are useful publicly, and which depend on private subjects or local actions? Manage URLs and folder subjects need an explicit public/private boundary.
- Is retaining a private Manage-location association index inside Preview useful when distribution deliberately excludes it?
- Should collection-specific subject representations and exact Catalogue navigation remain separate projections of a shared model? Their current validation and cardinality requirements differ.

Review semantic-token data, document-link data, and their UI actions against the same purpose/action/consumer/rules structure before deciding the target model. No consolidation implementation or broader data migration is specified here.
