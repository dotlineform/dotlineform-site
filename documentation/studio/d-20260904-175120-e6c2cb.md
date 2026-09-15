---
draft: false
doc_id: d-20260904-175120-e6c2cb
title: R2 Workspace Backups
added_date: "2026-09-04 17:51:20"
last_updated: "2026-09-04 17:51:20"
summary: Back up selected external workspace folders to private R2 storage with retained history and a defined restore path.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# R2 Workspace Backups

Provide an off-machine backup of selected external workspace folders, initially `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/`, with other folders considered explicitly. Preserve editable sources, media and the state needed for recovery, including work that has not been published.

## Basic Approach

- Use rclone to copy local files into a dedicated private R2 bucket, separate from public media. The recent Catalogue archive demonstrated R2/rclone compatibility; backing up local folders would upload their contents over the network.
- Start with dated, complete snapshots as the simplest proposed restore model. Each completed snapshot retains the selected folder hierarchy and can be downloaded independently. Earlier snapshots remain available when local files are changed or deleted.
- Make Backup independently runnable. An optional Publish/Deploy hook could follow, but backups should also cover unpublished work and should not change Build, Publish or deployment semantics.
- Show progress, completion/failure and the last successful backup. An interrupted upload must not appear as a completed recovery point.
- Restore a chosen snapshot into a separate local folder for inspection before explicitly replacing working data.

This backs up original workspace files. Browser-readable HTML Export and the frozen public Catalogue archive remain separate capabilities.

## Issues And Decisions

| question | consideration |
| --- | --- |
| What is included? | Confirm whole scopes, sub-scopes and media coverage. Decide whether to retain rebuildable `generated/` output and accepted `published/` snapshots. Catalogue sources/media and other external folders need explicit inclusion. Repository configuration may also be needed to restore a usable workspace. |
| Full or incremental history? | Complete snapshots are easy to restore but duplicate unchanged files. Incremental backups reduce transfer/storage at the cost of more recovery logic. R2 does not currently provide S3 object versioning, so retained history must be managed explicitly. |
| When does backup run? | Choose manual operation, a schedule or optional workflow hooks. A Publish-only trigger would miss unpublished work. |
| Is the snapshot consistent? | iCloud files must be locally available. Decide how to handle edits, watcher builds or Publish writes during copying, unavailable folders and interrupted runs. |
| How long is history kept? | Define retention and deletion behavior before automatic cleanup. Estimate cost from retained snapshot size and request volume; consider whether R2 retention locks are useful. |
| How is access controlled? | Keep the bucket private and credentials outside tracked files. Decide whether client-side encryption is needed and how its recovery key would be retained. |
| Does recovery work? | Define the restore procedure and exercise it with real source/media before relying on the backup. Transfer success alone does not demonstrate a usable restored workspace. |

## References

- [Cloudflare rclone setup](https://developers.cloudflare.com/r2/examples/rclone/)
- [Rclone retained-file options](https://rclone.org/docs/#backup-dir-string)
- [R2 S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/), [pricing](https://developers.cloudflare.com/r2/pricing/) and [retention locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/)

Proposed only. Folder selection, history, retention, restore and workflow integration remain open; no backup job or storage change has been implemented.
