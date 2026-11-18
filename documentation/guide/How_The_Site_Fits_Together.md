# How the site fits together

Dotlineform is a public portfolio and reading site. Visitors browse documents, Works and Galleries through a read-only Docs Viewer. The author uses two local web apps to make changes. Studio maintains the Catalogue, and Docs Viewer Manage maintains the documents and publishes the prepared changes.

| Surface | What it does | Where to start |
| --- | --- | --- |
| **Public site** | GitHub Pages serves the tracked `site/` tree. The public reader loads prepared data from that tree and media from the configured destinations. | Run `bin/site-preview` to inspect the repository snapshot locally. [Public entry page](../../site/index.html) |
| **Studio** | Edits canonical Works, Series, Galleries and memberships. **Refresh Catalogue** prepares the changed data and media for Working. | Run `bin/local-studio`. [Maintain the Catalogue](Maintain_The_Catalogue.md) |
| **Docs Viewer Manage** | Edits and organises Working documents and media. Catalogue **Regenerate** updates Catalogue documents from Studio's refreshed inputs. **Publish** applies queued Docs and Catalogue changes. | Run `docs-viewer/bin/docs-viewer`. [Local runners](../studio/Local_Runners.md) |

The public reader can run from static files because the local apps finish the authoring and preparation before release. Manage and Public share reader code such as document rendering and navigation. Each gets its data and capabilities from its own entry point. Manage can call local authoring services, while Public reads prepared files. The local Docs service can also serve a separate preview of validated returned packages. [Docs Viewer runtime](../studio/Docs_Viewer_Runtime.md#three-surfaces) · [Docs Review](../studio/Docs_Review.md)

## Find the source of a change

- **Document content and organisation.** Edit the Working Markdown and front matter at its configured location. The ordinary Index order and each Book Tree record the authored placement. The builders produce the JSON that Manage and Public read. Working's generated files can be replaced by the owning build. [Working storage and roles](../studio/Source_Organisation.md#storage-and-roles)
- **Catalogue facts.** Edit a Work, Series or Gallery in Studio. Studio saves these records under `studio/data/canonical/catalogue/`. Refresh prepares the changed Working data. Regenerate adopts the relevant Work facts and Gallery references into Catalogue documents, which the reader can open directly by Work ID. [Adopted Work data](../studio/Generated_Data_Contracts.md#catalogue-reference-and-presentation)
- **Shared viewer behaviour or styling.** Edit the canonical files under `docs-viewer/`. The public website serves the tracked projection under `site/docs-viewer/`. The projection inventory identifies the files that ship publicly. This lets local apps use the canonical code and lets Pages serve a ready snapshot without a build step. [Public code projection inventory](../../site-tools/config/site-code-update.json)

## Working, Preview and the static site

One configured Docs workspace contains **Working** and **Preview**. Working owns editable document source, current media, replaceable generated data and the queues of prepared publication changes. Preview retains selected public documents and media prepared by Publish. The separate `bin/site-preview` command serves the repository's `site/` directory.

For local authoring, `DOTLINEFORM_DOCS_BASE_DIR` selects the Docs workspace. `DOTLINEFORM_PROJECTS_BASE_DIR` independently selects the Projects workspace used for Catalogue media staging and other project inputs. Set the applicable roots in `.env.local` to their existing locations. The checked workspace configuration owns the collection registrations and public destinations. [Docs workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) · [Workspace roles](../studio/Source_Organisation.md#storage-and-roles)

Follow a change from Working to the public site in [Publish and deploy](Publish_And_Deploy.md). Return to the [guide contents](README.md).
