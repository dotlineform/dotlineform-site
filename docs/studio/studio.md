# Studio

This document is the central reference for series-level tags plus per-work override editing in the Series Tag Editor page (`/studio/series-tag-editor/?series=:series_id`).

Related references:

- `docs/studio/ui-framework.md` for shared Studio UI primitives and naming rules
- `docs/studio/regression-checklist.md` for manual verification coverage

## Local Development

Use the repo-local runner from `dotlineform-site/`:

```bash
bin/dev-studio
```

What it does:

- starts Jekyll on `127.0.0.1:4000`
- starts `scripts/studio/tag_write_server.py`
- keeps both processes attached to the current terminal so their output stays visible
- stops both processes when you press `Ctrl+C`

Default URLs:

- site: `http://127.0.0.1:4000`
- Series Tag Editor: `http://127.0.0.1:4000/studio/series-tag-editor/?series=<series_id>`

Notes:

- this runner does not enable `--livereload`
- use a manual browser refresh after JS/template changes
- Studio editing remains stable because tag writes do not force a browser reload

## Scope

- UI/editor controller: `assets/studio/js/tag-studio.js`
- Editor domain/state helpers: `assets/studio/js/tag-studio-domain.js`
- Editor save helpers: `assets/studio/js/tag-studio-save.js`
- Index status logic (RAG): `assets/studio/js/tag-studio-index.js`
- Shared Studio config loader: `assets/studio/js/studio-config.js`
- Shared Studio data helpers: `assets/studio/js/studio-data.js`
- Shared Studio transport helpers: `assets/studio/js/studio-transport.js`
- Layout/page wiring:
  - `studio/series-tag-editor/index.md`
  - `assets/studio/js/series-tag-editor-page.js`
- Registry browsing page:
  - `studio/tag-registry/index.md`
  - `assets/studio/js/tag-registry.js`
  - `assets/studio/js/tag-registry-domain.js`
  - `assets/studio/js/tag-registry-save.js`
  - `assets/studio/js/tag-registry-service.js`
- Alias browsing page:
  - `studio/tag-aliases/index.md`
  - `assets/studio/js/tag-aliases.js`
  - `assets/studio/js/tag-aliases-domain.js`
  - `assets/studio/js/tag-aliases-save.js`
  - `assets/studio/js/tag-aliases-service.js`
- Series assignments overview page:
  - `studio/series-tags/index.md`
  - `assets/studio/js/series-tags.js`
- Works curator page:
  - `studio/studio-works/index.md`
  - `assets/studio/js/studio-works.js`
- Group descriptions reference page:
  - `studio/tag-groups/index.md`
  - `assets/studio/js/tag-groups.js`
- Tag write service: `scripts/studio/tag_write_server.py`
- Data contracts:
  - `assets/studio/data/studio_config.json`
  - `assets/studio/data/tag_registry.json`
  - `assets/studio/data/tag_aliases.json`
  - `assets/studio/data/tag_assignments.json`

## Studio Config

`assets/studio/data/studio_config.json` is the Studio-specific config file for:

- public data paths used by Studio pages
- public route paths used across Studio links
- RAG scoring thresholds and completeness math
- Studio UI copy overrides

The file is loaded by `assets/studio/js/studio-config.js`, which also resolves configured root-relative paths against the site base path at runtime.

Current config scope:

- `paths.data.studio`
  - `tag_registry`
  - `tag_aliases`
  - `tag_assignments`
  - `tag_groups`
- `paths.data.site`
  - `series_index`
  - `works_index`
- `paths.routes`
  - `series_tag_editor`
  - `tag_groups`
  - additional Studio/site route bases reserved for future wiring
- `analysis.groups`
  - ordered group list
  - coverage group list
- `analysis.rag`
  - deprecated-status handling
  - completeness formula parameters
  - red/amber thresholds
- `ui_text.series_tag_editor`
  - editor shell labels/placeholders
  - contextual hint copy
  - save-mode/status/error strings
  - tokenized templates such as `{mode}` and `{saved_at}`
- `ui_text.tag_registry`
  - import, search, filter, table-heading, and modal labels
  - edit/delete/demote validation and status strings
  - confirm and import-parser error text
  - import-mode/status/patch-result strings
- `ui_text.tag_aliases`
  - import, search, filter, table-heading, and modal labels
  - edit/promote/demote validation and status strings
  - confirm/prompt and import-parser error text
  - import-mode/status/patch-result strings
- `ui_text.series_tags`
  - table headings
  - filter/empty/error text
- `ui_text.tag_groups`
  - empty/error text
  - long-description fallback copy

The config is intended to decouple Studio from current file placement and from selected UI copy. Studio-owned JSON files and key copy on the Series Tag Editor, Series Tags, Tag Registry, Tag Aliases, and Tag Groups pages are no longer hard-coded in those modules.

`assets/studio/js/studio-config.js` exports `getStudioText(config, key, fallback, tokens)` for Studio pages:

- `key` is a dot-path under `ui_text`, for example `series_tag_editor.context_hint_default`
- `fallback` is used when the config key is missing
- `tokens` optionally replaces placeholders like `{mode}` or `{saved_count}`

## Shared Data and Transport Modules

`assets/studio/js/studio-data.js` centralizes the low-level Studio JSON access and common data-shaping helpers used across Studio pages. Current shared responsibilities include:

- fetching Studio/site JSON payloads from config-derived paths
- registry lookup building
- group description normalization
- assignments-series access and series tag extraction

`assets/studio/js/studio-transport.js` centralizes local write-service concerns. Current shared responsibilities include:

- local endpoint definitions
- health probing for local write availability
- shared JSON POST transport

These modules are now used by the smaller Studio pages plus the larger `tag-registry.js`, `tag-aliases.js`, and `tag-studio.js` controller. They are intended to reduce repeated fetch/parse and local-write transport logic before larger controller splits in those feature modules.

## Series Tag Editor Module Split

The Series Tag Editor now separates responsibilities across three modules:

- `assets/studio/js/tag-studio.js`
  - page controller
  - initial data load
  - shell rendering and event wiring
  - modal open/close and status rendering
- `assets/studio/js/tag-studio-domain.js`
  - tag and assignment normalization
  - registry/assignment lookups
  - work-state cloning and diff calculation
  - group-aware sorting and display comparisons
- `assets/studio/js/tag-studio-save.js`
  - local write POST call for tag saves
  - patch snippet generation
  - save-mode and save-success message formatting

This split is intended to keep DOM concerns in the controller while isolating pure business/state logic and save mechanics into smaller, reusable modules.

The Series Tag Editor also persists work selection in the page URL:

- `series`
  - current series id
- `works`
  - comma-separated selected work ids
- `active`
  - currently active work id

Selection state is restored from those query params on load and rewritten with `history.replaceState` when the selected/active work changes. This is intended to preserve editor selection across local LiveReload refreshes.

## Registry Module Split

The Tag Registry page now separates responsibilities across:

- `assets/studio/js/tag-registry.js`
  - page controller
  - modal state
  - render and event wiring
- `assets/studio/js/tag-registry-domain.js`
  - registry normalization
  - filter/sort helpers
  - validation/query helpers
- `assets/studio/js/tag-registry-save.js`
  - patch builders
  - import payload parsing
  - summary/message helpers
- `assets/studio/js/tag-registry-service.js`
  - async mutation and preview workflows

## Alias Module Split

The Tag Aliases page now separates responsibilities across:

- `assets/studio/js/tag-aliases.js`
  - page controller
  - modal state
  - render and event wiring
- `assets/studio/js/tag-aliases-domain.js`
  - alias normalization
  - registry/group lookup shaping
  - filter/sort helpers
  - alias/tag validation helpers
- `assets/studio/js/tag-aliases-save.js`
  - patch builders
  - alias import parsing
  - import-mode and summary helpers
- `assets/studio/js/tag-aliases-service.js`
  - async import, delete, edit, promote, and demote workflows

## Group Model

Groups are configured in `studio_config.json` and currently ordered as:

- `subject`
- `domain`
- `form`
- `theme`

Tags are canonical IDs in the format `<group>:<slug>`, for example `form:curvilinear`.

Source of truth is split as follows:

- `studio_config.json`
  - Studio group ordering used by the UI and analysis logic
- `tag_registry.json`
  - allowed vocabulary and tag definitions
- `tag_groups.json`
  - group descriptions and long-form guidance

`tag_registry.json` remains the vocabulary source of truth:

- `policy.allowed_groups` defines allowed groups.
- `tags[]` defines tag entries:
  - `tag_id`
  - `group`
  - `label`
  - `status` (`active`, `deprecated`, `candidate`)
  - `description`

Editor behavior currently expects those four groups and uses `active` tags for input suggestions.

## Resolution and Aliases

When a user enters text, resolution is:

1. Canonical ID if input contains `:`
2. Alias lookup (`tag_aliases.json`) using lowercased input
3. Registry slug match (part after `group:`)
4. Registry label match (case-insensitive normalized)

If multiple matches are found, the value is treated as ambiguous.
If no match is found, it is unresolved and save is blocked.
For alias arrays, one valid target resolves directly; multiple valid targets require selecting one canonical target from autocomplete.

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

Computed from the selected work override state:

- `unresolvedCount`

Current save gate:

- Save disabled when no work is selected
- Save disabled when `unresolvedCount > 0`

Current tags display in fixed rows (`subject`, `domain`, `form`, `theme`):

- series tags are always shown for context
- when no work is selected, series tags use the normal group color chips
- when a work is selected, inherited series tags switch to monochrome chips
- work override tags stay group-colored and removable

Work override chips include a `w_manual` dot control:
- white = `0.3`
- amber = `0.6`
- green = `0.9`
- click cycles `0.3 -> 0.6 -> 0.9 -> 0.3`

### 2) Index metrics / RAG (`tag-studio-index.js`)

Computed per series from `tag_assignments.json`, registry lookup, and `studio_config.json`:

- `nTotal`: unique assigned tags
- group counts: `subject`, `domain`, `form`, `theme`
- `groupsPresent`
- `nUnknown`: tags not found in registry
- `nDeprecated`: tags whose registry status is listed in `studio_config.json` as deprecated-like (currently `deprecated` and `candidate`)
- `completeness`:
  - denominator, tag-bonus cap, and score cap come from `studio_config.json`

RAG rules are configured in `studio_config.json`:

- Red: currently `nTotal == 0` or `nUnknown > 0`
- Amber: currently one-group-only, too few tags (`nTotal < 3`), deprecated present, or both form+theme missing
- Green: otherwise

Tooltip includes tags/groups/missing/unknown/deprecated/completeness.

## Suggestions: Current Implementation

While typing in `Add Tag`, autocomplete shows two sections in one popup:

1. `tags` section:
   - matches active tags by `slug` prefix only
   - rendered as group-colored pills
2. `aliases` section:
   - matches alias keys by alias prefix
   - each alias row shows:
     - alias pill (neutral white/grey style)
     - vertical list of group-colored canonical target tag pills for that alias
   - alias rows are laid out horizontally with wrapping (like tag pills)

Interaction:

- Clicking a tag pill adds that canonical tag immediately
- Clicking an alias target pill adds that canonical tag immediately
- Alias pills are display-only and are not clickable
- `Esc` or clicking outside closes popup
- Popup is constrained to a compact scrollable height sized for roughly 6 suggestion rows

## Save Flow

Save mode is probed at page load:

- Health check against local save service (500ms timeout)
- If available: `Save mode: Local server`
- Else: `Save mode: Patch`

### Local server mode

- Endpoint: `POST /save-tags` on the local save service
- Payload:
  - `series_id`
  - `work_id`
  - `tags` (array of work-override assignment objects; may be empty to delete that work row):
    - `{ "tag_id": "<group>:<slug>", "w_manual": 0.3|0.6|0.9 }`
  - `client_time_utc`
- Save scope:
  - `Save` compares the current editor state against the baseline from page load or last successful save, then persists only the diff
  - when multiple work pills are present and one is active, the active work's current override set is the persisted state for all selected work pills
- Save sanitization:
  - inherited series tags are not persisted in work rows
  - duplicate work tags are collapsed
  - removing a work pill deletes that `series[series_id].works[work_id]` row entirely
  - selected work rows may persist with `tags: []` when the work row itself is part of the saved diff
- On success:
  - UI status message includes save timestamp
- On failure:
  - UI falls back to Patch mode and opens patch modal
- Local write operations are logged to `var/studio/logs/tag_write_server.log` (JSONL).

### Patch mode

- Shows modal with:
  - canonical resolved work-override object array
  - patch guidance to paste under `series[series_id].works` in `tag_assignments.json`
  - delete guidance when the sanitized work delta is empty
- Copy button uses `navigator.clipboard.writeText`

## Data Files: Purpose and Governance

### `assets/studio/data/studio_config.json`

Purpose:

- Central Studio config for public path resolution and analysis policy.

Governance:

- Maintain deliberately with review when Studio data locations or scoring behavior change.
- Prefer moving thresholds and path changes into this file instead of editing multiple Studio scripts.
- `updated_at_utc` should be bumped when changing config behavior.

### `assets/studio/data/tag_registry.json`

Purpose:

- Controlled vocabulary and policy for tags.

Governance:

- Maintained manually in repo.
- Should be updated deliberately with review because it defines allowed semantics used across editor/index.
- `updated_at_utc` should be bumped when changing tags/policy.

### `assets/studio/data/tag_aliases.json`

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

### `assets/studio/data/tag_assignments.json`

Purpose:

- Per-series canonical tag assignments plus per-work delta overrides.
- `series[*].tags` schema is object-only:
  - `tag_id`: canonical `<group>:<slug>`
  - `w_manual`: discrete manual weight (`0.3`, `0.6`, `0.9`)
  - effective weighting is derived at runtime and is not persisted in this file
- `series[*].works[*].tags` uses the same object-only schema
  - stores only the work delta, never a materialized inherited list

Governance and maintenance:

- Generated/synced by `scripts/generate_work_pages.py` to ensure all series IDs exist with default `tags: []` and `works: {}`.
- Updated interactively via:
  - patch workflow (manual paste), or
  - local save service (`scripts/studio/tag_write_server.py`).
- Server writes are constrained to this file, with timestamped backups in `var/studio/backups/`.
- Top-level `updated_at_utc`, per-series `updated_at_utc`, and touched work-row `updated_at_utc` values must be kept current by writer flow.
- Script change events are logged in `logs/`:
  - `var/studio/logs/tag_write_server.log`
  - `logs/run_draft_pipeline.log`
  - `logs/generate_work_pages.log`
  - retention: 30 days, with fallback to keep the latest 1 day's entries when activity is older than 30 days.
- `scripts/audit_site_consistency.py` reports drift when `tag_assignments.json` references series/work rows that no longer match `series_index.json` or `works_index.json`.

## Operational Notes

- Editor starts with a `work_id` selector scoped to the current series membership from `series_index.json`.
- Work selection accepts padded or unpadded IDs (`342` -> `00342`) and supports comma-separated entry for selecting multiple works at once.
- Selected work pills are shown in series order; one pill is active at a time for editing, and inactive pills use a white/black outline style.
- Saved work override rows are restored as work pills on page load; the page still opens with no active work selected until the curator clicks a pill.
- When multiple work pills are present, editing happens on the active pill, and `Save` copies that active override set to all selected work pills.
- Save enabled/disabled state is diff-based against the last persisted baseline.
- Removing a restored work pill counts as a pending deletion and keeps `Save` enabled even if no work is currently active.
- Editor stores canonical work-override assignment objects (`tag_id`, `w_manual`) in save payload/snippet.
- Unknown/unresolved user inputs are blocked from save.
- Effective work tags are `series tags ∪ work override tags`.
- A work cannot persist any tag already inherited from its series; inherited duplicates are dropped on save.
- Empty work override arrays delete that work row from `tag_assignments.json`.
- Editor layout shows four fixed group rows (`subject:`, `domain:`, `form:`, `theme:`); rows with no tags are left blank.
- Series RAG remains driven by `series[*].tags` only.
- Add/search controls now sit below the work selector row and above the save-mode text.
- New assignments default to `w_manual: 0.6`.
- UI only edits and persists `w_manual`.

## Open Issues

- Editor metrics are internal (save gate + logic) and no longer shown as a user-facing metrics panel.
- Registry group list in JS is currently fixed to four groups; future policy changes would require coordinated code updates.

## Feature Requests

- Rich ambiguity chooser for multiple matches before adding a tag.
- Keyboard navigation for suggestion popup.
- Configurable suggestion strategies (beyond slug/alias prefix).
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

The Studio Tag Registry page (`/studio/tag-registry/`) reads `assets/studio/data/tag_registry.json` and:

- lists tags with columns: tag, description
- default sort is alphabetical by tag label
- supports header click sorting (tag/description, asc/desc)
- displays group color coding using the same chip palette as Studio Series
- shows a group key above the list
  - group pills use `tag_groups.json` `description` as hover text (`title`)
  - includes an `i` info pill that opens `/studio/tag-groups/` in a new tab
- supports key-button filtering by group
- provides an `All tags` button to clear filter
- supports import from a local JSON file (recommended from `var/studio/import`)
  - mode `add (no overwrite)`: add tags with new `tag_id` only, keep existing entries unchanged
  - mode `replace`: replace the full tag list
  - mode `add + overwrite`: add new tags and overwrite matching `tag_id` entries, leaving other entries untouched
  - includes `New tag` button (right side of import controls) to open tag-create modal
- local-server import writes update timestamps:
  - top-level `updated_at_utc`
  - per-tag `updated_at_utc` for added/overwritten tags
- import response includes `summary_text` and the same summary is written to `var/studio/logs/tag_write_server.log`
- import response/log includes `import_filename` (basename only)
- clicking a tag pill opens an edit modal:
  - shows the tag group as a color-coded pill
  - group pill hover text uses `tag_groups.json` `description`
  - shows tag name as read-only
  - allows editing `description`
- tag create behavior:
  - `New tag` opens modal with group-selection pills above slug input
  - modal group key includes an `i` info pill that opens `/studio/tag-groups/` in a new tab
  - live duplicate check warns if `<group>:<slug>` already exists
  - description is optional/editable in create modal
  - local server mode uses `POST /import-tag-registry` in `add` mode with a single tag payload
  - patch mode provides add-tag row snippet
- tag row includes `<-` action to demote canonical tag into alias mapping
  - opens a demotion modal (not free-text prompt)
  - modal group-key pills use `tag_groups.json` `description` as hover text
  - modal group key includes an `i` info pill that opens `/studio/tag-groups/` in a new tab
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
  - delete modal shows live impact preview via `POST /mutate-tag-preview` before confirm
  - edit updates tag `description` in registry row
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

The Studio Tag Aliases page (`/studio/tag-aliases/`) reads `assets/studio/data/tag_aliases.json` and:

- lists aliases with columns: alias, group tags
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
  - group pills use `tag_groups.json` `description` as hover text (`title`)
  - includes an `i` info pill that opens `/studio/tag-groups/` in a new tab
- supports search by alias prefix
- supports header sorting (alias, asc/desc)
- supports import from a local JSON file (recommended from `var/studio/import`)
  - mode `add (no overwrite)`: add aliases with new key only
  - mode `replace`: replace the full aliases map
  - mode `add + overwrite`: add new aliases and overwrite matching keys, leaving other aliases untouched
  - includes `New alias` button (right side of import controls) to open alias-create modal
- local-server import uses `POST /import-tag-aliases`
  - response includes `summary_text` and `import_filename` (basename only)
  - summary is written to `var/studio/logs/tag_write_server.log`
- alias delete behavior:
  - local server mode uses `POST /delete-tag-alias`
  - patch mode provides copyable snippet with `aliases_to_remove`
- alias edit behavior:
  - local server mode uses `POST /mutate-tag-alias`
  - server validates alias uniqueness and registry-backed selected tags
  - modal closes via `Cancel` button (outside/backdrop click does not close)
  - modal group-key pills use `tag_groups.json` `description` as hover text
  - modal group key includes an `i` info pill that opens `/studio/tag-groups/` in a new tab
  - patch mode provides ordered `set_alias`/`remove_alias_key` steps
- alias create behavior:
  - `New alias` opens modal with same tag search/selection flow and group-key info link as edit
  - alias name uniqueness is validated live while typing
  - local server mode uses `POST /import-tag-aliases` in `add` mode with a single alias payload
  - patch mode provides add-alias fragment snippet
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

The Series Tags page (`/studio/series-tags/`) reads:

- `assets/data/series_index.json` for the series list/title/link target
- `assets/studio/data/tag_assignments.json` for assigned tags per series

It then:

- lists series in alphabetical order by title
- links each series title to its Series Tag Editor page (`/studio/series-tag-editor/?series=<series_id>`)
- shows per-series status (RAG dot) using the same rules as Studio Series
- renders assigned tags as color-coded pills
- sorts tags alphabetically by label (fallback: tag id)
- uses an inline header key (`All tags` + group pills) in the tags column
- group pills use `tag_groups.json` `description` as hover text (`title`)
- includes an `i` info pill that opens `/studio/tag-groups/` in a new tab
- applies key filtering to visible tag pills only (series rows and counts remain unchanged)
