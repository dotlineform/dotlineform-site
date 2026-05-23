---
doc_id: local-setup-environment
title: Local Setup Environment
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: local-setup
sort_order: 2200
---
# Local Setup Environment

## Repo-local env file

Use a gitignored repo-local env file for runtime paths, local runner options, and R2 credentials:

```bash
mkdir -p var/local
$EDITOR var/local/site.env
```

Recommended shape:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/absolute/path/to/dotlineform"
export MAKE_SRCSET_JOBS=4
export DOCS_STARTUP_REBUILD_SCOPES=""

export R2_ACCOUNT_ID="..."
export R2_ACCESS_KEY_ID="..."
export R2_SECRET_ACCESS_KEY="..."
export R2_BUCKET="..."
export R2_ENDPOINT="https://<account_id>.r2.cloudflarestorage.com"
```

Local repo scripts and `bin/local-studio` read this file directly.
Do not duplicate these repo-specific values in shell startup files.

What the shared variables mean:

- `DOTLINEFORM_PROJECTS_BASE_DIR`: base directory that contains the source `projects/` and `moments/` trees used for dimension reads and source-media lookup
- `MAKE_SRCSET_JOBS`: optional default parallel worker count for srcset generation
- `DOCS_STARTUP_REBUILD_SCOPES`: optional `bin/local-studio` startup docs/docs-search rebuild scopes; keep it blank as an explicit reminder that startup rebuilds are off

Media staging, generated srcset output, and staged work downloads are repo-local under `var/catalogue/media/`.

R2 media publishing also requires:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

Do not commit R2 credential values.
The publisher script reports missing variable names without printing configured values.
`var/local/` is gitignored, so `var/local/site.env` is local-only.

The R2 publisher reads `var/local/site.env` by default:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
```

Two additional env vars are used by the srcset wrapper, but they are usually set per-command by pipeline scripts rather than persisted globally:

- `MAKE_SRCSET_WORK_IDS_FILE`
- `MAKE_SRCSET_SUCCESS_IDS_FILE`

Those manifest env vars do not normally need to be added to your shell startup files.

## site.env versus process environment

For local runs, `var/local/site.env` is the canonical source for repo-specific runtime configuration.
The shared Python loader reads it directly, and values from this file win over inherited shell values when the same key appears in both places.

- `var/local/site.env` is a repo-specific source file that keeps local paths and credentials in one predictable place.
- Local CLI scripts and local services read `site.env` server-side; browser code must never read this file or receive R2 credentials.
- If `site.env` is absent, scripts fall back to process environment variables for cloud/Codespaces runs.
- In cloud/Codespaces, use platform secret stores or configured environment variables instead of creating, committing, or syncing a `site.env` file.

The practical reason for this convention is that media handling is increasingly driven by local Studio actions.
Keeping repo-specific runtime config in `var/local/site.env` gives CLI commands, local write services, and future UI-triggered orchestration one consistent source of local configuration without relying on shell startup files.


## Repo-specific operating notes

- Run project commands from `dotlineform-site/`.
- Prefer the project-local script form: `./scripts/...`.
- canonical catalogue metadata now lives under `assets/studio/data/catalogue/`.
- `data/works_bulk_import.xlsx` is only used for the separate bulk-import workflow for new works and new work details.
- Shared env var names and media subpaths are defined in `_data/pipeline.json`.
- The pipeline currently generates primary image variants at `800`, `1200`, and `1600` widths.
- Thumb sizes are currently `96` and `192`.
- The repo still accepts some legacy `2400` references in compatibility checks, but new moment variants should stay at `800`, `1200`, and `1600`.
- HEIC/HEIF input conversion uses macOS `sips` when available and otherwise falls back to `heif-convert`.
- Image derivative generation requires `ffmpeg`; the scripts fail fast if it is missing.
- Script logs are written locally under `logs/` and `var/studio/logs/`.

Common commands:

```bash
./scripts/checks/audit_site_consistency.py --strict
./scripts/catalogue/validate_catalogue_source.py
./scripts/catalogue/catalogue_json_build.py --work-id 00001
python3 ./scripts/checks/css_token_audit.py
bin/local-studio
```
