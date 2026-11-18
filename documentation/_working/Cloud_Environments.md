---
draft: false
doc_id: d-20260414-000000-f22e3e
title: Cloud Environments
added_date: "2026-04-14 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20261118-235100-64ad2e
ui_status: proposed
---
# Cloud Environments

## Status And Next Decision

The [27 October handoff](<2026-10-27 - dotlineform-environment-handoff.md>) records the Codex Cloud setup attempt from iPad without access to Codex desktop. Current environment state still needs checking.

- **Verified in that session.** Static site validation passed. Public preview served the homepage, default document and public assets over HTTP, including after restart. The cloud checkout used the repository `.venv` because the local Miniconda interpreter path was absent in the image.
- **Setup blocker.** Dependency downloads were blocked by the running environment's disabled network policy. The UI rejected Save and Publish and showed locked Manage controls. The scripts and restricted network proposal were recoverable in a saved draft, but the running instance still used the old policy. Correcting the imported mount path did not resolve the rejection. Its cause and effective permissions were unconfirmed.
- **Repository follow-ups.** The handoff proposed aligning the lint package, lockfile and CI with the Node 24 image and documenting the cloud `.venv` interpreter alongside local Miniconda. The checked lint declarations still specify Node 22. Scope these separately from the environment settings issue.
- **Unverified.** Full dependency installation, lint, activation in a fresh cloud task and authoring with real Docs and Projects storage.

- [x] Recover the ChatGPT handoff and identify the open setup, access and dependency issues.
- [ ] Check the saved draft and effective access in the intended account/workspace, and confirm whether settings can be applied before retrying installation. Agree the supported cloud work, storage, interpreter, network and secret configuration against the current repository owners.
- [ ] Propose the smallest setup changes and explicit validation/write scope; keep Codespaces, local Miniconda, native App and Processing lifecycles distinct.
- [ ] Implement and record observed environment evidence only after the setup scope is agreed. Compile stable operating instructions into the appropriate Reference/Development owner.

## Repository Baseline To Review

The checked owners are [setup.sh](../../.codex/setup.sh), [devcontainer](../../.devcontainer/devcontainer.json), [container image](../../.devcontainer/Dockerfile), [requirements](../../requirements.txt), feature/tool manifests and actual platform settings. Exact flags/packages come from those files. Current source includes the repository lint environments in bootstrap.

The earlier bootstrap path created/reused `.venv`, installed pinned Python dependencies and optionally persisted PATH/`SITE_PYTHON`/`PYTHON_BIN` in shell setup. Its operator flags include `SETUP_SKIP_APT`, `FORCE_APT_PACKAGES`, `SETUP_INSTALL_MEDIA_PACKAGES` and `SETUP_PERSIST_AGENT_ENV`. Review shell persistence, checkout-path stability and cached environments for the new runtime. Bootstrap does not itself generate, Publish or deploy content.

Codespaces uses its own image and post-create configuration, selecting the repository virtualenv. Its current container defaults do not establish Codex Cloud storage availability. The checked container still names `DOTLINEFORM_MEDIA_BASE_DIR` and has no `DOTLINEFORM_DOCS_BASE_DIR` entry; trace actual consumers/platform overrides before deciding changes.

## Storage, Tools And Effects

`DOTLINEFORM_DOCS_BASE_DIR` selects an existing Docs workspace. `DOTLINEFORM_PROJECTS_BASE_DIR` independently selects project/media and package inputs. Dependency installation cannot manufacture private content or establish these owners. Platform environment/secrets supply cloud values; `.env.local` remains local-machine configuration. Keep R2 credentials out of tracked files and logs. [Storage and startup](../reference/Local_Setup.md) · [Dependency classes](../development/Runtime_Dependencies.md)

Separate normal code/document work from media work and authorised publication. Media operations need their actual tools and source roots; site validation and runtime code projection do not need media processing. Dependency-download access, agent web access and application network/storage permissions are different requirements. Use only the access required by the agreed task.

Review Python and system-library differences, private workspace availability and any absolute path persisted by bootstrap. Use focused installation and import diagnostics for setup. Agree focused test work separately if a specific failure warrants it. [Verification](../development/Verification.md) · [Test Contract Discipline](../development/Test_Contract_Discipline.md)

## Evidence To Agree

Use focused Python/dependency/import diagnostics and repository static validation for the supported work. Name their purpose, costs, cache/file/network effects and any unavailable real workspace. Generator writes, media processing, service/browser startup and publication need their own agreed operational scope. Use dry-run generators in cloud unless a write run was explicitly requested.
