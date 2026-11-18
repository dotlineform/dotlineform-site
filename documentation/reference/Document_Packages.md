---
draft: false
doc_id: d-20260722-151224-7b61c4
title: Package Prepare
added_date: "2026-07-22 15:12:24"
last_updated: "2026-11-18"
parent_id: d-20260424-000000-50b63f
---

# Package Prepare

**Prepare package…** produces a structured exchange file from checked documents in a configured collection. **Import docs…** can apply a trusted edited return only when both the profile and that collection enable it. The checked-in return-enabled collection is Concepts. [Profiles](../../docs-viewer/config/document-packages/profiles.json) · [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) · [Design rationale](../design/Document_Import_And_Packages.md)

## Follow A Checked-Document Round Trip

1. In **Concepts**, choose **Select** and check two documents. Open **Collection Actions → Prepare package…**, pick **Document content**, choose JSONL and Markdown, and leave **Only documents missing summaries** off to include both. Check the final total. The modal freezes the checked collection and IDs, then submits the final explicit IDs after filtering. Display focus, descendants, Draft and Publish exclusions do not add or remove records. Checks remain after the action.
2. Send the file from `data-sharing/exports/` for editing. Keep the exact package header and both `doc_id` values, even if only one document gets a new Summary. A summary-only return keeps each row's ID and title, omits `content` for both and supplies `summary` only on the changed row. Returning the generated `content` would request a body replacement. [What survives](#package-output)
3. Put the complete returned file directly in `data-sharing/import-staging/` and open **Concepts → Collection Actions → Import docs…**. Select the return and inspect every planned overwrite. **Open in Docs Review** can render the return for separate read-only inspection. For a summary-only return, canonical body preservation belongs to Import. [Docs Review](Docs_Review.md)
4. Apply the entire plan once. The service writes the reviewed source changes to the existing IDs and awaits one selected collection rebuild. Check the affected documents in Concepts. Existing eligibility determines what generation prepares or updates in the publication queue. Publish is a separate action. [Working handoff](Builder.md#publish-preparation) · [Publish workflow](../guide/Publish_And_Deploy.md)

## Profiles

| Profile | Export shape | Return |
| --- | --- | --- |
| **Document content** (`document-content`) | JSONL by default, or JSON. Rendered-derived Markdown by default, or plain text. Optional **Only documents missing summaries** starts off and filters whitespace-only or empty source Summary. A body can be truncated at the configured 50,000-character paragraph boundary with `[truncated]`. | Supported for an opted-in collection with matching trusted metadata. |
| **Document tree** (`document-tree`) | JSON metadata without body. Application selection is flat and exact. | Export only. |

Neither profile currently sets a package-wide count or character limit. The Catalogue Management action allows HTML Export and hides Prepare package. [Collection action rules](../../docs-viewer/runtime/js/management/docs-viewer-action-definitions.js) · [HTML Export](Export.md)

## Package Output

The producer renders selected Markdown through the document builder before the format transform. It uses the shared static Catalogue preparer for content-bearing output, carrying adopted Work titles, captions, Entry and public media URLs into the transform. The package can preserve rendered prose, headings and links. Source-only Markdown constructs, exact formatting, reference tokens and media bytes do not round-trip through that rendering. Plain text and truncation lose more information. Keep `content` absent to preserve the canonical body.

The package flattens Summary whitespace into one paragraph for `current_summary`, `summary` and expanded Summary body text. Metadata retains authored emphasis markers as text. `current_summary` is comparison context. Applying the prepared `summary` can remove canonical line breaks. A returned multiline Summary is stored as multiline front matter. [Summary authoring](Builder.md#summary-block)

## Package Provenance

Prepare writes the external JSON/JSONL and an internal `meta/<export_id>.meta.json` under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`. The external file carries `export_id` at the JSON top level or in the first nonempty JSONL `data_sharing_header`. The local `data_sharing_export_meta_v4` sidecar records documents adapter, profile, container/content formats, capabilities, exact collection, selected IDs and their prepared `source_last_updated`. Keep the sidecar local. Filenames and returned row fields cannot choose a target. Collisions block a write. If provenance is missing, restore the matching sidecar or prepare a fresh package. [Metadata producer](../../docs-viewer/services/docs_document_packages/export_payloads.py) · [Return validation](../../docs-viewer/services/docs_document_packages/returned_validation.py)

## What A Return Can Overwrite

Each prepared ID must appear exactly once and still resolve to an existing member of the recorded collection. Row order can change. Changed prepared source timestamps, wrong collection, missing or extra records, invalid content, nonempty hierarchy fields or new asset plans block the whole return. Choose a fresh prepare if the canonical source changed, then reconcile the external edits against it.

| Return field | Effect on canonical source |
| --- | --- |
| `doc_id` | Selects the existing member. Its ID, source path, membership and added date stay in place. |
| `title` | Required. Can replace the title. Return the original value to keep it. |
| `summary` | Omit to preserve it. Supply a string to replace it. A blank string clears it. |
| `content` | Omit to preserve the body. Supply a string to replace the whole body. An empty replacement gets a title heading. A rendered or truncated export returned here can replace richer source. |

Destination-owned Draft, group, status and other local metadata stay with the canonical source. Local `last_updated` follows applied Title, Summary or body edits. A return cannot install or replace media bytes. A replacement body can change media references and thus the normal exact removal effects during generation. [Overwrite planner](../../docs-viewer/services/docs_import_document.py) · [Owned media removals](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

Apply revalidates the confirmed package and exact canonical targets. A changed plan needs review again. A write or rebuild failure triggers restoration of the selected source snapshot and regeneration of its prior projection, with the result recording restoration status. If generation completed but the publication handoff failed, check the saved result and address the queue or media error at its owner. The previous media comparison may be needed to recover a removal. [Package apply](../../docs-viewer/services/docs_import_collection_apply.py) · [Write and rebuild](../../docs-viewer/services/docs_write_rebuild.py) · [Media failure and queue ordering](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Implementation Boundary

The frontend owns checked selection and filters. `POST /docs/packages/prepare-options` resolves the exact collection and returns only the profiles and selected metadata needed by the modal. `POST /docs/packages/prepare` receives `collection`, `profile_id`, final explicit `doc_ids`, `target_format` and, for content profiles, `content_format`. The producer owns rendering, mapping and artifact writes. Preparation leaves source, generated documents, Search and the publication queue untouched. Canonical return uses the whole-package `POST /docs/import-source` flow. [Prepare service](../../docs-viewer/services/docs_document_packages/service.py) · [Return plan](../../docs-viewer/services/docs_import_document_package_collection.py) · [Docs Import](Docs_Import.md#import-a-trusted-collection)

## Prepare CLI

The independent ordinary Working CLI defaults to dry-run. Add `--write` to write package artifacts. It supports explicit IDs or `--all`, the content profile's missing-summary filter, and tree selection with descendant expansion. It has no Manage return path.

```bash
python3 docs-viewer/services/docs_document_packages/export.py --config-id document-content --doc-id <doc-id>
```

## Return Parser CLI

The parser reads a trusted staged package and prints a validation report. Add `--no-records` to omit normalized records. Exit codes are 0 for a valid report, 2 for a validation failure and 1 for an execution error. Use Manage to preview and apply canonical changes. [Parser](../../docs-viewer/services/docs_import.py)

```bash
python3 docs-viewer/services/docs_import.py --file document-content.jsonl
```
