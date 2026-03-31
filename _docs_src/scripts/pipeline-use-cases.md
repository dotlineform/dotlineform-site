---
doc_id: pipeline-use-cases
title: Pipeline Use Cases
last_updated: 2026-03-29
parent_id: scripts
sort_order: 10
---

# Pipeline Use Cases

This guide assumes:

- the workbook edits have already been made in `data/works.xlsx`
- commands are run from `dotlineform-site/`
- you dry-run first, then rerun with `--write` where applicable
- media-affecting flows have local env vars set:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="/path/to/dotlineform-icloud"
```

Two current CLI rules matter for almost every use case:

- `build_catalogue.py` is best when source media has changed and you need copy + srcset + generation.
- `generate_work_pages.py` is best when workbook metadata changed and you mainly need generated repo artifacts refreshed.
- `--force` is required when the affected `Works` or `Series` rows are already `published` and you need page stubs, work-file staging, or work-link publishing loops to run again.
- removal flows do not fully clean up stale generated artifacts; only full work deletion has a dedicated script, and even that still leaves workbook/source cleanup to you.

Scoping notes:

- `--work-ids` scopes work-loop artifacts such as `work-pages`, `work-json`, `work-files`, `work-links`, and `work-details-pages` to those work IDs.
- `--series-ids` plus any work-loop artifact expands the run to all works in those series.
- `--only series-pages` respects `--series-ids`.
- `--only series-index-json` always rebuilds the single global `assets/data/series_index.json` file.
- `--only works-index-json` always rebuilds the single global `assets/data/works_index.json` file.
- To avoid rewriting unaffected per-work files, prefer a series-scoped call for `work-pages` only, and a separate work-scoped call for `work-json` plus the global index files.

## 1) Add a new work to an existing series

Workbook edits before run:

- Add a `Works` row for the new `work_id`.
- Set `Works.series_ids` to include the existing `series_id`.
- Set `Works.status=draft`.
- Fill primary-image source fields such as `project_folder` and `project_filename` if the work has a primary image.
- Add any `WorkDetails`, `WorkFiles`, and `WorkLinks` rows needed for the new work. New detail/file/link rows should be `draft`.
- If the new work should become the series primary work, update `Series.primary_work_id`.

CLI:

```bash
./scripts/build_catalogue.py --mode work --mode work_details --work-ids 01234 --dry-run
./scripts/build_catalogue.py --mode work --mode work_details --work-ids 01234
./scripts/generate_work_pages.py \
  --series-ids existing-series \
  --only work-pages \
  --force
./scripts/generate_work_pages.py \
  --series-ids existing-series \
  --only work-pages \
  --force \
  --write
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force \
  --write
```

Add a separate `--only series-pages` pass if you also changed `Series` metadata such as `primary_work_id`.

Repo artifacts touched by the calls:

- `data/works.xlsx`
- `_works/01234.md`
- `_work_details/01234-*.md` if details were added
- `assets/works/index/01234.json`
- `assets/data/works_index.json`
- `assets/data/series_index.json`
- `_works/<work_id>.md` for other works in the affected series when the second command refreshes `series_sort`

Workbook/manual follow-up after run:

- None normally.
- Keep the series-scoped `work-pages` pass. `build_catalogue.py` only regenerates the selected work, not every existing work in the series.
- The work-scoped `work-json` pass avoids rewriting per-work JSON for unaffected works in the series.
- `series-index-json` and `works-index-json` are still global rebuilds in the work-scoped pass.
- If you backed out any new detail rows after the first run, manually remove stale `_work_details/<detail_uid>.md` files and stale staged media.

Potential improvements:

- Add a single `add-work` command that chains media generation with the required series-cache refresh.
- Let `build_catalogue.py` optionally refresh all work pages for affected series when membership/order changes.

## 2) Add new work details to an existing work

Workbook edits before run:

- Add new `WorkDetails` rows for the existing `work_id`.
- Give each row a unique `detail_id`.
- Set new rows to `status=draft`.
- Fill `project_subfolder` and `project_filename`.

CLI:

```bash
./scripts/build_catalogue.py --mode work_details --work-ids 01234 --dry-run
./scripts/build_catalogue.py --mode work_details --work-ids 01234
```

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_work_details/01234-*.md` for the new details
- `assets/works/index/01234.json`
- `assets/data/works_index.json`
- `assets/data/series_index.json`

Workbook/manual follow-up after run:

- None normally.
- Close and reopen the workbook if you want to see auto-written `published_date`, `width_px`, and `height_px` values immediately.

Potential improvements:

- Add a dedicated `publish-work-details --work-id <id>` command that skips unrelated work loops.

## 3) Edit, add, or remove work files for an existing work

Workbook edits before run:

- Edit, add, or remove rows in `WorkFiles` for the `work_id`.
- For new rows, set `status=draft`.
- For changed rows on an already published work, update the row values directly.
- If you want a file to disappear from the site, remove the row from `WorkFiles`. Current generation does not honor row-level `WorkFiles.status` when building output.

CLI:

```bash
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-files \
  --only work-json \
  --only works-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-files \
  --only work-json \
  --only works-index-json \
  --force \
  --write
```

Repo artifacts touched by the call:

- `data/works.xlsx`
- `assets/works/index/01234.json`
- `assets/data/works_index.json`

External media touched by the call:

- `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/01234-*`

Workbook/manual follow-up after run:

- Delete stale staged files under `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/` when a file row was removed or renamed.
- Do not leave retired `WorkFiles` rows in place expecting `status` alone to hide them. Remove or archive those rows instead.

Scoping note:

- `assets/works/index/01234.json` is work-scoped here.
- `assets/data/works_index.json` is still rebuilt globally.

Potential improvements:

- Make `WorkFiles.status` authoritative.
- Add staged-file cleanup for removed/renamed `WorkFiles` rows.

## 4) Edit, add, or remove work links for an existing work

Workbook edits before run:

- Edit, add, or remove rows in `WorkLinks` for the `work_id`.
- For new rows, set `status=draft`.
- If you want a link removed from output, remove the row from `WorkLinks`. Current generation does not honor row-level `WorkLinks.status` when building output.

CLI:

```bash
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-links \
  --only work-json \
  --only works-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-links \
  --only work-json \
  --only works-index-json \
  --force \
  --write
```

Repo artifacts touched by the call:

- `data/works.xlsx`
- `assets/works/index/01234.json`
- `assets/data/works_index.json`

Workbook/manual follow-up after run:

- Remove or archive retired `WorkLinks` rows. Leaving the row in the workbook can cause the link to be republished on later forced runs.

Scoping note:

- `assets/works/index/01234.json` is work-scoped here.
- `assets/data/works_index.json` is still rebuilt globally.

Potential improvements:

- Make `WorkLinks.status` authoritative.
- Add a `--prune-links` mode that removes links no longer present in the workbook from generated JSON in a more explicit way.

## 5) Remove all work details from an existing work

Workbook edits before run:

- Remove all `WorkDetails` rows for the `work_id`, or move them to an archive sheet outside the generator's scope.
- If you want the work to have no public details, row deletion is cleaner than changing `status` in place.

CLI:

```bash
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --write
```

Repo artifacts touched by the call:

- `assets/works/index/01234.json`
- `assets/data/works_index.json`

Workbook/manual follow-up after run:

- Manually delete stale `_work_details/01234-*.md` files.
- Manually delete stale detail media and derivatives for that work if they should no longer exist anywhere in the publishing pipeline.
- No further workbook edit is needed if the rows were already removed before the run.

Scoping note:

- `assets/works/index/01234.json` is work-scoped here.
- `assets/data/works_index.json` is still rebuilt globally.

Potential improvements:

- Add a `delete-work-details --work-id <id>` command that prunes detail stubs and derivative media in sync with the workbook.

## 6) Remove specific work details from an existing work

Workbook edits before run:

- Remove only the target `WorkDetails` rows, or move them to an archive sheet.

CLI:

```bash
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --write
```

Repo artifacts touched by the call:

- `assets/works/index/01234.json`
- `assets/data/works_index.json`

Workbook/manual follow-up after run:

- Manually delete the stale stub files for the removed detail IDs, for example `_work_details/01234-005.md`.
- Manually delete stale detail media and derivatives for the removed detail IDs if they should no longer exist.

Scoping note:

- `assets/works/index/01234.json` is work-scoped here.
- `assets/data/works_index.json` is still rebuilt globally.

Potential improvements:

- Add a `delete-work-detail --detail-uid <uid>` command.
- Add generator-side pruning of orphaned `_work_details/*.md` files.

## 7) For a work associated with multiple series, remove it from one of the series

Workbook edits before run:

- Remove the target `series_id` from `Works.series_ids` for the work.
- If that series used this work as `primary_work_id`, choose a replacement in `Series`.
- If `SeriesSort` has rules that are now stale, clean them up.

CLI:

```bash
./scripts/generate_work_pages.py \
  --series-ids old-series \
  --only work-pages \
  --force
./scripts/generate_work_pages.py \
  --series-ids old-series \
  --only work-pages \
  --force \
  --write
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force \
  --write
```

Add a separate `--only series-pages` pass if you also changed the `Series` row, for example to replace `primary_work_id`.

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_works/<work_id>.md` for works in the affected series
- `_series/old-series.md` if `series-pages` was also selected
- `assets/works/index/<work_id>.json` for the affected work
- `assets/data/works_index.json`
- `assets/data/series_index.json`

Workbook/manual follow-up after run:

- Remove stale `SeriesSort` rows or stale sort-field assumptions if they no longer make sense for the series.
- If the removed series is now empty, decide whether to keep it or use the series-deletion workflow below.
- The work-scoped call avoids rewriting `assets/works/index/*.json` for unrelated works.
- `series-index-json` and `works-index-json` are still global rebuilds in that work-scoped call.

Potential improvements:

- Add a `remove-work-from-series` command that updates work JSON, series JSON, and work-page `series_sort` caches in one step.

## 8) Reassign a work from one series to another

Workbook edits before run:

- Change `Works.series_ids` so the work no longer references the old series and does reference the new series.
- Update `Series.primary_work_id` in the old and/or new series if needed.
- Clean up or add `SeriesSort` rules as needed.

CLI:

```bash
./scripts/generate_work_pages.py \
  --series-ids old-series,new-series \
  --only work-pages \
  --force
./scripts/generate_work_pages.py \
  --series-ids old-series,new-series \
  --only work-pages \
  --force \
  --write
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force \
  --write
```

Add a separate `--only series-pages` pass if you also changed either affected `Series` row.

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_works/<work_id>.md` for works in the old and new series
- `_series/old-series.md` if `series-pages` was also selected
- `_series/new-series.md` if `series-pages` was also selected
- `assets/works/index/<work_id>.json` for the reassigned work
- `assets/data/works_index.json`
- `assets/data/series_index.json`

Workbook/manual follow-up after run:

- Clean up `SeriesSort` rows for the old and new series if the reassignment made them stale.
- The work-scoped call avoids rewriting `assets/works/index/*.json` for unrelated works.
- `series-index-json` and `works-index-json` are still global rebuilds in that work-scoped call.

Potential improvements:

- Add a first-class `move-work-between-series` command.

## 9) Add a work to an additional series

Workbook edits before run:

- Add the extra `series_id` to `Works.series_ids`.
- If the work should become the new series' `primary_work_id`, update `Series.primary_work_id`.
- Add or update `SeriesSort` rules if the target series uses them.

CLI:

```bash
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-pages \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-pages \
  --only work-json \
  --only works-index-json \
  --only series-index-json \
  --force \
  --write
./scripts/generate_work_pages.py \
  --series-ids additional-series \
  --only work-pages \
  --force
./scripts/generate_work_pages.py \
  --series-ids additional-series \
  --only work-pages \
  --force \
  --write
```

The first pair is the narrow work-scoped publish pass. The second pair is optional and broader: use it only if you need to refresh cached `series_sort` values for all works in the additional series.

Add a separate `--only series-pages` pass if you also changed the target `Series` row, for example to promote the work to `primary_work_id`.

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_works/<work_id>.md` for works in the affected series
- `_series/additional-series.md` if `series-pages` was needed
- `assets/works/index/<work_id>.json` for the affected work
- `assets/data/works_index.json`
- `assets/data/series_index.json`

Workbook/manual follow-up after run:

- Clean up `SeriesSort` if the added membership requires explicit ordering rules.
- `series-index-json` and `works-index-json` are global rebuilds even in the narrow work-scoped pass.

Potential improvements:

- Add a `add-work-to-series` command that knows when `series-pages` is actually required and when `series-index-json` alone is enough.

## 10) Delete a work

Workbook edits before run:

- Set `Works.status=delete` for the work.
- Decide whether dependent `WorkDetails`, `WorkFiles`, and `WorkLinks` rows should be removed or archived after deletion. The delete script does not clean those sheets.
- If the work is referenced by `Series.primary_work_id`, choose a replacement in the workbook. The current delete script only updates generated JSON, not the workbook `Series` sheet.

CLI:

```bash
./scripts/delete_work.py --work-id 01234
./scripts/delete_work.py --work-id 01234 --write
```

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_works/01234.md`
- `_work_details/01234-*.md`
- `assets/works/index/01234.json`
- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/studio/data/tag_assignments.json`
- `var/delete_work/backups/YYYYMMDD-HHMMSS/` on `--write`

Workbook/manual follow-up after run:

- Remove or archive the deleted work's rows from `WorkDetails`, `WorkFiles`, and `WorkLinks`.
- Update the `Series` sheet manually if the deleted work was still referenced there.
- Manually remove or archive the deleted work's canonical prose file from the external projects prose folder if you do not want to keep it.
- Manually remove stale staged media under `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/01234-*` and any stale detail media.

Potential improvements:

- Add cross-sheet workbook cleanup for `WorkDetails`, `WorkFiles`, `WorkLinks`, and `Series.primary_work_id`.
- Add bulk-delete support.
- Add staged-media cleanup for deleted works.

Current caveat:

- Dry-run this command before relying on it. The script is clearly intended to be the delete path, but it still leaves important workbook cleanup manual and should be treated as a targeted generated-artifact cleanup tool, not a full catalog mutation workflow.

## 11) Delete a series and all the works in it

Workbook edits before run:

- Decide whether every work in the series is truly being deleted, or whether some works are being kept and merely removed from this series.
- For works being deleted, set `Works.status=delete`.
- For works being kept elsewhere, remove the `series_id` from `Works.series_ids` instead.
- Remove the series row from `Series` once the work-level plan is clear.
- Remove the series row from `SeriesSort` if present.

CLI:

```bash
./scripts/delete_work.py --work-id 01234
./scripts/delete_work.py --work-id 01234 --write
./scripts/delete_work.py --work-id 04567
./scripts/delete_work.py --work-id 04567 --write
./scripts/generate_work_pages.py --only series-index-json
./scripts/generate_work_pages.py --only series-index-json --write
```

Run the delete command once per work in the series. If any works are being reassigned instead of deleted, also run the relevant membership-change workflow from sections 7 to 9.

Repo artifacts touched by the calls:

- The same per-work artifacts listed in use case 10, once per deleted work
- `assets/data/series_index.json`

Workbook/manual follow-up after run:

- Manually delete stale `_series/<series_id>.md`.
- Manually delete or archive the canonical external prose source file for the series, if one exists at `projects/<primary_work_project_folder>/<prose_subdir>/<series_prose_file>`.
- Manually remove the series entry from `assets/studio/data/tag_assignments.json`.
- Remove stale `SeriesSort` rows and any surviving workbook references to the deleted series.

Potential improvements:

- Add a dedicated `delete-series` command.
- Make that command delete or reassign member works, remove the series stub, remove the Tag Studio entry, and validate that no workbook references remain.

## 12) Change metadata for a series

Workbook edits before run:

- Edit the `Series` row fields such as `title`, `year`, `year_display`, `primary_work_id`, `notes`, or `series_type`.
- If the change also affects sort behavior, update `SeriesSort`.

CLI:

```bash
./scripts/generate_work_pages.py \
  --series-ids some-series \
  --only series-pages \
  --only series-index-json \
  --force
./scripts/generate_work_pages.py \
  --series-ids some-series \
  --only series-pages \
  --only series-index-json \
  --force \
  --write
```

If you also changed `SeriesSort`, add `--only work-pages` so `_works/<work_id>.md` gets fresh `series_sort` values for that series.

Scoping note:

- `series-pages` is scoped to `some-series`.
- `series-index-json` is still a global rebuild of one file.

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_series/some-series.md`
- `assets/data/series_index.json`
- `_works/<work_id>.md` for that series if `work-pages` was also selected

Workbook/manual follow-up after run:

- None normally.

Potential improvements:

- Allow published series metadata refresh without requiring `--force`.
- Add a `series-metadata` mode that does not also bump `published_date` on forced rewrites.

## 13) Change metadata for a work

Workbook edits before run:

- Edit the `Works` row fields such as `title`, `year`, `dimensions`, `medium`, or other work metadata.
- If the primary source image path changed too, update `project_filename` and use the media pipeline in addition to the metadata refresh.

CLI:

```bash
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-pages \
  --only work-json \
  --only works-index-json \
  --force
./scripts/generate_work_pages.py \
  --work-ids 01234 \
  --only work-pages \
  --only work-json \
  --only works-index-json \
  --force \
  --write
```

If the primary source image changed as well, run the media pipeline first:

```bash
./scripts/build_catalogue.py --mode work --work-ids 01234 --dry-run
./scripts/build_catalogue.py --mode work --work-ids 01234
```

Repo artifacts touched by the call:

- `data/works.xlsx`
- `_works/01234.md`
- `assets/works/index/01234.json`
- `assets/data/works_index.json`

Scoping note:

- `_works/01234.md` and `assets/works/index/01234.json` are work-scoped here.
- `assets/data/works_index.json` is still rebuilt globally.

Workbook/manual follow-up after run:

- None normally.
- If the primary source image changed and the old staged media should disappear, remove stale staged media manually. Current pipeline runs add/refresh media; they do not prune obsolete media automatically.

Potential improvements:

- Add a `work-metadata` mode for published works that does not require `--force`.
- Add stale-primary-media pruning when `project_filename` changes.
