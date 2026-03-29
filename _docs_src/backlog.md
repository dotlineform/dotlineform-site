---
published: false
---

# Backlog

This file tracks deferred improvements and follow-up work.

## Now

- Keep `schema` warnings as backlog (do not fail workflow on warnings).
- Continue using audit checks locally before publish/generation changes.
- Use `docs/css-primitives.md` and `docs/css-audit-latest.md` as the working baseline for CSS/UI cleanup.
- Capture UI consistency findings in the CSS/UI backlog sections below instead of keeping ad hoc notes.

## Next

- Add CI job(s) to run `scripts/audit_site_consistency.py` on pull requests.
- Decide CI policy for warnings vs errors (`--strict` currently errors-only).
- Add a short contributor checklist for when to run scoped vs full audit checks.
- Extend `scripts/css_token_audit.py` beyond tokens into selector/declaration duplication reporting.
- Start a UI review pass that logs:
  - style variations that should be consolidated
  - UI inconsistencies that justify controlled redesign
  - page-specific exceptions that should remain local

## Later

- Optional JSON content-integrity check:
  - recompute/verify JSON `version`/checksum fields in `assets/data/series_index.json`, `assets/data/works_index.json`, and `assets/works/index/*.json`.
- Extend orphan checks to additional optional media/content domains as needed.
- Add automated tests for audit script behaviors (fixtures + expected findings).
- If the UI review reveals stable new patterns, promote them into `docs/css-primitives.md` only after they exist in code.

## CSS/UI Backlog

Use this section for CSS cleanup and UI consistency work.

### Intake Rules

- Log each item as one of:
  - `consolidate`
    repeated styles/selectors that should be reduced without changing UI intent
  - `refine`
    small UI adjustments that improve consistency while staying within the current design language
  - `redesign`
    larger visual/interaction changes that may alter page appearance or hierarchy
- Prefer one backlog item per pattern, not per selector.
- If an item changes both behavior and presentation, split the work.
- When a new shared pattern lands in code, update `docs/css-primitives.md`.

### Current Candidates

- `consolidate`: reduce remaining repeated list-row/grid variants in `assets/css/main.css`.
- `consolidate`: reduce remaining repeated Studio shell/layout declarations in `assets/studio/css/studio.css`.
- `refine`: review cross-page spacing consistency for headings, panel interiors, and list section starts.
- `refine`: review whether shared link states across site lists should be made more visually consistent.
- `redesign`: identify cases where current list or panel patterns are technically consistent but visually weaker than the rest of the site.
- `refine`: active group/filter pills should use a simpler selected state: black border, no thicker border, no added shadow/ring.
  - technical target:
    - shared active-state treatment in `assets/studio/css/studio.css`
    - likely affects `tagStudioFilters__allBtn`, `tagStudioFilters__groupBtn`, and any related key-pill active states
  - required outcome:
    - selected appearance is distinct
    - border width does not change
    - no box-shadow/ring is added
  - check for regressions on:
    - `studio/series-tags/`
    - `studio/tag-registry/`
    - `studio/tag-aliases/`
- `refine`: all Studio pill variants should share one baseline height and `--font-small` text size across pages and modals.
  - reference style:
    - use the pills in the `tags` column on `studio/series-tags/` as the visual baseline
  - technical target:
    - shared pill primitives in `assets/studio/css/studio.css`
    - likely affects:
      - `.tagStudio__chip`
      - `.tagStudio__keyPill`
      - `.tagStudio__popupPill`
      - `.tagStudio__selectedWorkPill`
      - any modal/tag-picker pill variants built from those primitives
  - required outcome:
    - same height across series tag, work tag, work ID, and group-name pills
    - same font size: `--font-small`
    - page-specific color/group styling may vary, but the base dimensions and type scale should not
  - check for regressions on:
    - `studio/series-tag-editor/`
    - `studio/series-tags/`
    - `studio/tag-registry/`
    - `studio/tag-aliases/`
- `refine`: all Studio list shells should share one baseline row/header treatment using the `tag-registry` list as the reference.
  - reference style:
    - use the list header and row treatment on `studio/tag-registry/` as the baseline
  - technical target:
    - shared list-shell primitives in `assets/studio/css/studio.css`
    - likely affects:
      - `.tagStudioList__head`
      - `.tagStudioList__headLabel`
      - `.tagStudioList__row`
      - page-specific list rows such as `seriesTags__head` / `seriesTags__row`
  - required outcome:
    - headers and rows use `--font-small`
    - shared row padding and header spacing
    - shared row vertical alignment
    - shared border color
    - shared list/background surface treatment where appropriate
  - implementation note:
    - page-specific column grids can remain different, but spacing and baseline row styling should come from the shared list primitive layer
  - check for regressions on:
    - `studio/tag-registry/`
    - `studio/tag-aliases/`
    - `studio/series-tags/`
- `refine`: the shared info button (`i`) should render as a circle and align vertically with surrounding text/controls wherever it appears.
  - technical target:
    - shared info-button primitive in `assets/studio/css/studio.css`
    - likely affects `.tagStudio__keyInfoBtn` and any wrapper/layout rules around it
  - required outcome:
    - circular shape
    - vertically centered within the row it appears in
    - same treatment across page headers, filter rows, and modal contexts
  - check for regressions on:
    - Studio page header info buttons
    - `studio/series-tags/` filter row
    - any modal/group-info usage of the same control
- `refine`: work/series metadata blocks should share one unboxed metadata component, using the work page metadata on `/works/<work_id>/` as the reference.
  - reference style:
    - use the metadata layout and styling on a work page such as `/works/00093/`
  - technical target:
    - shared metadata styling in `assets/css/main.css`
    - Studio series metadata area in `assets/studio/css/studio.css`
    - affected templates/pages likely include:
      - work pages
      - work detail pages
      - series tag editor page
  - required outcome:
    - no field labels except `work_id` / `series_id`, using label text `cat.`
    - font size `--font-small`
    - no row borders
    - title in bold
    - no container background
    - no container border
  - implementation note:
    - the fields shown may differ by page, but the metadata presentation should come from one shared styling pattern
    - no extra decoration should be added when metadata is listed for a work or series
  - check for regressions on:
    - `/works/<work_id>/`
    - `/work_details/<detail_uid>/`
    - `studio/series-tag-editor/`
- `refine`: whenever a tag group name is displayed, it should use the coloured pill treatment rather than plain text.
  - rule:
    - tag-group names are always shown as coloured pills
    - pill size and typography should follow the shared pill baseline already recorded above
  - known nonconforming page:
    - `studio/series-tag-editor/`, where group names currently act as row headers
  - technical target:
    - shared group-pill treatment in `assets/studio/css/studio.css`
    - group-row/header rendering in `assets/studio/js/tag-studio.js`
  - implementation note:
    - group names may still function as row/header anchors, but the visible treatment should be the coloured pill style, not a plain text label
  - check for regressions on:
    - `studio/series-tag-editor/`
    - `studio/series-tags/`
    - any modal or page that renders group-name pills
- `refine`: define one standard message/result container pattern for status, warnings, and outcome text across Studio pages and modals.
  - technical target:
    - shared message/status primitives in `assets/studio/css/studio.css`
    - shared rendering/usage patterns in page controllers and modal helpers
  - required outcome:
    - consistent spacing, typography, and state treatment for message/result areas
    - pages and modals should not compose multiple mostly-empty message boxes when only one line is present
    - multi-line status/output should render as one coherent message block where appropriate
  - known example:
    - `studio/series-tag-editor/` currently splits the message area across multiple status/result containers, leaving visible empty space when only one line is active
  - likely affected surfaces:
    - editor save/status area
    - registry and aliases toolbar result/status areas
    - modal warning/status/impact areas
  - follow-up:
    - update `docs/studio/ui-framework.md` once the shared message pattern exists in code
- `redesign`: `Delete Tag` modal needs its own redesign pass beyond shared message-container cleanup.
  - technical target:
    - delete-tag modal content and rendering in registry flow
    - related styles in `assets/studio/css/studio.css`
  - known issues:
    - impact content should enumerate affected objects more clearly
    - tag-group reference styling needs review
    - current presentation should not be treated as solved by the generic message/result container pass
  - check for regressions on:
    - `studio/tag-registry/` delete flow
- `refine`: define one baseline style for all Studio action buttons.
  - technical target:
    - shared button primitives in `assets/studio/css/studio.css`
    - modal action rows and page-level action buttons across Studio controllers/templates
  - required outcome:
    - consistent font size
    - consistent control height
    - consistent padding, border radius, and visual weight
    - applies to actions such as `Add`, `OK`, `Cancel`, `Save`, `Import`, and similar buttons
  - implementation note:
    - variant meaning can still differ (primary vs secondary), but the base button treatment should not drift by page or modal
  - check for regressions on:
    - `studio/series-tag-editor/`
    - `studio/tag-registry/`
    - `studio/tag-aliases/`
    - shared modal actions
- `refine`: define one baseline style for all Studio text inputs, including search inputs.
  - technical target:
    - shared input primitives in `assets/studio/css/studio.css`
    - search rows, modal form fields, and editor inputs across Studio pages
  - required outcome:
    - consistent font size
    - consistent height/padding
    - consistent border radius and border treatment
    - search inputs should feel like the same control family rather than a separate ad hoc component
  - implementation note:
    - search-specific affordances can remain, but the base text-input styling should come from one primitive
  - check for regressions on:
    - `studio/series-tag-editor/`
    - `studio/series-tags/`
    - `studio/tag-registry/`
    - `studio/tag-aliases/`
    - shared modal forms
- `redesign`: Studio should have its own navigation instead of reusing the main site header navigation.
  - technical target:
    - Studio layout/header structure
    - likely `_layouts/studio.html` and any related shared header/nav styling
  - required outcome:
    - Studio pages use a navigation model appropriate to Studio workflows
    - Studio no longer inherits the main site works/moments navigation header
  - implementation note:
    - treat this as structural/navigation work, not a cosmetic CSS-only tweak
- `refine`: `studio/series-tags/` should move group filter pills out of the tags-column header and adopt the shared “above list” filter layout used by `studio/tag-registry/`.
  - technical target:
    - template/page shell in `studio/series-tags/index.md`
    - controller render flow in `assets/studio/js/series-tags.js`
    - list/header styling in `assets/studio/css/studio.css`
  - required outcome:
    - filter pills render above the list rather than inside the tags column header
    - tags column gets an explicit header label: `tags`
  - follow-up:
    - update `docs/studio/pages/series-tags.md`
    - update `docs/studio/regression-checklist.md`
- `refine`: `studio/series-tags/` list should support sorting from clickable column headers.
  - technical target:
    - interactive header rendering and state in `assets/studio/js/series-tags.js`
    - sortable header styling in `assets/studio/css/studio.css`
  - implementation notes:
    - preserve current group filter behavior while introducing sort state
    - likely add `data-state`/ARIA treatment consistent with other sortable Studio lists
    - sortable keys: all visible columns
    - default sort: `series`
    - tags sort: compare the visible tags as a delimited list string rather than as independent chips
  - follow-up:
    - update `docs/studio/pages/series-tags.md`
    - update `docs/studio/regression-checklist.md`

### Review Workflow

1. Review pages in-browser and record findings here.
2. Label each finding `consolidate`, `refine`, or `redesign`.
3. Group similar findings into one implementation pass.
4. Keep token cleanup, primitive cleanup, and visual refinement in separate commits.

## Decisions

- 2026-02-21: Treat `schema` warnings as backlog (not blockers).
- 2026-02-21: `media` audit assumes primaries are remote-hosted and checks local thumbs/downloads only.
- 2026-03-09: CSS/UI cleanup should fit the UI to shared tokens and primitives, not preserve local one-off values.
