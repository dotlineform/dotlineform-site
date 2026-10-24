import { runCatalogueRegeneration } from "./docs-viewer-management-client.js";
import { normalizeManagedDocumentCollectionTarget } from "./docs-viewer-management-document-target.js";
import { openCatalogueRegenerateModal } from "./docs-viewer-management-catalogue-regenerate-modal.js";

/** Complete queued regeneration and report refresh before opening the result. */
export async function openCatalogueRegenerate(options) {
  var target = normalizeManagedDocumentCollectionTarget(options.target);
  if (target.collection !== "catalogue") {
    throw new Error("Regenerate requires the Working Catalogue collection.");
  }
  if (typeof options.refreshCollection !== "function") {
    throw new Error("Catalogue report refresh is unavailable.");
  }
  var payload;
  var failure = null;
  try {
    payload = await runCatalogueRegeneration(target, options.clientOptions);
    if (payload.counts.built || payload.counts.delete || payload.counts.create) {
      try {
        await options.refreshCollection(target);
      } catch (cause) {
        var error = new Error("Catalogue documents were updated, but the report could not refresh. " + cause.message);
        error.payload = payload;
        throw error;
      }
    }
  } catch (error) {
    failure = error;
  }
  options.onBusyChange(false);
  return openCatalogueRegenerateModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    payload: payload,
    error: failure
  });
}
