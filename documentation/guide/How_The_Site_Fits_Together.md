# How the site fits together

Dotlineform is a public portfolio and reading site. Visitors browse documents, Works and Galleries through a read-only Docs Viewer. The author uses two local web apps to make changes. Studio maintains the Catalogue, and Docs Viewer Manage maintains the documents and publishes the prepared changes.

## Start a local surface

Run these commands from the repository root. For a first local setup, follow the toolchain and environment instructions. Public preview serves the repository files and can use the configured public media URLs. Studio and Manage need the applicable existing local workspaces described below. [Local setup](../reference/Local_Setup.md)

| Surface | What it does | Where to start |
| --- | --- | --- |
| **Public site** | GitHub Pages serves the tracked `site/` tree. The public reader loads prepared data from that tree and media from the configured destinations. | Run `bin/site-preview` and open `http://127.0.0.1:4000/`. [Read and browse](Find_And_Read_Things.md) |
| **Studio** | Edits canonical Works, Series, Galleries and memberships. **Refresh Catalogue** prepares the changed data and media for Working. | Run `bin/local-studio` and open `http://127.0.0.1:8765/studio/catalogue-work/`. [Maintain the Catalogue](Maintain_The_Catalogue.md) |
| **Docs Viewer Manage** | Edits and organises Working documents and media. Catalogue **Regenerate** updates Catalogue documents from Studio's refreshed inputs. **Publish** applies queued Docs and Catalogue changes. | Set `DOCS_VIEWER_MANAGEMENT_ENABLED=1` in `.env.local`, export that file for standalone startup, then run `docs-viewer/bin/docs-viewer` and open `http://127.0.0.1:8776/docs/`. [Startup environment](../reference/Local_Setup.md#environment) · [Author and organise documents](Author_And_Organise_Documents.md) |

The addresses use the default ports. Check the runner's startup message when a local override changes the address. Use `bin/local-all` when following a change across Studio, Manage and public preview. [Local runners](../reference/Local_Runners.md#choose-a-runner)

If a service fails to start or a control is unavailable, check the named process, its health flags and capabilities, then follow the requested route to its configured input. The startup reference covers port conflicts, unavailable storage, stale projections and partially completed operations. [Checks and local recovery](../reference/Local_Setup.md#recover-the-failed-owner)

The public reader can run from static files because the local apps finish the authoring and preparation before release. Manage and Public share reader code such as document rendering and navigation. Each gets its data and capabilities from its own entry point. Manage can call local authoring services, while Public reads prepared files. The local Docs service can also serve a separate preview of validated returned packages. [Docs Viewer runtime](../reference/Docs_Viewer_Runtime.md#three-surfaces) · [Docs Review](../reference/Docs_Review.md)

## Find the source of a change

Use the [repository ownership map](../reference/Source_Tree_Ownership.md) for code roots and separate-project boundaries, and the [Docs Viewer reference map](../reference/Docs_Viewer.md#find-the-owner) to locate a reader, authoring or service owner. The [public shell reference](../reference/Public_Docs_Route_Shell.md) owns the installed site entry point and runtime projection.

- **Document content and organisation.** Edit the Working Markdown and front matter at its configured location. The ordinary Index order and each Book Tree record the authored placement. The builders produce the JSON that Manage and Public read. Working's generated files can be replaced by the owning build. [Working storage and roles](../reference/Source_Organisation.md#storage-and-roles)
- **Catalogue facts.** Edit a Work, Series or Gallery in Studio. Studio saves these records under `studio/data/canonical/catalogue/`. Refresh prepares the changed Working data. Regenerate adopts the relevant Work facts and Gallery references into Catalogue documents, which the reader can open directly by Work ID. [Adopted Work data](../reference/Generated_Data_Contracts.md#catalogue-reference-and-presentation)
- **Shared viewer behaviour or styling.** Edit the canonical files under `docs-viewer/`. The public website serves the tracked projection under `site/docs-viewer/`. The projection inventory identifies the files that ship publicly. This lets local apps use the canonical code and lets Pages serve a ready snapshot without a build step. [Public code projection inventory](../../site-tools/config/site-code-update.json)

## Working, Preview and the static site

One configured Docs workspace contains **Working** and **Preview**. Working owns editable document source, current media, replaceable generated data and the queues of prepared publication changes. Preview retains selected public documents and media prepared by Publish. The separate `bin/site-preview` command serves the repository's `site/` directory.

For local authoring, `DOTLINEFORM_DOCS_BASE_DIR` selects the Docs workspace. `DOTLINEFORM_PROJECTS_BASE_DIR` independently selects the Projects workspace used for Catalogue media staging and other project inputs. Set the applicable roots in `.env.local` to their existing locations. The checked workspace configuration owns the collection registrations and public destinations. [Docs workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) · [Workspace roles](../reference/Source_Organisation.md#storage-and-roles)

Follow a change from Working to the public site in [Publish and deploy](Publish_And_Deploy.md). Return to the [guide contents](README.md).
