# Pipeline Config Refactor Plan

This document tracks the phased refactor to move pipeline policy out of scattered script/template defaults and into one shared configuration model.

## Goals

- Make the media pipeline easier to reuse in different local installs.
- Move semi-permanent policy out of hard-coded script/template logic.
- Keep one-off execution choices as CLI flags.
- Keep UI/runtime assumptions in sync with pipeline generation rules.
- Preserve backward compatibility for existing generated media.

## Non-Goals

- Store absolute local filesystem paths in tracked config.
- Replace environment variables with tracked path values.
- Change current media behavior in phase 1.
- Require immediate regeneration of all existing media.

## Status

- Overall status: `phase 1 completed`
- Phase 1: `completed`
- Phase 2: `not started`
- Phase 3: `not started`
- Phase 4: `not started`

## Current Problems

- Srcset widths, thumb sizes, output names, and ffmpeg settings are hard-coded in `scripts/make_srcset_images.sh`.
- Media subfolder layout and env-var assumptions are duplicated in `scripts/run_draft_pipeline.py`, `scripts/copy_draft_media_files.py`, and `scripts/generate_work_pages.py`.
- UI/runtime widths are duplicated in `_layouts/work.html`, `_layouts/work_details.html`, `_layouts/moment.html`, and `assets/studio/js/series-tag-editor-page.js`.
- Audit rules accept a hard-coded set of filenames and widths in `scripts/audit_site_consistency.py`.

## Working Decisions

- Tracked config should store env var names, not path values.
- Tracked config should store relative media subpaths.
- CLI flags should continue to override config-derived defaults.
- Backward compatibility needs separate concepts for:
  - generation widths
  - UI render widths
  - accepted legacy widths
- Bash should not become the long-term owner of shared config parsing.

## Proposed Config Scope

The shared config should cover:

- Environment variable names
  - `projects_base_dir_env`
  - `media_base_dir_env`
  - `srcset_jobs_env`
- Relative media paths per mode
  - `work`
  - `work_details`
  - `moment`
- Variant policy
  - primary widths
  - thumb sizes
  - naming suffixes
  - output subfolders
- Encoder policy
  - codec
  - preset
  - quality values
  - compression level
- Compatibility policy
  - `generate_widths`
  - `render_widths`
  - `accepted_legacy_widths`

## Phase 1: Introduce Shared Config Without Behavior Change

Status: `completed`

### Needs

- Add a tracked config file for pipeline policy.
- Add a shared Python config loader used by Python scripts.
- Keep all current defaults unchanged.
- Keep all current CLI flags working.
- Do not yet change how the srcset builder is implemented.

### Deliverables

- New config file, likely under `_data/` or another small docs-adjacent location.
- New Python helper module for loading and validating config.
- Python scripts updated to read env-var names and relative path defaults from config.
- Docs updated to describe the new config source of truth.

### Likely Touch Points

- `scripts/run_draft_pipeline.py`
- `scripts/copy_draft_media_files.py`
- `scripts/generate_work_pages.py`
- `docs/scripts-overview.md`

### Done

- 2026-03-20: Added tracked shared policy file at `_data/pipeline.json`.
- 2026-03-20: Added shared Python loader at `scripts/pipeline_config.py`.
- 2026-03-20: Updated `scripts/run_draft_pipeline.py`, `scripts/copy_draft_media_files.py`, and `scripts/generate_work_pages.py` to read env var names and path defaults from shared config.
- 2026-03-20: Updated `docs/scripts-overview.md` and `README.md` to document the new config source of truth.
- 2026-03-20: Sanitized this plan doc to use repo-relative references only.

### Verification

- 2026-03-20: Ran Python syntax checks with the configured Python interpreter via `python3 -m py_compile` for:
  - `scripts/pipeline_config.py`
  - `scripts/copy_draft_media_files.py`
  - `scripts/run_draft_pipeline.py`
  - `scripts/generate_work_pages.py`
- 2026-03-20: Ran dry-run pipeline check:
  - `DOTLINEFORM_PROJECTS_BASE_DIR=/tmp/dlf-pipeline-check DOTLINEFORM_MEDIA_BASE_DIR=/tmp/dlf-pipeline-check python3 scripts/run_draft_pipeline.py --dry-run --mode moment --moment-ids nonexistent-moment`
- 2026-03-20: Confirmed the dry-run completed successfully with config-backed defaults and no writes.

## Phase 2: Move Srcset Builder Onto Shared Config

Status: `not started`

### Needs

- Remove hard-coded widths and encoder settings from the srcset builder.
- Decide whether to:
  - replace the Bash script with Python, or
  - keep a thin Bash wrapper that delegates to Python
- Keep behavior unchanged on first migration.

### Preferred Direction

- Replace the current Bash implementation with Python.

Reason:

- Shared config parsing is straightforward in Python and awkward in Bash.
- Width loops, report aggregation, and validation logic become easier to maintain.
- This reduces the number of places that need bespoke config handling.

### Deliverables

- Config-driven srcset generation implementation.
- Compatibility-preserving wrapper or command alias if needed.
- No change in output filenames or current generated widths in the first pass.

### Likely Touch Points

- `scripts/make_srcset_images.sh`
- New Python srcset builder module/script
- `scripts/run_draft_pipeline.py`
- `docs/scripts-overview.md`

### Done

- None yet.

### Verification

- Dry-run srcset generation for `work`, `work_details`, and `moment`.
- Confirm generated filenames and counts match current behavior.
- Confirm manifest handling and source cleanup behavior are preserved.

## Phase 3: Make UI and Studio Read From Shared Variant Policy

Status: `not started`

### Needs

- Remove hard-coded srcset widths from templates and Studio JS.
- Ensure UI emits widths from config-derived render policy.
- Keep rendering compatible with older generated media.

### Deliverables

- Site templates read from shared variant policy.
- Studio JS reads from the same policy or from generated runtime-safe data derived from it.
- Runtime media links choose the configured preferred full-size asset.

### Likely Touch Points

- `_layouts/work.html`
- `_layouts/work_details.html`
- `_layouts/moment.html`
- `assets/studio/js/series-tag-editor-page.js`

### Compatibility Rules

- `generate_widths` controls what new pipeline runs produce.
- `render_widths` controls what widths templates and Studio emit in `srcset`.
- `accepted_legacy_widths` controls which old files remain valid for audits and orphan scans.
- Additive rollout should be two-step:
  - generate new widths first
  - switch render policy later when coverage is acceptable

### Done

- None yet.

### Verification

- Manual checks on work, work detail, and moment pages.
- Manual checks on desktop and mobile layouts.
- Confirm Studio primary-media preview still resolves correctly.

## Phase 4: Update Audits, Docs, and Ongoing Maintenance Rules

Status: `not started`

### Needs

- Remove hard-coded audit assumptions about allowed widths.
- Document compatibility expectations and rollout procedure.
- Establish a clear update path for future width additions or naming changes.

### Deliverables

- Audit rules driven by shared compatibility policy.
- Scripts/docs updated to explain:
  - where pipeline policy lives
  - how env var names are configured
  - how width additions should be rolled out safely
- This plan document updated with completed work and follow-ups.

### Likely Touch Points

- `scripts/audit_site_consistency.py`
- `docs/scripts-overview.md`
- `README.md`
- `AGENTS.md` if workflow expectations change

### Done

- None yet.

### Verification

- Run scoped and full audit checks relevant to changed files.
- Confirm old image files are not incorrectly flagged as invalid.
- Confirm docs match actual command/runtime behavior.

## Risks

- Partial migration could leave scripts, UI, and audits out of sync.
- Width additions can create mixed-media inventories that UI and audits need to tolerate.
- Replacing the Bash srcset builder is higher effort than adding config alone.
- Config sprawl is possible if unrelated concerns get folded into the same file.

## Benefits

- One source of truth for pipeline policy.
- Easier reuse of the repo in different local environments.
- Lower drift risk between generation, UI, Studio, and audits.
- Safer future changes to widths, encoder settings, and media layout.

## Open Questions

- Should the tracked config live in `_data/` so Jekyll can consume it directly, or elsewhere with a generated runtime export for templates?
- Should Studio read config directly at runtime, or should generation write a small derived runtime policy object?
- Is there any reason to preserve Bash as the primary srcset implementation once config is introduced?

## Update Protocol

When work starts on a phase:

- Change the phase status.
- Add dated notes under that phase’s `Done` section.
- Record any scope changes in `Open Questions` or a new decision log entry.
- Keep `Verification` current with what was actually run.

## Decision Log

- 2026-03-20: Use tracked config for policy, but keep absolute local paths in env vars only.
- 2026-03-20: Allow env var names themselves to be configured.
- 2026-03-20: Treat backward compatibility for media widths as a first-class requirement.
