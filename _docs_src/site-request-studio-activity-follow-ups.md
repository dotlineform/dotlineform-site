---
doc_id: site-request-studio-activity-follow-ups
title: Studio Activity Follow-Ups
added_date: 2026-05-08
last_updated: "2026-05-08 21:04"
ui_status: proposed
parent_id: change-requests
sort_order: 209
viewable: true
---
# Studio Activity Follow-Ups

Status:

- proposed

## Summary

This request holds activity-log work that remains outside the closed [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log).

The unified `/studio/activity/` surface is now implemented and is the only active Studio activity report.
This follow-up exists so optional expansion and cleanup work can be tracked without keeping the original implementation request open.

## Scope

This request covers activity-report improvements that are useful but not required for the closed unified activity milestone:

- bulk catalogue save activity rows
- readiness prose and media action activity rows
- background watcher/source-change attribution
- explicit terminal-script run context
- R2 media publish/delete activity when triggered from Studio
- optional future write surfaces when those surfaces become writable
- small naming cleanups that make activity attribution easier to understand

## Work Items

| Item | Scope | Status | Notes |
|---|---|---|---|
| Bulk work save activity | `/studio/catalogue-work/` bulk mode `#catalogueWorkSave` | planned | Record grouped counts, affected work ids, rebuild attempts, lookup refresh, and search update rows without flooding the modal. |
| Bulk work-detail save activity | `/studio/catalogue-work-detail/` bulk mode `#catalogueWorkDetailSave` | planned | Group detail ids by parent work so rebuild/search rows stay understandable. |
| Work prose import activity | `/studio/catalogue-work/` readiness `data-prose-import="work"` | planned | Record source prose writes, overwrite backups, and blocked/no-op outcomes. |
| Work media refresh activity | `/studio/catalogue-work/` readiness `data-media-refresh="work"` | planned | Distinguish missing source media, blocked derivative generation, successful local derivative refresh, and public thumbnail staging. |
| Detail media refresh activity | `/studio/catalogue-work-detail/` readiness `data-media-refresh="detail"` | planned | Keep detail media rows separate from metadata save rows and include parent-work context where useful. |
| Series prose import activity | `/studio/catalogue-series/` readiness `data-prose-import="series"` | planned | Mirror work prose import behavior with series id and primary-work context. |
| Moment prose and media readiness activity | `/studio/catalogue-moment/` readiness actions | planned | Keep staged moment import coverage separate from later readiness prose/media refresh rows. |
| Background docs rebuild attribution | docs source changes after user editing | future | Add only when the event can carry meaningful source context such as edited doc id or source file, rather than pretending a Studio button click happened. |
| Jekyll/site watcher attribution | local filesystem changes | future | Only useful when correlated to a Studio action or explicit user command. |
| Manual terminal script context | direct shell command | future | Could emit activity rows later if scripts accept an explicit run context and avoid local path or payload leakage. |
| R2 media publish/delete activity | future Studio-triggered media publishing | future | Add when a Studio workflow can trigger R2 publish/delete through the local service without exposing credentials to browser code. |
| Future writable review surfaces | tag groups, catalogue field registry, or similar pages | future | Keep excluded while the pages are read-only; add activity rows if write actions are introduced. |
| `lookup_refresh` naming cleanup | catalogue write responses | done | Moment save responses now report `moment_build_invalidation` instead of `lookup_refresh`, and moment publication skips the shared Studio lookup refresh path. Moment save/publication/delete activity contracts explicitly describe moment runtime/search work without implying Studio lookup payload writes. |

## Acceptance Criteria

Each implemented item should:

- add or update `assets/studio/data/activity_contract.json`
- preserve initiating page/action context through previews and confirmations
- keep preview-only commands excluded when they do not persist data
- write concise activity detail items without raw payloads, credentials, or local absolute paths
- add targeted tests for row shape, grouping, and registry coverage
- update the owning Studio docs and this request

## Risks

- bulk actions can make the activity modal noisy unless rows summarize groups carefully
- readiness media actions often have blocked or partial outcomes, so status wording needs to distinguish warning from failure
- background watcher rows can imply false causality unless the source context is explicit
- terminal-script activity can leak local paths if report fields are not sanitized
