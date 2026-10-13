import { deleteManagedCollectionDoc } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
import { DOCS_VIEWER_ACTION_IDS } from "./docs-viewer-action-definitions.js";
import { openDocsViewerConfirmModal } from "./docs-viewer-management-modals.js";

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
        body: ["Document: " + options.title + " (" + target.doc_id + ").", "Collection: " + target.collection, "Permanently deletes this one collection document."],
        primaryLabel: "Delete document", primaryTone: "danger", initialFocus: "cancel",
        cancelLabel: "Cancel", signal: modalAbortController.signal
      });
      modalAbortController = null;
      if (!active || !confirmed) return null;
      stopBusy = options.startBusyOperation();
      options.setStatus("Deleting " + options.title + "...", false);
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
