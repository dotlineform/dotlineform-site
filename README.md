# dotlineform.com (Jekyll site)

This repository is the source for the dotlineform website, built with Jekyll and deployed via GitHub Pages. The site is served on the custom domain `www.dotlineform.com`.

Primary goals:
- Publish a browsable catalogue of works
- Keep catalogue metadata reproducible (generated from a canonical spreadsheet).

## Local development

Run the site locally:

```bash
bundle exec jekyll serve
```

Then open:
- http://127.0.0.1:4000

## Catalogue model for works

Works are identified by a stable ID (e.g. `00361`). The site expects as a minimum:
- a work record in `_works/<id>.md`
- associated media files in the expected `assets/` location (including generated thumbnails)
- primary images stored remotely (Cloudflare R2)

## Scripts

Scripts are run locally from the repo root. They are designed to keep the catalogue consistent and reduce manual work. See [`_docs_src/scripts-overview.md`](_docs_src/scripts-overview.md) for details.

For a centralized local install/setup guide covering Python, Ruby, external tools, env vars, and version checks, see [`_docs_src/local-setup.md`](_docs_src/local-setup.md).

Before running media/generation scripts, set local environment variables:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="/path/to/dotlineform-icloud"
```

Shared pipeline defaults live in `_data/pipeline.json`. That file stores env var names and relative media subpaths, while absolute local paths stay in your shell environment.

Quick audit command:

```bash
./scripts/audit_site_consistency.py --strict
```

Sorting architecture and consistency contract are documented in [`_docs_src/sorting-architecture.md`](_docs_src/sorting-architecture.md)

Deferred improvements and follow-up tasks are tracked in [`_docs_src/backlog.md`](_docs_src/backlog.md)

Site-shell layout/runtime decisions are documented in [`_docs_src/site-shell-runtime.md`](_docs_src/site-shell-runtime.md).

## Working on this repo

Basic workflow:

1) Update canonical metadata (spreadsheet)
2) Run the pipeline script (dry-run first)
3) Copy media assets to local and remote folders as appropriate
4) Test site locally
5) Commit and push
