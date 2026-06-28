---
doc_id: scripts-cloud-environments
title: Cloud Environments
added_date: 2026-04-14
last_updated: "2026-06-28"
parent_id: dev-home
---
# Cloud Environments

This guide records the current cloud-hosted setup for this repo across Codex Cloud and GitHub Codespaces.

It should stay aligned with:

- `.codex/setup.sh`
- `.devcontainer/`
- `requirements.txt`
- `AGENTS.md`
- [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)

## Current Repo Contract

The repo is currently Python-first for cloud bootstrap.

Baseline checked-in dependencies:

- Python packages: `requirements.txt`
- local static-site validation config: `site-tools/config/site-tools.json`
- cloud bootstrap script: `.codex/setup.sh`
- Codespaces container config: `.devcontainer/`

The cloud bootstrap path is intentionally Python-only.

## Codex Cloud Behavior

Current Codex Cloud environment behavior:

- Codex checks out the selected repo branch or commit in a hosted container.
- The configured setup script runs before the agent phase.
- Setup scripts run with internet access so dependencies can be installed.
- Agent internet access is off by default unless enabled in the Codex environment settings.
- Environment variables are available during setup and the agent phase.
- Secrets are available only during setup and are removed before the agent phase.
- The setup script runs in a separate shell from the agent phase, so plain `export` commands inside setup do not persist unless written to shell startup files or configured as environment variables.
- Hosted containers may be cached; reset the environment cache when setup, dependency, or runtime assumptions change.

Configure Codex environments in Codex settings. Use `.codex/setup.sh` as the setup script:

```bash
bash .codex/setup.sh
```

No Codex-specific maintenance script is currently defined in this repo.

## Setup Script Contract

`.codex/setup.sh` is the shared bootstrap entrypoint for Codex Cloud and Codespaces post-create setup.

Current behavior:

- runs from the repo root
- optionally installs baseline apt packages when `apt-get` and non-interactive privilege are available
- creates or reuses `.venv`
- upgrades pip only when creating a new virtualenv
- installs `requirements.txt` into `.venv`
- persists `.venv/bin` plus `SITE_PYTHON` and `PYTHON_BIN` into `~/.bashrc` for later cloud agent shells
- prints version diagnostics for Python, venv Python, and optional `ffmpeg`
- does not run docs builders, search builders, catalogue builders, site validation, or test profiles

Setup flags:

| Flag | Effect |
| --- | --- |
| `SETUP_SKIP_APT=1` | Skip apt installation entirely. Useful when the image already has system packages. |
| `FORCE_APT_PACKAGES=1` | Run apt installation even when baseline commands are already present. |
| `SETUP_INSTALL_MEDIA_PACKAGES=1` | Include optional media tools: `ffmpeg` and `libheif-examples`. |
| `SETUP_PERSIST_AGENT_ENV=0` | Do not append the `.venv` PATH block to `~/.bashrc`. |

Default Codex Cloud setup:

```bash
bash .codex/setup.sh
```

Fast setup when the cloud image already has system packages:

```bash
SETUP_SKIP_APT=1 bash .codex/setup.sh
```

Media-capable setup:

```bash
SETUP_INSTALL_MEDIA_PACKAGES=1 bash .codex/setup.sh
```

Use media-capable setup when a task needs source image conversion, HEIF/HEIC handling, thumbnail work, or srcset generation. The setup script treats `ffmpeg` and `heif-convert` as required commands when `SETUP_INSTALL_MEDIA_PACKAGES=1`, so it will not skip apt merely because the non-media baseline is already present.

## Codespaces Contract

Codespaces is configured through `.devcontainer/`.

Current files:

- `.devcontainer/devcontainer.json`
- `.devcontainer/Dockerfile`
- `.devcontainer/post-create.sh`

Current Codespaces behavior:

- builds from `mcr.microsoft.com/devcontainers/base:ubuntu-24.04`
- installs Python 3, `python3-venv`, `python3-pip`, build tooling, `gh`, `ffmpeg`, and `libheif-examples`
- sets VS Code's default Python interpreter to `/workspaces/dotlineform-site/.venv/bin/python`
- sets `DOTLINEFORM_PROJECTS_BASE_DIR=/workspaces`
- sets `MAKE_SRCSET_JOBS=4`
- runs `.devcontainer/post-create.sh`, which delegates to `bash .codex/setup.sh`

## Runtime Modes

### Fast script mode

Use this for docs, search, static validation, most Python service tests, and non-media maintenance:

```bash
SETUP_SKIP_APT=1 bash .codex/setup.sh
```

Then run checks with the venv interpreter:

```bash
.venv/bin/python admin-app/commands/run_checks.py --profile quick
```

### Media mode

Use this when source media conversion matters:

```bash
SETUP_INSTALL_MEDIA_PACKAGES=1 bash .codex/setup.sh
```

Codespaces normally has media tools already because the Dockerfile installs `ffmpeg` and `libheif-examples`.

### Publish-sensitive mode

Use the same setup as the relevant task, then run explicit validation. Setup alone is not a publish validation step.

Recommended starting checks:

```bash
.venv/bin/python -m pip check
.venv/bin/python admin-app/commands/run_checks.py --profile quick
SITE_PYTHON="$PWD/.venv/bin/python" bin/site-validate
```

Use broader check profiles only when the change warrants them.

## Environment Variables And Secrets

Minimum shared variables for media/generation and external Docs Viewer scopes:

- `DOTLINEFORM_PROJECTS_BASE_DIR`
- optional `MAKE_SRCSET_JOBS`

Codespaces currently sets:

```text
DOTLINEFORM_PROJECTS_BASE_DIR=/workspaces
MAKE_SRCSET_JOBS=4
```

For cloud environments that need source media or external Docs Viewer scopes, make sure the configured path exists and contains the expected child roots.

R2 publishing variables should be configured through platform secret stores:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

Do not commit `.env.local` or cloud credentials. `.env.local` is local-machine configuration only; cloud sessions should use configured environment variables and secret stores.

## Internet Access

Codex Cloud setup runs with internet access for dependency installation.

Agent-phase internet access should remain off unless a task genuinely needs it. If it is enabled, prefer a narrow allowlist and read-only HTTP methods where possible.

Typical dependency domains for this repo, when setup needs them:

- `pypi.org`
- `pythonhosted.org`
- `github.com`
- `githubusercontent.com`
- `packages.microsoft.com`
- `cli.github.com`

## Build And Verification Commands

Run commands from `dotlineform-site/`.

Use the venv interpreter in cloud sessions:

```bash
.venv/bin/python -m pip check
.venv/bin/python admin-app/commands/run_checks.py --list
.venv/bin/python admin-app/commands/run_checks.py --profile quick
```

Docs payload dry runs:

```bash
.venv/bin/python docs-viewer/build/build_docs.py --scope studio
.venv/bin/python docs-viewer/build/build_search.py --scope studio
```

Write runs should be explicit:

```bash
.venv/bin/python docs-viewer/build/build_docs.py --scope studio --write
.venv/bin/python docs-viewer/build/build_search.py --scope studio --write
```

Static-site validation:

```bash
SITE_PYTHON="$PWD/.venv/bin/python" bin/site-validate
```

Public preview in cloud/Codespaces is optional and only useful when port forwarding is available:

```bash
SITE_PYTHON="$PWD/.venv/bin/python" bin/site-preview --host 0.0.0.0
```

## Local And Cloud Parity Notes

Local AGENTS guidance prefers `$HOME/miniconda3/bin/python3` because that is the local machine interpreter convention.

Cloud sessions should use `.venv/bin/python` after `.codex/setup.sh` has run. The setup script also writes `.venv/bin` into `~/.bashrc` for later Codex agent shells, but explicit `.venv/bin/python` commands are still clearer in docs and closeout notes.

Keep generator runs dry-run by default in cloud sessions unless a write was requested.

## Current Risks

- Container caches can leave old dependencies in place after setup changes; reset the Codex environment cache when setup behavior changes.
- Media workflows still need real source media roots under `DOTLINEFORM_PROJECTS_BASE_DIR`; dependency setup cannot create those private assets.
- Agent internet access can expose the repo to prompt-injection risk if broad web access is enabled.
- Cloud and local Python patch versions may differ; run version/dependency checks before treating a failure as a repo regression.

## Related References

- [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Local Setup Environment](/docs/?scope=studio&doc=local-setup-environment)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2)
