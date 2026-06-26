---
doc_id: python
title: "python"
added_date: 2026-06-26
last_updated: 2026-06-26
---

Python `3.12.7` is fine for this repo unless you have a specific dependency/security reason to move.

I’d avoid casually upgrading the base Miniconda Python because this repo appears to rely on that interpreter path:

```text
/Users/dlf/miniconda3/bin/python3
```

A Python upgrade can change package ABI compatibility and break installed tools like Playwright, Pillow, pytest plugins, etc.

Practical approach:

```bash
/Users/dlf/miniconda3/bin/python3 --version
/Users/dlf/miniconda3/bin/python3 -m pip list --outdated
```

If everything works, leave it. If you want newer Python, create a separate env first:

```bash
conda create -n dlf-py312 python=3.12
# or later:
conda create -n dlf-py313 python=3.13
```

Then test the repo against that env before changing the default `/Users/dlf/miniconda3/bin/python3`.

For this project, stability is worth more than being on the newest patch release.

~

I would not bulk-upgrade that environment with `pip install -U ...`.

This looks like your **base Miniconda environment**, and several outdated packages are Conda’s own plumbing:

```text
conda-package-handling
conda_package_streaming
truststore
archspec
boltons
ruamel.yaml
zstandard
```

Updating those with `pip` can put Conda into a mixed/fragile state.

Best approach:

```bash
conda update -n base conda
conda update -n base --all
```

Then only use `pip` for packages that are intentionally pip-managed in that env.

If you want a low-risk maintenance pass, I’d do:

```bash
conda update -n base conda certifi openssl requests urllib3 cryptography
```
[ran that, updated ok]

For repo tooling like `pytest`, `playwright`, `pillow`, `beautifulsoup4`, `lxml`, I’d leave them unless you need a fix. They are recent enough.

One special note: if you upgrade Playwright, you may also need:

```bash
/Users/dlf/miniconda3/bin/python3 -m playwright install
```

So I would not touch Playwright casually unless browser checks start failing or you specifically want the newer browser bundle.