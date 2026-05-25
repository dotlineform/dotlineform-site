---
doc_id: site-request-local-report-snapshot-boundary
title: Local Report Snapshot Boundary
added_date: 2026-05-25
last_updated: 2026-05-25
ui_status: planned
parent_id: change-requests
sort_order: 9500
viewable: true
---
# Local Report Snapshot Boundary

Status:

- planned

## Summary

Generated local report snapshots should not live in the Docs Viewer source tree just because they are Markdown.

The current examples are:

- `docs-viewer/source/studio/project-state.md`
- `docs-viewer/source/studio/audit-latest.md`
- `docs-viewer/source/studio/css-audit-latest.md`

These files are generated operational output, not authored documentation.
They are currently kept out of generated Docs Viewer payloads with `published: false`, but that makes the Docs Viewer source folder carry two different responsibilities:

- authored docs and draft docs
- latest-run report snapshots

The implementation should move latest-run report snapshots to a local operational output path and leave Docs Viewer source for authored docs.

## Background

The docs source model now has two different visibility fields:

- `published`
- `viewable`

`published` is the older pipeline-inclusion field.
`published: false` means the source Markdown is excluded before Docs Viewer JSON/search payloads are generated.

`viewable` was added later to solve a different problem: generated docs that should exist in Docs Viewer manage mode but stay hidden from public/default discovery.
`viewable: false` is useful when a doc is still part of the generated Docs Viewer corpus and should be reviewable in manage mode.

That distinction matters here.
Generated latest report snapshots are not draft docs that need manage-mode review.
They are local run output.
Using `published: false` for them works mechanically, but it is a weak ownership signal.

Relevant current docs:

- [Viewability Workflow Spec](/docs/?scope=studio&doc=docs-viewer-draft-publishing-spec)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)

## Current Behavior

Project State:

- `studio/services/catalogue/project_state_report.py` writes `docs-viewer/source/studio/project-state.md` by default.
- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report) documents that path and describes the generated document as a local artifact with `published: false`.
- `/studio/project-state/?mode=manage` reports the same output path in the UI.

Site Consistency Audit:

- `studio/checks/audit_site_consistency.py` defaults Markdown output to `docs-viewer/source/studio/audit-latest.md`.
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency) documents that output path.
- `audit-latest.md` does not declare a `doc_id`, which reinforces that it is not normal Docs Viewer source.

CSS Token Audit:

- `studio/checks/css_token_audit.py` defaults Markdown output to `docs-viewer/source/studio/css-audit-latest.md`.
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit) documents that output path.

## Proposed Direction

Move generated latest report snapshots to a local operational report path, probably under `var/`.

Candidate target:

```text
var/studio/reports/
```

Candidate files:

```text
var/studio/reports/project-state.md
var/studio/reports/audit-latest.md
var/studio/reports/css-audit-latest.md
```

This keeps report snapshots with other local working output, backups, staging, and run summaries.
It also avoids making Docs Viewer source cleanup depend on whether a generated report happens to be Markdown.

## Implementation Notes

This should be a small ownership cleanup, not a broad report redesign.

Expected changes:

- update default Markdown output paths in:
  - `studio/services/catalogue/project_state_report.py`
  - `studio/checks/audit_site_consistency.py`
  - `studio/checks/css_token_audit.py`
- update Local Studio Project State UI copy/default path display if it hardcodes the old source path
- update script docs that currently advertise Docs Viewer source output paths
- remove or stop regenerating the old `docs-viewer/source/studio/*-latest.md` report snapshots
- decide whether any old generated snapshots should be deleted in the implementation slice or left for a separate cleanup commit

Do not change the meaning of `published` or `viewable` as part of this request.

Do not move authored unpublished docs.
Authored working notes can still use `published: false` when they intentionally remain source-only and excluded from generated Docs Viewer payloads.

## Acceptance Criteria

- latest report snapshots no longer default to `docs-viewer/source/studio/`
- Project State, Site Consistency Audit, and CSS Token Audit docs name the new report output paths
- Project State UI reports or opens the new report path correctly
- `docs-viewer/source/studio/` no longer contains generated latest-run report snapshots after the cleanup
- `published: false` remains available for authored source-only docs
- `viewable: false` remains the mechanism for generated-but-hidden/manage-reviewable docs
- targeted checks cover updated script defaults and any UI path assumptions

## Risks

- local workflows or habits may still look for the old Docs Viewer source paths
- scripts or tests may have hidden hardcoded references to `audit-latest.md`, `css-audit-latest.md`, or `project-state.md`
- deleting tracked report snapshots could remove historical context if the latest reports have been used as durable records rather than ephemeral output

## Verification Plan

Use focused checks:

- search for old output paths after implementation
- syntax-check changed Python scripts
- run dry-run or targeted report generation for each affected script when practical
- smoke the Project State route if UI path handling changes
- run `git diff --check`

## Related References

- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report)
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit)
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Viewability Workflow Spec](/docs/?scope=studio&doc=docs-viewer-draft-publishing-spec)
