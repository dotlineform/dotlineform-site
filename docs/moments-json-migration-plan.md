# Moments JSON Migration Plan

This document defines the phased migration from the current include-based moments pipeline to a JSON-driven runtime flow aligned with the existing work page architecture.

## Goals

- Move moment prose to a runtime JSON payload instead of build-time include insertion.
- Keep canonical moment prose in the source tree at `moments/<moment_id>.md`.
- Generate per-moment JSON at `assets/moments/index/<moment_id>.json`.
- Convert `_moments/<moment_id>.md` into lightweight routing stubs.
- Build and verify the new flow in parallel with the current pipeline before switching the site over.
- Keep rollback simple while both paths exist.

## Non-Goals

- Replace the current moment page URL structure.
- Change the current moment image pipeline beyond what is needed for JSON-backed rendering.
- Migrate markdown rendering to Python in the first pass.
- Remove the legacy prose include flow before the JSON path is proven in local testing.

## Status

- Overall status: `phase 1, phase 2, and phase 4 completed; phase 3 and phase 5 not started`
- Phase 1: `completed`
- Phase 2: `completed`
- Phase 3: `not started`
- Phase 4: `completed`
- Phase 5: `not started`

## Working Decisions

- Canonical moment prose remains in the source root:
  - `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md`
- Canonical moment images remain in the configured images subdirectory:
  - `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/images/<moment_id>.jpg`
- The first JSON migration should use the local Jekyll stack for markdown-to-HTML rendering.
- The renderer should be hidden behind one narrow pipeline interface so a future Python renderer remains possible.
- During the parallel rollout, the layout should support both:
  - legacy server-rendered body content
  - JSON-fetched runtime HTML
- The switch between legacy and JSON rendering should be controlled by tracked config, not by editing templates ad hoc.
- Once moment pages become stubs, `_moments/<moment_id>.md` should contain no fallback prose content.
- Stub front matter should retain `title` for minimal runtime-failure fallback.
- The initial per-moment JSON payload should include rendered HTML only.
- If moment JSON fails to load in JSON mode, the runtime page should show `problem loading content` rather than trying to fall back to stub prose.
- No-JS prose fallback is not a current project goal for the moments migration.
- Canonical moment source files should keep their existing `<pre class="moment-text">...</pre>` wrappers for the initial JSON migration.
- Conversion of moment source files to pure markdown should happen only in a later phase, after the JSON pipeline and runtime path are stable.

## Target Architecture

### Canonical Source Inputs

- Workbook metadata:
  - `data/works.xlsx` worksheet `Moments`
- Canonical prose:
  - `moments/<moment_id>.md`
- Canonical source image:
  - `moments/images/<moment_id>.jpg`

### Generated Artifacts

- Stub moment page:
  - `_moments/<moment_id>.md`
- Per-moment JSON:
  - `assets/moments/index/<moment_id>.json`

### Runtime Flow

1. Jekyll builds a stub moment page from `_moments/<moment_id>.md`.
2. The moment layout reads a pipeline feature flag from `_data/pipeline.json`.
3. In legacy mode:
   - render the current server-side page content path.
4. In JSON mode:
   - fetch `assets/moments/index/<moment_id>.json`
   - use JSON metadata as canonical runtime page data
   - inject `content_html` into the page body at runtime

## Proposed Moment JSON Shape

The exact field list can evolve, but the initial shape should be:

```json
{
  "header": {
    "schema": "moment_record_v1",
    "version": "...",
    "generated_at_utc": "...",
    "moment_id": "blue-sky"
  },
  "moment": {
    "moment_id": "blue-sky",
    "title": "Blue sky",
    "date": "2024-01-01",
    "date_display": null,
    "images": [],
    "width_px": 1200,
    "height_px": 800
  },
  "content_html": "<p>...</p>"
}
```

## Feature Flag

Add a tracked config flag under `_data/pipeline.json`, for example:

- `features.moments_runtime_source`

Allowed values:

- `legacy`
- `json`

Behavior:

- `legacy`:
  - keep current include/content rendering path
  - JSON generation may still run in parallel
- `json`:
  - runtime page uses per-moment JSON as the canonical prose source

## Phase 1: Add JSON Generation In Parallel

Status: `completed`

### Needs

- Add a per-moment JSON output path.
- Add markdown rendering via the local Jekyll stack.
- Keep the current moment page generation flow working.
- Keep the current `_includes/moments_prose` flow working during this phase.

### Deliverables

- A small renderer helper that converts `moments/<moment_id>.md` to HTML using the local Jekyll stack.
- `scripts/generate_work_pages.py` writes `assets/moments/index/<moment_id>.json`.
- Deterministic JSON version/checksum behavior for moments, similar to work JSON.
- New docs covering the generated JSON artifact and its source of truth.

### Likely Touch Points

- `scripts/generate_work_pages.py`
- new markdown-render helper script
- `_data/pipeline.json`
- `docs/scripts-overview.md`

### Verification

- Python syntax check for updated Python scripts.
- Syntax/runtime check for the markdown-render helper.
- Dry-run generation for one or more scoped moments.
- Manual inspection of generated JSON for:
  - metadata correctness
  - expected HTML structure
  - stable version behavior

### Main Benefit

- Introduces the future runtime source without disturbing the current page rendering path.

### Main Risk

- Markdown-to-HTML output may drift from the site if the renderer is not tightly aligned with Jekyll.

### Done

- 2026-03-28: Added tracked feature flag `features.moments_runtime_source` with initial default `legacy`.
- 2026-03-28: Added Jekyll-backed markdown renderer helper at `scripts/render_markdown_with_jekyll.rb`.
- 2026-03-28: Added `moment-json` as a separate `generate_work_pages.py --only` artifact.
- 2026-03-28: Added `--moments-json-dir` with default `assets/moments/index`.
- 2026-03-28: Added per-moment JSON generation at `assets/moments/index/<moment_id>.json`.
- 2026-03-28: Kept the legacy moment page and `_includes/moments_prose` flow intact in parallel.
- 2026-03-28: Updated scripts docs to describe the new JSON artifact and output path.

### Verification

- 2026-03-28: Ran Python syntax checks with the configured interpreter via `python3 -m py_compile` for:
  - `scripts/pipeline_config.py`
  - `scripts/generate_work_pages.py`
- 2026-03-28: Ran Ruby syntax check for:
  - `scripts/render_markdown_with_jekyll.rb`
- 2026-03-28: Ran the renderer helper directly against `moments/blue-sky.md` and confirmed it emitted the expected HTML without Jekyll config chatter.
- 2026-03-28: Ran dry-run moment JSON generation:
  - `./scripts/generate_work_pages.py --only moment-json --moment-ids blue-sky`
- 2026-03-28: Ran scoped write-mode verification to a temporary output directory:
  - `./scripts/generate_work_pages.py --only moment-json --moment-ids blue-sky --force --moments-json-dir /tmp/... --write`
- 2026-03-28: Confirmed the generated sample JSON included:
  - `header.schema = moment_record_v1`
  - deterministic `version`
  - public `moment` metadata
  - rendered `content_html`

## Phase 2: Add Dual-Path Runtime Rendering

Status: `completed`

### Needs

- Teach the moment layout to support both legacy and JSON-backed rendering.
- Keep the current page usable when JSON is missing or the flag remains `legacy`.
- Avoid duplicating image rendering logic more than necessary.

### Deliverables

- Updated `_layouts/moment.html` with:
  - a legacy path
  - a JSON runtime path behind the feature flag
- Small moment-page JS to:
  - fetch JSON
  - populate metadata
  - inject `content_html`
  - fail safely when JSON is unavailable

### Likely Touch Points

- `_layouts/moment.html`
- new or shared frontend JS file
- `assets/css/main.css` only if runtime content needs small structural adjustments
- `_data/pipeline.json`

### Verification

- `bundle exec jekyll build --quiet`
- Manual checks on desktop and mobile for:
  - title
  - date
  - hero image
  - prose insertion
  - `problem loading content` failure state when JSON cannot be fetched
  - no layout shift beyond acceptable levels

### Main Benefit

- Allows direct comparison between legacy and JSON-backed rendering before cutover.

### Main Risk

- Two rendering paths create temporary complexity and increase the chance of drift if both are edited inconsistently.

### Done

- 2026-03-28: Updated `_layouts/moment.html` to support both:
  - `legacy` server-rendered prose
  - `json` runtime prose loading behind `features.moments_runtime_source`
- 2026-03-28: Added moment runtime loader at `assets/js/moment.js`.
- 2026-03-28: Added runtime metadata hydration for:
  - title
  - date/date_display
  - hero image
  - body HTML
- 2026-03-28: Added JSON-mode load-failure behavior that displays `problem loading content`.
- 2026-03-28: Kept the tracked feature flag default as `legacy` so the new runtime path can be enabled intentionally during testing.

### Verification

- 2026-03-28: Ran JS syntax check for:
  - `assets/js/moment.js`
- 2026-03-28: Ran:
  - `bundle exec jekyll build --quiet`
- 2026-03-28: Confirmed the site builds successfully with the runtime feature flag in place.
- 2026-03-28: Manual JSON-mode checks succeeded for representative moment pages and the `problem loading content` failure state.

## Phase 3: Convert Moment Pages To Stubs

Status: `not started`

### Needs

- Make `_moments/<moment_id>.md` lightweight, similar in spirit to `_works/<work_id>.md`.
- Keep enough front matter for routing, fallbacks, and no-JS safety decisions.
- Stop treating the page body as canonical moment content.

### Deliverables

- Stub moment front matter with only the fields needed for routing and fallback display.
- No prose include in the page body for JSON mode.
- No fallback prose content in the stub body.

### Likely Touch Points

- `scripts/generate_work_pages.py`
- `_moments/*.md` generated output contract
- `_layouts/moment.html`
- docs describing the stub contract

### Verification

- Dry-run and write-mode scoped generation for selected moments.
- Diff review of representative `_moments/*.md` outputs.
- Manual page checks with the feature flag in both modes.

### Main Benefit

- Aligns moment pages with the same lightweight-page / runtime-data pattern already used elsewhere.

### Main Risk

- If the stub removes too much too early, the fallback path becomes weak during rollout.
- JSON mode will depend on runtime fetch success because the stub intentionally carries no prose content.

## Phase 4: Switch Default To JSON Mode

Status: `completed`

### Needs

- Flip the tracked config flag from `legacy` to `json`.
- Verify the JSON path across a wider moment sample.
- Keep rollback to `legacy` trivial until retirement is complete.

### Deliverables

- `_data/pipeline.json` default switched to JSON mode.
- Docs updated to describe JSON mode as the active workflow.
- A short cutover checklist recorded in this plan or companion docs.

### Verification

- `bundle exec jekyll build --quiet`
- Scoped generation and runtime checks for representative moments:
  - with image and prose
  - with prose but no image
  - with image but missing prose warning path
- Manual checks on desktop and mobile

### Main Benefit

- Makes the new flow the default user-facing behavior without yet deleting rollback support.

### Main Risk

- Runtime regressions become user-facing if the flag is switched before enough representative moments are checked.

### Done

- 2026-03-28: Switched `_data/pipeline.json` `features.moments_runtime_source` to `json`.
- 2026-03-28: Updated `scripts/pipeline_config.py` fallback default to `json` to match the tracked config.
- 2026-03-28: Updated docs to describe JSON mode as the active default while keeping `legacy` available for rollback.

### Verification

- 2026-03-28: Ran:
  - `bundle exec jekyll build --quiet`
- 2026-03-28: Manual checks succeeded on representative moment pages in JSON mode.

## Phase 5: Retire Legacy Moment Prose Includes

Status: `not started`

### Needs

- Remove `_includes/moments_prose` from the active moment pipeline.
- Remove legacy prose-copy/sync logic.
- Simplify templates, docs, and verification rules around a single path.

### Deliverables

- `scripts/generate_work_pages.py` no longer mirrors prose into `_includes/moments_prose`.
- `_layouts/moment.html` no longer contains the legacy content path.
- Docs updated so JSON is the only documented runtime source.
- Legacy-only code paths removed.

### Likely Touch Points

- `scripts/generate_work_pages.py`
- `_layouts/moment.html`
- `docs/scripts-overview.md`
- `AGENTS.md` only if workflow expectations materially change

### Verification

- Full targeted dry-run for moments.
- `bundle exec jekyll build --quiet`
- Manual regression checks on multiple moment pages and the moments index.

### Main Benefit

- Removes duplicated logic and makes the moment pipeline conceptually simpler.

### Main Risk

- Once retired, rollback is no longer just a config flip; it becomes a code revert.

## Markdown Rendering Strategy

Preferred initial approach:

- use the local Jekyll stack for markdown-to-HTML conversion

Reason:

- best match for the site’s actual rendering semantics
- lowest drift risk during migration

Future option:

- replace the renderer implementation with a Python library only if there is a concrete portability or maintenance reason

Constraint:

- the rendering step should remain encapsulated behind one pipeline interface so the JSON schema and generator do not depend on the renderer choice

Deferred follow-up:

- if search or index use cases need plain text later, add that in a separate generated artifact such as `moments_index.json` rather than enlarging the first per-moment runtime payload

## Verification Plan

### Codex-Run Checks

- Python syntax checks for changed Python scripts
- syntax/runtime check for the markdown-render helper
- scoped dry-runs for:
  - legacy moment generation
  - JSON generation
  - flag-switched runtime behavior where locally verifiable
- `bundle exec jekyll build --quiet`

### Manual Checks

- desktop and mobile moment page review
- compare legacy vs JSON mode on representative moments
- confirm title/date/image/prose parity
- confirm missing-prose warning behavior
- confirm no unwanted FOUC or empty content state during JSON fetch

## Rollback Strategy

Before Phase 5 retirement:

- switch `features.moments_runtime_source` back to `legacy`
- keep generating JSON in parallel if useful for debugging

After Phase 5 retirement:

- rollback would require code reintroduction or git revert, not just config change

## Deferred Follow-On Work

After the moments migration is complete and stable:

- add a separate phase to move works prose out of `_includes/work_prose` and into per-work JSON
- add a separate phase to convert moment source files from `<pre class="moment-text">...</pre>` wrappers to pure markdown
- aim for the same conceptual model across works and moments:
  - lightweight page stubs
  - runtime JSON metadata
  - runtime HTML prose payloads
- keep that work separate from the moments migration so the first rollout stays tightly scoped

## Open Questions

- Should the future search/index flow generate a dedicated `moments_index.json` with plain-text content or excerpts?
