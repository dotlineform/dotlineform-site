---
doc_id: github-notes
title: "github notes"
added_date: 2026-06-02
last_updated: 2026-06-12
ui_status: draft
---

Next is the actual cutover. The two live-setting changes are:
```
gh variable set PUBLIC_SITE_PAGES_DEPLOY_ENABLED --body true
gh api --method PUT repos/dotlineform/dotlineform-site/pages -f build_type=workflow
```
Then trigger the deploy:
```
gh workflow run "Public site" --ref main
```

```
brew install actionlint
✔︎ JSON API packages.arm64_tahoe.jws.json                                                                                                                 Downloaded   15.2MB/ 15.2MB
==> Would install 1 formula:
actionlint
==> Downloading https://ghcr.io/v2/homebrew/core/actionlint/manifests/1.7.12-1
####### 100.0%
==> Would install 2 dependencies for actionlint:
gmp
shellcheck
==> Do you want to proceed with the installation? [y/n]
==> Fetching downloads for: actionlint
✔︎ Bottle Manifest gmp (6.3.0)                                                                                                                            Downloaded   13.3KB/ 13.3KB
✔︎ Bottle Manifest shellcheck (0.11.0)                                                                                                                    Downloaded   11.0KB/ 11.0KB
✔︎ Bottle gmp (6.3.0)                                                                                                                                     Downloaded    1.0MB/  1.0MB
✔︎ Bottle actionlint (1.7.12)                                                                                                                             Downloaded    2.1MB/  2.1MB
✔︎ Bottle shellcheck (0.11.0)                                                                                                                             Downloaded   14.1MB/ 14.1MB
==> Installing dependencies for actionlint: gmp and shellcheck
==> Installing actionlint dependency: gmp
==> Pouring gmp--6.3.0.arm64_tahoe.bottle.tar.gz
🍺  /opt/homebrew/Cellar/gmp/6.3.0: 22 files, 3.4MB
==> Installing actionlint dependency: shellcheck
==> Pouring shellcheck--0.11.0.arm64_tahoe.bottle.tar.gz
🍺  /opt/homebrew/Cellar/shellcheck/0.11.0: 8 files, 68.4MB
==> Installing actionlint
==> Pouring actionlint--1.7.12.arm64_tahoe.bottle.1.tar.gz
🍺  /opt/homebrew/Cellar/actionlint/1.7.12: 8 files, 6.0MB
==> Running `brew cleanup actionlint`...
Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
```

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