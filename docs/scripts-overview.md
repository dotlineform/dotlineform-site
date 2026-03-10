---
permalink: /docs/scripts-overview/
---

# Scripts Overview

Use this command prefix for all script commands:

```bash
./
```

All commands below assume you are in `dotlineform-site/`.

Local environment variables (required for media/generation scripts):

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="/path/to/dotlineform-icloud"
```

Sorting behavior and consistency contract:

- `docs/sorting-architecture.md`

Deferred improvements and follow-up items:

- `docs/backlog.md`
- `docs/css-audit-spec.md`
- `docs/css-audit-latest.md`

## Main Pipeline

Run everything (copy -> srcset -> page generation):

```bash
./scripts/run_draft_pipeline.py --dry-run
./scripts/run_draft_pipeline.py
```

Useful flags:

- `--dry-run`: preview only (no workbook writes/deletes)
- `--force-generate`: pass `--force` through to `generate_work_pages.py`
- `--jobs N`: srcset parallel jobs (default: `4`, or `MAKE_SRCSET_JOBS` env var)
- `--mode work|work_details|moment`: run only selected flow(s). Repeat flag to run multiple.
- `--work-ids`, `--work-ids-file`: limit work + work_details scope
- `--series-ids`, `--series-ids-file`: pass series scope to generation
- `--moment-ids`, `--moment-ids-file`: limit moment scope
- `--xlsx PATH`: workbook path override
- `--input-dir`, `--output-dir`: works source/derivative dirs
- `--detail-input-dir`, `--detail-output-dir`: work_details source/derivative dirs
- `--moment-input-dir`, `--moment-output-dir`: moments source/derivative dirs

Mode examples:

```bash
./scripts/run_draft_pipeline.py --mode moment --dry-run
./scripts/run_draft_pipeline.py --mode work --mode work_details --dry-run
./scripts/run_draft_pipeline.py --mode moment --moment-ids blue-sky,compiled --dry-run
./scripts/run_draft_pipeline.py --mode work --work-ids 00456 --dry-run
```

Note: when `--mode work` is used and no `--series-ids*` are provided, draft series are auto-included in generation.

## Individual Scripts

### 1) Copy draft source images from workbook

Unified script with mode flags:

```bash
./scripts/copy_draft_media_files.py --mode work --ids-file /tmp/work_ids.txt --copied-ids-file /tmp/copied_work_ids.txt --write
./scripts/copy_draft_media_files.py --mode work_details --ids-file /tmp/detail_uids.txt --copied-ids-file /tmp/copied_detail_uids.txt --write
./scripts/copy_draft_media_files.py --mode moment --ids-file /tmp/moment_ids.txt --copied-ids-file /tmp/copied_moment_ids.txt --write
```

Flags:

- `--mode work|work_details|moment`
- `--ids-file`: optional filter manifest (one ID per line)
- `--copied-ids-file`: optional output manifest of successfully copied IDs
- `--write`: perform copy (omit for dry-run)
- `--keep-ext` / `--no-ext`: keep/remove source extension in copied filename

### 2) Build srcset derivatives

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_work_ids.txt \
MAKE_SRCSET_2400_IDS_FILE=/tmp/work_2400_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/work_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/srcset_images" \
  4
```

Moments example (no 2400):

```bash
: > /tmp/empty_2400_ids.txt
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_moment_ids.txt \
MAKE_SRCSET_2400_IDS_FILE=/tmp/empty_2400_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/moment_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/srcset_images" \
  4
```

### 3) Generate Jekyll pages from workbook

```bash
./scripts/generate_work_pages.py data/works.xlsx
./scripts/generate_work_pages.py data/works.xlsx --write
```

Common scoped runs:

```bash
./scripts/generate_work_pages.py data/works.xlsx --work-ids 00456 --write
./scripts/generate_work_pages.py data/works.xlsx --work-ids-file /tmp/work_ids.txt --write
./scripts/generate_work_pages.py data/works.xlsx --series-ids curve-poems,dots --write
```

Useful flags:

- `--write`: persist file/workbook changes
- `--force`: regenerate even when checksums match
- `--work-ids`, `--work-ids-file`
- `--series-ids`, `--series-ids-file`
- `--moment-ids`, `--moment-ids-file`
- `--works-files-dir` (default `assets/works/files`)
- `--moments-sheet` (default `Moments`)
- `--moments-output-dir` (default `_moments`)
- `--moments-prose-dir` (default `_includes/moments_prose`)
- `--projects-base-dir`: base path used for source-image dimension reads
  - default is taken from `DOTLINEFORM_PROJECTS_BASE_DIR`
- `--series-index-json-path` (default `assets/data/series_index.json`)
- `--works-index-json-path` (default `assets/data/works_index.json`)
- `--work-details-index-json-path` (default `assets/data/work_details_index.json`)
- `--only`: limit generation to selected artifacts
  - allowed: `work-pages`, `works-curator-pages`, `work-files`, `series-pages`, `series-index-json`, `work-details-pages`, `work-json`, `works-index-json`, `work-details-index-json`, `moments`
  - coupling:
    - `works-curator-pages` runs only when explicitly included in `--only`
  - `work-pages`: writes `_works/<work_id>.md` as lightweight stubs (`work_id`, `title`, `layout`, `checksum`) plus optional prose include
  - `series-pages`: writes `_series/<series_id>.md` as lightweight stubs (`series_id`, `title`, `layout`, `checksum`) plus prose include
  - `work-details-pages`: writes `_work_details/<detail_uid>.md` as lightweight stubs (`work_id`, `detail_id`, `detail_uid`, `title`)
  - `series-index-json`: writes `assets/data/series_index.json` (full rebuild) with:
    - header: `schema`, deterministic content `version`, `generated_at_utc`, `count`
    - series map keyed by `series_id`
    - full series metadata used by generated series pages (`layout`, `status`, `published_date`, `title`, `title_sort`, `sort_fields`, `series_type`, `year`, `year_display`, `primary_work_id`, `notes`, `project_folders`, `checksum`)
    - ordered `works` (in canonical series sort order derived from `sort_fields`) and `thumb` selection
  - `works-index-json`: writes `assets/data/works_index.json` as a lightweight object keyed by `work_id`
    - each work keeps backward-compatible `series_id` as the first series and adds ordered `series_ids`
    - runtime thumb paths are derived from `work_id`, so no media/thumb payload is persisted here
    - always rebuilt as a full index (not scoped by `--work-ids`)
  - `work-details-index-json`: writes `assets/data/work_details_index.json` as a lightweight object keyed by `detail_uid`
    - always rebuilt as a full index (not scoped by `--work-ids`)
  - `work-json`: writes `assets/works/index/<work_id>.json` with `header` version/checksums, full `work`, and full `sections[].details[]`
    - `work.series_id` remains the first series and `work.series_ids` preserves the full ordered membership list from the workbook
    - work-driven: emits one file per selected work_id (uses `sections: []` when a work has no details)

Runtime canonical data flow:

- `/series/` and `/series/<series_id>/` read `assets/data/series_index.json`.
- `/series/<series_id>/` also reads `assets/data/works_index.json` for card metadata.
- `/works/<work_id>/` series nav/counter/link visibility read `assets/data/series_index.json`.
- `/work_details/` reads `assets/data/work_details_index.json`.

### 3b) Tag Studio local save server

Run:

```bash
python3 scripts/studio/tag_write_server.py
```

Optional flags:

- `--port 8787`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection (`_config.yml` parent search)
- `--dry-run`: validate and return response without writing files

Behavior:

- Exposes:
  - `GET /health`
  - `POST /save-tags`
  - `POST /import-tag-registry`
  - `POST /import-tag-aliases`
  - `POST /delete-tag-alias`
  - `POST /mutate-tag-alias-preview`
  - `POST /mutate-tag-alias`
  - `POST /promote-tag-alias-preview`
  - `POST /promote-tag-alias`
  - `POST /demote-tag-preview`
  - `POST /demote-tag`
  - `POST /mutate-tag-preview`
  - `POST /mutate-tag`
  - Tag Studio page probes `/health` and shows:
  - `Save mode: Local server` when available
  - `Save mode: Patch` when unavailable (fallback to patch modal)
  - `POST /save-tags` expects assignment objects in `tags`:
    - series save payload: `{ "series_id": "<series>", "tags": [...] }`
    - work override save payload: `{ "series_id": "<series>", "work_id": "<work_id>", "keep_work": true|false, "tags": [...] }`
    - `{ "tag_id": "<group>:<slug>", "w_manual": 0.3|0.6|0.9 }`
  - save writes `assets/studio/data/tag_assignments.json` with object-only tag rows (no string tags)
  - save is diff-based in the Series Tag Editor: the UI compares current series/work state against the last loaded/saved baseline and sends one `/save-tags` request for the series row when needed plus one request per changed work row
  - when multiple work pills are selected in the Series Tag Editor, the active work's current override set is used as the persisted state for all selected work pills
  - work override saves strip tags already inherited from `series[*].tags`
  - `keep_work: false` plus empty tags deletes `series[*].works[work_id]`
  - `keep_work: true` allows an explicit work row with `tags: []`
- Tag Registry page probes `/health` and shows:
  - `Import mode: Local server` when available
  - `Import mode: Patch` when unavailable (fallback to manual patch copy)
  - tag edit/delete requires local server mode
  - `New tag` button opens create modal:
    - group selected via group pills; slug + optional description entry
    - live duplicate check blocks existing `<group>:<slug>`
    - local mode uses `POST /import-tag-registry` with `mode: add` and a single tag payload
    - patch mode emits add-tag row snippet
- Import modes supported by endpoint:
  - `add` (no overwrite)
  - `merge` (add + overwrite)
  - `replace` (replace entire registry)
  - successful import responses include `summary_text` (same format used by Tag Registry UI and server log)
  - import request may include `import_filename`; server logs basename only (no client path)
  - tag mutation endpoint behavior (`POST /mutate-tag`):
    - `action: edit`: update canonical tag `description` (tag id/name remains fixed in UI flow)
    - `action: delete`: remove tag
    - delete cascades update `tag_assignments.json` and `tag_aliases.json`
    - aliases that become 1:1 self-maps (`alias == target slug`) are removed automatically
  - preview endpoint (`POST /mutate-tag-preview`) returns the same impact stats without writing files
  - tag demotion behavior:
    - trigger via tag pill `<-` action in registry list
    - preview via `POST /demote-tag-preview` is required before confirm
    - apply via `POST /demote-tag`
    - demotion removes canonical tag from registry, creates alias (`<slug>` -> chosen canonical targets), and rewrites assignments/alias target refs
    - patch fallback emits ordered manual steps only
- Tag Aliases page probes `/health` and shows:
  - `Import mode: Local server` when available
  - `Import mode: Patch` when unavailable (fallback to manual patch copy)
  - alias pill `×` delete:
    - local mode uses `POST /delete-tag-alias`
    - patch mode generates manual snippet with `aliases_to_remove`
  - alias text click opens edit modal:
    - live alias-name uniqueness validation
    - editable description + selected tags
    - selected tags must be canonical and satisfy: max 4 tags, max 1 per group
    - local mode uses `POST /mutate-tag-alias`
    - patch mode emits ordered `set_alias`/`remove_alias_key` steps
  - `New alias` button opens create modal:
    - same alias/tag validation and tag-picker behavior as edit modal
    - local mode uses `POST /import-tag-aliases` with `mode: add` and a single alias payload
    - patch mode emits add-alias fragment snippet
  - alias pill `→` promote:
    - user chooses target group at action time
    - preview via `POST /promote-tag-alias-preview` is required before confirm
    - apply via `POST /promote-tag-alias`
    - canonical tag id is `<group>:<alias-slug>`; label auto-derived from slug
    - if canonical already exists, alias key is removed only
    - patch fallback emits ordered manual steps only
  - Import modes supported by endpoint:
    - `add` (no overwrite)
    - `merge` (add + overwrite)
    - `replace` (replace entire aliases)
  - successful import responses include `summary_text` and `import_filename` (basename only)

Security constraints:

- Binds to loopback interface only (local machine only)
- CORS allows loopback origins only
- Write target is allowlisted to these files only:
  - `assets/studio/data/tag_assignments.json`
  - `assets/studio/data/tag_registry.json`
  - `assets/studio/data/tag_aliases.json`
  - timestamped backups are created in `var/studio/backups/`:
    - `tag_assignments.json.bak-YYYYMMDD-HHMMSS`
    - `tag_registry.json.bak-YYYYMMDD-HHMMSS`
    - `tag_aliases.json.bak-YYYYMMDD-HHMMSS`

Script logging:

- Per-script logs are written to repo-root log directories (auto-created).
- Current pipeline/logged scripts include:
  - `scripts/run_draft_pipeline.py` -> `logs/run_draft_pipeline.log`
  - `scripts/generate_work_pages.py` -> `logs/generate_work_pages.log`
  - `scripts/studio/tag_write_server.py` -> `var/studio/logs/tag_write_server.log`
- Log format is JSON Lines (one JSON object per line).
- Retention policy:
  - keep entries from the last 30 days
  - if no entries fall inside the last 30 days, keep the latest 1 day's worth (based on newest entry)

### 3c) CSS token audit

Run:

```bash
python3 scripts/css_token_audit.py
```

Optional flags:

- `--md-out docs/css-audit-latest.md`: override Markdown output path
- `assets/css/main.css assets/studio/css/studio.css`: optional file list override

Behavior:

- scans CSS for `font-size` declarations and color literals
- reports repeated raw typography values and direct color literals
- writes the current snapshot to `docs/css-audit-latest.md`

### 4) Audit site consistency (read-only)

Run an audit across generated pages and JSON:

```bash
./scripts/audit_site_consistency.py --strict
```

Scope and output options:

```bash
./scripts/audit_site_consistency.py \
  --checks cross_refs,schema,json_schema,links,media,orphans \
  --series-ids collected-1989-1998 \
  --json-out /tmp/site-audit.json \
  --md-out docs/audit-latest.md \
  --strict
```

Run a single check with the convenience alias:

```bash
./scripts/audit_site_consistency.py \
  --check-only schema \
  --max-samples 10
```

Or run multiple checks with repeated `--check-only`:

```bash
./scripts/audit_site_consistency.py \
  --check-only cross_refs \
  --check-only json_schema \
  --series-ids collected-1989-1998
```

Current checks:

- `cross_refs`: validates key references across `_works`, `_series`, `_work_details`, `assets/data/series_index.json`, and `assets/data/work_details_index.json` (including duplicate IDs)
- `schema`: validates required front matter fields by collection and format/consistency checks (`work_id`, `detail_uid`, slug-safe IDs, `sort_fields` token rules with `work_id` last sourced from canonical `series_index.json` with `_series` fallback, optional `_works.series_id` slug format, and `detail_uid` prefix matching `work_id`)
- `json_schema`: validates generated JSON structure/count consistency for:
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/data/work_details_index.json`
  - `assets/works/index/*.json`
- `links`: validates sitemap source/URL targets and query-parameter contract sanity across generated pages
- `media`: validates expected local thumbs/download files for published `_works` and `_work_details` (primaries are treated as remote-hosted and are not asserted locally)
- `orphans`: reports orphan pages/JSON; optionally include orphan media files with `--orphans-media`

`--strict` behavior and value:

- `--strict` exits non-zero when audit errors are found (`errors > 0`), so scripts/CI can fail fast.
- Warnings do not fail the run under `--strict`.
- Without `--strict`, the audit is informational and exits zero.

Query contract map used by `links` check:

| flow | produced query keys | destination accepts |
| --- | --- | --- |
| `series -> work` | `series`, `series_page` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |
| `works index -> work` | `from`, `return_sort`, `return_dir`, `return_series` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |
| `work -> work_details index` | `from_work`, `from_work_title`, `section`, `section_label`, `series`, `series_page` | `sort`, `dir`, `from_work`, `from_work_title`, `section`, `section_label`, `series`, `series_page` |
| `work -> work_details page` | `from_work`, `from_work_title`, `section`, `details_section`, `details_page`, `series`, `series_page` | `from_work`, `from_work_title`, `section`, `series`, `series_page`, `details_section`, `details_page`, `section_label` |
| `work_details page -> work` | `series`, `series_page`, `details_section`, `details_page` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |

Orphan media scan (optional):

```bash
./scripts/audit_site_consistency.py \
  --check-only orphans \
  --orphans-media
```

Markdown report is written by default to `docs/audit-latest.md` (overwrites each run).

To write to a different path:

```bash
./scripts/audit_site_consistency.py \
  --md-out /tmp/site-audit.md
```

Known limits:

- `media` assumes primaries are remote-hosted and checks local thumbs/downloads only.
- `json_schema` validates structure/counts, not recomputed payload hash integrity.
- `links` query-contract checks are static sanity checks; they do not execute browser flows.
- Orphan checks currently focus on works/series/work_details artifacts.

Warning policy:

- Treat schema warnings as backlog by default.
- Current warning rule: `_works.title_sort` is only warned when `title` contains digits and `title_sort` is missing.

### 5) Autofix missing numeric `title_sort` on works

Dry-run:

```bash
./scripts/fix_missing_title_sort.py
```

Write changes:

```bash
./scripts/fix_missing_title_sort.py --write
```

Scope to selected IDs/ranges:

```bash
./scripts/fix_missing_title_sort.py \
  --work-ids 66-74,38,40 \
  --write
```

### Works download files

If `Works.download` is set, generation also copies that file and links it on the work page.

- Source path:
  - `[projects-base-dir]/projects/[project_folder]/[download]`
- Destination path:
  - `assets/works/files/[work_id]-[filename.ext]`
- Work page link:
  - Label: `download`
  - Link text: `filename.ext`
  - Rendered before `cat. <work_id>`
