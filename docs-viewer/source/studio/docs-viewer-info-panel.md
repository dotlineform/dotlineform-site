---
doc_id: docs-viewer-info-panel
title: Docs Viewer Info Panel
added_date: "2026-06-04 11:43"
last_updated: "2026-06-04 11:43"
parent_id: change-requests
---
# Docs Viewer Info Panel

status: to be implemented

## New behaviour

The public info panel should not mirror the manage-mode metadata surface. For public read-only routes, the info panel should display only public reader-facing document data:

- `title`
- `summary`
- `last updated`

## Design

- the info panel should read from `by-id` payloads, not public index rows, not `index.json`. this should be a consistent principle for both local and public routes.
- keep manage mode compatible with the shared runtime while allowing local/manage projections to be richer than public projections
- preserve public route behavior for tree navigation, selected document loading, search, recently-added, and info-panel opening

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned |  |

## Acceptance Criteria

- public info panel reads summary from by-id payloads, not public index rows
- public info panel shows only reader-facing metadata
- public read-only routes do not load management-only JS/CSS or management service data
- manage mode still opens and edits metadata through its existing management surfaces