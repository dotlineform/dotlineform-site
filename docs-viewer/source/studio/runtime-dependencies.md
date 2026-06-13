---
doc_id: runtime-dependencies
title: Runtime Dependencies
added_date: 2026-04-23
last_updated: 2026-06-13
parent_id: dev-home
---
# Runtime Dependencies

This document records the main runtime and package dependencies used by this repo, where they come from, and which ones are critical in local versus cloud environments.

Use it to answer:

- which checked-in dependency files matter
- which packages are required for publish-sensitive parity
- which packages are feature-specific rather than baseline
- which dependencies matter in Codespaces and Codex Cloud

## Source Of Truth

Current checked-in dependency sources:

- Python packages:
  - `requirements.txt`
- system tools and cloud bootstrap expectations:
  - `.codex/setup.sh`
  - `.devcontainer/` files when present
- machine setup guidance:
  - [Local Setup](/docs/?scope=studio&doc=local-setup)
  - [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)

## Dependency Categories

The repo currently has four practical dependency layers:

1. Python packages from `requirements.txt`
2. external command-line tools used by media/generation workflows
3. local app/service runners and public-site preview/validation runners that consume Python
4. local or cloud runtime bootstrap scripts that install or verify the above

## Python Packages

Current checked-in Python packages:

| Package | Source | Used for in this repo | Local critical | Cloud critical | Notes |
| --- | --- | --- | --- | --- | --- |
| `openpyxl` | PyPI via `requirements.txt` | workbook and spreadsheet reads/writes in the Python pipeline | yes | yes when spreadsheet-driven scripts are used | baseline Python package for existing data flows |
| `beautifulsoup4` | PyPI via `requirements.txt` | HTML parsing for Docs HTML import | feature-specific | feature-specific | required for the HTML import feature once that importer is in use |
| `lxml` | PyPI via `requirements.txt` | parser backend for the Docs HTML import tree build | feature-specific | feature-specific | treated as part of the pinned HTML import parser stack |
| `bleach` | PyPI via `requirements.txt` | HTML sanitization for Docs HTML import | feature-specific | feature-specific | required for the intended import sanitization boundary even if the first scaffold uses only a subset of that behavior |
| `Pillow` | PyPI via `requirements.txt` | raster image conversion for Docs Markdown package imports | feature-specific | feature-specific | required when importing package images that must become 800px-max WebP outputs |
| `markdown-it-py` | PyPI via `requirements.txt` | CommonMark Markdown rendering for Python Docs Viewer builders and catalogue prose rendering | feature-specific | feature-specific | current renderer pin uses `MarkdownIt("commonmark")`, the built-in `table` rule, and no external plugins |

Current interpretation:

- `openpyxl` is the only current baseline Python package for the established catalogue/workbook pipeline
- `beautifulsoup4`, `lxml`, and `bleach` are checked-in because the HTML import feature is intended to build against a fixed parser/sanitizer stack from the start
- `Pillow` is checked-in because Markdown package imports convert local package images to WebP during write
- `markdown-it-py` is checked in because Docs Viewer payload generation and catalogue prose rendering use a pinned Python Markdown renderer
- in cloud environments that never touch Docs Import or generated Markdown rendering, these feature-specific packages are less critical operationally than `openpyxl`, but they are still part of the checked-in repo dependency set and should normally be installed for parity

## External Command-Line Tools

Some repo workflows depend on non-Python tools rather than extra Python packages.

Current notable tools:

| Tool | Source | Used for in this repo | Local critical | Cloud critical | Notes |
| --- | --- | --- | --- | --- | --- |
| `ffmpeg` | system package manager | media conversion and srcset-related workflows | workflow-specific | workflow-specific | not needed for docs-only or search-only work |
| `heif-convert` / `libheif` tools | system package manager | HEIF image conversion in media workflows | workflow-specific | workflow-specific | same boundary as media/import generation |
| `sips` | macOS system tool | local image handling on macOS | workflow-specific | no | macOS-only convenience/tooling boundary |

Current interpretation:

- these tools are not baseline dependencies for every repo task
- they matter for media/generation flows
- they are not required just to run docs builders, docs search builders, or the shared Docs Viewer

## Local Vs Cloud Priority

### Always important for parity

- `requirements.txt`
- `site-tools/config/site-tools.json`

These are the main checked-in contracts that keep local and cloud runs aligned.

### Usually needed in both local and cloud

- `openpyxl`
- the Python static validator when public-site deploy readiness matters

### Feature-specific but now part of the repo baseline install

- `beautifulsoup4`
- `lxml`
- `bleach`
- `Pillow`
- `markdown-it-py`

Reason:

- even though some packages are tied to Docs Import or generated-output features, they are now intentionally checked into `requirements.txt`
- Codespaces and Codex Cloud should therefore install them normally rather than treating them as purely ad hoc local extras

### Optional unless the workflow needs them

- `ffmpeg`
- `heif-convert`
- other media-tooling system packages

These matter only for workflows that actually generate or transform media.

## Local App Runtime Boundaries

The local apps use the existing Python runtime and checked-in source; the Analytics and UI Catalogue split did not add new package dependencies.

Current local app boundaries:

| Local app | Runner | Default URL | Dependency role |
| --- | --- | --- | --- |
| Public site preview | `bin/site-preview` | `http://127.0.0.1:4000/` | Python runtime plus checked-in `site/` files and `site-tools/` validation. |
| Local Studio | `bin/local-studio` | `http://127.0.0.1:8765/studio/` | Python runtime plus repo source for Studio catalogue, docs watcher, and startup maintenance tasks. |
| Local Admin | `bin/local-admin` | `http://127.0.0.1:8768/admin/` | Python runtime plus Admin source for operational pages and Admin-hosted UI Catalogue routes. |
| Local Analytics | `bin/local-analytics` | `http://127.0.0.1:8766/analytics/` | Python runtime plus Analytics app source, Analytics tag helpers, and Data Sharing workflow/adapters. |
| Docs Viewer | `docs-viewer/bin/docs-viewer` | `http://127.0.0.1:8776/docs/` | Python runtime plus Docs Viewer services, generated-read helpers, docs management, import/export, and conversion helpers. |

`bin/local-all` supervises these sibling services when a local session needs the full stack.
The services remain separate ownership boundaries; public preview does not publish through Studio, Studio does not host Analytics or Docs Viewer, Analytics does not proxy retired Studio paths, and UI Catalogue routes do not depend on Studio route config.
Docs Viewer docs/search generation, catalogue search generation, catalogue prose rendering, and public-site preview/validation are Python-backed local tooling paths.

## Codespaces And Codex Cloud Expectations

Current expectation:

- `requirements.txt` should normally be installed in cloud environments
- that means the HTML import parser/sanitizer stack is now part of the standard Python environment for cloud sessions
- this is useful because it avoids a split where local development uses one parser boundary and cloud sessions silently use another

Current practical split:

- critical for cloud parity:
  - Python packages in `requirements.txt`
  - public-site static builder and config when running publish-sensitive checks
- less critical for simple cloud sessions:
  - media system tools when the task does not touch media workflows

## Dependency Change Policy

When adding a dependency:

- add it to the checked-in source of truth for that layer
- document what uses it and whether it is baseline, workflow-specific, or feature-specific
- update relevant setup/runtime docs if cloud or local bootstrap expectations change

For Python packages:

- add to `requirements.txt`
- update this doc
- update [Local Setup](/docs/?scope=studio&doc=local-setup) or [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments) when bootstrap or verification guidance changes materially

For external command-line tools:

- document whether they are baseline or workflow-specific
- avoid implying they are required in cloud or local setups unless the workflow truly depends on them

## Benefits

- makes `requirements.txt` and the static-site validation stack easier to reason about
- clarifies which dependencies are baseline versus workflow-specific
- reduces ambiguity when cloud sessions install the same dependency set as local work

## Risks

- this registry can drift if new dependencies are added without updating docs
- feature-specific dependencies can start looking “optional” even after they are intentionally pinned into baseline installs
- cloud bootstrap can still become heavier over time if too many one-off features land in the main dependency files

## Related References

- [Site Docs](/docs/?scope=studio&doc=dev-home)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
