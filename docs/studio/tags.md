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
- Alias browsing page:
  - `studio/tag-aliases/index.md`
  - `assets/js/tag-aliases.js`
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
  - canonical value format:
    - object with:
      - `description` (string)
      - `tags` (array of canonical `tag_id`, max 4, max 1 tag per group)
  - legacy values are still read for compatibility:
    - string (single canonical `tag_id`)
    - array of strings (multiple canonical `tag_id` values)

Example:

```json
{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-03-01T00:00:00Z",
  "aliases": {
    "floral": {
      "description": "flower-related shorthand",
      "tags": ["subject:flower"]
    },
    "signal": {
      "description": "",
      "tags": ["theme:signal", "domain:communication", "subject:wave"]
    }
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
- Alias contract:
  - alias key is lowercase slug-safe text
  - `tags` must contain 1-4 canonical tag IDs
  - max one tag per group (`subject/domain/form/theme`)
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
- import response includes `summary_text` and the same summary is written to `logs/tag_write_server.log`
- import response/log includes `import_filename` (basename only)
- clicking a tag pill opens an edit modal:
  - shows the tag group as a color-coded pill
  - edit canonical slug (group fixed)
  - `label` is auto-derived from slug
- tag row includes `<-` action to demote canonical tag into alias mapping
  - opens a demotion modal (not free-text prompt)
  - target tag picker uses the same autocomplete-style popup as alias edit:
    - search matches tag label/slug prefix
    - selecting adds removable target pills below the search field
    - current tag being demoted is excluded from available targets
  - demotion is blocked if alias key already exists (no overwrite allowed)
  - selected targets are sorted by canonical `tag_id` before submit
  - target constraints enforced in the modal: at least 1 target, max 4 targets, max 1 target per group
- tag row includes `×` action to delete canonical tag
  - opens a delete modal (same chip-remove button style as aliases page)
  - warns that delete also removes matching series assignments and alias target refs
  - warns that aliases left with no targets are deleted
  - in patch mode, modal remains available but delete is blocked with local-server-required status
- local-server mutation uses `POST /mutate-tag`
  - edit and delete modals show live impact previews via `POST /mutate-tag-preview` before confirm
  - slug edits update registry row and auto-refresh label
  - canonical rename cascades into `tag_assignments.json` and `tag_aliases.json`
  - delete removes tag from registry and removes references from assignments/aliases
  - aliases that become empty after delete are removed and reported in mutation stats (`aliases_removed_empty`)
  - aliases that become 1:1 self-maps (`alias == target slug`) are removed
- local-server demotion uses:
  - `POST /demote-tag-preview` (required before confirm)
  - `POST /demote-tag` (apply)
  - demotion removes canonical tag, creates alias `<slug> -> target tag_id(s)`, rewrites assignment refs and alias target refs

Tag Registry import modes:

- `Import mode: Local server`
  - uses `POST /import-tag-registry`
  - returns import result counts (imported, added, overwritten, unchanged, removed, final)
- `Import mode: Patch`
  - server unavailable fallback
  - generates copyable patch snippet for **new tags only**
  - does not attempt overwrite in manual mode

## Tag Aliases Page

The Studio Tag Aliases page (`/studio/tag-aliases/`) reads `assets/data/tag_aliases.json` and:

- lists aliases with columns: timestamp, alias, group tags
- renders alias values inline as color-coded pills in the `group tags` column
  - alias row supports one or more canonical target tags
  - single-group aliases use that group color
  - multi-group or unresolved aliases use warning color
  - known group-tag pills include `←` demote
  - alias pills include `→` promote
  - alias pills include `×` delete
  - clicking alias text opens edit modal:
    - live alias-name collision check
    - editable description
    - tag picker with autocomplete from registry only (no free-text tag IDs)
    - selected tags shown as removable pills
    - save enabled only when alias name, description, or selected tags change
    - alias tag constraints enforced: max 4 total, max 1 per group
- includes a group key above the list (`All tags` + group pills) to filter rows by mapped group
- supports search by alias prefix
- supports header sorting (timestamp/alias)
- supports import from a local JSON file (recommended from `assets/data/import`)
  - mode `add (no overwrite)`: add aliases with new key only
  - mode `replace`: replace the full aliases map
  - mode `add + overwrite`: add new aliases and overwrite matching keys, leaving other aliases untouched
- local-server import uses `POST /import-tag-aliases`
  - response includes `summary_text` and `import_filename` (basename only)
  - summary is written to `logs/tag_write_server.log`
- alias delete behavior:
  - local server mode uses `POST /delete-tag-alias`
  - patch mode provides copyable snippet with `aliases_to_remove`
- alias edit behavior:
  - local server mode uses `POST /mutate-tag-alias`
  - server validates alias uniqueness and registry-backed selected tags
  - patch mode provides ordered `set_alias`/`remove_alias_key` steps
- alias promotion behavior:
  - user chooses target group at action time
  - local server mode uses `POST /promote-tag-alias-preview` then `POST /promote-tag-alias`
  - canonical target id is `<group>:<alias-slug>`; label auto-derived from slug
  - if canonical exists already, promotion removes alias key only
  - patch mode provides ordered manual steps
- tag demotion behavior from aliases page:
  - trigger via `←` on known group-tag pills
  - local server mode uses `POST /demote-tag-preview` then `POST /demote-tag`
  - patch mode provides ordered manual steps
- import patch fallback mode provides a copyable snippet for **new aliases only**

## Series Tags Page

The Series Tags page (`/studio/series-tags/`) reads `assets/data/tag_assignments.json` and:

- lists series in alphabetical order by title
- links each series title to its Studio Series page
- shows assigned-tag count per series
- renders assigned tags as color-coded pills
- sorts tags alphabetically by label (fallback: tag id)
- uses an inline header key (`All tags` + group pills) in the tags column
- applies key filtering to visible tag pills only (series rows and counts remain unchanged)
