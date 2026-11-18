---
draft: false
doc_id: d-20260508-093841-3e27b1
title: Publish Media To R2
added_date: "2026-05-08 09:38:41"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6

---
# Publish Media To R2

## Transport Ownership

`studio/services/media/publish_media_to_r2.py` provides Catalogue remote comparison, upload and exact operator-requested deletion. It is a maintenance transport, not the normal Catalogue Save workflow or the owner of media versions.

Studio Save prepares required rendition sets and records dimensions and versions. Refresh Catalogue hands their selected bytes to Working. Docs Viewer **Publish** distributes completed queued selections. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#current-workflow) · [Catalogue Deployment](Catalogue_Deployment.md#current-lifecycle)

The CLI retains a separate `--scope docs` mode. Despite the command's historical name, that mode materializes one staged file into the local shared Docs assets; it does not publish it to R2. The domain selector is not a retired Docs scope identity.

## Catalogue Maintenance

The local upload source is the configured Working primary tree at `$DOTLINEFORM_DOCS_BASE_DIR/working/assets/works/primary/`. The pipeline and site configuration own rendition widths and object naming.

```text
works/img/<work_id>-primary-<width>.webp
```

Preview one Work, then deliberately apply the reviewed maintenance operation:

```bash
python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --write
```

Changed remote objects require `--force`; matching bytes are skipped. Incomplete required variant groups are blocked unless the operator explicitly permits partial CLI transfer. No transfer, including a partial transfer, advances canonical versions or refreshes generated JSON. Retired Detail media has no active publisher kind.

The maintenance CLI accepts one exact Work for remote deletion with `--delete --write`. Normal Publish applies its own queued removals, including exact media removals. [Catalogue deployment](Catalogue_Deployment.md#per-work-publish) · [Document media removals](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Versions Belong To Local Completion

Works carry positive canonical `media_version` values, used as primary URL cache tokens. Local preparation compares completed rendition bytes with existing local renditions. A difference in an existing rendition advances the Work version once; unchanged bytes and missing-rendition repair retain it. Prepared bytes, dimensions and versions use the Catalogue transaction owner together. Failed preparation does not promote an incomplete set.

Upload and copy operations preserve those versions. Do not infer a new content revision from a missing remote object, retransmission or deployment outcome. [Catalogue Media Pipeline Config](Catalogue_Media_Pipeline_Config.md) owns derivative policy.

## Docs Exact-File Materialization

The Docs mode reads one direct-child file from shared import staging and prepares it for the exact owning document in Working through `docs_media_storage.py`. Supply the document ID in both planning and write commands.

```bash
python3 studio/services/media/publish_media_to_r2.py --scope docs --docs-doc-id <doc-id> --kind files --staged-filename document.pdf
python3 studio/services/media/publish_media_to_r2.py --scope docs --docs-doc-id <doc-id> --kind files --staged-filename document.pdf --write
```

Use `--docs-collection <id>` for a configured collection. There is no `--docs-scope`, Docs `--all` or Docs remote-delete operation. Changed local bytes require `--force`. The command does not author a document link, prepare Preview or distribute public media; those remain with the [Docs media workflow](Media_And_Asset_Handling.md).

## Credentials And Safety

Catalogue R2 operations load settings from `.env.local`, optional `--env-file` inputs and the configured environment. Missing variables are named; configured values and signed transport details remain private.

For credential rotation use the provider's current [Roll tokens instructions](https://developers.cloudflare.com/fundamentals/api/how-to/roll-token/). Update the corresponding local secrets and restart the owning service before verifying access. Never copy credentials into tracked documentation or reports.

The transport confines local inputs, rejects traversal and symlink escapes, defaults to dry-run, requires `--write` for mutation and compares size and ETag/MD5 before selecting remote changes. Reports contain non-secret identifiers and statuses. Run `--help` for supported maintenance options. [Publish and deploy](../guide/Publish_And_Deploy.md) covers the normal release path.
