---
doc_id: runtime-dependencies
title: "Runtime Dependencies"
added_date: 2026-04-23
last_updated: 2026-04-23
parent_id: site-docs
sort_order: 20
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
- Ruby/Jekyll packages:
  - `Gemfile`
  - `Gemfile.lock`
- Ruby runtime:
  - `.ruby-version`
- system tools and cloud bootstrap expectations:
  - `.codex/setup.sh`
  - `.devcontainer/` files when present
- machine setup guidance:
  - [Local Setup](/docs/?scope=studio&doc=local-setup)
  - [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)

## Dependency Categories

The repo currently has four practical dependency layers:

1. Python packages from `requirements.txt`
2. Ruby/Jekyll packages from the GitHub Pages stack
3. external command-line tools used by media/generation workflows
4. local or cloud runtime bootstrap scripts that install or verify the above

## Python Packages

Current checked-in Python packages:

| Package | Source | Used for in this repo | Local critical | Cloud critical | Notes |
| --- | --- | --- | --- | --- | --- |
| `openpyxl` | PyPI via `requirements.txt` | workbook and spreadsheet reads/writes in the Python pipeline | yes | yes when spreadsheet-driven scripts are used | baseline Python package for existing data flows |
| `beautifulsoup4` | PyPI via `requirements.txt` | HTML parsing for Docs HTML import | feature-specific | feature-specific | required for the HTML import feature once that importer is in use |
| `lxml` | PyPI via `requirements.txt` | parser backend for the Docs HTML import tree build | feature-specific | feature-specific | treated as part of the pinned HTML import parser stack |
| `bleach` | PyPI via `requirements.txt` | HTML sanitization for Docs HTML import | feature-specific | feature-specific | required for the intended import sanitization boundary even if the first scaffold uses only a subset of that behavior |

Current interpretation:

- `openpyxl` is the only current baseline Python package for the established catalogue/workbook pipeline
- `beautifulsoup4`, `lxml`, and `bleach` are now checked-in because the HTML import feature is intended to build against a fixed parser/sanitizer stack from the start
- in cloud environments that never touch the HTML import flow, those three import packages are less critical operationally than `openpyxl`, but they are still part of the checked-in repo dependency set and should normally be installed for parity

## Ruby And Jekyll Stack

The site build/runtime side is governed by the GitHub Pages Jekyll stack rather than ad hoc Ruby gems.

Current checked-in sources:

- `Gemfile`
- `Gemfile.lock`
- `.ruby-version`

Current repo role:

- build the site locally with Jekyll
- render docs Markdown through the same Jekyll Markdown converter used by the docs builder
- keep publish-sensitive checks aligned with the GitHub Pages-compatible stack

Current practical dependency boundary:

- `github-pages` is the top-level Ruby gem contract
- Jekyll and related gems come through that stack
- the docs builder and site verification should therefore be treated as depending on the repo's pinned Ruby/Bundler/Jekyll contract, not just on “some Ruby”

Local/cloud criticality:

- local: critical for any Jekyll build, docs rendering, or publish-sensitive verification
- cloud: critical in parity mode and for final verification; less critical for Python-only script work that does not touch site rendering

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
- `Gemfile` / `Gemfile.lock`
- `.ruby-version`

These are the main checked-in contracts that keep local and cloud runs aligned.

### Usually needed in both local and cloud

- `openpyxl`
- the pinned Ruby/Bundler/Jekyll stack when site/docs rendering matters

### Feature-specific but now part of the repo baseline install

- `beautifulsoup4`
- `lxml`
- `bleach`

Reason:

- even though they are currently tied to the HTML import feature, they are now intentionally checked into `requirements.txt`
- Codespaces and Codex Cloud should therefore install them normally rather than treating them as purely ad hoc local extras

### Optional unless the workflow needs them

- `ffmpeg`
- `heif-convert`
- other media-tooling system packages

These matter only for workflows that actually generate or transform media.

## Codespaces And Codex Cloud Expectations

Current expectation:

- `requirements.txt` should normally be installed in cloud environments
- that means the HTML import parser/sanitizer stack is now part of the standard Python environment for cloud sessions
- this is useful because it avoids a split where local development uses one parser boundary and cloud sessions silently use another

Current practical split:

- critical for cloud parity:
  - Python packages in `requirements.txt`
  - pinned Ruby/Bundler/Jekyll contract when running parity checks
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

For Ruby/Jekyll changes:

- keep `Gemfile.lock` and `.ruby-version` in sync with the intended parity contract
- update this doc and the relevant setup/runtime docs

For external command-line tools:

- document whether they are baseline or workflow-specific
- avoid implying they are required in cloud or local setups unless the workflow truly depends on them

## Benefits

- makes `requirements.txt` and the Jekyll stack easier to reason about
- clarifies which dependencies are baseline versus workflow-specific
- reduces ambiguity when cloud sessions install the same dependency set as local work

## Risks

- this registry can drift if new dependencies are added without updating docs
- feature-specific dependencies can start looking “optional” even after they are intentionally pinned into baseline installs
- cloud bootstrap can still become heavier over time if too many one-off features land in the main dependency files

## Related References

- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs HTML Import Spec](/docs/?scope=studio&doc=ui-request-docs-html-import-spec)
- [Docs HTML Import Task](/docs/?scope=studio&doc=ui-request-docs-html-import-task)
