---
doc_id: devcontainer
title: "devcontainer"
added_date: 2026-06-28
last_updated: 2026-06-28
---

Run these locally from any terminal:

```bash
docker --version
docker info
devcontainer --version
```

Interpretation:

- `docker --version` works: Docker CLI is installed.
- `docker info` works: Docker daemon/Desktop is running and usable.
- `devcontainer --version` works: Dev Containers CLI is installed.

If `devcontainer` is missing, install it with:

```bash
npm install -g @devcontainers/cli
```

Then from `dotlineform-site/` you can test the image with:

```bash
devcontainer build --workspace-folder .
```

If you only care about Codespaces itself, the practical test is simpler: open the repo in Codespaces and choose **Rebuild Container**.

For this repo, the benefits are modest but real.

Docker + Dev Containers locally would let you:

- Test `.devcontainer/Dockerfile` before pushing or opening Codespaces.
- Reproduce the Codespaces Linux environment on your Mac.
- Catch apt/package/runtime issues earlier, especially after changing `.devcontainer/` or `.codex/setup.sh`.
- Run a clean bootstrap without relying on your local Miniconda/macOS setup.
- Validate “cloud will probably work” before starting a Codex Cloud or Codespaces session.

The tradeoffs:

- Docker Desktop is fairly heavy.
- It uses disk space and memory.
- It adds another environment to maintain.
- For this repo, you probably would not use it often unless you expect more Codespaces/Codex Cloud work.

My pragmatic view: don’t install it just for occasional use. If you are about to rely on Codespaces repeatedly, Docker + Dev Containers becomes useful as a local preflight tool. Otherwise, just let Codespaces rebuild the container when needed and fix any setup issue there.