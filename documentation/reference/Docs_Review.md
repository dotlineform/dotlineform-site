---
draft: false
doc_id: d-20260711-214307-b4c800
title: Docs Review
added_date: 2026-07-11 21:43:07
last_updated: "2026-11-18"
summary: Durable product, workflow, persistent package, explicit Build, source-open, and authority contract for the local returned-package review route.
parent_id: d-20260424-000000-50b63f

---

# Docs Review

Docs Review displays a validated returned package at `/docs-review/?package=<package_id>&doc=<doc_id>`. It reuses the reader with a package provider. The package service validates a staged return and materializes its local source and generated preview. Review's operations stay within that package. [Prepare and return](Document_Packages.md)

## Open And Inspect A Package

1. In the owning collection's **Import docs…** chooser, select a server-declared reviewable returned package and choose **Open in Docs Review**. The handoff prepares or reuses its validated retained projection and opens a new tab.
2. Inspect the package tree, content and Assets inventory. `package` remains in Review navigation, and `doc` selects the exact record inside it.
3. Use the VS Code control to open that exact package source. After external edits, choose **Build** to regenerate the complete package preview and reload the selected document.
4. To apply accepted edits, copy the complete package `source/` folder into import staging and confirm its overwrite plan through the owning collection's **Import docs…** action. [Edited-source Import](#optional-edited-source-round-trip)

`DOCS_VIEWER_REVIEW_ENABLED` independently enables the package APIs. `local-all` defaults it on. The standalone service defaults it off. The shell may load while disabled APIs return 403, so check the health flag when Review is unavailable. [Local startup](Local_Setup.md#environment)

## Package Contract

Packages live under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/<package_id>/`.

```text
manifest.json
source/<doc_id>.md
generated/index-tree.json
generated/by-id/<doc_id>.json
assets/...
inventories/assets.json
inventories/links.json
inventories/embedded-content.json
```

The manifest uses `docs_review_validated_package_v4`, matching package/folder identity, `status: validated`, explicit capability flags, `source_collection` and the exact `selected_doc_ids`. The source files must be direct, nonsymlink Markdown children with safe unique IDs and matching filenames. The exact source set must equal the manifest selection. Optional inventories describe package-local assets. The package-list envelope is `docs_review_packages_v3`. [Package reader](../../docs-viewer/services/docs_review_packages.py) · [Current provenance](../../docs-viewer/services/docs_document_packages/provenance.py)

Materialized source carries `review_folder_id`, `review_source_export_id`, `review_profile_id` and, for a named owner, `review_source_collection`. Its dates describe the review projection. The local prepare metadata separately retains canonical source versions for later Import. Rendered-derived source can omit source-only constructs and media. [Source materializer](../../docs-viewer/services/docs_document_packages/review_sources.py) · [Package fidelity](Document_Packages.md#package-output)

## Build And Asset Rendering

Initial materialization builds in a temporary sibling directory and exposes the completed package with a rename. Explicit **Build** renders the complete retained `source/` into that package's `generated/`. Ordinary reads reuse healthy generated JSON and rebuild package-local output when the requested JSON is absent or malformed. Source edits require explicit Build to refresh otherwise readable output. [Materialization](../../docs-viewer/services/docs_review_materialization.py) · [Review builder](../../docs-viewer/services/docs_review_build.py)

The synthetic builder preserves package-record identity and package-rooted routes. Media resolves through its declared inventory. Interactive HTML runs in a sandboxed iframe with scripts allowed. Source-open launches VS Code for the exact package/document member. The shared renderer and configured asset boundary own the resulting preview.

A Build error can leave incomplete generated files because explicit rebuilding writes in place. Correct the package source or output problem and retry Build on the same package. Canonical comparison and Import retain their independent owners.

## Review Authority

| Operation | Authority |
| --- | --- |
| List, manifest, inventory and generated reads | Inspect the validated package and its declared assets. |
| Build or conditional generated repair | Write only the package's derived preview. |
| Open source | Launch VS Code for one exact package-local source file. External editing changes that retained projection. |
| Canonical acceptance | The owning Manage Import independently validates and confirms the complete returned selection. |

The capability response always reports `canonical_write`, `management` and `publish` as false. Healthy Review output establishes what the package renders. The Import planner establishes which canonical fields and existing IDs can change. [Review dispatcher](../../docs-viewer/services/docs_review_service.py) · [Import fields and recovery](Document_Packages.md#what-a-return-can-overwrite)

The current **Open canonical** control is produced only when the manifest's `source_collection` is empty. Named collection packages, including Concepts returns, currently lack that shortcut. Compare through the normal Manage route with the exact collection and ID. This gap is recorded for code review. [Control owner](../../docs-viewer/runtime/js/review/docs-viewer-review-controller.js) · [Follow-ups](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)

## Optional Edited-Source Round Trip

Keep the complete source set, IDs, review provenance and projection dates intact while editing body, Title and Summary. Build and inspect the retained projection, then stage the complete `source/` folder. Its reviewed entry resolves the original prepare metadata and retained manifest before planning exact existing-member overwrites. The original JSON/JSONL return can also use direct Import. [Return planner](../../docs-viewer/services/docs_import_review_source_folder.py) · [Complete package workflow](Document_Packages.md#follow-a-checked-document-round-trip)

## API Surface

All routes are beneath `/docs-review/` and use the separate Review enablement/origin boundary.

| Method and suffix | Input and behavior |
| --- | --- |
| GET `capabilities`, `packages` | External workspace/capability status, or validated package list with rejected-folder diagnostics. |
| GET `packages/manifest`, `packages/assets`, `packages/index-tree` | `package_id`; manifest, optional inventories or generated tree. |
| GET `packages/payload` | `package_id` and `doc_id`; exact generated payload. |
| GET `packages/assets-content/<package_id>/<asset-path>` | A declared, confined existing package asset. |
| POST `packages/build` | JSON containing `package_id`; complete package-local generation. |
| POST `packages/open-source` | `package_id` and `doc_id`; exact VS Code handoff. |

Disabled APIs return 403, missing input 404, invalid contracts 400 and execution failures 500. JSON responses use `no-store`. The management-side `POST /docs/packages/returned/review` owns the selected Import-row handoff. [Route constants](../../docs-viewer/services/docs_review_routes.py) · [Service boundary](../../docs-viewer/services/docs_viewer_service.py) · [Earlier evidence](../deliveries/Document_Grammar_And_Review_Delivery.md)
