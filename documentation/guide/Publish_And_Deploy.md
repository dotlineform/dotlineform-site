# Publish and deploy

A content release has three parts. Prepare changes in Working, run **Publish** to apply queued changes to their configured destinations, then deploy the tracked `site/` snapshot to GitHub Pages. Each step has a different owner and a different point at which the change becomes visible.

## 1. Prepare the change

| What changed | How to prepare it |
| --- | --- |
| An ordinary document or a document in an authored collection | Save in Docs Viewer Manage. Save completes the exact Working generation and prepares the eligible publication effects. For a Markdown file edited outside Manage, run the exact document build. Use a full Working rebuild when the change requires wider reconciliation, such as a renderer change. [External edits and rebuilds](../reference/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Working rebuild](../reference/Builder.md#working-rebuild) |
| A Catalogue Work or shared definition | Save or Delete in Studio and run **Refresh Catalogue**. Refresh queues shared public output directly. Use **Regenerate** in Docs Viewer to complete and queue affected Work documents. [Maintain the Catalogue](Maintain_The_Catalogue.md) |
| Search or Recent | Choose **Actions → Refresh Search and Recent** in Manage when those results need updating. A full Working rebuild from the command line also generates discovery data. Ordinary document edits preserve the saved Search and Recent files. Each changed discovery file is queued for Publish. [Search and Recent](../reference/Reader_Discovery_And_Return.md#build-and-publication) |
| Shared or public viewer code | Change the canonical runtime in `docs-viewer/` and run `bin/site-code-update` for files in the public projection inventory. Review the tracked `site/` changes, then run `bin/site-code-update --check` and `bin/site-validate`. For a code-only change, continue directly to step 3. [Projection inventory](../../site-tools/config/site-code-update.json) · [Example configuration change](Change_The_System_Safely.md#prepare-and-check-the-change) |

**Exact document build.** After editing an eligible page externally, use **Edit doc → Rebuild**. Working regenerates that page and its exact dependencies, queues its public document and media selection, and updates affected public metadata. A Draft or exclusion edit can instead queue withdrawals for a formerly eligible branch, including an affected hosted collection. Working keeps the authored sources. [Exact build and eligibility](../reference/Builder.md#docs-build-flow)

**Full Working Build.** For a shared renderer change, run `python3 docs-viewer/build/rebuild_working.py --write` from the repository root with the project Python. It rebuilds ordinary and non-Catalogue collection documents, checks their ready media, compares public eligibility with saved membership, and queues the completed document and shared effects. Changed Recent and Search outputs join the queue. Check the maintenance result before publishing because an error in a later phase can leave earlier completed effects pending. [Full Working Build](../reference/Builder.md#working-rebuild)

## 2. Publish queued content

In Docs Viewer Manage, return to the Index tree if Search or Recent is open, then choose **Actions → Publish** after preparation has completed. Publish processes the selected Docs and Catalogue units, prepares the required Preview files and applies the supplied writes and removals to the configured repository and R2 destinations. For selected documents and Works that need Catalogue presentation, Publish prepares it from completed Working data. A successful unit clears its queue entry. Empty queues skip transfers. [Publish entry point](../../docs-viewer/services/docs_publish.py) · [Preparation and transfer contract](../reference/Builder.md#publish-preparation)

The queue carries the effects that Working already decided and prepared. When expected changes are missing from the queue, start with the owning preparation step. Publish transfers Search and Recent when their prepared files are queued. [Recent contract](../reference/Generated_Data_Contracts.md#recent-contract)

After publication succeeds, the same click backs up saved Docs source, document media and the three Working queues to the private Docs data repository. It also backs up published site data and canonical Studio Catalogue JSON to the site repository. The button remains busy through both Git backups. Successful backups are silent. If a push fails after a local commit, the message says the commit was saved locally and the next Publish retries the push. [Publish and Git backups](../reference/Builder.md#preview-and-deployment-boundary) · [What each backup covers](../reference/Local_Setup.md#restore-the-docs-workspace)

If Publish stops, use the reported phase and target to decide what to fix. Completed writes and removals remain in place, and failed or unprocessed selections stay pending. After correcting the cause, rerun Publish to process the remaining selections. Review the affected destinations, since R2 media can change while Pages still serves the previous repository snapshot. The **Docs Media → R2** report records suspected orphaned Docs media for manual review. [Publish failure and recovery](../reference/Builder.md#preview-and-deployment-boundary) · [R2 orphan report](../reference/Media_And_Asset_Handling.md#r2-orphan-report)

## 3. Review and deploy the site

1. Use `bin/site-preview` to review the changed routes in the repository's `site/` tree. Run `bin/site-validate` to check the deploy artifact.
2. Confirm the intended content checkpoint is on `main`. Review, commit and push any approved site code or runtime changes separately.
3. Manually run the **Public site** GitHub Pages workflow on `main`. It validates and uploads the tracked `site/` tree. The deploy job requires the repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` to be `true`. Confirm the deploy job succeeded, then check the affected routes on the live site. [Public site workflow](../../.github/workflows/public-site.yml)

The manual workflow makes the live release a deliberate step after inspecting the exact artifact. The same path deploys static content and public runtime changes. For an overview of the owners, see [How the site fits together](How_The_Site_Fits_Together.md) or return to the [guide contents](README.md).
