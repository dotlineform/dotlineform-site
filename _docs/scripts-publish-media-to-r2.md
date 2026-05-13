---
doc_id: scripts-publish-media-to-r2
title: Publish Media To R2
added_date: 2026-05-08
last_updated: "2026-05-13 17:18"
parent_id: catalogue
sort_order: 180
hidden: false
---
# Publish Media To R2

Project-local entrypoint:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
```

The media-owned command publishes approved local media derivatives to Cloudflare R2.
It also provides an exact-id remote delete path for catalogue records that have been deleted locally.
It defaults to dry-run mode and requires `--write` before it uploads or deletes anything.

## Current Scope

The first implementation supports catalogue primary-image derivatives only:

- works
- work details
- moments

Docs media publishing is reserved for a later milestone.

## Credentials

The script reads R2 settings from `var/local/site.env` by default for local runs:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

It can also load additional files passed with `--env-file`.
If `var/local/site.env` is absent, it falls back to process environment variables for cloud/Codespaces runs.

`var/local/site.env` is gitignored and must not be committed.
When credentials are missing, the command reports the missing variable names but never prints configured values.

## Source And Target Mapping

Source files come from repo-local staged primary derivatives:

- `var/catalogue/media/works/srcset_images/primary/`
- `var/catalogue/media/work_details/srcset_images/primary/`
- `var/catalogue/media/moments/srcset_images/primary/`

The script reads `_data/pipeline.json` for those subpaths and `_config.yml` for remote media prefixes.
Default object-key mapping is:

- `works/img/<work_id>-primary-<width>.webp`
- `work_details/img/<detail_uid>-primary-<width>.webp`
- `moments/img/<moment_id>-primary-<width>.webp`

The expected catalogue primary widths are `800`, `1200`, and `1600`.
If a selected item is missing one of those variants, the item is blocked by default.
Use `--allow-partial` only when intentionally publishing an incomplete set.

## Usage

Preview one work:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
```

Preview all catalogue primary derivatives:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --all
```

Upload one work:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --write
```

Preview remote primary-variant deletion for one deleted work:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --delete
```

Delete remote primary variants for one deleted work:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --delete --write
```

Write a JSON report:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind moments --id keys --report-json var/local/r2-publish-report.json
```

Overwrite changed remote objects intentionally:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --force --write
```

## Safety Behavior

The publisher:

- reads from allowlisted derivative roots only
- refuses path traversal and symlink escapes
- checks remote object size and ETag against the local MD5 digest
- skips unchanged remote objects
- blocks changed remote objects unless `--force` is passed
- deletes remote objects only when `--delete --write` is passed with an exact `--kind` and `--id`
- keeps logs to ids, relative local paths, object keys, statuses, and non-secret reasons

Remote deletion is intentionally narrower than upload discovery.
It does not support `--all` because deleted local files may no longer exist for discovery, and broad remote cleanup should stay a deliberate operation.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
