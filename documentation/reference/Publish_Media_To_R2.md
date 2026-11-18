---
draft: false
doc_id: d-20260508-093841-3e27b1
title: Publish Media To R2
added_date: "2026-05-08 09:38:41"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6

---
# Publish Media To R2

[The media module](../../studio/services/media/publish_media_to_r2.py) owns both an explicit maintenance CLI and the R2 credential/client primitives reused by [artifact adapters](../../docs-viewer/services/docs_artifact_locations.py). Its CLI planning and normal publication have different workflow owners.

## Transport Ownership

| Caller | Work performed |
| --- | --- |
| Catalogue maintenance CLI | Discover selected Working primary renditions, compare exact remote keys, upload or explicitly delete |
| Docs exact-file CLI mode | Materialize one staged file into the selected document's local Working media |
| Normal Docs/Catalogue Publish | [SelectedTransfers](../../docs-viewer/services/docs_publication_transfer.py) uses the shared R2 client through configured adapters; it consumes finished queue selections and verifies exact transfers |

Studio local media completion owns canonical `media_version`; Refresh and Regenerate carry completed metadata onward, and [Publish](Builder.md#preview-and-deployment-boundary) transfers selected bytes. A changed existing rendition advances the version once; unchanged bytes and missing-rendition repair retain it. Calling this CLI neither advances versions nor updates document/consumer output or queues. [Version owner](../../studio/services/catalogue/catalogue_media_version.py) The selector `--scope catalogue|docs` is a transport domain, separate from retired Docs workspace scopes.

## Catalogue Maintenance

The CLI reads configured Working primary files, currently `working/assets/works/primary/` beneath the Docs workspace. Pipeline widths/suffix/format and site media prefixes select keys such as `works/img/<work_id>-primary-<width>.webp`. Selection is rendition-file based rather than a canonical Work read. It lists that local primary directory, confines files to it and computes selected sizes/MD5. It does not list the remote bucket; planning HEADs the exact keys.

From the repository root, plan one Work and deliberately apply its reviewed maintenance selection:

```bash
python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --write
```

Dry-run still requires credentials, reads local files and contacts R2. An existing equal-size/equal-ETag object is unchanged. Changed remote bytes are blocked until `--force`; missing required rendition groups are blocked unless `--allow-partial` is explicitly selected. `--all` intentionally broadens upload discovery; `--changed-only` affects reporting. Upload/block/failure statuses determine exit success.

Explicit `--delete` requires `--kind works --id <id>`; it HEADs deterministic configured rendition keys and deletes only with `--write`. It has no `--all` or partial-delete mode and does not select dependent legacy Details. Normal Publish owns its independently queued removals. A successful maintenance upload/delete reports transport completion, with no canonical version or queue handoff.

## Docs Exact-File Materialization

The Docs branch accepts `--kind img|files`, exact `--docs-doc-id`, one direct-child `--staged-filename` and optional `--docs-collection`. [The staged owner](../../docs-viewer/services/docs_media_storage.py) resolves the existing source target and configured import staging, then prepares `<doc_id>/<filename>` through the local media adapter. Its staging root is configured by the package workspace beneath the Projects base.

Use the [exported workspace environment](Local_Setup.md#environment) for this branch. For a configured named collection:

```bash
python3 studio/services/media/publish_media_to_r2.py --scope docs --docs-collection <collection> --docs-doc-id <doc-id> --kind files --staged-filename document.pdf
```

`--write` applies the local file change; differing local bytes require `--force`. It authors no link, creates no publication selection and sends nothing to R2. Ordinary Source Save and Import retain the normal linked-media workflow. This CLI has no Docs remote deletion or batch mode.

**Current gap:** omitting `--docs-collection` passes an empty collection field to the exact-target resolver, which rejects it. The ordinary-document example in the older guidance therefore does not work as written. The tracker records this code follow-up and the CLI's missing media-effect/queue integration; source inspection has not exercised either path. [Current media ownership](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Credentials, Reports And Verification

Catalogue CLI credentials come from `.env.local`, optional `--env-file` inputs and the environment. Missing configuration reports variable names. Keep credentials and signed request details local.

Results print to stdout. `--report-json <path>` deliberately writes a report, including during dry-run; no report file is written by default. Exact supported flags/statuses remain code-owned. The module's R2 client is live through normal publication adapters; retaining or changing the CLI requires tracing those consumers independently.

This review inspected current source and callers only. It performed no CLI execution, remote HEAD/list/upload/delete, credentials check or publication. Existing publisher tests contain retired Details/version-promotion and Docs-scope expectations; their review is separately tracked.
