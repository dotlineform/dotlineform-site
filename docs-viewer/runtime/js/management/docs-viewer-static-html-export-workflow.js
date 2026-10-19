import {
  applyManagedDocsStaticHtmlExport,
  previewManagedDocsStaticHtmlExport
} from "./docs-viewer-management-client.js";
import {
  openDocsViewerConfirmModal
} from "./docs-viewer-management-modals.js";

function normalizeIds(values) {
  var seen = new Set();
  return (Array.isArray(values) ? values : []).map(function (value) {
    return String(value || "").trim();
  }).filter(function (docId) {
    if (!docId || seen.has(docId)) return false;
    seen.add(docId);
    return true;
  });
}

function setBusy(callbacks, busy) {
  if (typeof callbacks.setBusy === "function") callbacks.setBusy(busy);
  if (typeof callbacks.render === "function") callbacks.render();
}

function setMessage(callbacks, message, isError) {
  if (typeof callbacks.setMessage === "function") callbacks.setMessage(message, isError);
}


export function staticHtmlSnapshotPreviewCanApply(preview) {
  return preview.replace_allowed === true && preview.target_state !== "non_directory";
}

export function buildStaticHtmlSnapshotConfirmationBody(preview) {
  var mediaCount = Number(preview.media_count || 0);
  var externalCount = Number(preview.external_dependency_count || 0);
  var body = [
    preview.destination_label,
    "Includes " + mediaCount + " media file" + (mediaCount === 1 ? "" : "s") + "."
  ];
  if (externalCount > 0) {
    body.push(
      "Leaves " + externalCount + " external media reference"
        + (externalCount === 1 ? "" : "s") + " unchanged."
    );
  }
  return body;
}

export function staticHtmlSnapshotConfirmationTitle(preview) {
  var documentCount = Number(preview.document_count || 0);
  return "Export " + documentCount + " document" + (documentCount === 1 ? "" : "s") + " to:";
}

export function staticHtmlSnapshotConfirmationOptions(preview, options = {}) {
  var canApply = staticHtmlSnapshotPreviewCanApply(preview);
  var replacing = preview.target_state === "recognized" || preview.target_state === "unrecognized";
  return {
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: staticHtmlSnapshotConfirmationTitle(preview),
    body: [
      ...(preview.collection ? ["Collection: " + preview.collection] : []),
      ...(options.targetDocument ? [
        "Document: " + options.targetDocument.title + " (" + options.targetDocument.doc_id + "). Includes this document and all its descendants."
      ] : []),
      ...buildStaticHtmlSnapshotConfirmationBody(preview)
    ],
    primaryLabel: replacing ? "Replace" : canApply ? "Create snapshot" : "Unavailable",
    primaryDisabled: !canApply,
    primaryTone: replacing ? "danger" : "",
    initialFocus: replacing || !canApply ? "cancel" : "",
    cancelLabel: "Cancel"
  };
}

export async function openStaticHtmlSnapshotExportWorkflow(options = {}) {
  var docIds = normalizeIds(options.docIds);
  var callbacks = options.callbacks || {};
  var clientOptions = options.clientOptions || {};
  var previewSnapshot = options.previewSnapshot || previewManagedDocsStaticHtmlExport;
  var applySnapshot = options.applySnapshot || applyManagedDocsStaticHtmlExport;
  var confirmSnapshot = options.confirmSnapshot || openDocsViewerConfirmModal;
  if (!docIds.length) throw new Error("No documents are available for export.");

  var preview;
  setBusy(callbacks, true);
  setMessage(callbacks, "", false);
  try {
    preview = await previewSnapshot(docIds, clientOptions);
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, "", false);

  var canApply = staticHtmlSnapshotPreviewCanApply(preview);
  var confirmed = await confirmSnapshot(staticHtmlSnapshotConfirmationOptions(preview, options));
  if (!confirmed) return null;
  if (!canApply) throw new Error("Snapshot destination cannot be replaced.");

  var applied;
  setBusy(callbacks, true);
  setMessage(callbacks, "", false);
  try {
    applied = await applySnapshot(preview, clientOptions);
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, applied && applied.summary_text || "Dated snapshot exported.", false);
  return applied;
}
