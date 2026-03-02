# Studio Tags

This document is the central reference for series-level tag editing in Studio Series pages (`/studio/studio-series/:series_id/`).

## Scope

- UI/editor logic: `assets/js/tag-studio.js`
- Index status logic (RAG): `assets/js/tag-studio-index.js`
- Layout/page wiring:
  - `_layouts/studio_series.html`
  - `studio/studio-series/index.html`
- Registry browsing page:
  - `studio/tag-registry/index.md`
  - `assets/js/tag-registry.js`
- Series assignments overview page:
  - `studio/series-tags/index.md`
  - `assets/js/series-tags.js`
- Tag write service: `scripts/tag_write_server.py`
- Data contracts:
  - `assets/data/tag_registry.json`
  - `assets/data/tag_aliases.json`
  - `assets/data/tag_assignments.json`

## Group Model

Groups are fixed and ordered in the editor code:

- `subject`
- `domain`
- `form`
- `theme`

Tags are canonical IDs in the format `<group>:<slug>`, for example `form:curvilinear`.

Source of truth for groups and tag definitions is `tag_registry.json`:

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
2. Alias lookup (`tag_aliases.json`) using lowercased input
3. Registry slug match (part after `group:`)
4. Registry label match (case-insensitive normalized)

If multiple matches are found, the value is treated as ambiguous.
If no match is found, it is unresolved and save is blocked.
For alias arrays, one valid target resolves directly; multiple valid targets are treated as ambiguous.

`tag_aliases.json` maps shorthand inputs to canonical `tag_id` values:

- Version field: `tag_aliases_version`
- Update timestamp: `updated_at_utc`
- Map: `aliases`
  - value may be either:
    - string (single canonical `tag_id`)
    - array of strings (multiple canonical `tag_id` values)

Example:

```json
{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-03-01T00:00:00Z",
  "aliases": {
    "floral": "subject:flower",
    "signal": ["theme:signal", "domain:communication", "subject:wave"]
  }
}
```

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

Computed per series from `tag_assignments.json` and registry lookup:

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

- Health check against local save service (500ms timeout)
- If available: `Save mode: Local server`
- Else: `Save mode: Patch`

### Local server mode

- Endpoint: `POST /save-tags` on the local save service
- Payload:
  - `series_id`
  - `tags` (canonical IDs, may be empty to clear)
  - `client_time_utc`
- On success:
  - UI status message includes save timestamp
- On failure:
  - UI falls back to Patch mode and opens patch modal
- Local write operations are logged to `logs/tag_write_server.log` (JSONL).

### Patch mode

- Shows modal with:
  - canonical resolved tags array
  - JSON snippet to paste under `series[series_id]` in `tag_assignments.json`
- Copy button uses `navigator.clipboard.writeText`

## Data Files: Purpose and Governance

### `assets/data/tag_registry.json`

Purpose:

- Controlled vocabulary and policy for tags.

Governance:

- Maintained manually in repo.
- Should be updated deliberately with review because it defines allowed semantics used across editor/index.
- `updated_at_utc` should be bumped when changing tags/policy.

### `assets/data/tag_aliases.json`

Purpose:

- Stable shorthand mappings to canonical tag IDs.

Governance:

- Maintained manually in repo.
- Keep aliases deterministic and unambiguous where possible.
- `updated_at_utc` should be bumped when aliases change.

### `assets/data/tag_assignments.json`

Purpose:

- Per-series canonical tag assignments used by studio pages and index RAG.

Governance and maintenance:

- Generated/synced by `scripts/generate_work_pages.py` to ensure all series IDs exist with default `tags: []`.
- Updated interactively via:
  - patch workflow (manual paste), or
  - local save service (`scripts/tag_write_server.py`).
- Server writes are constrained to this file, with timestamped backups in `assets/data/backups/`.
- Top-level `updated_at_utc` and per-series `updated_at_utc` must be kept current by writer flow.
- Script change events are logged in `logs/`:
  - `logs/tag_write_server.log`
  - `logs/run_draft_pipeline.log`
  - `logs/generate_work_pages.log`
  - retention: 30 days, with fallback to keep the latest 1 day's entries when activity is older than 30 days.

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
- Surface persisted server log entries directly in Studio UI.

## Documentation Maintenance Rule

When studio tag behavior changes, update this document in the same change:

- UI logic (resolution, suggestions, save flow)
- RAG/metrics logic
- Data contract expectations
- Operational workflow (manual patch vs local server)

Keep `docs/scripts-overview.md` updated as well for command-level usage and script flags.

## Tag Registry Page

The Studio Tag Registry page (`/studio/tag-registry/`) reads `assets/data/tag_registry.json` and:

- lists tags with columns: timestamp, tag, description
- default sort is alphabetical by tag label
- supports header click sorting (timestamp/tag/description, asc/desc)
- displays group color coding using the same chip palette as Studio Series
- shows a group key above the list
- supports key-button filtering by group
- provides an `All tags` button to clear filter
- supports import from a local JSON file (recommended from `assets/data/import`)
  - mode `add (no overwrite)`: add tags with new `tag_id` only, keep existing entries unchanged
  - mode `replace`: replace the full tag list
  - mode `add + overwrite`: add new tags and overwrite matching `tag_id` entries, leaving other entries untouched
- local-server import writes update timestamps:
  - top-level `updated_at_utc`
  - per-tag `updated_at_utc` for added/overwritten tags

Tag Registry import modes:

- `Import mode: Local server`
  - uses `POST /import-tag-registry`
  - returns import result counts (imported, added, overwritten, unchanged, removed, final)
- `Import mode: Patch`
  - server unavailable fallback
  - generates copyable patch snippet for **new tags only**
  - does not attempt overwrite in manual mode

## Series Tags Page

The Series Tags page (`/studio/series-tags/`) reads `assets/data/tag_assignments.json` and:

- lists series in alphabetical order by title
- links each series title to its Studio Series page
- shows assigned-tag count per series
- renders assigned tags as color-coded pills
- sorts tags alphabetically by label (fallback: tag id)
- uses an inline header key (`All tags` + group pills) in the tags column
- applies key filtering to visible tag pills only (series rows and counts remain unchanged)
