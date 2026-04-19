---
doc_id: scripts-delete-moment
title: "Delete Moment"
last_updated: 2026-04-01
parent_id: scripts
sort_order: 80
---
# Delete Moment

Script:

```bash
./scripts/delete_moment.py --moment-id blue-sky
./scripts/delete_moment.py --moment-id blue-sky --write
./scripts/delete_moment.py --moment-id blue-sky --delete-source-prose --delete-source-image --write
```

## Behavior

- dry-run by default; pass `--write` to apply changes
- requires exactly one `--moment-id`
- deletes:
  - `_moments/<moment_id>.md`
  - `assets/moments/index/<moment_id>.json`
  - matching repo moment thumbs under `assets/moments/img/`
  - removes the moment from `assets/data/moments_index.json`
  - matching local staged/srcset moment media under `DOTLINEFORM_MEDIA_BASE_DIR` when configured
- rebuilds `assets/data/search/catalogue/index.json`
- leaves canonical source prose and source image untouched by default
- `--delete-source-prose` deletes `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md`
- `--delete-source-image` deletes the canonical source image resolved from front matter `image_file`, or `<moment_id>.jpg` by default

Intentionally left untouched:

- remote media under `https://media.dotlineform.com/moments/img/...`
- unrelated repo artifacts

## Flags

- `--moment-id MOMENT_ID`
  - required single slug-safe moment ID
- `--write`
  - apply changes; omit for dry-run
- `--delete-source-prose`
  - also delete the canonical source prose file
- `--delete-source-image`
  - also delete the canonical source image resolved from moment front matter
- `--repo-root PATH`
  - override repo-root auto-detection
- `--projects-base-dir PATH`
  - override canonical source base dir
- `--media-base-dir PATH`
  - override local media base dir used for staged/srcset cleanup

## Source And Target Artifacts

Source artifacts:

- `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md`
- optional canonical source image under `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/images/`
- `_moments/<moment_id>.md`
- `assets/moments/index/<moment_id>.json`
- `assets/moments/img/<moment_id>-thumb-*.*`
- `assets/data/moments_index.json`
- local moment staged/srcset media under `DOTLINEFORM_MEDIA_BASE_DIR`

Target artifacts on `--write`:

- deletion or rewrite of the artifacts above
- timestamped backups in `var/delete_moment/backups/YYYYMMDD-HHMMSS/`
- rebuilt `assets/data/search/catalogue/index.json`

## Backups

- `--write` creates timestamped backups under `var/delete_moment/backups/YYYYMMDD-HHMMSS/`
- backups preserve repo-relative paths for repo files and scoped `projects/` or `media/` relative paths for canonical source and local media files when possible

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
