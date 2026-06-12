---
doc_id: github-notes
title: "github notes"
added_date: 2026-06-02
last_updated: 2026-06-12
ui_status: draft
---

> when we upload the generated site, are we uploading the whole thing or just deltas?

Whole thing uploaded

GitHub Pages artifact deploy uploads a complete generated static site artifact each run, not a delta. The workflow should build `_public_site/`, verify it, then upload that directory as the Pages artifact. GitHub Pages deploys that artifact as the current site.

So the builder must produce a complete deployable tree every time, including:

- HTML route files
- `.nojekyll`
- `CNAME`
- favicon / manifest files
- CSS/JS/assets
- generated public data
- public Docs Viewer payloads/runtime files
- `404.html`

This is also why copy allowlists and source-leak checks matter: anything in `_public_site/` is what gets deployed.

it uploads the whole generated site artifact each deploy.

It does not go through a tracked staging branch/folder. The process is:

```text
build _public_site/
verify _public_site/
upload _public_site/ as a Pages artifact
deploy that artifact to GitHub Pages
```

There is a kind of staging inside GitHub Actions: the generated artifact exists before deploy, and the deploy job can be gated by checks or a GitHub `environment` approval. But it is not a persistent staging site and not a delta upload.

If upload size becomes a problem, the right mitigations are:

- keep `_public_site/` allowlisted and minimal
- avoid copying local/source/test/log paths
- keep large media optimized
- consider external object storage/CDN for very large media later
- use PR build/verify to catch issues before `main` deploys

But the Pages artifact itself should be complete every time.

107 MB is not scary for Pages artifact deploy.

Current GitHub docs say custom Pages workflow artifacts must be under 10 GB, and the upload action notes GitHub Pages’ officially supported practical maximum is 1 GB. So 107 MB is comfortably inside that. Sources: [GitHub custom workflows](https://docs.github.com/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [upload-pages-artifact](https://github.com/marketplace/actions/upload-github-pages-artifact).

The more relevant check is what makes up the 107 MB:

- If it is mostly optimized public media that really belongs on the site, fine.
- If it includes `_site` leftovers, source files, Studio/docs management payloads, logs, or duplicated generated data, the new builder should not copy those.
- The `_public_site/` builder should report artifact size and largest file/folder contributors as part of the verification gate.

I’d add a task/check: after building `_public_site/`, print total size plus top 20 largest paths, and fail only if size crosses a chosen warning threshold, maybe `250 MB` initially.

> it's mostly index.html files for the thousands of works and work details

That should drop substantially with the new route model.

Those thousands of `index.html` files are Jekyll collection output for old per-record routes like:

- `/works/<work_id>/index.html`
- `/series/<series_id>/index.html`
- `/work_details/<detail_uid>/index.html`

The new static builder should not generate those. It should generate fixed shells:

- `/works/index.html`
- `/series/index.html`
- `/work-details/index.html`

Then record state is restored through query parameters and public JSON payloads:

- `/works/?work=00001`
- `/series/?series=009`
- `/work-details/?detail=00001-001`

So `_public_site/` should be much smaller than `_site/` if the builder follows the simplified route contract. Individual moment pages still remain, but that is a small route family compared with works and details.

The artifact-size task is useful here: it will prove that `_works/`, `_series/`, and `_work_details/` style route explosion is gone before deploy.

> yes the rest of the site is about 10MB

That’s a good sign. The static artifact target should be closer to that ~10 MB baseline plus:

- fixed shell HTML pages
- individual moment pages
- public JSON payloads
- public Docs Viewer `/library/` and `/analysis/` payloads/runtime
- current public assets/media that still need publishing

The task tracker already has the right guard now: artifact size report plus largest contributors. For this migration, the important expected result is not just “under 250 MB,” but “no thousands of generated work/detail/series HTML pages.” That should be part of the build surface audit.