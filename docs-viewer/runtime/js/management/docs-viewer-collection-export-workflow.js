import { fetchManagementJson } from "./docs-viewer-management-client.js";
import { openDocsViewerConfirmModal } from "./docs-viewer-management-modals.js";

function confirmationOptions(preview, options) {
  var canApply = preview.replace_allowed;
  var replacing = preview.replacement_required;
  var body = [
    "Collection: " + preview.collection,
    preview.destination_label,
    "Includes " + preview.media_count + " media file" + (preview.media_count === 1 ? "" : "s") + "."
  ];
  if (preview.external_dependency_count > 0) {
    body.push("Leaves " + preview.external_dependency_count + " external media reference"
      + (preview.external_dependency_count === 1 ? "" : "s") + " unchanged.");
  }
  return {
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Export " + preview.document_count + " document" + (preview.document_count === 1 ? "" : "s") + " to:",
    body: body,
    primaryLabel: replacing ? "Replace" : canApply ? "Create snapshot" : "Unavailable",
    primaryDisabled: !canApply,
    primaryTone: replacing ? "danger" : "",
    initialFocus: replacing || !canApply ? "cancel" : "",
    cancelLabel: "Cancel"
  };
}

async function requestSnapshot(operation, payload, options) {
  var stopBusy = options.startBusyOperation();
  options.setStatus("", false);
  try {
    return await fetchManagementJson("/docs/export/static-html/" + operation, "POST", payload, options.clientOptions);
  } finally {
    stopBusy();
  }
}

/** Export one captured collection selection; own requests, confirmation and busy completion. */
export async function openCollectionExportWorkflow(options) {
  var preview = await requestSnapshot("preview", {
    collection: options.target.collection,
    doc_ids: options.target.doc_ids.slice()
  }, options);
  var confirmed = await openDocsViewerConfirmModal(confirmationOptions(preview, options));
  if (!confirmed) return null;

  return requestSnapshot("apply", {
    collection: preview.collection,
    doc_ids: preview.doc_ids,
    export_date: preview.export_date,
    plan_revision: preview.plan_revision,
    target_revision: preview.target_revision,
    confirm: true,
    replace_existing: preview.replacement_required
  }, options);
}
