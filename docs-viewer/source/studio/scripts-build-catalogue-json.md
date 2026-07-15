---
doc_id: scripts-build-catalogue-json
title: Scoped JSON Catalogue Build
added_date: 2026-04-18
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Scoped JSON Catalogue Build

## Purpose

`studio/services/catalogue/catalogue_json_build.py` previews or executes a narrow public catalogue rebuild from canonical JSON source.

It is the command-line companion to Work and Series public-update actions in Local Studio. The script also retains wider catalogue maintenance capabilities, including Moment and catalogue-wide thumbnail scopes; those CLI options do not imply that Local Studio has matching editor routes.

## Common Commands

Preview or apply one Work scope:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --write
```

Preview the effect of specific changed fields:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --changed-fields duration
```

Regenerate only local media for a Work or one detail:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --media-only --force --write
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --detail-uid 00001-003 --media-only --force --write
```

Preview or apply one Series scope:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --series-id 004
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --series-id 004 --write
```

Use `--extra-series-ids` when a membership change must also rebuild a previous Series. Use `--thumbnail-only --force` for deliberate catalogue-wide thumbnail maintenance. Run `--help` for the exact current option inventory.

## Execution Path

```text
CLI or Studio build request
  -> catalogue_json_build.py
  -> catalogue_build_scopes.py resolves records
  -> catalogue_build_field_plan.py narrows artifact families
  -> catalogue_build_media.py plans local media
  -> catalogue_build_commands.py shapes generator/search commands
  -> generate_work_pages.py writes selected public artifacts
  -> build_search.py refreshes catalogue search when selected
```

The field registry path comes from `studio/app/frontend/config/studio-config.json`. Unknown fields or mixed dependency classes use a conservative fallback and explain that choice in preview output.

## Build Boundary

- Canonical metadata is read from `studio/data/canonical/catalogue/` and is never written by this command.
- Optional Work and Series prose is rendered from `studio/data/canonical/catalogue-markdown/`.
- Draft Work and Series records are not public build targets.
- Scope validation checks Series publication, membership, and primary-Work requirements.
- Normal runs skip unchanged output by content; `--force` requests intentional regeneration.
- `--media-only` stops before page/JSON generation and catalogue search.
- The command does not upload primary images to R2 or advance media versions.

## Media Outputs

Work images resolve from their project folder, optional project subfolder, and filename. Detail images resolve from the parent Work folder, optional section detail subfolder, and detail filename.

Local primary and temporary thumbnail variants are generated under `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/`. Thumbnails are copied into the repo-owned public asset folders; primary variants remain staged for [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2).

The external staging root has no repo-local fallback. It is rebuildable from canonical catalogue metadata and configured source-media trees.

## Where To Change It

- record selection and publication constraints: `catalogue_build_scopes.py`
- field-to-artifact planning: `catalogue_build_field_plan.py` and the catalogue field registry
- source-image and derivative behavior: `catalogue_build_media.py`
- generator/search invocation: `catalogue_build_commands.py`
- public payload construction: `generate_work_pages.py`
- CLI options and orchestration: `catalogue_json_build.py`

Keep the preview and apply planners aligned. Tests and `studio/services/catalogue/verify_catalogue_field_registry.py` are the authority for exact current selection behavior.
