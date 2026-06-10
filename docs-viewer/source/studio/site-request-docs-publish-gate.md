---
doc_id: site-request-docs-publish-gate
title: Docs Public Publish Gate
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: in-progress
parent_id: change-requests
---
# Docs Public Publish Gate

## Summary

Public Docs Viewer scopes currently publish as soon as their generated payloads are rebuilt.
That is useful for local manage-mode review, but it gives public routes no explicit publish step.

Add a Docs Viewer publish gate for public scopes.
The working generated payloads should be Docs Viewer-owned and should update immediately for manage mode, the live public payloads should update only when a user runs a deliberate `Publish docs` action.

The first implementation should be local and file-based.
Later, the same user action could trigger a GitHub Actions build or deploy workflow, but that is out of scope for v1.

## Problem

Current public scopes such as `library` and `analysis` write generated docs and search payloads directly under:

```text
assets/data/docs/scopes/<scope>/
assets/data/search/<scope>/index.json
```

Those paths are also the public route data paths.
When a public-scope source doc changes and the Docs live rebuild watcher or manage-mode rebuild runs, the public site data changes immediately.

This creates three problems:

- public docs can change as a side effect of local editing or local watcher activity
- manage-mode preview and public publication are coupled to the same generated files
- a future static hosting workflow has no clear publish boundary to map onto a deploy/build action

## Goals

- Keep fast local manage-mode rebuild behavior for public scopes.
- Add an explicit publish step before public routes see changed public-scope docs.
- Make `docs-viewer/generated/` the working generated root for all Docs Viewer scopes, including public scopes.
- Keep `assets/data/docs/` and `assets/data/search/` as the public published snapshot roots.
- Let `/docs/?scope=<public-scope>&mode=manage` preview unpublished generated changes.
- Keep `/library/` and `/analysis/` reading only the published public snapshot.
- Provide clear status evidence for unpublished changes before publish.
- Keep the publish operation allowlisted by configured public scope and safe paths.

## Non-Goals

- Do not add GitHub Actions triggering in v1.
- Do not change the public route payload shape.
- Do not change `viewable: false` semantics.
- Do not introduce draft branches, remote deploy credentials, or multi-user approval.
- Do not make Jekyll responsible for Docs Viewer payload generation.
- Do not add rollback, unpublish, persistent publish manifests, or persistent publish summary artifacts in v1.
- Do not keep compatibility warnings or dual-output compatibility behavior for old public-scope builder output paths.

## Proposed Model

Separate each public scope into two artifact roots:

| Layer | Purpose | Example |
| --- | --- | --- |
| Working generated | Local manage-mode preview and rebuild target | `docs-viewer/generated/docs/library/` |
| Working generated search | Local manage-mode search preview | `docs-viewer/generated/search/library/index.json` |
| Published docs snapshot | Public route data | `assets/data/docs/scopes/library/` |
| Published search snapshot | Public route search data | `assets/data/search/library/index.json` |

For local scopes such as `studio`, the working generated root remains the route data root.
No public publish step is needed.

For public scopes, `build_docs.py`, `build_search.py`, Docs management rebuilds, and the live rebuild watcher should write working generated payloads only.
The publish action copies the working generated docs and search artifacts into the public snapshot roots.
The live watcher should keep watching the same source roots under `docs-viewer/source/...`; only the public-scope output roots change.

## Scope Config

`docs-viewer/config/scopes/docs_scopes.json` should distinguish generated and published paths for public scopes.

One possible shape:

```json
{
  "scope_id": "library",
  "scope_type": "public",
  "source": "docs-viewer/source/library",
  "output": "docs-viewer/generated/docs/library",
  "search_output": "docs-viewer/generated/search/library/index.json",
  "publish_output": "assets/data/docs/scopes/library",
  "publish_search_output": "assets/data/search/library/index.json"
}
```

The exact field names can change during implementation, but the ownership split should ensure that:

- builder output is working generated data
- publish output is public route data
- public scopes must have explicit publish output paths
- local scopes must not accidentally publish

`build_docs.py --scope <public> --write` and `build_search.py --scope <public> --write` should move to working generated output directly.
They should not keep compatibility warnings or dual writes for the old public asset output paths.

## Publish Action

Add a local Docs Viewer publish operation for public scopes.
Publish confirmation is enough for v1; no stored confirmation id is needed.
Publish apply should revalidate the current plan before writing.

Inputs:

- scope id
- optional dry-run flag

Validation:

- scope exists
- scope is public
- working generated docs root exists
- working generated search payload exists
- publish roots are configured and repo-relative
- source and destination paths stay inside allowlisted roots

Confirmation output:

- files that would be added, changed, removed, or left unchanged
- generated root and publish root paths
- search payload status
- warnings for missing generated artifacts

Write output:

- sync working generated docs payloads to the public docs snapshot root
- sync working generated search payload to the public search snapshot path
- remove stale published by-id payloads that no longer exist in the working generated root

The published snapshot should not include a persistent manifest or publish summary artifact in v1.

The publish operation should be atomic enough for local development:

- write changed files to temporary paths before replacing
- avoid partially removed output when validation fails
- report failures clearly without mutating source docs

## Scope Lifecycle

Existing `New scope` and `Delete scope` actions must understand the new path split.

For public scopes, create preview/apply should plan and validate both:

- working generated docs/search paths under `docs-viewer/generated/`
- published docs/search snapshot paths under `assets/data/`

For local scopes, create preview/apply should continue to create only working generated paths and must not configure publish paths.

Delete preview/apply should show and remove all manifest-owned paths for a deleted user-created scope:

- source root
- working generated docs root
- working generated search payload
- public route file/config when present
- published docs snapshot root when the deleted scope is public
- published search snapshot when the deleted scope is public

System-owned scopes still must not be delete-eligible.
All lifecycle path handling must remain repo-relative and allowlisted by scope mode.

## Admin Checks Target Map

This request adds new target-map surface area even if the public routes themselves do not change.

Expected route ids remain:

- `/docs/`
- `/library/`
- `/analysis/`

Expected families also likely remain the existing technical families, especially:

- `build`
- `config`
- `runtime-js`
- `services`
- `tests`

Implementation should update `admin-app/checks/config/admin-checks.json` for any new publish-gate files and then run the target-map audit.
Start by mapping publish-gate files into the existing `docs-build`, `management`, and `config` areas where those names are accurate.
Add a new area such as `publishing` only if the final file set makes publication a distinct workflow that would be unclear or under-mapped under the existing areas.

## UI

Add a restrained manage-mode command for public scopes:

```text
Publish docs
```

This should appear only when:

- manage mode is available
- the selected scope is public
- the local Docs Viewer service supports the publish endpoint

The command should:

1. Request publish confirmation data.
2. Show a confirmation modal with changed counts and destination paths.
3. Run the publish apply endpoint after confirmation; apply revalidates the current plan before writing.
4. Show the result summary.
5. Reload public-scope manage generated data if needed.

The public `/library/` and `/analysis/` routes must not show publish controls or call publish endpoints.

## API And Scripts

Likely local management endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/docs/publish/status?scope=<scope>` | Report whether working generated output differs from the published snapshot. |
| `POST` | `/docs/publish/confirm` | Return confirmation data for a public scope. |
| `POST` | `/docs/publish/apply` | Revalidate and apply the current publish plan. |

Likely script owner:

```text
docs-viewer/services/docs_publish.py
```

This script should own path validation, diff planning, copy/sync behavior, and stale-file removal.
Endpoint modules should stay thin.

## Public Route Contract

Public routes continue to read:

```text
assets/data/docs/scopes/<scope>/
assets/data/search/<scope>/index.json
```

They must not fall back to `docs-viewer/generated/`.
The publish gate is only meaningful if public routes cannot see unpublished working generated payloads.

Manage mode can read the working generated roots through the existing Docs Viewer service/generated-read boundary.

## Cross-Scope Links

Docs may link across scopes.
The builder should keep rewriting same-scope doc links onto the current scope route and preserving cross-scope viewer links for the target scope.

The publish gate should not make public cross-scope links load unpublished working generated payloads.
For example, a published `/analysis/` doc linking to `/library/?doc=<doc_id>` should stay on the public `/library/` route and read the published Library snapshot.

Manage-mode links are different:

- same-scope manage navigation should keep using the active manage context and working generated payloads
- cross-scope links to public routes should remain public route links unless the source explicitly links to `/docs/?scope=<target>&mode=manage`
- source Markdown links should not need to include `mode=manage`

Because there may be no current public cross-scope examples, this request should add focused fixtures or tests for cross-scope link rewriting and route behavior.

Non-public tooling must not treat published public snapshots as source-of-truth data.
Data Sharing has already moved away from public `index-tree.json` reads and should continue to use its Docs Viewer source-metadata helper.
Docs Viewer reports and management tooling, including the broken-links report, should read working generated payloads through configured Docs Viewer output roots.
If any current non-public consumer still reads public `by-id/<doc_id>.json` payloads, it should move to one of these owners:

- working generated payloads under `docs-viewer/generated/docs/<scope>/by-id/` when it needs rendered preview payloads
- Docs Viewer source metadata helpers when it needs document records, summaries, hierarchy, or export data

The only intended consumers of published `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` after this request are public read-only routes.

## Implementation Plan

Implementation is tracked in [Docs Public Publish Gate Implementation Plan](/docs/?scope=studio&doc=site-request-docs-publish-gate-implementation-plan).

## Follow-On

- Consider a GitHub-backed publish target where `Publish docs` triggers an allowlisted workflow instead of copying local files.
