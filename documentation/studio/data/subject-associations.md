---
draft: false
doc_id: d-20260927-135604-05446e
title: Subject Associations
added_date: "2026-09-27 13:56:04"
last_updated: "2026-09-27 20:20:16"
summary: Manifest-owned subjects, in-memory report associations, exact navigation, and private/public generation boundaries.
parent_id: d-20260423-000000-d015e6
---
# Subject Associations

## Purpose And Review Boundary

This is a current-state inventory, inspected on 2026-09-27, for understanding document relationships before deciding whether their data model or presentation should change. Record each data product's purpose, the UI actions that read or change it, its consumers, and its update/publication rules. Use the same questions when reviewing semantic tokens, document links, and their UI actions.

Reports derive associations in memory from normalized `authoring_subject` rows in each collection's private `manage-manifest.json`. An explicitly declared subject maps to the documents about that subject. The former `subject-associations.json` product is retired from every collection: no producer, generated-data read allowance, Preview validation or distribution branch remains. There is no replacement lookup file. Subjects do not collect semantic-token references, Markdown links, or all documents related through Catalogue membership.

The proposed UI idea is to present document relationships as **related links**, regardless of how they were derived. That is an exploration aim, not an implemented or agreed replacement model. This document records current behavior separately from questions for that review.

## Key Data Files

All workspace paths below are relative to the configured `$DOTLINEFORM_DOCS_BASE_DIR`. [Workspace configuration](../../../docs-viewer/config/workspace/docs-workspace.json) resolves storage and collection ownership; these are external workspace files, not repository-owned generated documents.

| File | Purpose And Authority | UI Actions And Consumers | Update And Publication Rules |
| --- | --- | --- | --- |
| `working/source/collections/<collection>/documents/*.md` | Canonical document identities and subject declarations in front matter. | Assign/Change Subject writes the configured subject field group. Open Source permits direct file editing. Collection Regenerate can replace generated document source, including Catalogue Work declarations. | Source changes feed collection document builds. Publish captures eligible source and builds temporary Preview output. Canonical Working source is not distributed as reader data. |
| `working/generated/collections/<collection>/documents/manage-manifest.json` | Private document list with normalized `authoring_subject` per row when subject projection is enabled, plus `subject_generation`. Retains missing, malformed, and conflicting subject states for management. | Collection Subject display and assignment context; Catalogue Work-to-document navigation; Project State's Works grouping. | Collection builds maintain the rows and generation. Targeted builds merge selected rows with saved rows, preserving unselected metadata. Excluded from the completed Preview snapshot and public distribution. |
| `working/generated/collections/<collection>/documents/manifest.json` | Reader document list. Catalogue rows carry `work_id`; other collection rows carry a public-safe Work/Series `subject` or `null`. | Collection readers use their existing public-safe representation. | Written by the collection builder. Preview rebuilds its reader list from the prepared document set, and distribution projects that list into `site/assets/data/docs/<collection>/manifest.json`. Folder subjects and authoring diagnostics are not reader subject data. |
| `working/generated/catalogue/reports/works/manifest.json` | Private exact Work/Series title maps, separate from document manifests. | Context's Subject column displays current titles and opens Work/Series subjects in Media View by exact Catalogue identity. | Maintained by Studio Save. Context does not need Catalogue document mappings to open media. |

Catalogue Works' private `working/generated/catalogue/reports/catalogue-works/metadata.json` supplies Work/Series display and search data. Catalogue's management manifest supplies document identities; the link reader composes their destinations using the configured report host and the existing route helper. Studio Work Save updates the report metadata but does not regenerate or rewrite linked Catalogue documents. [Catalogue Works](../Catalogue_Works.md) owns that distinction. The local browser configuration projects each collection's existing `report_host_doc_id`; Manage requires that exact identity rather than inferring a host from the current route or document tree.

## Subject And Association Shape

The recognized declarations are `work_id` → `work`, `series_id` → `series`, and `folder_path` → `folder`. A document must have exactly one valid declaration to participate in report associations. No declaration normalizes to `none`; multiple declared fields normalize to `conflicting`; a bad value or unsupported folder declaration normalizes to `malformed`. These states remain management evidence, while only `valid` subjects produce associations.

Work keys are exact five-digit strings. Series keys use the canonical lowercase alphanumeric/hyphen format. Supported folder keys are normalized relative targets. Normalization does not check current Work/Series registry membership or folder existence, and never infers identity from titles, filenames, body text, selected rows, or route context.

Management manifests retain their existing shape: `docs` contains immutable `doc_id`, presentation metadata and normalized `authoring_subject`; subject-enabled manifests also contain `subject_generation`. No schema or source-field change accompanies the cutover. Project State groups valid rows by `{kind, key}`, keeps every matching document, composes exact Manage links from the configured Works host, and preserves title/ID ordering. Catalogue navigation builds an in-memory `work_id → URL` map from valid Work rows. There is no publishing-stage discriminator or persisted association payload.

Several documents may share a subject. That is valid for Project State. Catalogue navigation requires one exact Catalogue document per associated Work and rejects duplicate document identities or ambiguous Work mappings. A Work with no mapping remains plain text; failure to load or validate the management manifest is an error.

## UI Action Map

| UI Action | Effect On Subject Data | Completion Or Freshness Boundary |
| --- | --- | --- |
| Assign Subject / Change Subject, including clearing it | Writes the exact document's configured front-matter field group, then rebuilds its collection outputs. | The management operation awaits its source-write and collection-build follow-through. Current assignment rejects non-empty Folder subjects, although existing Working Works folder declarations remain readable. |
| Open Source and edit canonical Markdown | A declaration change updates normalized subjects in the management manifest. | The Working watcher rebuilds affected document output independently after the file changes. |
| Source Editor Save | Saves body plus editable Title/Summary while preserving subject fields. The resulting document build can rewrite output, but Save is not a subject-assignment UI. | Save completes at canonical source persistence; watcher generation is independent. |
| Working document Build or collection document rebuild | Recomputes normalized subjects and manifest generation. | A successful build owns the result. Targeted collection builds use merged saved metadata, preserving unselected documents. |
| Collection Regenerate | Rewrites collection-owned generated source and rebuilds document outputs and manifests. | Source regeneration and its owning rebuild are separate from Studio Work Save. |
| Document create, import, or delete with collection rebuild follow-through | Adds or removes exact manifest rows. | The source operation's collection build owns reconciliation. |
| Publish | Captures eligible source, builds temporary document output, validates/replaces Preview and distributes the completed snapshot. | One awaited Publish action. Management manifests remain private; no association artifact is generated. Git commit, push and Deploy Public are separate actions. |
| Open Catalogue Works | Reads Catalogue's management manifest alongside private report metadata to construct Work ID/title links. | One manifest read per report mount; the read blocks report readiness. |
| Open Context (Working Works collection) | Uses its own normalized document subjects and private Work/Series title metadata. Both Work and Series subjects open Media View by exact Catalogue identity. | Loaded with the collection subject contribution; no Catalogue document-manifest read is required. Folder subjects retain their local-folder action. |
| Project State Run/Refresh | Reads Works' management manifest, groups valid subjects and places documents against project folders and canonical Catalogue data. | Returns a newly assembled report without rebuilding or repairing its inputs. |
| Follow a document link or open a Series gallery | Uses the exact destination or the separate Media View owner. | Navigation only. |

## Generation And Publication Rules

The producer is [CollectionDocsBuilder](../../../docs-viewer/build/docs_builder/collection.py), using [docs_document_subjects.py](../../../docs-viewer/services/docs_document_subjects.py). Catalogue and Works always project authoring subjects, including for empty builds. Other collections enable this projection through configured subject support or recognized declarations in input documents. Saved management-manifest generation also participates in targeted reconstruction. Required subject projection never depends on an obsolete file's presence.

The builder writes manifests only when their serialized bytes change. `subject_generation` remains a deterministic hash of collection identity and normalized per-document subjects, not a receipt for all document content, current Catalogue state or composed URLs. Project State retains this field in its report generation. There is no cross-file receipt or membership comparison.

Working subjects include draft documents independently of publication readiness. Publish selects documents using explicit `draft`, ordinary `unpublishable.json` exclusions and inherited exclusions; exclusion of a collection's report host excludes the collection. [Preview preparation](../../../docs-viewer/services/docs_prepare_preview.py) rebuilds that eligible set in isolated temporary storage.

The configured Works publication owner removes authoring subject fields and retains only a valid Work or Series declaration. Folder subjects and invalid/conflicting subject declarations do not survive that projection. This specialization belongs to Works; other collection source fields are not globally stripped. Preview removes other Working collection customisations while retaining Works' derived subject support.

[Snapshot assembly](../../../docs-viewer/services/docs_preview_snapshot.py) excludes management manifests and retains the existing reader payloads. [Repository distribution](../../../docs-viewer/services/docs_deploy_repo.py) consumes that completed snapshot. Neither operation has association-file handling. Search rebuilding remains separate.

## Active Consumer Owners

| Owner | Input And Responsibility |
| --- | --- |
| [Catalogue document link reader](../../../docs-viewer/runtime/js/management/docs-viewer-management-catalogue-document-links.js) | Loads Catalogue's configured management manifest, validates exact Work-to-document mappings and composes links using its configured host for Catalogue Works. |
| [Catalogue Works report](../../../docs-viewer/runtime/js/reports/catalogue-works-report.js) | Combines those mappings with separately generated Work/Series report metadata; Work IDs and titles link to Catalogue documents. |
| [Working collection subjects](../../../docs-viewer/runtime/js/management/docs-viewer-management-collection-working-subjects.js) | Context uses normalized subjects and private title metadata. Work and Series subjects open the existing Media View; Folder opens Finder. It does not consume Catalogue document associations. |
| [Project State producer](../../../docs-viewer/services/docs_project_state.py) | Groups valid Works management rows, then places documents against project folders using Folder, Work and Series relationships. Invoked by Run/Refresh through `/docs/project-state`. |

## Artifact Retirement

Obsolete association files were removed from configured Working and Preview collection document owners. Cleanup preserves source, registrations, media, reader manifests, management manifests and unrelated output. Changing Preview bytes invalidates its completion receipt; the receipt was already absent at this cutover and remains absent. A subsequent explicitly requested Publish owns rebuilding and verifying a completed snapshot.

## Questions For The Relationship Review

- Should a document's related links include other documents declaring the same exact subject, documents directly linked in its body, and documents reached through semantic-token references? Which Catalogue relationships should contribute?
- Should the UI show one destination once when several derivations find it, and what ordering or grouping would make that list useful?
- Can one presentation consume a consistent relationship projection while retaining derivation, direction, and exact identity for maintenance and explanation?
- Which relationships are useful publicly, and which depend on private subjects or local actions? Manage URLs and folder subjects need an explicit public/private boundary.
- Should collection-specific subject representations and exact Catalogue navigation remain separate projections of a shared model? Their current validation and cardinality requirements differ.

Review semantic-token data, document-link data, and their UI actions against the same purpose/action/consumer/rules structure before deciding the target model. No consolidation implementation or broader data migration is specified here.
