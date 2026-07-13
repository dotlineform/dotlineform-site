---
doc_id: scripts-publish-media-to-r2
title: Publish Media To R2
added_date: 2026-05-08
last_updated: 2026-07-13
parent_id: studio
viewable: true
---
# Publish Media To R2

Project-local entrypoint:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
```

The media-owned command publishes approved local media derivatives to Cloudflare R2.
It also provides an exact-id remote delete path for catalogue records that have been deleted locally.
It defaults to dry-run mode and requires `--write` before it uploads or deletes anything.

## Current Scope

The first implementation supports catalogue primary-image derivatives only:

- works
- work details

Docs media publishing is reserved for a later milestone.

## Credentials

The script reads R2 settings from `.env.local` by default for local runs:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

It can also load additional files passed with `--env-file`.
If `.env.local` is absent, it falls back to process environment variables for cloud/Codespaces runs.

`.env.local` is gitignored and must not be committed.
When credentials are missing, the command reports the missing variable names but never prints configured values.

## Source And Target Mapping

Source files come from external staged primary derivatives:

- `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/works/srcset_images/primary/`
- `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/work_details/srcset_images/primary/`

The publisher has no repo-local staging fallback.
Local Studio serves staged image previews through `/studio/media/catalogue/...`, mapped directly to this external root.

The script reads the shared pipeline config for those subpaths and `site-tools/config/site-tools.json` for remote media prefixes.
Default object-key mapping is:

- `works/img/<work_id>-primary-<width>.webp`
- `work_details/img/<detail_uid>-primary-<width>.webp`

The expected catalogue primary widths are `800`, `1200`, and `1600`.
If a selected item is missing one of those variants, the item is blocked by default.
Use `--allow-partial` only for an intentional incomplete remote write; a partial set is never promoted as the confirmed public version.

## Confirmed Media Versions

Each media-bearing work and work detail has a positive canonical `media_version`.
All primary widths for one item share that version, and public work/detail routes append it to R2 primary `src`, full-size links, and `srcset` entries as `?v=<media_version>`.

Write-mode upload behavior is:

- the complete required local width set must be present before the item can be promoted
- when at least one required R2 object is uploaded or overwritten and every required object succeeds, the publisher increments the item's canonical version once
- the publisher then rebuilds the owning `site/assets/works/index/<work_id>.json`; work-detail versions remain nested in that work payload
- when every remote object already matches, the publisher rebuilds the current version without incrementing it
- failed, blocked, or partial groups do not change the confirmed version

Ordinary Studio Save and local derivative generation do not increment this value.
The optional JSON report includes a `media_versions` section describing promotion, current-version rebuilds, and non-promoted or failed groups.

## Usage

Preview one work:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
```

Preview all catalogue primary derivatives:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --all
```

Upload one work:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --write
```

Preview remote primary-variant deletion for one deleted work:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --delete
```

Delete remote primary variants for one deleted work:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --delete --write
```

Write a JSON report:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind work_details --id 00001-003 --report-json var/local/r2-publish-report.json
```

Overwrite changed remote objects intentionally:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007 --force --write
```

## Safety Behavior

The publisher:

- reads from allowlisted derivative roots only
- refuses path traversal and symlink escapes
- checks remote object size and ETag against the local MD5 digest
- skips unchanged remote objects
- blocks changed remote objects unless `--force` is passed
- promotes the canonical media version only after the complete required primary set succeeds
- deletes remote objects only when `--delete --write` is passed with an exact `--kind` and `--id`
- keeps logs to ids, relative local paths, object keys, statuses, and non-secret reasons

Remote deletion is intentionally narrower than upload discovery.
It does not support `--all` because deleted local files may no longer exist for discovery, and broad remote cleanup should stay a deliberate operation.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
