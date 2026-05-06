---
doc_id: scripts-studio-backup-retention
title: Studio Backup Retention
added_date: 2026-05-04
last_updated: "2026-05-06 20:41"
parent_id: studio
sort_order: 56
---
# Studio Backup Retention

Script:

```bash
./scripts/studio_backup_retention.py
```

## Purpose

`scripts/studio_backup_retention.py` prunes local Studio backup files so untracked backup folders do not grow indefinitely.

It manages:

- `var/studio/backups/`
- `var/studio/catalogue/backups/`

These backups are local operational safety files created by the Studio tag and catalogue write services.
They are not canonical source and are not committed.

## Retention Policy

The script keeps backups by target file rather than by operation type.

Defaults:

- `var/studio/backups/`: keep the newest `20` backups per target file
- `var/studio/catalogue/backups/`: keep the newest `30` backups per target file

For catalogue backup bundles, the script keeps a whole bundle if any file inside that bundle is still inside the newest-N retention set for its original target path.
It deletes a bundle only when every target inside the bundle has newer retained backups.

The script uses timestamps parsed from backup filenames and bundle directory names.
It does not use filesystem modification time because copied backup files can preserve older source mtimes.

Unparseable backup files or bundles are skipped and reported.
Known local filesystem metadata such as `.DS_Store` is ignored.

## Commands

Preview cleanup:

```bash
./scripts/studio_backup_retention.py --dry-run
```

Apply cleanup:

```bash
./scripts/studio_backup_retention.py --write
```

Override retention counts:

```bash
./scripts/studio_backup_retention.py --dry-run --studio-keep 20 --catalogue-keep 30
```

## Dev Studio Startup

`bin/dev-studio` runs backup retention once during startup before the long-running services start:

```bash
./scripts/studio_backup_retention.py --write --quiet
```

If cleanup fails, `bin/dev-studio` prints a warning and continues startup.

Disable startup retention for one session:

```bash
DOTLINEFORM_BACKUP_RETENTION=off bin/dev-studio
```

`DOTLINEFORM_BACKUP_RETENTION=0` is also accepted.

## Verification

Focused checks:

```bash
./tests/python/test_studio_backup_retention.py
```

The `quick` profile also runs the focused retention check:

```bash
./scripts/run_checks.py --profile quick
```
