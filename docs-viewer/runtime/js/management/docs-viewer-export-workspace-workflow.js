import { readManagedDocsIndex } from "./docs-viewer-management-client.js";
import { stageStaticHtmlExportCapability } from "./docs-viewer-management-capabilities.js";
import { openStaticHtmlSnapshotExportWorkflow } from "./docs-viewer-static-html-export-workflow.js";
import { normalizeDocsIndexTreePayload } from "../shared/docs-viewer-tree-payload-adapter.js";

/** Export the complete ordinary index of the explicitly selected stage. */
export async function runManagedDocsExportWorkspaceWorkflow(options = {}) {
  const clientOptions = options.clientOptions || {};
  const capability = stageStaticHtmlExportCapability(options.capabilities, clientOptions.stage);
  if (!capability.available) throw new Error(capability.reason || "Workspace export is unavailable.");
  const callbacks = options.callbacks || {};
  let checkedDocIds;
  if (callbacks.setBusy) callbacks.setBusy(true);
  if (callbacks.render) callbacks.render();
  try {
    const index = normalizeDocsIndexTreePayload(await readManagedDocsIndex(clientOptions));
    const docs = Array.isArray(index.docs) ? index.docs : [];
    checkedDocIds = docs.map((doc) => String(doc.doc_id || "").trim());
    if (!checkedDocIds.length || checkedDocIds.some((id) => !id)
        || new Set(checkedDocIds).size !== checkedDocIds.length) {
      throw new Error("Workspace export requires a generated index with distinct document identities.");
    }
  } finally {
    if (callbacks.setBusy) callbacks.setBusy(false);
    if (callbacks.render) callbacks.render();
  }
  return openStaticHtmlSnapshotExportWorkflow({ ...options, checkedDocIds });
}
