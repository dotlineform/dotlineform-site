---
doc_id: scripts-main-pipeline
title: Build Catalogue
last_updated: 2026-04-01
parent_id: scripts
sort_order: 20
---

# Build Catalogue

Script:

```bash
./scripts/build_catalogue.py
```

Run everything:

```bash
./scripts/build_catalogue.py --dry-run
./scripts/build_catalogue.py
```

Default behavior now includes a planner pass before execution. `build_catalogue.py` fingerprints workbook-backed source records plus canonical source media and current work/series/moment prose sources, compares them to `var/build_catalogue_state.json`, and infers which work IDs, series IDs, and moment IDs need generation. When the planner state predates a newer planner version, the script loads that state in compatibility mode and rewrites it with the current planner metadata on the next successful write run. When the planner state predates media or prose tracking, the next write run treats current source files as the baseline and updates `var/build_catalogue_state.json` without forcing a synthetic rebuild.

When workbook rows have been removed, the planner now also deletes the matching stale repo-owned generated artifacts, stale local media under `DOTLINEFORM_MEDIA_BASE_DIR`, and stale `tag_assignments.json` rows before rebuilding catalogue search.

Before any copy, srcset, workbook, or generated-file writes begin, the pipeline now runs a shared workbook preflight. That preflight aggregates blocking workbook errors for actionable catalogue rows, including malformed IDs, unknown `Works.series_ids` references, missing `Series.primary_work_id`, `Series.primary_work_id` values that do not belong to the series, orphaned `WorkDetails.work_id` values, and non-slug-safe `Moments.moment_id` values. The run stops at that point if any blocking errors are found.

## Useful Flags

- `--dry-run`: preview only, with no workbook writes or deletes
- `--plan`: print the inferred execution plan and exit
- `--full`: ignore saved planner state and rebuild all workbook-backed generation targets
- `--reset-state`: remove `var/build_catalogue_state.json` before planning
- `--force-generate`: pass `--force` through to `generate_work_pages.py` and the catalogue search rebuild
- `--jobs N`: srcset parallel jobs; default `4`, or `MAKE_SRCSET_JOBS`
- `--mode work|work_details|moment`: run only selected flow(s); repeat flag to run multiple
- `--work-ids`, `--work-ids-file`: limit work and work-details scope
- `--series-ids`, `--series-ids-file`: pass series scope to generation
- `--moment-ids`, `--moment-ids-file`: limit moment scope
- `--xlsx PATH`: workbook path override
- `--input-dir`, `--output-dir`: works source and derivative dirs
- `--detail-input-dir`, `--detail-output-dir`: work-details source and derivative dirs
- `--moment-input-dir`, `--moment-output-dir`: moments source and derivative dirs

## Preflight Behavior

- workbook preflight runs after planning and before any copy/srcset/generation step
- preflight failures are aggregated and printed together so workbook fixes can be made in one pass
- preflight is intended to prevent partial publish states where work rows or media are written before a later series or moment validation failure aborts the run

## Mode Examples

```bash
./scripts/build_catalogue.py --plan
./scripts/build_catalogue.py --full --dry-run
./scripts/build_catalogue.py --mode moment --dry-run
./scripts/build_catalogue.py --mode work --mode work_details --dry-run
./scripts/build_catalogue.py --mode moment --moment-ids blue-sky,compiled --dry-run
./scripts/build_catalogue.py --mode work --work-ids 00456 --dry-run
```

When `--mode work` is used and no `--series-ids*` flags are provided, the planner auto-includes draft series, changed series rows, and series linked to affected works.

Current pipeline tail:

- `generate_work_pages.py` refreshes the canonical catalogue route stubs and JSON artifacts
- `build_search.rb --scope catalogue` then rebuilds `assets/data/search/catalogue/index.json` from those repo JSON artifacts

## Source And Target Artifacts

Primary source artifacts:

- `data/works.xlsx`
- source media under `DOTLINEFORM_PROJECTS_BASE_DIR`
  - `projects/...`
  - `moments/...`
- planner state:
  - `var/build_catalogue_state.json`

Primary target artifacts:

- staged media under `DOTLINEFORM_MEDIA_BASE_DIR`
- srcset derivatives under `DOTLINEFORM_MEDIA_BASE_DIR`
- generated repo artifacts written by `generate_work_pages.py`, including:
  - `_works/`
  - `_series/`
  - `_work_details/`
  - `_moments/`
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/data/moments_index.json`
  - `assets/series/index/`
  - `assets/works/index/`
  - `assets/moments/index/`
  - `assets/studio/data/work_storage_index.json`
- generated repo artifact written by `build_search.rb --scope catalogue`:
  - `assets/data/search/catalogue/index.json`
- generated local activity artifacts written after successful non-dry-run runs:
  - `var/build_activity/build_catalogue.jsonl`
  - `assets/studio/data/build_activity.json`

## Planner Notes

- The saved planner state is orchestration data, not canonical site data.
- `var/build_catalogue_state.json` is intentionally local and untracked:
  - it is derived from canonical inputs rather than being a canonical input itself
  - it changes during normal local runs and would create noisy commits
  - different machines can have different valid baselines without that meaning the site data has diverged
  - it can be bootstrapped again from the current workbook, prose, and source-media state by deleting it and running `build_catalogue.py`
- `var/build_catalogue_state.json` now includes top-level planner metadata:
  - `schema`
  - `planner_version`
  - `migration_note`
- Older planner state files are still accepted if their inputs are compatible. The script normalizes them in memory and rewrites them on the next successful write run.
- The planner currently tracks workbook-backed rows and grouped workbook sections:
  - `Works`
  - `Series`
  - `WorkDetails`
  - `WorkFiles`
  - `WorkLinks`
  - `Moments`
- It also fingerprints canonical source media for:
  - work primary images
  - work-detail source images
  - moment source images
- It also fingerprints canonical prose sources for:
  - work prose files resolved from `Works.project_folder` plus `Works.work_prose_file`
  - series prose files resolved from `Series.primary_work_id` plus `Series.series_prose_file`
- moment prose files resolved from `moments/<moment_id>.md`
- Work, series, and moment prose changes trigger generation targeting only.
  They do not trigger copy/srcset and do not currently force a catalogue search rebuild on their own.
- The current stale-artifact cleanup pass removes repo-owned generated artifacts for removed:
  - works
  - work details
  - series
  - moments
- The same cleanup pass removes local media artifacts for removed works, work details, and moments under `DOTLINEFORM_MEDIA_BASE_DIR`, including:
  - staged `make_srcset_images` inputs
  - generated `primary/` and `thumb/` srcset files
  - staged work downloads under `works/files/`
- The same pass also prunes removed series rows and removed work overrides from `assets/studio/data/tag_assignments.json`.
- Canonical source media under `DOTLINEFORM_PROJECTS_BASE_DIR` and remote media such as R2 remain separate from planner-driven cleanup.

## Logging

Per-script logs are written to repo-root log directories and are auto-created as needed.

`build_catalogue.py` also writes a separate curated activity summary after successful non-dry-run runs:

- local journal:
  - `var/build_activity/build_catalogue.jsonl`
- Studio-facing feed:
  - `assets/studio/data/build_activity.json`

Current logged scripts:

- `scripts/build_catalogue.py` -> `logs/build_catalogue.log`
- `scripts/generate_work_pages.py` -> `logs/generate_work_pages.log`
- `scripts/delete_work.py` -> `logs/delete_work.log`
- `scripts/studio/tag_write_server.py` -> `var/studio/logs/tag_write_server.log`

Log format:

- JSON Lines, one JSON object per line

Retention policy:

- keep entries from the last 30 days
- if no entries fall inside the last 30 days, keep the latest 1 day's worth based on the newest entry

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
