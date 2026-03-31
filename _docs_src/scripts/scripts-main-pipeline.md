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

Default behavior now includes a planner pass before execution. `build_catalogue.py` fingerprints workbook-backed source records, compares them to `var/build_catalogue_state.json`, and infers which work IDs, series IDs, and moment IDs need generation. The copy/srcset stages remain draft-driven for now, so published media-only changes still need explicit flags.

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
- generated repo artifact written by `build_search.rb --scope catalogue`:
  - `assets/data/search/catalogue/index.json`

## Planner Notes

- The saved planner state is orchestration data, not canonical site data.
- The planner currently tracks workbook-backed rows and grouped workbook sections:
  - `Works`
  - `Series`
  - `WorkDetails`
  - `WorkFiles`
  - `WorkLinks`
  - `Moments`
- It uses those fingerprints to infer generation/search scope, but it does not yet fingerprint source media.
- Removed workbook rows can still leave stale generated files. Deletion flows remain separate from planner-driven rebuilds.

## Logging

Per-script logs are written to repo-root log directories and are auto-created as needed.

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
