---
doc_id: scripts-docs-builder
title: Docs Viewer Builder
added_date: 2026-04-23
last_updated: 2026-05-26
parent_id: docs-viewer
sort_order: 20000
---
# Docs Viewer Builder

Script:

```bash
./docs-viewer/build/build_docs.rb --write
```

The operational entrypoint is the Docs Viewer-owned builder above.
There is no root `scripts/` wrapper for this command; use the full path so command ownership stays visible.

## Scope

Source location:

- `docs-viewer/source/studio/`
- `docs-viewer/source/analysis/`
- `docs-viewer/source/library/`

Viewer route:

- Studio docs: `/docs/`
- Analysis docs: `/analysis/`
- Library docs: `/library/`

Generated outputs:

- `docs-viewer/generated/docs/studio/index.json`
- `docs-viewer/generated/docs/studio/by-id/<doc_id>.json`
- `docs-viewer/generated/docs/studio/references/index.json`
- `docs-viewer/generated/docs/studio/references/by-doc/<doc_id>.json`
- `docs-viewer/generated/docs/studio/references/by-target/<target_kind>/<target_id_slug>.json`
- `assets/data/docs/scopes/analysis/index.json`
- `assets/data/docs/scopes/analysis/by-id/<doc_id>.json`
- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Scope configuration:

- `docs-viewer/config/scopes/docs_scopes.json`

This config is the shared source of truth for docs scope ids, Markdown source roots, generated docs output roots, generated search output paths, viewer route bases, imported-media path prefixes, nested-source policy, updated-date display, unresolved-parent validation policy, and browser-safe Docs Viewer settings.
`./docs-viewer/build/build_docs.rb`, the Docs Viewer service, the docs HTML importer, and the live rebuild watcher all read the same config.
The `output` field owns the generated docs payload root.
The `search_output` field owns the generated docs-search index path.

## What The Builder Does

- reads Markdown source docs from each configured scope source root
- reads front matter metadata such as `doc_id`, `title`, `added_date`, `last_updated`, optional `summary`, optional `ui_status`, `parent_id`, optional `sort_order`, and optional `viewable`
- renders each Markdown body to HTML using the local Jekyll Markdown stack
- passes raw HTML through as part of the Markdown body, so self-contained HTML/CSS/SVG docs can live in `.md` files
- resolves <code>&#91;&#91;media:...&#93;&#93;</code> tokens in doc bodies against `_config.yml` `media_base` before rendering
- resolves <code>&#91;&#91;interactive-html:...&#93;&#93;</code> tokens to same-scope sandboxed iframes for repo-local interactive HTML assets
- resolves <code>&#91;&#91;ref:&lt;kind&gt;:&lt;id&gt;|&lt;label&gt;&#93;&#93;</code> semantic-reference tokens for catalogue works, series, and moments before Markdown rendering
- rewrites same-scope doc-to-doc links onto the scope-owned viewer route
- adds missing image `title` attributes from image `alt` text so rendered docs images expose the same text on hover without changing explicit titles
- emits scope-level viewer options such as compatibility non-loadable ids, compatibility manage-only tree root ids, and document-view updated-date visibility
- writes one index payload plus one per-doc payload for each configured scope
- writes incremental semantic-reference relationship artifacts under `references/`
- writes `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json` from `docs-viewer/config/scopes/docs_scopes.json`, including route/scope data and the `docs_viewer` browser settings used by local manage mode and public read-only routes
- writes incrementally: unchanged payloads and unchanged Docs Viewer browser config are skipped, and stale per-doc payloads are removed when they no longer belong to the rebuilt scope
- supports targeted same-scope payload rebuilds through `--only-doc-ids` when an orchestration layer has already proven the affected ids are safe

## Source Inclusion And Viewability

- every root-level `.md` file in `docs-viewer/source/studio/` is included in generated docs payloads
- every root-level `.md` file in `docs-viewer/source/library/` is included in generated docs payloads
- every `.md` file under `docs-viewer/source/analysis/` is included in generated docs payloads, including nested docs
- nested Markdown docs are rejected for Studio and Library so their flat source-layout contract stays explicit
- nested Markdown docs are allowed for Analysis, but viewer organisation still comes from `doc_id`, `parent_id`, and `sort_order`
- add front matter with `viewable: false` to generate a doc but keep it hidden from public/default tree, search, and recently-added views
- `archive` is treated as an ordinary doc id and parent folder; visibility comes from `viewable`, not from a structural system-folder rule
- docs can contain ordinary Markdown, raw HTML, or a mix of both
- generated index rows include `content_text_length`, derived from rendered HTML after plain-text extraction and title stripping, so Studio tooling can cheaply find docs with no body content
- Library source docs may temporarily contain imported `parent_id` values that do not resolve to current Library docs; the builder preserves those values in source but emits them as root-level generated relationships so `/library/` remains navigable
- if front matter is omitted, the builder falls back to:
  - `doc_id`: filename stem
  - `title`: first Markdown `#` heading, or a humanized filename

## Common Front Matter Fields

- `doc_id`
  stable ID used by the scope-owned viewer route
- `title`
  label used in the viewer index and page title
- `added_date`
  generated docs index metadata for recently-added lists; legacy source docs without this field fall back to `last_updated`; date-only `YYYY-MM-DD` and minute-precision `YYYY-MM-DD HH:MM` values are both valid
- `last_updated`
  display metadata for viewer scopes whose generated `viewer_options.show_updated_date` is not `false`, and search metadata for docs-domain search; date-only `YYYY-MM-DD` and minute-precision `YYYY-MM-DD HH:MM` values are both valid
- `summary`
  optional plain-text summary carried into docs-viewer index and per-doc payloads
- `ui_status`
  optional UI status key carried into docs-viewer index and per-doc payloads; the builder normalizes whitespace but does not validate the value against viewer config
- `parent_id`
  empty string for a top-level doc
- `sort_order`
  optional integer for stable ordering inside the index tree
- `viewable`
  optional boolean; set `false` to keep a generated doc hidden from public/default Docs Viewer discovery

## Link And Media Conventions

Practical authoring guidance:

- for task-level guidance on where docs images should be saved and what syntax to type, use [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)

Internal doc links:

- preferred Studio public link format: `/docs/?scope=studio&doc=<doc_id>`
- preferred Analysis public link format: `/analysis/?doc=<doc_id>`
- preferred Library public link format: `/library/?doc=<doc_id>`
- optional anchors should use the normal hash suffix on the scope-owned route
- the builder rewrites scope-owned viewer links and relative `.md` links onto the current scope-owned viewer route
- cross-scope viewer links are preserved when the linked viewer path or explicit `scope` query belongs to another docs scope
- the builder no longer rewrites legacy `/docs/.../` path links

Docs media tokens:

- use the literal token <code>&#91;&#91;media:path/to/file.jpg&#93;&#93;</code> in Markdown or raw HTML doc bodies
- the builder resolves this token against `_config.yml` `media_base`
- example:
  - <code>![Example](&#91;&#91;media:library/example.jpg&#93;&#93;)</code>
  - <code>&lt;img src="&#91;&#91;media:library/example.jpg&#93;&#93;" alt="Example"&gt;</code>
- this is intended for remotely hosted docs media, keeping the repo free of full-size docs images
- repo-local docs assets are ordinary public asset paths such as `/assets/docs/...`; they are not a builder token

Interactive HTML tokens:

- use the literal token <code>&#91;&#91;interactive-html:filename.html&#93;&#93;</code> when a doc needs to embed a repo-local interactive HTML asset
- add an optional pixel height as <code>&#91;&#91;interactive-html:filename.html height=546&#93;&#93;</code> when the default iframe height is too tall or too short for that asset
- filenames are same-scope only; do not include a scope name, slash, nested path, absolute path, or `..`
- the builder resolves the token to `assets/docs/interactive/<scope>/filename.html` and fails the build if that file is missing
- the rendered doc receives a sandboxed iframe with `sandbox="allow-scripts"` so the embedded file's JavaScript runs inside the iframe, not in the main Docs Viewer page
- start from `assets/docs/interactive/template.html`, save the finished file under the current scope folder, and test it directly in a browser before adding the token
- Docs Import can copy staged HTML files marked with `<meta name="dlf:docs-import-role" content="interactive-html">` into the matching scope folder, but the source doc still needs a manual token where each iframe should appear
- example for a Library doc:
  - source asset: `assets/docs/interactive/library/coincidence-salience.html`
  - Markdown token: <code>&#91;&#91;interactive-html:coincidence-salience.html height=546&#93;&#93;</code>

Semantic reference tokens:

- use the literal token <code>&#91;&#91;ref:&lt;kind&gt;:&lt;id&gt;|&lt;label&gt;&#93;&#93;</code> when a doc should render a normal link and record a generated relationship to a stable registry record
- omit the label as <code>&#91;&#91;ref:&lt;kind&gt;:&lt;id&gt;&#93;&#93;</code> to use the current resolved catalogue title
- v1 supports `work`, `series`, and `moment`
- v1 supports only `action=link`, which is also the default
- published catalogue targets open in a new browser tab with `target="_blank"` and `rel="noopener noreferrer"` so the current doc remains in place
- unsupported actions, unsupported kinds, missing ids, and draft catalogue targets render as inert annotated text and produce build warnings
- semantic-reference tokens are ignored inside fenced code blocks and inline code
- normal Markdown links remain plain links and do not create semantic-reference records
- examples:
  - <code>&#91;&#91;ref:work:00638|3 symbols&#93;&#93;</code>
  - <code>&#91;&#91;ref:work:00638&#93;&#93;</code>
  - <code>&#91;&#91;ref:series:026|collected 1989-1998&#93;&#93;</code>

## Commands

Default command:

```bash
./docs-viewer/build/build_docs.rb --write
```

Dry run:

```bash
./docs-viewer/build/build_docs.rb
```

Flags:

- `--scope NAME`
  limit the build to a named docs scope
  current values: `studio`, `analysis`, `library`
  if omitted, the builder runs for all configured scopes
- `--source PATH`
  override docs source directory for a single selected scope
- `--output PATH`
  override output directory for generated JSON payloads for a single selected scope
- `--viewer-base-url URL`
  override viewer route base used when generating `viewer_url` values and rewritten internal doc links for a single selected scope
- `--only-doc-ids IDS`
  comma-separated doc ids for a targeted same-scope payload rebuild; this requires exactly one selected scope and is intended for docs-management and watcher orchestration, not broad manual cleanup
- `--write`
  persist generated files; if omitted, the script prints a dry-run summary only

Targeted dry run:

```bash
./docs-viewer/build/build_docs.rb --scope studio --only-doc-ids docs-build-management-import-export-improvements
```

Targeted write:

```bash
./docs-viewer/build/build_docs.rb --scope studio --write --only-doc-ids docs-build-management-import-export-improvements
```

## Diagnostics

Each selected scope run prints one compact diagnostics line after the dry-run or write summary:

```text
Docs builder diagnostics: {"scope":"studio",...}
```

The diagnostics payload is console output only. It does not change the generated Docs Viewer JSON schema.

Current fields:

- `scope`
- `build_mode`
- `only_doc_ids`
- `source_files_scanned`
- `docs_emitted`
- `doc_payloads_changed`
- `doc_payloads_removed`
- `reference_index_changed`
- `reference_by_doc_payloads_changed`
- `reference_by_doc_payloads_removed`
- `reference_by_target_payloads_changed`
- `reference_by_target_payloads_removed`
- `warning_count`
- `warnings`
- `elapsed_seconds`

## Operational Notes

- `bin/local-studio` runs this builder only when `DOCS_STARTUP_REBUILD_SCOPES` requests a startup docs/docs-search rebuild
- `bin/local-studio` also starts the Docs Live Rebuild Watcher, which watches `docs-viewer/source/studio/*.md`, `docs-viewer/source/analysis/**/*.md`, and `docs-viewer/source/library/*.md` and then rebuilds same-scope docs payloads plus same-scope docs search
- if you disable the watcher or want explicit control while the dev runner is already running, re-run `./docs-viewer/build/build_docs.rb --scope <scope> --write`
- Docs Viewer manage mode rebuilds the current docs scope through the standalone Docs Viewer service
- manual `./docs-viewer/build/build_docs.rb --scope <scope> --write` remains a low-level docs-payload rebuild only
- live Docs Viewer management actions chain same-scope docs search through the Docs Viewer service rather than through `build_docs.rb` itself
- changing only the docs data does not require any separate asset pipeline
- manual `./docs-viewer/build/build_docs.rb --write` with no `--scope` rebuilds all configured docs scopes, currently `studio`, `analysis`, and `library`
- current write behavior is incremental within the rebuilt scope:
  - unchanged `index.json` or `by-id/<doc_id>.json` payloads are not rewritten
  - stale `by-id/<doc_id>.json` payloads are removed when the rebuilt scope no longer generates that doc
  - unchanged semantic-reference by-doc and by-target payloads are not rewritten
  - stale semantic-reference by-doc and by-target payloads are removed when references or source docs no longer generate them
- targeted `--only-doc-ids` writes still rebuild the scope index from current source metadata, but render and write only selected per-doc payloads; unchanged unselected rows keep their existing generated payload text length
- targeted semantic-reference writes rebuild the selected docs' by-doc records and derive by-target buckets from the refreshed selected records plus existing unselected by-doc records, so stale target buckets are removed when a selected doc changes or drops references
- targeted writes require existing full-scope generated output for the scope; use a full `./docs-viewer/build/build_docs.rb --scope <scope> --write` first when initializing or repairing an output tree
- if you want a scope-specific rebuild, use `--scope studio`, `--scope analysis`, or `--scope library` explicitly

Jekyll verification builds:

- if `jekyll serve` is already running, avoid building into the default `_site/` destination at the same time
- concurrent writes to the same `_site/` tree can produce transient static-file copy failures even when the source asset is valid
- for a one-off verification build while the dev server is active, use a separate destination:

```bash
bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build
```

Local runtime values shared with media/generation scripts live in `var/local/site.env`:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/path/to/dotlineform"
export MAKE_SRCSET_JOBS=4
```

Pipeline policy config:

- shared pipeline defaults live in `_data/pipeline.json`
- that config stores env var names and repo-local media staging subpaths
- the default env var names remain `DOTLINEFORM_PROJECTS_BASE_DIR` and `MAKE_SRCSET_JOBS`
- srcset manifest env var names also live there; defaults remain `MAKE_SRCSET_WORK_IDS_FILE` and `MAKE_SRCSET_SUCCESS_IDS_FILE`
- CLI flags still override config-derived defaults

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- CSS Audit Latest
