---
draft: false
doc_id: d-20260629-152159-ac1af9
title: Export
added_date: "2026-06-29 15:21:59"
last_updated: "2026-11-18"
summary: create guarded dated HTML snapshots from checked collection documents and their referenced media
parent_id: d-20260424-000000-50b63f
---

# Export

**Collection Actions → Export…** creates a dated static HTML snapshot from checked collection documents in Manage, including Catalogue. Choose **Select**, check the desired rows, then open Actions. **All** works within the filtered collection view. Checks retained across page or filter changes are included. Export captures the exact collection and checked IDs when invoked. It leaves source, generated documents, discovery and publication state unchanged. [Document packages](Document_Packages.md)

## Input And Eligibility

The service reads the Working collection's generated `manage-manifest.json` and selected by-ID payloads. It uses manifest order, even for a partial selection. Draft and publication-excluded rows are eligible when present in Manage. Rebuild first if the generated rendering is behind the saved source. Missing selected output or referenced owned media blocks Export. [Exact generation](Builder.md#exact-generation)

## Destination And Replacement

The snapshot lives under `$DOTLINEFORM_PROJECTS_BASE_DIR/dotlineform-site/docs-export/`. A single document uses `<document title> - YYYY-MM-DD`. Multiple documents use `<collection title> - YYYY-MM-DD` for a complete selection or `<collection title> selection - YYYY-MM-DD` for a partial one. Labels are confined and normalized for filenames. The date is the server's local date.

Preview shows the destination and counts of packaged media and unchanged external dependencies. **Create snapshot** writes an absent destination. An existing directory requires explicit **Replace**, including a user-owned directory with the same name. Replacement removes other contents and preserves ordinary `.DS_Store` files. A non-directory blocks the operation. A changed selection payload, media file or destination requires a fresh preview.

Apply writes the confirmed directory in place and writes `snapshot.json` last. If writing or verification fails, the completion manifest is removed and the partial directory remains. Fix the failure, preview again and use **Replace**. Snapshot folders are user-owned and are managed in the filesystem.

## Artifact Contract

A single document gets a title-named root HTML page. Multiple documents get an `index.html` and `docs/<doc_id>.html` pages in manifest order, with the first selected document as default. Both layouts include `styles.css`, `snapshot.json`, and `portable.html`. Referenced owned media is copied once into deterministic `media/` paths. The manifest records the exact selection and copied/external dependencies.

The browseable pages retain rendered body, heading fragments, expanded Summary formatting and copied media. Same-collection links to selected documents become relative links. Other viewer and external destinations remain links to their original targets. Unmatched external media is left referenced and recorded. The export resolves supported media URLs in generated markup and does not recursively collect assets from linked pages or HTML companions.

`portable.html` is a self-contained, text-first reader for devices where multi-file local navigation is unreliable. It inlines styles, links selected documents by article fragment, shows images as alt-text placeholders and prints a reusable viewer Markdown link for each document. Both views use a 50ch reading width for Moments and apply the generated verse/axis styles. [Design rationale](../design/Document_Import_And_Packages.md#two-kinds-of-export)

Catalogue references use the shared static preparer. The browseable result includes Work Entry, captions, the standard image rendition, currently 800 px, and exact linked files emitted in the selected markup. Work openers point to that packaged rendition. It does not package every Gallery member. [Catalogue presentation](Generated_Data_Contracts.md#catalogue-reference-and-presentation)

## Service Boundary

`POST /docs/export/static-html/preview` receives `collection` and explicit `doc_ids`. `POST /docs/export/static-html/apply` carries the same target, local `export_date`, `plan_revision`, `target_revision`, `confirm: true` and explicit `replace_existing`. Apply recomputes the selected bytes and target revision before replacement. It verifies the final file set and bytes, including the `docs_static_html_snapshot_v3` completion manifest. [Workflow](../../docs-viewer/runtime/js/management/docs-viewer-collection-export-workflow.js) · [Snapshot writer](../../docs-viewer/services/docs_static_html_export.py) · [Media owner](../../docs-viewer/services/docs_static_html_export_media.py)

This action exports checked documents. Book curation and editions have their own owners. [Books](Collections_And_Books.md) · [Whole-Book export follow-on](../deliveries/Collections_Books_And_Reports_Review.md)
