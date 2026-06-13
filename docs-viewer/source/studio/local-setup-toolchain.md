---
doc_id: local-setup-toolchain
title: Local Setup Toolchain
added_date: 2026-05-19
last_updated: 2026-06-13
parent_id: local-setup
---
# Local Setup Toolchain

## Current repo/runtime summary

Current baseline runtime:

- Python: `3.12.7`
- Python packages: install from `requirements.txt`

Current external tools used by media workflows:

- macOS `sips`
- `ffmpeg`
- `heif-convert` from `libheif`

Public preview serves the tracked `site/` root, and deploy validation runs through `site-tools/`.

Use [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies) as the dependency-role reference.

## Fresh macOS install

Recommended order on a fresh macOS 24 system:

1. Install Apple command line tools if they are not already present:

```bash
xcode-select --install
```

2. Install non-Python command-line dependencies with Homebrew:

```bash
brew install ffmpeg libheif
brew install --cask miniconda
```

3. Initialize Conda for your shell, then open a new shell:

```bash
conda init zsh
```

If you use `bash` instead of the default macOS `zsh`, run:

```bash
conda init bash
```

4. Create and activate a dedicated Python environment:

```bash
conda create -n dotlineform python=3.12.7
conda activate dotlineform
```

5. Install checked-in Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Version checks

Check that the active Python is the expected one:

```bash
which python3
python3 -V
python3 -m pip check
```

Expected current value:

- `python3 -V` -> `Python 3.12.7`

Check the media tools:

```bash
ffmpeg -version | head -n 1
heif-convert --version
sips --help | head -n 1
```

Check the public static site validator:

```bash
bin/site-validate
```

## Switching to the correct Python

Activate the repo environment:

```bash
conda activate dotlineform
```

See available Conda environments:

```bash
conda info --envs
```

If `python3` still points somewhere unexpected, check:

```bash
which python3
python3 -V
```

Codex runs should prefer the pinned local interpreter path:

```bash
$HOME/miniconda3/bin/python3
```
