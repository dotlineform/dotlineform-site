import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";

/** Show a completed regeneration result or error with Close ready on opening. */
export function openCatalogueRegenerateModal(options) {
  var result = options.payload;
  var error = options.error;
  var content;
  if (error) {
    result = { ...error.payload, ok: false, error: error.message };
    var message;
    if (error.payload?.ok) {
      message = "Catalogue documents were updated, but the report could not refresh.";
    } else if (result.committed_source_operations) {
      message = "Source operations completed: " + result.committed_source_operations + ". Inspect the error before retrying.";
    } else {
      message = "Regenerate stopped before completing.";
    }
    content = "<div>" + escapeHtml(message) + "</div>";
  } else {
    var counts = result.counts;
    content = "<div>" + escapeHtml("Updated " + counts.updated) + "</div>"
      + "<div>" + escapeHtml("Created " + counts.create) + "</div>"
      + "<div>" + escapeHtml("Deleted " + counts.delete) + "</div>";
  }

  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Regenerate Catalogue",
    bodyHtml: content,
    actions: [
      { role: "modal-primary", label: "Close" }
    ],
    onOpen: function (modalApi) {
      if (error) modalApi.setStatus(error.message);
    }
  }).then(function () { return result; });
}
