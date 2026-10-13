import { staticHtmlExportCapability } from "./docs-viewer-management-capabilities.js";
import { openStaticHtmlSnapshotExportWorkflow } from "./docs-viewer-static-html-export-workflow.js";
/** Export the complete ordinary index of the local workspace. */
export async function runManagedDocsExportWorkspaceWorkflow(options = {}) {
  const capability = staticHtmlExportCapability(options.capabilities);
  if (!capability.available) throw new Error(capability.reason || "Workspace export is unavailable.");
  const docIds = options.docIds;
  if (!docIds.length) throw new Error("No documents are available for export.");
  return openStaticHtmlSnapshotExportWorkflow({ ...options, docIds });
}
