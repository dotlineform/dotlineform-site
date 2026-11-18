# Publish and deploy

A content release has three parts. Prepare changes in Working, run **Publish** to apply queued changes to their configured destinations, then deploy the tracked `site/` snapshot to GitHub Pages. Each step has a different owner and a different point at which the change becomes visible.

## 1. Prepare the change

| What changed | How to prepare it |
| --- | --- |
| An ordinary document or a document in an authored collection | Save in Docs Viewer Manage. Save completes the exact Working generation and prepares the eligible publication effects. For a Markdown file edited outside Manage, run the exact document build. Use a full Working rebuild when the change requires wider reconciliation, such as a renderer change. [External edits and rebuilds](../reference/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Working rebuild](../studio/Builder.md#working-rebuild) |
| A Catalogue Work or shared definition | Save or Delete in Studio and run **Refresh Catalogue**. Refresh queues shared public output directly. Use **Regenerate** in Docs Viewer to complete and queue affected Work documents. [Maintain the Catalogue](Maintain_The_Catalogue.md) |
| Search or Recent | Choose **Actions → Refresh Search and Recent** in Manage when those results need updating. A full Working rebuild from the command line also generates discovery data. Ordinary document edits preserve the saved Search and Recent files. Each changed discovery file is queued for Publish. [Search and Recent](../studio/Docs_Viewer_Search.md#build-and-publication) |
| Shared or public viewer code | Change the canonical runtime in `docs-viewer/` and run `bin/site-code-update` for files in the public projection inventory. Review the tracked `site/` changes, then run `bin/site-code-update --check` and `bin/site-validate`. For a code-only change, continue directly to step 3. [Projection inventory](../../site-tools/config/site-code-update.json) · [Example configuration change](Change_The_System_Safely.md#prepare-and-check-the-change) |

Working owns the public eligibility decision because it already has the authored Draft flags, hierarchy, placements and publication exclusions when it prepares the change. A draft or excluded ordinary parent withholds its descendants. An excluded collection host also withholds its collection documents. This lets an author keep a Book's chapters ready in Manage while keeping its web pages out of publication. Catalogue Work data and media have separate owners from its document collection. [Publication eligibility](../reference/Source_Organisation.md#operations)

## 2. Publish queued content

In Docs Viewer Manage, return to the Index tree if Search or Recent is open, then choose **Actions → Publish** after preparation has completed. Publish processes the selected Docs and Catalogue units, prepares the required Preview files and applies the supplied writes and removals to the configured repository and R2 destinations. For selected documents and Works that need Catalogue presentation, Publish prepares it from completed Working data. A successful unit clears its queue entry. Empty queues return without publication work. [Publish entry point](../../docs-viewer/services/docs_publish.py) · [Preparation and transfer contract](../studio/Builder.md#publish-preparation)

The queue carries the effects that Working already decided and prepared. That keeps Publish focused on transferring those selections and checking their completion. When expected changes are missing from the queue, start with the owning preparation step. In particular, Search and Recent can change during Publish only when their prepared files were queued. [Recent contract](../studio/Generated_Data_Contracts.md#recent-contract)

If Publish stops, use the reported phase and target to decide what to fix. Completed writes and removals remain in place, and failed or unprocessed selections stay pending. After correcting the cause, rerun Publish to process the remaining selections. Review the affected destinations, since R2 media can change while Pages still serves the previous repository snapshot. The **Docs Media → R2** report can help diagnose suspected orphaned Docs media. It records candidates for manual review. [Failure and timing](../studio/Catalogue_Deployment.md#failure-and-timing) · [R2 orphan report](../studio/Media_And_Asset_Handling.md#r2-orphan-report)

## 3. Review and deploy the site

1. Use `bin/site-preview` to review the changed routes in the repository's `site/` tree. Run `bin/site-validate` to check the deploy artifact.
2. Review the intended changes, then commit and push the reviewed snapshot so that it is on `main`.
3. Manually run the **Public site** GitHub Pages workflow on `main`. It validates and uploads the tracked `site/` tree. The deploy job requires the repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` to be `true`. Confirm the deploy job succeeded, then check the affected routes on the live site. [Public site workflow](../../.github/workflows/public-site.yml)

The manual workflow makes the live release a deliberate step after inspecting the exact artifact. The same path deploys static content and public runtime changes. For an overview of the owners, see [How the site fits together](How_The_Site_Fits_Together.md) or return to the [guide contents](README.md).
