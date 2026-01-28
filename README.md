# dotlineform.com (Jekyll site)

This repository is the source for the dotlineform website, built with Jekyll and deployed via GitHub Pages (deploy from `main` / root). The site is served on the custom domain `www.dotlineform.com`.

Primary goals:
- Publish a browsable catalogue of works (stable work IDs, consistent URLs).
- Keep media handling predictable (primaries, thumbnails, attachments).
- Keep catalogue metadata reproducible (generated from a canonical spreadsheet where appropriate).

## Repo structure

- `_works/`  
  Work records (one Markdown file per work ID). Front matter is the canonical metadata for each work page.

- `assets/works/`  
  Site media. Conventionally split by purpose (e.g., images vs files).

- `_layouts/`, `_includes/`, `assets/`  
  Jekyll layouts, includes, and styling.

- `scripts/`  
  Local helper scripts to generate/update catalogue content and derived images.

## Local development

Requirements:
- Ruby + Bundler (standard Jekyll toolchain)

Install dependencies:

```bash
bundle install
```

Run the site locally:

```bash
bundle exec jekyll serve
```

Then open:
- http://127.0.0.1:4000

## Catalogue model for works

Works are identified by a stable ID (e.g. `00361`). The site expects:
- a work record in `_works/<id>.md`
- associated images in the expected `assets/` location (including generated thumbnails)

## Key scripts (purpose and usage)

The scripts below are intended to be run locally from the repo root. They are designed to keep the catalogue consistent and reduce manual work.

### 1) Generate/update `_works` from the canonical spreadsheet

- From the canonical “works” spreadsheet generate `_works/<id>.md`.
- Normalise/coerce fields (types, blanks, formatting) into a stable front matter schema.
- Avoid unnecessary rewrites by computing a deterministic checksum of each work record and skipping unchanged works.
- `scripts/scripts/generate_work_pages.py`

Typical behaviour:
- DRY-RUN mode (show what would change without writing)
- SKIP unchanged works when checksum matches
- WRITE only when a work is new or its checksum differs

### 2) Generate images for works pages

- Create small, fast thumbnails for indexes and grids, larger images for work display
- Uses `ffmpeg` for WebP encoding and scaling/cropping.
- `scripts/make_work_images.sh`

## Working on this repo

Suggested workflow:

1) Update canonical metadata (spreadsheet)
2) Run the works generator script (dry-run first)
3) Generate thumbnails/derived images
4) Test site locally
5) Commit and push
