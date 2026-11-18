# Change the system safely

Start with the outcome you want and identify the source that owns it. Authored documents belong to Working, Catalogue facts to Studio, shared reader behaviour to the canonical runtime, and design-time workspace settings to the checked configuration. Follow the affected output from that source to the reader that uses it. [How the site fits together](How_The_Site_Fits_Together.md) · [Development Checklist](../studio/Development_Checklist.md#before-editing-a-material-change)

## Choose the owner

Suppose the public homepage and Docs Viewer Manage should open a different ordinary document by default. The top-level `default_doc_id` in `docs-viewer/config/workspace/docs-workspace.json` owns that choice for both readers. Copy the exact ID from the ordinary document’s link or source. Check its by-ID files in the configured Docs workspace’s `working/generated/documents/by-id/` and in `site/assets/data/docs/by-id/`. Use a ready, published target so both bare routes can open it. [Workspace and target contracts](../studio/Configuration_And_Extension_Points.md#workspace-and-target-contracts)

## Prepare and check the change

1. **Edit the setting and generate browser configuration.** With the Docs workspace configured, run `python3 docs-viewer/build/build_browser_config.py` from the repository root using the project interpreter. Check `workspace.default_doc_id` in `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json`. Both should carry the intended ID. [Config-only projection](../studio/Configuration_And_Extension_Points.md#builder-and-local-service-integration)
2. **Project and validate the public copy.** Run `bin/site-code-update`. Inspect `git diff -- docs-viewer/config site/docs-viewer` for the setting, both generated files and the public copy. Run `bin/site-code-update --check` and `bin/site-validate`. The validator checks that the public default document’s by-ID file exists. [Projection commands](../studio/Run_Checks.md#docs-viewer-site-code-projection)
3. **Open both routes.** Open the bare local Manage and public-preview URLs in fresh tabs. A URL already carrying `?doc=…` tests an explicit target. Confirm the bare URLs open the new default, then follow an explicit link to a different document and confirm that it still opens its own target. [Local addresses](How_The_Site_Fits_Together.md#start-a-local-surface)
4. **Release the reviewed files.** Include the workspace setting and its three generated copies in the reviewed Git change. The public copy travels with the committed `site/` snapshot through the manual Pages workflow. Use the Publish step only for separate queued content changes, such as preparing a new default document for the public site. [Publish and deploy](Publish_And_Deploy.md#3-review-and-deploy-the-site)

For other changes, choose the smallest check that can expose the failure you are concerned about. Presentation changes usually need a manual look. A change to a parser, service or output contract can use a focused existing check at that boundary. Agree the specification before adding or changing tests. [Verification policy](../studio/Development_Workflow.md#verify-proportionally) · [Test Contract Discipline](../studio/Test_Contract_Discipline.md#running-tests)

## Recover from a failure

- **Configuration generation fails or the projection is stale.** Use the error to check the workspace setting or the configured workspace location. Rerun the config-only command and confirm both browser files carry the intended ID. Run `bin/site-code-update`, then inspect and validate the corrected projection.
- **The public default document is missing.** Read the by-ID path in the validator error. The public root has the internal route ID `analysis`, which can appear in that message. Correct a wrong ID in the workspace configuration and repeat its projection. If the intended page is still in Working and should be public, prepare and Publish it, then validate the public snapshot. [Document preparation](Publish_And_Deploy.md#1-prepare-the-change)
- **Pages does not release the reviewed change.** Check which revision the run used. If validation failed, reproduce it locally on that revision. If deployment was skipped after validation, check the workflow branch and deployment gate. To revert a change already live, restore the previous workspace setting from Git, regenerate its copies and release the reviewed correction. [GitHub Actions debugging](../studio/GitHub_Actions.md#debugging)

For a failed authoring or publication operation, use the reported phase and completed effects to choose where to resume. If Source Save persisted Markdown before generation failed, correct the problem and rebuild that document. If Publish stopped during a transfer, inspect the affected destination and pending selection before deciding whether to rerun Publish. Completed effects can already be in place. [External edits and rebuilds](../reference/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Publication failure and timing](../studio/Catalogue_Deployment.md#failure-and-timing)

Return to the [guide contents](README.md).
