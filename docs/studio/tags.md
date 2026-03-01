# Studio Tags

This document is the central reference for series-level tag editing in Studio Series pages (`/studio/studio-series/:series_id/`).

## Scope

- UI/editor logic: `assets/js/tag-studio.js`
- Index status logic (RAG): `assets/js/tag-studio-index.js`
- Layout/page wiring:
  - `_layouts/studio_series.html`
  - `studio/studio-series/index.html`
- Tag write service: `scripts/tag_write_server.py`
- Data contracts:
  - `assets/data/tag_registry_v1.json`
  - `assets/data/tag_aliases_v1.json`
  - `assets/data/tag_assignments_v1.json`

## Group Model

Groups are fixed and ordered in the editor code:

- `subject`
- `domain`
- `form`
- `theme`

Tags are canonical IDs in the format `<group>:<slug>`, for example `form:curvilinear`.

Source of truth for groups and tag definitions is `tag_registry_v1.json`:

- `policy.allowed_groups` defines allowed groups.
- `tags[]` defines tag entries:
  - `tag_id`
  - `group`
  - `label`
  - `status` (`active`, `deprecated`, `candidate`)
  - `description`

Editor behavior currently expects those four groups and uses `active` tags for input suggestions and group examples.

## Resolution and Aliases

When a user enters text, resolution is:

1. Canonical ID if input contains `:`
2. Alias lookup (`tag_aliases_v1.json`) using lowercased input
3. Registry slug match (part after `group:`)
4. Registry label match (case-insensitive normalized)

If multiple matches are found, the value is treated as ambiguous.
If no match is found, it is unresolved and save is blocked.

`tag_aliases_v1.json` maps shorthand inputs to canonical `tag_id` values:

- Version field: `tag_aliases_version`
- Update timestamp: `updated_at_utc`
- Map: `aliases`

## Metrics Currently Calculated

Two metric sets are in use.

### 1) Editor metrics (`tag-studio.js`)

Computed from current entry state:

- `groupCounts` by group
- `collisions`: duplicate canonical IDs
- `unresolvedCount`

Current save gate:

- Save disabled when `unresolvedCount > 0`
- Message: `Resolve unknown tags before saving.`

Current tags display only resolved tags (sorted alphabetically by label).

### 2) Index metrics / RAG (`tag-studio-index.js`)

Computed per series from `tag_assignments_v1.json` and registry lookup:

- `nTotal`: unique assigned tags
- group counts: `subject`, `domain`, `form`, `theme`
- `groupsPresent`
- `nUnknown`: tags not found in registry
- `nDeprecated`: tags with registry status not equal to `active`
- `completeness`:
  - base = `groupsPresent / 4`
  - tag bonus = up to `+0.25` capped by tag count

RAG rules in code:

- Red: `nTotal == 0` or `nUnknown > 0`
- Amber: one-group-only, too few tags (`nTotal < 3`), deprecated present, or both form+theme missing
- Green: otherwise

Tooltip includes tags/groups/missing/unknown/deprecated/completeness.

## Suggestions: Current Implementation

Suggestions are generated from missing groups only:

1. Compute editor `groupCounts`
2. For each missing group, take first 3 active tags from registry group list
3. Build a pool of those tags
4. While typing, show popup matches where `label` starts with typed prefix (normalized), max 12 shown

Interaction:

- Clicking a suggestion sets input text to the tag label
- It does not auto-add; user confirms via `Add` or Enter
- `Esc` or clicking outside closes popup

## Save Flow

Save mode is probed at page load:

- Health check: `GET http://127.0.0.1:8787/health` (500ms timeout)
- If available: `Save mode: Local server`
- Else: `Save mode: Patch`

### Local server mode

- Endpoint: `POST http://127.0.0.1:8787/save-tags`
- Payload:
  - `series_id`
  - `tags` (canonical IDs, may be empty to clear)
  - `client_time_utc`
- On success:
  - UI status message includes save timestamp
- On failure:
  - UI falls back to Patch mode and opens patch modal

### Patch mode

- Shows modal with:
  - canonical resolved tags array
  - JSON snippet to paste under `series[series_id]` in `tag_assignments_v1.json`
- Copy button uses `navigator.clipboard.writeText`

## Data Files: Purpose and Governance

### `assets/data/tag_registry_v1.json`

Purpose:

- Controlled vocabulary and policy for tags.

Governance:

- Maintained manually in repo.
- Should be updated deliberately with review because it defines allowed semantics used across editor/index.
- `updated_at_utc` should be bumped when changing tags/policy.

### `assets/data/tag_aliases_v1.json`

Purpose:

- Stable shorthand mappings to canonical tag IDs.

Governance:

- Maintained manually in repo.
- Keep aliases deterministic and unambiguous where possible.
- `updated_at_utc` should be bumped when aliases change.

### `assets/data/tag_assignments_v1.json`

Purpose:

- Per-series canonical tag assignments used by studio pages and index RAG.

Governance and maintenance:

- Generated/synced by `scripts/generate_work_pages.py` to ensure all series IDs exist with default `tags: []`.
- Updated interactively via:
  - patch workflow (manual paste), or
  - local save service (`scripts/tag_write_server.py`).
- Server writes are constrained to this file (plus `.bak` backup).
- Top-level `updated_at_utc` and per-series `updated_at_utc` must be kept current by writer flow.

## Operational Notes

- Editor always stores canonical IDs in save payload/snippet.
- Unknown/unresolved user inputs are blocked from save.
- Empty tag array is valid and means clear all tags for that series.

## Open Issues

- Suggestions only match prefix on label and only from "missing group examples"; this is intentionally narrow and will likely be refined.
- Ambiguous shorthand resolution is computed but not surfaced as a dedicated chooser UI yet.
- Editor metrics are internal (save gate + logic) and no longer shown as a user-facing metrics panel.
- Registry group list in JS is currently fixed to four groups; future policy changes would require coordinated code updates.

## Feature Requests

- Rich ambiguity chooser for multiple matches before adding a tag.
- Keyboard navigation for suggestion popup.
- Configurable suggestion strategies (beyond missing-group examples).
- Stronger server-side validation against registry (optional phase, currently client-side only).
- History/change log for tag assignment edits.

## Documentation Maintenance Rule

When studio tag behavior changes, update this document in the same change:

- UI logic (resolution, suggestions, save flow)
- RAG/metrics logic
- Data contract expectations
- Operational workflow (manual patch vs local server)

Keep `docs/scripts-overview.md` updated as well for command-level usage and script flags.
