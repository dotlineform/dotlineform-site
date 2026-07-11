---
doc_id: local-setup-environment
title: Local Setup Environment
added_date: 2026-05-19
last_updated: 2026-06-22
parent_id: local-setup
---
# Local Setup Environment

## Repo-local env file

Use a gitignored repo-local env file for runtime paths, local runner options, and R2 credentials:

```bash
$EDITOR .env.local
```

Recommended shape:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/absolute/path/to/dotlineform"
export MAKE_SRCSET_JOBS=4

export R2_ACCOUNT_ID="..."
export R2_ACCESS_KEY_ID="..."
export R2_SECRET_ACCESS_KEY="..."
export R2_BUCKET="..."
export R2_ENDPOINT="https://<account_id>.r2.cloudflarestorage.com"
```

Local repo scripts, `bin/local-studio`, `bin/local-admin`, `bin/local-analytics`, `bin/local-all`, and `docs-viewer/bin/docs-viewer` read this file directly.
Do not duplicate these repo-specific values in shell startup files.

What the shared variables mean:

- `DOTLINEFORM_PROJECTS_BASE_DIR`: base directory for source-media trees and external local application workspaces
- `MAKE_SRCSET_JOBS`: optional default parallel worker count for srcset generation

Docs Viewer external local scopes also use `DOTLINEFORM_PROJECTS_BASE_DIR`.
For those scopes, create the external Docs Viewer data root before using the New scope action:

```bash
mkdir -p "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"
mkdir -p "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing"
```

Docs Viewer then derives external local source and generated JSON paths below that fixed directory.
The New scope modal does not accept a custom external path.

Data Sharing and Docs Review use the fixed `data-sharing/` workspace for exports, returned-package staging, metadata, and preview sessions. Active Data Sharing capabilities are unavailable with setup guidance when this directory is missing, unreadable, or unwritable.

Common local app runner variables:

- `STUDIO_APP_HOST`, `STUDIO_APP_PORT`, `STUDIO_APP_ACCESS_LOG`
- `ADMIN_APP_HOST`, `ADMIN_APP_PORT`, `ADMIN_APP_ACCESS_LOG`
- `ANALYTICS_APP_HOST`, `ANALYTICS_APP_PORT`, `ANALYTICS_APP_ACCESS_LOG`
- `DOCS_VIEWER_HOST`, `DOCS_VIEWER_PORT`, `DOCS_VIEWER_BASE_URL`, `DOCS_VIEWER_REVIEW_ENABLED`
- `SITE_ENABLED`, `SITE_HOST`, `SITE_PORT`, `SITE_ROOT`, `SITE_PREVIEW_BASE`

`bin/local-all` also reads `SITE_ENABLED`, `STUDIO_APP_ENABLED`, `ADMIN_APP_ENABLED`, and `ANALYTICS_APP_ENABLED` so a full-stack session can skip one of the supervised children without changing the independent runners.

Media staging, generated srcset output, and staged work downloads are repo-local under `var/catalogue/media/`.

R2 media publishing also requires:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

Do not commit R2 credential values.
The publisher script reports missing variable names without printing configured values.
`.env.local` is gitignored, so it is local-only.

The R2 publisher reads `.env.local` by default:

```bash
./scripts/media/publish_media_to_r2.py --scope catalogue --kind works --id 01007
```

Two additional env vars are used by the srcset wrapper, but they are usually set per-command by pipeline scripts rather than persisted globally:

- `MAKE_SRCSET_WORK_IDS_FILE`
- `MAKE_SRCSET_SUCCESS_IDS_FILE`

Those manifest env vars do not normally need to be added to your shell startup files.

## .env.local versus process environment

For local runs, `.env.local` is the canonical source for repo-specific runtime configuration.
The shared Python loader reads it directly, and values from this file win over inherited shell values when the same key appears in both places.

- `.env.local` is a repo-specific source file that keeps local paths and credentials in one predictable place.
- Local CLI scripts and local services read `.env.local` server-side; browser code must never read this file or receive R2 credentials.
- If `.env.local` is absent, scripts fall back to process environment variables for cloud/Codespaces runs.
- In cloud/Codespaces, use platform secret stores or configured environment variables instead of creating, committing, or syncing a `.env.local` file.

The practical reason for this convention is that media handling is increasingly driven by local Studio actions.
Keeping repo-specific runtime config in `.env.local` gives CLI commands, local write services, and future UI-triggered orchestration one consistent source of local configuration without relying on shell startup files.


## Repo-specific operating notes

- Run project commands from `dotlineform-site/`.
- Prefer the project-local script form: `./scripts/...`.
- canonical catalogue metadata now lives under `studio/data/canonical/catalogue/`.
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
$HOME/miniconda3/bin/python3 admin-app/checks/audit_site_consistency.py --strict
$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001
$HOME/miniconda3/bin/python3 admin-app/checks/css_token_audit.py
bin/local-studio
bin/local-admin
bin/local-analytics
docs-viewer/bin/docs-viewer
```
