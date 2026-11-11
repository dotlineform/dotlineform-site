import { deleteManagedCollectionDoc, deleteManagedDoc } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
import { DOCS_VIEWER_ACTION_IDS } from "./docs-viewer-action-definitions.js";
import { openDocsViewerConfirmModal } from "./docs-viewer-management-modals.js";

/** Confirm the checked Book documents and apply the effects of one Delete request. */
export async function openBookSelectionDeleteWorkflow(options) {
  var target = options.target;
  var count = target.doc_ids.length;
  var label = count + " Book " + (count === 1 ? "document" : "documents");
  var confirmed = await openDocsViewerConfirmModal({
    root: options.root, restoreFocus: options.restoreFocus, title: "Delete " + label + "?",
    body: "This permanently deletes the checked Book documents and their owned media and removes them from their sections. The Library originals stay in Library.",
    primaryLabel: "Delete", primaryTone: "danger", initialFocus: "cancel"
  });
  if (!confirmed) return;

  var stopBusy = options.startBusyOperation();
  options.setStatus("", false);
  try {
    var payload;
    var deleteError;
    try {
      payload = await deleteManagedDoc(target.doc_ids, { ...options.clientOptions, collection: target.collection });
    } catch (error) {
      deleteError = error;
      payload = error.payload;
    }
    var failures = [];
    for (var docId of payload?.deleted_doc_ids || []) {
      failures.push(...(options.commitDocumentChange({
        target: { collection: target.collection, doc_id: docId }, deleted: true
      }) || []));
    }
    if (failures.length) {
      var prefix = deleteError ? deleteError.message + " " : "Documents deleted. ";
      throw new Error(prefix + "Retained views could not be updated: " + failures.map(failure => failure.message).join("; "));
    }
    if (deleteError) throw deleteError;
  } finally {
    stopBusy();
  }
}

/** Confirm one loaded flat target and await its deletion and display completion. */
export function createDocsViewerManagementCollectionDeleteWorkflow(options) {
  var target = normalizeManagedDocumentTarget(options.target);
  if (!target.collection) throw new Error("Collection Delete requires an exact collection target.");
  var button = options.button;
  var active = true;
  var busy = false;
  var modalAbortController = null;

  function projectButton() {
    var resolution = options.resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE, target);
    button.hidden = resolution.hidden;
    button.disabled = busy || resolution.disabled;
    button.title = resolution.disabledReason || "Delete " + options.title;
    button.setAttribute("aria-label", button.title);
    if (busy) button.setAttribute("aria-busy", "true");
    else button.removeAttribute("aria-busy");
    return resolution.enabled;
  }

  function matches(payload) {
    return payload && payload.target && managedDocumentTargetsEqual(payload.target, target);
  }

  async function run() {
    if (!active || busy || options.resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE, target).disabled) return null;
    busy = true;
    projectButton();
    var stopBusy = null;
    var complete = false;
    try {
      modalAbortController = new AbortController();
      var confirmed = await openDocsViewerConfirmModal({
        root: options.root, restoreFocus: options.restoreFocus || button,
        title: "Delete " + options.title + "?",
        body: ["Document: " + options.title + " (" + target.doc_id + ").", "Collection: " + target.collection, "Permanently deletes this one collection document and its document-owned media and thumbnail, including unused files."],
        primaryLabel: "Delete document", primaryTone: "danger", initialFocus: "cancel",
        cancelLabel: "Cancel", signal: modalAbortController.signal
      });
      modalAbortController = null;
      if (!active || !confirmed) return null;
      stopBusy = options.startBusyOperation();
      options.setStatus("", false);
      var payload = await deleteManagedCollectionDoc(target, options.clientOptions);
      if (!matches(payload) || payload.source_deleted !== true || payload.generation_complete !== true
        || !Array.isArray(payload.deleted_doc_ids) || payload.deleted_doc_ids.length !== 1 || payload.deleted_doc_ids[0] !== target.doc_id) {
        throw new Error("Delete did not return its completed exact collection target.");
      }
      complete = true;
      await options.commitDeletedDocument(target);
      options.setStatus("", false);
      return payload;
    } catch (error) {
      var partial = error.payload;
      var failures = [];
      if (matches(partial) && Array.isArray(partial.deleted_doc_ids) && partial.deleted_doc_ids.includes(target.doc_id)) {
        failures = options.commitDocumentChange({ target: target, deleted: true }) || [];
      }
      var projectionMessage = failures.length ? " Retained views could not be updated: " + failures.map(function (failure) { return failure.message; }).join("; ") : "";
      options.setStatus((complete ? "Document deleted and generated state updated, but display failed: " : "") + (error.message || "Delete failed.") + projectionMessage, true);
      return null;
    } finally {
      if (stopBusy) stopBusy();
      busy = false;
      if (active) projectButton();
    }
  }

  button.addEventListener("click", run);
  return {
    initialize: projectButton,
    run: run,
    destroy: function () {
      active = false;
      if (modalAbortController) modalAbortController.abort();
      button.removeEventListener("click", run);
      button.disabled = true;
    }
  };
}
