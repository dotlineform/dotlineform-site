---
draft: false
doc_id: d-20260508-093841-3e27b1
title: Publish Media To R2
added_date: "2026-05-08 09:38:41"
last_updated: "2026-11-19"
parent_id: d-20260423-000000-d015e6

---
# Publish Media To R2

The maintenance CLI plans Catalogue R2 operations and Docs Working file copies. The shared R2 client owns credential loading, request signing and object transport for the CLI and the artifact adapters. Docs and Catalogue use shared helpers for file checksums and content types. [Maintenance CLI](../../studio/services/media/publish_media_to_r2.py) · [R2 client](../../studio/shared/python/r2_client.py) · [Artifact adapters](../../docs-viewer/services/docs_artifact_locations.py) · [File helpers](../../studio/shared/python/media_files.py)

## Transport Ownership

| Caller | Work performed |
| --- | --- |
| Catalogue maintenance CLI | Discover selected Working primary renditions, compare exact remote keys, upload or explicitly delete |
| Docs exact-file CLI mode | Materialize one staged file into the selected document's local Working media |
| Normal Docs/Catalogue Publish | [SelectedTransfers](../../docs-viewer/services/docs_publication_transfer.py) uses the shared R2 client through configured adapters; it consumes finished queue selections and verifies exact transfers |

Studio local media completion owns canonical `media_version`; Refresh and Regenerate carry completed metadata onward, and [Publish](Builder.md#preview-and-deployment-boundary) transfers selected bytes. A changed existing rendition advances the version once; unchanged bytes and missing-rendition repair retain it. Calling this CLI neither advances versions nor updates document/consumer output or queues. [Version owner](../../studio/services/catalogue/catalogue_media_version.py) The selector `--scope catalogue|docs` is a transport domain, separate from retired Docs workspace scopes.

## Catalogue Maintenance

Each Catalogue upload or delete plan loads the selected repository's pipeline widths, suffix, output format and site media prefixes once. Those settings select keys such as `works/img/<work_id>-primary-<width>.webp`. Upload discovery lists the configured Working primary directory, currently `working/assets/works/primary/` beneath the Docs workspace. It confines selected files to that directory and computes their sizes and MD5 checksums. Both plans use HEAD for the exact remote keys.

From the repository root, plan one Work and deliberately apply its reviewed maintenance selection:

```bash
python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --write
```

Dry-run still requires credentials, reads local files and contacts R2. An existing equal-size/equal-ETag object is unchanged. Changed remote bytes are blocked until `--force`; missing required rendition groups are blocked unless `--allow-partial` is explicitly selected. `--all` intentionally broadens upload discovery; `--changed-only` affects reporting. Upload/block/failure statuses determine exit success.

Explicit `--delete` requires `--kind works --id <id>`; it HEADs deterministic configured rendition keys and deletes only with `--write`. It has no `--all` or partial-delete mode and does not select dependent legacy Details. Normal Publish owns its independently queued removals. A successful maintenance upload/delete reports transport completion, with no canonical version or queue handoff.

## Docs Exact-File Materialization

The Docs branch accepts `--kind img|files`, exact `--docs-doc-id`, one direct-child `--staged-filename` and optional `--docs-collection`. [The staged owner](../../docs-viewer/services/docs_media_storage.py) resolves the existing source target and configured import staging, then prepares `<doc_id>/<filename>` through the local media adapter. Its staging root is configured by the package workspace beneath the Projects base.

Omit `--docs-collection` for an ordinary document. Supply the configured collection ID for a named collection. Run either command with the exported workspace environment. [Environment setup](Local_Setup.md#environment)

```bash
python3 studio/services/media/publish_media_to_r2.py --scope docs --docs-doc-id <doc-id> --kind files --staged-filename document.pdf
python3 studio/services/media/publish_media_to_r2.py --scope docs --docs-collection <collection> --docs-doc-id <doc-id> --kind files --staged-filename document.pdf
```

Use this command for manual maintenance of one local Working file. `--write` applies and verifies the copy. Replacing differing Working bytes requires `--force`. The terminal report identifies the operation as **Docs Working media materialization**.

For a new attachment, use **Add image** or **Add file** and **Save** to add the source reference and queue eligible media. For a file the saved document already references, **Edit doc → Rebuild** selects the current referenced media for an eligible document. **Publish** reads the current Working bytes of each selected file, including a file that was already queued when the CLI replaced it. [Add a new image or download](Media_And_Asset_Handling.md#add-a-new-image-or-download) · [Build and Publish flow](Builder.md#docs-build-flow)

## Credentials, Reports And Verification

Catalogue CLI credentials come from `.env.local`, optional `--env-file` inputs and the environment. Missing configuration reports variable names. Keep credentials and signed request details local.

Results print to stdout. `--report-json <path>` deliberately writes a report, including during dry-run; no report file is written by default. Exact supported flags/statuses remain code-owned.

Dry runs using temporary staging verified target resolution and local media planning for an ordinary document and a Concepts document. Local Catalogue plans for Work `01007` produced the same upload and deletion keys before and after the R2 transport extraction. Import checks exercised shared client construction with sample credentials.
