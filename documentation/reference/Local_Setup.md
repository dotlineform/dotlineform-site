---
draft: false
doc_id: d-20260413-000000-d314b7
title: Local Setup
added_date: 2026-04-13 00:00:00
last_updated: "2026-11-19"
parent_id: ""

---

# Local Setup

Run commands from the repository root. Studio and Docs Viewer use the applicable existing external workspaces. Public preview serves the tracked site and its configured media URLs. [Local runners and addresses](Local_Runners.md#default-boundaries)

## Toolchain

Local runners prefer `$HOME/miniconda3/bin/python3` when present. Install [`requirements.txt`](../../requirements.txt) into the interpreter the runner actually uses. Activating another Conda environment leaves that runner preference in place. The lint toolchain has its own Python environment and Node lockfile. [Dependency owners and installation](../development/Runtime_Dependencies.md)

For a fresh macOS setup, install the command-line developer tools and Miniconda, then install the checked Python requirements with the selected interpreter.

```bash
"$HOME/miniconda3/bin/python3" -m pip install -r requirements.txt
```

For interpreter or import failures, check that specific environment before changing packages.

```bash
"$HOME/miniconda3/bin/python3" -V
"$HOME/miniconda3/bin/python3" -m pip check
```

Media workflows can additionally need `ffmpeg`, `heif-convert` or macOS `sips`. Check those commands when the failed operation invokes them. Repository lint uses `npm ci --prefix tooling/lint` and the dedicated Ruff environment described by the dependency owner. [Cloud and Codespaces setup](../_working/Cloud_Environments.md)

## Environment

Keep machine-specific roots, runner flags and credentials in gitignored `.env.local`. Use platform environment variables and secret stores in cloud sessions. `DOTLINEFORM_DOCS_BASE_DIR` points to the existing Docs workspace. `DOTLINEFORM_PROJECTS_BASE_DIR` independently points to the existing Projects workspace. Root availability and read/write access belong to the operation that uses them. [Storage roles](Source_Organisation.md#storage-and-roles)

Under the Projects root, the site uses `dotlineform-site/catalogue/media-staging/`, `dotlineform-site/data-sharing/` and `dotlineform-site/docs-export/`. Studio looks for original media under the Projects root's separate `projects/` and `processing/` directories. Select files from the Library inbox with the native picker for single-file imports. [Catalogue media configuration](Catalogue_Media_Pipeline_Config.md) · [Docs Import](Docs_Import.md)

The shell runners for Studio, public preview and `local-all` source `.env.local` and export it to their children. At startup, the Docs service fills missing process variables from `.env.local` for its workspace, binding and capability settings. To start Docs Viewer on its own, run its launcher from the repository root.

```bash
docs-viewer/bin/docs-viewer
```

The Docs service uses explicit `--host`, `--port` and `--base-url` flags for their respective settings, then inherited process values, then `.env.local`. Builder bootstrap overlays the local file on inherited settings, then applies supported explicit workspace arguments. Keep shared settings consistent across these entrypoints. Local file values are simple bindings, and secrets stay server-side. [Service configuration](../../docs-viewer/services/docs_viewer_service.py) · [Builder bootstrap](../../docs-viewer/build/docs_builder/runtime_bootstrap.py)

Set `DOCS_VIEWER_MANAGEMENT_ENABLED=1` for Manage authoring and `DOCS_VIEWER_REVIEW_ENABLED=1` for Review. Their checked defaults are false. Generated reads default true through `DOCS_VIEWER_GENERATED_READS_ENABLED`. `local-all` defaults Review on. Restart after changing process settings. [Runner overrides](Local_Runners.md#configuration)

## Restore The Docs Workspace

**Publish** transfers queued public changes and then pushes both Git backups. The backups also run when the queues are empty. Review the site with `bin/site-preview` before running **Deploy Public** manually. [Publish and deploy](../guide/Publish_And_Deploy.md)

| Recovery source | What it supplies |
| --- | --- |
| Private `docs-viewer-data` repo | Saved Docs source, including drafts, document media, and all three Working queues. |
| `dotlineform-site` repo | The five canonical Studio Catalogue JSON files and the exact published Docs, Catalogue and Search data in `site/`, including Work thumbnails. |
| R2 | Published document media and Work srcsets and downloads. Matching published files can supply missing Working copies. |
| Time Machine | The rest of the local workspace, including Work assets, generated output, Preview, and the kept-downloaded Projects tree with originals and Catalogue staging. |

For a Git-based restore, clone `dotlineform-site` and the private `dotlineform/docs-viewer-data` repository into separate folders. In the site checkout's `.env.local`, set `DOTLINEFORM_DOCS_BASE_DIR` to the absolute path of the data checkout itself. [Data repository](https://github.com/dotlineform/docs-viewer-data) · [Source version history](Source_Organisation.md#source-version-history)

For a full workspace restore, use the same Time Machine recovery point for Docs and Projects. Include the saved source, document media, `working/assets/works/`, `working/generated/`, `preview/`, the Working queues, and Catalogue media staging under Projects. Keep the iCloud Drive Projects tree downloaded on the laptop so the backup has the local files.

The last pushed commit in the private data repository supplies fallback copies of `working/catalogue-updates-pending.json`, `working/catalogue-publish-pending.json` and `working/docs-publish-pending.json`. If a queue and the restored workspace come from different recovery points, check its selected writes against the restored prepared output and staged or Working media. Check removals against the intended source and current published state. Recover missing inputs, rerun the owning preparation for changes still needed, and reconcile stale selections before resuming Refresh, Regenerate or Publish.

Use Full Working Build when the restored document, Search, and Recent output needs refreshing. It requires ready media, the prepared public membership and the Docs publication queue, and can regenerate a missing ordinary management tree. Catalogue Work output has its own Refresh and Regenerate workflow. [Full Working Build](Builder.md#working-rebuild) · [Catalogue workflow and media destinations](Catalogue_Save_And_Refresh.md#storage-and-selection)

## Service Health And Capabilities

With the owner running, inspect its endpoint at the configured address. These default-address commands are read-only.

```bash
curl -fsS http://127.0.0.1:8765/health
curl -fsS http://127.0.0.1:8776/health
curl -fsS http://127.0.0.1:8776/capabilities
```

Studio health identifies the process as `studio`. Docs health returns `ok`, `service: docs_viewer` and process-level management, generated-read and Review flags. Its capabilities response additionally reports Working availability, generated document/Search presence, package/staging access and Publish destination availability. A healthy process can still lack an operation's inputs. Review uses its separate package capability surface. [Capability producer](../../docs-viewer/services/docs_management_capabilities_service.py) · [Review endpoints](Docs_Review.md#api-surface)

## Public Preview And Projection

`bin/site-preview` validates `site/` and serves it at `http://127.0.0.1:4000/`. Use `--port 4010` for another preview port, or `--site-root <path>` for an explicitly selected root. `bin/site-validate` runs validation and exits. `--no-validate` skips preview's startup validation when deliberately inspecting incomplete output.

Shared/public Docs code and styles are maintained under `docs-viewer/` and copied through `bin/site-code-update`. Public-only HTML and route records belong under `site/`. After a relevant change, inspect its tracked projection, run `bin/site-code-update --check` and `bin/site-validate`, then reload the browser. A running preview serves changed files directly. Public release requires the separate committed Pages workflow. [Configuration projection](Configuration_And_Extension_Points.md#builder-and-local-service-integration) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Recover The Failed Owner

| Symptom | Check and recovery |
| --- | --- |
| Runner cannot bind or integrated startup stops | Read the named child and error. Stop an owned conflicting instance or choose a free configured port. Keep Studio's Docs link base, Docs' own binding/base URL and preview cross-links aligned. Start only the needed runners while isolating a failure. [Supervision](Local_Runners.md#all-services-runner). |
| Docs says the workspace is unavailable | Check `DOTLINEFORM_DOCS_BASE_DIR` in the launch environment and `.env.local`, then check the selected root, mount and permissions. Restore the intended existing storage and restart. |
| Manage controls or a local operation are unavailable | Check health flags, capabilities, the served route registry and the exact action restriction. Enable the intended process flag, restore the required input or use the owning action, then restart/reload as needed. [Availability trace](Configuration_And_Extension_Points.md#how-a-workflow-becomes-available). |
| Browser requests the wrong collection, default or media destination | Correct the owning workspace or route record and repeat its projection. Inspect both canonical browser files and the public site copy. A missing public default is diagnosed by `bin/site-validate`. [Default walkthrough](../guide/Change_The_System_Safely.md). |
| Correct local code still looks old in Public | Check the canonical/public projection and browser cache, reload, and check the deployed revision when testing production. [Public projection](Runtime_Module_Ownership.md#public-deployment-projection). |
| An authoring or publication operation failed after writing | Read its phase and completed effects. Fix the owning source, build or transfer, then use exact Rebuild, Publish or a fresh display as appropriate. Preserve the prior media comparison when removal handoff needs recovery. [Source phases](Source_Editing.md#if-save-stops) · [Publish recovery](Builder.md#preview-and-deployment-boundary). |
| Tools disappear after macOS or Xcode updates | Inspect `command -v python3`, `xcode-select -p` and the relevant tool's version. Restore the intended shell initialization or tool installation. Bash login sessions use `.bash_profile`, which can source `.bashrc`. Conda initialization belongs to the shell actually in use. Repeat the smallest failing command. |

Use read-only diagnostics first and choose a build or write operation for the failed owner. Test execution and changes follow the maintained verification policy. [Testing](../development/Verification.md) · [Completed code follow-ups](../deliveries/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)
