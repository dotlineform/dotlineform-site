---
doc_id: scripts-docs-builder
title: "Docs Viewer Builder"
last_updated: 2026-04-21
parent_id: scripts
sort_order: 20
---
# Docs Viewer Builder

Script:

```bash
./scripts/build_docs.rb --write
```

## Scope

Source location:

- `_docs_src/`
- `_docs_library_src/`

Published viewer route:

- Studio docs: `/docs/`
- Library docs: `/library/`

Generated outputs:

- `assets/data/docs/scopes/studio/index.json`
- `assets/data/docs/scopes/studio/by-id/<doc_id>.json`
- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

## What The Builder Does

- reads Markdown source docs from each configured flat scope source root
- reads front matter metadata such as `doc_id`, `title`, `last_updated`, `parent_id`, optional `sort_order`, and optional `published`
- renders each Markdown body to HTML using the local Jekyll Markdown stack
- passes raw HTML through as part of the Markdown body, so self-contained HTML/CSS/SVG docs can live in `.md` files
- resolves `[[media:...]]` tokens in doc bodies against `_config.yml` `media_base` before rendering
- rewrites doc-to-doc links onto the scope-owned viewer route
- writes one index payload plus one per-doc payload for each configured scope
- writes incrementally: unchanged payloads are skipped, and stale per-doc payloads are removed when they no longer belong to the rebuilt scope

## Publishing Rules

- every root-level `.md` file in `_docs_src/` is published by default
- every root-level `.md` file in `_docs_library_src/` is published by default
- nested Markdown docs are rejected so the flat source-layout contract stays explicit
- add front matter with `published: false` to keep a Markdown file in either source root without publishing it
- docs can contain ordinary Markdown, raw HTML, or a mix of both
- if front matter is omitted, the builder falls back to:
  - `doc_id`: filename stem
  - `title`: first Markdown `#` heading, or a humanized filename

## Common Front Matter Fields

- `doc_id`
  stable ID used by the scope-owned viewer route
- `title`
  label used in the viewer index and page title
- `last_updated`
  display metadata for the viewer
- `parent_id`
  empty string for a top-level doc
- `sort_order`
  optional integer for stable ordering inside the index tree
- `published`
  optional boolean; set `false` to exclude the file from published docs output

## Link And Media Conventions

Internal doc links:

- preferred Studio public link format: `/docs/?scope=studio&doc=<doc_id>`
- preferred Library public link format: `/library/?doc=<doc_id>`
- optional anchors should use the normal hash suffix on the scope-owned route
- the builder rewrites scope-owned viewer links and relative `.md` links onto the current scope-owned viewer route
- the builder no longer rewrites legacy `/docs/.../` path links

Docs media tokens:

- use `[[media:path/to/file.jpg]]` in Markdown or raw HTML doc bodies
- the builder resolves this token against `_config.yml` `media_base`
- example:
  - `![Example]([[media:library/example.jpg]])`
  - `<img src="[[media:library/example.jpg]]" alt="Example">`
- this is intended for remotely hosted docs media, keeping the repo free of full-size docs images

## Commands

Default command:

```bash
./scripts/build_docs.rb --write
```

Dry run:

```bash
./scripts/build_docs.rb
```

Flags:

- `--scope NAME`
  limit the build to a named docs scope
  current values: `studio`, `library`
- `--source PATH`
  override docs source directory for a single selected scope
- `--output PATH`
  override output directory for generated JSON payloads for a single selected scope
- `--viewer-base-url URL`
  override viewer route base used when generating `viewer_url` values and rewritten internal doc links for a single selected scope
- `--write`
  persist generated files; if omitted, the script prints a dry-run summary only

## Operational Notes

- `bin/dev-studio` currently runs this builder for the `studio` scope once before starting Jekyll
- if you edit `_docs_src/` or `_docs_library_src/` while the dev runner is already running, re-run `./scripts/build_docs.rb --write`
- docs viewer manage mode rebuilds the current docs scope through the localhost docs-management service
- changing only the docs data does not require any separate asset pipeline
- current write behavior is incremental within the rebuilt scope:
  - unchanged `index.json` or `by-id/<doc_id>.json` payloads are not rewritten
  - stale `by-id/<doc_id>.json` payloads are removed when the rebuilt scope no longer publishes that doc
- if you want a scope-specific rebuild, use `--scope studio` or `--scope library` explicitly

Jekyll verification builds:

- if `jekyll serve` or `bin/dev-studio` is already running, avoid building into the default `_site/` destination at the same time
- concurrent writes to the same `_site/` tree can produce transient static-file copy failures even when the source asset is valid
- for a one-off verification build while the dev server is active, use a separate destination:

```bash
bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build
```

Local environment variables shared with media/generation scripts:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="/path/to/dotlineform-icloud"
```

Pipeline policy config:

- shared pipeline defaults live in `_data/pipeline.json`
- that config stores env var names and relative media subpaths
- the default env var names remain `DOTLINEFORM_PROJECTS_BASE_DIR`, `DOTLINEFORM_MEDIA_BASE_DIR`, and `MAKE_SRCSET_JOBS`
- srcset manifest env var names also live there; defaults remain `MAKE_SRCSET_WORK_IDS_FILE` and `MAKE_SRCSET_SUCCESS_IDS_FILE`
- CLI flags still override config-derived defaults

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest)
