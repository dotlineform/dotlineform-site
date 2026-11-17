# Publish and deploy

A content release has three parts. Prepare changes in Working, run **Publish** to apply queued changes to their configured destinations, then deploy the tracked `site/` snapshot to GitHub Pages. Each step has a different owner and a different point at which the change becomes visible.

## 1. Prepare the change

| What changed | How to prepare it |
| --- | --- |
| An ordinary document or a document in an authored collection | Save in Docs Viewer Manage. Save completes the exact Working generation and prepares the eligible publication effects. For a Markdown file edited outside Manage, run the exact document build. Use a full Working rebuild when the change requires wider reconciliation, such as a renderer change. [External edits and rebuilds](../studio/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Working rebuild](../studio/Builder.md#working-rebuild) |
| A Catalogue Work | Save or Delete in Studio, run **Refresh Catalogue**, then **Regenerate** in Docs Viewer. Refresh prepares selected Working data and media. Regenerate produces the affected Catalogue documents and queues them for publication. Shared definition changes that affect no Work documents can be prepared by Refresh alone. [Catalogue workflow](../studio/Catalogue_Save_And_Refresh.md#current-workflow) |
| Search or Recent | Use **Refresh Search and Recent** in Manage when those results need updating. A full Working rebuild also generates discovery data. Ordinary document edits preserve the saved Search and Recent files. Each changed discovery file is queued for Publish. [Search and Recent](../studio/Docs_Viewer_Search.md) |
| Shared or public viewer code | Change the canonical runtime in `docs-viewer/` and run `bin/site-code-update` for files in the public projection inventory. Review the tracked `site/` changes, then run `bin/site-code-update --check` and `bin/site-validate`. [Projection inventory](../../site-tools/config/site-code-update.json) |

Working owns the public eligibility decision because it already has the authored Draft flags, hierarchy, placements and publication exclusions when it prepares the change. A draft or excluded ordinary parent withholds its descendants. An excluded collection host also withholds its collection documents. This lets an author keep a Book's chapters ready in Manage while keeping its web pages out of publication. Catalogue Work data and media have separate owners from its document collection. [Publication eligibility](../studio/Source_Organisation.md#operations)

## 2. Publish queued content

In Docs Viewer Manage, choose **Publish** after the relevant preparation has completed. Publish processes the selected Docs and Catalogue units, prepares the required Preview files and applies the supplied writes and removals to the configured repository and R2 destinations. It can prepare the presentation of a selected Catalogue item from completed Working data. A successful unit clears its queue entry. Empty queues return without publication work. [Publish entry point](../../docs-viewer/services/docs_publish.py) · [Preparation and transfer contract](../studio/Builder.md#publish-preparation)

The queue carries the effects that Working already decided and prepared. That keeps Publish focused on transferring those selections and checking their completion. When expected changes are missing from the queue, start with the owning preparation step. In particular, Search and Recent can change during Publish only when their prepared files were queued. [Recent contract](../studio/Generated_Data_Contracts.md#recent-contract)

If Publish stops, use the reported phase and target to decide what to fix. Completed writes and removals remain in place, and failed or unprocessed selections stay pending. Review the affected destinations before deciding whether to run Publish again. R2 media changes take effect during Publish, so they can be visible while Pages still serves the previous repository snapshot. For suspected orphaned Docs media, use **Docs Media → R2** to inspect candidates before deciding what to remove. [Failure and timing](../studio/Catalogue_Deployment.md#failure-and-timing) · [R2 orphan report](../studio/Media_And_Asset_Handling.md#r2-orphan-report)

## 3. Review and deploy the site

1. Use `bin/site-preview` to review the changed routes in the repository's `site/` tree. Run `bin/site-validate` to check the deploy artifact.
2. Review the intended changes, then commit and push the reviewed snapshot so that it is on `main`.
3. Manually run the **Public site** GitHub Pages workflow on `main`. It validates and uploads the tracked `site/` tree. The deploy job requires the repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` to be `true`. Confirm the deploy job succeeded, then check the affected routes on the live site. [Public site workflow](../../.github/workflows/public-site.yml)

The manual workflow makes the live release a deliberate step after inspecting the exact artifact. The same path deploys static content and public runtime changes. For an overview of the owners, see [How the site fits together](How_The_Site_Fits_Together.md) or return to the [guide contents](README.md).
