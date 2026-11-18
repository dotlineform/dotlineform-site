# Change the system safely

Start with the outcome you want and identify the source that owns it. Authored documents belong to Working, Catalogue facts to Studio, shared reader behaviour to the canonical runtime, and design-time workspace settings to the checked configuration. Follow the affected output from that source to the reader that uses it. [How the site fits together](How_The_Site_Fits_Together.md) · [Development Checklist](../studio/Development_Checklist.md#before-editing-a-material-change)

## Choose the owner

Suppose the public homepage and Docs Viewer Manage should open a different ordinary document by default. The top-level `default_doc_id` in `docs-viewer/config/workspace/docs-workspace.json` owns that choice for both readers. Pick an exact ID for a document available in Working and the public `site/` snapshot. One setting feeds both readers, and each reader’s browser configuration supplies its own URLs. [Workspace and target contracts](../studio/Configuration_And_Extension_Points.md#workspace-and-target-contracts)

## Prepare and check the change

1. **Edit the setting and generate browser configuration.** From the repository root, run `python3 docs-viewer/build/build_browser_config.py`. Inspect the two generated JSON files under `docs-viewer/config/defaults/` and confirm they carry the intended ID. This command updates browser configuration only. [Config-only projection](../studio/Configuration_And_Extension_Points.md#builder-and-local-service-integration)
2. **Project and validate the public copy.** Run `bin/site-code-update` and inspect `git diff -- site/docs-viewer` for the expected change to the public browser configuration. Run `bin/site-code-update --check` to check that the copy matches its canonical file and `bin/site-validate` to check the deploy tree. The validator checks for the configured public default document’s by-ID file. [Projection commands](../studio/Run_Checks.md#docs-viewer-site-code-projection)
3. **Open both routes.** Use the local Docs Viewer runner for `/docs/` and `bin/site-preview` for `/`. Open the bare routes and confirm they display the new default. Follow an explicit link to a different document to confirm that links still open their own targets. This checks what the reader displays with the prepared configuration and data. [Local runners](../studio/Local_Runners.md#choose-a-runner)
4. **Release the reviewed files.** Include the workspace setting and its generated copies in the reviewed Git change. The public config travels with the committed `site/` snapshot through the manual Pages workflow. [Publish and deploy](Publish_And_Deploy.md#3-review-and-deploy-the-site)

For other changes, choose the smallest check that can expose the failure you are concerned about. Presentation changes usually need a manual look. A change to a parser, service or output contract can use a focused existing check at that boundary. Agree the specification before adding or changing tests. [Verification policy](../studio/Development_Workflow.md#verify-proportionally) · [Test Contract Discipline](../studio/Test_Contract_Discipline.md#running-tests)

## Recover from a failure

- **Configuration generation fails or the projection is stale.** Use the error to check the workspace setting or the configured workspace location. Rerun the config-only command and confirm both browser files carry the intended ID. Run `bin/site-code-update`, then inspect and validate the corrected projection.
- **The public default document is missing.** Read the ID and path in the validator error. Correct a wrong ID in the workspace configuration and repeat its projection. If the intended page is still in Working and should be public, prepare and Publish it, then validate the public snapshot. [Document preparation](Publish_And_Deploy.md#1-prepare-the-change)
- **The reviewed change fails on Pages.** Inspect the failing job and the revision it used. Reproduce artifact validation locally. Use the run details to diagnose a Pages configuration or permission failure. If the default is already live and needs to be reverted, restore the previous workspace setting from Git, regenerate its copies and release the reviewed correction through the normal workflow. [GitHub Actions debugging](../studio/GitHub_Actions.md#debugging)

For a failed authoring or publication operation, use the reported phase and completed effects to choose where to resume. If Source Save persisted Markdown before generation failed, correct the problem and rebuild that document. If Publish stopped during a transfer, inspect the affected destination and pending selection before deciding whether to rerun Publish. Completed effects can already be in place. [External edits and rebuilds](../studio/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Publication failure and timing](../studio/Catalogue_Deployment.md#failure-and-timing)

Return to the [guide contents](README.md).
