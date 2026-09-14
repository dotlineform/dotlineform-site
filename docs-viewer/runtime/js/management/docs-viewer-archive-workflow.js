import { previewManagedDocumentArchive, applyManagedDocumentArchive } from "./docs-viewer-management-client.js";
import { openDocsViewerConfirmModal } from "./docs-viewer-management-modal-shell.js";

/** Confirm only the server-counted subtree size, then apply its exact Archive receipt. */
export async function openArchiveWorkflow(options = {}) {
  var callbacks = options.callbacks || {};
  function busy(value) {
    if (callbacks.setBusy) callbacks.setBusy(value);
    if (callbacks.render) callbacks.render();
  }
  function message(value) {
    if (callbacks.setMessage) callbacks.setMessage(value, false);
  }
  var preview;
  busy(true);
  message("Preparing Archive…");
  try {
    preview = await previewManagedDocumentArchive(options.source, options.docIds, options.clientOptions);
  } finally {
    busy(false);
  }
  message("");
  var count = preview && preview.document_count;
  if (!preview || !preview.ok || !preview.receipt || !Number.isInteger(count) || count < 1) {
    throw new Error("Archive returned an invalid document count.");
  }
  var confirmed = await openDocsViewerConfirmModal({
    root: options.root, restoreFocus: options.restoreFocus,
    title: "Archive", bodyHtml: '<p>' + count + (count === 1 ? " document" : " documents") + ' will be moved.</p>',
    primaryLabel: "Archive", cancelLabel: "Cancel", initialFocus: "cancel"
  });
  if (!confirmed) return null;
  busy(true);
  message("Archiving…");
  try {
    var result = await applyManagedDocumentArchive(preview.receipt, options.clientOptions);
    if (callbacks.onApplied) await callbacks.onApplied(result);
    return result;
  } finally {
    busy(false);
    message("");
  }
}
