import {
  applyCatalogueRegeneration,
  previewCatalogueRegeneration
} from "./docs-viewer-management-client.js";
import { normalizeManagedDocumentCollectionTarget } from "./docs-viewer-management-document-target.js";
import { openCatalogueRegenerateModal } from "./docs-viewer-management-catalogue-regenerate-modal.js";

/** Keep the exact collection and receipt through Apply and its awaited report refresh. */
export function openCatalogueRegenerate(options) {
  var target = normalizeManagedDocumentCollectionTarget(options.target);
  if (target.stage !== "working" || target.collection !== "catalogue") {
    throw new Error("Regenerate requires the Working Catalogue collection.");
  }
  if (typeof options.refreshCollection !== "function") {
    throw new Error("Catalogue report refresh is unavailable.");
  }
  return openCatalogueRegenerateModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    onBusyChange: options.onBusyChange,
    preview: function (onlyCreateNew) {
      return previewCatalogueRegeneration({ ...target, only_create_new: onlyCreateNew }, options.clientOptions);
    },
    apply: async function (preview) {
      var payload = await applyCatalogueRegeneration({
        ...target,
        only_create_new: preview.only_create_new,
        work_ids: preview.work_ids,
        preview_revision: preview.preview_revision,
        confirm: true
      }, options.clientOptions);
      if (payload.counts.selected) {
        try {
          await options.refreshCollection(target);
        } catch (cause) {
          var error = new Error("Documents generated, but the Catalogue report could not refresh. " + cause.message);
          error.payload = payload;
          throw error;
        }
      }
      return payload;
    }
  });
}
