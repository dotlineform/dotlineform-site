import { runCatalogueRegeneration } from "./docs-viewer-management-client.js";
import { normalizeManagedDocumentCollectionTarget } from "./docs-viewer-management-document-target.js";
import { openCatalogueRegenerateModal } from "./docs-viewer-management-catalogue-regenerate-modal.js";

/** Keep the exact collection through one awaited Run and report refresh. */
export function openCatalogueRegenerate(options) {
  var target = normalizeManagedDocumentCollectionTarget(options.target);
  if (target.collection !== "catalogue") {
    throw new Error("Regenerate requires the Working Catalogue collection.");
  }
  if (typeof options.refreshCollection !== "function") {
    throw new Error("Catalogue report refresh is unavailable.");
  }
  return openCatalogueRegenerateModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    onBusyChange: options.onBusyChange,
    run: async function () {
      var payload = await runCatalogueRegeneration(target, options.clientOptions);
      if (payload.counts.built || payload.counts.delete || payload.counts.create) {
        try {
          await options.refreshCollection(target);
        } catch (cause) {
          var error = new Error("Catalogue documents were updated, but the report could not refresh. " + cause.message);
          error.payload = payload;
          throw error;
        }
      }
      return payload;
    }
  });
}
